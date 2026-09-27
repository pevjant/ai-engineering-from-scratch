> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 프로덕션(운영 환경)의 MCP 인증: 발급자에 묶인 등록과 토큰

> 레슨 16은 OAuth 2.1 상태 기계를 만들었습니다. 이 레슨은 MCP 2026-07-28을 위한 프로덕션 경계를 강화합니다: 클라이언트 ID 메타데이터 문서(CIMD) 우선, 폐기 예정인 동적 등록은 호환성 목적으로만, 인가 응답 발급자 검증, 발급자 키 기반 클라이언트 자격 증명, JWKS 새로 고침, 그리고 모든 상태 비저장 요청에서 오디언스에 고정된 토큰.
>
> **명세 노트(2026-07-28):** 동적 클라이언트 등록(DCR)은 폐기 예정(deprecated)이며, 클라이언트 ID 메타데이터 문서(CIMD)로 대체됩니다. DCR은 호환성 메커니즘으로 남습니다. DCR을 사용할 때는 클라이언트가 올바른 `application_type`을 선언합니다. 클라이언트는 존재하는 RFC 9207 `iss` 값을 검증하고, 인가 서버 발급자를 넘어 자격 증명을 재사용하지 않습니다.

**유형:** Build
**언어:** Python (stdlib)
**선수 지식:** 페이즈 13 · 16(OAuth 2.1 상태 기계), 페이즈 13 · 17(게이트웨이)
**소요 시간:** 약 90분

## 학습 목표

- RFC 8414 메타데이터로 인가 서버를 탐색하고 그 계약을 검증할 수 있다.
- 클라이언트 ID 메타데이터 문서로 등록하고, 폐기 예정인 DCR을 폴백으로 격리할 수 있다.
- RFC 9207 `iss`를 검증하고, 등록을 인가 서버 발급자 키로 저장하며, 리소스에 묶인 토큰을 (발급자+리소스) 키로 저장할 수 있다.
- JWKS 키를 주기적으로 캐시하고 새로 고쳐서 키 롤오버(교체) 이후에도 서명 검증이 계속 동작하게 만들 수 있다.
- RFC 8707 리소스 지시자로 토큰을 단일 MCP 리소스에 고정하고, 혼동된 대리인(confused-deputy) 재사용을 거부할 수 있다.
- JWT 검증과 토큰 인트로스펙션 중 하나를 고르고, 폐기(revocation) 신선도를 정의하며, 신원 의존성을 사용할 수 없을 때 안전하게 실패하도록 만들 수 있다.
- 인가 서버, 리소스 서버, 클라이언트를 분리해서 각자가 자기 검증만 집행하게 만들 수 있다.
- 배포 체크리스트로 인가 서버를 감사하고, 안전하지 않은 등록이나 토큰 재사용을 거부할 수 있다.

## 문제 상황

레슨 16 시뮬레이터는 메모리 안에서 OAuth 2.1을 돌립니다. 프로덕션에는 메모리 전용 시뮬레이터가 보지 못하는 세 가지 운영 공백이 있습니다.

첫 번째 공백은 등록과 자격 증명 격리입니다. 실제 조직은 수백 개의 MCP 서버와 수천 개의 MCP 클라이언트를 운영할 수 있습니다. 2026-07-28 리비전은 **클라이언트 ID 메타데이터 문서(CIMD)**를 선호합니다. 클라이언트는 자기가 통제하는, 경로를 가진 HTTPS URL을 자기 식별자로 쓰고, 인가 서버가 그 메타데이터를 끌어 당겨 옵니다(pull). RFC 7591 동적 등록은 폐기 예정인 호환성 경로로만 남습니다. DCR을 쓸 수밖에 없을 때는 요청이 올바른 `application_type`을 선언합니다. 클라이언트는 등록을 인가 서버 발급자 키로, 액세스 토큰은 `(issuer, resource)` 쌍 키로 저장합니다. 발급자가 바뀌면 새 등록이 필요하고, 리소스가 다르면 별도로 오디언스에 묶인 토큰이 필요합니다.

두 번째 공백은 키 로테이션입니다. JWT 검증은 인가 서버의 서명 키에 의존하는데, 이 키는 JSON Web Key Set(JWKS)으로 공개됩니다. 인가 서버는 일정에 따라 이 키들을 교체합니다(보통 시간 단위, 사고 대응 중에는 더 빠르게). 부팅 때 JWKS를 한 번만 가져오는 MCP 서버는 교체 윈도우까지만 정상 동작하다가 — 그 이후로는 재시작할 때까지 모든 요청이 실패합니다. 프로덕션은 JWKS를 캐시된 값으로 연결하고, 이전 키가 만료되기 전에 캐시를 덮어쓰는 새로 고침 작업을 붙입니다. 거기에 더해, 캐시보다 새 키로 서명된 토큰이 도착하는 경우를 위한 캐시 미스 시 폴백 가져오기까지 갖춥니다.

세 번째 공백은 오디언스 바인딩입니다. 레슨 16은 RFC 8707 리소스 지시자를 소개했습니다. 프로덕션에서 이 지시자는 모든 요청에 대한 단단한 클레임 검사가 됩니다. MCP 서버는 `token.aud`를 자기 캐노니컬(canonical) 리소스 URL과 비교하고, 불일치하면 HTTP 401로 거부합니다. 이것이 상위(upstream) MCP 서버가(또는 어떤 서버를 위한 토큰을 쥔 악의적인 클라이언트가) 같은 신뢰 메시 안의 다른 서버에 그 토큰을 재생(replay)하는 것을 막는 유일한 방어입니다.

이 레슨은 각 공백을 표면의 구체적 조각에 대응시킵니다. 메타데이터 문서는 HTTP 엔드포인트입니다. JWKS 캐시 새로 고침은 예약 작업에 키-값 캐시를 더한 것입니다. JWT 검증은 리소스 서버가 어떤 도구든 디스패치하기 전에 실행하는 루틴입니다. 세 역할을 분리해 두면 각자가 자기 소유의 검증만 집행합니다: 인가 서버는 발급과 키 교체를, 리소스 서버는 캐싱과 검증을, 클라이언트는 탐색과 등록을 맡습니다.

