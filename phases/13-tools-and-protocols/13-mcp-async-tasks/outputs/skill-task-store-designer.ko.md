---
name: task-store-designer
description: 현재 Tasks 확장, 상태 없는 요청, 명시적 소유권, 폴링, 입력 업데이트, 취소로 오래가는 MCP 작업을 설계합니다.
version: 2.0.0
phase: 13
lesson: 13
tags: [mcp, tasks, extension, durable-state, stateless]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-task-store-designer.md](skill-task-store-designer.md)

`io.modelcontextprotocol/tasks` 확장을 대상으로 오래 걸리는 MCP 작업을 설계하세요.

다음을 산출합니다:

1. 자격 판단. 동기적 `tools/call` 대신 작업이 필요한 이유를 설명합니다.
2. 역량 계약. `server/discover`에 정확한 `supportedVersions`, 역량, `ttlMs`, `cacheScope`를 보여 주고, 요청별 클라이언트 역량에 Tasks 확장을 넣습니다. 도구를 광고한다면 유효한 객체형 `inputSchema`, 서버 식별 메타데이터, 캐시 힌트를 갖춘 필수·결정론적 `tools/list` 디스크립터를 포함합니다. 확장이 없으면 `requiredCapabilities` 객체와 함께 `-32021`, 미지원 버전이면 정확한 `supported`·`requested` 데이터와 함께 `-32022`를 사용합니다.
3. 생성 트랜잭션. `tasks/get`이 해석할 수 있을 때까지 작업을 영속화한 뒤, 서버 주도 `resultType: "task"`를 돌려줍니다.
4. 상태 형태. `taskId`, `status`, `statusMessage`, ISO 타임스탬프, `ttlMs`, `pollIntervalMs`, 권위 있는 소유자, 원래 연산 참조, 결과 또는 오류, 미해결 입력 요청, 발급된 모든 입력 키를 포함합니다. 완료된 작업의 안쪽 `CallToolResult`는 필수인 `resultType: "complete"`를 가지며 자체 `io.modelcontextprotocol/serverInfo` 메타데이터도 함께 실어야 합니다(SHOULD).
5. 현재 메서드. `tasks/get`, `tasks/update`, `tasks/cancel`을 정의합니다. Streamable HTTP에서 각 요청은 `Mcp-Name`을 `params.taskId`로 설정합니다. `tasks/status`, `tasks/result`, `tasks/list`를 도입하지 마세요.
6. 입력 연속. 생성 전 MRTR과 생성 후 `tasks/get`+`tasks/update`를 분리합니다. 수명 전체에서 유일한 입력 키와 부분 응답 처리를 요구합니다.
7. 내구성 계획. 원자적 파일시스템 저장, 트랜잭션 데이터베이스, 공유 큐+저장소 중 하나를 고릅니다. 워커 임대(lease)와 재시작 동작을 포함합니다.
8. 소유권 정책. 모든 작업 메서드와 구독을 테넌트와 주체로 승인합니다. 작업 id를 안다는 것을 권한으로 취급하지 마세요.
9. 취소 계약. 승인은 협조적이며 `cancelled`로 이어지지 않을 수 있음을 명시합니다.
10. 알림 옵션. POST 응답 SSE 스트림 위의 `subscriptions/listen`과 `notifications/tasks`를 사용하되, 폴링이 기본값입니다. listen 요청 id와 같은 `io.modelcontextprotocol/subscriptionId`를 승인과 모든 작업 알림에 넣습니다. id 없는 알림은 JSON-RPC 응답을 받지 않으며, 수락된 HTTP 알림은 본문 없는 `202`를 받습니다.
11. 만료 정책. `ttlMs`를 생성 시점부터 해석하고, 제거(purge) 동작을 정의하며, 다른 테넌트의 작업 존재 여부를 새지 않습니다.
12. 마이그레이션 맵. 클라이언트 요청 작업 플래그와 제거된 실험 메서드를 현재 확장 흐름으로 교체합니다.

하드 리젝(필수 반려 사항):

- 오래가는 읽기 가시성보다 작업 핸들을 먼저 돌려주는 것.
- 확장을 광고하지 않은 요청에 `resultType: "task"`를 돌려주는 것.
- `params._meta.task.required`, `tasks/status`, `tasks/result`, `tasks/list`를 현재 API로 쓰는 것.
- `initialize`, `Mcp-Session-Id`, 스티키 라우팅, 숨겨진 전송 세션 상태를 작업 저장소로 쓰는 것.
- `tasks/cancel` 승인을 워커 정지 증거로 취급하는 것.
- 하나의 작업 수명 동안 `inputRequests` 키를 재사용하는 것.
- 권위 있는 소유자가 아닌 호출자에게 작업을 돌려주는 것.
- 독립 GET, 세션 SSE, `Last-Event-ID` 재생으로 알림 전달을 구현하는 것.

거부 규칙:

- 호출자가 구체적인 내구성 요구를 제시하지 않는 한, 빠른 결정론적 조회에 대한 작업은 거부합니다.
- 작업이 프로세스 재시작을 넘어 살아남아야 하는데 메모리 전용 프로덕션 저장소를 쓰는 것은 거부합니다.
- 무한한 결과 페이로드는 거부합니다. 큰 산출물은 외부에 저장하고 승인된 리소스 핸들을 돌려줍니다.
- 명시적인 테넌트 소유권, 필터링, 페이지네이션, 보존 정책이 없는 이력 엔드포인트는 거부합니다.

수명 주기 표, 와이어 메서드, 영속화 트랜잭션, 소유권 규칙, 입력 흐름, 폴링 주기, 취소 의미론, 구독 옵션, 만료 정리, 실패 모델, 레거시 마이그레이션 맵이 담긴 한 페이지 설계를 출력하세요.
