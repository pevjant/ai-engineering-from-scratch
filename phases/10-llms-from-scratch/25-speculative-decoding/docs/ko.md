> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 스페큘레이티브 디코딩과 EAGLE

> 프론티어 LLM이 토큰 하나를 만들려면 수십억 개 파라미터를 통과하는 순전파 한 번이 필요합니다. 그런데 이 순전파는 심하게 남는 살림입니다. 대부분의 경우 훨씬 작은 모델이 다음 3~5개 토큰을 맞히고, 큰 모델은 그 추측을 *검증*만 하면 됩니다. 추측이 맞으면 1개 값으로 5개 토큰을 얻는 셈입니다. 스페큘레이티브 디코딩(Leviathan 외 2023)은 이 아이디어를 정확하게 만들었고, EAGLE-3(2025)는 검증 1회당 약 4.5토큰의 수용률까지 끌어올렸습니다. 같은 출력 분포를 유지한 채 4~5배 속도 향상입니다.

**유형:** Build
**언어:** Python (numpy 포함)
**선수 지식:** 페이즈 10 레슨 12 (추론 최적화), 페이즈 10 레슨 04 (사전학습 미니-GPT)
**시간:** 약 75분

## 문제 상황

H100에서 70B급 모델의 디코드 처리량은 보통 초당 40~80토큰입니다. 토큰 하나마다 모델 가중치 전부를 HBM에서 읽는 순전파 한 번이 필요합니다. 출력을 바꾸지 않고 모델을 더 작게 만들 수도 없고, 메모리를 넘어 배치 크기를 늘릴 수도 없습니다. 막혀 있는 겁니다. 순전파 한 번에 토큰을 하나 이상 출력하게 할 수 있다면 이야기가 달라집니다.

자기회귀 생성은 본질적으로 직렬처럼 보입니다. `x_{t+1} = sample(p(· | x_{1:t}))`. 하지만 동시성의 기회가 숨어 있습니다. "다음 4개 토큰은 아마 [a, b, c, d]"라고 말해 주는 값싼 예측기가 있다면, 큰 모델의 **순전파 단 한 번**으로 5개 위치를 모두 검증하고 가장 긴 일치 접두사를 받아들일 수 있습니다.

Leviathan, Kalai, Matias(2023, "Fast Inference from Transformers via Speculative Decoding")는 타깃 모델의 샘플링 분포를 보존하는 영리한 수용/거부 규칙으로 이것을 정확하게 만들었습니다. 같은 출력 분포로 2~4배 빠릅니다.

## 개념

### 두 모델 구성

- **타깃 모델** `M_p`: 실제로 샘플을 얻고 싶은 크고 느리고 품질 좋은 모델. 분포: `p(x)`.
- **드래프트 모델** `M_q`: 작고 빠르고 품질이 낮은 모델. 분포: `q(x)`. 5~30배 작음.

단계당:

1. 드래프트 모델이 `K`개 토큰을 자기회귀적으로 제안합니다: `x_1, x_2, ..., x_K ~ q`.
2. 타깃 모델이 `K+1`개 위치 전체를 병렬로 순전파 한 번에 통과하며, 제안된 각 토큰에 대한 `p(x_k)`를 만들어 냅니다.
3. 아래의 변형된 기각 샘플링 규칙으로 각 토큰을 왼쪽에서 오른쪽으로 수용/거부합니다. 가장 긴 일치 접두사를 받아들입니다.
4. 거부된 토큰이 있으면 교정된 분포에서 대체 토큰을 샘플링하고 멈춥니다. 없다면 `p(· | x_1...x_K)`에서 보너스 토큰 하나를 샘플링합니다.

드래프트가 타깃과 완벽히 일치하면 타깃 순전파당 K+1개 토큰을 얻습니다. 첫 위치에서 드래프트가 틀리면 1토큰만 얻습니다.

### 정확성 규칙

스페큘레이티브 디코딩은 **p에서 샘플링하는 것과 분포가 동일함이 증명 가능**합니다. 기각 규칙:

```
For each drafted token x_t:
    r ~ Uniform(0, 1)
    if r < p(x_t) / q(x_t):
        accept x_t
    else:
        sample replacement from residual: (p - q)+ / ||(p - q)+||_1
        stop
```

여기서 `(p - q)+`는 원소별 차이의 양수 부분입니다. 드래프트와 타깃이 일치하면(`p ≈ q`) 수용률은 거의 1입니다. 불일치하더라도 잔차 분포가 그 전체 샘플이 여전히 정확히 `p`가 되도록 만들어 줍니다.

