> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# KV 캐시, Flash Attention, 추론 최적화

> 학습은 병렬이고 FLOP 병목입니다. 추론은 직렬이고 메모리 병목입니다. 병목이 다르니 쓰는 기술도 달라야죠.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 7 · 02(셀프 어텐션), 페이즈 7 · 05(풀 트랜스포머), 페이즈 7 · 07(GPT)
**시간:** 약 75분

## 문제 상황

순진한 자기회귀 디코더가 토큰 `N`개를 만들려면 `O(N²)`의 작업을 합니다: 매 단계마다 접두사 전체에 대한 어텐션을 다시 계산하니까요. 4K 토큰짜리 응답이라면 어텐션 연산이 1,600만 번이고, 그 대부분은 중복입니다. 접두사 토큰의 은닉 상태는 한 번 계산되면 결정론적입니다 — 새 토큰의 쿼리를, 앞에 있는 모든 토큰의 캐시된 키와 값에 대해 한 번만 돌리면 됩니다.

거기에 더해, 어텐션 자체도 데이터를 많이 옮깁니다. 표준 어텐션은 N×N 점수 행렬, N×d 소프트맥스 출력, N×d 최종 출력을 실제 메모리에 만들어 냅니다 — HBM(High Bandwidth Memory) 읽기/쓰기가 너무 많죠. N≥2K부터 어텐션은 FLOP 병목이 되기 전에 메모리 병목이 됩니다. 고전적 어텐션 커널은 최신 GPU를 4~10배나 못 씁니다.

Dao 외의 연구에서 나온 두 가지 최적화가 최전선 추론을 '느림'에서 '빠름'으로 바꿔 놓았습니다:

1. **KV 캐시.** 모든 접두사 토큰의 K, V 벡터를 저장합니다. 새 토큰의 어텐션은 캐시된 키에 대한 쿼리 하나죠. 생성 단계당 추론 비용이 `O(N²)`에서 `O(N)`으로 줄어듭니다.
2. **Flash Attention.** 어텐션 계산을 타일 단위로 쪼개서 N×N 행렬 전체가 HBM에 닿지 않게 합니다. 소프트맥스 + 행렬 곱이 전부 SRAM에서 일어납니다. A100에서 2~4배, FP8을 쓰는 H100에서는 5~10배의 벽시계 시간 단축입니다.

2026년 현재 이 둘은 보편 기술입니다. 모든 프로덕션 추론 스택(vLLM, TensorRT-LLM, SGLang, llama.cpp)이 이를 전제로 합니다. 모든 최전선 모델은 Flash Attention을 켠 채 출시됩니다.

## 개념

![KV 캐시 성장과 Flash Attention 타일링](../assets/kv-cache-flash-attn.svg)

### KV 캐시 계산

디코더 레이어 하나, 토큰 하나, 헤드 하나 기준:

```
bytes_per_token_per_layer = 2 * d_head * dtype_size
                          ^
                          K와 V
```

레이어 32개, 헤드 32개, d_head=128, fp16인 7B 모델이라면:

```
토큰 하나, 레이어 하나 = 2 * 128 * 2 = 512 bytes
토큰 하나(32개 레이어) = 16 KB
32K 컨텍스트 = 512 MB
```

Llama 3 70B(80개 레이어, d_head=128, KV 헤드 8개의 GQA)라면:

```
토큰 하나, 레이어 하나 = 2 * 8 * 128 * 2 = 4096 bytes (4 KB)
32K 컨텍스트 = 10.4 GB
```

그 10 GB 때문에 128K 컨텍스트의 Llama 3 70B는 배치 크기 1인데도 KV 캐시만으로 40 GB A100의 대부분을 잡아먹습니다.

**GQA가 KV 캐시의 승부처입니다.** 헤드 64개짜리 MHA라면 32 GB가 됩니다. MLA는 여기서 더 압축합니다.

차원을 끌어당기며 캐시 크기가 어떻게 변하는지 보세요. 시퀀스 길이나 배치를 키우면 한 대의 GPU를 얼마나 빨리 넘어서는지 확인할 수 있습니다:

```figure
kv-cache-sizer
```

### Flash Attention — 타일링 비법

표준 어텐션:

```
S = Q @ K^T          (HBM 읽기, N×N, HBM 쓰기)
P = softmax(S)       (HBM 읽기, HBM 쓰기)
O = P @ V            (HBM 읽기, HBM 쓰기)
```

HBM 왕복이 세 번입니다. H100 기준으로 HBM 대역폭은 3 TB/s, SRAM은 30 TB/s입니다. HBM 왕복 한 번이 칩 안에 다 두고 하는 것과 비교해 10배 느려지는 요인입니다.

Flash Attention:

```
Q의 각 블록마다 (타일 크기 ~128 × 128):
    Q_tile을 SRAM에 적재
    K, V의 각 블록마다:
        K_tile, V_tile을 SRAM에 적재
        S_tile = Q_tile @ K_tile^T 계산     (SRAM)
        진행형 softmax 집계                  (SRAM)
        O_tile에 누적                        (SRAM)
    O_tile을 HBM에 기록
```

