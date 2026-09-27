> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# OpenTelemetry GenAI — 도구 호출을 엔드투엔드로 추적하기

> 어떤 에이전트가 도구 다섯 개, MCP 서버 세 개, 하위 에이전트 둘을 호출한다고 합시다. 이 전부를 관통하는 트레이스 하나가 필요합니다. OpenTelemetry GenAI 시맨틱 컨벤션(v1.37 이상에서 안정 속성)은 2026년의 표준이며, Datadog, Langfuse, Arize Phoenix, OpenLLMetry, AgentOps가 기본 지원합니다. 이 레슨은 필수 속성들의 이름을 짚고, 스팬 계층(에이전트 → LLM → 도구)을 따라가 보고, 어떤 OTel 익스포터에도 꽂을 수 있는 stdlib 스팬 방출기(emitter)를 출시합니다.

**유형:** Build
**언어:** Python (stdlib, OTel 스팬 방출기)
**선수 지식:** 페이즈 13 · 07(MCP 서버), 페이즈 13 · 08(MCP 클라이언트)
**소요 시간:** 약 75분

## 학습 목표

- LLM 스팬과 도구 실행 스팬에 필요한 OTel GenAI 속성들을 말할 수 있다.
- 에이전트 루프, LLM 호출, 도구 호출, MCP 클라이언트 디스패치를 아우르는 트레이스 계층을 만들 수 있다.
- 어떤 콘텐츠를 캡처할지(옵트인)와 어떤 콘텐츠를 마스킹할지(기본값) 결정할 수 있다.
- 도구 코드를 재작성하지 않고 로컬 수집기(Jaeger, Langfuse)로 스팬을 내보낼 수 있다.

## 문제 상황

2026년 2월의 디버깅 사례: 사용자가 "내 에이전트는 응답에 30초 걸릴 때가 있고, 어떤 때는 3초 걸립니다"라고 보고합니다. 트레이스는 없습니다. 로그에는 LLM 호출이 보이지만, 도구 디스패치도, MCP 서버 왕복도, 하위 에이전트도 보이지 않습니다. 추측만 합니다. 결국 이것을 발견합니다: MCP 서버 하나가 콜드 스타트 때 가끔 멈춘다는 것을요.

엔드투엔드 추적이 없으면 이것을 찾을 수 없습니다. OTel GenAI가 이것을 고쳐 줍니다.

이 컨벤션은 2025-2026년 동안 OpenTelemetry semantic-conventions 그룹 아래에서 정착됐습니다. 안정적인 속성 이름을 정의해서, Datadog, Langfuse, Phoenix, OpenLLMetry, AgentOps가 모두 같은 스팬을 파싱하게 합니다. 한 번 계측하면(instrument), 어떤 백엔드로든 내보냅니다.

## 개념

### 스팬 계층

```
agent.invoke_agent  (top, INTERNAL span)
 ├── llm.chat       (CLIENT span)
 ├── tool.execute   (INTERNAL)
 │    └── mcp.call  (CLIENT span)
 ├── llm.chat       (CLIENT span)
 └── subagent.invoke (INTERNAL)
```

전부가 하나의 트레이스 id 아래 중첩됩니다. 스팬 id가 부모-자식 관계를 연결합니다.

### 필수 속성

2025-2026 semconv 기준:

- `gen_ai.operation.name` — `"chat"`, `"text_completion"`, `"embeddings"`, `"execute_tool"`, `"invoke_agent"`.
- `gen_ai.provider.name` — `"openai"`, `"anthropic"`, `"google"`, `"azure_openai"`.
- `gen_ai.request.model` — 요청한 모델 문자열(예: `"gpt-4o-2024-08-06"`).
- `gen_ai.response.model` — 실제 서빙한 모델.
- `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`.
- `gen_ai.response.id` — 상관관계를 위한 공급자 응답 id.

도구 스팬용:

- `gen_ai.tool.name` — 도구 식별자.
- `gen_ai.tool.call.id` — 구체적인 호출 id.
- `gen_ai.tool.description` — 도구 설명(선택).

에이전트 스팬용:

- `gen_ai.agent.name` / `gen_ai.agent.id` / `gen_ai.agent.description`.

### 스팬 종류

- `SpanKind.CLIENT` — 프로세스 경계를 넘는 호출(LLM 공급자, MCP 서버)용.
- `SpanKind.INTERNAL` — 에이전트 자체 루프 단계와 도구 실행용.

### 옵트인 콘텐츠 캡처

기본적으로 스팬은 메트릭과 타이밍을 실지 — 프롬프트나 완성문(completions)은 실지 않습니다. 큰 페이로드와 PII(개인 식별 정보)는 기본적으로 꺼져 있습니다. 콘텐츠를 포함하려면 `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`과 특정 콘텐츠 캡처 환경 변수를 설정하세요. 프로덕션(운영 환경)에서 켜기 전에 신중히 검토하세요.

### 스팬 위의 이벤트

토큰 수준 이벤트는 스팬 이벤트로 추가할 수 있습니다:

- `gen_ai.content.prompt` — 입력 메시지.
- `gen_ai.content.completion` — 출력 메시지.
- `gen_ai.content.tool_call` — 기록된 그대로의 도구 호출.

이벤트는 상세 리플레이를 위해 스팬 안에서 시간순으로 정렬됩니다.

### 익스포터

OTel 스팬은 다음으로 내보냅니다:

- **Jaeger / Tempo.** OSS, 온프레미스.
- **Langfuse.** LLM 관측 가능성(옵저버빌리티) 특화; 토큰 사용량을 시각화.
- **Arize Phoenix.** 평가(eval) + 추적 결합.
- **Datadog.** 상용; `gen_ai.*` 속성을 기본 파싱.
- **Honeycomb.** 컬럼 지향; 쿼리 친화적.

