> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 투기적 디코딩 — 드래프트, 검증, 반복

> 자기회귀 디코딩은 직렬입니다. 토큰마다 이전 토큰을 기다려야 하죠. 투기적 디코딩은 이 사슬을 끊습니다: 값싼 모델이 토큰 N개를 드래프트하고, 비싼 모델이 N개를 순전파 한 번으로 검증합니다. 드래프트가 맞았다면 N개 생성에 큰 순전파 한 번 값을 냈을 뿐입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 7 · 07(GPT 인과 LM), 페이즈 7 · 12(KV 캐시 & Flash Attention)
**시간:** 약 60분

## 문제 상황

70B LLM이 토큰 하나를 샘플링하는 데 H100에서 약 30 ms가 걸립니다. 3B 드래프트 모델은 약 3 ms입니다. 3B 모델이 5토큰 앞서 드래프트하게 한 뒤 70B 모델을 딱 *한 번* 돌려 5개를 모두 검증하면, 총 시간은 `5×3 + 30 = 45 ms`로 최대 5토큰을 받아들입니다 — 직진 생성의 `5×30 = 150 ms`와 비교하면요. 이것이 투기적 디코딩의 모든 것입니다: 약간의 추가 GPU 메모리(드래프트 모델)를 치르고 디코딩 지연 시간을 2~4배 줄입니다.

단, 이 트릭은 분포를 보존해야 합니다. Leviathan 외(2023)가, 그리고 같은 시기에 Chen 외가 소개한 투기적 샘플링(speculative sampling)은 출력 시퀀스가 큰 모델이 혼자 만들었을 결과와 **동일한 분포**임을 보장합니다. 품질 트레이드오프가 없습니다. 그저 빨라질 뿐입니다.

2026년 추론을 지배하는 드래프트-검증 조합은 네 계열입니다:

1. **기본 투기적 디코딩(Leviathan 2023).** 별도의 드래프트 모델(예: Llama 3 1B) + 검증자(예: Llama 3 70B).
2. **Medusa(Cai 2024).** 검증자에 여러 디코딩 헤드를 두고 위치 `t+1..t+k`를 병렬로 예측합니다. 별도의 드래프트 모델이 없습니다.
3. **EAGLE 계열(Li 2024, 2025).** 검증자의 은닉 상태를 재사용하는 가벼운 드래프트; 기본 방식보다 수락률이 높고 보통 3~4배입니다.
4. **Lookahead 디코딩(Fu 2024).** 야코비 반복; 드래프트 모델이 전혀 필요 없습니다. 자기 투기(self-speculation)죠. 틈새지만 의존성이 없습니다.

2026년 모든 프로덕션 추론 스택은 투기적 디코딩을 기본 탑재합니다. vLLM, TensorRT-LLM, SGLang, llama.cpp가 모두 최소 기본 방식 + EAGLE-2를 지원합니다.

## 개념

### 핵심 알고리즘

검증자 `M_q`와 더 값싼 드래프트 `M_p`가 주어졌을 때:

1. 이미 디코딩된 접두사를 `x_1..x_k`라 둡니다.
2. **드래프트**: `M_p`로 자기회귀적으로 `d_{k+1}, d_{k+2}, ..., d_{k+N}`을 드래프트 확률 `p_1..p_N`과 함께 제안합니다.
3. **병렬 검증**: `M_q`를 `x_1..x_k, d_{k+1}, ..., d_{k+N}`에 한 번 돌려 위치 `k+1..k+N+1`의 검증자 확률 `q_1..q_{N+1}`을 얻습니다.
4. **드래프트 토큰을 왼쪽부터 차례로 수락/거절**: 각 `i`마다 확률 `min(1, q_i(d_i) / p_i(d_i))`로 수락합니다.
5. 위치 `j`에서 처음 거절되면: '잔여(residual)' 분포 `(q_j - p_j)_+`를 정규화한 것에서 `t_j`를 샘플링합니다. `j` 뒤의 모든 드래프트는 버립니다.
6. `N`개를 모두 수락했다면: `q_{N+1}`에서 토큰 하나를 더 샘플링합니다(공짜 보너스 토큰).

이 잔여 분포 트릭이 바로, 출력이 `M_q`가 처음부터 샘플링한 것과 정확히 같은 분포가 되게 만드는 수학적 통찰입니다.

