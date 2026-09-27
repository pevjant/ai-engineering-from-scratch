> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# DeepSeek-V3 아키텍처 둘러보기

> 페이즈 10 · 레슨 14에서는 모든 오픈 모델이 조절하는 여섯 가지 아키텍처 다이얼을 살펴봤습니다. DeepSeek-V3(2024년 12월, 총 671B 파라미터, 활성 37B)는 이 여섯 개를 모두 돌리는 데서 그치지 않고 네 가지를 더 추가했습니다: Multi-Head Latent Attention(MLA), 보조 손실 없는(auxiliary-loss-free) 로드 밸런싱, Multi-Token Prediction(MTP), 그리고 DualPipe 학습입니다. 이 레슨에서는 DeepSeek-V3의 아키텍처를 위에서 아래까지 훑어보고, 공개된 설정값(config)에서 모든 파라미터 개수를 직접 유도해 봅니다. 이 레슨을 마치면 671B/37B 비율이 왜 옳은 선택인지, 그리고 프론티어(최전선)급 모델에서 MLA와 MoE를 함께 쓰는 것이 둘 중 하나만 쓰는 것보다 왜 나은지 설명할 수 있게 됩니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 파라미터 계산기)
**선수 지식:** 페이즈 10 · 14 (오픈 모델 둘러보기), 페이즈 10 · 17 (NSA), 페이즈 10 · 18 (MTP), 페이즈 10 · 19 (DualPipe)
**시간:** 약 75분

## 학습 목표

- DeepSeek-V3 설정값을 위에서 아래까지 읽고, 각 필드를 GPT-2의 여섯 가지 다이얼에 DeepSeek 고유의 네 가지 추가 요소를 더한 관점에서 설명할 수 있다.
- 전체 파라미터 수(671B), 활성 파라미터 수(37B), 그리고 각 숫자에 기여하는 구성 요소를 유도할 수 있다.
- 128k 컨텍스트에서 MLA의 KV 캐시 크기를 계산하고, 활성 파라미터가 같은 GQA 기반 밀집(dense) 모델이 감당해야 할 크기와 비교할 수 있다.
- DeepSeek 고유의 네 가지 혁신(MLA, MTP, 보조 손실 없는 라우팅, DualPipe)을 꼽고, 각각이 아키텍처/학습 스택의 어느 부분을 겨냥한 것인지 말할 수 있다.

## 문제 상황

DeepSeek-V3는 아키텍처가 Llama 계열과 의미 있게 다른 최초의 프론티어 오픈 모델입니다. Llama 3 405B는 "다이얼을 여섯 개 돌린 GPT-2"였습니다. DeepSeek-V3는 여섯 개 다이얼을 모두 돌리고 네 개를 더 얹은 GPT-2입니다. Llama 3 설정값을 읽는 것은 DeepSeek 설정값을 읽기 위한 워밍업이지만, 깊은 구조 — 어텐션 블록의 형태, 라우팅 로직, 학습 시 목적 함수 — 는 충분히 달라서 별도의 둘러보기가 필요합니다.

이걸 배워서 얻는 것: DeepSeek-V3의 오픈 웨이트 공개는 오픈 모델에서 "프론티어급 성능"이 무엇을 의미하는지 바꿔 놓았습니다. 이 아키텍처는 2026년의 수많은 학습 러닝(run)이 베끼고 있는 청사진입니다. 프론티어 LLM 학습이나 추론에 손대는 어떤 역할이든, 이것을 이해하는 것은 기본 소양입니다.

## 개념

### 다시 보는 불변의 코어

DeepSeek-V3도 여전히 자기회귀(autoregressive) 모델입니다. 여전히 디코더 블록을 쌓습니다. 각 블록은 여전히 어텐션 + MLP + 두 개의 RMSNorm으로 이루어져 있습니다. MLP 안에서 여전히 SwiGLU를 쓰고, RoPE도 씁니다. Pre-norm 방식, 웨이트 타이(weight-tied) 임베딩도 그대로입니다. Llama든 Mistral이든 모든 모델과 같은 베이스라인입니다.

