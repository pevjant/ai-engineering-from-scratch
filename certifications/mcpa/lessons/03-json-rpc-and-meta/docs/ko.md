> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# JSON-RPC 봉투(envelope)

> 한 번도 여러분과 이야기해 본 적 없는 서버라도, 이 단 한 개의 메시지만으로 다음을 알아야 합니다. 답장을 기다리는 요청인지, 어떤 프로토콜 버전을 말하는지, 그리고 메타데이터가 어디서 끝나고 인자가 어디서 시작하는지 말이죠.

**유형:** 레퍼런스
**언어:** Python
**선수 지식:** 레슨 02
**시간:** 약 45분

## 학습 목표

- 와이어 위의 아무 2026-07-28 메시지를 요청, 알림(notification), 결과 응답, 오류 응답 중 하나로 분류하고, 각각을 그렇게 만드는 id 규칙 말하기
- resultType의 의미, complete와 input_required가 두 핵심 값인 이유, 클라이언트가 인식 못하는 값이나 없는 값을 어떻게 다뤄야 하는지 설명하기
- `_meta` 키 이름을 접두사(prefix)와 이름(name) 문법으로 검증하고, 비슷해 보이는 접두사와 예약된 MCP 접두사를 첫 라벨이 아니라 두 번째 라벨로 구분하기
- 요청, 알림, 결과가 각각 실는 예약된 `_meta` 키들과, OpenTelemetry 트레이스 컨텍스트를 위해 접두사 규칙이 만드는 유일한 예외 말하기
- 필수 `_meta` 필드가 빠진 요청이 `-32602`로 거부되는 이유, 그리고 어떤 두 MCP 메시지도 하나의 배치(batch)로 함께 이동하지 않는 이유 설명하기

## 문제 상황

레슨 02는 한 클라이언트가 한 번도 본 적 없는 두 서버를 디스커버하고 각각의 툴을 호출하는 모습을 보여 줬습니다. 그 교환의 밑바닥에는 시험이 망설임 없이 답하길 기대하는 더 작고 더 예리한 질문이 있습니다. stdio로 갓 들어왔거나 Streamable HTTP POST 본문에 도착한 정체불명의 JSON 덩어리를 받았을 때, 그것은 어떤 종류의 메시지인가? 그리고 수신자가 그것에 대해 가정해도 되는 것은 무엇인가?

JSON-RPC 2.0은 MCP에게 선택 가능한 네 가지 모양을 주고, 사양은 수신자가 그것들을 어떻게 구분하는지 엄격하게 규정합니다. 상태 비저장 서버에게는 연결 수준의 합의라는 안전망이 없기 때문입니다. "이 연결은 버전 X로 이야기한다"거나 "이 스트림은 클라이언트 Y의 요청만 실는다"고 못 박아 둔 오프닝 핸드셰이크 같은 것은 존재한 적이 없습니다. 모든 메시지는 자신의 정체에 충분한 정보를 직접 실어야 합니다. 그래야 수신자가 그 메시지를 고립된 상태로 처리하더라도 — 바로 직전 메시지를 처리한 것과 완전히 다른 서버 레플리카에서 처리될 수도 있습니다 — 언제나 같은 결론에 도달합니다.

이 자기 기술(self-description)은 두 층에서 일어납니다. 바깥층은 봉투 자체입니다. 이것이 답장을 기다리는 요청인지, 그렇지 않은 알림인지, 일을 끝낸 결과인지, 끝내지 못한 오류인지 말이죠. `id` 필드를 잘못 다루면 서버는 요청과 알림을 구분하지 못하고, 클라이언트는 응답을 그것을 만든 호출에 다시 연결짓지 못합니다. 안쪽 층은 `_meta`입니다. 요청, 알림, 결과가 프로토콜 수준의 사실 — 예컨대 요청이 어떤 프로토콜 버전을 말한다는 사실 — 을 실을 때 쓰는 속성으로, 이러한 사실들이 애플리케이션이 자기 인자에서 부르는 `version`이나 `capabilities`와 충돌하지 않게 해 줍니다. `_meta` 명명 규칙을 잘못 다루면 서버 고유의 필드가 프로토콜이 의존하는 필드를 조용히 가려 버리거나, 그 반대가 일어날 수 있습니다.

