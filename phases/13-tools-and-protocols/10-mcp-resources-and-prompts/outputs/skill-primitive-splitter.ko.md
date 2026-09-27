---
name: primitive-splitter
description: MCP 서버 설계를 검토하고 2026-07-28 계약에 따라 도구, 리소스, 프롬프트, 캐싱, 구독을 분리합니다.
version: 2.0.0
phase: 13
lesson: 10
tags: [mcp, resources, prompts, subscriptions, caching]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-primitive-splitter.md](skill-primitive-splitter.md)

제안된 MCP 서버를 소비자(호출하는 쪽)의 관점에서 검토하세요.

다음을 산출합니다:

1. 리비전 `2026-07-28`과 정확한 리소스·프롬프트 역량을 알리는 `server/discover` 결과.
2. `name`, `chooser`, `primitive`, `reason` 열을 갖춘 표.
3. 안정적인 리소스 URI 스킴과, 있다면 개수가 유계인(bounded) 리소스 템플릿.
4. 프롬프트 이름, 설명, 필수 또는 선택 인자.
5. 모든 목록 메서드에 대한 결정론적 정렬 규칙.
6. 캐시 가능한 각 결과마다 `ttlMs`와 `cacheScope`를 붙인 캐시 정책.
7. 갱신이 필요한 리소스나 목록 변경을 위한 `subscriptions/listen` 필터.
8. JSON-RPC `-32602`를 돌려주는 잘못된 리소스 사례 하나, 그리고 `supported`와 `requested`를 함께 담아 `-32022`를 돌려주는 미지원 리비전 사례 하나.

다음 판단 규칙을 사용하세요:

- 모델이 선택하는 연산은 도구입니다.
- 호스트가 읽을 수 있는, URI로 주소 지정된 콘텐츠는 리소스입니다.
- 사용자가 선택하는 메시지 워크플로는 프롬프트입니다.
- 갱신 스트림은 `subscriptions/listen`을 통해 클라이언트가 엽니다.
- listen 요청의 ID가 `io.modelcontextprotocol/subscriptionId`가 됩니다.
- 승인(acknowledgment)은 해당 구독의 모든 이벤트보다 먼저 와야 합니다.
- 알림이 이후 읽기의 권한 검사를 건너뛰게 하는 일은 없어야 합니다.
- 클라이언트가 다른 메서드를 먼저 호출하기로 해도 `server/discover`는 필수입니다.

다음 경우 설계를 반려합니다:

- 목록이 연결 이력 때문에 달라지는 경우.
- 비공개 결과가 공개 캐시에 들어가는 경우.
- 리소스 URI를 파싱·권한 검사·경계 검사 없이 받아들이는 경우.
- 설계가 `resources/subscribe`를 쓰거나, 구독을 프로토콜 세션처럼 다루는 경우.
- 프롬프트가 신뢰할 수 있는 호스트 지시를 덮어쓸 수 있게 허용하는 경우.

한 페이지짜리 계약 리뷰를 돌려주세요. 마지막에는 가장 위험한 프리미티브·캐시·구독 실수와 그것을 고치는 가장 작은 수정을 적습니다.