### 속도 향상을 결정하는 것

`α` = 드래프트 토큰당 기대 수락률. `c` = 드래프트 대비 검증 비용 비율. 스텝당:

- 순진한 생성은 토큰당 큰 모델 호출 1번.
- 투기적 디코딩은 `α`가 높을 때 `(1 - α^{N+1}) / (1 - α) ≈ 1/(1-α)`개 토큰마다 큰 모델 호출 1번.

`α = 0.75`, `N = 5`일 때의 경험 법칙: 큰 모델 호출이 3배 줄어듭니다. 드래프트 비용은 5배 쌉니다(값쌉니다). 총 벽시계 시간은 약 2.5배 줄어듭니다.

**α는 다음에 달렸습니다:**

- 드래프트가 검증자를 얼마나 잘 근사하는지. 같은 계열 / 같은 학습 데이터면 α가 크게 올라갑니다.
- 디코딩 전략. 그리디 드래프트 vs 그리디 검증자: α가 높습니다. 온도 샘플링: 맞추기 어렵고 수락률이 떨어집니다.
- 과제 유형. 코드와 구조화된 출력은 잘 수락되고(예측 가능), 자유로운 창작 글쓰기는 덜 수락됩니다.

### Medusa — 드래프트 모델 없이 드래프트하기

Medusa는 드래프트 모델을 검증자의 추가 출력 헤드로 대체합니다. 위치 `t`에서:

```
shared trunk → hidden h_t
    ├── head_0: predict token at t+1  (standard LM head)
    ├── head_1: predict token at t+2
    ├── head_2: predict token at t+3
    ├── head_3: predict token at t+4
```

각 헤드는 자신의 로짓을 냅니다. 추론 때는 각 헤드에서 샘플링해 후보 시퀀스를 만들고, 모든 후보 이어지기(continuation)를 한꺼번에 고려하는 트리 어텐션 방식으로 순전파 한 번에 검증합니다.

장점: 두 번째 모델이 없습니다. 단점: 학습되는 파라미터가 늘고; 지도 파인튜닝 단계가 필요합니다(약 1B 토큰); 좋은 드래프트를 쓰는 기본 투기 방식보다 수락률이 조금 낮습니다.

### EAGLE — 은닉 상태를 재사용하는 더 나은 드래프트

EAGLE-1/2/3(Li 외, 2024~2025)은 드래프트 모델을, 검증자의 마지막 층 은닉 상태를 입력받는 아주 작은 트랜스포머(보통 1층)로 만듭니다. 드래프트가 검증자의 특성 표현을 보기 때문에, 예측이 검증자의 출력 분포와 강하게 상관됩니다. 수락률이 약 0.6(기본 방식)에서 0.85 이상으로 올라갑니다.

EAGLE-3(2025)은 후보 이어지기에 대한 트리 탐색을 더했습니다. vLLM과 SGLang은 Llama 3/4와 Qwen 3의 기본 투기 경로로 EAGLE-2/3을 탑재합니다.

### KV 캐시 춤

검증은 `N`개 드래프트 토큰을 검증자에 순전파 한 번으로 넣습니다. 이러면 검증자의 KV 캐시가 `N`개 항목만큼 늘어납니다. 드래프트 일부가 거절되면 캐시를 수락된 접두사 길이로 되돌려야(rollback) 합니다.

프로덕션 구현(vLLM의 `--speculative-model`, TensorRT-LLM의 LookaheadDecoder)은 스크래치 KV 버퍼로 이를 처리합니다. 먼저 쓰고, 수락되면 커밋합니다. 개념적으로 어렵지는 않지만 손이 많이 갑니다.

```figure
draft-verify-tokens
```

## 만들어 보기

`code/main.py`를 보세요. 핵심 투기적 샘플링 알고리즘(거절 스텝 + 잔여 분포)을 다음과 함께 구현합니다:

- 손으로 코딩한 분포 위의 결정론적 softmax인 '큰 모델'(수락 수학을 해석적으로 검증할 수 있게).
- 큰 모델을 살짝 흔든(perturbation) '드래프트 모델'.
- 직접 샘플링과 같은 주변 분포를 내놓는 수락/거절 루프.

### 단계 1: 거절 스텝

