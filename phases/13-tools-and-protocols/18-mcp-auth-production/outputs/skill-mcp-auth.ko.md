---
name: mcp-auth-wiring
description: 발급자에 묶인 등록, CIMD, 보호 리소스 메타데이터, JWKS 새로 고침, 오디언스 고정, 요청별 검증을 갖춘 MCP 2026-07-28 인가를 설계한다.
version: 2.0.0
phase: 13
lesson: 18
tags: [mcp, oauth, cimd, dcr, jwks, rfc8414, rfc7591, rfc8707, rfc7636, rfc9728, rfc9207]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mcp-auth.md](skill-mcp-auth.md)

MCP 서버 구성과 IdP capability 집합이 주어졌을 때, 프로덕션 MCP 인가 계층을 이루는 인증 표면과 거부 규칙을 출력한다.

입력:

- `mcp_resource_url` — 캐노니컬(canonical) 리소스 URL(가장 구체적인 식별자; 공동 호스팅되는 서버들을 구분할 때만 경로를 유지). `aud`로도, 보호 리소스 메타데이터의 `resource` 값으로도 쓰인다.
- `idp_metadata_url` — IdP의 `/.well-known/oauth-authorization-server`(또는 OpenID Connect Discovery) URL.
- `idp_capabilities`: `issuer`, `code_challenge_methods_supported`, `grant_types_supported`, `client_id_metadata_document_supported`, 폐기 예정인 `registration_endpoint`, `response_types_supported`, `authorization_response_iss_parameter_supported`의 관측된 값.
- `pre_registered_client_ids`: 인가 서버 운영자가 프로비저닝한 선택적 발급자-클라이언트 ID 맵. CIMD보다 이 발급자 범위의 신원을 우선하고, 폐기 예정인 DCR은 최후의 호환성 경로로만 쓴다.
- `application_type`: `native` 또는 `web`. 폐기 예정인 DCR 호환성이 선택됐을 때 필수.
- `credential_store`: 인가 서버 발급자를 키로 하는 클라이언트 ID와 등록 자격 증명. 액세스 토큰은 `(issuer, mcp_resource_url)`을 키로 한다.
- `tools`: 각각 요구하는 스코프가 붙은 MCP 도구 목록.

산출물:

1. **거부 관문.** 다음 단단한 조건 중 하나라도 실패하면 연결을 거부하고 중단한다:
   - `code_challenge_methods_supported`에 `S256`이 없음(PKCE에는 저하 모드가 없다).
   - `grant_types_supported`에 `authorization_code`가 없음.
   - `response_types_supported`가 정확히 `["code"]`가 아님.
   - 등록 경로가 존재하지 않음: 사전 등록된 `client_id`, `client_id_metadata_document_supported: true`, 폐기 예정인 DCR 호환성 엔드포인트 중 어느 것도 없음.
   - CIMD가 선택됐는데 그 `client_id`가 경로를 가진 절대 HTTPS 문서 URL이 아니거나, 문서 URL과 일치하지 않거나, 문서에 비어 있지 않은 `client_name` 또는 `redirect_uris` 배열이 없음. `application_type`은 CIMD에서 선택 사항이다.
   - 돌아온 RFC 9207 `iss`가 리디렉션 전에 기록한 발급자와 다르거나, 서버가 지원한다고 광고했는데 생략됨.
   - 폐기 예정인 DCR에 `application_type`이 없거나, 그 리디렉션 URI 정책이 `native` 또는 `web`과 충돌함.

2. **보호 리소스 메타데이터 문서**(RFC 9728) — MCP 서버용. 경로를 가진 리소스는 그 경로 앞에 well-known 세그먼트를 넣는다: `https://host/team/mcp`는 `https://host/.well-known/oauth-protected-resource/team/mcp`로 대응된다. `resource`, `authorization_servers`(발급자 허용 목록), `scopes_supported`, `bearer_methods_supported: ["header"]`를 포함한다.

3. **HTTP 엔드포인트.**
   - `GET /.well-known/oauth-protected-resource` — (2)의 문서를 돌려준다.
   - `POST /mcp`(상태 비저장 MCP 전송): 어떤 도구가 디스패치되기 전에 이 요청의 베어러 토큰을 검증한다.
   - DCR 호환성 전용: `POST /register`. 애플리케이션 타입 검사와 그 앞의 속도 제한 검사가 붙는다.

