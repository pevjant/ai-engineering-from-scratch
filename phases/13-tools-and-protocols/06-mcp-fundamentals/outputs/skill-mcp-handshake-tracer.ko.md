---
name: mcp-request-tracer
description: 현대 무상태 및 명시적 레거시 프로토콜 시대에 걸쳐 MCP 트랜스크립트를 메시지별로 감사합니다.
version: 2.0.0
phase: 13
lesson: 06
tags: [mcp, json-rpc, stateless, metadata, compatibility]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mcp-handshake-tracer.md](skill-mcp-handshake-tracer.md)

MCP JSON-RPC 봉투들의 연속이 주어지면, 각 메시지를 MCP `2026-07-28` 기준으로 독립적으로 감사합니다. 레거시 트래픽은 탐지하되, 핸드셰이크나 프로토콜 세션이 존재한다고 절대 가정하지 않습니다.

산출물:

1. 메시지 주석. 방향, JSON-RPC 종류, 메서드, 원시 기능, 요청 id, 탐지된 시대를 명시합니다.
2. 현대 메타데이터 검사. 모든 요청에서 `params._meta.io.modelcontextprotocol/protocolVersion`과 `params._meta.io.modelcontextprotocol/clientCapabilities`를 검증합니다. 권장 `clientInfo`가 있는지 기록합니다.
3. 결과 검사. 모든 현대 성공이 `resultType: "complete"` 또는 다른 명시된 결과 타입을 가지는지, 그리고 결과 `_meta`에 권장 서버 신원이 있는지 검증합니다.
4. 디스커버리와 버전 검사. 현대 서버가 `server/discover`를 구현하는지 검증합니다. `-32022`를 현대의 증거로 해석하고 `data.requested`와 `data.supported`를 확인합니다.
5. 캐시 검사. `server/discover`, 목록 메서드, `resources/read`에서 `ttlMs`와 `cacheScope`를 요구합니다. 비결정론적 목록 순서를 표시합니다.
6. 방향 검사. 현대 트래픽에서 서버가 시작한 JSON-RPC 요청은 거부합니다. 요청 관련 알림과 클라이언트가 연 `subscriptions/listen` 스트림은 허용합니다.
7. 호환성 검사. `initialize`와 `notifications/initialized`는 레거시로만 표시합니다. 현대 트래픽에서 요구하지 않습니다.

즉시 반려 사항:

- stdio 프로세스, HTTP 연결, 또는 `Mcp-Session-Id`를 현대 프로토콜 상태로 취급하는 것.
- 이전 요청에서 클라이언트 기능을 추론하는 것.
- `-32020`, `-32021`, `-32022` 같이 인식된 현대 에러 뒤에 레거시로 폴백하는 것.
- `resultType` 없는 현대 성공을 받아들이는 것.

거절 규칙:

- 트랜스크립트가 JSON-RPC 2.0이 아니면 멈추고 호환되지 않는 봉투를 지목하세요.
- 증거를 조용히 다시 쓰라는 요청은 거절하세요. 원본 트랜스크립트를 보존하고 별도의 수정된 예제를 만드세요.

도착 순서대로 메시지마다 한 줄씩 출력합니다:

```text
[request/modern/tools] id=7 tools/list metadata=valid
```

현대, 레거시, 무효, 모호 메시지의 개수로 끝내고, 그 뒤에 첫 번째 교정 조치를 잇습니다.
