> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# LLM API 부하 테스트 — k6와 Locust가 왜 거짓말하는가

> 전통적 부하 테스터는 스트리밍 응답, 가변 출력 길이, 토큰 수준 메트릭, GPU 포화를 위해 설계되지 않았습니다. 대부분의 팀을 무는 트랩 두 개가 있습니다. GIL 트랩: Locust의 토큰 수준 측정은 토크나이징을 Python GIL 아래에서 돌리는데, 높은 동시성에서 요청 생성과 경쟁합니다; 토크나이징 적체가 보고되는 토큰 간 지연을 부풀립니다 — 병목은 서버가 아니라 클라이언트(테스트 하네스)입니다. 프롬프트 균일성 트랩: 루프 안의 동일한 프롬프트는 토큰 분포의 한 점만 검사합니다; 실제 트래픽은 길이가 가변적이고 프리픽스 매칭도 다양합니다. LLMPerf는 `--mean-input-tokens` + `--stddev-input-tokens`로 이것을 고칩니다. 2026년 도구 매핑: 토큰 수준 정확도에는 LLM 특화 도구(GenAI-Perf, LLMPerf, LLM-Locust, guidellm); **k6 v2026.1.0** + **k6 Operator 1.0 GA (2025년 9월)** — 스트리밍 인지, TestRun/PrivateLoadZone CRD를 통한 Kubernetes 네이티브 분산, CI/CD 관문에 최적; Go의 정률 포화 테스트에는 Vegeta; 스트리밍용 Locust는 2.43.3이라도 반드시 LLM-Locust 확장과 함께. 부하 패턴: 정상 상태(steady-state), 램프(ramp), 스파이크(오토스케일링 테스트), 소크(메모리 누수).

**유형:** 빌드
**언어:** Python (표준 라이브러리, 현실적 프롬프트 생성기 + 지연 수집기 장난감 버전)
**선수 지식:** 페이즈 17 · 08 (추론 메트릭), 페이즈 17 · 03 (GPU 오토스케일링)
**시간:** 약 75분

## 학습 목표

- 범용 부하 테스터가 LLM API에서 거짓말하게 만드는 두 가지 안티패턴(GIL 트랩, 프롬프트 균일성 트랩)을 설명할 수 있습니다.
- 목적에 맞는 도구를 고를 수 있습니다: LLMPerf(벤치마크 실행), k6 + 스트리밍 확장(CI 관문), guidellm(대규모 합성), GenAI-Perf(NVIDIA 참조).
- 네 가지 부하 패턴(정상, 램프, 스파이크, 소크)을 설계하고 각각이 잡아내는 실패 양상의 이름을 말할 수 있습니다.
- 고정 길이가 아니라 입력 토큰의 평균 + 표준편차로 현실적인 프롬프트 분포를 만들 수 있습니다.

## 문제 상황

동시 사용자 500명으로 LLM 엔드포인트를 k6로 테스트했습니다. 버텼습니다. 출시합니다. 실제 사용자 200명뿐인 프로덕션(운영 환경)에서 서비스가 넘어졌습니다 — P99 TTFT가 폭주하고 GPU가 고정(포화)됩니다.

두 가지 일이 벌어졌습니다. 첫째, k6는 500개의 동일한 프롬프트를 보냈습니다 — 요청 병합과 프리픽스 캐싱 덕에 실제로는 하나를 처리하면서도 500개 동시 디코드를 처리하는 것처럼 보였습니다. 둘째, k6는 스트리밍 응답의 토큰 간 지연을 사람 눈이 경험하는 방식으로 추적하지 않습니다; 다양한 간격으로 도착하는 500개 토큰이 아니라 하나의 HTTP 연결을 봅니다.

LLM 부하 테스트는 그 자체로 하나의 분야입니다.

## 개념

### GIL 트랩 (Locust)

Locust는 Python을 쓰고 토크나이징을 GIL 아래 클라이언트 쪽에서 돌립니다. 높은 동시성에서 토크나이저는 요청 생성 뒤에 줄을 섭니다. 보고되는 토큰 간 지연에는 클라이언트 쪽 토크나이징 적체가 포함됩니다. 서버가 느리다고 생각하지만, 느린 것은 테스트 하네스입니다.

해법: LLM-Locust 확장은 토크나이징을 별도 프로세스로 옮기고, 컴파일 언어 하네스를 쓸 수도 있습니다(k6, tokenizers.rs를 쓰는 LLMPerf).

### 프롬프트 균일성 트랩

알려진 모든 부하 테스터는 프롬프트 하나를 설정하게 해줍니다. 1만 회 반복 테스트에서 완전히 같은 프롬프트가 매번 전송됩니다. 서버는 매번 같은 프리픽스를 봅니다 — 프리픽스 캐시 적중률이 100%에 수렴하고, 처리량이 멋져 보입니다.

해법: 프롬프트 분포에서 샘플링하세요. LLMPerf는 `--mean-input-tokens 500 --stddev-input-tokens 150`을 씁니다 — 다양한 길이, 다양한 내용.

### 네 가지 부하 패턴

1. **정상 상태(steady-state)** — 30-60분간 일정 RPS. 잡아내는 것: 베이스라인 성능 회귀.
2. **램프(ramp)** — 15분에 걸쳐 RPS를 0에서 목표까지 선형 증가. 잡아내는 것: 용량 분기점, 워밍업 이상.
3. **스파이크(spike)** — 갑자기 3-10배 RPS를 2분 유지 후 복귀. 잡아내는 것: 오토스케일링 지연, 큐 포화, 콜드스타트 영향.
4. **소크(soak)** — 4-8시간 정상 상태. 잡아내는 것: 메모리 누수, 커넥션 풀 드리프트, 관측 도구 오버플로.

