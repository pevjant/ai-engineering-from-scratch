> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 전문가 혼합(Mixture of Experts, MoE)

> 덴스(dense) 70B 트랜스포머는 토큰 하나를 처리할 때 모든 파라미터를 깨웁니다. 671B MoE는 토큰당 37B만 깨우는데도 모든 벤치마크에서 그 모델을 이깁니다. 희소성(sparsity)은 이 10년 가장 중요한 스케일링 아이디어입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 7 · 05(풀 트랜스포머), 페이즈 7 · 07(GPT)
**시간:** 약 45분

## 문제 상황

덴스 트랜스포머의 추론 FLOPs는 파라미터 수와 같습니다(순전파 기준 2배). 덴스 모델을 키우면 토큰 하나하나가 전체 요금을 다 냅니다. 2024년경 최전선 모델들은 연산 벽에 부딪혔습니다. 뚜렷하게 더 똑똑해지려면 토큰당 FLOPs가 기하급수적으로 더 필요했죠.

전문가 혼합(MoE)은 이 연결고리를 끊습니다. 각 FFN을 `E`개의 독립적인 전문가(expert)와, 토큰마다 `k`명의 전문가를 고르는 라우터로 바꿉니다. 전체 파라미터 = `E × FFN_size`. 토큰당 활성 파라미터 = `k × FFN_size`. 2026년 전형적인 설정은 `E=256`, `k=8`입니다. 저장 공간은 `E`에 비례해 늘고, 연산량은 `k`에 비례합니다.

2026년 최전선은 거의 전부 MoE입니다: DeepSeek-V3(전체 671B / 활성 37B), Mixtral 8×22B, Qwen2.5-MoE, Llama 4, Kimi K2, gpt-oss. Artificial Analysis의 독립 리더보드에서 오픈소스 상위 10개 모델은 전부 MoE입니다.

## 개념

![MoE 레이어: 라우터가 토큰마다 E명의 전문가 중 k명을 선택](../assets/moe.svg)

### FFN 교체하기

덴스 트랜스포머 블록:

```
h = x + attn(norm(x))
h = h + FFN(norm(h))
```

MoE 블록:

```
h = x + attn(norm(x))
scores = router(norm(h))              # (N_tokens, E)
top_k = argmax_k(scores)              # 토큰마다 E명 중 k명 선택
h = h + sum_{e in top_k}(
        gate(scores[e]) * Expert_e(norm(h))
    )
```

모든 전문가는 독립적인 FFN입니다(보통 SwiGLU). 라우터는 선형 레이어 하나입니다. 각 토큰은 자기만의 `k`명 전문가를 고르고, 그 출력들을 게이트 가중치로 섞은 결과를 받습니다.

### 부하 분산 문제

라우터가 토큰의 90%를 3번 전문가에게 보내면 나머지 전문가들은 굶습니다. 시도된 해법은 세 가지입니다:

1. **보조 부하 분산 손실(auxiliary load-balancing loss)**(Switch Transformer, Mixtral). 전문가 사용량의 분산에 비례하는 벌점을 더합니다. 동작하지만 하이퍼파라미터와 두 번째 그래디언트 신호가 추가됩니다.
2. **전문가 용량 + 토큰 버리기(token dropping)**(초기 Switch). 각 전문가는 최대 `C × N/E`개 토큰만 처리하고, 넘치는 토큰은 이 레이어를 건너뜁니다. 품질이 떨어집니다.
3. **보조 손실 없는 균형(auxiliary-loss-free balancing)**(DeepSeek-V3). 학습된 전문가별 편향(bias)을 추가해 라우터의 top-k 선택을 조정합니다. 편향은 학습 손실 바깥에서 갱신됩니다. 본 목적 함수에는 벌점이 없습니다. 2024년의 큰 돌파구입니다.

DeepSeek-V3 방식: 학습 스텝마다 모든 전문가의 사용량이 목표보다 높은지 낮은지 확인하고, 편향을 `±γ`만큼 조금씩 움직입니다. 선택에는 `scores + bias`를 쓰고, 게이팅에 쓰는 전문가 확률은 원본 `scores` 그대로입니다. 라우팅과 표현을 분리하는 것이죠.

### 공유 전문가

DeepSeek-V2/V3는 전문가를 *공유(shared)*와 *라우티드(routed)*로 나눕니다. 모든 토큰은 공유 전문가를 전부 통과합니다. 라우티드 전문가는 top-k로 고릅니다. 공유 전문가는 공통 지식을 담고, 라우티드 전문가는 특화됩니다. V3는 공유 전문가 1명 + 256명 중 top-8 라우팅으로 동작합니다.

