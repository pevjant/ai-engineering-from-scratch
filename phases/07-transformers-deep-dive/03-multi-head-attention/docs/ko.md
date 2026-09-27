# 멀티 헤드 어텐션

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 어텐션 헤드 하나는 한 번에 한 가지 관계만 학습합니다. 여덟 개 헤드는 여덟 가지를 학습합니다. 헤드는 공짜입니다. 많이 담으세요.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 7 · 02 (스크래치로 만드는 셀프 어텐션)
**시간:** 약 75분

## 문제 상황

셀프 어텐션 헤드 하나는 어텐션 행렬 하나를 계산합니다. 그 행렬은 한 가지 종류의 관계만 담습니다 — 보통 학습 신호가 주는 손실을 가장 줄여 주는 관계죠. 데이터에 주어-동사 일치, 상호 참조, 장거리 담화, 구문 청킹이 한데 얽혀 있다면, 헤드 하나는 이것들을 하나의 소프트맥스 분포에 뭉개 버려 신호의 절반을 잃어버립니다.

2017년 Vaswani 논문의 해법: 어텐션 함수 여러 개를 병렬로 돌리고, 각각 자체 Q, K, V 프로젝션을 갖게 한 뒤 출력을 이어 붙입니다. 각 헤드는 `d_model / n_heads` 차원의 더 작은 부분 공간에서 동작합니다. 전체 파라미터 수는 그대로고, 표현력만 올라갑니다.

멀티 헤드 어텐션은 2026년 모든 트랜스포머가 기본으로 싣는 구성입니다. 논쟁은 *몇 개의* 헤드를 쓸 것인가, 그리고 키와 값이 프로젝션을 공유할 것인가(Grouped-Query Attention, Multi-Query Attention, Multi-head Latent Attention) 정도입니다.

## 핵심 개념

![멀티 헤드 어텐션은 분리하고, 주시하고, 이어 붙인다](../assets/multi-head-attention.svg)

**분리(Split).** `(N, d_model)` 모양의 `X`를 받습니다. 각각 `(N, d_model)` 모양인 Q, K, V로 프로젝션합니다. `d_head = d_model / n_heads`로 `(N, n_heads, d_head)`로 재구성하고, `(n_heads, N, d_head)`로 전치합니다.

**병렬 어텐션.** 각 헤드 안에서 스케일드 닷프로덕트 어텐션을 실행합니다. 각 헤드는 `(N, d_head)`을 만들어 냅니다. 헤드들은 임베딩의 서로 다른 부분 공간에서 동작하며, 어텐션 계산 자체 중에는 서로 이야기하지 않습니다.

**이어 붙이고 프로젝션.** 헤드들을 다시 `(N, d_model)`로 쌓고, `(d_model, d_model)` 모양의 학습된 출력 행렬 `W_o`를 곱합니다. 헤드들이 서로 섞이는 곳이 바로 `W_o`입니다.

**왜 동작하는가.** 각 헤드가 다른 헤드와 표현력을 다투지 않고도 전문화할 수 있습니다. 2019~2024년의 프로빙(probing) 연구들은 헤드별로 뚜렷한 역할을 밝혔습니다: 위치 헤드, 이전 토큰을 주시하는 헤드, 복사 헤드, 개체명 헤드, 유도 헤드(induction head, 문맥 내 학습의 기반).

**2026년의 변형 계보:**

| 변형 | Q 헤드 수 | K/V 헤드 수 | 사용처 |
|---------|---------|-----------|---------|
| Multi-head (MHA) | N | N | GPT-2, BERT, T5 |
| Multi-query (MQA) | N | 1 | PaLM, Falcon |
| Grouped-query (GQA) | N | G (예: N/8) | Llama 2 70B, Llama 3+, Qwen 2+, Mistral |
| Multi-head latent (MLA) | N | 저랭크로 압축 | DeepSeek-V2, V3 |

GQA가 현대의 기본값입니다. 거의 완전한 품질을 유지하면서 KV 캐시 메모리를 `N/G`배 줄이기 때문입니다. MLA는 더 나아가 K/V를 잠재 공간으로 압축했다가 연산 시점에 다시 프로젝션합니다 — FLOPs를 희생하고 그보다 훨씬 많은 메모리를 아낍니다.

