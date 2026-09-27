---
name: gateway-bootstrap
description: 레지스트리 심사, 정책, 라우팅, 호환성 경계를 갖춘 상태 비저장 MCP 2026-07-28 게이트웨이를 설계한다.
version: 2.0.0
phase: 13
lesson: 17
tags: [mcp, gateway, stateless, registry, rbac, subscriptions, tasks]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-gateway-bootstrap.md](skill-gateway-bootstrap.md)

클라이언트, 백엔드, 인가 요구 사항, 규제 준수 제약이 주어졌을 때, 게이트웨이 설계를 산출한다.

## 필요한 입력

- 공개 게이트웨이 리소스 URI, 받아들이는 프로토콜 리비전, 전송 방식.
- 인증된 주체(principal)와 역할(role) 모델.
- 백엔드 엔드포인트, 발급자, 리소스, 레지스트리 레코드, 퍼블리셔 증빙, 승인된 디스크립터.
- 도구 가시성, 인자 정책, 비용 등급, 데이터 민감도.
- 스트리밍, 변경 알림, MRTR, Tasks 요구 사항.
- 감사(audit), 보존, 트레이스, 마스킹(redaction) 요구 사항.

## 산출물

1. 상태 비저장 인그레스. POST 엔드포인트 하나, 요청별 버전과 capability, 일치하는 메서드·이름 헤더, JSON 또는 요청 범위(request-scoped) SSE, 현대적 GET과 DELETE에 대한 405. 버전 지원 검증 전에 헤더 일치를 먼저 검증한다. HTTP 400 `-32020`, 정확한 supported/requested 데이터가 담긴 HTTP 400 `-32022`, HTTP 404 `-32601`, 선택적 에러 데이터 직렬화, 빈 본문 202 알림 처리를 명시한다.
2. 탐색 계획. 게이트웨이 `server/discover`를 구현하고, 각 백엔드를 탐색하며, 안전한 엔드투엔드 capability 교집합만 노출하고, 현재의 `resultType`, `ttlMs`, `cacheScope`, 서버 식별 메타데이터를 포함한다.
3. 심사(admission) 테이블. 공식 레지스트리 `server.json` 발행 형태와 `com.example/*` 스타일 이름 검증은 보안 심사와 분리해서 수행한다. 모든 백엔드에 대해 레코드를 외부 검증된 퍼블리셔 네임스페이스, 출처(provenance) 소스, 엔드포인트, 버전 정책, 디스크립터 다이제스트, 발급자, 리소스, 승인, 만료 상태와 조인한다.
4. 네임스페이스 맵. 모든 백엔드 도구에 안정적인 정규화된 공개 이름을 부여하고, 모든 `tools/list` 디스크립터에 유효한 객체 루트 `inputSchema`를 유지한다. 순서에 의한 충돌(collision-by-order)은 거부한다.
5. 인가 매트릭스. 주체와 역할을 공개 도구, 리소스, 인자, 스코프에 매핑한다. 바깥쪽 자격 증명과 백엔드 자격 증명은 분리하고 발급자에 묶어 둔다.
6. 전달 계약. 자기 완결적인 새 백엔드 요청을 만들고, 중개되는 클라이언트 capability만 광고하며, 백엔드 결과를 검증하고, 트레이스 상관관계(trace correlation)를 보존한다.
7. 캐시 계획. 주체에 의존하는 탐색과 목록은 private으로 만든다. 상한이 있는 TTL과 무효화 동작을 정한다.
8. 속도 제한 및 감사 정책. 제한을 주체, 발급자, 리소스, 도구, 비용 등급, 시간을 키로 매긴다. 자격 증명과 불필요한 민감 인자는 마스킹한다.
9. 상호작용 라우팅. 요청 범위 SSE, `subscriptions/listen` 확인(acknowledgment)과 재연결 동작, 바이트 단위로 정확한 MRTR 상태 전달, `Mcp-Name`의 작업 id에 의한 Tasks 라우팅을 기술한다.
10. 전송 어댑터. 게이트웨이가 파싱된 요청과 헤더를 받는다면 인프로세스 프로토콜 모델로 표시하고, JSON Content-Type과 JSON+SSE Accept 강제를 위해 레슨 09에 연결한다.
11. 호환성 어댑터. 구형 초기화, 세션 id, GET 스트림, 리소스 구독, 실험적 작업 메서드는 현대적 게이트웨이 코어에서 울타리(fence)로 분리한다.

## 하드 리젝트(절대 거부)

- 세션 어피니티(affinity), 세션 스토어, 세션 id 재작성을 2026-07-28에 필수라고 주장하는 경우.
- 심사 증빙 없이 레지스트리 등재나 표시 이름을 신뢰하는 경우.
- 조용한 도구 충돌, 또는 재승인 없는 디스크립터 핀(pin) 업데이트.
- 백엔드에서 바깥쪽 베어러 토큰을 재사용하거나, 백엔드 토큰을 다른 발급자나 리소스에서 재사용하는 경우.
- 주체로 필터링된 목록을 공개 캐시하는 경우.
- 독립적인 현대적 GET 이벤트 스트림, Last-Event-ID 리플레이, 리소스 구독 메서드.
- 새로운 `tasks/list`나 `tasks/result` 동작.
- 제거된 프로토콜 세션만 키로 매긴 속도 제한.
- 별도의 검증된 심사와 출처 상태가 아닌, `server.json` 안에서 발명된 보안 검증.
- `inputSchema`가 빠진 네임스페이스화된 도구 디스크립터.

## 출력 형식

Ingress, Discovery, Admission, Namespace Map, Authorization, Forwarding, Cache, Rate Limits, Audit, Interactions, Legacy Adapter라는 이름의 섹션을 돌려준다. 마지막에 가장 강력한 인수 테스트를 요구하는 단 하나의 경로를 명시한다.