```python
def accept_or_reject(q_prob, p_prob, draft_token, u):
    ratio = q_prob / p_prob if p_prob > 0 else float("inf")
    return u < min(1.0, ratio)
```

`u`는 균등 난수입니다. `q_prob`는 드래프트된 토큰에 대한 검증자의 확률, `p_prob`는 드래프트 모델의 확률입니다. Leviathan 정리는 바로, 이 베르누이 판정 뒤에 거절 시 잔여 분포에서 샘플링하면 검증자의 분포가 정확히 보존된다는 것입니다.

### 단계 2: 잔여 분포

```python
def residual_dist(q, p):
    raw = [max(0.0, qi - pi) for qi, pi in zip(q, p)]
    s = sum(raw)
    return [r / s for r in raw]
```

`q`에서 `p`를 원소별로 빼고, 음수는 0으로 잘라내고, 다시 정규화합니다. 거절이 있을 때마다 여기서 샘플링합니다.

### 단계 3: 투기적 스텝 하나

```python
def spec_step(prefix, q_model, p_model, N, rng):
    drafts = []
    p_probs = []
    ctx = list(prefix)
    for _ in range(N):
        p_dist = p_model(ctx)
        d = sample(p_dist, rng)
        drafts.append(d)
        p_probs.append(p_dist[d])
        ctx.append(d)

    q_dists = [q_model(prefix + drafts[:i]) for i in range(N + 1)]

    for i, d in enumerate(drafts):
        u = rng.random()
        q_prob = q_dists[i][d]
        p_prob = p_probs[i]
        if u < min(1.0, q_prob / p_prob if p_prob > 0 else float("inf")):
            prefix = prefix + [d]
        else:
            res = residual_dist(q_dists[i], p_model(prefix))
            prefix = prefix + [sample(res, rng)]
            return prefix
    prefix = prefix + [sample(q_dists[N], rng)]
    return prefix
```

5개 수락 → 보너스 1개 → 검증자 패스 한 번에 토큰 6개가 나옵니다.

### 단계 4: 수락률 측정

드래프트 품질 수준을 바꿔 가며 투기적 스텝 10,000번을 실행합니다. 수락률 vs 드래프트-검증자 분포 간 KL 발산을 그려 보세요. 깔끔한 단조 관계가 보여야 합니다.

### 단계 5: 분포 동등성 검증

경험적으로: 투기적 루프가 만든 토큰 히스토그램은 검증자에서 직접 샘플링한 히스토그램과 일치해야 합니다. 이것이 실전 속 Leviathan 정리입니다. 카이제곱 검정이 샘플링 오차 범위 내에서 이를 확인합니다.

## 사용해 보기

프로덕션:

```bash
# vLLM with EAGLE
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-model /models/llama-3.1-eagle-70b \
    --speculative-draft-tensor-parallel-size 1 \
    --num-speculative-tokens 5

# vLLM with vanilla draft model
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-model meta-llama/Llama-3.2-1B-Instruct \
    --num-speculative-tokens 5
```

TensorRT-LLM은 2026년 중반 기준 가장 빠른 Medusa 경로를 제공합니다. `faster-whisper`는 작은 드래프트로 Whisper-large에 투기적 디코딩을 감싸 줍니다.

**드래프트 고르기:**

| 전략 | 고르는 시점 | 속도 향상 |
|----------|--------------|---------|
| 기본 드래프트(1B/3B Llama 계열) | 빠른 프로토타입, 학습 없음 | 1.8–2.3배 |
| Medusa 헤드 | 검증자를 파인튜닝할 수 있을 때 | 2–3배 |
| EAGLE-2 / 3 | 프로덕션, 최대 속도 | 3–4배 |
| Lookahead | 드래프트 없음, 학습 없음, 추가 파라미터 없음 | 1.3–1.6배 |

**투기적 디코딩을 쓰지 말아야 할 때:**

- 1~5토큰짜리 단일 시퀀스 생성. 오버헤드가 이깁니다.
- 극도로 창의적 / 고온도 샘플링(α가 떨어집니다).
- 메모리 제약 배포(드래프트 모델이 VRAM을 더 씁니다).

## 출시하기

