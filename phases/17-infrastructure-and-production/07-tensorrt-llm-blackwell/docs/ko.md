> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 하드웨어 특화 추론 컴파일 — Blackwell에서의 FP8과 NVFP4

> 하드웨어 특화 추론 컴파일은 이식성을 처리량과 맞바꾸는 거래이고, TensorRT-LLM — NVIDIA 전용, Blackwell에 맞춘 — 은 이 거래가 먹힌다는 가장 선명한 사례입니다. Dynamo 오케스트레이션과 함께 돌리는 GB200 NVL72에서 SemiAnalysis InferenceX는 2026년 1~2분기, 120B 모델 기준 백만 토큰당 $0.012를 측정했습니다. H100 + vLLM의 $0.09/M과 겨루면 경제 격차가 7배입니다. 이 스택은 세 개의 부동소수점 체제가 겹쳐 효과를 냅니다. FP8은 KV 캐시와 어텐션 커널에 필요한 동적 범위를 갖고 있어 여전히 필수입니다. NVFP4(4비트 마이크로스케일링)는 가중치와 활성값을 담당합니다. 여기에 멀티 토큰 예측(MTP)과 분리형 프리필/디코드가 그 위에 2~3배를 더 얹습니다. Day-0 모델 지원은 학습 후 변환 없이 FP4 가중치를 그대로 불러옵니다. 2026년 엔지니어링 팀에게 붙는 단서: TRT-LLM은 오픈소스지만 NVIDIA 전용 — CUDA와 Blackwell에 특화 — 이므로, 채택한다는 건 이식성을 처리량과 맞바꾸는 일입니다. 커밋하기 전에 여러분의 모델·하드웨어 조합으로 계산을 직접 돌려 보세요.

**유형:** Learn
**언어:** Python (표준 라이브러리, 장난감 수준 FP8/NVFP4 메모리·비용 계산기)
**선수 지식:** Phase 17 · 04 (서빙 엔진 내부 구조), Phase 10 · 13 (양자화)
**시간:** 약 75분

## 학습 목표

- 가중치가 NVFP4인데도 KV 캐시와 어텐션에는 FP8이 여전히 필수인 이유를 설명할 수 있다.
- 프론티어 모델의 HBM 점유를 BF16, FP8, NVFP4 각각에 대해 계산하고, 절약이 어디서 오는지 추론할 수 있다.
- TRT-LLM이 활용하는 Blackwell 전용 기능들을 말할 수 있다(day-0 FP4, MTP, 분리형 서빙, 올투올 프리미티브).
- 어떤 조건에서 TRT-LLM의 NVIDIA 락인이 Hopper 위의 vLLM 대비 7배 비용 격차를 정당화하는지 판단할 수 있다.

## 문제 상황

2026년 추론 경제학의 최전선은 "달러당 몇 토큰"입니다. 답은 네 가지 선택이 쌓인 결과입니다: 하드웨어 세대(Hopper H100/H200 vs Blackwell B200/GB200), 정밀도(BF16 → FP8 → NVFP4), 서빙 엔진(vLLM vs SGLang vs TRT-LLM), 오케스트레이션(평범 vs 분리형 vs Dynamo).

vLLM을 얹은 Hopper에서는 120B MoE가 백만 토큰당 약 $0.09입니다. TRT-LLM + Dynamo를 얹은 Blackwell에서는 같은 모델이 약 $0.012 — 7배 더 쌉니다. 격차의 일부는 하드웨어입니다(Blackwell은 GPU당 LLM 처리량이 Hopper 대비 11~15배). 일부는 스택입니다. FP4 가중치, MTP 드래프트, 분리형 프리필/디코드, MoE 전문가 통신을 위한 NVLink 5 올투올이 그렇습니다.

NVIDIA 스택 밖에서는 이걸 재현할 수 없습니다. 그게 트레이드오프입니다 — 경제성과 맞바꾸는 이식성. 어떤 스택 선택이 격차의 어느 몫을 주는지 이해하는 것이 이 레슨의 핵심입니다.

## 개념

### FP8이 여전히 KV 캐시의 바닥값인 이유

2026년의 흔한 실수: NVFP4가 모든 곳에 적용된다고 가정하는 것. 그렇지 않습니다. KV 캐시에는 FP8(8비트 부동소수점)이 필요합니다. 넓은 동적 범위를 가로지르는 어텐션 키와 값을 저장하기 때문입니다. KV를 FP4로 양자화하면 치명적인 정확도 손실이 옵니다 — 분포의 꼬리가 떨어져 나가고 어텐션 점수가 무너집니다. FP8의 지수 비트가 KV 캐시에 필요한 범위를 주는 겁니다.