### 비틀기 1: GQA 대신 MLA

페이즈 10 · 14에서 배웠듯이 GQA는 Q 헤드 그룹들이 K와 V를 공유하게 해서 KV 캐시를 줄입니다. Multi-Head Latent Attention(MLA)은 한 걸음 더 나아갑니다. K와 V를 하나의 공유 저랭크(latent) 잠재 표현(`kv_lora_rank`)으로 압축해 뒀다가, 필요할 때 헤드별로 즉석에서 다시 펼치는(decompress) 것입니다. KV 캐시에는 잠재 표현만 저장합니다. 토큰당 레이어당 보통 512개의 부동소수점 값이면 되고, 8 x 128 = 1024개가 필요하지 않습니다.

128k 컨텍스트에서 MLA를 쓰는 DeepSeek-V3는 (토큰당 레이어당 공유 잠재 표현 `c^{KV}` 하나; K와 V는 모두 이 잠재 표현을 업 프로젝션해서 얻는데, 이 업 프로젝션은 뒤따르는 행렬 곱에 흡수될 수 있습니다):

```
kv_cache = num_layers * kv_lora_rank * max_seq_len * bytes_per_element
         = 61 * 512 * 131072 * 2
         = 7.6 GB
```

가상의 GQA 베이스라인(Llama 3 70B 형태, KV 헤드 8개, 헤드 차원 128)이라면:

```
kv_cache = 2 * 61 * 8 * 128 * 131072 * 2
         = 30.5 GB
```

MLA는 128k 컨텍스트에서 Llama-3-70B 스타일 GQA 캐시보다 4배 작습니다.

트레이드오프: MLA는 어텐션을 계산할 때마다(헤드마다) 압축 해제 단계를 하나 추가합니다. 하지만 이 추가 연산 비용은 절약되는 대역폭에 비하면 아주 작습니다. 긴 컨텍스트 추론에서는 전체적으로 이득입니다.

### 라우팅: 보조 손실 없는(auxiliary-loss-free) 로드 밸런싱

MoE 라우터는 각 토큰을 어떤 top-k 전문가(expert)가 처리할지 결정합니다. 순진한 라우터는 소수 전문가에게 일이 몰리게 두고 나머지는 놀게 만듭니다. 표준적인 해법은 부하 불균형에 벌점을 주는 보조 손실(auxiliary loss) 항을 추가하는 것입니다. 이 방법은 효과가 있지만 본래 작업 성능이 조금 떨어집니다.

DeepSeek-V3는 보조 손실 없는 방식을 도입했습니다. 전문가별 편향(bias) 항을 라우터 로짓에 더하고, 학습 중에 간단한 규칙으로 조정합니다. 전문가 `e`에 부하가 몰리면 `bias_e`를 낮추고, 놀고 있으면 올립니다. 별도의 손실 항이 없습니다. 학습은 깔끔하게 유지되고, 전문가 부하는 균형을 유지합니다.

본래 손실에 미치는 영향: 측정될 만큼 없습니다. MoE 아키텍처에 미치는 영향: 더 깔끔해져서, 튜닝할 보조 손실 하이퍼파라미터가 사라집니다.

### MTP: 더 촘촘한 학습 + 공짜 드래프트

페이즈 10 · 18에서 배웠듯이 DeepSeek-V3는 두 위치 앞의 토큰을 예측하는 D=1 MTP 모듈을 추가합니다. 추론 시에는 학습된 이 모듈을 스페큘레이티브 디코딩(플래닝 디코딩)의 드래프트 모델로 재활용하는데, 수용률(acceptance rate)이 80% 이상 나옵니다. 학습 시에는 각 은닉 상태가 D+1 = 2개의 타깃으로 감독되어, 더 촘촘한(dense) 학습 신호를 제공합니다.

파라미터: 본체 671B에 추가로 14B. 오버헤드는 2.1%입니다.

