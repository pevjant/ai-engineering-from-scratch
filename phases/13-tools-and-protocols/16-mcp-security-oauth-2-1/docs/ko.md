> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# MCP 인가: CIMD, 발급자 바인딩, PKCE, 단계적 권한 상승

> 원격 MCP 요청은 상태를 저장하지 않지만, 그 인가가 익명인 것은 아닙니다. 모든 자격 증명은 그것을 만든 발급자(issuer)에, 모든 토큰은 그것을 받는 리소스에 각각 묶으세요(바인딩).

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 13 · 09(전송 방식), 페이즈 13 · 15(보안)
**소요 시간:** 약 90분

## 학습 목표

- 보호 리소스 메타데이터를 통해 인가 서버를 찾아낼 수 있다.
- 폐기 예정(deprecated)이 된 동적 클라이언트 등록(DCR)보다 클라이언트 ID 메타데이터 문서(CIMD)를 우선 사용할 수 있다.
- DCR 호환 경로를 쓸 수밖에 없을 때 올바른 `application_type`을 선언할 수 있다.
- 인가 응답의 `iss` 값을 검증하고, 발급자별로 자격 증명을 격리할 수 있다.
- PKCE, 리소스 지시자(resource indicator), 오디언스 검증, 점진적 스코프 요청을 활용할 수 있다.
- 프로토콜 세션 없이 인가된 MCP 2026-07-28 요청을 보낼 수 있다.

## 문제 상황

원격 MCP 서버는 개인 기록을 읽거나, 외부 시스템에 쓰거나, 비용이 큰 작업을 실행할 수 있습니다. 인증(authentication)은 "이 자격 증명을 누가 제시했는가"를 알려줍니다. 그다음 인가(authorization)는 아래 질문에도 답해야 합니다.

- 어떤 인가 서버가 이 자격 증명을 발급했는가?
- 이 토큰은 어떤 MCP 리소스를 위한 것인가?
- 어떤 클라이언트와 리디렉션 URI가 이 흐름을 완료했는가?
- 사용자는 어떤 작업들을 승인했는가?
- 지금 이 요청이 그 승인 범위 안에 still 들어맞는가?

2026-07-28 인가 프로파일은 클라이언트 등록과 발급자 처리를 강화했습니다. 클라이언트 ID 메타데이터 문서(CIMD)를 선호하고, 동적 클라이언트 등록(DCR)은 폐기 예정으로 분류하며, DCR을 쓸 때는 올바른 `application_type`을 요구하고, RFC 9207 발급자 응답을 검증하며, 발급자 간 자격 증명 재사용을 금지합니다.

이 규칙들은 상태 비저장(stateless) 코어를 보완하는 것입니다. 예전의 코어 핸드셰이크나 `Mcp-Session-Id`를 되돌려 놓는 것이 아닙니다.

## 개념

### 세 가지 역할을 알아두기

- **MCP 클라이언트:** 리소스 소유자를 대신해 요청을 보냅니다.
- **MCP 리소스 서버:** 액세스 토큰을 받아들이고 MCP 엔드포인트를 서빙합니다.
- **인가 서버:** 리소스 소유자를 인증하고, 동의를 받고, 토큰을 발급합니다.

리소스 서버와 인가 서버를 한 곳에서 함께 운영할 수도 있지만, 두 서버의 식별자와 검증 책임은 분리해서 관리하세요.

### 인가는 HTTP에 적용된다

MCP 인가 명세는 HTTP 기반 전송 방식에 적용됩니다. 로컬 stdio 서버는 프로세스와 운영체제의 신뢰 경계 안에서 실행됩니다. 단지 형식을 맞춘다는 이유로 stdio에 가짜 브라우저 OAuth 흐름을 얹지 마세요.

원격 Streamable HTTP에서는 모든 요청의 `Authorization` 헤더에 베어러 토큰을 담아 보냅니다. 절대 URL에 넣지 마세요.

### 보호 리소스 메타데이터에서 시작하기

리소스 서버는 RFC 9728 메타데이터를 공개합니다:

```json
{
  "resource": "https://notes.example.com/mcp",
  "authorization_servers": ["https://auth.example.com"],
  "scopes_supported": ["notes:delete", "notes:read", "notes:write"]
}
```

클라이언트는 MCP 리소스 URL에서 출발해 이 문서를 가져오고, 광고된 인가 서버 중 하나를 고른 뒤, 그 서버의 OAuth 또는 OpenID Connect 메타데이터를 가져옵니다.