4. **백그라운드 작업 + 루틴.**
   - 예약된 JWKS 새로 고침 — `jwks_uri`를 다시 가져와 `{keys, fetched_at}` 캐시에 넣는다. 멱등(idempotent)하며 절대 키를 만들지 않는다. AS가 교체하고, 리소스 서버는 새로 고침만 한다. 기본 `0 */6 * * *`; 자주 교체하는 IdP에는 `*/15 * * * *`로 조인다.
   - `validate` 루틴 — `iss` 허용 목록, 캐시된 JWKS에 대한 서명, `aud == mcp_resource_url`, `exp`, 필요한 스코프를 검사한다.
   - 단계 상승 발급 경로 — 도구 목록에 사용자가 처음에 부여하지 않는 스코프 뒤에 게이트가 걸린 작업이 있을 때만.

5. **캐시 계획.** 받아들인 발급자마다 `issuer`를 키로 하는 항목 하나가 `{keys, fetched_at}`을 담는다. 읽기 패턴을 문서화한다: 검증기는 캐시를 읽고, `kid` 미스 시 한 번의 동기식 새로 고침으로 폴백한다(재가져오기이지 교체가 아니다 — 재가져오기는 멱등해서 키 생성 DoS로 바뀔 수 없다).

6. **스코프 매핑.** 모든 도구를 그것이 요구하는 스코프에 매핑한다. 표를 출력한다:
   `| tool | required_scope | rationale |`. 파괴적인 도구는 자기 스코프 아래로 묶는다. 읽기 스코프를 쓰기 도구에 재사용하지 않는다.

7. **런타임 거부 규칙** (검증기가 다음을 인코딩해야 한다):
   - `aud != mcp_resource_url`이면 거부 → 401 `Bearer error="invalid_token", error_description="audience mismatch", resource_metadata="<prm_url>"`.
   - `iss not in authorization_servers`이면 거부.
   - 한 번의 재가져오기 폴백 후에도 `kid`가 캐시된 JWKS에 없으면 거부.
   - 필요한 스코프가 없으면 거부 → 403 `Bearer error="insufficient_scope", scope="<required>", resource_metadata="<prm_url>"`.
   - S256 `code_challenge`가 없는 인가 요청은 거부하고, `code_verifier`, 클라이언트, 리디렉션 URI, `resource`가 일회용 인가 코드 레코드와 맞지 않는 토큰 요청도 거부한다.
   - 발급자가 자격 증명 저장소 키와 맞지 않는 자격 증명이나 토큰은 거부한다. 발급자 변경에는 새 등록이 필요하다.

하드 리젝트(절대 연결하지 않는다 — 요청을 거부하고 이유를 문서화한다):

- `client_secret`을 평문으로 저장. 공개 클라이언트는 `token_endpoint_auth_method: none`을 쓰고, 기밀 클라이언트는 `private_key_jwt`를 쓴다. 저장 시 평문 공유 시크릿도, 등록 응답 로그에도 남기지 않는다.
- 검증기에서 `aud` 검사를 건너뛰는 것. 오디언스 바인딩(액세스 토큰 권한 제한)이 RFC 8707 + RFC 9728이 존재하는 이유 그 자체다.
- JWKS 캐시 미스 폴백을 재가져오기 대신 교체-생성에 연결하는 것. 빠진 `kid`를 결국 만들어 내지 못하고, 공격자가 조작한 `kid` 값이 무한한 키 생성을 강제하게 한다. 폴백은 반드시 멱등한 새로 고침이어야 한다.
- PKCE 없는 인가 코드 요청 허용. OAuth 2.1이 금지한다. 저장된 인가 코드 레코드에 `code_challenge`가 없는 `/token` 교환은 무엇이든 검증기가 거부해야 한다.
- 새로 고침 작업 없이 JWKS를 캐시하는 것. 예약 새로 고침이 함께 출시되거나, 인증 표면은 배포되지 않는다.
- 허용 목록 없이 `iss` 클레임을 신뢰하는 것. 어떤 `iss`든 받아들이는 검증기는 공격자가 자기 IdP를 세워 토큰을 위조하게 한다.
- 인바운드 MCP 토큰을 상위 API로 전달(토큰 통과, passthrough). MCP 서버가 상위 API를 호출한다면 반드시 자기 자신만의 별도 토큰을 받아야 한다. 통과는 confused-deputy 문제를 만든다.
- `registration_access_token`을 평문으로 저장. 저장 시 해시; 매 업데이트에서 평문을 요구.
- MCP 요청 메타데이터나 제거된 프로토콜 세션을 인가 상태로 취급. 2026-07-28 전송은 상태 비저장이다. 모든 요청을 인증하고 인가한다.

출력: 보호 리소스 문서, 발급자 키 기반 등록 배치, 발급자+리소스 토큰 배치, 선택된 등록 경로, HTTP 엔드포인트, JWKS 새로 고침 작업, 스코프 매핑, 런타임 거부 규칙이 담긴 한 페이지짜리 계획. 마지막에 인가 서버의 실제 메타데이터에서 발견된 첫 번째 미충족 배포 관문을 명시한다.
