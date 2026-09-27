> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [client-registration-guide.md](client-registration-guide.md)

# 클라이언트 등록 가이드

MCPA '보안과 거버넌스' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## 등록 우선 순위

1. 이 인가 서버에 이미 등록돼 파일로 보관 중인 사전 등록 자격 증명.
2. Client ID Metadata Document(CIMD). 인가 서버가 `client_id_metadata_document_supported`를 광고할 때.
3. Dynamic Client Registration(DCR). 폐기됨. `registration_endpoint`가 존재하고 CIMD를 쓸 수 없을 때만.
4. 클라이언트 사용자에게 클라이언트 정보를 손으로 입력해 달라고 요청.

## 인가 서버가 CIMD에서 확인하는 것

| 검사 | 요구 사항 |
|-------|-------------|
| 스킴과 경로 | client_id는 실제 경로 구성 요소를 가진 https URL |
| 정확한 일치 | 문서 자신의 client_id 필드가 가져온 URL과 정확히 동일 |
| 필수 필드 | client_id, client_name, redirect_uris가 모두 존재 |
| 리디렉트 URI | 각각 https이거나 localhost의 http이며, 인가 요청과 일치 |
| 가져오기 안전 | SSRF 방어, HTTP 캐시 헤더 존중, localhost 전용 리디렉트에는 각별히 강한 경고 |

## DCR application_type

- `native`: 데스크톱 앱, 모바일 앱, CLI 도구, localhost로 접근하는 로컬 호스팅 앱.
- `web`: 원격의, 브라우저 기반 애플리케이션.
- 생략하면 OIDC에서 `web`이 기본이 되는데, 이 경우 localhost 리디렉트 URI를 거부할 수 있습니다.

## 인가 서버 바인딩

- 보관한 자격 증명의 키는 그것을 발행한 발급자(issuer)로 합니다.
- 인가 서버가 바뀌었음은 갱신된 보호 리소스 메타데이터를 통해 감지합니다.
- 한 인가 서버의 자격 증명을 다른 인가 서버에 재사용하지 않습니다. 대신 재등록합니다.
- CIMD id는 인가 서버를 넘나들 수 있지만 DCR id는 그렇지 않습니다.

## 혼동된 대리자(Confused deputy)

많은 다운스트림의 동적으로 등록된 클라이언트를 하나의 정적 client id로 제3자 인가 서버에 중계하는 프록시는, 그 클라이언트의 요청을 중계하기 전에 각 다운스트림 클라이언트마다 개별적으로 사용자 동의를 받아야 합니다.

## 인가 확장

| 확장 | 어울리는 곳 | 동작 방식 |
|-----------|------|---------------|
| OAuth Client Credentials | CI 파이프라인, 데몬, 백그라운드 서비스. 대화형 사용자 없음 | 클라이언트가 JWT bearer assertion(권장) 또는 클라이언트 시크릿으로 인증 |
| Enterprise-Managed Authorization | 기업 아이덴티티 제공자 뒤의 직원들 | 클라이언트가 SSO 아이덴티티 assertion을 ID-JAG로 교환하고, ID-JAG를 MCP 접근 토큰으로 교환 |

두 확장 모두 옵트인 방식이고 `clientCapabilities.extensions`에서 선언하며, 기본으로 활성화되는 일은 없습니다.

## 시험을 위해 기억하기

- Dynamic Client Registration은 폐기됐습니다. 사전 등록 다음으로 선호되는 경로는 Client ID Metadata Documents입니다.
- CIMD의 client_id는 그것을 가져온 URL과 정확히 같아야 하며, 그렇지 않으면 인가 서버가 거부해야 합니다.
- 자격 증명의 키는 발급자입니다. 인가 서버를 넘나들며 공유하는 일은 절대 없습니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 12절.