## 범위: 레슨 16 이후의 프로덕션 집행

[레슨 16: OAuth 2.1을 활용한 MCP 보안](../../16-mcp-security-oauth-2-1/docs/en.md)이 인가 코드 상태 기계, PKCE, 보호 리소스 탐색, 리소스 지시자, 스코프 결정을 담당합니다. 이 레슨은 두 번째 OAuth 흐름을 정의하지 않습니다. 그 계약들이 이미 존재한다는 전제에서 출발해, 배포된 리소스 서버가 키 로테이션, 불투명 토큰 검증, 폐기, 의존성 실패, 롤아웃, 사고 대응 도중에도 그 계약들을 어떻게 계속 집행하는지 묻습니다.

프로덕션 경계는 더 좁고 더 운영적입니다:

- JWT 경로는 매 요청에서 고정된 발급자, 알고리즘, 서명 키, 오디언스, 시간 클레임, 스코프를 검증하면서 JWKS를 안전하게 새로 고칩니다.
- 불투명 토큰 경로는 발급자의 인증된 인트로스펙션 엔드포인트를 호출하고, 돌아온 active 상태, 오디언스 또는 리소스, 만료, 주체(subject), 스코프를 검증합니다.
- 폐기 정책은 자격 증명이 얼마나 빨리 동작을 멈춰야 하는지, 어떤 캐시가 그 사실을 지연시킬 수 있는지 정의합니다.
- 실패 정책은 탐색, JWKS, 인트로스펙션, 폐기 인프라를 쓸 수 없을 때 무슨 일이 일어나는지 결정합니다.
- 증빙(evidence)은 토큰을 저장하지 않으면서, 어떤 발급자 메타데이터와 키 셋 또는 인트로스펙션 응답, 토큰 클레임, 정책 버전, 거부 사유가 결과를 만들었는지 기록합니다.

이 구분이 레슨들을 조합 가능하게 만듭니다. 레슨 16이 흐름을 증명합니다. 레슨 18은 실제 MCP 요청 경로에 도달한 뒤에도 토큰이 계속 신뢰할 수 있는지, 아니면 거부되는지를 증명합니다.

## 개념

### RFC 8414 — OAuth 인가 서버 메타데이터

`/.well-known/oauth-authorization-server`에 있는 문서가 클라이언트에게 필요한 모든 것을 기술합니다:

```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
  "client_id_metadata_document_supported": true,
  "registration_endpoint": "https://auth.example.com/register",
  "authorization_response_iss_parameter_supported": true,
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "scopes_supported": ["mcp:tools.read", "mcp:tools.invoke"],
  "token_endpoint_auth_methods_supported": ["none", "private_key_jwt"]
}
```

MCP 리소스 URL을 받은 클라이언트는 탐색을 사슬처럼 잇습니다: RFC 9728의 `oauth-protected-resource`(리소스 서버의 문서)가 발급자를 지목하고, 이어서 `oauth-authorization-server`(이 RFC)가 모든 엔드포인트를 지목합니다. 클라이언트는 인가 URL을 절대 하드코딩하지 않습니다.

경로를 가진 리소스 식별자는 그 경로 앞에 well-known 세그먼트를 넣습니다. 예를 들어 `https://mcp.example.com/team/server`는 `https://mcp.example.com/.well-known/oauth-protected-resource/team/server`에서 보호 리소스 메타데이터를 찾습니다. 리소스 경로 뒤에 `/.well-known/...`를 덧붙이는 것은 틀렸습니다.

MCP를 위해 IdP를 신뢰하기 전에 검증할 계약:

- `code_challenge_methods_supported`에 `S256`이 포함(PKCE, RFC 7636). 명세가 명확합니다: 이 필드가 **없으면** 인가 서버가 PKCE를 지원하지 않는 것이고 클라이언트는 진행을 **거부해야(MUST)** 합니다.
- `grant_types_supported`에 `authorization_code`가 포함되고 `password`와 `implicit`은 거부합니다.
- 최소한 하나의 등록 경로가 있어야 합니다: `client_id_metadata_document_supported: true`(CIMD, 선호), 사전 등록된 클라이언트, 또는 `registration_endpoint`(폐기 예정인 RFC 7591 호환성).
- `authorization_response_iss_parameter_supported`가 true라면, 클라이언트는 돌아온 RFC 9207 `iss`를 요구하고 리디렉션 전에 기록해 둔 발급자와 정확히 비교합니다.
- OAuth 2.1에서 `response_types_supported`는 정확히 `["code"]`입니다.

`S256`이 없다면 MCP 서버는 이 IdP에 대한 배포를 거부합니다 — PKCE에는 저하 모드(degraded mode)가 없습니다. 어느 등록 경로도 광고되지 않고 사전 등록된 `client_id`도 없다면 등록 자체가 불가능합니다. 배포 매니페스트가 틀린 것이지 코드가 틀린 게 아닙니다.

### RFC 9728 (복습) — 보호 리소스 메타데이터

RFC 9728은 레슨 16에서 다뤘습니다. 프로덕션에서의 차이점: 이 문서가 *이* MCP 서버가 신뢰하는 인가 서버들을 찾으려고 클라이언트가 보는 유일한 곳입니다. 하나의 MCP 서버가 여러 IdP(직원용 하나, 파트너용 하나)의 토큰을 받아들일 수 있습니다. RFC 9728이 그 집합을 선언하고, RFC 8414 문서가 각 IdP가 무엇을 지원하는지 기술합니다.

```json
{
  "resource": "https://notes.example.com",
  "authorization_servers": ["https://auth.example.com", "https://partners.example.com"],
  "scopes_supported": ["mcp:tools.invoke"],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://notes.example.com/docs"
}
```

### 클라이언트 ID 메타데이터 문서(권장 기본값)

CIMD는 등록을 *푸시(push)*에서 *풀(pull)*로 뒤집습니다. 인가 서버에 `client_id`를 만들어 달라고 부탁하는 대신, 클라이언트는 자기가 통제하는 HTTPS URL을 **그 자체로** `client_id`로 씁니다. 그 URL은 JSON 메타데이터 문서로 연결되고, 인가 서버는 OAuth 흐름 도중 필요할 때 그 문서를 가져옵니다. 신뢰의 뿌리는 DNS입니다: 서버 운영자가 `app.example.com`을 신뢰한다면 `https://app.example.com/client.json`에서 서빙되는 클라이언트도 신뢰합니다. 등록 왕복도 없고, 고갈 걱정할 `client_id` 네임스페이스도 없고, 동기화해야 할 서버별 상태도 없습니다.

