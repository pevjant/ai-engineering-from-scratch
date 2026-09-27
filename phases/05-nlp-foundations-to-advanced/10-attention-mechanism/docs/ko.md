> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 어텐션 메커니즘 — 그 돌파구 (Attention Mechanism — The Breakthrough)

> 디코더가 눈을 가늘게 뜨고 압축된 요약만 보던 시절이 끝났습니다. 이제 원문 전체를 봅니다. 이 다음의 모든 것은 어텐션 + 엔지니어링입니다.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 09(시퀀스-투-시퀀스 모델)
**소요 시간:** 약 45분

## 해결할 문제

레슨 09는 측정된 실패로 끝났습니다. 장난감 복사 과제로 학습한 GRU 인코더-디코더는 길이 5에서 89%였던 정확도가 길이 80에서는 거의 찍는 수준으로 떨어집니다. 이유는 구조적이지 학습 버그가 아닙니다. 인코더가 모은 정보의 모든 비트가 고정 크기 은닉 상태 하나에 들어가야 하고, 디코더는 그 외의 것을 전혀 보지 못하기 때문입니다.

Bahdanau, Cho, Bengio가 2014년에 세 줄짜리 해법을 발표했습니다. 디코더에게 인코더의 최종 상태만 주는 대신, 모든 인코더 상태를 계속 들고 있는 것입니다. 디코더의 각 단계에서 인코더 상태들의 가중 평균을 계산하는데, 그 가중치가 말해 줍니다. "지금 이 순간 디코더는 인코더 위치 `i`를 얼마나 봐야 하는가?" 이 가중 평균이 컨텍스트이고, 디코더 단계마다 바뀝니다.

아이디어는 그게 전부입니다. 트랜스포머는 이것을 확장했습니다. 셀프 어텐션은 이것을 하나의 시퀀스 안에 적용했고, 멀티헤드 어텐션은 병렬로 돌렸습니다. 하지만 2014년 버전이 이미 병목을 깨 놨고, 그것만 있으면 트랜스포머로의 전환은 개념의 문제가 아니라 엔지니어링의 문제입니다.

## 핵심 개념

![Bahdanau 어텐션: 디코더가 모든 인코더 상태에 질의한다](../assets/attention.svg)

디코더의 각 단계 `t`에서:

1. 이전 디코더 은닉 상태 `s_{t-1}`을 **질의(query)**로 씁니다.
2. 모든 인코더 은닉 상태 `h_1, ..., h_T`와 점수를 매깁니다. 인코더 위치마다 스칼라 하나씩.
3. 점수들에 소프트맥스를 적용해 합이 1이 되는 어텐션 가중치 `α_{t,1}, ..., α_{t,T}`를 얻습니다.
4. 컨텍스트 벡터는 `c_t = Σ α_{t,i} * h_i`. 인코더 상태들의 가중 평균입니다.
5. 디코더는 `c_t`와 이전 출력 토큰을 받아 다음 토큰을 만들어 냅니다.

포인트는 가중 평균입니다. 디코더가 "Je"를 "I"로 번역해야 할 때는 "Je" 위의 인코더 상태에 높은 가중치를, 나머지에는 낮은 가중치를 줍니다. "not"이 필요하면 "pas"에 높은 가중치를 줍니다. 컨텍스트 벡터는 단계마다 모양을 바꿉니다.

## 모양(Shapes) — 모두를 문 다녀가는 것

모든 어텐션 구현이 처음에 여기서 틀어집니다. 천천히 읽으세요.

| 것 | 모양 | 비고 |
|-------|-------|-------|
| 인코더 은닉 상태들 `H` | `(T_enc, d_h)` | BiLSTM이면 `d_h = 2 * d_hidden` |
| 디코더 은닉 상태 `s_{t-1}` | `(d_s,)` | 벡터 하나 |
| 어텐션 점수 `e_{t,i}` | 스칼라 | 인코더 위치마다 하나 |
| 어텐션 가중치 `α_{t,i}` | 스칼라 | 모든 `i`에 대해 소프트맥스를 통과한 뒤 |
| 컨텍스트 벡터 `c_t` | `(d_h,)` | 인코더 상태와 같은 모양 |

