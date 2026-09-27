> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [authorization-flow-checklist.md](authorization-flow-checklist.md)

# OAuth 인가 흐름 체크리스트

HTTP 기반 MCP 서버를 인가하기 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## 세 개의 역할

- MCP 서버: OAuth 2.1 리소스 서버. bearer 토큰을 받아들이거나 거부합니다.
- MCP 클라이언트: OAuth 2.1 클라이언트. 흐름을 이끌고 요청에 토큰을 붙입니다.
- 인가 서버: 사용자를 인증하고 토큰을 발행하는 별도의 서비스.
- stdio 서버는 이 흐름을 아예 돌리지 말아야(SHOULD NOT) 합니다. 대신 자격 증명을 환경에서 읽습니다.

## 보호 리소스 메타데이터 탐색 (401 이후)

1. `WWW-Authenticate`에서 `resource_metadata="..."`를 파싱합니다. 있으면 그 URL을 가져오고 끝냅니다.
2. 없으면 잘 알려진(well-known) URI로 순서대로 폴백합니다:
   - `https://<host>/.well-known/oauth-protected-resource<path>` (경로별)
   - `https://<host>/.well-known/oauth-protected-resource` (루트)

이 문서는 `resource`와 `authorization_servers`의 최소 한 개 항목을 알려 줍니다.

## 인가 서버 메타데이터 탐색

경로 구성 요소가 있는 발급자의 경우(`https://auth.example.com/tenant1`):

1. `https://auth.example.com/.well-known/oauth-authorization-server/tenant1`
2. `https://auth.example.com/.well-known/openid-configuration/tenant1`
3. `https://auth.example.com/tenant1/.well-known/openid-configuration`

경로가 없는 발급자의 경우(`https://auth.example.com`):

1. `https://auth.example.com/.well-known/oauth-authorization-server`
2. `https://auth.example.com/.well-known/openid-configuration`

가져온 문서의 `issuer` 필드는 URL을 만들 때 쓴 발급자 식별자와 반드시(MUST) 같아야 합니다. 그렇지 않으면 가져오기 자체가 성공했더라도 문서를 거부합니다.

## PKCE

- PKCE는 필수입니다. 기술적으로 가능한 곳에서는 `S256`을 씁니다.
- 인가 서버 메타데이터에 `code_challenge_methods_supported`가 없으면 진행을 거부하세요. PKCE 지원을 확인할 다른 방법이 없습니다.
- `code_challenge = base64url(sha256(code_verifier))`. 표준 라이브러리의 `hashlib`와 `base64`로 계산합니다.

## 리소스 인디케이터 (RFC 8707)

- 인가 요청과 토큰 요청 양쪽 모두에 `resource`를 보냅니다. 언제나, 인가 서버가 무시하더라도요.
- 값은 MCP 서버의 정규(canonical) URI입니다: 스킴과 호스트는 소문자, 프래그먼트 없음, 슬래시가 의미를 갖는 경우가 아니면 끝의 슬래시 없음.
- 예: `https://mcp.example.com/mcp`.

## iss 검증 (RFC 9207): 네 행 표

| 서버가 `authorization_response_iss_parameter_supported` 광고 | 응답의 `iss` | 클라이언트 동작 |
|---|---|---|
| true | 있음 | 기록해 둔 발급자와 정확히 비교 |
| true | 없음 | 응답 거부 |
| false 또는 없음 | 있음 | 기록해 둔 발급자와 정확히 비교 |
| false 또는 없음 | 없음 | 진행 |

리디렉트 전에 기대하는 발급자를 기록해 둡니다. 이 검사를 오류 응답에도 적용하세요.

## 토큰 사용

- 모든 HTTP 요청에 `Authorization: Bearer <token>`. 쿼리 문자열에는 절대 넣지 않습니다.
- 서버는 토큰의 audience를 자신의 정규 URI와 대조해 검증하고(MUST) 다른 것은 거부해야 합니다.
- 업스트림 API로의 토큰 전달(passthrough)은 금지입니다. 업스트림 호출에는 별도의 토큰을 쓰세요.
- 리프레시 토큰은 보장되지 않습니다. 퍼블릭 클라이언트의 리프레시 토큰은 회전(rotate)됩니다.

## 상태 코드

| 코드 | 의미 | 언제 |
|---|---|---|
| 401 | Unauthorized | 토큰 없음, 무효한 토큰, 만료된 토큰, 또는 잘못된 audience |
| 403 | Forbidden | 토큰은 유효하나 필요한 스코프(scope)가 없음 |
| 400 | Bad Request | 인가 요청 자체가 잘못된 형식 |

## 시험을 위해 기억하기

- 토큰이 없거나 무효해서 거부하는 일은 HTTP 계층에서 일어납니다. JSON-RPC 오류 바디가 없습니다.
- `S256` 지원을 광고하지 않은 PKCE는 경고가 아니라 완전한 거부입니다.
- audience가 틀린 잘 만들어진, 만료되지 않은 토큰도 여전히 401로 거부됩니다.
- 클라이언트 등록(`client_id`를 어떻게 얻는가)과 실행 중 스코프 상승은 별개의 레슨입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 12절.
