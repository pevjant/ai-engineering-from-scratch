> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 함수 호출 심층 탐구 — OpenAI, Anthropic, Gemini

> 세 프론티어 프로바이더는 2024년에 같은 도구 호출 루프로 수렴했지만, 그 외의 모든 것에서는 갈라졌습니다. OpenAI는 `tools`와 `tool_calls`를 씁니다. Anthropic은 `tool_use`와 `tool_result` 블록을 씁니다. Gemini는 `functionDeclarations`와 고유 id 상관관계를 씁니다. 이 레슨은 셋을 나란히 비교(diff)해서, 한 프로바이더에서 출시한 코드를 포팅할 때 깨지지 않도록 돕습니다.

**유형:** Build(빌드)
**언어:** Python(표준 라이브러리, 스키마 변환기)
**선수 지식:** 페이즈 13 · 01(도구 인터페이스)
**시간:** 약 75분

## 학습 목표

- OpenAI, Anthropic, Gemini 함수 호출 페이로드의 세 가지 형태 차이(선언, 호출, 결과)를 말할 수 있습니다.
- 하나의 도구 선언을 세 프로바이더 형식 모두로 번역하고, strict 모드 제약이 어디서 달라질지 예측할 수 있습니다.
- 각 프로바이더에서 `tool_choice`를 사용해 도구 호출을 강제하거나, 금지하거나, 자동으로 고르게 할 수 있습니다.
- 프로바이더별 하드 리밋(도구 수, 스키마 깊이, 인자 길이)과 한도를 넘겼을 때 각 프로바이더가 내보내는 에러 시그니처를 알 수 있습니다.

## 문제

함수 호출 요청의 모양은 프로바이더마다 다릅니다. 2026년 프로덕션 스택에서 뽑은 세 가지 실제 예제입니다.

**OpenAI Chat Completions / Responses API.** `tools: [{type: "function", function: {name, description, parameters, strict}}]`를 넘깁니다. 모델의 응답에는 `choices[0].message.tool_calls: [{id, type: "function", function: {name, arguments}}]`가 담기는데, `arguments`는 여러분이 직접 파싱해야 하는 JSON 문자열입니다. strict 모드(`strict: true`)는 제약 디코딩으로 스키마 준수를 강제합니다.

**Anthropic Messages API.** `tools: [{name, description, input_schema}]`를 넘깁니다. 응답은 `content: [{type: "text"}, {type: "tool_use", id, name, input}]` 형태로 돌아옵니다. `input`은 이미 파싱되어 있습니다(문자열이 아니라 객체). 여러분은 `{type: "tool_result", tool_use_id, content}` 블록을 담은 새 `user` 메시지로 답합니다.

**Google Gemini API.** `tools: [{functionDeclarations: [{name, description, parameters}]}]`를 넘깁니다(`functionDeclarations` 아래에 중첩). 응답은 `candidates[0].content.parts: [{functionCall: {name, args, id}}]`로 도착하는데, `id`는 Gemini 3 이상에서 병렬 호출 상관관계를 위해 고유합니다. 여러분은 `{functionResponse: {name, id, response}}`로 답합니다.

같은 루프입니다. 그런데 필드 이름도, 중첩 구조도, 문자열-vs-객체 관례도, 상관관계 메커니즘도 다릅니다. OpenAI로 날씨 에이전트를 만든 팀은 배관 작업만으로 Anthropic 포팅에 이틀, Gemini 포팅에 또 하루를 지불합니다.

이 레슨은 세 형식을 하나의 정규(canonical) 도구 선언으로 통일하고 엣지에서 라우팅하는 변환기를 만듭니다. 페이즈 13 · 17은 같은 패턴을 LLM 게이트웨이로 일반화합니다.

## 개념

### 공통 구조

모든 프로바이더에게 필요한 것은 다섯 가지입니다.