RFC 9728 well-known URL을 만들 때는 리소스 경로를 유지하세요. 리소스가 `https://notes.example.com/mcp`라면, 이 레슨에서는 `https://notes.example.com/.well-known/oauth-protected-resource/mcp`를 사용합니다. `/mcp` 접미사를 빼 버리면 같은 오리진(origin)에 있는 다른 보호 리소스의 메타데이터를 집어 올 수 있습니다.

호스트명만 보고 인가 서버를 추측하지 마세요. 검증되지 않은 에러 응답 본문에서 발견한 발급자를 따라가지도 마세요. 클라이언트가 어떤 발급자들을 신뢰할지에 대한 정책을 두세요.

### 인가 서버 메타데이터 검증하기

메타데이터는 엔드포인트와 지원하는 제어 항목들을 노출해야 합니다:

```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "code_challenge_methods_supported": ["S256"],
  "authorization_response_iss_parameter_supported": true,
  "client_id_metadata_document_supported": true
}
```

PKCE에는 S256을 요구하세요. 발급자 문자열을 그대로, 정확히 기록해 두세요. 이 정확한 값이 이후 등록과 토큰 저장의 키가 됩니다.

### 등록 우선순위 따르기

클라이언트가 선택된 발급자와 이미 명시적인 관계를 맺고 있다면, 사전 등록된 클라이언트 정보를 사용하세요. 그렇지 않고 인가 서버가 지원을 광고한다면 클라이언트 ID 메타데이터 문서(CIMD)를 우선하세요. DCR은 폐기 예정인 호환성 폴백으로만 사용하고, 어느 메커니즘도 쓸 수 없을 때 비로소 클라이언트 정보를 직접 입력받으세요.

### 클라이언트 ID 메타데이터 문서 선호하기

클라이언트 ID 메타데이터 문서(CIMD)는 인가 서버에 HTTPS URL 하나를 건네줍니다. 이 URL이 곧 클라이언트 식별자이자 그 메타데이터의 위치입니다:

```json
{
  "client_id": "https://client.example.com/oauth/metadata.json",
  "client_name": "Notes desktop client",
  "application_type": "native",
  "redirect_uris": ["http://127.0.0.1:8765/callback"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"]
}
```

인가 서버가 이 문서를 가져와 검증합니다. `client_id`는 경로를 가진 HTTPS URL이어야 하고, 문서 안의 값은 그 URL과 정확히 일치해야 합니다. 필수 문서 필드는 `client_id`, `client_name`, `redirect_uris`입니다. `application_type`은 이 예제에 등장하지만 CIMD의 필수 요건은 아닙니다. 이 필드가 새로 의무화된 곳은 특별히 DCR 경로입니다.

문서를 가져오는 행위는 SSRF에 민감한 작업으로 취급하세요. 목적지를 해석하고 검증하고, 루프백·사설·링크 로컬 등 허용되지 않는 주소는 거부하고, 리디렉션과 DNS 변경 이후에 다시 확인하고, 리디렉션 횟수·바이트 수·시간을 제한하고, JSON을 요구하고, 검증된 HTTP 캐시 제어에 따라서만 캐시하세요. `client_name` 같은 표시용 필드는 신뢰할 수 없는 텍스트로 다루세요.

CIMD는 첫 접촉마다 새 동적 식별자를 만들어야 하는 수고를 없애 줍니다. 하지만 리디렉션 URI 검증, 발급자 정책, 사용자 동의까지 없애 주는 것은 아닙니다.

### DCR은 호환성 경로다

동적 클라이언트 등록(DCR)은 오래된 인가 서버를 위해 여전히 사용할 수 있지만, 새 MCP 구현에서는 폐기 예정입니다.

DCR을 사용할 때는 `application_type`을 선언하세요:

```json
{
  "client_name": "Notes desktop client",
  "application_type": "native",
  "redirect_uris": ["http://127.0.0.1:8765/callback"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"]
}
```

- 데스크톱, 모바일, 명령줄, 루프백 클라이언트는 `native`를 사용합니다.
- 원격으로 호스팅되는 브라우저 애플리케이션은 `web`과 원격 HTTPS 리디렉션을 사용합니다.

이 필드를 빠뜨리면 OpenID Connect 등록 구현에서 기본값이 `web`이 되어, 정당한 루프백 리디렉션이 실패할 수 있습니다.