**Bahdanau(가산, additive) 점수.** `e_{t,i} = v_α^T * tanh(W_a * s_{t-1} + U_a * h_i)`.

- `s_{t-1}`의 모양은 `(d_s,)`, `h_i`의 모양은 `(d_h,)`입니다.
- `W_a`의 모양은 `(d_attn, d_s)`, `U_a`의 모양은 `(d_attn, d_h)`입니다.
- tanh 안의 그 합은 모양이 `(d_attn,)`입니다.
- `v_α`의 모양은 `(d_attn,)`입니다. `v_α`와의 내적이 스칼라로 붕괴시킵니다. **이것이 `v_α`가 하는 일입니다.** 마법이 아닙니다. 어텐션 차원 벡터를 스칼라 점수로 바꾸는 그 프로젝션이고요.

**Luong(곱셈, multiplicative) 점수.** 세 가지 변형이 있습니다.

- `dot`: `e_{t,i} = s_t^T * h_i`. `d_s == d_h`가 필요합니다. 강한 제약입니다. 인코더가 양방향이면 건너뛰세요.
- `general`: `e_{t,i} = s_t^T * W * h_i`, `W`의 모양은 `(d_s, d_h)`. 차원이 같아야 한다는 제약을 없앱니다.
- `concat`: 본질적으로 Bahdanau 형태입니다. 앞의 둘이 더 싸서 거의 쓰이지 않습니다.

**이름 붙여 둘 Bahdanau/Luong 함정 하나.** Bahdanau는 `s_{t-1}`(현재 단어를 생성하기 *전의* 디코더 상태)을 씁니다. Luong은 `s_t`(*후의* 상태)를 씁니다. 둘을 섞으면 디버깅이 극도로 어려운, 미묘하게 틀린 그래디언트가 나옵니다. 논문 하나를 고르고 그 관례만 따르세요.

```figure
attention-heatmap
```

## 만들어 보기

### 단계 1: 가산(Bahdanau) 어텐션

```python
import numpy as np


def additive_attention(decoder_state, encoder_states, W_a, U_a, v_a):
    projected_dec = W_a @ decoder_state
    projected_enc = encoder_states @ U_a.T
    combined = np.tanh(projected_enc + projected_dec)
    scores = combined @ v_a
    weights = softmax(scores)
    context = weights @ encoder_states
    return context, weights


def softmax(x):
    x = x - np.max(x)
    e = np.exp(x)
    return e / e.sum()
```

모양을 위 표와 대조해 보세요. `encoder_states`의 모양은 `(T_enc, d_h)`입니다. `projected_enc`의 모양은 `(T_enc, d_attn)`입니다. `projected_dec`의 모양은 `(d_attn,)`이고 브로드캐스팅됩니다. `combined`의 모양은 `(T_enc, d_attn)`입니다. `scores`의 모양은 `(T_enc,)`입니다. `weights`의 모양은 `(T_enc,)`입니다. `context`의 모양은 `(d_h,)`입니다. 이제 출시하세요.

### 단계 2: Luong dot과 general

```python
def dot_attention(decoder_state, encoder_states):
    scores = encoder_states @ decoder_state
    weights = softmax(scores)
    return weights @ encoder_states, weights


def general_attention(decoder_state, encoder_states, W):
    projected = W.T @ decoder_state
    scores = encoder_states @ projected
    weights = softmax(scores)
    return weights @ encoder_states, weights
```

각각 세 줄입니다. Luong의 논문이 먹힌 이유가 이것입니다. 대부분의 과제에서 정확도는 같으면서 코드는 훨씬 적거든요.

### 단계 3: 손으로 계산해 보는 수치 예제

세 개의 인코더 상태(대충 "cat", "sat", "mat")와 첫 번째와 가장 잘 맞는 디코더 상태가 주어지면, 어텐션 분포는 위치 0에 몰립니다. 디코더 상태가 마지막 것과 맞도록 옮겨지면 어텐션은 위치 2로 움직입니다. 컨텍스트 벡터가 따라갑니다.