타일당 HBM 왕복 한 번입니다. 전체 메모리 사용량이 `O(N²)`에서 `O(N)`으로 떨어집니다. 역전파는 순전파 값을 저장해 두는 대신 일부를 다시 계산합니다 — 메모리 측면의 또 하나의 승리죠.

**수치 비법.** 진행형 softmax는 타일을 넘나들며 `(최댓값, 합)`을 유지하므로 최종 정규화가 정확합니다. 근사가 아닙니다 — Flash Attention은 표준 어텐션과 비트 단위로 동일한 출력을 계산합니다(fp16 비결합성 오차는 제외).

**버전 발전사:**

| 버전 | 연도 | 핵심 변화 | 기준 하드웨어 대비 속도 |
|---------|------|-----------|-------------------------------|
| Flash 1 | 2022 | 타일화된 SRAM 커널 | A100에서 2배 |
| Flash 2 | 2023 | 더 나은 병렬화, 인과 마스크 우선 배치 | A100에서 3배 |
| Flash 3 | 2024 | Hopper 비동기성, FP8 | H100에서 1.5~2배 (~740 TFLOPs FP16) |
| Flash 4 | 2026 | Blackwell 5단계 파이프라인, 소프트웨어 exp2 | 추론 우선(초기에는 순전파만) |

Flash 4는 출시 당시 순전파 전용입니다. 학습에는 여전히 Flash 3를 씁니다. Flash 4의 GQA와 varlen 지원은 보류 중입니다(2026년 중반).

### 투기적 디코딩(speculative decoding) — 지연 시간의 또 다른 승수

값싼 모델이 토큰 N개를 제안합니다. 큰 모델이 N개를 병렬로 검증합니다. 검증이 k개를 수락하면, 큰 모델의 순전파 1번으로 k개를 생성한 셈입니다. 코드와 산문에서는 보통 k=3~5입니다.

2026년 기본 선택지:
- **EAGLE 2 / Medusa.** 검증자의 은닉 상태를 공유하는 통합형 드래프트 헤드. 품질 손실 없이 2~3배 속도 향상.
- **드래프트 모델을 곁들인 투기적 디코딩.** 소비자용 하드웨어에서 2~4배 속도 향상.
- **Lookahead 디코딩.** 야코비 반복; 드래프트 모델이 필요 없습니다. 틈새지만 공짜입니다.

### 연속 배칭(continuous batching)

고전적 배치 추론: 가장 느린 시퀀스가 끝날 때까지 기다렸다가 새 배치를 시작합니다. 짧은 응답이 먼저 끝나도 GPU는 놀게 됩니다.

연속 배칭(처음은 Orca에서, 지금은 vLLM, TensorRT-LLM, SGLang에서): 끝난 요청이 나가는 즉시 새 요청을 배치에 넣습니다. 전형적인 채팅 작업에서 5~10배 처리량 향상입니다.

### PagedAttention — 가상 메모리처럼 쓰는 KV 캐시

vLLM의 대표 기능입니다. KV 캐시를 16토큰 블록 단위로 할당하고, 페이지 테이블이 논리적 위치를 물리적 블록에 매핑합니다. 병렬 샘플(빔 서치, 병렬 샘플링) 간 KV 공유, 프롬프트 캐싱을 위한 접두사 핫스왑, 메모리 조각 모음이 가능해집니다. 순진한 연속 할당 대비 4배 처리량 향상입니다.

```figure
flash-attention-memory
```

## 만들어 보기

`code/main.py`를 보세요. 구현하는 것은:

1. 순진한 `O(N²)` 증분 디코더.
2. `O(N)` KV 캐시 디코더.
3. Flash Attention의 running-max 알고리즘을 흉내 내는 타일화된 softmax.

### 단계 1: KV 캐시

```python
class KVCache:
    def __init__(self, n_layers, n_heads, d_head):
        self.K = [[[] for _ in range(n_heads)] for _ in range(n_layers)]
        self.V = [[[] for _ in range(n_heads)] for _ in range(n_layers)]

    def append(self, layer, head, k, v):
        self.K[layer][head].append(k)
        self.V[layer][head].append(v)

    def read(self, layer, head):
        return self.K[layer][head], self.V[layer][head]
```

단순합니다: 레이어별, 헤드별 리스트에 토큰마다 K, V 벡터를 계속 쌓습니다.

### 단계 2: 타일화된 softmax

```python
def tiled_softmax_dot(q, K, V, tile=4):
    """running max/sum을 쓰는 Flash-attention 스타일 softmax(qK^T)V."""
    m = float("-inf")
    s = 0.0
    out = [0.0] * len(V[0])
    for start in range(0, len(K), tile):
        k_block = K[start:start + tile]
        v_block = V[start:start + tile]
        scores = [sum(qi * ki for qi, ki in zip(q, k)) for k in k_block]
        new_m = max(m, *scores)
        exp_old = math.exp(m - new_m) if m != float("-inf") else 0.0
        exp_new = [math.exp(sc - new_m) for sc in scores]
        s = s * exp_old + sum(exp_new)
        for j in range(len(out)):
            out[j] = out[j] * exp_old + sum(e * v[j] for e, v in zip(exp_new, v_block))
        m = new_m
    return [o / s for o in out]
```

