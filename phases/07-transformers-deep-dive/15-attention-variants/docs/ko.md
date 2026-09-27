> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 어텐션 변형 — 슬라이딩 윈도우, 희소, 차등 어텐션

> 풀 어텐션은 원(circle)입니다. 모든 토큰이 모든 토큰을 보고, 메모리가 그 대가를 치릅니다. 네 가지 변형이 이 원의 모양을 구부려서 비용의 절반을 되찾아 줍니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 7 · 02(셀프 어텐션), 페이즈 7 · 03(멀티헤드), 페이즈 7 · 12(KV 캐시 / Flash Attention)
**시간:** 약 60분

## 문제 상황

풀 어텐션은 시퀀스 길이에 대해 `O(N²)` 메모리와 `O(N²)` 연산을 요구합니다. 128K 컨텍스트의 Llama 3 70B라면 레이어당 어텐션 항목이 160억 개, 거기에 80개 레이어를 곱한 셈입니다. Flash Attention(레슨 12)은 `O(N²)` 활성화 메모리를 숨겨 주지만 산술 비용 자체를 바꾸지는 못합니다 — 여전히 모든 토큰이 모든 토큰을 봐야 하니까요.

세 부류의 변형이 어텐션 행렬의 위상(topology) 자체를 바꿉니다:

1. **슬라이딩 윈도우 어텐션(SWA).** 각 토큰이 전체 접두사가 아니라 이웃의 고정된 윈도우만 봅니다. 메모리와 연산이 `O(N · W)`(`W`는 윈도우 크기)로 떨어집니다. Gemma 2/3, Mistral 7B의 앞쪽 레이어, Phi-3-Long.
2. **희소 / 블록 어텐션.** 선택된 쌍 `(i, j)`만 점수를 매기고, 나머지는 가중치를 강제로 0으로 만듭니다. Longformer, BigBird, OpenAI sparse transformer.
3. **차등 어텐션(differential attention).** 서로 다른 Q/K 투영으로 어텐션 맵 두 개를 계산해 하나를 다른 하나에서 뺍니다. 앞 몇 토큰에 가중치가 새어 들어가는 '어텐션 싱크'를 죽입니다. Microsoft의 DIFF Transformer(2024).

이들은 공존합니다. 2026년 최전선 모델은 흔히 이들을 섞습니다: 대부분의 레이어는 SWA-1024, 다섯 번째마다 글로벌 풀 어텐션, 그리고 검색을 정리하는 차등 헤드 몇 개. Gemma 3의 5:1 SWA:글로벌 비율이 현재의 교과서 기본값입니다.

## 개념

### 슬라이딩 윈도우 어텐션(SWA)

위치 `i`의 각 쿼리는 `[i - W, i]`(인과 SWA) 또는 `[i - W/2, i + W/2]`(양방향) 범위의 위치만 봅니다. 윈도우 밖 토큰은 점수 행렬에서 `-inf`를 받습니다.

```
full causal:           sliding window (W=4):
positions 0-7          positions 0-7, W=4
    0 1 2 3 4 5 6 7        0 1 2 3 4 5 6 7
0 | x                0 |  x
1 | x x              1 |  x x
2 | x x x            2 |  x x x
3 | x x x x          3 |  x x x x
4 | x x x x x        4 |    x x x x
5 | x x x x x x      5 |      x x x x
6 | x x x x x x x    6 |        x x x x
7 | x x x x x x x x  7 |          x x x x
```

`N = 8192`, `W = 1024`라면 점수 행렬은 기대상 1024 × 8192개의 0이 아닌 행을 갖습니다 — 8배 절감입니다.

**KV 캐시도 SWA와 함께 줄어듭니다.** 레이어마다 K, V의 마지막 `W`개 토큰만 유지하면 됩니다. Gemma-3 비슷한 설정(윈도우 1024, 컨텍스트 128K)이라면 KV 캐시가 128배 줄어듭니다.

**품질 비용.** SWA만 쓰는 트랜스포머는 장거리 검색에서 고전합니다. 해법: SWA 레이어와 풀 어텐션 레이어를 섞는 것. Gemma 3는 5:1 SWA:글로벌을 씁니다. Mistral 7B는 정보가 겹치는 윈도우를 타고 '앞으로 흐르는' 인과-SWA 스택을 썼습니다 — 각 레이어가 실효 수용 영역을 `W`만큼 늘리고, `L`개 레이어를 지나면 모델이 `L × W`개 토큰 뒤를 볼 수 있습니다.

