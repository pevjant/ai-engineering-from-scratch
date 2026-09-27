> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 11 — LLM 관측 가능성(옵저버빌리티) 및 평가 대시보드

> Langfuse가 오픈 코어로 전환했습니다. Arize Phoenix는 2026년 GenAI 시맨틱 컨벤션 매핑을 공개했습니다. Helicone과 Braintrust는 모두 사용자별 비용 귀속에 힘을 실었습니다. Traceloop의 OpenLLMetry는 사실상 표준 SDK 인스트루먼테이션이 되었습니다. 프로덕션(운영 환경) 형태는 이렇습니다: 트레이스는 ClickHouse, 메타데이터는 Postgres, UI는 Next.js, 그리고 샘플링된 트레이스 위에서 돌아가는 소규모 평가 작업 부대(DeepEval, RAGAS, LLM 심사관). 하나를 셀프 호스팅으로 만들고, 최소 4개 SDK 계열에서 데이터를 흡수하고, 주입된 퇴보(regression)를 5분 안에 잡아내는 모습을 시연하세요.

**유형:** 캡스톤
**언어:** TypeScript (UI), Python / TypeScript (수집 + 평가), SQL (ClickHouse)
**선수 지식:** 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구), 페이즈 17 (인프라), 페이즈 18 (안전성)
**활용 페이즈:** P11 · P13 · P17 · P18
**소요 시간:** 25시간

## 문제

2026년에 프로덕션 트래픽을 처리하는 모든 AI 팀은 모델 곁에 관측 평면(observability plane)을 함께 둡니다. 비용 귀속. 환각 탐지. 드리프트 모니터링. 탈옥 신호. SLO 대시보드. PII 유출 알림. 오픈소스 참고 사례들 — Langfuse, Phoenix, OpenLLMetry — 는 흡수 스키마로 OpenTelemetry GenAI 시맨틱 컨벤션에 수렴했습니다. 이제 하나의 SDK로 OpenAI, Anthropic, Google, LangChain, LlamaIndex, vLLM을 계측하고 호환되는 스팬을 내보낼 수 있습니다.

여러분은 최소 4개 SDK 계열에서 데이터를 흡수하고, 샘플링된 트레이스 위에서 소규모 평가 작업을 돌리고, 드리프트를 탐지하고, 알림을 보내는 셀프 호스팅 대시보드를 만들 것입니다. 측정 기준은 이것입니다: 일부러 주입한 퇴보(PII를 만들어 내기 시작하는 프롬프트)가 주어지면, 대시보드가 이를 잡아내고 5분 안에 알림을 발사해야 합니다.

## 개념

흡수(ingest)는 OTLP HTTP입니다. SDK는 GenAI 시맨틱 컨벤션 스팬을 만들어 냅니다: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.response.id`, `llm.prompts`, `llm.completions`. 스팬은 컬럼 기반 분석을 위해 ClickHouse에 도착하고, 메타데이터(사용자, 세션, 앱)는 Postgres에 도착합니다.

평가는 샘플링된 트레이스 위에서 배치 작업으로 돕니다. DeepEval은 충실도, 독성, 답변 관련성을 채점합니다. RAGAS는 트레이스가 검색 컨텍스트를 갖고 있을 때 검색 지표를 채점합니다. 커스텀 LLM 심사관(LLM-judge)은 도메인 특화 검사(PII 유출, 정책 위반 응답)를 돌립니다. 평가 실행 결과는 부모 트레이스에 연결된 평가 스팬으로 같은 ClickHouse에 기록됩니다.

드리프트 탐지는 시간에 따른 임베딩 공간 분포(프롬프트 임베딩에 대한 PSI 또는 KL 발산)와 평가 점수 추이를 지켜봅니다. 알림은 Prometheus Alertmanager로 흘러가고 그다음 Slack / PagerDuty로 갑니다. UI는 Recharts를 얹은 Next.js 15입니다.

## 아키텍처

```
production apps:
  OpenAI SDK  +  Anthropic SDK  +  Google GenAI SDK
  LangChain + LlamaIndex + vLLM
       |
       v
  OpenTelemetry SDK with GenAI semconv
       |
       v  OTLP HTTP
  collector (ingest, sample, fan-out)
       |
       +-------------+-----------+
       v             v           v
   ClickHouse    Postgres    S3 archive
   (spans)       (metadata)  (raw events)
       |
       +---> eval jobs (DeepEval, RAGAS, LLM-judge)
       |     sampled or all-trace
       |     write eval spans back
       |
       +---> drift detector (PSI / KL on prompt embeddings)
       |
       +---> Prometheus metrics -> Alertmanager -> Slack / PagerDuty
       |
       v
   Next.js 15 dashboard (Recharts)