`softmax(qK) V`를 한 번에 계산한 것과 비트 단위로 동일한 출력이지만, 어느 시점이든 작업 집합은 `tile × d_head` 블록 하나지 전체 `N × d_head`가 아닙니다.

### 단계 3: 100토큰 생성에서 순진한 방식 vs 캐시 방식 비교

어텐션 연산 수를 셉니다. 순진한 방식: `O(N²)` = 5050. 캐시: `O(N)` = 100. 코드가 둘 다 출력합니다.

## 사용해 보기

```python
# HuggingFace transformers는 decoder-only generate()에서 KV 캐시를 자동으로 켭니다.
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B",
    attn_implementation="flash_attention_2",  # Hopper면 FA3 사용
    torch_dtype="bfloat16",
)
# generate()는 KV 캐시를 자동으로 사용합니다
```

vLLM 프로덕션:

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 4 \
    --max-model-len 32768 \
    --enable-prefix-caching \
    --kv-cache-dtype fp8
```

요청 간 접두사 캐싱은 2026년의 큰 승수입니다 — 같은 시스템 프롬프트, 퓨샷 예시, 긴 컨텍스트 문서는 호출마다 KV를 재사용합니다. 도구 프롬프트를 반복하는 에이전트 작업에서 접두사 캐싱은 흔히 5배 처리량 향상으로 이어집니다.

## 출시하기

`outputs/skill-inference-optimizer.md`를 보세요. 이 스킬은 새 추론 배포를 위해 어텐션 구현, KV 캐시 전략, 양자화, 투기적 디코딩을 골라 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 순진한 디코더와 캐시 디코더가 같은 출력을 내는지 확인하고, 연산 수 차이를 기록합니다.
2. **보통.** 접두사 캐싱을 구현해 보세요: 프롬프트 P와 여러 완성문이 주어지면 P에 대해 순전파 한 번으로 KV 캐시를 채우고, 완성문마다 갈라져 나갑니다. P를 매번 다시 인코딩할 때와의 속도 향상을 측정합니다.
3. **어려움.** 장난감 PagedAttention을 구현해 보세요: 16토큰 고정 블록에 여유 목록(free-list)을 둔 KV 캐시입니다. 시퀀스가 끝나면 그 블록을 풀로 돌려보냅니다. 길이가 제각각인 채팅 완성 1,000건을 시뮬레이션하고, 연속 할당과 비교해 메모리 단편화를 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| KV 캐시 | "디코딩을 빠르게 만드는 비법" | 모든 접두사 토큰의 K와 V를 저장해 둔 것; 새 쿼리는 재계산 대신 이를 참조. |
| HBM | "GPU 메인 메모리" | High Bandwidth Memory; H100은 80 GB, B200은 192 GB. 대역폭 약 3 TB/s. |
| SRAM | "온칩 메모리" | SM별 고속 메모리, H100에서 SM당 약 256 KB. 대역폭 약 30 TB/s. |
| Flash Attention | "타일화된 어텐션 커널" | N×N 행렬을 HBM에 만들지 않고 어텐션을 계산. |
| 연속 배칭(Continuous batching) | "기다리지 않는 배칭" | 배치를 비우지 않고 끝난 시퀀스를 빼고 새 시퀀스를 넣음. |
| PagedAttention | "vLLM의 대표 기능" | 페이지 테이블과 함께 고정 블록 단위로 할당하는 KV 캐시; 단편화 제거. |
| 접두사 캐싱(Prefix caching) | "긴 프롬프트 재사용" | 공유 접두사의 KV를 요청 간에 캐시; 에이전트 비용을 크게 줄임. |
| 투기적 디코딩(Speculative decoding) | "드래프트 + 검증" | 값싼 드래프트 모델이 토큰을 제안; 큰 모델이 한 번에 k개를 검증. |

## 더 읽을거리

- [Dao 외 (2022). FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) — Flash 1.
- [Dao (2023). FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) — Flash 2.
- [Shah 외 (2024). FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](https://arxiv.org/abs/2407.08608) — Flash 3.
- [FlashAttention-4 릴리스 노트 (Dao-AILab, 2026)](https://github.com/Dao-AILab/flash-attention) — Blackwell 5단계 파이프라인과 소프트웨어 exp2 비법; 이 레슨에서 언급한 순전파 전용 출시 주의사항은 저장소 README를 읽어 보세요.
- [Kwon 외 (2023). Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) — vLLM 논문.
- [Leviathan 외 (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — 투기적 디코딩.
- [Li 외 (2024). EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077) — 이 레슨이 인용한 통합형 드래프트 방식의 EAGLE-1/2 논문.
- [Cai 외 (2024). Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774) — EAGLE와 함께 언급되는 Medusa 방식.
- [vLLM 문서 — PagedAttention](https://docs.vllm.ai/en/latest/design/kernel/paged_attention.html) — 16토큰 블록과 페이지 테이블 설계에 관한 정석적인 심화 자료.