```python
H = np.array([
    [1.0, 0.0, 0.2],
    [0.5, 0.5, 0.1],
    [0.1, 0.9, 0.3],
])

s_close_to_cat = np.array([0.9, 0.1, 0.2])
ctx, w = dot_attention(s_close_to_cat, H)
print("weights:", w.round(3))
```

```
weights: [0.464 0.305 0.231]
```

첫 행이 이겼습니다. 이제 디코더 상태를 세 번째 인코더 상태 쪽으로 옮기고 가중치가 어떻게 이동하는지 지켜보세요. 어텐션이란 그겁니다. 명시적인 정렬(alignment)이죠.

### 단계 4: 이것이 왜 트랜스포머로 가는 다리인가

위의 언어를 Q/K/V로 옮겨 쓰면 다음과 같습니다.

- **질의(Query)** = 디코더 상태 `s_{t-1}`
- **키(Key)** = 인코더 상태들(점수를 매기는 대상)
- **값(Value)** = 인코더 상태들(가중치를 곱해 더하는 대상)

고전 어텐션에서는 키와 값이 같은 것입니다. 셀프 어텐션은 둘을 분리합니다. 시퀀스가 자기 자신에게 질의할 수 있고, K와 V에 서로 다른 학습된 프로젝션을 쓸 수 있죠. 멀티헤드 어텐션은 서로 다른 학습된 프로젝션으로 이것을 병렬로 돌립니다. 트랜스포머는 이 전체 무대를 여러 겹 쌓고 RNN을 버립니다.

수학은 같습니다. 모양도 같습니다. Bahdanau 어텐션에서 스케일드 점곱(dot-product) 어텐션으로 가는 개념적 점프는 대부분 표기법의 문제입니다.

## 활용하기

PyTorch와 TensorFlow는 어텐션을 기본 탑재하고 나옵니다.

```python
import torch
import torch.nn as nn

mha = nn.MultiheadAttention(embed_dim=128, num_heads=8, batch_first=True)
query = torch.randn(2, 5, 128)
key = torch.randn(2, 10, 128)
value = torch.randn(2, 10, 128)

output, weights = mha(query, key, value)
print(output.shape, weights.shape)
```

```
torch.Size([2, 5, 128]) torch.Size([2, 5, 10])
```

이것이 바로 트랜스포머 어텐션 레이어입니다. 5개 위치의 질의 배치, 10개 위치의 키/값 배치, 각각 128차원, 8개 헤드. `output`은 컨텍스트가 더해진 새 질의입니다. `weights`는 시각화할 수 있는 5x10 정렬 행렬이고요.

### 고전 어텐션이 여전히 중요한 때

- 교육. 단일 헤드, 단일 레이어, RNN 기반 버전은 모든 개념이 눈에 보입니다.
- 트랜스포머가 안 맞는 온디바이스 시퀀스 과제.
- 2014~2017년 논문이라면 무엇이든. Bahdanau의 관례를 모르면 잘못 읽게 됩니다.
- 기계 번역에서의 세밀한 정렬 분석. 날어텐션 가중치는 트랜스포머 모델에서도 해석 도구가 되며, 읽으려면 그것이 무엇인지 알아야 합니다.

### 어텐션 가중치 = 설명이라는 함정

어텐션 가중치는 해석 가능해 보입니다. 위치들에 걸쳐 합이 1인 가중치고, 그래프로 그릴 수 있고, 높으면 "여기를 봤다"는 뜻으로 읽히죠. 리뷰어들이 좋아합니다.

하지만 보기만큼 해석 가능하지 않습니다. Jain과 Wallace(2019)는 일부 과제에서 어텐션 분포를 임의의 다른 분포로 뒤섞거나 바꿔도 모델 예측이 변하지 않음을 보였습니다. 어블레이션(ablation)이나 반사실(counterfactual) 점검 없이 어텐션 가중치를 추론의 증거로 보고하는 일은 절대 없어야 합니다.

## 출시하기

`outputs/prompt-attention-shapes.md`로 저장하세요:

```markdown
---
name: attention-shapes
description: 어텐션 구현의 모양(shape) 버그를 디버깅합니다.
phase: 5
lesson: 10
---

망가진 어텐션 구현이 주어지면 어느 모양이 맞지 않는지 찾아냅니다. 출력:

1. 어느 행렬의 모양이 틀렸는지. 텐서 이름을 밝힙니다.
2. 그 모양이 무엇이어야 하는지, `(d_s, d_h, d_attn, T_enc, T_dec, batch_size)`에서 유도합니다.
3. 한 줄짜리 수정. 전치(transpose), 리셰이프(reshape), 또는 프로젝션(project).
4. 회귀를 잡아낼 테스트. 보통은: `output.shape == (batch, T_dec, d_h)`와 `weights.shape == (batch, T_dec, T_enc)`와 `weights.sum(dim=-1)`이 1에 가까운지 단언(assert)합니다.

조용히 브로드캐스팅으로 넘어가는 수정을 추천하는 일은 거부합니다. 브로드캐스팅에 숨은 버그는 나중에 조용한 정확도 저하로 떠오릅니다. 어텐션 버그 중 최악의 종류죠.

Bahdanau 혼동에는 디코더 입력이 `s_{t-1}`(단계 이전 상태)임을 주장합니다. Luong에는 `s_t`(단계 이후 상태)입니다. 점곱 어텐션에서 처음 겪는 가장 흔한 오류인 질의/키 차원 불일치는 명확히 표시합니다.
```

## 연습 문제

1. **(쉬움)** `softmax` 마스킹을 구현해서 인코더의 패딩 토큰이 어텐션 가중치 0을 받게 하세요. 길이가 제각각인 시퀀스 배치로 테스트합니다.
2. **(보통)** Luong `general` 형태에 멀티헤드 어텐션을 추가하세요. `d_h`를 `n_heads`개 그룹으로 쪼개고, 헤드별로 어텐션을 돌리고, 이어 붙입니다. 단일 헤드 경우가 앞서 구현한 것과 일치하는지 검증합니다.
3. **(어려움)** Bahdanau 어텐션을 붙인 GRU 인코더-디코더를 레슨 09의 장난감 복사 과제로 학습시키세요. 시퀀스 길이별 정확도를 그래프로 그리고, 어텐션 없는 베이스라인과 비교합니다. 길이가 늘어날수록 격차가 벌어지는지 확인하세요. 어텐션이 병목을 들어 올린다는 것을 입증하는 것입니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 어텐션 | 뭘 보는 것 | 값 시퀀스의 가중 평균. 가중치는 질의-키 유사도로부터 계산됨. |
| 질의, 키, 값 | QKV | 세 프로젝션: Q는 묻고, K는 맞춰 볼 대상, V는 돌려받을 내용. |
| 가산 어텐션 | Bahdanau | 순전파 점수: `v^T tanh(W q + U k)`. |
| 곱셈 어텐션 | Luong dot / general | 점수가 `q^T k` 또는 `q^T W k`. 더 싸고, 대부분 과제에서 정확도는 같음. |
| 정렬 행렬 | 그 예쁜 그림 | `(T_dec, T_enc)` 격자로 본 어텐션 가중치. 읽으면 모델이 무엇을 봤는지 알 수 있음. |

## 더 읽을거리

- [Bahdanau, Cho, Bengio (2014). Neural Machine Translation by Jointly Learning to Align and Translate](https://arxiv.org/abs/1409.0473) — 그 원 논문.
- [Luong, Pham, Manning (2015). Effective Approaches to Attention-based Neural Machine Translation](https://arxiv.org/abs/1508.04025) — 세 가지 점수 변형과 그 비교.
- [Jain and Wallace (2019). Attention is not Explanation](https://arxiv.org/abs/1902.10186) — 해석 가능성에 관한 주의 사항.
- [Dive into Deep Learning — Bahdanau Attention](https://d2l.ai/chapter_attention-mechanisms-and-transformers/bahdanau-attention.html) — PyTorch로 돌려 볼 수 있는 튜토리얼.
