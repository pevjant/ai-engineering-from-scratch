> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 추론 지표 — TTFT, TPOT, ITL, 굿푸트, P99

> 추론 배포가 잘 돌아가는지를 가리는 지표는 넷입니다. TTFT는 프리필 + 큐 + 네트워크입니다. TPOT(ITL과 같은 말)는 메모리 바운드인 토큰당 디코드 비용입니다. 엔드투엔드(E2E) 지연은 TTFT + TPOT × 출력 길이입니다. 처리량은 플릿 전체를 합친 초당 토큰 수입니다. 하지만 제품 관점에서 진짜 중요한 것은 굿푸트(goodput)입니다 — 모든 SLO를 동시에 충족한 요청의 비율이죠. 낮은 굿푸트에서의 높은 처리량은, 제때 사용자에게 닿지 못하는 토큰을 열심히 처리하고 있다는 뜻입니다. 2026년 TRT-LLM의 Llama-3.1-8B-Instruct 기준 참고 숫자: 평균 TTFT 162ms, 평균 TPOT 7.33ms, 평균 E2E 1,093ms. 항상 P50, P90, P99를 보고하세요 — 평균만 내는 건 금물입니다. 그리고 측정 함정을 조심하세요. GenAI-Perf는 ITL 계산에서 TTFT를 빼고, LLMPerf는 넣습니다. 같은 실행에서 두 도구의 TPOT이 서로 다릅니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 장난감 수준 백분위 계산기 및 굿푸트 리포터)
**선수 지식:** Phase 17 · 04 (서빙 엔진 내부 구조)
**시간:** 약 60분

## 학습 목표

- TTFT, TPOT, ITL, E2E, 처리량, 굿푸트를 정확히 정의하고, 각각이 무엇을 측정하는 구성 요소인지 말할 수 있다.
- LLM 서빙에서 평균이 잘못된 통계량인 이유와 P50/P90/P99를 읽는 법을 설명할 수 있다.
- SLO 다중 제약(예: TTFT<500ms AND TPOT<15ms AND E2E<2초)을 만들고, 그에 대한 굿푸트를 계산할 수 있다.
- 같은 실행에서 TPOT이 서로 다르게 나오는 벤치마크 도구 두 개를 말하고, 그 이유를 설명할 수 있다.

## 문제 상황

"우리 처리량은 초당 15,000 토큰입니다." 그래서 뭐죠? 요청의 40%가 엔드투엔드 2초를 넘겨서 사용자가 세션을 끊었다면? 처리량만으로는 제품이 동작하는지 알 수 없습니다.

추론에는 지연의 축이 여러 개이고, 각각이 서로 다르게 무너집니다. 프리필은 컴퓨트 바운드이고 프롬프트 길이에 비례해 커집니다. 디코드는 메모리 바운드이고 배치 크기에 비례합니다. 큐 지연은 운영 문제입니다. 네트워크는 물리적 거리 문제입니다. 각각을 위한 개별 지표가 필요하고, 백분위가 필요하고, "사용자가 기대한 것을 받았는가"를 한 줄로 말해 주는 합성 지표가 필요합니다 — 그것이 굿푸트입니다.

## 개념

### TTFT — 첫 토큰까지의 시간

`TTFT = queue_time + network_request + prefill_time`

프롬프트가 길면 프리필이 지배합니다. H100의 Llama-3.3-70B FP8에서 32k 프롬프트는 순수 프리필만 약 800ms입니다. 큐 시간은 부하 상태의 스케줄러 동작입니다. 네트워크 요청은 TLS를 포함한 와이어 시간입니다. TTFT는 아무것도 스트리밍되기 전까지 사용자가 겪는 지연입니다.

### TPOT / ITL — 토큰 간 지연

하나의 양에 붙은 여러 이름입니다. `TPOT`(출력 토큰당 시간), `ITL`(토큰 간 지연), `토큰당 디코드 지연` — 전부 같은 것입니다. 첫 토큰 이후 연속으로 스트리밍되는 토큰들 사이의 시간입니다.

