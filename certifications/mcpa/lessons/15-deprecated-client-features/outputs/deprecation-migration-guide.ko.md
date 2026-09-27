> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [deprecation-migration-guide.md](deprecation-migration-guide.md)

# 폐기된 클라이언트 기능 마이그레이션 가이드

MCPA '상호작용과 실행' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## Deprecated의 의미

- Active: 완전히 명세됐고 현재 리비전이 요구하는 상태.
- Deprecated: 여전히 완전히 명세돼 있고 완전히 동작하는 상태. 문서화된 마이그레이션 경로가 있고, 제거 후보가 되기 전에 최소 12개월의 기간(폐기시킨 리비전의 출시부터 계산)이 있습니다.
- Removed: 초안 명세에서 삭제돼 다음 Current 리비전에는 없는 상태.
- 가장 이른 제거 시점은 그 기간이 끝난 날짜 이후에 Current로 출시되는 첫 번째 리비전입니다. 실제 제거 날짜는 별개의 Core Maintainer 결정이며 더 늦어질 수 있습니다.

## SEP-2577이 폐기한 클라이언트 대면 기능 셋

| 기능 | 하던 일 | 마이그레이션 경로 | 가장 이른 제거 |
|---|---|---|---|
| Roots | 클라이언트가 서버에 디렉터리 힌트를 참고용 안내로 건네줌 | 도구 매개변수, 리소스 URI, 서버 설정으로 디렉터리나 파일 전달 | 2027-07-28 이후 첫 리비전 |
| Sampling | 서버가 클라이언트에게 LLM 생성을 대신 실행해 달라고 요청 | LLM 제공자 API와 직접 통합 | 2027-07-28 이후 첫 리비전 |
| Logging | 서버가 클라이언트에 구조화된 로그 알림을 보냄 | stdio 전송에서는 stderr로 기록, 관측 가능성이 필요하면 OpenTelemetry 사용 | 2027-07-28 이후 첫 리비전 |

## 폐기 레지스트리에 있는 그 밖의 항목

| 기능 | 폐기된 리비전 | 마이그레이션 경로 | 가장 이른 제거 |
|---|---|---|---|
| Dynamic Client Registration | 2026-07-28 | Client ID Metadata Documents | 2027-07-28 이후 첫 리비전 |
| `includeContext: "thisServer" / "allServers"` | 2025-11-25 | 필드 생략, 또는 `"none"` 전송(기본값) | Sampling을 따름 |
| HTTP+SSE 전송 | 2025-03-26 | Streamable HTTP | SEP-2596이 Final에 도달한 지 3개월 후 |

## 여전히 유효하고 지금도 와이어에 오르는 것들 (이것들을 legacy로 포장하지 마세요)

- MRTR `inputRequests` 항목으로서의 `roots/list`. 클라이언트가 `roots` 기능을 선언해야 통과합니다.
- MRTR `inputRequests` 항목으로서의 `sampling/createMessage`. 클라이언트가 `sampling` 기능을 선언해야 통과합니다.
- `_meta` 안의 요청별 `io.modelcontextprotocol/logLevel` 키. 그 요청 자신의 응답 스트림 위에서, 요청된 레벨 이상의 `notifications/message`로, 그 요청이 진행 중인 동안에만 답합니다.

## 2026-07-28에서 실제로 제거된 것 (따로 또 다른, 더 짧은 목록)

- `initialize`와 `notifications/initialized`
- `Mcp-Session-Id`와 Streamable HTTP GET·DELETE 세션 엔드포인트
- `resources/subscribe`와 `resources/unsubscribe`(`subscriptions/listen` 사용)
- `ping`
- `logging/setLevel`(연결 전체 로그 레벨 설정자. 레벨을 담아 둘 세션이 남아 있지 않음)
- `notifications/roots/list_changed`
- `Last-Event-ID`와 SSE 재개(resumability)
- MRTR 밖의 서버가 먼저 시작하는 어떤 요청이든
- `tasks/result`와 `tasks/list`(tasks는 `io.modelcontextprotocol/tasks` 확장으로 이동)
- `notifications/elicitation/complete`와 URL 모드 `elicitationId` 필드
- 오류 코드 `-32002`와 `-32042`

## 시험을 위해 기억하기

- Deprecated는 Removed가 아닙니다. 오늘 완전히 동작하면서 나중의 제거 일정에 올라 있는 상태가 동시에 가능합니다.
- `roots/list`, `sampling/createMessage`, 요청별 `logLevel`은 포장을 벗기면 모두 2026-07-28 와이어 검사기를 통과합니다.
- `logging/setLevel`과 `notifications/roots/list_changed`는 2026-07-28에 존재하지 않습니다.
- 정확한 제거 날짜("이후 첫 리비전"이 아니라)를 지목하는 선지는 그 기간을 잘못 묘사하고 있는 것입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 11절과 15절.