## 개념

**네 가지 모양, 하나씩의 규칙.** 요청(request)은 `id`, `method`, 선택적 `params`를 실습니다. id는 문자열이나 정수여야 하고, 절대 `null`이어서는 안 되며, 보낸 쪽이 아직 답을 기다리고 있는 id를 재사용해서도 안 됩니다.

```json
{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "get_weather", "arguments": {"location": "Pune"}}}
```

알림(notification)은 `method`와 선택적 `params`를 실고, `id`를 전혀 포함해서는 안 됩니다. 수신자는 성공이든 실패든 그 어떤 답장도 보내서는 안 됩니다. 절대로요.

```json
{"jsonrpc": "2.0", "method": "notifications/progress", "params": {"progressToken": 7, "progress": 1, "total": 2}}
```

결과 응답(result response)은 요청의 `id`를 그대로 되돌려 주며 `result` 객체를 실습니다. 그 객체에는 `resultType` 필드가 반드시 포함되어야 합니다.

```json
{"jsonrpc": "2.0", "id": 7, "result": {"resultType": "complete", "content": [{"type": "text", "text": "Pune: sunny, 26C"}], "isError": false}}
```

오류 응답(error response)도 요청의 `id`를 되돌려 줍니다. 단 하나의 예외가 있습니다. 요청이 너무 심하게 깨져 파싱조차 불가능해서 id를 읽을 수 없었던 경우입니다. 오류 응답은 정수 `code`와 문자열 `message`를 가진 `error` 객체를 실고, `data` 필드를 덧붙일 수도 있습니다.

```json
{"jsonrpc": "2.0", "id": 3, "error": {"code": -32602, "message": "Missing required _meta field(s): io.modelcontextprotocol/protocolVersion"}}
```

**resultType은 클라이언트에게 뒤따르는 내용을 어떻게 읽어야 하는지 알려 줍니다.** `"complete"`라는 값은 결과가 최종 콘텐츠를 담고 있고 더 할 일이 없다는 뜻입니다. `"input_required"`라는 값은 결과가 `InputRequiredResult`라는 뜻입니다. 원래 호출을 끝내기 전에 클라이언트에게 더 받아야 할 것이 있을 때 쓰는 모양으로, 다중 왕복(multi round-trip) 패턴이 사용합니다. 이 재시도 메커니즘은 이 경로의 뒤에서 자기만의 레슨을 갖습니다. 확장(extension)은 `"task"`처럼 장기 실행 작업용 추가 값을 등록할 수 있지만, 클라이언트가 그에 맞는 기능(capability)을 광고했을 때에만 그렇습니다. 인식할 수 없는 resultType을 받은 클라이언트는 모양을 추측하는 대신 그 결과를 무효(invalid)로 다뤄야 합니다. 그리고 이전 프로토콜 버전으로 이야기하는, resultType을 아예 보낸 적 없는 서버와 대화하는 클라이언트는 그 없는 필드를 `"complete"`로 다뤄야 합니다. 그 외엔 엄격한 이 규칙이 하위 호환을 위해 유일하게 허용하는 부분입니다.