**그리디(탐욕) 경우.** temperature=0 샘플링에서는 `argmax(p) == x_t`만 확인하면 됩니다. 맞으면 수용, 틀리면 `argmax(p)`를 출력하고 멈춥니다.

### 기대 속도 향상

드래프트 모델의 토큰별 수용률이 `α`라면, 타깃 순전파 1회당 기대 토큰 수는:

```
E[tokens] = (1 - α^{K+1}) / (1 - α)        # K = draft length, α in [0, 1]
```

`α = 0.8, K = 4`일 때: `(1 - 0.8^5)/(1 - 0.8) = 3.36`토큰/순전파. 타깃 순전파 한 번의 비용은 대략 `cost_q * K + cost_p`(드래프트 K단계 + 타깃 검증 1회)입니다. `cost_p >> cost_q * K`라면 처리량 속도 향상은 `3.36× / 1 = 3.36×`입니다.

진짜 파라미터는 `α` 하나뿐이고, 이는 전적으로 드래프트-타깃 정합성에 달려 있습니다. 좋은 드래프트가 전부입니다.

### 드래프트 학습: 증류

무작위로 고른 작은 모델은 형편없는 드래프트입니다. 표준 레시피는 타깃에서 증류하는 것입니다:

1. 작은 아키텍처를 고릅니다(70B 타깃에는 약 1B, 7B 타깃에는 약 500M).
2. 큰 텍스트 코퍼스에서 타깃 모델을 돌리고, 다음 토큰 분포를 저장합니다.
3. 타깃의 분포를 정답 토큰이 아니라 기준으로 삼아, KL 발산으로 드래프트를 학습시킵니다.

결과: 코딩에서 `α`는 보통 0.6~0.8, 자연어 채팅에서 0.7~0.85. 프로덕션에서 2~3배 속도 향상.

### EAGLE: 트리 드래프팅 + 특징 재사용

Li, Wei, Zhang, Zhang(2024, "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty")은 표준 스페큘레이티브 디코딩에서 두 가지 비효율을 발견했습니다:

1. 드래프트는 K번의 직렬 단계를 밟는데, 각 단계가 풀 스택입니다. 그런데 드래프트는 가장 최근 검증에서 타깃의 특징(은닉 상태)을 재사용할 수 있습니다. 타깃이 이미 풍부한 표현을 계산해 뒀는데 드래프트가 그것을 처음부터 다시 유도하고 있는 것입니다.
2. 드래프트는 직선 사슬을 출력합니다. 만약 드래프트가 후보들의 *트리*를 출력할 수 있다면(각 노드가 여러 추측), 타깃의 단일 순전파가 트리 어텐션 마스크로 여러 후보 경로를 병렬로 검증하고 가장 긴 수용 분기를 고를 수 있습니다.

EAGLE-1의 변화:
- 드래프트 입력 = 원시 토큰이 아니라 위치 t에서 타깃의 최종 은닉 상태.
- 드래프트 아키텍처 = 별도의 작은 모델이 아니라 트랜스포머 디코더 레이어 1개.
- 출력 = 깊이당 K = 4~8개 후보의 트리, 깊이 4~6.

EAGLE-2(2024)는 동적 트리 토폴로지를 더합니다. 드래프트가 불확실한 곳에서는 트리가 넓어지고 확신하는 곳에서는 좁게 유지됩니다. 검증 비용을 늘리지 않고 `α_effective`를 끌어올립니다.

EAGLE-3(Li 외 2025, "EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test")은 고정된 최상위 레이어 특징 의존성을 제거하고, 드래프트를 새로운 "테스트 시 시뮬레이션(test-time simulation)" 손실로 학습시킵니다. 드래프트는 교사 강제(teacher-forcing) 학습 분포가 아니라 타깃의 테스트 시 분포와 일치하는 출력으로 학습됩니다. 수용률이 0.75(EAGLE-2)에서 0.82(EAGLE-3)로 올라가고, 검증당 평균 토큰 수는 3.0에서 4.5로 늘어납니다.

### 트리 어텐션 검증

드래프트가 트리를 출력하면, 타깃 모델은 **트리 어텐션 마스크**로 단일 순전파 안에서 그것을 검증합니다. 순수한 직선이 아니라 트리 토폴로지를 인코딩하는 인과 마스크입니다. 각 토큰은 트리에서 자기 조상들만 봅니다. 검증 패스는 여전히 순전파 한 번, 행렬 곱 한 번입니다. 토폴로지 마스크는 KV 항목 몇 개만 추가로 소모합니다.