DCR 코드는 명시적인 폴백 결정 뒤에 두세요. 아무 CIMD 검증 실패가 나면 조용히 폴백하는 식으로 만들지 마세요. 그렇게 하면 보안 실패를 더 약한 등록 경로로 바꿔 버릴 수 있습니다.

### 자격 증명을 발급자에 묶기

발급자가 만들어 준 등록 자료는 정확히 그 발급자를 키로 저장하세요:

```text
issuer_credentials[issuer] = pre_registered_or_dcr_client
tokens[(issuer, resource)] = access_token
```

보호 리소스 탐색 결과가 `https://auth-one.example`에서 `https://auth-two.example`로 바뀌었다면, 신뢰를 다시 평가하세요. 첫 번째 발급자의 클라이언트 시크릿, DCR 클라이언트 id, 등록 액세스 토큰, 리프레시 토큰, 액세스 토큰을 두 번째 발급자에게 절대 보내지 마세요. 사전 등록 클라이언트와 DCR 클라이언트는 새 발급자를 위해 발급된 자격 증명을 사용해야 합니다.

CIMD 클라이언트 id는 다릅니다. 그것은 인가 서버가 만들어 준 자격 증명이 아니라 자가 호스팅되는 HTTPS URL이기 때문입니다. 같은 CIMD URL은 이동 가능(portable)합니다. 새로 신뢰한 발급자가 문서를 가져와 검증하면 DCR 재등록 없이 됩니다. 다만 인가 응답과 토큰은 여전히 새 발급자 기준으로 검증하고 저장합니다.

### PKCE를 곁들인 인가 코드 흐름

대화형 흐름은 다음과 같습니다:

1. 높은 엔트로피의 `code_verifier`를 생성합니다.
2. S256 `code_challenge`를 유도합니다.
3. 정확한 `client_id`, `redirect_uri`, `scope`, `code_challenge`, `resource`를 담아 인가 요청을 보냅니다.
4. `code`를 담고 있는(그리고 제공된다면 `iss`도 담고 있는) 인가 응답을 받습니다.
5. 응답의 어떤 필드라도 사용하기 전에, 기록해 둔 정확한 발급자와 `iss`를 비교해 검증합니다.
6. `code_verifier`, 같은 리디렉션 URI, 같은 `resource`를 들고 코드를 교환합니다.
7. 결과 토큰을 `(issuer, resource)` 키로 저장합니다.

RFC 8707의 `resource` 파라미터는 인가 요청과 토큰 요청 양쪽에 모두 들어갑니다. 이 값이 캐노니컬(canonical) MCP 서버 URI를 식별합니다.

### `iss`는 정확하게 검증하기

RFC 9207은 어떤 인가 서버가 준 인가 응답이 다른 발급자의 응답과 뒤섞이는 일을 막아 줍니다.

`iss`가 있으면 기록해 둔 발급자와 비교하세요. 이때 대소문자 통합, 슬래시 덧붙이기/떼기, 기본 포트 제거, 퍼센트 인코딩 정규화 같은 건 아무것도 하지 말고 문자 그대로 비교해야 합니다. 불일치하면 코드로 아무 작업도 하지 말고, 그 응답에서 공격자가 조작한 에러 상세를 화면에 보여주는 일조차 하지 마세요.

`iss`를 포함하는 인가 서버는 `authorization_response_iss_parameter_supported: true`를 광고합니다. 현재 클라이언트들은 그 광고가 빠져 있어도, 존재하는 `iss`는 검증해야 합니다.

### MCP 서버에서 오디언스 검증하기

리소스 서버는 자기 자신을 위해 발급된 토큰만 받아들입니다:

```text
token.issuer == configured_authorization_server
token.audience == canonical_mcp_resource
```

유효하지 않거나, 만료되었거나, 발급자가 틀렸거나, 오디언스가 틀린 토큰에는 401을 돌려줍니다. MCP 서버는 다른 서비스를 위한 토큰을 받아들이거나 전달해서는 안 됩니다.

### 지금 필요한 가장 작은 스코프만 요청하기

지금 필요한 스코프에서 시작하세요. 나중에 어떤 도구가 더 많은 권한을 요구하면, 서버가 권위 있는(authoritative) 스코프 챌린지를 담아 403을 돌려줍니다:

```text
WWW-Authenticate: Bearer error="insufficient_scope",
  scope="notes:delete",
  resource_metadata="https://notes.example.com/.well-known/oauth-protected-resource/mcp"
```

