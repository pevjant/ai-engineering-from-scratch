> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 병렬 도구 호출과 도구 스트리밍

> 날씨 조회 세 번을 순서대로 돌리면 왕복 세 번입니다. 병렬로 돌리면 총 시간이 가장 느린 호출 하나의 시간으로 줄어듭니다. 이제 모든 프론티어 프로바이더가 한 턴에 여러 도구 호출을 내보냅니다. 이득은 확실한데, 배관이 은근히 까다롭습니다. 이 레슨은 두 축 — 병렬 펼쳐 내기(fan-out)와 스트리밍된 인자 재조립 — 을 모두 다루며, 특히 id 상관관계 함정을 강조합니다.

**유형:** Build(빌드)
**언어:** Python(표준 라이브러리, 스레드 풀 + 스트리밍 하네스)
**선수 지식:** 페이즈 13 · 02(함수 호출 심층 탐구)
**시간:** 약 75분

## 학습 목표

- `parallel_tool_calls: true`가 왜 존재하는지, 언제 끄는지 설명할 수 있습니다.
- 병렬 펼쳐 내기 중에 스트리밍된 인자 청크를 올바른 도구 호출 id와 연결 지을 수 있습니다.
- 부분 `arguments` 문자열을 파싱을 서두르지 않고 완전한 JSON으로 재조립할 수 있습니다.
- 순차 실행 대비 병렬 실행의 지연 시간 이득을 보여 주는 3개 도시 날씨 벤치마크를 실행할 수 있습니다.

## 문제

병렬 호출이 없으면 "벵갈루루, 도쿄, 취리히 날씨"에 답하는 에이전트는 이렇게 움직입니다.

```
user -> LLM
LLM -> call get_weather(Bengaluru)
host -> run executor, reply with result
LLM -> call get_weather(Tokyo)
host -> run executor, reply with result
LLM -> call get_weather(Zurich)
host -> run executor, reply with result
LLM -> final text answer
```

LLM 왕복 세 번, 그리고 각 왕복마다 실행기 지연 시간까지 치릅니다. 이상적인 벽시계 시간의 대략 4배죠.

병렬 호출이 있으면 이렇게 됩니다.

```
user -> LLM
LLM -> call get_weather(Bengaluru); call get_weather(Tokyo); call get_weather(Zurich)
host -> run all three executors concurrently, reply with three results
LLM -> final text answer
```

LLM 왕복 한 번. 실행기 시간은 세 개의 합이 아니라 최댓값입니다. OpenAI, Anthropic, Gemini의 프로덕션 벤치마크는 펼쳐 내기(fan-out) 워크로드에서 벽시계 시간이 60~70퍼센트 줄어듦을 보여 줍니다.

대가는 상관관계 복잡도입니다. 세 호출이 순서가 뒤엉켜 완료될 때, 결과들이 짝이 맞는 `tool_call_id`를 달고 있어야 모델이 줄을 맞출 수 있습니다. 결과가 스트리밍될 때는 실행 전에 부분 인자 조각들을 완전한 JSON으로 조립해야 합니다. Gemini 3가 고유 id를 추가한 것은 부분적으로, 같은 도구로 향하는 두 병렬 호출을 구분할 수 없었던 실제 문제를 풀기 위함이었습니다.

## 개념

### 병렬 켜기

- **OpenAI.** `parallel_tool_calls: true`가 기본값. `false`로 두면 직렬로 강제합니다.
- **Anthropic.** `disable_parallel_tool_use: false`로 병렬(Claude 3.5 이상 기본값). `true`로 두면 직렬.
- **Gemini.** 항상 병렬 가능. `tool_config.function_calling_config.mode = "AUTO"`면 모델이 결정합니다.

도구 사이에 순서 의존성이 있을 때(`create_file` 후 `write_file`), 한 호출의 출력이 다른 호출의 입력을 알려 줄 때, 또는 레이트 리미터가 펼쳐 내기를 감당하지 못할 때는 병렬을 끄세요.

### id 상관관계

모델이 내보내는 모든 호출에는 `id`가 있습니다. 호스트가 돌려주는 모든 결과에는 같은 id가 들어 있어야 합니다. 이게 없으면 결과들이 모호해집니다.

- **OpenAI.** tool 역할 메시지마다 `tool_call_id`.
- **Anthropic.** `tool_result` 블록마다 `tool_use_id`.
- **Gemini.** `functionResponse`마다 `id`(Gemini 3 이상; Gemini 2는 이름으로 매칭했기 때문에 같은 이름의 병렬 호출이 깨졌습니다).

### 호출 동시에 실행하기

호스트는 각 호출의 실행기를 자기만의 스레드, 코루틴, 또는 원격 워커에서 돌립니다. 가장 간단한 하네스는 스레드 풀이고, 프로덕션은 `asyncio.gather`를 쓰는 asyncio 또는 구조적 동시성을 씁니다. 완료 순서는 예측할 수 없습니다. id가 곧 식별자입니다.