```
        root
       /    \
      a      b
     / \    / \
    c  d   e   f
```

`a, b`가 경쟁하는 첫 토큰 후보이고 `c, d, e, f`가 두 번째 토큰 후보라면, 여섯 위치가 모두 한 번의 순전파로 검증됩니다. 출력은 수용된 경로 중 가장 긴 접두사입니다.

### 이기는 경우, 지는 경우

**이깁니다:**
- 예측 가능한 텍스트(코드, 흔한 영어, 구조화된 출력)의 채팅/완성. `α`가 높습니다.
- 디코드 중 GPU 연산력이 놀고 있는 환경(메모리 병목 페이즈). 트리 드래프팅이 남는 FLOPs를 씁니다.

**지거나 이득 없음:**
- 매우 확률적인 출력(높은 temperature의 창작 글쓰기). `α`가 `1/|vocab|` 쪽으로 떨어집니다.
- 매우 높은 동시성의 배치 서빙. 배칭이 이미 FLOPs를 채우기 때문에 트리 검증에 남을 여유가 거의 없습니다.
- 드래프트가 그다지 작지 않은 매우 작은 타깃 모델.

프로덕션 현장의 보고는 대체로 이렇습니다. 채팅에서 2~3배 실제 시간 속도 향상, 코드 생성에서 3~5배, 창작 글쓰기에서는 거의 0.

```figure
speculative-decoding
```

## 만들어 보기

`code/main.py`:

- 정확한 기각 규칙을 구현하고 타깃 분포를 보존하는지 검증하는(일반 타깃 샘플링 대비 경험적 KL < 0.01) 참조용 `speculative_decode(target, draft, prompt, K, temperature)`.
- top-p 분기로 깊이-K 트리를 만드는 EAGLE 스타일 트리 드래프터.
- 검증기에 맞는 인과 패턴을 만들어 주는 트리 어텐션 마스크 빌더.
- 두 방식 모두를 아주 작은 LM(1B 미만)에서 돌려 보는 수용률 하네스(GPT-2-medium 타깃에서 GPT-2-small 하나를 증류).

```python
def speculative_step(p_target, q_draft, K, temperature=1.0):
    """스페큘레이티브 디코딩 한 라운드. 수용된 토큰 리스트를 반환합니다."""
    # 1. K개 토큰을 드래프트
    draft_tokens = []
    q_probs = []
    state = draft_state_init()
    for _ in range(K):
        probs = softmax(q_draft(state) / temperature)
        t = np.random.choice(len(probs), p=probs)
        draft_tokens.append(t)
        q_probs.append(probs[t])
        state = draft_step(state, t)

    # 2. 타깃이 드래프트된 모든 위치에서 p를 계산 + 1개 추가
    p_probs_all = target_forward_batched(p_target, draft_tokens, temperature)

    # 3. 왼쪽에서 오른쪽으로 수용/거부
    accepted = []
    for k, tok in enumerate(draft_tokens):
        r = np.random.uniform()
        if r < p_probs_all[k][tok] / q_probs[k]:
            accepted.append(tok)
        else:
            residual = np.maximum(p_probs_all[k] - q_probs[k], 0)
            residual /= residual.sum()
            accepted.append(np.random.choice(len(residual), p=residual))
            return accepted
    # 4. K개 전부 수용 → 타깃에서 보너스 토큰 샘플링
    accepted.append(np.random.choice(len(p_probs_all[-1]), p=p_probs_all[-1]))
    return accepted
```

## 사용해 보기

- **vLLM**과 **SGLang**은 1급 스페큘레이티브 디코딩을 탑재합니다. 플래그: `--speculative_model`, `--num_speculative_tokens`. `--spec_decoding_algorithm eagle` 플래그로 EAGLE-2/3를 지원합니다.
- **NVIDIA TensorRT-LLM**은 Medusa와 EAGLE 트리를 네이티브로 지원합니다.
- **참조 드래프트 모델**: `Qwen/Qwen3-0.6B-spec`(Qwen3-32B용 드래프트), `meta-llama/Llama-3.2-1B-Instruct-spec`(70B용 드래프트).
- **Medusa 헤드**(Cai 외 2024, "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads"): 드래프트 모델 대신 타깃 자체에 K개의 병렬 예측 헤드를 붙입니다. 배포가 더 간단하지만 수용률은 EAGLE보다 약간 낮습니다.

## 출시하기