1. **도구 목록.** 도구별 이름, 설명, 입력 스키마.
2. **도구 선택.** 특정 도구 강제, 도구 금지, 또는 모델의 판단에 맡기기.
3. **호출 방출.** 도구 이름과 인자를 담은 구조화된 출력.
4. **호출 id.** 응답을 올바른 호출과 연결(병렬일 때 중요).
5. **결과 주입.** 결과를 호출에 다시 묶어 주는 메시지 또는 블록.

### 형태 차이, 필드별로

| 항목 | OpenAI | Anthropic | Gemini |
|--------|--------|-----------|--------|
| 선언 봉투 | `{type: "function", function: {...}}` | `{name, description, input_schema}` | `{functionDeclarations: [{...}]}` |
| 스키마 필드 | `parameters` | `input_schema` | `parameters` |
| 응답 컨테이너 | 어시스턴트 메시지의 `tool_calls[]` | 타입이 `tool_use`인 `content[]` | 타입이 `functionCall`인 `parts[]` |
| 인자 타입 | 문자열화된 JSON | 파싱된 객체 | 파싱된 객체 |
| id 형식 | `call_...`(OpenAI가 생성) | `toolu_...`(Anthropic) | UUID(Gemini 3+) |
| 결과 블록 | role `tool`, `tool_call_id` | `tool_result`, `tool_use_id`를 담은 `user` | 짝이 맞는 `id`를 가진 `functionResponse` |
| 도구 강제 | `tool_choice: {type: "function", function: {name}}` | `tool_choice: {type: "tool", name}` | `tool_config: {function_calling_config: {mode: "ANY"}}` |
| 도구 금지 | `tool_choice: "none"` | `tool_choice: {type: "none"}` | `mode: "NONE"` |
| strict 스키마 | `strict: true` | 스키마가 곧 계약(항상 강제됨) | 요청 수준의 `responseSchema` |

### 실제로 부딪히는 한도

- **OpenAI.** 요청당 도구 128개. 스키마 깊이 5. 인자 문자열은 8192바이트 이하. strict 모드는 `$ref` 금지, 겹치는 `oneOf`/`anyOf`/`allOf` 금지, 모든 프로퍼티를 `required`에 명시해야 합니다.
- **Anthropic.** 요청당 도구 64개. 스키마 깊이는 사실상 무제한이지만 실질 한도는 10. strict 모드 플래그는 없습니다. 스키마가 곧 계약이고 모델이 대체로 이를 지킵니다.
- **Gemini.** 요청당 함수 64개. 스키마 타입은 OpenAPI 3.0 서브셋(JSON Schema 2020-12와 살짝 갈라짐). 병렬 호출용 고유 id는 Gemini 3부터.

### `tool_choice` 동작

모두가 지원하는 세 모드, 이름만 다를 뿐입니다.

- **Auto.** 모델이 도구나 텍스트를 고릅니다. 기본값.
- **Required / Any.** 모델이 최소 하나의 도구를 호출해야 합니다.
- **None.** 모델은 도구를 호출하면 안 됩니다.

거기에 프로바이더별 고유 모드가 하나씩 있습니다.

- **OpenAI.** 이름으로 특정 도구를 강제합니다.
- **Anthropic.** 이름으로 특정 도구를 강제합니다. `disable_parallel_tool_use` 플래그가 단일/다중을 나눕니다.
- **Gemini.** `mode: "VALIDATED"`는 모델의 의도와 무관하게 모든 응답을 스키마 검증기로 통과시킵니다.

### 병렬 호출

OpenAI의 `parallel_tool_calls: true`(기본값)는 하나의 어시스턴트 메시지에 여러 호출을 담습니다. 여러분은 전부 실행하고 `tool_call_id`마다 항목을 하나씩 담은 배치형 tool 역할 메시지로 답합니다. Anthropic은 역사적으로 단일 호출이었고, `disable_parallel_tool_use: false`(Claude 3.5부터 기본값)가 다중 호출을 켭니다. Gemini 2는 병렬 호출을 허용했지만 안정적인 id를 주지 않았습니다. Gemini 3는 UUID를 추가해 순서가 뒤엉킨 응답도 깔끔하게 연결됩니다.