클라이언트가 호스팅하는 메타데이터 문서:

```json
{
  "client_id": "https://app.example.com/oauth/client.json",
  "client_name": "Example MCP Client",
  "client_uri": "https://app.example.com",
  "application_type": "native",
  "redirect_uris": ["http://127.0.0.1:7333/callback", "http://localhost:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none"
}
```

문서 안의 `client_id` 값은 **반드시** 그 문서가 서빙되는 URL과 같아야 합니다(인가 서버가 검증하며, 불일치는 거부됩니다). 인가 서버는 자기 RFC 8414 메타데이터에 `client_id_metadata_document_supported: true`로 지원을 광고합니다.

현재 CIMD 계약에서는 `client_id`, `client_name`, 비어 있지 않은 `redirect_uris` 배열이 필수입니다. 클라이언트 식별자는 경로를 가진 절대 HTTPS URL입니다. `application_type`은 포함할 수 있지만 CIMD의 필수 필드는 아닙니다. DCR의 `application_type` 요구 사항을 선호 경로인 CIMD에 복사해 오지 마세요.

명세가 뼈아프게 솔직하게 말하는 두 가지 보안 사실:

- **SSRF.** 인가 서버는 공격자가 제공한 URL을 가져옵니다. 서버 사이드 요청 위조(server-side request forgery)를 방어해야 합니다(내부/관리자 엔드포인트로의 가져오기 금지).
- **localhost 사칭.** CIMD만으로는 로컬 공격자가 정당한 클라이언트의 메타데이터 URL을 주장하고 아무 `localhost` 리디렉션이나 묶는 것을 막을 수 없습니다. 인가 서버는 동의 화면에서 리디렉션 URI 호스트명을 **반드시** 명확히 보여줘야(MUST) 하고, `localhost` 전용 리디렉션에는 경고를 **해야(SHOULD)** 합니다.

CIMD는 서버 측 상태가 필요 없으므로, DCR이 요구하듯 등록기(registrar)를 세워 둘 필요가 없습니다. 클라이언트 측은 읽기 전용입니다: 정적 HTTPS 엔드포인트에서 메타데이터 문서를 서빙하고, 인가 서버가 끌어 가게 두세요.

인가 서버 운영자가 이미 클라이언트 식별자를 프로비저닝해 뒀다면, 자동 등록을 시도하기 전에 그 발급자 범위의 등록을 사용하세요. 아니면 CIMD를 선호하세요. 폐기 예정인 DCR은 발급자가 사전 등록과 CIMD 둘 다 쓸 수 없을 때만 사용합니다.

### RFC 7591: 폐기 예정인 호환성 등록

DCR은 2026-07-28 리비전에서 폐기 예정입니다. CIMD를 소비할 수 없고 사전 등록이 비현실적인 인가 서버를 위해서만 유지하세요. 호환성 클라이언트는 이렇게 보냅니다:

```json
POST /register
Content-Type: application/json

{
  "application_type": "native",
  "redirect_uris": ["http://127.0.0.1:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none",
  "scope": "mcp:tools.invoke",
  "client_name": "Cursor",
  "software_id": "com.cursor.cursor",
  "software_version": "0.42.0"
}
```

서버는 나중의 업데이트를 위한 `registration_access_token`과 함께 `client_id`로 응답합니다:

```json
{
  "client_id": "c_3e7f1a",
  "client_id_issued_at": 1769472000,
  "redirect_uris": ["http://127.0.0.1:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "registration_access_token": "regt_b2...",
  "registration_client_uri": "https://auth.example.com/register/c_3e7f1a"
}
```

`application_type`은 장식이 아닙니다. 루프백 데스크톱 클라이언트는 `native`를 선언하고, 서버 호스팅 클라이언트는 `web`을 선언하고 HTTPS 리디렉션 URI를 씁니다. `token_endpoint_auth_method: none`은 공개 네이티브 클라이언트에 맞는 기본값입니다. 이런 클라이언트는 `client_id`만 받고, 소유 증명은 PKCE가 대신합니다.

프로덕션 함정 세 가지:

- 등록 엔드포인트는 반드시 소스 IP 기준으로 속도 제한을 해야 합니다. 그렇지 않으면 적대적 행위자가 수백만 건의 가짜 등록을 스크립트로 돌려 `client_id` 네임스페이스를 고갈시킵니다. 등록기가 요청을 처리하기 전에 속도 제한 검사를 돌리세요.
- `software_statement`(클라이언트를 보증하는 서명된 JWT)를 요구하는 엔터프라이즈 IdP들이 있습니다. 이 레슨의 목 구현은 건너뛰지만, 프로덕션은 검증 단계를 연결해 localhost 리디렉션 URI 외의 것에서 온 서명되지 않은 등록을 거부해야 합니다.
- `registration_access_token`은 평문이 아니라 해시로 저장해야 합니다. 이 토큰이 유출되면 공격자가 클라이언트의 리디렉션 URI를 재작성할 수 있습니다.

### RFC 8707 (복습) — 리소스 지시자

형태는 레슨 16에서 확립했습니다. 프로덕션 규칙: 모든 토큰 요청이 `resource=<canonical-mcp-url>`을 포함하고, MCP 서버는 모든 호출에서 `token.aud`가 자기 리소스 URL과 일치하는지 검증합니다. 캐노니컬 URI는 서버에 대한 *가장 구체적인* 식별자입니다: 소문자 스킴과 호스트를 쓰고, 프래그먼트가 없고, 관례상 마지막 슬래시도 없습니다. 경로 구성 요소는 규칙에 따라 벗겨지는 것이 **아닙니다** — 개별 MCP 서버를 식별하는 데 필요하면 명세가 경로를 유지합니다. `https://mcp.example.com`, `https://mcp.example.com/mcp`, `https://mcp.example.com:8443`, `https://mcp.example.com/server/mcp` 모두 유효한 캐노니컬 URI입니다. 서버당 하나를 고르고 `aud`를 정확히 그것으로 고정하세요. (이 레슨의 목 구현은 간결함을 위해 `https://notes.example.com` 같은 베어 호스트 오디언스를 씁니다. 하나의 오리진 아래 여러 MCP 서버를 함께 호스팅하는 배포는 경로로 그것들을 구분합니다.)