이 레슨은 `outputs/skill-speculative-tuning.md`를 산출합니다. 타깃 모델의 작업 부하를 프로파일링하고 다음을 선택하는 스킬입니다: 드래프트 모델, K(드래프트 길이), 트리 너비, temperature, 그리고 언제 평범한 디코딩으로 폴백할지.

## 연습 문제

1. 정확한 기각 규칙을 구현하고 경험적으로 검증하세요. `speculative_decode`와 일반 타깃 샘플링으로 각각 1만 개 샘플을 실행하고, 두 출력 분포 사이의 TV 거리를 계산하세요. 0.01 미만이어야 합니다.

2. 속도 향상 공식을 계산하세요. 고정된 `α`와 `K`에 대해 타깃 순전파당 기대 토큰 수를 그래프로 그리세요. α ∈ {0.5, 0.7, 0.9} 각각에 대한 최적 K를 찾으세요.

3. 아주 작은 드래프트를 학습시키세요. 124M GPT-2 타깃을 잡고, 1억 토큰으로 KL 손실로 30M GPT-2 드래프트를 증류하세요. 홀드아웃 텍스트에서 `α`를 측정하세요. 기대치: 0.6~0.7.

4. EAGLE 스타일 트리 드래프팅을 구현하세요. 사슬 대신 각 깊이에서 top-3 분기를 출력하게 하세요. 트리 어텐션 마스크를 만들고, 타깃이 가장 긴 올바른 분기를 수용하는지 검증하세요.

5. 실패 모드를 측정하세요. temperature=1.5(높은 확률성)로 스펙 디코드를 실행하세요. α가 무너지고 드래프트 오버헤드 때문에 알고리즘이 평범한 디코딩보다 느려지는 것을 보여주세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| Target model | "큰 모델" | 샘플을 얻고 싶은 느리고 고품질인 모델(p 분포) |
| Draft model | "스페큘레이터" | 작고 빠른 예측기(q 분포). 5~30배 작음 |
| K / draft length | "미리 보기" | 검증 패스당 추측(speculate)하는 토큰 수 |
| α / acceptance rate | "적중률" | 드래프트의 제안이 수용될 토큰별 확률 |
| Exact rejection rule | "수용 검사" | 타깃 분포를 보존하는 r < p/q 비교 |
| Residual distribution | "교정된 p-q" | (p - q)+ / ||(p - q)+||_1. 거부 시 샘플링할 분포 |
| Tree drafting | "분기하는 추측" | 드래프트가 후보 트리를 출력하고, 트리 구조 어텐션 마스크로 한 번에 검증 |
| Tree attention mask | "토폴로지 마스크" | 트리 토폴로지를 인코딩해 각 노드가 자기 조상만 보게 하는 인과 마스크 |
| Medusa heads | "병렬 헤드" | 타깃 자체에 붙는 K개의 추가 예측 헤드. 별도 드래프트 모델 불필요 |
| EAGLE feature reuse | "은닉 상태 드래프트" | 드래프트 입력이 원시 토큰이 아니라 타깃의 마지막 은닉 상태여서 드래프트가 작아짐 |
| Test-time simulation loss | "EAGLE-3 학습" | 교사 강제가 아니라 타깃의 테스트 시 분포와 일치하는 출력으로 드래프트를 학습 |

## 더 읽을거리

- [Leviathan, Kalai, Matias, 2023 — "Fast Inference from Transformers via Speculative Decoding"](https://arxiv.org/abs/2211.17192) — 정확한 기각 규칙과 이론적 속도 향상 분석
- [Chen, Borgeaud, Irving 외, 2023 — "Accelerating Large Language Model Decoding with Speculative Sampling"](https://arxiv.org/abs/2302.01318) — DeepMind에서 동시에 나온 스페큘레이티브 샘플링 논문
- [Cai, Li, Geng, Wang, Wang, Zhu, Dao, 2024 — "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads"](https://arxiv.org/abs/2401.10774) — 드래프트 모델의 병렬 헤드 대안
- [Li, Wei, Zhang, Zhang, 2024 — "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty"](https://arxiv.org/abs/2401.15077) — 특징 재사용과 트리 드래프팅
- [Li 외, 2024 — "EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees"](https://arxiv.org/abs/2406.16858) — 동적 트리 토폴로지
- [Li 외, 2025 — "EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test"](https://arxiv.org/abs/2503.01840) — 학습 시-테스트 시 매칭
- [Fu, Haotian, Peng 외, 2024 — "Break the Sequential Dependency of LLM Inference Using Lookahead Decoding"](https://arxiv.org/abs/2402.02057) — Jacobi/lookahead 디코딩. 스페큘레이터 없는 대안
