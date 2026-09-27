# GPT — 인과적 언어 모델링

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> BERT는 양쪽을 봅니다. GPT는 과거만 봅니다. 그 삼각형 마스크야말로 현대 AI에서 가장 영향력 큰 코드 한 줄입니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 7 · 02 (셀프 어텐션), 페이즈 7 · 05 (완전한 트랜스포머), 페이즈 7 · 06 (BERT)
**시간:** 약 75분

## 문제 상황

언어 모델은 질문 하나에 답합니다: 첫 `t-1`개 토큰이 주어졌을 때 토큰 `t`의 확률 분포는 무엇인가? 그 신호 — 다음 토큰 예측 — 로 학습하면 토큰을 하나씩 만들어 임의의 텍스트를 생성할 수 있는 모델이 나옵니다.

시퀀스 전체를 한꺼번에 병렬로 엔드투엔드 학습시키려면, 각 위치의 예측이 오직 앞선 위치에만 의존해야 합니다. 그렇지 않으면 모델이 정답을 몰래 훔쳐보고 말죠.

그 역할을 하는 게 인과 마스크(causal mask)입니다. 소프트맥스 전에 어텐션 점수에 더하는, `-inf` 값들의 위쪽 삼각형 행렬 하나입니다. 소프트맥스를 통과하면 그 위치들은 0이 됩니다. 각 위치는 자기 자신과 그보다 앞선 위치만 주시할 수 있죠. 그리고 시퀀스 전체에 한 번만 적용하면 되므로, 순전파 한 번으로 N개의 병렬 다음-토큰 예측을 얻습니다.

GPT-1(2018), GPT-2(2019), GPT-3(2020), GPT-4(2023), GPT-5(2025), Claude, Llama, Qwen, Mistral, DeepSeek, Kimi — 이들은 모두 같은 핵심 루프를 공유하는 디코더 전용 인과적 트랜스포머입니다. 이들을 가르는 것은 데이터 품질, 규모와 아키텍처 개선, 그리고 후처리 학습(SFT, RLHF, DPO와 그 후속 기법)입니다.

## 핵심 개념

![인과 마스크가 삼각형 어텐션 행렬을 만든다](../assets/causal-attention.svg)

### 마스크

길이 `N` 시퀀스가 주어지면 `N × N` 행렬을 만듭니다:

```
M[i, j] = 0       if j <= i
M[i, j] = -inf    if j > i
```

소프트맥스 전에 날 어텐션 점수에 `M`을 더합니다. `exp(-inf) = 0`이므로 마스크된 위치는 가중치 0을 기여합니다. 어텐션 행렬의 각 행은 오직 이전 위치들에 대한 확률 분포입니다.

구현 비용: `torch.tril()` 호출 한 번. 계산 시간: 나노초 단위. 분야에 미친 영향: 전부.

### 삼각형은 어디서 왔나

마스크는 보통 어텐션에 억지로 붙인 땜질로 소개됩니다. 유도를 반대 방향으로 돌리면 신비가 사라집니다: 어텐션은 접두사 평균(prefix average)의 세 번째 개선이고, 삼각형은 그 평균의 반복문 범위를 행렬로 적어 놓은 것입니다.

**1단계 — 접두사 평균.** 시퀀스를 요약하는 가장 단순한 인과적 방법: 위치 `i`가 위치 `0…i`의 평균이 됩니다. 반복문으로 쓰면 `out[i] = X[:i+1].mean(0)`입니다. 같은 계산을 행렬 곱셈 한 번으로 할 수 있습니다. 1로 채운 아래쪽 삼각형 행렬을 만들고, 각 행을 개수로 나눈 뒤 곱합니다:

```python
import numpy as np

A = np.tril(np.ones((n, n)))
A = A / A.sum(axis=1, keepdims=True)
out = A @ X
```

`A`의 행 `i`는 `[1/(i+1), …, 1/(i+1), 0, …, 0]`입니다. 대각선 위의 0이 곧 인과성입니다. 미래를 마스킹해 없앤 게 아닙니다. 애초에 합에 미래가 없었던 겁니다.

**2단계 — 학습되는 가중치.** 균등 평균은 모든 과거 토큰을 똑같이 관련 있다고 취급합니다. 1 대신 학습된 점수 행렬 `S`로 바꿉니다. 이제 행의 합이 구조적으로 1이 아니므로, 개수로 나누는 대신 각 행을 소프트맥스로 정규화합니다. 소프트맥스는 정확한 0을 내놓지 않는데, 이게 인과성을 깨뜨립니다 — 미래 점수가 `-inf`로 들어가서 `exp(-inf) = 0`이 되지 않는 한 말이죠:

```python
def softmax(x, axis):
    e = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e / e.sum(axis=axis, keepdims=True)

S = S + np.triu(np.full((n, n), -np.inf), k=1)
A = softmax(S, axis=1)
out = A @ X
```

같은 삼각형, 같은 행-확률 행렬, 같은 행렬 곱셈 하나. `-inf` 마스크는 새로운 장치가 아닙니다. 1단계의 0 성분들을 소프트맥스의 입력 영역으로 옮겨 적은 것입니다.