NVFP4(2025-2026)는 가중치와 활성값에 적용됩니다. 마이크로스케일링: 가중치 블록마다 자체 스케일 팩터를 가져서, 작은 블록들이 텐서 단위 스케일 손실 없이 서로 다른 동적 범위를 커버할 수 있습니다. 활성값에서 FP4가 버티는 이유는, 활성값이 레이어 안에서는 범위가 좁기 때문입니다.

전형적인 Blackwell 설정:

- 가중치: NVFP4 (4비트 마이크로스케일링).
- 활성값: NVFP4.
- KV 캐시: FP8.
- 어텐션 누적기: FP32 (softmax 안정성).

### TRT-LLM이 쓰는 Blackwell 전용 프리미티브

- **Day-0 FP4 가중치**: 모델 제공자가 FP4 가중치를 그대로 출시하고, TRT-LLM은 학습 후 변환 없이 불러옵니다. FP4에는 AWQ / GPTQ 단계가 없습니다.
- **멀티 토큰 예측(MTP)**: EAGLE(Phase 17 · 05)과 같은 아이디어인데 TRT-LLM 빌드에 통합되어 있습니다.
- **분리형 서빙**: 프리필과 디코드를 별개 GPU 풀에서 돌리고, KV 캐시를 NVLink 또는 InfiniBand로 전송합니다. Dynamo(Phase 17 · 20)와 같은 아이디어입니다.
- **올투올 통신 프리미티브**: NVLink 5가 MoE 전문가 통신 지연을 Hopper 대비 3배 줄였습니다. TRT-LLM의 MoE 커널은 이에 맞춰 튜닝되어 있습니다.
- **NVFP4 + MXFP8 마이크로스케일링**: Blackwell Tensor Cores에서 하드웨어 가속되는 스케일 팩터 처리.

### 외워 둘 숫자들

- HGX B200: TRT-LLM으로 GPT-OSS-120B에서 $0.02/M 토큰.
- GB200 NVL72: Dynamo(TRT-LLM 오케스트레이션)로 $0.012/M 토큰.
- H100 + vLLM: 비슷한 워크로드에서 약 $0.09/M 토큰.
- 3개월간 TRT-LLM 업데이트만으로 2.8배 처리량 향상(2026).
- GPU당 LLM 처리량, Blackwell vs Hopper: 11~15배.
- MLPerf Inference v6.0 (2026년 4월): 제출된 모든 태스크에서 Blackwell 압도.

### FP4가 품질에 실제로 부과하는 비용

NVFP4는 공격적입니다. 추론 사고가 많은(reasoning-heavy) 워크로드(사고의 연쇄, 수학, 긴 컨텍스트 코드 생성)에서는 FP4 가중치의 저하가 눈에 띕니다. 블록별 캘리브레이션이 완화하지만 없애지는 않습니다. 추론 모델을 출시하는 팀들은 종종 FP8 가중치 + FP4 활성값이라는 절충안을 쓰거나, 전체를 FP8로 유지하며 H200에 머뭅니다.

규칙: NVFP4 가중치를 결정하기 전에 항상 여러분의 eval 세트에서 태스크 품질을 검증하세요.

### 이것이 NVIDIA 락인 결정인 이유

TRT-LLM은 C++ + CUDA + 클로즈드소스 커널입니다. 모델은 특정 GPU SKU에 맞춰 컴파일되어야 합니다. AMD도, Intel도, ARM도 안 됩니다. 인프라 전략이 멀티 벤더라면 TRT-LLM이 서빙하는 티어는 처음부터 논외입니다 — 혼합 하드웨어에서는 vLLM으로 서빙할 수 있습니다. NVIDIA 온리라면 7배 격차가 락인 값을 지불해 줍니다.

### 2026년 실전 레시피

연간 $100M+ 추론 비용이라면 Hopper + vLLM에 머무는 것은 7~10배를 탁자에 두는 일입니다. 비용이 지배하는 워크로드를 Blackwell + TRT-LLM + Dynamo로 옮기세요. 모델 반복 속도를 위해 실험 티어는 H100 + vLLM에 유지하세요. NVFP4로 전환한 모델은 각각 프로덕션(운영 환경) 전에 품질을 검증하세요.

### 분리형 보너스