모두 와이어 포맷인 OTLP를 말합니다. 코드는 신경 쓸 필요가 없습니다.

### MCP를 가로지르는 전파(propagation)

MCP 클라이언트가 서버를 호출할 때, W3C traceparent 헤더를 요청에 주입하세요. Streamable HTTP는 표준 헤더를 지원합니다. Stdio는 HTTP 헤더를 기본으로 실지 않습니다. 명세의 2026 로드맵은 JSON-RPC 호출에 `_meta.traceparent` 필드를 추가하는 논의를 담고 있습니다.

그것이 출시되기 전까지는: 모든 요청의 `_meta`에 traceparent를 수동으로 넣으세요. 서버가 트레이스 id를 로그에 남깁니다.

### 메트릭

스팬과 함께, GenAI semconv는 메트릭을 정의합니다:

- `gen_ai.client.token.usage` — 히스토그램.
- `gen_ai.client.operation.duration` — 히스토그램.
- `gen_ai.tool.execution.duration` — 히스토그램.

호출별 상세가 필요 없는 대시보드에는 이것들을 쓰세요.

### AgentOps 계층

AgentOps(2024년 설립)는 GenAI 관측 가능성(옵저버빌리티)을 전문으로 합니다. 인기 프레임워크(LangGraph, Pydantic AI, CrewAI)를 감싸서 OTel 스팬을 자동으로 방출합니다. 스택이 지원되는 프레임워크를 쓴다면 유용하고, 아니라면 수동 계측을 쓰세요.

```figure
t3-span-waterfall
```

## 활용하기

`code/main.py`는 LLM을 호출하고 도구 두 개를 디스패치하고 MCP 왕복 한 번을 수행하는 에이전트에 대해, OTel 형태의 스팬을 stdout으로(OTLP-JSON 비슷한 형식으로) 방출합니다. 실제 익스포터는 없습니다 — 레슨은 스팬 형태와 속성 집합에 집중합니다. 출력을 OTLP 호환 뷰어에 붙여 넣거나 그냥 읽으세요.

볼 지점:

- 트레이스 id가 모든 스팬에서 공유됩니다.
- 부모-자식 링크가 `parentSpanId`로 인코딩됩니다.
- 필수 `gen_ai.*` 속성이 채워집니다.
- 콘텐츠 캡처는 기본적으로 꺼져 있고, 한 시나리오가 환경 변수로 켭니다.

## 출시하기

이 레슨은 `outputs/skill-otel-genai-instrumentation.md`를 산출합니다. 에이전트 코드베이스가 주어지면, 이 스킬은 계측 계획을 산출합니다: 어디에 스팬을 추가할지, 어떤 속성을 채울지, 어떤 익스포터를 대상으로 할지.

## 연습 문제

1. `code/main.py`를 실행하세요. 스팬 수를 세고 어느 것이 CLIENT이고 어느 것이 INTERNAL인지 식별하세요.

2. 콘텐츠 캡처를 켜고(환경 변수) `gen_ai.content.prompt`와 `gen_ai.content.completion` 이벤트가 나타나는지 확인하세요. PII에 대한 함의를 적어 보세요.

3. 도구 실행 메트릭 `gen_ai.tool.execution.duration`을 추가하고 호출마다 히스토그램 샘플로 방출하세요.

4. 부모 에이전트 스팬에서 traceparent를 MCP 요청의 `_meta.traceparent` 필드로 전파하세요. MCP 서버가 같은 트레이스 id를 보게 될지 확인하세요.

5. OTel GenAI semconv 명세를 읽고, 이 레슨의 코드가 방출하지 않는(semconv에 목록된) 속성 하나를 찾으세요. 그것을 추가하세요.

## 핵심 용어

| 용어 | 사람들이 부르는 이름 | 실제 의미 |
|------|----------------|------------------------|
| OTel | "OpenTelemetry" | 트레이스, 메트릭, 로그를 위한 오픈 표준 |
| GenAI semconv | "GenAI 시맨틱 컨벤션" | LLM / 도구 / 에이전트 스팬의 안정적인 속성 이름 |
| `gen_ai.*` | "속성 네임스페이스" | 모든 GenAI 속성이 공유하는 접두사 |
| 스팬(Span) | "시간 측정된 작업" | 시작, 끝, 속성을 가진 작업 단위 |
| 트레이스(Trace) | "스팬을 넘는 혈통" | 같은 트레이스 id를 공유하는 스팬 트리 |
| SpanKind | "CLIENT / SERVER / INTERNAL" | 스팬 방향에 대한 힌트 |
| OTLP | "OpenTelemetry Line Protocol" | 익스포터용 와이어 포맷 |
| 옵트인 콘텐츠 | "프롬프트 / 완성문 캡처" | 기본적으로 꺼짐; 환경 변수로 활성화 |
| traceparent | "W3C 헤더" | 서비스를 넘어 트레이스 컨텍스트를 전파 |
| 익스포터 | "백엔드별 발송기" | 스팬을 Jaeger / Datadog 등으로 보내는 구성 요소 |

## 더 읽을거리

- [OpenTelemetry — GenAI semconv](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — GenAI 스팬, 메트릭, 이벤트의 공식 컨벤션
- [OpenTelemetry — GenAI spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) — LLM 및 도구 실행 스팬 속성 목록
- [OpenTelemetry — GenAI agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/) — 에이전트 수준 `invoke_agent` 스팬
- [open-telemetry/semantic-conventions — GenAI spans](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-spans.md) — GitHub에 호스팅된 원천
- [Datadog — LLM OTel semantic convention](https://www.datadoghq.com/blog/llm-otel-semantic-convention/) — 프로덕션(운영 환경) 통합 워크스루