`outputs/skill-spec-decode-picker.md`를 보세요. 이 스킬은 새 추론 작업 부하를 위해 투기적 디코딩 전략(기본 / Medusa / EAGLE / lookahead)과 튜닝 파라미터(N, 드래프트 온도)를 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 투기적 토큰 분포가 50,000토큰 기준 검증자의 직접 샘플링 분포와 카이제곱 p > 0.05 이내에서 일치하는지 확인합니다.
2. **보통.** `α = 0.5, 0.7, 0.85`에 대해 속도 향상(큰 모델 순전파당 토큰 수)을 `N`의 함수로 그립니다. 각 α의 최적 `N`을 찾으세요. (힌트: 검증 호출당 기대 토큰 수 = `(1 - α^{N+1}) / (1 - α)`.)
3. **어려움.** 아주 작은 Medusa를 구현해 보세요: 레슨 14의 캡스톤 GPT를 가져와 위치 t+2, t+3, t+4를 예측하는 LM 헤드 3개를 추가합니다. 다중 헤드 공동 손실로 tinyshakespeare를 학습합니다. 같은 모델을 잘라 만든 기본 드래프트와 수락률을 비교합니다.
4. **어려움.** 롤백을 구현해 보세요: 10토큰 접두사 KV 캐시로 시작하고, 드래프트 토큰 5개를 넣고, 위치 3에서 거절을 시뮬레이션합니다. 다음 반복에서 캐시 읽기가 '접두사 + 수락된 처음 2개 드래프트'와 정확히 일치하는지 확인합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 드래프트 모델 | "값싼 모델" | 후보 토큰을 제안하는 더 작은 모델; 보통 검증자보다 10~50배 쌉니다. |
| 검증자(Verifier) | "큰 모델" | 분포를 보존하려는 대상 모델; 투기적 스텝당 한 번 돕니다. |
| 수락률(α) | "드래프트가 맞는 빈도" | 검증자가 드래프트를 수락하는 토큰당 확률. 보통 0.7~0.9. |
| 잔여 분포 | "거절 시 폴백" | `(q - p)_+`를 정규화한 것; 거절 시 여기서 샘플링하면 검증자의 분포가 보존됩니다. |
| 보너스 토큰 | "공짜 토큰" | N개 드래프트를 모두 수락했을 때 검증자의 다음 단계 분포에서 하나를 더 샘플링. |
| Medusa | "드래프트 없는 투기 디코딩" | 검증자의 여러 LM 헤드가 위치 t+1..t+k를 병렬로 예측. |
| EAGLE | "은닉 상태 드래프트" | 검증자의 마지막 층 은닉 상태를 조건으로 삼는 아주 작은 트랜스포머 드래프트. |
| Lookahead 디코딩 | "야코비 반복" | 부동점 반복을 쓰는 자기 투기; 드래프트 모델이 없습니다. |
| 트리 어텐션 | "여러 후보를 한꺼번에 검증" | 여러 드래프트 이어지기를 동시에 고려하는 분기형 검증. |
| KV 롤백 | "거절된 드래프트 되돌리기" | 스크래치 KV 버퍼; 수락 시 커밋, 거절 시 버림. |

## 더 읽을거리

- [Leviathan, Kalman, Matias (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — 핵심 알고리즘과 동등성 정리.
- [Chen 외 (2023). Accelerating Large Language Model Decoding with Speculative Sampling](https://arxiv.org/abs/2302.01318) — 동시 소개; 깔끔한 베르누이 거절 증명.
- [Cai 외 (2024). Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774) — Medusa 논문; 트리 어텐션 검증.
- [Li 외 (2024). EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077) — EAGLE-1; 은닉 상태 조건 드래프트.
- [Li 외 (2024). EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees](https://arxiv.org/abs/2406.16858) — EAGLE-2; 동적 트리 깊이.
- [Li 외 (2025). EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test](https://arxiv.org/abs/2503.01840) — EAGLE-3.
- [Fu 외 (2024). Break the Sequential Dependency of LLM Inference Using Lookahead Decoding](https://arxiv.org/abs/2402.02057) — 드래프트 없는 lookahead 접근법.
- [vLLM 문서 — Speculative Decoding](https://docs.vllm.ai/en/latest/features/spec_decode.html) — 네 전략이 모두 연결된 정석 프로덕션 레퍼런스.
- [SafeAILab / EAGLE 레퍼런스 구현](https://github.com/SafeAILab/EAGLE) — EAGLE-1/2/3의 레퍼런스 코드.