### 세밀한(fine-grained) 전문가

고전적 MoE(GShard, Switch): 각 전문가가 풀 FFN만 하게 넓습니다. `E`는 작고(8~64), `k`도 작습니다(1~2).

현대의 세밀한 MoE(DeepSeek-V3, Qwen-MoE): 각 전문가가 더 좁습니다(FFN 크기의 1/8). `E`는 크고(256+), `k`도 큽니다(8+). 총 파라미터는 같아도 조합 수가 훨씬 빠르게 늘어납니다. 토큰 하나당 가능한 '전문가' 조합이 `C(256, 8) = 400조`입니다. 품질은 올라가고 지연 시간은 그대로입니다.

### 비용 프로필

토큰 하나, 레이어 하나 기준:

| 설정 | 토큰당 활성 파라미터 | 전체 파라미터 |
|--------|-----------------------|--------------|
| Mixtral 8×22B | ~39B | 141B |
| Llama 3 70B (덴스) | 70B | 70B |
| DeepSeek-V3 | 37B | 671B |
| Kimi K2 (MoE) | ~32B | 1T |

DeepSeek-V3는 **토큰당 활성 FLOPs가 더 적으면서도** 거의 모든 벤치마크에서 덴스 Llama 3 70B를 이깁니다. 파라미터가 많을수록 지식이 많아집니다. 활성 FLOPs가 많을수록 토큰당 연산이 많아집니다. MoE는 이 둘을 분리합니다.

### 함정: 메모리

어떤 전문가가 동작하든 상관없이 모든 전문가가 GPU에 올라가 있어야 합니다. 671B 모델은 fp16 가중치만 약 1.3 TB의 VRAM이 필요합니다. 최전선 MoE 배포에는 전문가 병렬화(expert parallelism)가 필수입니다 — 전문가를 여러 GPU에 나눠 담고, 토큰을 네트워크 너머로 라우팅하죠. 지연 시간의 병목은 행렬 곱이 아니라 all-to-all 통신입니다.

```figure
expert-routing
```

## 만들어 보기

`code/main.py`를 보세요. 순수 표준 라이브러리만 쓴 컴팩트한 MoE 레이어입니다:

- `n_experts=8`개의 SwiGLU 비슷한 전문가(설명을 위해 각각 선형 하나)
- top-k=2 라우팅
- softmax로 정규화한 게이팅 가중치
- 전문가별 편향을 통한 보조 손실 없는 균형

### 단계 1: 라우터

```python
def route(hidden, W_router, top_k, bias):
    scores = [sum(h * w for h, w in zip(hidden, W_router[e])) for e in range(len(W_router))]
    biased = [s + b for s, b in zip(scores, bias)]
    top_idx = sorted(range(len(biased)), key=lambda i: -biased[i])[:top_k]
    # 선택된 전문가들의 원본 점수로 softmax 계산
    chosen = [scores[i] for i in top_idx]
    m = max(chosen)
    exps = [math.exp(c - m) for c in chosen]
    s = sum(exps)
    gates = [e / s for e in exps]
    return top_idx, gates
```

편향은 선택에만 영향을 주고 게이트 가중치에는 영향을 주지 않습니다. 이것이 DeepSeek-V3의 비결입니다 — 편향이 예측을 흔들지 않으면서 부하 불균형만 바로잡습니다.

### 단계 2: 토큰 100개를 라우터에 통과시키기

어떤 전문가가 얼마나 자주 동작하는지 기록합니다. 편향이 없으면 사용량이 치우칩니다. 편향 갱신 루프(과사용 전문가는 `-γ`, 과소사용 전문가는 `+γ`)를 돌리면 몇 번의 반복 만에 사용량이 균등 분포로 수렴합니다.

### 단계 3: 파라미터 수 비교

MoE 설정의 '덴스 등가물'을 출력합니다. DeepSeek-V3 형태: 라우티드 256 + 공유 1, 활성 8, d_model=7168. 총 파라미터 수는 어마어마합니다. 활성 수는 덴스 Llama 3 70B의 7분의 1입니다.

## 사용해 보기