클라이언트는 새 권한을 설명하고, 동의를 받고, 합쳐진 스코프 집합으로 새 인가 흐름을 수행한 뒤, 새 JSON-RPC id를 붙여 MCP 요청을 다시 시도합니다.

챌린지에 담긴 스코프가 `scopes_supported`의 부분집합이라고 가정하지 마세요. 챌린지가 현재 작업에 대한 권위 있는 기준입니다.

### 인가와 상태 비저장 MCP 와이어

인가된 도구 호출도 여전히 완전한 현재 요청 봉투(envelope)를 실어 보냅니다:

```text
POST /mcp
Authorization: Bearer <access-token>
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: notes.delete
```

```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "method": "tools/call",
  "params": {
    "name": "notes.delete",
    "arguments": {"id": "note-7"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": {
        "name": "oauth-lesson-client",
        "version": "1.0.0"
      }
    }
  }
}
```

토큰은 주체(principal)를 인가합니다. 요청 메타데이터는 프로토콜 동작을 협상합니다. 어느 한쪽이 다른 쪽을 대신할 수 없습니다.

와이어는 정해진 순서로 검증하세요: JSON-RPC와 메타데이터 타입 검사 → 헤더와 본문의 일치 여부 → 프로토콜 지원 여부. 라우팅이나 버전 헤더가 맞지 않으면 HTTP 400과 `-32020`을 돌려줍니다. 헤더와 본문이 일치하긴 하는데 지원하지 않는 버전이라면, HTTP 400과 `-32022`, 그리고 정확히 `{"supported":["2026-07-28"],"requested":"<actual>"}`인 `data`를 돌려줍니다. 알 수 없는 메서드에는 HTTP 404와 `-32601`을 돌려줍니다.

401 invalid token과 403 insufficient scope를 포함해 모든 요청 에러는 원래 요청의 `id`를 담은 JSON-RPC 에러 봉투로 돌아옵니다. 구조화된 복구 정보는 선택적인 에러 `data`에 들어가고, `WWW-Authenticate`는 HTTP 응답 헤더로 남습니다. 알림(notification)에는 `id`가 없으므로 JSON-RPC 본문도 받지 않습니다. 받아들여진 HTTP 알림은 빈 본문과 함께 202를 돌려줍니다.

서버가 `server/discover`를 구현하고 도구를 광고한다면, 의무적인 `tools/list` 메서드도 구현해야 합니다. 도구 디스크립터는 안정적인 이름, 설명, 객체 루트의 `inputSchema` 값을 가집니다. 목록은 결정적(deterministic)이며 `resultType`, 서버 식별 메타데이터, 상한이 있는 `ttlMs`, `cacheScope`를 돌려줍니다. 탐색(discovery)과 사용자에 의존하지 않는 도구 목록은 인가 전에도 제공할 수 있습니다. 둘 중 하나라도 주체에 따라 달라진다면 일반 정책과 사설 캐싱을 적용하세요.

### 토큰 통과 금지

MCP 서버는 클라이언트의 MCP 액세스 토큰을 다운스트림 API로 전달해서는 안 됩니다. 올바른 오디언스를 가진 별도의 다운스트림 토큰을 발급받거나, 명시적인 토큰 교환(token exchange) 설계를 사용하세요. 오디언스 검증은 서비스들이 남을 위해 만들어진 토큰을 거부할 때만 의미가 있습니다.

### 리프레시 토큰

리프레시 토큰은 선택 사항입니다. 발급되었다면 기밀로 저장하고 발급자와 리소스를 키로 구분하세요. 항상 존재한다고 가정하지 마세요. 인가 서버가 로테이션(순환)을 지원하면 로테이션하고, 무효화된 값의 재사용을 탐지하세요.

```figure
t3-scope-stepup
```

## 빌드하기

`code/main.py`는 인프로세스(in-process) 프로토콜 및 인가 시뮬레이터입니다. 보호 리소스 탐색, 인가 서버 메타데이터, CIMD 등록, 버전 게이트가 있는 DCR 폴백, 애플리케이션 타입 검사, PKCE, 발급자 검증, 리소스에 묶인 토큰, 스코프 단계 상승, `server/discover`, `tools/list`, 상태 비저장 도구 요청을 구현합니다.

모델은 파싱된 요청 본문과 라우팅 헤더를 받습니다. 완전한 HTTP 어댑터가 아니므로 `Content-Type`이나 `Accept`를 파싱하지 않습니다. 레슨 09의 Streamable HTTP 어댑터에 연결하세요. 그 어댑터는 `Content-Type: application/json`과 `application/json`과 `text/event-stream`을 모두 포함하는 `Accept` 값을 요구합니다.