`TPOT = (decode_forward_time + scheduler_overhead) / tokens_produced`

같은 Llama-3.3-70B H100 스택에서 청크드 프리필을 쓰면 TPOT 평균은 약 7ms입니다. 청크드 프리필이 없으면, 옆 시퀀스의 긴 프리필이 도는 동안 TPOT이 50ms로 뛸 수 있습니다. 평균 말고 P99를 보세요.

### E2E 지연

`E2E = TTFT + TPOT * output_tokens + network_response`

출력이 길면(500토큰 초과) E2E는 TPOT이 지배합니다. 프롬프트는 길고 출력은 짧으면 E2E는 TTFT가 지배합니다. 출력 길이별로 나눠서(conditioned) E2E를 보고하세요.

### 처리량

`throughput = total_output_tokens / elapsed_time`

집계 지표입니다. 플릿 효율을 알려 줍니다. 개별 요청의 건강 상태는 알려 주지 않습니다.

### 굿푸트 — 실제로 신경 쓸 지표

`goodput = (TTFT <= a) AND (TPOT <= b) AND (E2E <= c)를 모두 충족한 요청의 비율`

SLO는 다중 제약입니다. 모든 제약이 지켜졌을 때만 요청이 "좋은(good)" 것입니다. 굿푸트는 그 비율입니다. 굿푸트 60%의 높은 처리량은 실패입니다. 굿푸트 99%의 낮은 처리량이 목표입니다.

2026년에는 MLPerf Inference v6.0 제출과 AI 플랫폼 제공자들의 내부 SLA 추적에서 쓰이는 지표입니다.

### 평균이 잘못된 통계량인 이유

LLM 지연 분포는 오른쪽으로 기울어져 있습니다(right-skewed). 긴 프리필을 가진 이웃 하나가 있는 디코드 배치는, TPOT 약 7ms의 토큰 500개와 TPOT 약 60ms의 토큰 20개를 함께 내보낼 수 있습니다. 평균 TPOT은 9ms. P99 TPOT은 65ms. 사용자는 P99을 평소처럼 자주 맞닥뜨립니다 — 그래서 떠나는 겁니다.

항상 세 쌍(P50, P90, P99)을 보고하세요. 사용자 경험 기준으로 최적화할 것은 P99입니다.

### 참고 숫자 — TRT-LLM의 Llama-3.1-8B-Instruct, 2026

- 평균 TTFT: 162ms
- 평균 TPOT: 7.33ms
- 평균 E2E: 1,093ms
- P99 TPOT: 청크드 프리필 설정에 따라 10~25ms.

공개된 NVIDIA 참고 지점들입니다. 모델 크기(70B라면 3~5배), 하드웨어(H100 vs B200 약 3배), 부하에 따라 달라집니다.

### 측정 함정

2026년 가장 많이 쓰이는 벤치마크 도구 두 개가 같은 실행에서 TPOT이 서로 다릅니다:

- **NVIDIA GenAI-Perf**: ITL 계산에서 TTFT를 제외합니다. ITL은 2번 토큰부터 시작합니다.
- **LLMPerf**: TTFT를 포함합니다. ITL은 1번 토큰부터 시작합니다.

TTFT 500ms, 출력 100토큰, 총 디코드 700ms인 요청이라면 GenAI-Perf는 `ITL = 700/99 = 7.07ms`를 보고하고, LLMPerf는 `ITL = 1200/100 = 12.00ms`를 보고합니다. 도구 선택이 숫자를 바꿉니다.

항상 어떤 도구인지 밝히세요. 항상 정의를 공개하세요.

### SLO 만들기

2026년 70B 채팅 모델의 소비자 대면 SLO라면 적절한 예:

- TTFT P99 <= 800ms.
- TPOT P99 <= 25ms.
- E2E P99 <= 3초 (300토큰 미만 출력 기준).
- 굿푸트 목표 >= 99%.

엔터프라이즈 SLO는 TTFT를 더 조이고(200~400ms) E2E는 느슨하게 둡니다. 요점은 문서로 적고, 셋 모두를 측정하고, 굿푸트를 하나의 합성 지표로 추적하는 것입니다.