HuggingFace 로딩:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("mistralai/Mixtral-8x22B-v0.1")
```

2026년 프로덕션 추론: vLLM은 MoE 라우팅을 기본 지원합니다. SGLang이 가장 빠른 전문가 병렬 경로를 제공합니다. 둘 다 top-k 선택과 전문가 병렬화를 자동으로 처리합니다.

**MoE를 고르면 좋은 경우:**
- 토큰당 추론 비용은 낮추면서 최전선 품질을 원할 때.
- VRAM / 전문가 병렬 인프라가 있을 때.
- 작업 부하가 컨텍스트보다 토큰 위주(채팅, 코드)일 때. (긴 문서처럼 컨텍스트 위주가 아닐 때)

**MoE를 고르지 말아야 하는 경우:**
- 엣지 배포 — 활성 FLOP이 얼마든 저장 공간 전체 값을 치러야 합니다.
- 지연 시간이 중요한 단일 사용자 서빙 — 전문가 라우팅이 오버헤드를 더합니다.
- 작은 모델(7B 미만) — MoE의 품질 이점은 연산 임계값(활성 파라미터 약 6B)을 넘어야 나타납니다.

## 출시하기

`outputs/skill-moe-configurator.md`를 보세요. 이 스킬은 파라미터 예산, 학습 토큰 수, 배포 대상이 주어지면 새 MoE의 E, k, 공유 전문가 구성을 정해 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 보조 손실 없는 편향 갱신이 50회 반복 동안 전문가 사용량을 어떻게 고르게 만드는지 관찰합니다.
2. **보통.** 학습되는 라우터를 해시 기반 라우터(결정론적, 학습 없음)로 바꿔 보세요. 품질과 균형을 비교합니다. 학습되는 라우터가 왜 더 나은가요?
3. **어려움.** GRPO 스타일의 '롤아웃 일치 라우팅'(DeepSeek-V3.2 비법)을 구현해 보세요: 추론 중 어떤 전문가가 동작했는지 기록하고, 그래디언트 계산 때 같은 라우팅을 강제합니다. 장난감 정책 그래디언트 설정에서 그 효과를 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 전문가(Expert) | "여러 FFN 중 하나" | 독립적인 피드포워드 네트워크; FFN 연산의 희소한 일부에 전담 배치된 파라미터. |
| 라우터(Router) | "관문" | 각 토큰을 각 전문가와 대조해 점수를 매기는 아주 작은 선형 레이어; top-k 선택. |
| Top-k 라우팅 | "토큰당 k명의 활성 전문가" | 각 토큰의 FFN 연산이 정확히 k명의 전문가를 게이트 가중치와 함께 통과. |
| 보조 손실(Auxiliary loss) | "부하 분산 벌점" | 치우친 전문가 사용량에 벌점을 주는 추가 손실 항. |
| 보조 손실 없음(Auxiliary-loss-free) | "DeepSeek-V3의 비법" | 라우터의 선택에만 전문가별 편향을 얹어 균형을 맞춤; 추가 그래디언트 없음. |
| 공유 전문가(Shared expert) | "항상 켜져 있음" | 모든 토큰이 통과하는 추가 전문가; 공통 지식을 담음. |
| 전문가 병렬화(Expert parallelism) | "전문가 단위로 샤딩" | 서로 다른 전문가를 서로 다른 GPU에 나눠 담고, 토큰을 네트워크 너머로 라우팅. |
| 희소성(Sparsity) | "활성 파라미터 < 전체 파라미터" | `k × expert_size / (E × expert_size)` 비율; DeepSeek-V3는 37/671 ≈ 5.5%. |

## 더 읽을거리

- [Shazeer 외 (2017). Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer](https://arxiv.org/abs/1701.06538) — 아이디어의 원조.
- [Fedus, Zoph, Shazeer (2022). Switch Transformer: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961) — 고전적 MoE인 Switch.
- [Jiang 외 (2024). Mixtral of Experts](https://arxiv.org/abs/2401.04088) — Mixtral 8×7B.
- [DeepSeek-AI (2024). DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) — MLA + 보조 손실 없는 MoE + MTP.
- [Wang 외 (2024). Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts](https://arxiv.org/abs/2408.15664) — 편향 기반 균형 논문.
- [Dai 외 (2024). DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](https://arxiv.org/abs/2401.06066) — 이 레슨의 라우터가 쓰는 세밀한 전문가 + 공유 전문가 분할.
- [Kim 외 (2022). DeepSpeed-MoE: Advancing Mixture-of-Experts Inference and Training](https://arxiv.org/abs/2201.05596) — 공유 전문가의 원조 논문.