### 학습: DualPipe

페이즈 10 · 19에서 배웠듯이 DualPipe는 순전파/역전파 청크를 노드 간 all-to-all 통신과 겹치게 돌리는 양방향 파이프라인입니다. DeepSeek-V3의 2,048장 H800 규모에서는 1F1B 방식이 파이프라인 버블로 잃었을 약 245k GPU시간을 되찾아 줍니다.

### 설정값, 필드 하나하나

DeepSeek-V3 설정값입니다(단순화):

```
hidden_size: 7168
intermediate_size: 18432   (dense MLP hidden size, used on first few layers)
moe_intermediate_size: 2048 (expert MLP hidden size)
num_hidden_layers: 61
first_k_dense_layers: 3    (first 3 layers use dense MLP)
num_attention_heads: 128
num_key_value_heads: 128   (formally equal to num_heads under MLA, but
                           the real compression is in kv_lora_rank)
kv_lora_rank: 512          (MLA latent dimension)
num_experts: 256            (MoE expert count per block)
num_experts_per_tok: 8      (top-8 routing)
shared_experts: 1           (always-on shared expert per block)
max_position_embeddings: 163840
rope_theta: 10000.0
vocab_size: 129280
mtp_module: 1               (1 MTP module at depth 1)
```

해석해 보면:

- `hidden_size=7168`: 임베딩 차원.
- `num_hidden_layers=61`: 전체 블록 깊이.
- `first_k_dense_layers=3`: 처음 3개 블록은 크기 18432의 밀집 MLP를 사용합니다. 나머지 58개는 MoE를 사용합니다.
- `num_attention_heads=128`: 쿼리 헤드 128개.
- `kv_lora_rank=512`: K와 V가 이 잠재 차원으로 압축되고, 헤드별로 다시 펼쳐집니다.
- `num_experts=256, num_experts_per_tok=8`: 각 MoE 블록에는 전문가 256개가 있고, top-8 라우팅을 합니다.
- `shared_experts=1`: 256개의 라우팅 전문가 위에, 모든 토큰에 항상 기여하는 전문가가 1개 더 있습니다. 모든 토큰이 확실한 뭔가를 받도록 보장하는 "밀집 바닥판"이라고 생각하면 됩니다.
- `moe_intermediate_size=2048`: 각 전문가의 MLP 은닉 크기. 전문가가 256개나 되니 밀집 MLP보다 작습니다.

### 파라미터 계산

전체 계산은 `code/main.py`에 들어 있습니다. 요약하면:

- 임베딩: `vocab * hidden = 129280 * 7168 = 약 0.93B`.
- 처음 3개 밀집 블록: MLA 어텐션(블록당 약 144M) + 밀집 MLP(블록당 약 260M) + 정규화 레이어. 합계 약 1.2B.
- 58개 MoE 블록: MLA 어텐션(약 144M) + 전문가 256개(개당 30M) + 공유 전문가 1개(30M) + 정규화 레이어. 모든 전문가를 포함해 블록당 약 7.95B. 58개 MoE 블록 전체로 461B.
- MTP 모듈: 14B.

총합: 코어 아키텍처 약 476B + MTP 14B. 여기에 더해, 공개된 671B라는 숫자에는 추가 구조 파라미터(편향 텐서, 전문가별 구성 요소, 공유 전문가 스케일링 등)가 반영되어 있습니다. 계산기가 재현하는 숫자는 공개치와 3~5% 이내입니다. 이 차이는 DeepSeek 보고서 2장 부록에 문서화된 세밀한 계산 항목에서 옵니다.

순전파 1회당 활성 파라미터:

- 어텐션: 레이어당 144M * 61 = 8.8B (모든 레이어가 작동).
- 활성 MLP: 처음 3개 레이어는 밀집(3 * 260M = 780M), 58개 MoE 레이어는 각각 라우팅된 8개 + 공유 1개 + 라우팅 오버헤드로 작동. 레이어당 활성 MLP: 약 260M. 합계: 3 * 260M + 58 * 260M = 약 15.9B.
- 임베딩 + 정규화 레이어: 1.2B.
- 총 활성: 코어 약 26B + MTP 14B(학습되지만 추론 시 항상 돌아가는 건 아님) ≈ 37B.

