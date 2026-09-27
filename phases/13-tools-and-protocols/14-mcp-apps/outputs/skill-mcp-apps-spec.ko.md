---
name: mcp-apps-spec
description: 상태 없는 2026-07-28 프로토콜 위의 MCP 앱 계약을 설계하고 검토합니다.
version: 2.0.0
phase: 13
lesson: 14
tags: [mcp, apps, stateless, ui-resources, csp, sandbox]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mcp-apps-spec.md](skill-mcp-apps-spec.md)

인터랙티브한 뷰가 필요할 수 있는 MCP 도구가 주어지면, 프레임워크 중립적인 계약을 산출하세요.

## 필수 입력

- 도구 이름, 인자, 평범한 텍스트 결과, 구조화된 결과.
- 뷰가 지원해야 하는 사용자 상호작용.
- 데이터 민감도와 응답이 권한 컨텍스트에 따라 달라지는지 여부.
- 뷰가 필요로 하는 브라우저 권한과 외부 오리진.
- Apps 지원이 없는 호스트를 위한 텍스트 전용 동작.

## 산출물

1. 현재 코어 봉투. `2026-07-28`, 요청별 `protocolVersion`, `clientCapabilities`, 권장되는 `clientInfo`, 일치하는 `Mcp-Method`·`Mcp-Name` 헤더, `resultType` 응답을 보여 줍니다.
2. 디스커버리 항목. 보수적인 `ttlMs`와 `cacheScope`와 함께 `server/discover`에 `io.modelcontextprotocol/ui`를 광고합니다.
3. 도구 선언. `tools/list`가 돌려주는 도구에 중첩된 `_meta.ui.resourceUri`를 붙입니다. `tools/call`이 UI를 드러내길 기다리지 마세요.
4. 리소스 계약. `resources/read` 전에 결정론적 `resources/list` 메타데이터를 포함합니다. 하나의 정규(canonical) `ui://` URI, 안정적인 이름과 설명, `text/html;profile=mcp-app`, 캐시 힌트, CSP 도메인 목록(`connectDomains`, `resourceDomains`, `frameDomains`, `baseUriDomains`), 최소한의 권한 객체를 제공합니다.
5. 결과 계약. 호스트가 앱을 렌더링하든 아니든 유용한 텍스트와 구조화된 데이터를 돌려줍니다.
6. 브리지 계약. 모든 Apps `ui/*` 또는 프록시 메서드, 정확한 메시지 오리진, 인자 스키마, 결과 스키마, 호스트 쪽 동의 검사를 나열합니다.
7. 폴백. 클라이언트가 Apps 확장 역량을 생략할 때의 도구와 결과를 설명합니다.
8. 검증 표. 라우팅 전의 HTTP 400 `-32020` 헤더 불일치, 정확한 supported·requested 버전 데이터가 있는 HTTP 400 `-32022`, `data.requiredCapabilities`가 있는 HTTP 400 `-32021`, HTTP 404 `-32601`, 빈 본문 202 알림, CSP 위반, 신뢰할 수 없는 콘텐츠, 무단 브리지 호출, 텍스트 폴백을 다룹니다.
9. 전송 경계. 구현이 파싱된 요청과 헤더를 받는다면, 그것을 프로세스 내 프로토콜 모델이라고 라벨 붙이고 레슨 09의 완전한 Streamable HTTP 어댑터에 연결합니다. 진짜 어댑터는 JSON Content-Type과 JSON 더하기 SSE를 포함하는 Accept 값을 요구해야 합니다.

## 하드 리젝(필수 반려 사항)

- 코어 `initialize`, `notifications/initialized`, `Mcp-Session-Id` 경로를 현재 MCP로 내미는 것.
- 와일드카드 `postMessage` 대상 오리진, 또는 `event.origin` 검증을 건너뛰는 수신자.
- 도구가 실행된 후에만 드러나는 UI 바인딩.
- 와일드카드 CSP 도메인 목록, 무제한 네트워크 오리진, 눈에 보이는 기능 없는 권한.
- 정의된 살균(sanitization) 경계 없이 삽입되는 사용자 제어 HTML.
- iframe 클릭을 호스트 권한으로 취급하는 결과가 큰 UI 동작.
- 리소스를 광고하면서 `resources/list`를 빠뜨리는 서버.
- `id` 없는 알림에 대한 어떤 JSON-RPC 응답 본문.

## 호환성 경계

레거시 평평한 UI 메타데이터는 폴백으로 읽을 수 있지만, 새 출력은 중첩된 `_meta.ui.resourceUri`를 씁니다. `ui/initialize`는 Apps postMessage 핸드셰이크로 식별될 때만 허용됩니다. 제거된 MCP 코어 초기화를 대신하지 못합니다.

## 출력 형식

다음 제목을 가진 컴팩트한 설계를 돌려주세요: Core Wire, Discovery, Tool, Resource, Result, Bridge, Security, Fallback, Verification. 마지막에 가장 위험한 단 하나의 오리진·권한·동의 가정을 적습니다.
