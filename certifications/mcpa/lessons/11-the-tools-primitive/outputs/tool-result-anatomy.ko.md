> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [tool-result-anatomy.md](tool-result-anatomy.md)

# 도구 결과 해부도

MCPA '상호작용과 실행' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## tools/list 한눈에 보기

| 필드 | 위치 | 의미 |
|-------|-------|---------|
| `cursor` | 요청, 선택 | 이전 페이지가 준 불투명한(opaque) 토큰. 첫 요청에서는 생략 |
| `tools` | result | 이 페이지의 도구 정의들 |
| `nextCursor` | result, 선택 | 남은 도구가 더 있으면, 빈 문자열이더라도, 존재함 |
| `ttlMs` | result, 필수 | 밀리초 단위 신선도 힌트. 클라이언트는 이 시간이 지나기 전까지 캐시 가능 |
| `cacheScope` | result, 필수 | `public`(공유 가능) 또는 `private`(이 인가 컨텍스트 안에서만) |

도구 목록은 연결마다 달라지거나 다른 요청의 부수 효과로 달라져서는 안 됩니다. 요청 자신이 실어 온 인가(authorization)에 따라 달라지는 것은 허용됩니다.

## tools/call과 CallToolResult

| 필드 | 필수 여부 | 의미 |
|-------|----------|---------|
| `content` | 예 | 콘텐츠 블록 목록. 생략 불가, 비어 있을 수는 있음 |
| `structuredContent` | 아니요 | 어떤 JSON 값이든. outputSchema가 있다면 그에 맞아야 함 |
| `isError` | 아니요 | 없거나 false면 성공. true면 모델이 읽고 고칠 수 있는 도구 실행 오류 |

## 콘텐츠 블록 카탈로그

| 블록 타입 | 필수 필드 | 용도 |
|------------|------------------|----------|
| `text` | `text` | 평범한 자연어 출력 |
| `image` | `data`(base64), `mimeType` | 사용자에게 보여 줄 그림 |
| `audio` | `data`(base64), `mimeType` | 말소리나 소리 출력 |
| `resource_link` | `uri`, `name` | 리소스 내용을 직접 넣지 않고 가리키기만 할 때 |
| `resource` | `uri`, `mimeType`, 그리고 `text` 또는 `blob`을 가진 `resource` 객체 | 리소스 내용을 직접 끼워 넣기 |

어떤 블록이든 `annotations`를 가질 수 있습니다: `audience`(`user`, `assistant`, 또는 둘 다), `priority`(0에서 1), `lastModified`. 이것들은 블록의 다른 필드 옆에, `data`나 `resource`와 형제로 놓입니다. 한 단계 더 안쪽으로 중첩되는 일은 없습니다.

## 도구 어노테이션 기본값

| 어노테이션 | 기본값 | 비고 |
|------------|---------|------|
| `readOnlyHint` | false | true면 이 도구는 환경을 절대 수정하지 않는다는 뜻 |
| `destructiveHint` | true | `readOnlyHint`가 false일 때만 의미가 있음 |
| `idempotentHint` | false | true면 같은 인자로 반복 호출해도 새로운 일이 생기지 않는다는 뜻 |
| `openWorldHint` | true | false면 도구의 상호작용 범위가 닫혀 있다는 뜻 |

네 가지 모두 보장이 아니라 힌트입니다. 서버 자체를 신뢰하지 않는 한 신뢰하지 않는 값으로 취급하고, 어노테이션 하나만으로 안전 판단을 하지 마세요.

## 도구 호출의 두 오류 채널

| 상황 | 채널 | 예 |
|-----------|---------|---------|
| 지목된 도구가 존재하지 않음 | JSON-RPC 오류 | `-32602` |
| 도구는 실행됐는데 모델이 고칠 수 있는 문제에 부딪힘 | `isError: true`를 담은 결과 | 잘못된 날짜, 범위를 벗어난 값 |

## listChanged 한 줄 요약

클라이언트가 `toolsListChanged: true`로 `subscriptions/listen`을 열면 먼저 `notifications/subscriptions/acknowledged`를 받고, 이후 도구 집합이 바뀔 때마다 그 스트림의 구독 id가 붙은 `notifications/tools/list_changed`를 받아, 평범한 `tools/list`로 다시 가져옵니다.

## 시험을 위해 기억하기

- 더 페이징할지는 `nextCursor`의 진실성(truthiness)이 아니라 존재 여부로 판단합니다. 빈 문자열도 유효한 커서 값입니다.
- 도구 어노테이션은 의도를 묘사하지 강제가 아닙니다. 콘텐츠 어노테이션은 도구 전체가 아니라 그 하나의 블록을 묘사합니다.
- `isError`는 프로토콜 수준 오류가 아니라 모델을 위한 정상적인 결과 데이터입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 10절.
