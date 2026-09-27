> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# OpenTelemetry GenAI 시맨틱 컨벤션

> OpenTelemetry의 GenAI SIG(2024년 4월 출범)는 에이전트 텔레메트리의 표준 스키마를 정의합니다. 스팬 이름, 속성, 콘텐츠 수집 규칙이 벤더 전반에 걸쳐 수렴하기 때문에 에이전트 트레이스가 Datadog, Grafana, Jaeger, Honeycomb 어디서든 같은 의미로 읽힙니다.

**유형:** Learn + Build(학습 + 구축)
**언어:** Python (표준 라이브러리)
**선수 지식:** 페이즈 14 · 13(LangGraph), 페이즈 14 · 24(관측 가능성 플랫폼)
**시간:** 약 60분

## 학습 목표

- GenAI 스팬 카테고리를 말할 수 있습니다. model/client, agent, tool입니다.
- `invoke_agent`의 CLIENT 스팬과 INTERNAL 스팬의 차이, 그리고 각각이 언제 쓰이는지 구분할 수 있습니다.
- 최상위 GenAI 속성들(공급자 이름, 요청 모델, 데이터 소스 ID)을 나열할 수 있습니다.
- 콘텐츠 수집 규칙을 설명할 수 있습니다. 옵트인 방식, `OTEL_SEMCONV_STABILITY_OPT_IN`, 외부 참조 권장 사항입니다.

## 문제 상황

벤저마다 제각각의 스팬 이름을 만들어 쓰면, 운영팀은 프레임워크마다 대시보드를 따로 만들어야 합니다. OpenTelemetry의 GenAI SIG는 생태계 전체가 하나의 표준을 향하도록 이 문제를 해결합니다.

## 핵심 개념

### 스팬 카테고리

1. **모델 / 클라이언트 스팬.** 원시 LLM 호출을 다룹니다. 공급자 SDK(Anthropic, OpenAI, Bedrock)와 프레임워크의 모델 어댑터가 발행합니다.
2. **에이전트 스팬.** `create_agent`(에이전트가 생성될 때)와 `invoke_agent`(에이전트가 실행될 때)입니다.
3. **도구 스팬.** 도구 호출 하나당 하나씩 발행되며, 부모-자식 관계로 에이전트 스팬에 연결됩니다.

### 에이전트 스팬 이름 짓기

- 스팬 이름: 이름이 있으면 `invoke_agent {gen_ai.agent.name}`, 없으면 `invoke_agent`로 폴백합니다.
- 스팬 종류:
  - **CLIENT** — 원격 에이전트 서비스(OpenAI Assistants API, Bedrock Agents)를 호출할 때.
  - **INTERNAL** — 프로세스 내부에서 동작하는 에이전트 프레임워크(LangChain, CrewAI, 로컬 ReAct)일 때.

### 핵심 속성

- `gen_ai.provider.name` — `anthropic`, `openai`, `aws.bedrock`, `google.vertex`.
- `gen_ai.request.model` — 모델 ID.
- `gen_ai.response.model` — 실제 확정된 모델(라우팅 때문에 요청과 다를 수 있음).
- `gen_ai.agent.name` — 에이전트 식별자.
- `gen_ai.operation.name` — `chat`, `completion`, `invoke_agent`, `tool_call`.
- `gen_ai.data_source.id` — RAG의 경우 어떤 코퍼스나 저장소를 조회했는지.

Anthropic, Azure AI Inference, AWS Bedrock, OpenAI용 기술별 컨벤션도 별도로 존재합니다.

### 콘텐츠 수집

기본 규칙: 계측 코드는 기본적으로 입력/출력을 수집해서는 안 됩니다(SHOULD NOT). 수집은 옵트인 방식이며 다음 속성으로 이루어집니다.

- `gen_ai.system_instructions`
- `gen_ai.input.messages`
- `gen_ai.output.messages`

권장 프로덕션 패턴: 콘텐츠는 외부(S3, 자체 로그 저장소)에 저장하고, 스팬에는 참조만 기록합니다(문장이 아니라 포인터 ID). 이것이 레슨 27의 콘텐츠 오염 방어를 관측 가능성에 연결한 형태입니다.

### 안정성

2026년 3월 기준 대부분의 컨벤션은 실험 단계입니다. 다음처럼 안정 프리뷰에 옵트인할 수 있습니다.

```
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
```