```

## 스택

- 흡수: OpenTelemetry SDK + GenAI 시맨틱 컨벤션; OTLP HTTP 전송
- 컬렉터: 비용 관리용 tail-sampling 프로세서를 갖춘 OpenTelemetry Collector
- 저장소: 스팬은 ClickHouse, 메타데이터는 Postgres, 원본 이벤트 아카이브는 S3
- 평가: DeepEval, RAGAS 0.2, Arize Phoenix 평가기 팩, 커스텀 LLM 심사관
- 드리프트: 합산된 프롬프트 임베딩(sentence-transformers)에 대한 PSI / KL, 주간 실행
- 알림: Prometheus Alertmanager → Slack / PagerDuty
- UI: Next.js 15 App Router + Recharts + server actions
- 기본 지원 SDK: OpenAI, Anthropic, Google GenAI, LangChain, LlamaIndex, vLLM

```figure
ce-otel-drift
```

## 직접 만들기

1. **컬렉터 설정.** OTLP HTTP 수신기, 오류 트레이스는 100% 성공 트레이스는 10%를 남기는 tail-sampler, 그리고 ClickHouse와 S3로 내보내는 익스포터를 갖춘 OpenTelemetry Collector.

2. **ClickHouse 스키마.** GenAI 시맨틱 컨벤션을 그대로 반영하는 컬럼을 가진 `spans` 테이블: `gen_ai_system`, `gen_ai_request_model`, `input_tokens`, `output_tokens`, `latency_ms`, `prompt_hash`, `trace_id`, `parent_span_id`, 그리고 긴 페이로드를 위한 JSON 보관 컬럼. user_id와 app_id 보조 인덱스를 추가합니다.

3. **SDK 커버리지 테스트.** 각 SDK(OpenAI, Anthropic, Google, LangChain, LlamaIndex, vLLM)를 OpenLLMetry 자동 계측과 함께 쓰는 작은 클라이언트 앱을 작성합니다. 각각이 표준 GenAI 스팬을 만들어 ClickHouse에 도착시키는지 검증합니다.

4. **평가 작업.** 예약된 작업이 최근 15분간 샘플링된 트레이스를 읽고 DeepEval 충실도, 독성, 답변 관련성을 실행합니다. 결과는 부모 트레이스에 연결된 평가 스팬으로 기록됩니다.

5. **커스텀 LLM 심사관.** PII 유출 심사관: 응답이 주어지면 가드 LLM을 호출해 PII 유출 가능성을 채점합니다. 점수가 높은 응답은 분류(triage) 큐로 들어갑니다.

6. **드리프트 탐지.** 주간 작업이 이번 주 합산 프롬프트 임베딩과 최근 4주 베이스라인 사이의 PSI를 계산합니다. PSI가 임계값 위면 알림을 보냅니다.

7. **대시보드.** Next.js 15 페이지들: 개요(초당 스팬, 사용자당 비용, p95 지연 시간), 트레이스(검색 + 워터폴), 평가(충실도 추이, 독성), 드리프트(시간에 따른 PSI), 알림.

8. **알림 체인.** Prometheus 익스포터가 평가 점수 집계와 지연 시간 백분위를 읽습니다; Alertmanager는 경고는 Slack으로, 심각한 위반은 PagerDuty로 라우팅합니다.

9. **퇴보 프로브.** 버그를 주입합니다: 평가 대상 챗봇이 1% 확률로 가짜 주민등록번호(SSN)를 유출하기 시작합니다. MTTR을 측정합니다: 버그 배포부터 Slack 알림까지.

## 사용해 보기

```
$ curl -X POST https://my-otel-collector/v1/traces -d @trace.json
[collector]  accepted 1 trace, 3 spans
[clickhouse] inserted 3 spans (app=chat, user=u_42)
[eval]       DeepEval faithfulness 0.82, toxicity 0.03
[drift]      weekly PSI 0.08 (below 0.2 threshold)
[ui]         live at https://obs.example.com
```

## 출시하기

`outputs/skill-llm-observability.md`가 산출물입니다. LLM 애플리케이션이 주어지면 대시보드가 그 트레이스를 흡수하고, 평가를 돌리고, 드리프트에 알림을 보내고, Next.js에서 사용자당 비용 분해를 보여줍니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 트레이스 스키마 커버리지 | 표준 GenAI 스팬을 만들어 내는 SDK 계열 수 (목표: 6개 이상) |
| 20 | 평가 정확성 | 수작업 레이블 셋 대비 DeepEval / RAGAS 점수 |
| 20 | 대시보드 UX | 주입된 퇴보의 MTTR (목표 5분 미만) |
| 20 | 비용 / 확장성 | 백로그 없이 초당 1k 스팬 지속 흡수 |
| 15 | 알림 + 드리프트 탐지 | 끝까지 검증된 Prometheus/Alertmanager 체인 |
| **100** | | |

## 연습 문제

1. Haystack 프레임워크용 커스텀 계측을 추가합니다. 충실한 `gen_ai.*` 속성을 지닌 표준 스팬이 ClickHouse에 도착하는지 검증합니다.

2. 같은 트레이스에서 DeepEval을 Phoenix 평가기로 바꿔 봅니다. 두 평가 엔진 사이의 점수 드리프트를 측정합니다.

3. 드리프트 탐지기를 정밀하게 만듭니다: 전역이 아니라 앱 아이디(app-id)별로 PSI를 계산합니다. 앱별 드리프트 궤적을 보여줍니다.

4. "사용자 영향" 페이지를 추가합니다: 스파크라인과 함께 사용자당 비용과 사용자당 실패율을 보여줍니다.

5. 독성 > 0.5인 트레이스는 100% 남기고 나머지는 10% 층화(stratified) 샘플링하는 tail-sampling 정책을 만듭니다. 이때 생기는 샘플링 편향을 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| GenAI 시맨틱 컨벤션(semconv) | "OTel LLM 속성" | LLM 스팬 속성(시스템, 모델, 토큰)을 정의한 2025 OpenTelemetry 스펙 |
| Tail sampling | "트레이스 후 샘플링" | 컬렉터가 트레이스가 완료된 뒤에 남길지 버릴지 결정 (오류를 엿볼 수 있음) |
| PSI | "모집단 안정성 지수" | 두 분포를 비교하는 드리프트 지표; 0.2 초과면 보통 의미 있는 드리프트 신호 |
| LLM 심사관(LLM-judge) | "모델로 하는 평가" | 루브릭(충실도, 독성, PII)에 따라 다른 LLM의 출력을 채점하는 LLM |
| Tail-sampling 정책 | "보존 규칙" | 어떤 트레이스를 저장하고 어떤 트레이스를 버릴지 정하는 규칙; 오류 + 샘플링 비율 |
| 평가 스팬 | "연결된 평가 트레이스" | 원본 LLM 호출 스팬에 연결된 평가 점수를 지닌 자식 스팬 |
| 사용자당 비용 | "단위 경제성" | 특정 user_id에 일정 기간 동안 귀속된 달러 비용; 핵심 제품 지표 |

## 더 읽을거리

- [Langfuse](https://github.com/langfuse/langfuse) — 오픈 코어 관측 가능성 플랫폼의 참고 사례
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — 드리프트 지원이 강한 대안 참고 사례
- [OpenLLMetry (Traceloop)](https://github.com/traceloop/openllmetry) — 자동 계측 SDK 계열
- [OpenTelemetry GenAI 시맨틱 컨벤션](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 흡수 스키마
- [Helicone](https://www.helicone.ai) — 대안 호스팅 관측 가능성
- [Braintrust](https://www.braintrust.dev) — 평가 우선 대안 플랫폼
- [ClickHouse 문서](https://clickhouse.com/docs) — 컬럼 기반 스팬 저장소
- [DeepEval](https://github.com/confident-ai/deepeval) — 평가기 라이브러리
