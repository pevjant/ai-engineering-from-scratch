---
name: oauth-scope-planner
description: CIMD, 발급자 격리, 리소스 지시자, 단계적 스코프 상승을 갖춘 MCP 2026-07-28 인가를 설계한다.
version: 2.0.0
phase: 13
lesson: 16
tags: [mcp, oauth, cimd, pkce, issuer, resource-indicators]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-oauth-scope-planner.md](skill-oauth-scope-planner.md)

원격 HTTP MCP 서버와 그 도구 목록이 주어졌을 때, 완전한 인가 경계를 설계한다.

## 필요한 입력

- 캐노니컬(canonical) MCP 리소스 URI와 보호 리소스 메타데이터 위치.
- 허용된 인가 서버 발급자 목록.
- 클라이언트 런타임: native 또는 web, 정확한 리디렉션 URI 포함.
- 도구-스코프 매핑과 그에 따른 부수 작업들.
- 토큰, 리프레시, 자격 증명 저장에 관한 제약 조건.
- CIMD가 없는 구형(레거시) 인가 서버가 있다면 그 목록.

## 산출물

1. 리소스 메타데이터. RFC 9728의 `resource`, `authorization_servers`, `scopes_supported` 초안을 작성한다. well-known 세그먼트 뒤의 리소스 경로를 유지한다. 예: `https://notes.example.com/mcp`에 대해 `https://notes.example.com/.well-known/oauth-protected-resource/mcp`.
2. 발급자 정책. 정확한 허용 발급자, 메타데이터 검증, 변경 시 처리 방식, RFC 9207 `iss` 비교 방식을 명시한다.
3. 등록. 사전 등록이 가능하면 사용하고, 그렇지 않으면 클라이언트 ID 메타데이터 문서(CIMD)를 우선한다. 경로를 가진 HTTPS URL이 곧 `client_id`이며, 정확한 리디렉션 URI를 요구하고 표시용 메타데이터는 신뢰할 수 없는 것으로 다룬다. `application_type`은 여기서는 선택 사항이다.
4. DCR 폴백. 필요하다면 폐기 예정(deprecated)이라고 표시하고, `application_type`을 선언하고, 폴백을 허용하는 정확한 조건을 정의한다. 일반적인 CIMD 보안 실패 뒤에 더 약한 수준으로 격하하지 않는다.
5. 자격 증명 키. 사전 등록 및 DCR 자격 증명은 발급자를 키로, 토큰은 `(issuer, resource)`를 키로 저장한다. 발급자 간 재사용을 금지한다. 자가 호스팅 CIMD URL은 이동 가능(portable)하며, 신뢰하는 발급자가 바뀌어도 DCR 재등록이 필요 없음을 명시한다.
6. PKCE 흐름. S256, 정확한 리디렉션 URI, 인가 응답 발급자 검증, 인가 요청과 토큰 요청에 같은 `resource` 사용을 요구한다.
7. 스코프 모델. 모든 도구를 최소 스코프에 매핑한다. 현재의 `WWW-Authenticate` 스코프 챌린지를 권위 있는 기준으로 다룬다.
8. 단계적 권한 상승 경험. 추가 스코프, 사용자 설명, 동의 시점, 새 인가, 새 MCP 요청 id로 재시도하는 과정을 식별한다.
9. 리소스 서버 검사. 유효한 객체 루트 스키마, 결정적(deterministic) 순서, 결과 타입, 서버 식별 정보, 캐시 힌트를 갖춘 광고된 `tools/list`를 구현한다. 도구 디스패치 전에 발급자, 오디언스, 만료, 스코프, 현재 MCP 헤더, 요청 메타데이터를 검증한다.
10. 토큰 위생. 베어러 헤더만 사용, 쿼리 파라미터 토큰 금지, 토큰 통과(passthrough) 금지, 기밀 리프레시 저장, 로테이션 계획.
11. 에러 계약. OAuth 실패를 포함해 모든 요청 id를 JSON-RPC 에러 봉투에 보존한다. HTTP 400 `-32022` 버전 지원 검사보다 먼저 헤더 불일치에 대해 HTTP 400 `-32020`을 요구하고, 정확한 supported/requested 데이터를 담고, 알 수 없는 메서드에는 HTTP 404 `-32601`, 받아들여진 알림에는 빈 본문과 함께 202를 요구한다.
12. 전송 경계. 파싱된 본문 예제는 인프로세스 프로토콜 모델로 표시하고, JSON Content-Type과 JSON+SSE Accept 검증을 위해 레슨 09의 완전한 Streamable HTTP 어댑터에 연결한다.

## 하드 리젝트(절대 거부)

- DCR을 새 등록의 선호 메커니즘으로 제시하는 경우.
- `application_type` 없이 DCR을 쓰는 경우.
- 발급자가 바뀐 뒤 발급자가 발급한 등록 자격 증명, 액세스 토큰, 리프레시 토큰을 재사용하는 경우. 자가 호스팅 CIMD URL만이 이동 가능한 예외이지, 발급자가 발급한 시크릿이 아니다.
- 비교 전에 인가 응답의 `iss`를 정규화하는 경우.
- 인가 요청과 토큰 요청에 PKCE S256 또는 `resource`가 빠진 경우.
- 다른 오디언스용 토큰을 받아들이거나 MCP 토큰을 다운스트림으로 전달하는 경우.
- `clientInfo`, `serverInfo`, capability, 제거된 프로토콜 세션을 인증 수단으로 쓰는 경우.
- 원격 HTTP를 흉내 낸다는 이유만으로 로컬 stdio에 OAuth를 얹는 경우.
- RFC 9728 메타데이터 URL을 만들 때 보호 리소스 경로를 빠뜨리는 경우.
- MCP 요청 에러에 대해 같은 id를 가진 JSON-RPC 봉투 대신 일반 텍스트나 임의(ad hoc) 객체를 돌려주는 경우.

## 출력 형식

Resource, Issuers, Enrollment, Credential Store, PKCE Flow, Scope Matrix, Step-Up, Server Validation, Token Hygiene, Compatibility라는 이름의 섹션을 돌려준다. 마지막에 발급자 검토를 강제하는 정확한 이벤트와, 발급자가 발급한 클라이언트의 경우 재등록을 강제하는 이벤트를 명시한다.