Datadog v1.37+는 GenAI 속성을 자체 LLM Observability 스키마로 네이티브하게 매핑합니다. 그 외 백엔드(Grafana, Honeycomb, Jaeger)는 원시 속성을 그대로 지원합니다.

### 이 패턴이 잘못되기 쉬운 지점

- **스팬에 프롬프트 전문을 기록.** 운영팀이 읽을 수 있는 트레이스에 PII, 시크릿, 고객 데이터가 들어갑니다. 외부에 저장하세요.
- **`gen_ai.provider.name` 누락.** 귀속 정보가 없으면 멀티 공급자 대시보드가 깨집니다.
- **부모 링크 없는 스팬.** 도구 스팬이 고아가 됩니다. 항상 컨텍스트를 전파하세요.
- **안정성 옵트인 미설정.** 백엔드 업그레이드 때 속성 이름이 바뀔 수 있습니다.

```figure
ae-genai-span-tree
```

## 만들어 보기

`code/main.py`는 GenAI 컨벤션에 맞는 표준 라이브러리 기반 스팬 방출기를 구현합니다.

- GenAI 속성 스키마를 갖는 `Span`.
- `start_span`과 중첩 컨텍스트를 갖는 `Tracer`.
- 다음을 발행하는 스크립트화된 에이전트 실행: `create_agent`, `invoke_agent`(INTERNAL), 도구별 스팬, LLM 호출용 `chat` 스팬.
- 프롬프트를 외부에 저장하고 스팬에는 ID만 기록하는 콘텐츠 수집 모드.

실행 방법:

```
python3 code/main.py
```

출력: 필수 GenAI 속성을 모두 갖춘 스팬 트리, 그리고 옵트인 콘텐츠 참조를 보여 주는 "외부 저장소".

## 활용하기

- **Datadog LLM Observability** (v1.37+) — 속성을 네이티브하게 매핑합니다.
- **Langfuse / Phoenix / Opik** (레슨 24) — 생태계를 자동 계측합니다.
- **Jaeger / Honeycomb / Grafana Tempo** — 원시 OTel 트레이스. GenAI 속성으로 대시보드를 만듭니다.
- **셀프 호스팅** — GenAI 프로세서를 붙인 OTel Collector를 직접 실행합니다.

## 출시하기

`outputs/skill-otel-genai.md`는 기존 에이전트에 OTel GenAI 스팬을 연결하되, 콘텐츠 수집 기본값(꺼짐)과 외부 참조 저장을 적용합니다.

## 연습 문제

1. 레슨 01의 ReAct 루프에 `invoke_agent`(INTERNAL) + 도구별 스팬으로 계측을 붙이고 Jaeger 인스턴스로 전송해 보세요.
2. "참조만" 모드의 콘텐츠 수집을 추가해 보세요. 프롬프트는 SQLite로, 스팬 속성에는 행 ID만 담습니다.
3. `gen_ai.data_source.id` 스펙을 읽어 보고, 레슨 09의 Mem0 검색에 연결해 보세요.
4. `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`을 설정하고, 컬렉터가 속성 이름을 바꾸지 않는지 확인해 보세요.
5. GenAI 속성만으로 "어떤 도구 오류가 어떤 모델과 연관되는지" 보여 주는 대시보드를 만들어 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| GenAI SIG | "OpenTelemetry GenAI 그룹" | 스키마를 정의하는 OTel 워킹 그룹 |
| invoke_agent | "에이전트 스팬" | 에이전트 실행을 나타내는 스팬의 이름 |
| CLIENT 스팬 | "원격 호출" | 원격 에이전트 서비스 호출에 대한 스팬 |
| INTERNAL 스팬 | "프로세스 내부" | 프로세스 안에서 도는 에이전트 실행에 대한 스팬 |
| gen_ai.provider.name | "공급자" | anthropic / openai / aws.bedrock / google.vertex |
| gen_ai.data_source.id | "RAG 소스" | 검색이 어떤 코퍼스/저장소를 조회했는지 |
| 콘텐츠 수집 | "프롬프트 로깅" | 옵트인 방식의 메시지 수집. 프로덕션에서는 외부 저장 권장 |
| 안정성 옵트인 | "프리뷰 모드" | 실험적 컨벤션을 고정하는 환경 변수 |

## 더 읽을거리

- [OpenTelemetry GenAI 시맨틱 컨벤션](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 스펙 본문
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — 기본으로 GenAI 스팬 발행
- [AutoGen v0.4 (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — OTel 스팬 내장
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) — W3C 트레이스 컨텍스트 전파