**`_meta`는 프로토콜 사실을 애플리케이션 자신의 이름공간 밖에 둡니다.** `_meta` 키는 두 부분으로 이루어집니다. 선택적 접두사와 이름입니다. 접두사가 있을 때 그것은 점으로 구분된 하나 이상의 라벨 뒤에 슬래시가 붙은 형태입니다. 각 라벨은 문자로 시작하고, 문자나 숫자로 끝나며, 중간에는 문자, 숫자, 하이픈을 쓸 수 있습니다. 이름은 비어 있지 않은 경우 영숫자로 시작하고 끝나며, 중간에는 문자, 숫자, 하이픈, 밑줄, 점을 쓸 수 있습니다. 접두사는 그 두 번째 라벨(첫 번째가 아닙니다!)이 `modelcontextprotocol` 또는 `mcp`일 때 MCP 전용으로 예약됩니다. 바로 이 "두 번째"라는 단어에 시험 함정의 대부분이 숨어 있습니다. `io.modelcontextprotocol/protocolVersion`과 `dev.mcp/anything`은 둘 다 예약되어 있습니다. `modelcontextprotocol`과 `mcp`가 두 번째 위치에 있기 때문이죠. `com.example.mcp/scanId`는 예약되지 않았습니다. 두 번째 라벨이 `example`이고 `mcp`는 세 번째에 등장하기 때문입니다. `mcp.example/thing`처럼 `mcp`가 첫 번째 라벨이고 두 번째에 아무 예약어도 없는 키도 이 규칙에 따르면 예약되지 않습니다. 구현체는 자기 접두사에 역방향 DNS 표기법, 예컨대 `example.com/`이 아니라 `com.example/`을 쓰는 것이 권장됩니다. 이름공간 충돌이 사고가 아니라 선택이 되도록 하기 위함입니다.

**모든 요청은 자기 버전과 기능을 밝히고, 모든 결과는 누가 답했는지 말할 수 있습니다.** `io.modelcontextprotocol/` 아래 세 `_meta` 키가 모든 요청에서 중요합니다. `protocolVersion`(문자열, 필수), `clientCapabilities`(객체, 필수, 비어 있어도 됨), 그리고 `clientInfo`(클라이언트를 밝히는 `Implementation`. 엄밀히 필수는 아니지만 클라이언트가 의도적으로 생략하도록 설정한 경우가 아니라면 모든 요청에서 기대됩니다). 네 번째 키인 `logLevel`은 단일 요청을 폐기된(deprecated) 로깅 기능의 로그 알림에 넣어 줍니다. 폐기된 클라이언트 기능을 다루는 이후 레슨이 이를 자세히 다룹니다. 필수 필드 중 하나라도 빠진 요청은 잘못된(malformed) 요청이며, 규격에 맞는 서버는 JSON-RPC 오류 `-32602`로 거부해야 하고, HTTP 전송 계층에서는 `400 Bad Request` 상태를 내야 합니다. 돌아가는 길에는 서버가 결과의 `_meta`에 `io.modelcontextprotocol/serverInfo`를 붙여서, 응답이 자신을 만들어 낸 구현체를 밝히도록 해야 합니다. `clientInfo`와 `serverInfo`는 모두 보내는 쪽이 스스로 보고하는 값이며 프로토콜이 검증하는 일은 결코 없습니다. 표시, 로깅, 디버깅을 위해 존재할 뿐이고, 이 중 하나라도 인가나 라우팅 결정에 영향을 주게 만든 서버나 게이트웨이는 예의 바른 표시 필드를 자격 증명으로 착각한 것입니다.

**그 밖의 키 몇 개는 아예 예약되어 있습니다.** 접두사 없이 실리는 `progressToken`은 요청을 진행 알림(progress notification)에 넣어 줍니다. `io.modelcontextprotocol/subscriptionId`는 `subscriptions/listen` 스트림으로 전달되는 모든 알림에 등장해서 클라이언트가 어느 구독이 그것을 만들었는지 알 수 있게 해 줍니다. 이 메커니즘은 알림과 구독을 다루는 이후 레슨이 온전히 구축합니다. 그리고 `traceparent`, `tracestate`, `baggage` 키는 접두사 규칙의 유일한 의도적 예외입니다. OpenTelemetry의 트레이스 컨텍스트 관례가 바로 그 이름 그대로의 접두사 없는 이름을 기대하기 때문에, MCP는 기존 트레이싱 도구와의 상호 운용성을 깨지 않기 위해 이름공간 접두사 없이 예약했습니다. 이 선택은 SEP-414에 문서화되어 있습니다.