```figure
multihead-split
```

## 만들어 보기

### 단계 1: 이미 있는 단일 헤드 어텐션에서 헤드 분리하기

레슨 02의 `SelfAttention`을 가져다 분리/결합 쌍으로 감쌉니다. numpy 구현은 `code/main.py`를 보세요. 로직은 다음과 같습니다:

```python
def split_heads(X, n_heads):
    n, d = X.shape
    d_head = d // n_heads
    return X.reshape(n, n_heads, d_head).transpose(1, 0, 2)  # (heads, n, d_head)

def combine_heads(H):
    h, n, d_head = H.shape
    return H.transpose(1, 0, 2).reshape(n, h * d_head)
```

reshape 한 번, transpose 한 번. 반복문도 없습니다. PyTorch의 `nn.MultiheadAttention`이 내부에서 하는 일이 정확히 이것입니다.

### 단계 2: 헤드별 스케일드 닷프로덕트 어텐션 실행

각 헤드가 자기 몫의 Q, K, V를 받습니다. 어텐션이 배치 행렬 곱셈이 됩니다:

```python
def mha_forward(X, W_q, W_k, W_v, W_o, n_heads):
    Q = X @ W_q
    K = X @ W_k
    V = X @ W_v
    Qh = split_heads(Q, n_heads)         # (heads, n, d_head)
    Kh = split_heads(K, n_heads)
    Vh = split_heads(V, n_heads)
    scores = Qh @ Kh.transpose(0, 2, 1) / np.sqrt(Qh.shape[-1])
    weights = softmax(scores, axis=-1)
    out = weights @ Vh                    # (heads, n, d_head)
    concat = combine_heads(out)
    return concat @ W_o, weights
```

실제 하드웨어에서 `Qh @ Kh.transpose(...)`는 `bmm` 하나입니다. GPU는 `(heads, N, d_head) × (heads, d_head, N) -> (heads, N, N)` 모양의 배치 행렬 곱셈 한 건만 봅니다. 헤드를 더하는 건 공짜입니다.

### 단계 3: Grouped-Query Attention 변형

키와 값 프로젝션만 바뀝니다. Q는 `n_heads`개 그룹을 쓰고, K와 V는 `n_kv_heads < n_heads`개 그룹을 쓴 뒤 개수를 맞출 때까지 반복 복제합니다:

```python
def gqa_project(X, W, n_kv_heads, n_heads):
    kv = split_heads(X @ W, n_kv_heads)       # (kv_heads, n, d_head)
    repeat = n_heads // n_kv_heads
    return np.repeat(kv, repeat, axis=0)      # (n_heads, n, d_head)
```

추론 때는 KV 캐시에 `n_heads`개가 아니라 `n_kv_heads`개 복사본만 살아 있으므로 메모리가 절약됩니다. Llama 3 70B는 쿼리 헤드 64개에 KV 헤드 8개를 씁니다 — 캐시가 8분의 1로 줄어듭니다.

### 단계 4: 각 헤드가 무엇을 학습했는지 들여다보기

짧은 문장에 헤드 4개로 MHA를 돌립니다. 헤드마다 `(N, N)` 어텐션 행렬을 출력해 보세요. 무작위 초기화여도 헤드마다 다른 구조를 골라내는 것을 볼 수 있습니다 — 일부는 진짜 신호이고, 일부는 부분 공간의 회전 대칭 때문입니다.

## 활용하기

PyTorch에서 한 줄 버전:

```python
import torch.nn as nn

mha = nn.MultiheadAttention(embed_dim=512, num_heads=8, batch_first=True)
```

PyTorch 2.5+의 GQA:

```python
from torch.nn.functional import scaled_dot_product_attention

# scaled_dot_product_attention은 CUDA에서 Flash Attention을 자동으로 씁니다.
# GQA를 쓰려면 Q는 (B, n_heads, N, d_head), K,V는 (B, n_kv_heads, N, d_head)
# 모양으로 넘깁니다. 반복 복제는 PyTorch가 알아서 처리합니다.
out = scaled_dot_product_attention(q, k, v, is_causal=True, enable_gqa=True)
```

**헤드는 몇 개?** 2026년 프로덕션 모델들의 경험칙:

| 모델 크기 | d_model | n_heads | d_head |
|------------|---------|---------|--------|
| Small (~125M) | 768 | 12 | 64 |
| Base (~350M) | 1024 | 16 | 64 |
| Large (~1B) | 2048 | 16 | 128 |
| Frontier (~70B) | 8192 | 64 | 128 |

`d_head`는 거의 항상 64 또는 128에 떨어집니다. 이 값은 헤드 하나가 "볼 수 있는" 양의 단위입니다. 32 아래로 내려가면 헤드들이 스케일링 팩터 `sqrt(d_head)`와 싸우기 시작하고, 256 위로 올라가면 "잘게 나눈 전문가 여러 명"이라는 이점을 잃습니다.

## 출시하기

`outputs/skill-mha-configurator.md`를 보세요. 이 스킬은 파라미터 예산, 시퀀스 길이, 배포 대상이 주어진 새 트랜스포머에 헤드 수, kv 헤드 수, 프로젝션 전략을 추천합니다.

## 연습 문제

1. **쉬움.** `code/main.py`의 MHA에서 `n_heads`를 1에서 16으로 바꿔 보세요. `d_model=64`는 고정합니다. 합성 복사 과제에 대해 한 층짜리 작은 모델의 손실을 그려 보세요. 헤드가 많아지면 도움이 되나요, 정체되나요, 해가 되나요?
2. **보통.** MQA(모든 쿼리 헤드가 하나의 KV 헤드를 공유)를 구현합니다. 풀 MHA 대비 파라미터 수가 얼마나 줄어드는지 재고, N=2048에서 추론 시 KV 캐시 크기가 얼마나 줄어드는지 계산합니다.
3. **어려움.** Multi-head Latent Attention의 축소판을 구현합니다: K, V를 랭크 `r`짜리 잠재 표현으로 압축해 KV 캐시에 저장하고, 어텐션 시점에 압축을 풉니다. 검증 ppl이 1비트 이내로 유지되면서 캐시 메모리가 풀 MHA의 1/8 아래로 내려가는 `r`은 얼마인가요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 헤드 (Head) | "어텐션 회로 하나" | 차원 `d_head = d_model / n_heads`의 Q/K/V 프로젝션 하나와 자기 어텐션 행렬. |
| d_head | "헤드 차원" | 헤드당 은닉 폭; 프로덕션에서는 거의 항상 64 또는 128. |
| Split / combine | "reshape 트릭" | 어텐션 전후의 `(N, d_model) ↔ (n_heads, N, d_head)` reshape+transpose. |
| W_o | "출력 프로젝션" | 헤드를 이어 붙인 뒤 곱하는 `(d_model, d_model)` 행렬; 헤드들이 섞이는 곳. |
| MQA | "KV 헤드 하나" | Multi-Query Attention: K/V 프로젝션 하나를 공유. KV 캐시가 가장 작지만 품질이 일부 하락. |
| GQA | "Llama 2 이후의 기본값" | Grouped-Query Attention으로 `n_kv_heads < n_heads`; Q에 맞춰 반복 복제. |
| MLA | "DeepSeek의 트릭" | Multi-head Latent Attention: K, V를 저랭크 잠재 표현으로 압축했다가 어텐션 때 압축을 품. |
| 유도 헤드 (Induction head) | "문맥 내 학습을 떠받치는 회로" | 이전에 등장한 적이 있는 패턴을 찾아 그 뒤에 이어진 것을 복사하는 헤드 쌍. |

## 더 읽을거리

- [Vaswani et al. (2017). Attention Is All You Need §3.2.2](https://arxiv.org/abs/1706.03762) — 원조 멀티 헤드 명세.
- [Shazeer (2019). Fast Transformer Decoding: One Write-Head is All You Need](https://arxiv.org/abs/1911.02150) — MQA 논문.
- [Ainslie et al. (2023). GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245) — 학습 후 MHA를 GQA로 바꾸는 방법.
- [DeepSeek-AI (2024). DeepSeek-V2 Technical Report](https://arxiv.org/abs/2405.04434) — MLA와 캐시 메모리에서 MHA/GQA를 이기는 이유.
- [Olsson et al. (2022). In-context Learning and Induction Heads](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html) — 헤드가 실제로 하는 일에 대한 기계적 분석.