### 스트리밍

셋 모두 스트리밍 도구 호출을 지원합니다. 와이어 형식은 다릅니다.

- **OpenAI.** `tool_calls[i].function.arguments`의 델타 청크가 점진적으로 도착합니다. `finish_reason: "tool_calls"`가 올 때까지 누적합니다.
- **Anthropic.** 블록 시작 / 블록 델타 / 블록 종료 이벤트. `input_json_delta` 청크가 부분 인자를 실어 나릅니다.
- **Gemini.** `streamFunctionCallArguments`(Gemini 3에서 새로 등장)가 `functionCallId`를 가진 청크를 내보내 여러 병렬 호출이 서로 섞일 수 있게 합니다.

페이즈 13 · 03에서 병렬 + 스트리밍 재조립을 깊게 다룹니다. 이 레슨은 선언과 단일 호출 형태에 집중합니다.

### 에러와 복구

잘못된 인자 에러도 제각각으로 생겼습니다.

- **OpenAI(non-strict).** 모델이 `arguments: "{bad json}"`을 돌려주고, JSON 파싱이 실패하면, 여러분은 에러 메시지를 주입하고 다시 호출합니다.
- **OpenAI(strict).** 검증은 디코딩 중에 일어납니다. 잘못된 JSON은 불가능하지만 `refusal`이 나타날 수 있습니다.
- **Anthropic.** `input`에 예상치 못한 필드이 있을 수 있습니다. 스키마는 권고 사항입니다. 서버 쪽에서 검증하세요.
- **Gemini.** OpenAPI 3.0의 특이점: 객체 필드의 `enum`은 조용히 무시됩니다. 직접 검증하세요.

### 변환기 패턴

코드 속 정규 도구 선언은 이렇게 생겼습니다(형태는 여러분이 고릅니다).

```python
Tool(
    name="get_weather",
    description="Use when ...",
    input_schema={"type": "object", "properties": {...}, "required": [...]},
    strict=True,
)
```

작은 함수 세 개가 이것을 세 프로바이더 형태로 번역합니다. `code/main.py`의 하네스가 정확히 이 일을 하고, 가짜 도구 호출을 각 프로바이더의 응답 형태로 왕복시킵니다. 네트워크가 필요 없습니다. 이 레슨은 HTTP가 아니라 형태를 가르칩니다.

프로덕션 팀들은 이 변환기를 `AbstractToolset`(Pydantic AI), `UniversalToolNode`(LangGraph), `BaseTool`(LlamaIndex)로 감쌉니다. 페이즈 13 · 17은 셋 중 무엇이든 뒤에 두고 OpenAI 형태 API를 노출하는 게이트웨이를 출시합니다.

```figure
function-call-args
```

## 활용하기

`code/main.py`는 하나의 정규 `Tool` 데이터클래스와, OpenAI·Anthropic·Gemini 선언 JSON을 만들어 내는 세 변환기를 정의합니다. 그다음 각 형태로 손수 만든 프로바이더 응답을 같은 정규 호출 객체로 파싱해, 겉모습 아래 의미론이 동일함을 보여 줍니다. 실행해 보고 세 선언을 나란히 비교해 보세요.

볼 포인트:

- 세 선언 블록은 봉투와 필드 이름만 다릅니다.
- 세 응답 블록은 호출이 어디 사는지가 다릅니다(최상위 `tool_calls`, `content[]` 블록, `parts[]` 항목).
- 하나의 `canonical_call()` 함수가 세 응답 형태 모두에서 `{id, name, args}`를 뽑아 냅니다.

## 출시하기

이 레슨은 `outputs/skill-provider-portability-audit.md`를 만듭니다. 한 프로바이더에 맞춘 함수 호출 통합이 주어지면, 이 스킬이 포터빌리티(이식성) 감사를 만들어 냅니다. 어떤 프로바이더 한도에 의존하는지, 어떤 필드 이름을 바꿔야 하는지, 다른 프로바이더로 포팅하면 무엇이 깨지는지 알려 주죠.