TRT-LLM의 분리형 서빙(프리필 풀과 디코드 풀 분리)은 Phase 17 · 20에서 자세히 다룹니다. Blackwell에서는 배율이 겹쳐 쌓입니다. FP4 가중치 × MTP 가속 × 분리형 배치 × 캐시 인식 라우팅. 7배 숫자는 이 풀 스택을 전제합니다.

```figure
pipeline-parallel
```

## 직접 써보기

`code/main.py`는 세 스택 — H100 + BF16 + vLLM, H100 + FP8 + vLLM, B200 + NVFP4/FP8 + TRT-LLM — 에서 모델의 HBM 점유, 디코드 처리량(메모리 바운드 체제), $/백만 토큰을 계산합니다. 실행해 보면 복합 효과와, 각 변경이 격차에 기여하는 몫을 볼 수 있습니다.

## 산출물

이 레슨은 `outputs/skill-trtllm-blackwell-advisor.md`를 만듭니다. 워크로드, 모델 크기, 연간 토큰 물량이 주어지면 Blackwell + TRT-LLM 스택이 NVIDIA 락인 값어치를 하는지 판단합니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 활성 파라미터 30%인 120B MoE에 대해 H100 BF16, H100 FP8, B200 NVFP4/FP8의 메모리 대역폭 제약 디코드 처리량을 계산하세요. 가장 큰 점프는 어디서 오나요?
2. 어떤 고객이 H100 + vLLM에 연 $2M을 쓰고 있습니다. 7배 경제 격차를 감안해, 12개월 안에 TRT-LLM 마이그레이션 비용을 회수하려면 Blackwell GPU를 몇 장 사야 하나요?
3. NVFP4 가중치 전환 후 MATH에서 정확도가 3포인트 떨어졌습니다. 회복 경로 두 가지를 말하세요. 하나는 품질 우선(FP8 가중치 유지), 하나는 비용 우선(도메인 내 데이터로 캘리브레이션).
4. MLPerf v6.0 추론 결과를 읽으세요. Blackwell이 Hopper를 앞서는 격차가 가장 작은 태스크는 무엇이고, 왜 그런가요?
5. 405B 모델을 NVFP4 가중치 + FP8 KV 캐시, 128k 컨텍스트로 돌리는 데 필요한 HBM을 계산하세요. GB200 NVL72 노드 한 대에 들어가나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| FP8 | "8비트 부동소수점" | 8비트 부동소수점. 동적 범위 때문에 KV 캐시와 어텐션에 사용 |
| NVFP4 | "4비트 마이크로" | NVIDIA의 4비트 마이크로스케일링 FP 포맷. Blackwell에서 가중치와 활성값 담당 |
| MXFP8 | "MX 여덟" | 마이크로스케일링 FP8 변형. Blackwell Tensor Cores에서 하드웨어 가속 |
| Day-0 FP4 | "FP4 가중치 그대로 출시" | 모델 제공자가 FP4 가중치를 바로 출시. 학습 후 변환 단계 없음 |
| MTP | "멀티 토큰 예측" | TRT-LLM에 통합된 스페큘러티브 디코딩 드래프트 (Phase 17 · 05) |
| 분리형 서빙 | "프리필/디코드 분리" | 프리필과 디코드를 별개 GPU 풀에서. KV는 NVLink/IB로 전송 |
| 올투올 | "MoE 전문가 통신" | 토큰을 전문가 GPU로 라우팅하는 통신 패턴. NVLink 5가 3배 절감 |
| InferenceX | "SemiAnalysis 추론 벤치" | 2026년 업계 표준 토큰당 비용 벤치마크 |

## 더 읽을거리

- [NVIDIA — Blackwell Ultra MLPerf Inference v6.0](https://developer.nvidia.com/blog/nvidia-blackwell-ultra-sets-new-inference-records-in-mlperf-debut/) — 2026년 4월 MLPerf 결과.
- [NVIDIA — MoE Inference on Blackwell](https://developer.nvidia.com/blog/delivering-massive-performance-leaps-for-mixture-of-experts-inference-on-nvidia-blackwell/) — NVLink 5 올투올과 MoE 커널.
- [TensorRT-LLM Overview](https://nvidia.github.io/TensorRT-LLM/overview.html) — 공식 엔진 문서.
- [NVIDIA — Introducing Dynamo](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/) — TRT-LLM 위의 분리형 오케스트레이션.
- [MLPerf Inference](https://mlcommons.org/benchmarks/inference-datacenter/) — Blackwell 숫자를 발표하는 벤치마크 스위트.