**3단계 — 내용 의존적 가중치.** 2단계에서 `S`는 학습 후 고정입니다: 위치 7은 토큰 내용과 무관하게 위치 3을 항상 같은 비중으로 봅니다. 점수가 토큰 자체에 의존하게 만들면: `S = Q @ K.T / sqrt(d_k)`. 나머지는 아무것도 바뀌지 않습니다. 마스크, 소프트맥스, 행렬 곱셈 — 똑같습니다.

세 단계, 하나의 불변식: 시퀀스에 아래쪽 삼각형 행-확률 행렬을 곱한다. 균등 평균, 학습된 정적 가중치, 내용 의존적 가중치. 마스크는 어텐션에 나중에 더해진 게 아니라 평균으로부터 살아남은 것입니다.

```figure
mask-derivation
```

### 병렬 학습, 직렬 추론

학습: `(N, d_model)` 시퀀스 전체를 순전파 한 번 돌리고, N개의 교차 엔트로피 손실(위치마다 하나)을 계산해 더한 뒤 역전파합니다. 시퀀스를 따라 병렬입니다. GPT 학습이 확장되는 이유가 이것입니다 — 100만 토큰을 배치 하나로 GPU 패스 한 번에 처리합니다.

추론: 토큰을 하나씩 만듭니다. `[t1, t2, t3]`을 넣어 `t4`를 받습니다. `[t1, t2, t3, t4]`를 넣어 `t5`를 받습니다. `[t1, t2, t3, t4, t5]`를 넣어 `t6`을 받습니다. KV 캐시(레슨 12)가 `t1…tn`의 은닉 상태를 저장해 매 단계 다시 계산하지 않게 해 줍니다. 하지만 추론의 직렬 깊이 = 출력 길이입니다. 이것이 자기회귀 세금이고, 디코딩이 모든 LLM의 지연 시간 병목인 이유입니다.

### 손실 — 한 칸 밀기(shift-by-one)

토큰 `[t1, t2, t3, t4]`가 주어졌을 때:

- 입력: `[t1, t2, t3]`
- 타깃: `[t2, t3, t4]`

모든 위치 `i`에서 `-log P(target_i | inputs[:i+1])`를 계산해 더합니다. 이것이 시퀀스 전체의 교차 엔트로피입니다.

여러분이 아는 모든 트랜스포머 언어 모델이 이 손실로 학습합니다. 사전 학습, 파인튜닝, SFT — 같은 손실, 다른 데이터일 뿐입니다.

### 디코딩 전략

학습 후에는 샘플링 선택이 사람들이 생각하는 것보다 중요합니다.

| 방법 | 하는 일 | 언제 쓰나 |
|--------|--------------|-------------|
| Greedy | 매 단계 argmax | 결정론적 과제, 코드 완성 |
| Temperature | 로짓을 T로 나눠 샘플링 | 창의적 과제, T가 높을수록 다양성 증가 |
| Top-k | 상위 k개 토큰에서만 샘플링 | 낮은 확률의 꼬리를 제거 |
| Top-p (nucleus) | 누적 확률 ≥ p가 되는 최소 집합에서 샘플링 | 2020년 이후 기본값; 분포 모양에 적응 |
| Min-p | `p > min_p * max_p`인 토큰만 유지 | 2024년 이후; 긴 꼬리 거절이 top-p보다 나음 |
| Speculative decoding | 드래프트 모델이 N개 토큰 제안, 큰 모델이 검증 | 같은 품질에서 지연 시간 2-3배 감소 |

2026년에는 오픈 웨이트 모델에 min-p + temperature 0.7이 무난한 기본값입니다. Speculative decoding은 프로덕션 추론 스택이라면 기본 소양입니다.

### "GPT 레시피"가 통한 이유

1. **디코더 전용.** 인코더 오버헤드가 없습니다. 층당 어텐션 + FFN 한 패스.
2. **스케일링.** 124M → 1.5B → 175B → 조 단위. Chinchilla 스케일링 법칙(레슨 13)이 연산량을 쓰는 법을 알려 줍니다.
3. **문맥 내 학습.** 대략 6B~13B 규모에서 떠올랐습니다. 모델이 파인튜닝 없이도 퓨샷 예제를 따를 수 있습니다.
4. **RLHF.** 사람 선호에 대한 후처리 학습이 날 사전 학습 모델을 챗 어시스턴트로 바꿨습니다.
5. **Pre-norm + RoPE + SwiGLU.** 큰 규모에서도 안정적인 학습.

핵심 아키텍처는 GPT-2 이후 크게 바뀌지 않았습니다. 흥미로운 일은 전부 데이터, 규모, 후처리 학습에서 일어났습니다.

```figure
causal-mask
```

## 만들어 보기

### 단계 1: 인과 마스크

`code/main.py`를 보세요. 한 줄입니다:

```python
def causal_mask(n):
    return [[0.0 if j <= i else float("-inf") for j in range(n)] for i in range(n)]
```