### 2026년 도구 매핑

**LLMPerf** (Anyscale) — Python이지만 Rust 기반 토크나이징. 평균/표준편차 프롬프트. 스트리밍 인지. 성능 실행의 기본 선택.

**NVIDIA GenAI-Perf** — NVIDIA의 참조 도구. Triton 클라이언트 사용; 포괄적인 메트릭 커버리지. 참고로 이 도구의 ITL은 TTFT를 제외하고; LLMPerf의 것은 포함합니다. 같은 서버에서 두 도구는 다른 TPOT를 냅니다.

**LLM-Locust** (TrueFoundry) — GIL 트랩을 고치는 Locust 확장. 익숙한 Locust DSL + 스트리밍 메트릭.

**guidellm** — 대규모 합성 벤치마킹.

**k6 v2026.1.0** + **k6 Operator 1.0 GA (2025년 9월)**:
- k6 자체(Go, 컴파일 언어, GIL 없음)에 스트리밍 인지 메트릭이 추가됐습니다.
- k6 Operator는 TestRun / PrivateLoadZone CRD로 Kubernetes 네이티브 분산 테스팅을 합니다.
- CI/CD 관문과 SLA 테스트에 가장 적합합니다.

**Vegeta** — Go, k6보다 단순. 정률 HTTP 포화. LLM 인지는 없지만 게이트웨이 / 속도 제한 테스트에 좋습니다.

**Locust 2.43.3 순정** — LLM에는 GIL 트랩이 있습니다. 반드시 LLM-Locust 확장과 함께.

### CI 속의 SLA 관문

PR에서 k6를 이렇게 돌립니다:

- 베이스라인 RPS로 각각 30-50회 반복.
- 관문: P50/P95 TTFT, 5xx < 5%, 임계값 이하 TPOT.
- 위반 시 빌드를 깹니다.

### 현실적인 프롬프트 분포

실제 트래픽 샘플(있다면)이나 공개된 분포(예: 채팅은 ShareGPT 프롬프트, 코드는 HumanEval)로 만듭니다. 평균 + 표준편차를 LLMPerf에 먹입니다. 프롬프트 하나짜리 루프는 무슨 수를 써서라도 피하세요.

### 기억해야 할 숫자들

- k6 Operator 1.0 GA: 2025년 9월.
- k6 v2026.1.0: 스트리밍 인지 메트릭.
- 전형적인 LLMPerf 실행: 동시성 X에서 100-1000 요청.
- 전형적인 CI 관문: PR당 30-50회 반복.
- 네 가지 패턴: 정상, 램프, 스파이크, 소크.

```figure
load-pattern-waves
```

## 활용하기

`code/main.py`는 현실적인 프롬프트 분포로 부하 테스트를 시뮬레이션하고, 실효 TPOT를 측정하며, 균일 프롬프트 트랩을 보여줍니다.

## 출시하기

이 레슨은 `outputs/skill-load-test-plan.md`를 산출합니다. 워크로드와 SLA가 주어지면 도구를 고르고 네 가지 부하 패턴을 설계합니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 균일 분포와 현실적 분포를 비교하세요 — 격차는 어디에 있나요?
2. CI 관문용 k6 스크립트를 작성하세요: 동시성 100에서 TTFT P95 < 800ms, 실행 시간 5분.
3. 소크 테스트에서 시간당 50 MB의 메모리 증가가 보입니다. 원인 세 가지와 그중을 가려낼 계측 방법을 말하세요.
4. 10 RPS에서 100 RPS로 스파이크 테스트. Karpenter + vLLM production-stack이 갖춰져 있다면(페이즈 17 · 03 + 18) 예상 복구 시간은 얼마인가요?
5. GenAI-Perf는 TPOT=6ms를 보고하고; 같은 서버에서 LLMPerf는 TPOT=11ms를 보고합니다. 설명하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| LLMPerf | "그 LLM 하네스" | Anyscale 벤치마크 도구, 스트리밍 인지 |
| GenAI-Perf | "NVIDIA 도구" | NVIDIA 참조 하네스 |
| LLM-Locust | "LLM용 Locust" | GIL 트랩을 고치는 Locust 확장 |
| guidellm | "합성 벤치마크" | 대규모 합성 도구 |
| k6 Operator | "K8s k6" | CRD 기반 분산 k6 |
| GIL 트랩 | "Python 클라이언트 오버헤드" | 토크나이징 적체가 보고 지연을 부풀림 |
| 프롬프트 균일성 트랩 | "단일 프롬프트 거짓말" | 같은 프롬프트 루프는 캐시를 맞춰 처리량을 부풀림 |
| 정상 상태 | "일정 부하" | N분간 평평한 RPS |
| 램프 | "선형 상승" | 기간에 걸쳐 0에서 목표까지 |
| 스파이크 | "버스트 테스트" | 갑작스러운 배수 후 복귀 |
| 소크 | "장시간 테스트" | 누수 감지를 위한 몇 시간 |

## 더 읽을거리

- [TianPan — Load Testing LLM Applications](https://tianpan.co/blog/2026-03-19-load-testing-llm-applications)
- [PremAI — Load Testing LLMs 2026](https://blog.premai.io/load-testing-llms-tools-metrics-realistic-traffic-simulation-2026/)
- [NVIDIA NIM — Introduction to LLM Inference Benchmarking](https://docs.nvidia.com/nim/large-language-models/1.0.0/benchmarking.html)
- [TrueFoundry — LLM-Locust](https://www.truefoundry.com/blog/llm-locust-a-tool-for-benchmarking-llm-performance)
- [LLMPerf](https://github.com/ray-project/llmperf)
- [k6 Operator](https://github.com/grafana/k6-operator)
