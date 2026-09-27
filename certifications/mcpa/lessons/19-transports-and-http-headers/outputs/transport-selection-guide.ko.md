> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [transport-selection-guide.md](transport-selection-guide.md)

# 전송 방식 선택 가이드

MCPA '상호작용과 실행' 및 '아키텍처와 구성 요소' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## 전송 방식 고르기

| 상황 | 사용 | 이유 |
|---|---|---|
| 클라이언트가 서버를 실행하고 그 수명 주기를 소유함(로컬 도구, IDE 확장) | stdio | 가장 단순한 프레이밍, 네트워크 노출 없음, 자격 증명은 환경에서 읽음 |
| 서버가 네트워크 너머 많은 클라이언트에게 도달 가능함 | Streamable HTTP | 엔드포인트 하나, 독립적인 POST들, 로드 밸런서와 게이트웨이 뒤에서도 동작 |
| 서브프로세스도 HTTP도 아닌 신뢰할 수 있는 바이트 스트림(유닉스 소켓, TCP 연결) | stdio 프레이밍 재사용 | stdio 바인딩은 이미 스트림 위의 줄바꿈 구분 JSON-RPC임. 실행 방식, `stderr`, 종료 절차만 서브프로세스 고유의 것 |
| 2026-07-28 이전의 낡은 클라이언트나 서버 | 먼저 시대를 탐지(레슨 05)한 뒤 폴백 | 절대 가정하지 않기. 서버 프로세스나 오리진별로 탐지하고 판단을 캐시 |

## stdio 한눈에 보기

- 줄바꿈으로 구분된 JSON-RPC. 한 줄에 메시지 하나, 안에 줄바꿈 포함 불가.
- `stdout`은 MCP 메시지만 실어 옮깁니다. 서버가 거기에 요청을 쓰는 일은 없습니다.
- `stderr`는 어떤 심각도의 로그든 갈 곳입니다. 클라이언트가 그것만으로 오류 신호로 취급해서는 안 됩니다.
- 헤더 계층이 전혀 없습니다. 버전, 기능(capabilities), 식별 정보는 오직 `_meta`에만 삽니다.
- 취소는 `notifications/cancelled`로 합니다. 종료는 `stdin`을 닫는 방식이고, 필요하면 단계를 올립니다.
- 예기치 못한 종료 시: 재시작하고, 진행 중인 요청들은 잃고, `subscriptions/listen`을 다시 보냅니다.

## Streamable HTTP 필수 헤더

| 헤더 | 원래 필드 | 필요한 요청 | 불일치 시 |
|---|---|---|---|
| `MCP-Protocol-Version` | `params._meta["io.modelcontextprotocol/protocolVersion"]` | 모든 POST | `400` + `-32020` |
| `Mcp-Method` | `method` | 모든 요청 | `400` + `-32020` |
| `Mcp-Name` | `params.name`, 또는 `resources/read`의 `params.uri` | `tools/call`, `resources/read`, `prompts/get` | `400` + `-32020` |
| `Mcp-Param-{Name}` | 스키마에서 `x-mcp-header` 표시된 도구 인자 | 그것을 선언한 도구만 | `400` + `-32020` |

헤더 이름은 대소문자를 구분하지 않습니다. 메서드 이름과 도구 이름을 포함한 헤더 값은 대소문자를 구분합니다.

## Base64 센티넬(sentinel) 인코딩

`Mcp-Name`과 모든 `Mcp-Param-{Name}` 값에 적용됩니다. 값이 다음에 해당하면 `=?base64?{Base64EncodedValue}?=`로 인코딩합니다:

- 눈에 보이는 ASCII, 공백, 가로 탭 밖의 문자를 포함할 때,
- 앞이나 뒤에 공백 문자가 있을 때, 또는
- 이미 스스로 센티넬 패턴과 일치할 때(모호함을 피하기 위해).

그 외의 경우 값은 그대로 보냅니다. 서버는 헤더와 바디를 비교하기 전에 센티넬을 디코딩합니다.

## JSON-RPC 오류가 아닌 HTTP 상태 코드

| 상황 | 상태 | JSON-RPC 바디 |
|---|---|---|
| MCP 엔드포인트로의 GET 또는 DELETE | `405` | 필요 없음 |
| `Origin` 헤더가 있으나 허용되지 않음 | `403` | 필요 없음 |
| 수락된 알림 POST | `202` | 없음. 알림은 JSON-RPC 응답을 절대 받지 않음 |
| 헤더가 바디와 불일치 | `400` | `-32020` `HeaderMismatch` |
| 지원되지 않는 프로토콜 버전 | `400` | `-32022` `UnsupportedProtocolVersionError` |
| 모르는 메서드 | `404` | `-32601` `Method not found` |

## 2026-07-28이 Streamable HTTP에서 제거한 것

- 독립적인 GET 스트림과 그 `endpoint` 이벤트.
- `Mcp-Session-Id`와 세션 범위 상태. 모든 요청은 스스로를 설명합니다.
- 세션을 끝내기 위한 HTTP DELETE.
- `Last-Event-ID`를 통한 스트림 재개. 끊긴 스트림은 그 요청을 잃으며, 안전하다면 새 id로 재발행합니다.

## 시험을 위해 기억하기

- 바디가 언제나 진짜 원본(source of truth)입니다. 헤더는 라우팅을 위해 존재할 뿐, 두 번째 권위가 되는 일은 없습니다.
- 나쁜 Origin에 대한 `403`, GET이나 DELETE에 대한 `405`, 수락된 알림에 대한 `202`는 HTTP 수준의 결과입니다. JSON-RPC 결과도 오류도 아닙니다.
- `-32020`은 `HeaderMismatch`입니다. `-32021`(빠진 기능)이나 `-32022`(지원 안 하는 버전)와는 무관합니다.
- 바이트 스트림 위의 커스텀 전송은 새 프레이밍을 발명하는 대신 stdio 프레이밍을 재사용합니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 9절.