### 희소 / 블록 어텐션

`N × N` 희소 패턴을 미리 정합니다. 정석적인 세 모양:

- **로컬 + 스트라이드(OpenAI sparse transformer).** 마지막 `W`개 토큰에 더해 그 앞의 `stride`번째마다 토큰을 봅니다. `O(N · sqrt(N))` 연산으로 로컬과 장거리를 모두 잡습니다.
- **Longformer / BigBird.** 로컬 윈도우 + 모두를 보고 모두에게 보이는 소수의 글로벌 토큰(예: `[CLS]`) + 무작위 희소 링크. 같은 품질에서 경험적으로 2배 컨텍스트.
- **네이티브 희소 어텐션(DeepSeek, 2025).** `(Q, K)`의 어떤 블록이 중요한지 학습; 커널 수준에서 0 블록을 건너뜁니다. FlashAttention 호환.

희소 어텐션은 커널 엔지니어링 이야기입니다. 수학은 간단합니다(점수 행렬을 마스킹); 이득은 0 항목을 SRAM에 아예 적재하지 않는 데서 나옵니다. FlashAttention-3와 2026년 FlexAttention API가 사용자 지정 희소 패턴을 PyTorch의 일급 시민으로 만들었습니다.

### 차등 어텐션(DIFF Transformer, 2024)

일반 어텐션에는 '어텐션 싱크' 문제가 있습니다: softmax가 모든 행의 합을 1로 강제하기 때문에, 딱히 볼 곳이 없는 토큰이 그 가중치를 첫 토큰(또는 앞 몇 개)에 쏟아 붓습니다. 이것이 진짜 내용이 받아야 할 용량을 훔쳐 갑니다.

차등 어텐션은 **두 개의** 어텐션 맵을 계산해 서로 빼서 이를 해결합니다:

```
A1 = softmax(Q1 K1^T / √d)
A2 = softmax(Q2 K2^T / √d)
DiffAttn = (A1 - λ · A2) V
```

여기서 `λ`는 학습되는 스칼라입니다(보통 0.5~0.8). A1은 진짜 내용의 가중치를 담고, A2는 싱크를 담습니다. 뺄셈이 싱크를 상쇄하고 가중치를 관련 토큰에게 다시 배분합니다.

보고된 결과(Microsoft 2024): 퍼플렉서티 5~10% 감소, 같은 학습 길이에서 실효 컨텍스트 1.5~2배, 바늘 건짐(needle-in-haystack) 검색이 더 예리해짐.

### 변형 비교

| 변형 | 연산 | KV 캐시 | 풀 어텐션 대비 품질 | 프로덕션 사용 사례 |
|---------|---------|----------|-----------------|----------------|
| 풀 어텐션 | O(N²) | 레이어당 O(N) | 베이스라인 | 모든 모델의 기본 레이어 |
| SWA (윈도우 1024) | O(N·W) | 레이어당 O(W) | -0.1 ppl, 글로벌 레이어와 함께면 양호 | Gemma 2/3, Phi-3-Long |
| 로컬 + 스트라이드 희소 | O(N·√N) | 혼합 | SWA와 비슷 | OpenAI sparse transformer, Longformer |
| BigBird (로컬 + 글로벌 + 무작위) | O(N) 근사 | 혼합 | 2배 컨텍스트에서 풀 어텐션과 동등 | 초기 장문 컨텍스트 BERT |
| 네이티브 희소 (DeepSeek-V3.2) | O(N · 활성 비율) | O(N) | 0.05 ppl 이내 | DeepSeek-V3.2, 2025 |
| 차등 | O(2·N²) | O(2N) | -5 ~ -10% ppl | DIFF Transformer, 2026년 초반 모델들 |

```figure
gqa-kv-sharing
```

## 만들어 보기

`code/main.py`를 보세요. 풀, SWA, 로컬+스트라이드, 차등 어텐션을 장난감 시퀀스에서 나란히 보여 주는 인과 마스크 비교기를 구현합니다.

### 단계 1: 풀 인과 마스크(베이스라인)