### RFC 7636 (복습) — PKCE

PKCE는 OAuth 2.1에서 필수입니다. 이 레슨의 인가 코드 흐름은 항상 `code_challenge`와 `code_verifier`를 실습니다. 서버는 검증자(verifier)가 없는 토큰 요청이나, 저장된 챌린지로 해시되지 않는 검증자가 붙은 요청은 거부합니다.

### MCP 2026-07-28 인가 프로파일

현재 MCP 리비전은 MCP 전송을 상태 비저장으로 만들면서 OAuth 리소스 서버 경계를 유지합니다. 신원 결정을 캐시해 둘 프로토콜 세션이 없습니다. 따라서 인가 계층은 요청 하나하나를 독립적으로 검증합니다:

- RFC 9728 보호 리소스 메타데이터를 구현하고, 그 위치를 401의 `WWW-Authenticate: Bearer resource_metadata="..."` 헤더 **또는** well-known URI `/.well-known/oauth-protected-resource`로 제공합니다(SEP-985가 헤더를 선택 사항으로 만들고 well-known 폴백을 두었습니다). 메타데이터의 `authorization_servers` 필드는 **반드시(MUST)** 최소 하나의 서버를 지목해야 합니다.
- 토큰은 **모든** 요청에서 `Authorization: Bearer ...`로만 받아들입니다 — 절대 쿼리 스트링에 넣지 않고, 절대 세션 시작 때만 검증하지 않습니다.
- 요청마다 `aud`, `iss`, `exp`, 필요한 스코프를 검증합니다. 서버는 토큰이 자기를 위해 특별히 발급되었는지(오디언스) **반드시(MUST)** 검증합니다. `aud`가 없거나 틀리면 거부하며, 와일드카드로 취급하지 않습니다.
- 401/403에서는 `error=...`와 `resource_metadata="<PRM-URL>"` 파라미터(메타데이터 문서의 URL이지, 베어 리소스가 아닙니다), 그리고 `insufficient_scope`(403)일 때 `scope="..."`를 실은 `WWW-Authenticate: Bearer`를 돌려줍니다. 주의: 파라미터는 `resource_metadata`, 즉 탐색 포인터입니다. 챌린지에는 `resource` 파라미터가 없습니다.
- 인가 서버 탐색은 RFC 8414 OAuth 메타데이터 **또는** OpenID Connect Discovery 1.0 어느 쪽이든 받아들입니다. 클라이언트는 두 well-known 접미사를 우선순위대로 모두 시도해야 합니다.
- **믹스업 공격(mix-up attack)** 방어는 클라이언트(서버가 아님)가 합니다. 클라이언트는 리디렉션 전에 기대하는 `issuer`를 기록하고, 실제 인가 응답에 돌아온 `iss` 값(RFC 9207)을 코드를 사용하기 전에 검증합니다. PKCE만으로는 믹스업을 막지 못합니다. 클라이언트가 자기 `code_verifier`를 안내받은 토큰 엔드포인트 어디든 건네주기 때문입니다.
- 클라이언트 자격 증명은 하나의 인가 서버 발급자에 속합니다. 탐색이 다른 발급자로 해석되면, 클라이언트는 기존 `client_id`, 등록 토큰, 액세스 토큰을 제시하는 대신 재등록합니다.
- CIMD가 선호되는 등록 메커니즘입니다. DCR은 폐기 예정이며, 호환성 DCR 요청도 올바른 `application_type`을 선언합니다.

OAuth 2.1 초안이 기반이고, RFC 8414/7591/8707/9728/9207 + RFC 7636 + CIMD가 표면이며, MCP 명세가 그 프로파일입니다.

### 배포 capability 체크리스트

벤더 기능 표는 빨리 낡습니다. 실제로 배포할 인가 서버가 돌려주는 메타데이터를 직접 들여다보세요. 관문은 기계적입니다:

| 검사 | 요구되는 결정 |
|---|---|
| 발견된 발급자 | 정책이 기대하는 정확한 HTTPS 발급자 |
| PKCE | `S256`이 광고됨, 아니면 중단 |
| 등록 | CIMD 선호, 사전 등록 수용, DCR은 폐기 예정 호환성으로만 |
| 인가 응답 | 존재하거나 광고되면 RFC 9207 `iss` 검증 |
| 리소스 바인딩 | 토큰 요청이 `resource`를 실음; 리소스 서버가 일치하는 `aud` 요구 |
| 자격 증명 저장 | 클라이언트 ID와 등록 자격 증명은 발급자 키, 액세스 토큰은 발급자+리소스 키 |
| DCR 호환성 | `native` 또는 `web` 선언; 선언된 애플리케이션 타입에 맞지 않는 리디렉션 URI 거부 |

제품 이름이나 가격 등급으로 지원 여부를 추측하지 마세요. 발견된 문서를 배포 증빙에 담아 두고, 필수 필드가 없으면 fail closed(거부로 실패)하세요.

### JWKS 새로 고침 패턴(인가 서버에서 교체, 리소스 서버에서 새로 고침)

두 동사를 분리해서 유지하세요. 둘을 섞는 것은 실제 프로덕션 버그입니다:

- **교체(rotate)** 는 *인가 서버*가 하는 일입니다: 새 서명 키를 만들고, JWKS에 공개하고, 나중에 이전 키를 은퇴시킵니다. 리소스 서버는 여기에 참여하지 않고 할 수도 없습니다 — IdP의 개인 키를 갖고 있지 않으니까요.
- **새로 고침(refresh)** 은 *리소스 서버*가 하는 일입니다: 공개된 JWKS를 다시 `GET`해서 캐시에 넣습니다. 리소스 서버가 JWKS에 대해 하는 행위는 이것뿐입니다.