## 연습 문제

1. `code/main.py`를 실행해 세 프로바이더 선언 JSON이 모두 같은 `Tool` 객체를 직렬화하는지 확인하세요. 정규 도구에 enum 파라미터를 추가하고, OpenAPI 특이점을 다뤄야 하는 곳이 Gemini 변환기뿐인지 확인해 보세요.

2. 각 프로바이더마다 `list_tools` 또는 디스커버리 호출 후 모델이 돌려주는 도구 목록을 뽑아 내는 `ListToolsResponse` 파서를 추가하세요. OpenAI는 네이티브로 이런 게 없습니다. 이 비대칭을 기록해 두세요.

3. `tool_choice` 변환을 구현하세요. 정규 `ToolChoice(mode="force", tool_name="x")`를 세 프로바이더 형태 모두로 매핑해 보세요. 그다음 `mode="any"`와 `mode="none"`도 매핑하세요. 레슨의 diff 표를 확인하세요.

4. 세 프로바이더 중 하나를 골라 함수 호출 가이드를 처음부터 끝까지 읽으세요. 다른 둘이 지원하지 않는 스키마 명세의 필드를 하나 찾으세요. 후보: OpenAI `strict`, Anthropic `disable_parallel_tool_use`, Gemini `function_calling_config.allowed_function_names`.

5. 테스트 벡터를 작성하세요. 선언된 스키마를 어기는 인자를 가진 도구 호출입니다. 이것을 각 프로바이더의 검증기(레슨 01의 표준 라이브러리 검증기를 대리로 써도 됩니다)에 돌리고 어떤 에러가 발생하는지 기록하세요. 엄격함(strictness) 면에서 프로덕션에 쓸 프로바이더가 어디인지 문서화하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| 함수 호출(Function calling) | "도구 사용" | 구조화된 도구 호출 방출을 위한 프로바이더 수준 API |
| 도구 선언(Tool declaration) | "도구 명세" | 이름 + 설명 + JSON Schema 입력 페이로드 |
| `tool_choice` | "강제 / 금지" | Auto / required / none / 특정 이름 모드 |
| Strict 모드 | "스키마 강제" | 디코딩이 스키마에 맞도록 구속하는 OpenAI 플래그 |
| `tool_use` 블록 | "Anthropic의 호출 형태" | id, name, input을 담은 인라인 콘텐츠 블록 |
| `functionCall` 파트 | "Gemini의 호출 형태" | name, args, id를 담은 `parts[]` 항목 |
| 문자열 인자(Arguments-as-string) | "문자열화된 JSON" | OpenAI는 인자를 객체가 아니라 JSON 문자열로 돌려줌 |
| 병렬 도구 호출(Parallel tool calls) | "한 턴에 펼쳐 내기" | 하나의 어시스턴트 메시지 안의 여러 도구 호출 |
| Refusal(거절) | "모델이 사양함" | 호출 대신 나오는 strict 모드 전용 거절 블록 |
| OpenAPI 3.0 서브셋 | "Gemini 스키마 특이점" | Gemini는 JSON Schema와 비슷하지만 사소한 차이가 있는 방언을 씀 |

## 더 읽기

- [OpenAI — 함수 호출 가이드](https://platform.openai.com/docs/guides/function-calling) — strict 모드와 병렬 호출을 포함한 정규 레퍼런스
- [Anthropic — 도구 사용 개요](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) — `tool_use`와 `tool_result` 블록 의미론
- [Google — Gemini 함수 호출](https://ai.google.dev/gemini-api/docs/function-calling) — 병렬 호출, 고유 id, OpenAPI 서브셋
- [Vertex AI — 함수 호출 레퍼런스](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling) — Gemini의 엔터프라이즈 표면
- [OpenAI — 구조화된 출력](https://platform.openai.com/docs/guides/structured-outputs) — strict 모드 스키마 강제 상세