### 671B / 37B 비율

18배 희소(sparsity) 비율입니다(활성 파라미터가 전체의 5.5%). DeepSeek-V3는 오픈 웨이트가 공개된 프론티어 MoE 모델 중 가장 희소한 모델입니다. 비율 13/47(28%)인 Mixtral 8x7B는 훨씬 촘촘합니다. 비율 17B/400B(4.25%)인 Llama 4 Maverick은 비슷한 수준입니다. DeepSeek의 베팅은 이것입니다: 프론티어 규모에서는 전문가를 더 많이 두고 활성화 비율을 낮출수록, 활성 FLOP당 품질이 더 좋아진다는 것입니다.

### DeepSeek-V3의 위치

| 모델 | 전체 | 활성 | 비율 | 어텐션 | 새로운 아이디어 |
|-------|------|-------|-------|-----------|-------------|
| Llama 3 70B | 70B | 70B | 100% | GQA 64/8 | — |
| Llama 4 Maverick | 400B | 17B | 4.25% | GQA | — |
| Mixtral 8x22B | 141B | 39B | 27% | GQA | — |
| DeepSeek V3 | 671B | 37B | 5.5% | MLA 512 | MLA + MTP + 보조 손실 없음 + DualPipe |
| Qwen 2.5 72B | 72B | 72B | 100% | GQA 64/8 | YaRN 확장 |

### 후속: R1, V4

DeepSeek-R1(2025)은 V3 백본 위에서 수행한 추론 학습 러닝입니다. R1도 같은 아키텍처를 사용합니다. 바뀐 것은 사후 학습(post-training) 레시피(검증 가능한 작업에 대한 대규모 강화 학습)이지, 사전학습 아키텍처가 아닙니다.

DeepSeek-V4(출시된다면)는 MLA + MoE + MTP를 유지하고, 페이즈 10 · 17의 NSA 뒤를 잇는 DSA(DeepSeek Sparse Attention)를 추가할 것으로 예상됩니다. 계보는 안정적입니다. 아키텍처 수준의 혁신은 누적되고, 버전마다 다이얼을 추가로 돌립니다.

```figure
moe-routing
```

## 사용해 보기

`code/main.py`는 DeepSeek-V3 형태에 특화된 파라미터 계산기입니다. 실행해서 출력값을 논문의 숫자와 비교해 보고, 가상의 변형(전문가 256 vs 512, top-8 vs top-16, MLA 랭크 512 vs 1024)에도 적용해 보세요.

살펴볼 것:

- 전체 파라미터 수 vs 공개된 671B.
- 활성 파라미터 수 vs 공개된 37B.
- 128k 컨텍스트에서의 KV 캐시 — MLA vs GQA 비교.
- 레이어별 분석 — 파라미터 예산이 실제로 어디에 쓰이는지.

## 출시하기

이 레슨은 `outputs/skill-deepseek-v3-reader.md`를 산출합니다. DeepSeek 계열 모델(V3, R1, 또는 미래의 변형)이 주어지면, 설정값의 각 필드를 짚어주고 구성 요소별 파라미터 수를 유도하며, 네 가지 DeepSeek 고유 혁신 중 어떤 것이 쓰였는지 식별하는 구성 요소별 아키텍처 독해 결과를 만들어 냅니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 계산기의 전체 파라미터 추정치를 공개된 671B와 비교하고, 차이가 어디에서 오는지 찾아보세요. 논문 2장에 전체 항목별 내역이 있습니다.

2. 설정값을 MLA 랭크 512 대신 256을 쓰도록 수정하세요. 128k 컨텍스트에서 그에 따른 KV 캐시 크기를 계산해 보세요. 몇 퍼센트를 줄여 주고, 헤드별 표현력에는 어떤 비용이 드나요?