소프트맥스 전에 어텐션 점수에 더합니다. 메커니즘의 전부입니다.

### 단계 2: 2층짜리 GPT 비슷한 모델

디코더 블록 두 개(마스킹된 셀프 어텐션 + FFN, 크로스 어텐션 없음)를 쌓습니다. 토큰 임베딩, 위치 인코딩, 언임베딩(토큰 임베딩 행렬과 묶음 — GPT-2 이후의 표준 트릭)을 추가합니다.

### 단계 3: 다음 토큰 예측, 엔드투엔드

20토큰 장난감 어휘에서 모든 위치의 로짓을 만들어 냅니다. 한 칸 민 타깃에 대해 교차 엔트로피 손실을 계산합니다. 기울기는 없습니다 — 순전파 온전성 검사입니다.

### 단계 4: 샘플링

greedy, temperature, top-k, top-p, min-p를 구현합니다. 고정 프롬프트에 각각 돌려 출력을 비교합니다. 샘플링 함수는 10줄짜리입니다.

## 활용하기

PyTorch, 2026년 관용구:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")
tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")

prompt = "Attention is all you need because"
inputs = tok(prompt, return_tensors="pt")
out = model.generate(
    **inputs,
    max_new_tokens=64,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
)
print(tok.decode(out[0]))
```

내부적으로 `generate()`는 순전파를 돌리고, 마지막 위치의 로짓을 뽑아, 다음 토큰을 샘플링해, 이어 붙이고, 반복합니다. 모든 프로덕션 LLM 추론 스택(vLLM, TensorRT-LLM, llama.cpp, Ollama, MLX)이 같은 루프를 아주 세게 최적화해 구현합니다 — 배치 프리필(prefill), 연속 배칭, KV 캐시 페이징, speculative decoding 같은 것들이죠.

**GPT vs BERT, 한 줄 요약:** GPT는 `P(x_t | x_{<t})`를 예측합니다. BERT는 `P(x_masked | x_unmasked)`를 예측합니다. 손실이 모델이 생성할 수 있는지를 결정합니다.

## 출시하기

`outputs/skill-sampling-tuner.md`를 보세요. 이 스킬은 새로운 생성 과제에 샘플링 파라미터를 골라 주고, 결정론적 디코딩이 필요할 때 표시를 해 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 인과 어텐션 행렬이 소프트맥스 후 아래쪽 삼각형인지 검증합니다. 표본 확인: 3번째 행은 0~3번째 열에만 가중치가 있어야 합니다.
2. **보통.** 폭 4짜리 빔 서치(beam search)를 구현합니다. 짧은 프롬프트 10개에서 beam-4와 greedy의 퍼플렉시티를 비교합니다. 빔이 항상 이기나요? (힌트: 보통 번역에서는 그렇지만 열린 채팅에서는 그렇지 않습니다.)
3. **어려움.** Speculative decoding을 구현합니다: 2층짜리 작은 모델을 드래프트로, 6층 모델을 검증자로 씁니다. 길이 64짜리 완성 100건에 대해 벽시계 속도 향상을 측정하고, 출력이 검증자의 greedy 결과와 일치하는지 확인합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 인과 마스크 | "그 삼각형" | 위치 `i`가 `≤ i` 위치만 보도록 어텐션 점수에 더하는 위쪽 삼각형 `-inf` 행렬. |
| 다음 토큰 예측 | "그 손실" | 모든 위치에서 모델 분포와 실제 다음 토큰 사이의 교차 엔트로피. |
| 자기회귀 (Autoregressive) | "하나씩 생성한다" | 출력을 다시 입력으로 먹인다; 병렬화는 학습 때만 되고 생성 때는 안 된다. |
| 로짓 (Logits) | "소프트맥스 전 점수" | 소프트맥스 전 LM 헤드의 날 출력; 샘플링은 이 위에서 일어난다. |
| Temperature | "창의성 손잡이" | 로짓을 T로 나눈다; T→0 = greedy, T→∞ = 균등. |
| Top-p | "nucleus 샘플링" | 합이 ≥p인 최소 집합으로 분포를 잘라 그 안에서 샘플링한다. |
| Min-p | "top-p보다 나은 것" | `p ≥ min_p × max_p`인 토큰만 유지; 절단 기준이 분포의 뾰족함에 맞춰 조정된다. |
| Speculative decoding | "초안 + 검증" | 값싼 모델이 N개 토큰을 제안하고 큰 모델이 병렬로 검증한다. |
| Teacher forcing | "학습 트릭" | 학습 중 모델의 예측이 아니라 실제 이전 토큰을 먹인다. 모든 seq2seq LM의 표준. |

## 더 읽을거리

- [Radford et al. (2018). Improving Language Understanding by Generative Pre-Training](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf) — GPT-1.
- [Radford et al. (2019). Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) — GPT-2.
- [Brown et al. (2020). Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165) — GPT-3와 문맥 내 학습.
- [Leviathan, Kalman, Matias (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — speculative decoding 논문.
- [HuggingFace `modeling_llama.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py) — 인과적 LM 표준 참조 코드.
