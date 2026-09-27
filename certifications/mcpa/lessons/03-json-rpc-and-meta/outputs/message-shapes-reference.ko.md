> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [message-shapes-reference.md](message-shapes-reference.md)

# 메시지 형태 참고 자료

MCP 2026-07-28 와이어 트래픽을 위한 한 페이지 참고 자료입니다. 네 가지 JSON-RPC 형태, resultType, `_meta` 키 규칙을 다룹니다.

## 네 가지 형태

| 형태 | `id` 있음? | `method` 있음? | 실어 보내는 것 | 응답을 받나? |
|---|---|---|---|---|
| 요청(Request) | 있음, null이 아니며 진행 중인 id들과 중복되지 않음 | 있음 | `params`(선택) | 있음, 정확히 하나 |
| 알림(Notification) | 없음, 절대로 | 있음 | `params`(선택) | 없음, 절대로 |
| 결과 응답(Result response) | 있음, 요청의 id를 그대로 돌려줌 | 없음 | `resultType`을 담은 `result` | 이것이 곧 응답 |
| 오류 응답(Error response) | 있음, 단 id를 읽을 수 없었던 경우는 제외 | 없음 | `code`와 `message`를 담은 `error` | 이것이 곧 응답 |

## `resultType` 값

| 값 | 의미 |
|---|---|
| `complete` | 결과가 최종 콘텐츠를 담고 있음 |
| `input_required` | `InputRequiredResult`임. 클라이언트가 입력을 더해 다시 시도해야 함(MRTR) |
| 값이 없음(이전 프로토콜 버전의 서버) | 클라이언트는 `complete`로 취급해야 함 |
| 인식할 수 없는 값 | 클라이언트는 결과를 잘못된 것으로 취급해야 함 |
| 확장 값(예: `task`) | 일치하는 기능(capability)이 광고된 경우에만 유효 |

## `_meta` 키 문법

- 선택적 접두사: 점으로 구분된 라벨들 뒤에 슬래시가 옵니다. 각 라벨은 문자로 시작해서 문자나 숫자로 끝나며, 중간에 하이픈이 들어갈 수 있습니다.
- 이름: 비어 있지 않다면 영숫자로 시작하고 끝나야 하고, 중간에는 하이픈, 밑줄, 점이 들어갈 수 있습니다.
- 접두사가 MCP 전용으로 예약되려면 그 두 번째(second) 라벨이 `modelcontextprotocol`이나 `mcp`여야 합니다. 판단 기준은 '존재'가 아니라 '위치'입니다.
  - 예약됨: `io.modelcontextprotocol/`, `dev.mcp/`, `org.modelcontextprotocol.api/`, `com.mcp.tools/`
  - 예약 안 됨: `com.example.mcp/`(두 번째 라벨은 `example`), `mcp.example/`(두 번째 라벨이 일치하지 않음. `mcp`는 첫 번째 라벨일 뿐)

## 예약된 `_meta` 키

| 키 | 실리는 곳 | 비고 |
|---|---|---|
| `progressToken` | 요청 | 접두사 없음. 이 요청이 진행 알림을 받도록 신청하는 표시 |
| `io.modelcontextprotocol/protocolVersion` | 요청, 필수 | 이 요청의 프로토콜 버전 |
| `io.modelcontextprotocol/clientCapabilities` | 요청, 필수 | 이 요청과 관련된 클라이언트 기능. `{}`일 수 있음 |
| `io.modelcontextprotocol/clientInfo` | 요청, 권장(should) | 클라이언트 이름과 버전. 스스로 보고한 값 |
| `io.modelcontextprotocol/logLevel` | 요청, 선택 | 폐기된 로깅 옵트인. 2026-07-28에서 여전히 유효 |
| `io.modelcontextprotocol/serverInfo` | 결과, 권장(should) | 서버 이름과 버전. 스스로 보고한 값 |
| `io.modelcontextprotocol/subscriptionId` | `subscriptions/listen` 스트림 위의 알림 | 알림을 자신의 구독과 연결 |
| `traceparent`, `tracestate`, `baggage` | 어디든 | OpenTelemetry 추적 컨텍스트. 접두사 규칙의 유일한 예외(SEP-414) |

## 거부 규칙

`_meta`에 `protocolVersion`이나 `clientCapabilities`가 빠진 요청은 잘못된 형식입니다. JSON-RPC 오류 `-32602`, HTTP에서는 `400 Bad Request`가 돌아옵니다.

## 시험을 위해 기억하기

- `clientInfo`와 `serverInfo`는 스스로 보고한 값입니다. 보안이나 라우팅 판단의 근거로 절대 쓰지 마세요.
- 예약 접두사 검사는 두 번째 라벨을 확인합니다. 첫 번째 라벨도 아니고, "문자열 어딘가에 mcp가 있는가"도 아닙니다.
- 배칭 없음: Streamable HTTP POST 바디 한 개에는 요청이나 알림 하나, stdio 한 줄에는 메시지 하나.
- 오래된 서버가 `resultType`을 빠뜨리면 `complete`로 취급합니다. 어느 서버든 인식할 수 없는 `resultType`은 잘못된 것입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 2절과 3절.