### 측정하는 법

- 실제 트래픽 또는 현실적인 합성 트래픽을 돌립니다(LLMPerf의 `--mean-input-tokens 800 --stddev-input-tokens 300 --mean-output-tokens 150`).
- 벤치마크 실행은 피크 동시성의 2배를 목표로 합니다.
- 30~50회 반복을 돌리고, 합친 샘플의 백분위를 냅니다.
- 도구 이름, 도구 버전, 모델, 하드웨어, 동시성, 프롬프트 분포와 함께 공개합니다.

```figure
throughput-latency
```

## 직접 써보기

`code/main.py`는 장난감 굿푸트 계산기입니다. 합성 지연 분포를 만들고, SLO를 적용하고, 굿푸트를 계산합니다. 같은 트레이스에서 GenAI-Perf vs LLMPerf의 TPOT 차이도 보여줍니다.

## 산출물

이 레슨은 `outputs/skill-slo-goodput-gate.md`를 만듭니다. 워크로드와 SLO가 주어지면, 배포를 처리량이 아니라 굿푸트로 판정(gate)하는 CI/CD에 바로 쓸 수 있는 벤치마크 레시피를 만들어 줍니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 1% 꼬리 스파이크가 있는 분포를 만드세요. P99 TPOT 기준을 30ms에서 15ms로 조이면 굿푸트는 어떻게 바뀌나요?
2. 벤더가 "Llama 3.3 70B H100에서 15,000 tok/s"라고 제시했습니다. 믿기 전에 물어볼 질문 셋을 만들어 보세요.
3. 청크드 프리필은 왜 평균 TPOT이 아니라 P99 TPOT을 지키나요?
4. 음성 비서(첫 토큰을 읽는 게 아니라 듣는)를 위한 소비자 SLO를 만들어 보세요. 사용자에게 가장 잘 보이는 지표는 무엇인가요?
5. LLMPerf README와 GenAI-Perf 문서를 읽으세요. 두 도구가 서로 다른 지표를 세 개 더 찾아 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| TTFT | "첫 토큰까지 시간" | 큐 + 네트워크 + 프리필. 긴 프롬프트에서는 프리필이 지배 |
| TPOT | "출력 토큰당 시간" | 첫 토큰 이후 토큰당 메모리 바운드 디코드 비용 |
| ITL | "토큰 간 지연" | 대부분의 도구에서 TPOT과 같음(전부는 아님 — GenAI-Perf 참조) |
| E2E | "엔드투엔드" | TTFT + TPOT × 출력 길이. 위에 응답 측 네트워크가 더해짐 |
| 처리량 | "tok/s" | 플릿 효율. 지연 백분위 없이는 무용지물 |
| 굿푸트 | "SLO 충족률" | 모든 SLO 제약을 동시에 충족한 요청의 비율 |
| P99 | "꼬리" | 100번 중 1번 최악의 지연. 사용자 경험 지표 |
| SLO 다중 제약 | "조건 결합" | 세 지연 상한의 AND. 하나라도 깨지면 그 요청은 실패 |
| GenAI-Perf vs LLMPerf | "도구 함정" | ITL이 TTFT를 포함하는지 두 도구가 서로 다름 |

## 더 읽을거리

- [NVIDIA NIM — LLM Benchmarking Metrics](https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html) — TTFT, ITL, TPOT의 표준 정의.
- [Anyscale — LLM Serving Benchmarking Metrics](https://docs.anyscale.com/llm/serving/benchmarking/metrics) — 대안 정의와 측정 레시피.
- [BentoML — LLM Inference Metrics](https://bentoml.com/llm/inference-optimization/llm-inference-metrics) — 실제 배포에서의 응용 측정.
- [LLMPerf](https://github.com/ray-project/llmperf) — Ray 기반 오픈소스 벤치마크.
- [GenAI-Perf](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md) — NVIDIA의 벤치마크 도구.
- [MLPerf Inference](https://mlcommons.org/benchmarks/inference-datacenter/) — 업계 표준의 굿푸트 기반 벤치마크.