프로덕션 실패 모드는 낡은 캐시입니다. 예약 새로 고침 작업에 키-값 캐시를 더해서 해결합니다. 리소스 서버는 고정된 간격으로 `<issuer>/.well-known/jwks.json`을 가져와 `cache[issuer] = {keys, fetched_at}`를 덮어쓰는 작업(cron, 타이머, 런타임이 주는 무엇이든)을 돌립니다. 검증기는 그 캐시에서 읽습니다. 토큰의 `kid`가 캐시에 없으면 폴백으로 **한 번의** 동기식 새로 고침을 트리거하고 다시 검사합니다. 이것은 두 경우를 한 번에 처리합니다: 예약 새로 고침, 그리고 완전히 새 키로 서명된 토큰이 다음 예약 새로 고침보다 먼저 도착하는 키 겹침(overlap) 윈도우.

폴백은 **반드시 재가져오기(re-fetch)여야 하고, 절대 교체(rotate)여서는 안 됩니다**. 캐시 미스 경로를 교체-생성(rotate-and-mint)에 연결하면 두 가지가 망가집니다: (1) 새 키를 만들어도 그 `kid`는 *여전히* 토큰과 맞지 않아 결국 조회가 실패합니다. (2) 무작위 `kid` 값을 뿌리는 공격자가 무한한 키 생성 연쇄를 강제합니다 — 스스로에게 안 셈인 DoS입니다. 재가져오기는 멱등(idempotent)하므로 가짜 `kid`의 비용은 최대 한 번의 낭비된 가져오기입니다.

캐시 형태:

```json
{
  "https://auth.example.com": {
    "keys": [
      {"kid": "k_2026_03", "kty": "RSA", "n": "...", "e": "AQAB", "alg": "RS256", "use": "sig"},
      {"kid": "k_2026_04", "kty": "RSA", "n": "...", "e": "AQAB", "alg": "RS256", "use": "sig"}
    ],
    "fetched_at": 1772668800
  }
}
```

동시에 두 개의 키가 정상 상태(steady state)입니다. 인가 서버는 이전 키(`k_2026_03`)를 은퇴시키기 전에 다음 키(`k_2026_04`)를 먼저 소개하는 방식으로 교체하므로, 이전 키로 발급된 토큰은 만료될 때까지 유효합니다. 캐시는 그 합집합을 갖고, 검증기는 `kid`로 고릅니다.

### 검증 루틴

MCP 서버는 어떤 도구든 디스패치하기 전에 검증을 돌립니다. `code/main.py`가 쓰는 형태:

```python
result = server.validate(bearer_token, required_scope="mcp:tools.invoke")
if not result["valid"]:
    return {"status": result["status"], "WWW-Authenticate": result["www_authenticate"]}
```

`validate`는 JWT를 디코딩하고, JWKS 캐시에서 서명 키를 찾고(미스면 한 번 새로 고침), 서명을 검증한 뒤, `iss`를 허용 목록과, `aud`를 이 서버의 캐노니컬 리소스와, `exp`와, 필요한 스코프와 비교합니다 — 첫 실패에서 `WWW-Authenticate` 챌린지를 돌려줍니다. 리소스 서버의 단일 루틴으로 유지하면 모든 진입점(모든 도구 호출, 모든 전송)이 같은 검사를 거칩니다. 검증 없이 도구에 도달하는 경로는 없습니다.

### 불투명 토큰은 추측이 아니라 인트로스펙션을 쓴다

모든 액세스 토큰이 JWT인 것은 아닙니다. 발급자가 불투명(opaque) 토큰을 문서화했다면, 리소스 서버는 그것을 신뢰할 만한 클레임으로 디코딩할 수 없습니다. 리소스 서버는 토큰을 인증된 백채널(backchannel)을 통해 발급자의 RFC 7662 인트로스펙션 엔드포인트로 보내고, `active: true`, 기대하는 발급자 컨텍스트, 정확한 MCP 오디언스 또는 리소스, 만료되지 않은 시간 클레임, 구체적인 도구가 요구하는 스코프를 요구합니다.

인트로스펙션은 발급자, 단방향 토큰 다이제스트, MCP 리소스를 키로 캐시하세요. 평문 토큰을 로그나 캐시 레이블로 절대 쓰지 마세요. 긍정 캐시 항목은 토큰 만료, 발급자 캐시 안내, 배포의 폐기 신선도 목표 중 가장 이른 것에 맞춰 상한을 둡니다. 부정 캐시는 새로 발급된 토큰이 거짓으로 비활성인 채로 남지 않을 만큼 짧게 유지하세요. 한 리소스에 대한 결과는 불투명 토큰 문자열이 동일하더라도 다른 리소스를 인가할 수 없습니다.

검증 모드를 공격자가 조작할 수 있는 토큰 내용물로 고르지 마세요. JWT 대 인트로스펙션 동작은 검증된 발급자 메타데이터와 배포 구성에 고정하세요. JWT 경로에서는 받아들일 알고리즘과 신뢰하는 `jwks_uri`를 고정합니다. 토큰 헤더만으로 고른 키 URL이나 알고리즘을 따라가지 않습니다.

### 폐기는 신선도 계약이다

RFC 7009는 클라이언트가 인가 서버에 토큰 폐기를 요청하게 해 줍니다. 그 요청이 모든 리소스 서버가 이미 캐시해 둔 사본을 지우지는 못합니다. 허용 가능한 최대 폐기 지연을 정의하고 모든 캐시가 그것을 지키게 하세요.

불투명 토큰 배포는 고위험 호출마다 인트로스펙션을 돌리거나 짧은 긍정 캐시를 써서 더 빠른 폐기를 달성할 수 있습니다. 자기 완결적 JWT 배포는 보통 짧은 액세스 토큰 수명에 리프레시 토큰 폐기, 발급자 전체 사고 시의 키 은퇴, 긴급 로컬 거부를 위한 선택적 주체/세션/토큰 id 거부 목록(denylist)을 조합합니다. 리소스 서버가 현재의 외부 폐기 증빙을 갖고 있지 않으면 서명된 JWT는 만료까지 암호학적으로 유효합니다.