**어떤 메시지도 동행 없이는 이동하지 않습니다. 아니, 동행과 함께 이동하지 않습니다.** JSON-RPC 배치 처리(batching)는 2025-06-18 개정판에서 MCP에서 제거되었고 돌아오지 않았습니다. Streamable HTTP에서는 하나의 POST 본문이 정확히 하나의 요청이나 하나의 알림을 실습니다. stdio에서는 줄바꿈으로 구분된 한 줄이 정확히 하나의 메시지를 실습니다. 클라이언트에게 요청 세 개가 밀려 있다면, 세 개짜리 배열 하나가 아니라 POST 본문 세 개를 보냅니다.

```figure
mcpa-03-envelope
```

## 인터랙티브 랩

그림의 맨 윗줄은 네 가지 모양을 나란히 놓고 각각의 존재를 가르는 필드를 보여 줍니다. 요청의 null이 아닌 id, 알림의 id 완전 부재, 결과의 resultType, 오류의 code와 message입니다. 아래쪽 절반은 하나의 `_meta` 키를 두 번 확대해서, 각각을 슬래시에서 갈라 라벨들과 이름으로 나눕니다. `io.modelcontextprotocol/protocolVersion`은 두 번째 라벨인 `modelcontextprotocol`을 강조해 예약된 이유를 보여 줍니다. `com.example.mcp/scanId`도 두 번째 라벨을 강조하지만 그 라벨은 `example`입니다. 그래서 `mcp`가 문자열 뒤쪽에 등장하더라도 아무것도 예약되지 않습니다. 강조된 두 행을 나란히 읽으면 함정이 스스로 설명됩니다. 접두사가 MCP에 속하는지는 존재 여부가 아니라 위치가 결정합니다.

## 연습 랩

`code/main.py`를 열어 보세요. 네트워크 호출도 SDK도 없고 이 레슨이 가르치는 메시지 모양만 들어 있습니다. `classify_message`는 원시 dict를 보고 `"request"`, `"notification"`, `"result"`, `"error"`, `"invalid"` 중 하나를 반환하며, 위에 설명한 id 규칙을 그대로 사용합니다. `id` 없는 `method`는 알림, 잘 형성된 id를 가진 `method`는 요청, `null` id를 가진 `method`는 어느 쪽도 아니므로 invalid로 돌아옵니다. `meta_key_status`는 키 문자열을 받아 `"reserved"`, `"free"`, `"invalid"`를 반환하며, 접두사 문법과 두 번째 라벨 규칙을 적용해 판단합니다.

```bash
python3 code/main.py
```

먼저 출력된 분류 목록을 개념 절과 대조해 읽으세요. 그다음 `run_scenario`이 짧은 교환을 진행하는 모습을 지켜 보세요. 잘 형성된 `tools/call` 요청이 complete 결과로 답변되고, 어떤 답장도 받지 못하는 `notifications/progress` 알림, 그리고 와이어 체커가 실제 트래픽이 아니라 위반으로 취급하는 세 개의 일부러 만든 실수 — 각각에 틀린 이유가 라벨로 붙어 있습니다. 하나는 절대 가져서는 안 될 id를 실은 알림입니다. 하나는 id가 `null`인 요청입니다. 하나는 `_meta`가 통째로 빠진 요청으로, 그 뒤에는 규격에 맞는 서버가 보내는 실제 `-32602` 오류가 따라옵니다. 이 오류는 잘 형성된 호출이 쓴 것과 같은 `handle_request` 함수가 만든 것입니다. 빠진 필드를 `protocolVersion` 대신 `clientCapabilities`로 바꾸고 다시 실행하면, 오류 메시지가 다른 키를 이름으로 지목하는 모습을 볼 수 있습니다.

## 제공되는 산출물