```python
def causal_mask(n):
    return [[0.0 if j <= i else float("-inf") for j in range(n)] for i in range(n)]
```

레슨 07의 베이스라인입니다. 하삼각형; 대각선 위는 가중치 0.

### 단계 2: 슬라이딩 윈도우 인과 마스크

```python
def swa_mask(n, window):
    M = [[float("-inf")] * n for _ in range(n)]
    for i in range(n):
        lo = max(0, i - window + 1)
        for j in range(lo, i + 1):
            M[i][j] = 0.0
    return M
```

파라미터는 하나 — `window`. `window >= n`이면 풀 인과 어텐션으로 돌아갑니다. `window = 1`이면 각 토큰은 자기 자신만 봅니다.

### 단계 3: 로컬 + 스트라이드 희소 마스크

```python
def strided_mask(n, window, stride):
    M = [[float("-inf")] * n for _ in range(n)]
    for i in range(n):
        lo = max(0, i - window + 1)
        for j in range(lo, i + 1):
            M[i][j] = 0.0
        for j in range(0, i + 1, stride):
            M[i][j] = 0.0
    return M
```

촘촘한 로컬 윈도우에 더해 `stride`번째마다 시퀀스 시작까지 거슬러 올라가는 토큰을 봅니다. 레이어가 쌓일수록 수용 영역이 로그 스텝으로 늘어납니다.

### 단계 4: 차등 어텐션

```python
def diff_attention(Q1, K1, Q2, K2, V, lam):
    A1 = softmax_causal(Q1 @ K1.T / sqrt_d)
    A2 = softmax_causal(Q2 @ K2.T / sqrt_d)
    return (A1 - lam * A2) @ V
```

어텐션 패스 두 번, 학습된 혼합 계수로 뺍니다. 코드에서는 단일 어텐션과 차등 어텐션의 어텐션 싱크 히트맵을 비교하며 싱크가 무너지는 것을 봅니다.

### 단계 5: KV 캐시 크기

각 변형의 레이어당 캐시 크기를 `N = 131072`에서 출력합니다. SWA와 희소 변형은 10~100배 줄어듭니다. 차등은 두 배가 됩니다. 메모리 청구서는 의식하고 치르세요.

## 사용해 보기

2026년 프로덕션 패턴:

```python
from transformers import AutoModelForCausalLM
# Gemma 3는 SWA(윈도우=1024)와 글로벌 레이어를 5:1로 섞습니다.
model = AutoModelForCausalLM.from_pretrained("google/gemma-3-27b-it")
# print(model.config.sliding_window, model.config.layer_types)
```

PyTorch 2.5+의 FlexAttention은 마스크 함수를 받습니다:

```python
from torch.nn.attention.flex_attention import flex_attention, create_block_mask

def swa_pattern(b, h, q_idx, kv_idx):
    return (q_idx - kv_idx < 1024) & (q_idx >= kv_idx)

mask = create_block_mask(swa_pattern, B=batch, H=heads, Q_LEN=n, KV_LEN=n)
out = flex_attention(q, k, v, block_mask=mask)
```

이것은 사용자 지정 Triton 커널로 컴파일됩니다. 흔한 패턴 기준 FlashAttention-3 속도의 10% 이내이고, 마스크 함수는 그냥 Python 콜러블입니다.

**무엇을 언제 고를까:**

- **순수 풀 어텐션** — 컨텍스트 약 16K까지는 모든 레이어, 또는 검색 품질이 최우선일 때.
- **SWA + 글로벌 혼합** — 긴 컨텍스트(32K 초과), 학습과 추론 모두 메모리 병목일 때. 32K를 넘는 2026년의 기본값.
- **희소 블록 어텐션** — 사용자 지정 커널, 사용자 지정 패턴. 특수 작업(검색, 오디오)용으로 남겨 둡니다.
- **차등 어텐션** — 어텐션 싱크 오염이 해가 되는 모든 작업(장문 컨텍스트 RAG, 바늘 건짐 검색).

## 출시하기

