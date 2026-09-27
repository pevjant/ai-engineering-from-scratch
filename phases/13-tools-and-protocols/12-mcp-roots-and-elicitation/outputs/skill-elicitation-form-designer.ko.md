---
name: elicitation-form-designer
description: 권한 부여, 안전한 폼, 서명된 재시도 상태를 갖춘 명시적 리소스 범위와 상태 없는 MCP 2026-07-28 일론(elicitation)을 설계합니다.
version: 2.0.0
phase: 13
lesson: 12
tags: [mcp, elicitation, mrtr, scope, authorization]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-elicitation-form-designer.md](skill-elicitation-form-designer.md)

프로토콜 리비전 `2026-07-28`을 대상으로 하는 MCP 연산의 사용자 입력 단계를 설계하세요.

다음을 산출합니다:

1. 범위 계약. 워크스페이스, 디렉터리 또는 리소스 URI를 눈에 보이는 도구 인자나 서버 설정에 넣습니다. 어떤 인증된 주체들이 쓸 수 있는지 명시합니다.
2. 경계 검사. URI 정규화, 경로 구성 요소 포함(containment) 검사, 심볼릭 링크 정책, 운영체제 샌드박스를 정의합니다.
3. 트리거 조건. 사용자 입력을 요구하는 정확한 모호성, 확인, 외부 상호작용을 명시합니다.
4. 디스커버리와 역량 게이트. `server/discover`에서 정확한 `supportedVersions`, 역량, `ttlMs`, `cacheScope`를 돌려줍니다. 도구를 광고한다면 유효한 객체형 `inputSchema`, 서버 식별 메타데이터, 캐시 힌트를 갖춘 필수·결정론적 `tools/list` 디스크립터를 포함합니다. `elicitation: {}`과 명시적 `elicitation.form`을 폼 지원으로 취급합니다. 누락되었거나 URL 전용인 지원은 `-32021`과 `data.requiredCapabilities.elicitation.form`으로 거부하고, 미지원 버전에는 정확한 `supported`·`requested` 데이터와 함께 `-32022`를 사용합니다.
5. MRTR 결과. 안정적인 `inputRequests` 키와 `elicitation/create` 요청을 담은 `resultType: "input_required"`를 돌려줍니다.
6. 상호작용 설계. 폼 모드는 평범한 메시지와 제한된 평평한(flat) 스키마를 제공합니다. URL 모드는 HTTPS 목적지와 대역 외 완료 규칙을 보여 줍니다.
7. 재시도 계약. 새 JSON-RPC id, 원래 메서드와 인자, 이번 라운드의 `inputResponses`, 요청별 `_meta`, 정확한 `requestState` 에코를 요구합니다.
   id 없는 알림은 JSON-RPC 결과나 오류를 절대 받지 않습니다. 수락된 Streamable HTTP 알림은 본문 없는 `202`를 받습니다.
8. 분기 처리. `accept`, `decline`, `cancel`을 서로 다른 안전한 결과로 매핑합니다.
9. 상태 보호. HMAC 또는 인증된 암호화를 인증된 주체, 원래 인자 다이제스트, 후보 집합, 연산 페이즈, 만료, 1회용 논스(nonce)에 묶습니다. 모든 핸들러 인스턴스가 공유하는 유계·TTL 정리 재생 저장소에서 논스를 원자적으로 소비합니다.
10. 최종 재검증. 변경(mutation) 직전에 권한, 살아있는 레코드 상태, 포함 검사를 다시 수행합니다.

하드 리젝(필수 반려 사항):

- 폐기된 루츠를 권한 부여, 포함 검사, 샌드박싱처럼 다루는 것.
- 새 2026-07-28 설계에서 `roots/list`나 `notifications/roots/list_changed`를 쓰는 것.
- MRTR을 통해 돌려주는 대신 역방향 `elicitation/create` 요청을 보내는 것.
- 폼 모드에서 비밀번호, API 키, 접근 토큰, 결제 자격 증명을 수집하는 것.
- 현재 요청별 역량에 없는 일론 모드를 보내는 것.
- `clientInfo`를 인증된 사용자 신원처럼 다루는 것.
- 검증된 수락과 최종 권한 검사보다 파괴적 동작이 먼저 실행되는 것.
- 후보나 권한 관련 데이터를 실은, 서명되지 않은 `requestState`.

거부 규칙:

- 명시적 거절 이후의 반복 프롬프트는 거부합니다.
- 서버가 사용자 없이 도출하거나 검증할 수 있는 값에 대한 일론은 거부합니다.
- 자격 증명, 사용자 비밀값, 사전 인증된 베어러(bearer) 값이 들어 있는 URL은 거부합니다.
- 숨겨진 프로토콜 세션 상태, `initialize`, `Mcp-Session-Id`를 쓰는 요청은 거부합니다.

범위, 권한 부여, 포함 검사, 상호작용 모드, 스키마 또는 URL, MRTR 와이어 형태, 상태 필드, 응답 분기, 재생 정책, 최종 재검증 체크리스트가 담긴 한 페이지 설계를 출력하세요.