`outputs/message-shapes-reference.md`는 네 가지 메시지 모양, resultType 값들, 두 번째 라벨 테스트가 명시된 `_meta` 문법, 그리고 각 행이 브리프를 인용하는 전체 예약 키 표를 담은 한 페이지짜리 참조 자료입니다. 원시 MCP 트래픽을 읽는 동안 펼쳐 두세요. "이 모양이 유효한가", "이 키를 내가 써도 되는가"를 사양을 넘겨 보는 것보다 빠르게 답해 줍니다.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요.

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 확인합니다. 네 가지 모양이 모두 올바르게 분류되는지. null 요청 id와 id를 실은 알림이 둘 다 거부되는지. resultType 없는 결과가 표시되는지. `io.modelcontextprotocol/protocolVersion`과 `dev.mcp/anything`은 reserved로, `com.example.mcp/anything`은 free로 돌아오는지. 접두사 없는 네 예약 키가 인식되는지. 잘못된 키 이름이 invalid로 처리되는지. `protocolVersion`이 빠졌거나 `clientCapabilities`가 빠진 요청이 각각 `-32602`로 돌아오는지. 잘 형성된 요청이 정상적으로 완료되는지. 그리고 전송 기록의 모든 비랩핑(unwrapped) 결과가 resultType을 실고 있는지. 저장소의 와이어 체커는 같은 전송 기록을 2026-07-28 규칙 전체 집합에 맞춰 검증합니다. 일부러 만든 세 개의 위반이 어떻게 랩핑되는지도 포함해서요:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/03-json-rpc-and-meta
```

## 캡스톤 연결

레슨 04는 이 레슨이 정의한 봉투 위에 상태 비저장성(statelessness)을 곧바로 쌓습니다. 모든 요청이 이미 `_meta`에 자기 버전과 기능을 실고 있어서 연결에서 추론할 것이 아무것도 남지 않기 때문에, 서버는 모든 요청을 스스로 완결적인 것으로 다룰 수 있습니다. 레슨 18의 오류 분류 체계는 여러분이 이미 알고 있다고 가정합니다. `-32602`는 잘못된 `_meta`가 만들어 내는 코드이고, 오류 응답의 `data` 필드는 선택적이라는 것을요. 캡스톤의 엔드투엔드 교환은 이 레슨의 연습 랩에 있는 것과 정확히 같은 방식으로 만들어진 요청, 즉 `_meta`까지 갖춘 요청으로 열립니다. 그 첫 봉투가 틀리면 경로의 뒷부분은 아무것도 동작하지 않습니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 요청(Request) | `id`, `method`, 선택적 `params`를 가진 메시지. 정확히 하나의 답장을 기대한다 |
| 알림(Notification) | `method`와 선택적 `params`를 가지고 절대 `id`를 갖지 않는 메시지. 답장을 받지 않는다 |
| 결과 응답(Result response) | 요청 id를 되돌려 주고 resultType이 있는 `result` 객체를 실는 답장 |
| 오류 응답(Error response) | 정수 `code`와 문자열 `message`를 가진 `error` 객체를 실는 답장 |
| resultType | 이 결과가 어떤 종류인지 이름을 붙이는 필드. complete, input_required, 또는 확장 값 |
| `_meta` | 프로토콜 수준 메타데이터를 실는 속성. 점으로 구분된 선택적 접두사 + 이름으로 구성된다 |
| 예약 접두사 | 두 번째 점 구분 라벨이 `modelcontextprotocol` 또는 `mcp`인 `_meta` 접두사 |
| protocolVersion | 요청이 말하는 프로토콜 버전을 밝히는 필수 `_meta` 필드 |
| clientCapabilities | 하나의 요청과 관련된 기능을 밝히는 필수 `_meta` 필드 |
| 자기 보고 필드 | clientInfo와 serverInfo. 보내는 쪽이 제공하는 정체 정보로, 검증되지 않으며 보안 신호가 아니다 |

## 더 읽기

- [MCP 사양 2026-07-28, 베이스 프로토콜](https://modelcontextprotocol.io/specification/2026-07-28/basic), 특히 Messages와 `_meta` 일반 필드
- [SEP-414, `_meta`의 OpenTelemetry 트레이스 컨텍스트](https://modelcontextprotocol.io/seps/414-request-meta)
- [TypeScript 스키마, 모든 메시지 모양의 진짜 원천](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2026-07-28/schema.ts)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md` 2, 3절