로그아웃, 계정 비활성화, 동의 철회, 사고 대응은 서로 다른 트리거지만 하나의 측정 가능한 진술로 수렴해야 합니다: 선언된 폐기 윈도우 이내에 모든 복제본(replica)이 그 자격 증명을 거부한다. 그 진술을 따뜻한 프로세스 하나가 아니라 로드 밸런서를 통과하며 테스트하세요.

### 의존성 실패에는 선언된 결정이 필요하다

예외 처리기 안에서 가용성 정책을 즉흥적으로 만들지 마세요.

| 실패 | 안전한 프로덕션 동작 |
|---|---|
| 예약 JWKS 새로 고침이 실패했지만 알려진 `kid`가 아직 유효한 상한 캐시에 남아 있음 | 선언된 stale-on-error 윈도우 안에서만 계속하고 저하된 상태 증빙을 발행 |
| 토큰이 알 수 없는 `kid`를 갖고 허용된 한 번의 새로 고침이 실패 | 거부; 검증 불가능한 서명은 절대 수용하지 않음 |
| 인트로스펙션을 사용할 수 없음 | 보호된 호출은 fail closed; 네트워크 실패를 `active: true`로 바꾸지 않음 |
| 보호 리소스 또는 발급자 메타데이터가 예기치 않게 변경됨 | 새 등록과 토큰 획득을 중단; 상한 있는 사고 정책 아래 명시적으로 고정된, 만료되지 않은 구성만 유지 |
| 폐기 엔드포인트를 사용할 수 없음 | 로그아웃이나 폐기를 불완전하다고 보고, 가능하면 자격 증명을 로컬에서 사용 불가로 보존, 전역 폐기 성공을 주장하지 않음 |
| 시계 소스나 클레임 타입이 유효하지 않음 | 토큰이 통과할 때까지 허용 오차(skew)를 넓히는 대신 거부 |

실패를 유효하지 않은 자격 증명과 분리해서 분류하세요. 의존성 중단은 상태와 재시도 정책이 있는 운영 오류입니다. 나쁜 서명, 발급자, 오디언스, 만료, 스코프는 인가 거부입니다. 어느 쪽도 도구 핸들러에 도달하지 않고, 어느 쪽도 토큰 내용물을 감사 증빙으로 새어 흘려서는 안 됩니다.

### 오디언스 재생 워크스루(액세스 토큰 권한 제한)

서버 A(`notes.example.com`)와 서버 B(`tasks.example.com`)가 같은 인가 서버에 등록되어 있습니다. 서버 A가 침해당했습니다. 공격자는 어떤 사용자의 notes 토큰을 가져다 서버 B에 재생합니다.

서버 B의 검증기:

1. JWT를 디코딩하고, `kid`로 JWKS를 가져오고, 서명을 검증합니다.
2. `iss`를 자기 보호 리소스 메타데이터의 `authorization_servers`와 비교합니다. (통과 — 같은 IdP.)
3. `aud == "https://tasks.example.com"`을 검사합니다. (실패 — 토큰의 `aud`는 `https://notes.example.com`.)
4. `WWW-Authenticate: Bearer error="invalid_token", error_description="audience mismatch", resource_metadata="https://tasks.example.com/.well-known/oauth-protected-resource"`와 함께 401을 돌려줍니다.

오디언스 클레임이 프로토콜 계층에서 이 공격을 막는 유일한 방어입니다. 성능을 이유로 이것을 빠뜨리는 것이 가장 흔한 프로덕션 실수입니다. 검증기는 세션 시작 때만이 아니라 모든 요청에서 돌아가야 합니다. 명세는 이것을 **액세스 토큰 권한 제한(access-token privilege restriction)**이라 부릅니다. MCP 서버는 오디언스에 자기를 지목하지 않는 토큰을 **반드시(MUST)** 거부해야 합니다.

> **용어 노트.** 명세는 *confused deputy*(혼동된 대리인)라는 용어를 관련 있지만 별개인 문제에 씁니다: MCP 서버가 정적 클라이언트 ID로 OAuth **프록시** 역할을 하며 제3자 API에 토큰을 전달하는데, 클라이언트별 사용자 동의를 받지 않는 경우입니다. 오디언스 바인딩은 위의 재생을 고치고, confused-deputy 수정은 클라이언트별 동의 **더하기** 인바운드 토큰을 상위 API로 통과시키지 않는 것입니다(MCP 서버는 **반드시(MUST)** 자기 자신만의 별도 상위 토큰을 받아야 합니다).

### 믹스업 공격(서버가 대신 제공할 수 없는 클라이언트 측 방어)

클라이언트는 생애 동안 많은 인가 서버와 대화합니다. 악의적인 AS(인가 서버)는 클라이언트가 정직한 AS의 인가 코드를 공격자의 토큰 엔드포인트에서 사용하도록 유도하려 할 수 있습니다. 여기서 오디언스 바인딩은 소용없습니다 — 공격은 토큰이 존재하기 전에 일어나니까요. 방어는 클라이언트 안에 있습니다(RFC 9207):

1. 리디렉션 전에, 클라이언트는 검증된 AS 메타데이터에서 기대하는 `issuer`를 기록합니다.
2. 인가 응답에서, 클라이언트는 코드를 어디로 보내기 전에 돌아온 `iss` 파라미터를 그 기록된 발급자와 비교합니다(단순 문자열 비교, 정규화 없음).
3. 불일치(또는 AS가 `authorization_response_iss_parameter_supported`를 광고했는데 `iss`가 없음) → 거부하고, `error` 필드조차 화면에 보여주지 않습니다.

PKCE만으로는 믹스업을 막지 못합니다. 클라이언트가 자기 `code_verifier`를 안내받은 토큰 엔드포인트 어디든 건네주기 때문입니다. 명세가 발급자를 요청별로 PKCE 검증자와 `state` 옆에 기록하게 하는 이유입니다.

### 실패 모드

