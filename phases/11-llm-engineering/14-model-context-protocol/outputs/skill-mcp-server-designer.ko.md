---
name: mcp-server-designer
description: 명시적인 디스커버리, 상태, 트랜스포트, 안전 계약을 갖춘 상태 비저장 MCP 2026-07-28 서버를 설계한다
version: 2.0.0
phase: 11
lesson: 14
tags: [llm-engineering, mcp, stateless, tool-use]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mcp-server-designer.md](skill-mcp-server-designer.md)

도메인(내부 API, 데이터베이스, 파일 소스)과 이 서버를 탑재할 호스트들이 주어지면 다음을 출력합니다:

1. 프리미티브 맵. 어떤 기능이 `tools`(동작)가 되고, 어떤 것이 `resources`(읽기 전용 데이터)가 되며, 어떤 것이 `prompts`(사용자가 호출하는 템플릿)가 되는지 정리합니다. 프리미티브 하나당 한 줄씩.
2. 디스커버리 계약. 구현이 실제로 지원하는 버전, 기능(capability), 서버 식별 정보, instructions, `ttlMs`, `cacheScope`를 담아 `server/discover` 초안을 작성합니다.
3. 요청 계약. 모든 요청의 `params._meta`에 문자열 타입의 프로토콜 버전과 객체 타입의 클라이언트 기능을 요구합니다. 클라이언트 식별 정보는 권장합니다. 필수 메타데이터가 없거나 타입이 틀리면 Invalid Params(`-32602`)를 반환합니다. `UnsupportedProtocolVersionError`(`-32022`)는 서버가 구현하지 않은 버전 문자열이 실제로 전달된 경우에만, `data.supported`와 `data.requested`를 함께 돌려주며 반환합니다.
4. 결과 계약. 해당되는 모든 결과에 `resultType`, 서버 식별 메타데이터, 결정론적 목록 정렬, 캐시 정책을 붙입니다.
5. MRTR 계획. `input_required`는 `tools/call`, `resources/read`, `prompts/get`에서만 사용합니다. `inputRequests`와 불투명한(opaque) `requestState` 중 최소 하나를 포함하고, 새 JSON-RPC ID로 원래 메서드를 재시도하되 요청된 입력에 해당하는 input responses를 담고, state 값이 있었다면 그 값을 그대로 되돌려 보냅니다.
6. 상태 계획. 여러 번 호출에 걸치는 모든 워크플로에는 서버가 발급한 불투명한(opaque) 핸들을 정의해 평범한 도구 인자로 전달합니다. 상태를 연결이나 프로토콜 세션 뒤에 숨기지 않습니다.
7. 트랜스포트와 인가 계획. stdio 또는 2026-07-28 Streamable HTTP POST 엔드포인트 중 하나를 선택합니다. HTTP라면 Origin 검증과 요청별 인가를 정의합니다. POST 요청에는 `MCP-Protocol-Version`을, JSON-RPC 요청에는 `Mcp-Method`를 요구하고, `Mcp-Name`은 `tools/call`, `resources/read`, `prompts/get`에서만 요구합니다. 정상 접수된 알림 POST는 본문 없이 HTTP 202를 반환합니다.
8. 스키마 초안. 모든 도구 파라미터에 JSON Schema를 작성합니다. 설명은 모델이 도구를 고르기 좋게 다듬고, 신뢰할 수 없는 입력에는 명시적인 범위 제한을 둡니다.
9. 파괴적 동작 목록. 상태를 바꾸는 모든 도구에 `destructiveHint: true`를 표시하고 사람의 승인을 요구합니다.
10. 검증 계획. 다음을 모두 다룹니다: 알림이 JSON-RPC 응답을 만들지 않는 경우, 잘못된 형식의 봉투와 요청 ID, 메타데이터 거절, 디스커버리, 결정론적 목록, 버전 불일치, 캐시 필드, 헤더-본문 불일치, 인가, 승인, 프롬프트 인젝션 사례 하나.

`initialize`, `notifications/initialized`, `Mcp-Session-Id`, 독립적인 HTTP GET, HTTP DELETE, `Last-Event-ID`를 최신 경로로 사용하는 설계는 거절합니다. 이 메커니즘은 2025-11-25까지의 프로토콜 버전을 위한, 명확히 격리된 어댑터 안에서만 허용합니다. 지원 중단된 Roots, Sampling, Logging을 새 구현에 추가하지 마세요. 호환성 지원임을 반드시 표시하고, Roots나 Sampling 입력은 MRTR을 사용해야 합니다. 인가·검증·승인 경로 없이 디스크에 쓰거나 외부 API를 호출하는 서버는 받아들이지 않습니다.