3. DeepSeek-V3의 (전문가 256개, top-8) 라우팅을 가상의 (전문가 512개, top-8) 변형과 비교해 보세요. 전체 파라미터는 늘지만 활성 파라미터는 그대로입니다. 추가 전문가 용량은 이론적으로 무엇을 사 주고, 추론 시에는 무엇을 대가로 요구하나요?

4. DeepSeek-V3 기술 보고서(arXiv:2412.19437)의 2.1절 MLA 부분을 읽으세요. K와 V 압축 해제 행렬이 추론 효율을 위해 뒤따르는 행렬 곱에 "흡수"될 수 있는 이유를 세 문장으로 설명해 보세요.

5. DeepSeek-V3는 대부분의 연산에 FP8 학습을 사용합니다. 671B 가중치를 저장할 때 FP8이 BF16에 비해 주는 메모리 절감을 계산해 보세요. 이것이 14.8T 토큰 학습 예산과 어떻게 맞물릴까요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| MLA | "Multi-Head Latent Attention" | K와 V를 공유 저랭크 잠재 표현(kv_lora_rank, 보통 512)으로 압축하고 헤드별로 즉석에서 펼침. KV 캐시에는 잠재 표현만 저장 |
| kv_lora_rank | "MLA 압축 차원" | K와 V의 공유 잠재 표현 크기. DeepSeek-V3는 512 사용 |
| First k dense layers | "초반 레이어는 밀집 유지" | MoE 모델의 처음 몇 개 레이어는 안정성을 위해 MoE 라우터를 건너뛰고 밀집 MLP를 실행 |
| num_experts_per_tok | "Top-k 라우팅" | 토큰당 몇 개의 라우팅 전문가가 작동하는지. DeepSeek-V3는 8 사용 |
| Shared experts | "항상 켜져 있는 전문가" | 라우팅 결과와 무관하게 모든 토큰을 처리하는 전문가. DeepSeek-V3는 1개 사용 |
| Auxiliary-loss-free routing | "편향 조정 로드 밸런싱" | 손실 항을 추가하지 않고도 전문가 부하를 균형 있게 유지하도록, 학습 중에 전문가별 편향 항을 조정하는 방식 |
| MTP module | "추가 예측 헤드" | h^(1)과 E(t+1)로 t+2를 예측하는 트랜스포머 블록. 더 촘촘한 학습, 스페큘레이티브 디코딩 드래프트로 무료 재활용 |
| DualPipe | "양방향 파이프라인" | 순전파/역전파 연산을 노드 간 all-to-all 통신과 겹치게 돌리는 학습 스케줄 |
| Active parameter ratio | "희소성" | active_params / total_params. DeepSeek-V3는 5.5% 달성 |
| FP8 training | "8비트 학습" | 학습 저장과 대부분의 연산을 FP8로 수행. BF16 대비 약 절반의 메모리, 작은 품질 비용 |

## 더 읽을거리

- [DeepSeek-AI — DeepSeek-V3 Technical Report (arXiv:2412.19437)](https://arxiv.org/abs/2412.19437) — 전체 아키텍처, 학습, 결과가 담긴 문서
- [Hugging Face의 DeepSeek-V3 모델 카드](https://huggingface.co/deepseek-ai/DeepSeek-V3) — 설정 파일과 배포 노트
- [DeepSeek-V2 논문 (arXiv:2405.04434)](https://arxiv.org/abs/2405.04434) — MLA를 처음 소개한 선행 모델
- [DeepSeek-R1 논문 (arXiv:2501.12948)](https://arxiv.org/abs/2501.12948) — V3 아키텍처 기반의 추론 학습 후속 모델
- [Native Sparse Attention (arXiv:2502.11089)](https://arxiv.org/abs/2502.11089) — DeepSeek 계열 어텐션의 미래 방향
- [DualPipe 저장소](https://github.com/deepseek-ai/DualPipe) — 학습 스케줄 레퍼런스