- **낡은 JWKS.** AS가 키를 교체한 뒤 검증기가 정당한 토큰을 거부합니다. 해결책은 위의 cron 새로 고침 + 캐시 미스 재가져오기 패턴입니다. 새로 고침 작업 없이 JWKS를 캐시하지 마세요.
- **폴백으로서의 교체.** 캐시 미스 경로를 재가져오기 대신 교체-생성에 연결하는 것은 실제 버그입니다. 빠진 `kid`를 결국 만들어 내지 못하고, 공격자가 조작한 `kid` 값을 키 생성 DoS로 바꿔 버립니다. 폴백은 반드시 멱등한 `refresh-jwks`여야 합니다.
- **빠진 `aud` 클레임.** 일부 IdP는 토큰 요청에 `resource`가 없으면 `aud`를 생략하는 것이 기본입니다. 검증기는 `aud`가 없는 토큰을 거부해야 하고, 부재를 와일드카드로 취급하면 안 됩니다.
- **`iss` 검사 누락을 통한 믹스업.** 리디렉션 전에 기록한 발급자와 RFC 9207 `iss` 인가 응답 파라미터를 검증하지 않는 클라이언트는, 정직한 AS의 코드를 공격자의 토큰 엔드포인트에서 사용하도록 유도될 수 있습니다. 이것은 클라이언트 측 실패이며, 리소스 서버가 만회할 수 없습니다.
- **스코프 업그레이드 경쟁.** 같은 사용자에 대한 두 개의 동시 단계 상승 흐름이 둘 다 성공해 스코프가 다른 두 액세스 토큰을 만들 수 있습니다. 검증기는 "그 사용자의 현재 스코프"를 찾아보지 말고 요청에 제시된 토큰을 써야 합니다 — 후자는 TOCTOU 윈도우를 만듭니다.
- **등록 토큰 절도.** 유출된 `registration_access_token`은 공격자가 리디렉션 URI를 재작성하게 해 줍니다. 저장 시 해시하고, 매 업데이트에서 클라이언트가 평문을 제시하게 하고, 의심되면 교체하세요.
- **`iss` 미고정.** 어떤 `iss`든 받아들이는 검증기는 공격자가 자기 인가 서버를 세워 대상 오디언스를 위한 클라이언트를 등록하고 토큰을 발급하게 해 줍니다. 보호 리소스 메타데이터의 `authorization_servers` 목록이 허용 목록입니다. 그것을 집행하세요.
- **자격 증명 또는 토큰 캐시 충돌.** 등록을 리소스만 키로 저장하는 클라이언트는 한 인가 서버의 신원을 다른 서버에 제시할 수 있습니다. 액세스 토큰을 발급자만 키로 저장하는 클라이언트는 잘못된 오디언스에서 토큰을 재생할 수 있습니다. 등록은 검증된 발급자 키로, 액세스 토큰은 `(issuer, resource)` 키로 저장하고, 발급자가 바뀌면 언제든 재등록하세요.

```figure
t3-jwks-rotate
```

## 활용하기

`code/main.py`는 stdlib Python과 세 역할(`AuthorizationServer`, `ResourceServer`, `Client`)로 전체 프로덕션 흐름을 걸어 보여 줍니다. 흐름:

저장소 루트에서 실행:

```bash
cd phases/13-tools-and-protocols/18-mcp-auth-production
python3 code/main.py
python3 -m unittest discover -s code/tests -v
```

첫 명령은 발급자에 묶인 등록과 토큰 검증 대화 기록을 출력합니다. 두 번째 명령은 18개 검사의 통과를 보고합니다. 어느 명령도 네트워크 리스너를 열거나 자격 증명을 쓰지 않습니다.

1. 인가 서버가 `/.well-known/oauth-authorization-server`에서 RFC 8414 메타데이터를 공개합니다.
2. MCP 클라이언트가 메타데이터 엔드포인트를 호출하고 등록 옵션(CIMD용 `client_id_metadata_document_supported`, DCR용 `registration_endpoint`)과 `S256` PKCE 지원을 검사합니다.
3. 클라이언트는 발급자 범위의 사전 등록이 있는지 확인하고, 없으면 자기 HTTPS 클라이언트 ID 메타데이터 문서로 등록합니다. 폐기 예정인 DCR은 별도로 검험 가능한 호환성 메서드로 남습니다.
4. 클라이언트는 검증된 발급자를 기록하고, S256 챌린지를 만들고, 일회용 인가 코드와 `iss`를 받아, 돌아온 발급자를 검증한 뒤, 원래 검증자와 RFC 8707 `resource` 지시자로 코드를 사용합니다.
5. MCP 클라이언트가 `Authorization: Bearer ...`로 MCP 서버의 도구를 호출합니다.
6. MCP 서버는 `validate`를 돌리고 JWKS 캐시에서 서명 키를 찾습니다.
7. IdP가 키를 교체하고, 예약 새로 고침이 JWKS를 캐시로 다시 끌어 옵니다.
8. 다음 호출은 재시작 없이 새로 고쳐진 키로 검증되고, 이전 토큰은 겹침 윈도우 동안 여전히 검증됩니다.
9. 다른 MCP 리소스에 대한 오디언스 재생 시도는 `audience mismatch`와 `resource_metadata` 포인터와 함께 401을 받습니다.

여기서의 JWT는 공유 시크릿과 함께 HS256을 씁니다(레슨이 stdlib만으로 돌아가게 하기 위함입니다). 프로덕션은 위의 JWKS 패턴과 함께 RS256이나 EdDSA를 씁니다. 그 외의 검증 로직은 동일합니다. IdP와 리소스 서버가 한 프로세스 안에 있으므로 `refresh_jwks`는 인가 서버의 키 목록을 직접 읽습니다. 실제 와이어에서는 `jwks_uri`로의 HTTP `GET`입니다.

## 출시하기

이 레슨은 `outputs/skill-mcp-auth.md`를 산출합니다. MCP 서버 구성과 IdP capability 집합이 주어지면, 이 스킬은 세워야 할 인증 표면을 출력합니다 — 보호 리소스 메타데이터, 사용할 등록 경로(CIMD, 사전 등록, 또는 DCR 폴백), JWKS 새로 고침 일정, 스코프 매핑, IdP가 전체 RFC 프로파일을 지원하지 않을 때 적용할 거부 규칙들.

## 연습 문제