실행 방법:

```bash
cd phases/13-tools-and-protocols/16-mcp-security-oauth-2-1
python3 code/main.py
python3 -m unittest discover code/tests -v
```

출력에는 탐색, CIMD 등록, 일반 읽기, 두 번의 별개 스코프 단계 상승, 발급자 키 기반 자격 증명 저장이 순서대로 나타납니다.

## 활용하기

시뮬레이터 객체를 프로덕션(운영 환경) 구성 요소에 대응시켜 보세요:

- `ResourceServer.protected_resource_metadata`는 RFC 9728 엔드포인트가 됩니다.
- `AuthorizationServer.metadata`는 RFC 8414 또는 OpenID Connect 탐색이 됩니다.
- `Client.enroll`은 CIMD 해석에 명시적인 DCR 호환성 분기를 더한 것이 됩니다.
- 발급자가 발급한 클라이언트 자격 증명과 `tokens_by_issuer_resource`는 암호화된 레코드가 됩니다. CIMD URL은 이동 가능한 채로 남을 수 있지만, 그 인가 결과는 여전히 발급자에 묶입니다.
- `ResourceServer.handle`은 디스패치 전에 현재 MCP 헤더, 토큰, 도구 스코프를 검증하는 미들웨어가 되며, 모든 요청 에러를 대응하는 JSON-RPC 봉투로 돌려줍니다.

## 출시하기

이 레슨은 `outputs/skill-oauth-scope-planner.md`를 출시합니다. 이 스킬은 이제 등록 우선순위, 발급자에 묶인 자격 증명 저장, 애플리케이션 타입, PKCE, 리소스 지시자, 스코프 챌린지, 그리고 현재의 상태 비저장 요청 경계를 설계합니다.

## 연습 문제

1. 리프레시 토큰 로테이션을 추가하고, 이전 리프레시 토큰의 재사용을 거부하세요.
2. 발급자 허용 목록(allowlist)을 추가하세요. 발급자가 바뀌면 이동 가능한 CIMD URL만 재사용하고, 이전 발급자가 발급한 모든 자격 증명과 토큰은 거부하세요.
3. 인가 코드에 만료 시간을 추가하고, 늦은 교환이 실패하는지 확인하세요.
4. 원격 HTTPS 리디렉션을 쓰는 웹 클라이언트 변형을 만들고, 그 DCR 메타데이터를 네이티브 클라이언트와 비교하세요.
5. 같은 발급자 아래에 두 번째 리소스를 추가하세요. 첫 번째 리소스에서 두 번째 리소스의 액세스 토큰을 쓸 수 없는지 확인하세요.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 보호 리소스 메타데이터 | 리소스와 인가 서버들을 식별하는 RFC 9728 문서 |
| CIMD | 그 URL 자체가 OAuth 클라이언트 식별자인 HTTPS 메타데이터 문서 |
| DCR | 호환성을 위해 남겨 둔, 폐기 예정인 동적 클라이언트 등록 |
| `application_type` | `native` 또는 `web`. 리디렉션 URI 규칙 검증에 사용 |
| PKCE | 가로챈 인가 코드를 보호하는 검증자(verifier)와 S256 챌린지 |
| `iss` | RFC 9207 인가 응답 발급자 식별자 |
| 리소스 지시자 | 토큰 요청을 MCP 리소스에 묶는 RFC 8707 파라미터 |
| 오디언스(Audience) | 토큰이 유효한 대상 리소스 |
| 단계적 권한 상승(Step-up) | 추가로 필요해진 현재 작업 스코프를 위한 새 동의와 토큰 발급 |
| 발급자에 묶인 자격 증명 | 정확한 인가 서버 발급자별로 격리된 등록 및 토큰 레코드 |

## 더 읽을거리

- [MCP 2026-07-28 인가 명세](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [RFC 9728: OAuth 2.0 Protected Resource Metadata](https://www.rfc-editor.org/rfc/rfc9728)
- [RFC 8707: Resource Indicators for OAuth 2.0](https://www.rfc-editor.org/rfc/rfc8707)
- [RFC 9207: OAuth 2.0 Authorization Server Issuer Identification](https://www.rfc-editor.org/rfc/rfc9207)
- [OAuth Client ID Metadata Document draft](https://datatracker.ietf.org/doc/draft-ietf-oauth-client-id-metadata-document/)