흔한 버그 하나: 결과를 완료 순서가 아니라 호출 목록 순서로 답하는 것. 모델은 `tool_call_id`만 신경 쓰기 때문에 보통은 잘 동작하지만, 결과가 누락되거나 중복되면 뒤엉킨 제출 순서가 디버깅을 어렵게 만듭니다. 완료 순서대로 명시적인 id와 함께 답하는 편이 좋습니다.

### 도구 호출 스트리밍

모델이 스트리밍하면 `arguments`가 조각으로 도착합니다. 세 병렬 호출의 세 청크 스트림이 와이어 위에서 섞입니다. id마다 누산기(accumulator)가 하나씩 필요합니다.

프로바이더별 모양:

- **OpenAI.** 각 청크는 `choices[0].delta.tool_calls[i].function.arguments`(부분 문자열)입니다. 청크는 `index`(호출 목록에서의 위치)를 실어 나릅니다. index별로 누적하고, `id`가 처음 나타날 때 읽고, `finish_reason = "tool_calls"`가 오면 JSON을 파싱합니다.
- **Anthropic.** 스트림 이벤트는 `message_start`로 시작하고, 타입이 `tool_use`인 블록마다 하나의 `content_block_start`(id, 이름, 빈 input을 담음)가 따라옵니다. `content_block_delta` 이벤트가 `input_json_delta` 청크를 실어 나르고, `content_block_stop`이 각 블록을 닫습니다.
- **Gemini.** `streamFunctionCallArguments`(Gemini 3 이상)가 `functionCallId`를 가진 청크를 내보내 호출이 깔끔하게 섞이게 합니다. Gemini 3 전에는 스트리밍이 한 번에 완전한 호출 하나를 돌려줬습니다.

### 부분 JSON과 조급한 파싱의 함정

`arguments`는 완성되기 전에는 파싱할 수 없습니다. `{"city": "Beng` 같은 부분 JSON은 유효하지 않아 예외가 터집니다. 올바른 게이트는 프로바이더의 호출 종료 신호입니다. OpenAI의 `finish_reason = "tool_calls"`, Anthropic의 `content_block_stop`, 또는 Gemini의 스트림 종료 이벤트죠. 그때 비로소 `json.loads`를 시도하세요. 더 튼튼한 방법은 구조가 완성될 때마다 이벤트를 내보내는 증분 JSON 파서입니다. OpenAI의 스트리밍 가이드는 실시간 "생각 중" 표시기 같은 UX를 위해 이를 추천합니다. 중괄호 개수 세기는 완성도 판정으로는 믿을 수 없습니다(따옴표 안이나 이스케이프된 내용 속 중괄호가 거짓 양성을 만듭니다). 비공식 디버그 휴리스틱으로만 쓰세요.

### 순서가 뒤엉킨 완료

```
call_A: fast API, returns first
call_B: slow API, returns second
call_C: median API, returns third
```

호스트의 답장은 여전히 id를 밝혀야 합니다.

```
[{role: "tool", tool_call_id: "call_A", content: ...},
 {role: "tool", tool_call_id: "call_B", content: ...},
 {role: "tool", tool_call_id: "call_C", content: ...}]
```

답장에서의 순서는 OpenAI나 Anthropic에서 정확성에 영향을 주지 않습니다. Gemini도 id만 맞으면 어떤 순서든 받아들입니다.

### 벤치마크: 순차 vs 병렬

`code/main.py`의 하네스는 400, 600, 800밀리초 지연을 가진 세 실행기를 흉내 냅니다. 순차로 돌리면 총 1800밀리초. 병렬로 돌리면 max(400, 600, 800) = 800밀리초. 차이는 비례가 아니라 일정하므로, 도구 수가 늘어날수록 절약이 커집니다.

현실의 단서: 병렬 호출은 다운스트림 API에 부담을 줍니다. 레이트 리밋이 있는 서비스로 10갈래 펼쳐 내기는 실패합니다. 페이즈 13 · 17이 게이트웨이 수준 배압(backpressure)을 다루고, 재시도 의미론은 향후 페이즈에서 다룰 예정입니다.

### 스트리밍 펼쳐 내기의 벽시계 시간

모델 자체가 스트리밍한다면, 모든 호출이 확정되기를 기다릴 필요 없이 한 호출의 인자가 완성되는 즉시 실행을 시작할 수 있습니다. OpenAI가 문서화한 최적화지만 모든 SDK가 노출하는 것은 아닙니다. 이 레슨의 하네스가 정확히 이렇게 합니다. 흉내 낸 스트림이 완전한 인자 객체를 뱉는 즉시 호스트가 그 호출을 착수합니다.

```figure
tp-parallel-fanout
```

## 활용하기

`code/main.py`는 두 부분으로 되어 있습니다. 첫 부분은 흉내 낸 날씨 호출 세 개를 `concurrent.futures.ThreadPoolExecutor`로 순차/병렬 실행하고 벽시계 시간을 출력합니다. 둘째 부분은 가짜 스트리밍 응답 — 세 병렬 호출의 `arguments` 청크가 한 스트림 위에서 섞인 것 — 을 재생하고 `StreamAccumulator`로 id별 재조립합니다. LLM도 네트워크도 없습니다. 재조립 로직만 있습니다.

볼 포인트:

- 순차 타이머는 1.8초를 찍습니다. 병렬 타이머는 같은 가짜 지연에서 0.8초를 찍습니다.
- 누산기는 순서가 뒤엉켜 도착하는 청크를 id별 버퍼링으로 처리하고, 각 호출의 JSON이 완성됐을 때만 파싱합니다.
- 실행기는 모든 스트림이 끝난 뒤가 아니라, 한 id의 인자가 확정되는 즉시 착수합니다.

## 출시하기

이 레슨은 `outputs/skill-parallel-call-safety-check.md`를 만듭니다. 도구 레지스트리가 주어지면, 이 스킬이 어떤 도구가 병렬화해도 안전한지, 어떤 도구가 순서 의존성을 갖는지, 어떤 도구가 다운스트림 레이트 리밋을 압도할지 감사합니다. 그리고 도구별 `parallel_safe` 플래그를 단 수정된 레지스트리를 돌려줍니다.

## 연습 문제

1. `code/main.py`를 실행하며 흉내 낸 지연을 바꿔 보세요. 병렬/순차 비율이 대략 `max/sum`인지 확인하세요(실제 실행은 스레드 스케줄링, 직렬화, 하네스 오버헤드 때문에 이상값에서 조금 벗어납니다). 어떤 지연 분포에서 병렬이 더 이상 의미 없어질까요?

2. 누산기를 확장해 "호출이 스트림 도중 취소됨" 사례를 처리하세요. 버퍼를 버리고 `cancelled` 이벤트를 내보내는 방식입니다. 어떤 프로바이더가 이 사례를 명시적으로 문서화하고 있나요? Anthropic의 `content_block_stop` 의미론과 OpenAI의 `finish_reason: "length"` 동작을 확인해 보세요.

3. 스레드 풀을 `asyncio.gather`로 바꿔 보세요. 둘 다 벤치마크하세요. 컨텍스트 스위치 비용이 낮아 비동기에서 작은 이득을 봐야 하지만, 실행기가 진짜 I/O를 할 때만 그렇습니다.

4. 병렬화하면 안 되는 도구 두 개를 고르세요(예: `create_file` 후 `write_file`). 레지스트리에 `ordering_dependency` 그래프를 추가하고 병렬 펼쳐 내기를 그 그래프로 게이트하세요. 이것이 의존성을 인지하는 스케줄링의 최소 장치이며, 향후 에이전트 엔지니어링 페이즈에서 형식화합니다.

5. OpenAI의 병렬 함수 호출 섹션과 Anthropic의 `disable_parallel_tool_use` 문서를 읽으세요. Anthropic이 병렬화를 끄라고 권하는 실전 도구 유형 하나를 찾으세요. (힌트: 같은 리소스에 대한 결과형 변경.)

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| 병렬 도구 호출(Parallel tool calls) | "한 턴에 펼쳐 내기" | 모델이 하나의 어시스턴트 메시지에 여러 도구 호출을 내보냄 |
| `parallel_tool_calls` | "OpenAI의 플래그" | 다중 호출 방출 켜기/끄기 |
| `disable_parallel_tool_use` | "Anthropic의 역방향" | 옵트아웃 플래그. 기본값은 병렬 활성화 |
| 도구 호출 id(Tool call id) | "상관관계 손잡이" | 결과 메시지가 반드시 되돌려 말해야 하는 호출별 식별자 |
| 누산기(Accumulator) | "스트림 버퍼" | 부분 `arguments` 청크를 담는 id별 문자열 버퍼 |
| 순서가 뒤엉킨 완료(Out-of-order completion) | "빠른 것 먼저" | 병렬 호출이 예측 불가능한 순서로 끝남. id가 접착제 |
| 의존성 그래프(Dependency graph) | "순서 제약" | 출력이 다른 도구의 입력으로 들어가는 도구들. 병렬화 불가 |
| 조급한 파싱 함정(Parse-early trap) | "JSON.parse 폭발" | 불완전한 `arguments` 문자열을 파싱하려 시도하는 것 |
| `streamFunctionCallArguments` | "Gemini 3 기능" | 호출별 고유 id를 가진 스트리밍 인자 청크 |
| 완료 순서 답장(Completion-order reply) | "전부 기다리지 않기" | 결과가 도착하는 대로 id를 키로 답장 |

## 더 읽기

- [OpenAI — 병렬 함수 호출](https://platform.openai.com/docs/guides/function-calling#parallel-function-calling) — 기본 동작과 옵트아웃 플래그
- [Anthropic — 도구 사용: 도구 사용 구현](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implementing-tool-use) — `disable_parallel_tool_use`와 결과 배치 처리
- [Google — Gemini 함수 호출 병렬 섹션](https://ai.google.dev/gemini-api/docs/function-calling) — Gemini 3부터의 id 상관관계 병렬 호출
- [OpenAI — 도구와 함께 스트리밍 응답](https://platform.openai.com/docs/api-reference/responses-streaming) — OpenAI 스트림의 청크 인자 재조립
- [Anthropic — 메시지 스트리밍](https://docs.anthropic.com/en/api/messages-streaming) — `input_json_delta`를 담은 `content_block_delta`