1. `code/main.py`를 실행하고 흐름을 추적하세요. 6단계에서 IdP가 키를 교체하고, 예약된 `refresh_jwks`가 공개된 셋을 다시 끌어 오고, 이전 토큰(겹침 윈도우)과 새 토큰 둘 다 재시작 없이 검증된다는 점을 확인하세요.

2. 보호 리소스 메타데이터의 `authorization_servers` 목록에 새 IdP를 추가하세요. 새 IdP가 서명한 토큰을 발급해 검증기가 받아들이는지 확인하세요. 목록에 없는 IdP가 서명한 토큰을 발급해 검증기가 `WWW-Authenticate: Bearer error="invalid_token", error_description="iss not allowed"`로 거부하는지 확인하세요.

3. 등록기가 요청을 수용하기 전에 돌아가는 속도 제한 검사를 `register_client`에 추가하세요. IP를 키로 하는 작은 딕셔너리에 소스 IP별 토큰 버킷을 담아 쓰세요.

4. RFC 7591을 읽고 이 레슨의 `/register` 핸들러가 검증하지 않는 두 필드를 찾으세요. 검증을 추가하세요. (힌트: `software_statement`와 `redirect_uris`의 URI 스킴.)

5. 두 번째 인가 서버를 추가하세요. 클라이언트가 별도의 발급자 키 기반 등록을 저장하고, 첫 발급자의 토큰이나 `client_id`를 재사용하는 것을 거부하는지 확인하세요.

6. DoS 수정을 증명하세요. 무작위 `kid`를 가진 토큰을 검증기에 보내고 `refresh_jwks`가 최대 한 번만 돌고 인가 서버의 키 개수가 늘지 않는지 확인하세요. 그다음 일부러 폴백을 교체-생성으로 다시 연결하고 가짜 토큰마다 키 개수가 치솟는지 보세요 — 그 후 재가져오기로 복원하세요.

7. 폐기 예정인 DCR을 `native`와 `web` 클라이언트 둘 다로 실습하세요. HTTP 리디렉션 URI를 가진 web 클라이언트와 정확한 루프백 리디렉션이 없는 native 클라이언트가 거부되는지 확인하세요.

## 핵심 용어

| 용어 | 사람들이 부르는 이름 | 실제 의미 |
|------|----------------|------------------------|
| ASM | "OAuth 메타데이터 문서" | RFC 8414 `/.well-known/oauth-authorization-server` JSON |
| CIMD | "클라이언트 메타데이터 URL" | 클라이언트 ID 메타데이터 문서: `client_id`로 쓰이는 HTTPS URL; AS가 JSON을 끌어 옴. MCP 2026-07-28의 선호 등록 방식 |
| DCR | "셀프서비스 클라이언트 등록" | RFC 7591 `POST /register`; 현재 MCP에서는 폐기 예정이며 호환성을 위해서만 유지 |
| JWKS | "JWT 검증용 공개 키" | JSON Web Key Set. `jwks_uri`에서 가져오며 `kid`로 색인 |
| 교체 vs 새로 고침 | "키 업데이트" | *교체(rotate)* = AS가 서명 키를 만들고/은퇴시킴; *새로 고침(refresh)* = 리소스 서버가 공개된 셋을 다시 가져옴. 리소스 서버는 새로 고침만 함 |
| 리소스 지시자 | "오디언스 파라미터" | 토큰을 한 서버에 고정하는 RFC 8707 `resource` 파라미터 |
| `aud` 클레임 | "오디언스" | 검증기가 캐노니컬 리소스 URL과 비교하는 JWT 클레임 |
| 오디언스 재생 | "토큰 재생" | 서버 A를 위해 발급된 토큰을 서버 B에 제시; 오디언스 검증이 방어 (명세: 액세스 토큰 권한 제한) |
| Confused deputy | "프록시 토큰 오용" | 정적 클라이언트 ID를 가진 MCP 프록시가 클라이언트별 동의 없이 토큰을 전달; 오디언스 재생과는 별개 |
| 믹스업 공격 | "잘못된 토큰 엔드포인트" | 클라이언트가 정직한 AS의 코드를 공격자의 엔드포인트에서 사용하도록 유도됨; RFC 9207 `iss`로 클라이언트 측 방어 |
| `iss` 허용 목록 | "신뢰하는 인가 서버들" | 보호 리소스 메타데이터의 `authorization_servers`에 지목된 집합 |
| `resource_metadata` | "PRM 문서 위치" | 401/403에서 RFC 9728 메타데이터 URL을 지목하는 `WWW-Authenticate` 파라미터 |
| 공개 클라이언트 | "네이티브 또는 브라우저 클라이언트" | `client_secret`이 없는 OAuth 클라이언트; PKCE가 보완 |
| `WWW-Authenticate` | "401/403 응답 헤더" | 클라이언트 복구를 이끄는 `Bearer error=...` 지시문을 실음 |

## 더 읽을거리

- [MCP 인가 명세(2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) - 현재 MCP 인가 프로파일
- [MCP 2026-07-28 체인지로그](https://modelcontextprotocol.io/specification/2026-07-28/changelog) - CIMD, 발급자 검증, DCR 폐기 예정화, 발급자 키 기반 자격 증명 변경
- [OAuth Client ID Metadata Document (draft-ietf-oauth-client-id-metadata-document-00)](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-client-id-metadata-document-00) — CIMD
- [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414) — 탐색 계약
- [RFC 7591 — OAuth 2.0 Dynamic Client Registration Protocol](https://datatracker.ietf.org/doc/html/rfc7591) — DCR (폴백 경로)
- [RFC 7636 — Proof Key for Code Exchange (PKCE)](https://datatracker.ietf.org/doc/html/rfc7636) — 공개 클라이언트의 소유 증명
- [RFC 8707 — Resource Indicators for OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc8707) — 오디언스 고정
- [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728) — 리소스 서버 탐색
- [RFC 9207 — OAuth 2.0 Authorization Server Issuer Identification](https://datatracker.ietf.org/doc/html/rfc9207) — 믹스업 공격을 막는 `iss` 파라미터
- [RFC 7662: OAuth 2.0 Token Introspection](https://datatracker.ietf.org/doc/html/rfc7662)
- [RFC 7009: OAuth 2.0 Token Revocation](https://datatracker.ietf.org/doc/html/rfc7009)