`outputs/skill-attention-variant-picker.md`를 보세요. 이 스킬은 목표 컨텍스트 길이, 검색 요구, 학습/추론 연산 프로필이 주어지면 새 모델의 어텐션 위상을 정해 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. `window=4`인 SWA가 각 행에서 마지막 4토큰 밖을 전부 0으로 만드는지 확인합니다. `window=n`이 풀 인과 어텐션을 비트 단위로 그대로 재현하는지 확인합니다.
2. **보통.** 레슨 07 캡스톤 위에 `window=1024` 인과 SWA를 구현하세요. tinyshakespeare로 1,000 스텝 학습합니다. 풀 어텐션 대비 검증 손실은 얼마나 나빠지나요? 피크 메모리는 얼마나 떨어지나요?
3. **어려움.** 캡스톤 모델에 Gemma-3 스타일 5:1 레이어 혼합(SWA 5, 글로벌 1)을 구현하세요. 파라미터를 맞춘 상태에서 순수 SWA 베이스라인과 순수 글로벌 베이스라인과 비교해 손실, 메모리, 생성 품질을 평가합니다.
4. **어려움.** 헤드별 학습되는 `λ`를 갖는 차등 어텐션을 구현하세요. 합성 검색 과제(바늘 하나, 방해물 2,000개)로 학습합니다. 파라미터를 맞춘 단일 어텐션 베이스라인과 비교해 검색 정확도를 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 슬라이딩 윈도우 어텐션(SWA) | "로컬 어텐션" | 각 쿼리가 자신의 마지막 `W`개 토큰만 봄; KV 캐시가 `O(W)`로 줄어듭니다. |
| 실효 수용 영역 | "모델이 얼마나 멀리까지 보나" | 윈도우 `W`인 `L`층 SWA 스택에서 최대 `L × W`개 토큰. |
| Longformer / BigBird | "로컬 + 글로벌 + 무작위" | 항상 보는 글로벌 토큰 몇 개가 있는 희소 패턴; 초기 장문 컨텍스트 접근법. |
| 네이티브 희소 어텐션 | "DeepSeek의 커널 트릭" | 블록 수준 희소성을 학습; 품질을 유지하며 커널 수준에서 0 블록을 건너뜁니다. |
| 차등 어텐션 | "맵 두 개, 하나를 뺌" | DIFF Transformer: 첫 어텐션 맵에서 학습된 `λ`배의 두 번째 맵을 빼 어텐션 싱크를 상쇄. |
| 어텐션 싱크 | "가중치가 0번 토큰으로 샘" | softmax 정규화가 행의 합을 1로 강제; 정보가 없는 쿼리가 가중치를 위치 0에 쏟아붙입니다. |
| FlexAttention | "마스크를 Python으로" | 임의의 마스크 함수를 FlashAttention 형태의 커널로 컴파일하는 PyTorch 2.5+ API. |
| 레이어 타입 혼합 | "5:1 SWA:글로벌" | 스택 안에 희소 레이어와 풀 어텐션 레이어를 섞어 더 낮은 메모리로 품질을 유지합니다. |

## 더 읽을거리

- [Beltagy, Peters, Cohan (2020). Longformer: The Long-Document Transformer](https://arxiv.org/abs/2004.05150) — 정석적인 슬라이딩 윈도우 + 글로벌 토큰 논문.
- [Zaheer 외 (2020). Big Bird: Transformers for Longer Sequences](https://arxiv.org/abs/2007.14062) — 로컬 + 글로벌 + 무작위.
- [Child 외 (2019). Generating Long Sequences with Sparse Transformers](https://arxiv.org/abs/1904.10509) — OpenAI의 로컬+스트라이드 패턴.
- [Gemma Team (2024). Gemma 2: Improving Open Language Models at a Practical Size](https://arxiv.org/abs/2408.00118) — 1:1 SWA:글로벌 혼합.
- [Gemma Team (2025). Gemma 3 technical report](https://arxiv.org/abs/2503.19786) — 지금 교과서 기본값이 된 윈도우=1024의 5:1 혼합.
- [Ye 외 (2024). Differential Transformer](https://arxiv.org/abs/2410.05258) — DIFF Transformer 논문.
- [Yuan 외 (2025). Native Sparse Attention](https://arxiv.org/abs/2502.11089) — DeepSeek-V3.2의 학습형 희소 어텐션.
- [PyTorch — FlexAttention 블로그와 문서](https://pytorch.org/blog/flexattention/) — '사용해 보기'의 마스크-콜러블 패턴 API 레퍼런스.
