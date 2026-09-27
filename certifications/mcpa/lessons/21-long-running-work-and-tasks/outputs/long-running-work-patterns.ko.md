> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [long-running-work-patterns.md](long-running-work-patterns.md)

# 장기 실행 작업 패턴

MCP 2026-07-28을 위한 한 페이지 판단 참고 자료입니다. '상호작용과 실행' 도메인에 맞춰져 있습니다. 어떤 도구가 하나의 요청 안에서 끝나지 않을 수 있을 때 서버의 도구 설명 곁에 두고 보세요.

## 이 순서대로 결정하기

1. **평범한 호출.** 작업이 값싸고 결정적이며 평범한 요청 타임아웃 안에서 충분히 끝납니다. `resultType: "complete"`를 바로 돌려줍니다. 대부분의 도구는 여기서 멈춥니다.
2. **다중 왕복 요청(MRTR).** 서버가 이 같은 요청을 끝내기 전에 클라이언트에게 짧은 답 하나가 필요합니다. 일러시테이션, 샘플링 호출, 또는 roots 목록이요. `resultType: "input_required"`를 돌려주고, 클라이언트가 새 id, `inputResponses`, 에코된 `requestState`로 원래 요청을 재시도하게 합니다. 전체 교환은 여전히 몇 번의 왕복 안에서 끝납니다.
3. **태스크.** 작업 자체가 요청 타임아웃보다 오래 살아있을 수 있거나, 미리가 아니라 실행 도중에 입력이 필요하거나, 클라이언트 재시작을 이겨내고 살아남는 게 이롭거나, 협조적인 취소를 지원해야 합니다. 클라이언트가 이 요청에 `io.modelcontextprotocol/tasks`를 선언했고 서버가 `server/discover`에서 그것을 광고해야 합니다.
4. **서버가 발급한 핸들.** 상태가 애초에 하나의 연산이 끝나길 기다리는 것과 무관합니다. 호출을 넘나드는 애플리케이션 상태, 장바구니, 열린 세션, 트랜잭션을 모델이 평범한 인자로 계속 들고 다니는 것입니다(레슨 04의 SEP-2567 패턴). 태스크의 `taskId`는 이 일반 패턴의 한 사례로, 미뤄진 작업 하나를 폴링하는 데에만 한정된 것입니다.

## 기능 협상 체크리스트

- 클라이언트는 필요할지도 모르는 모든 요청에 `io.modelcontextprotocol/clientCapabilities.extensions["io.modelcontextprotocol/tasks"]`로 지원을 선언합니다. 세션 전체에 한 번이 아니라요. 그것을 기억해 둘 세션이 없기 때문입니다.
- 서버는 `server/discover`의 `capabilities.extensions`에 같은 확장을 선언합니다.
- 서버는 그 확장을 선언하지 않은 요청에 `CreateTaskResult`를 돌려주어서는(MUST NOT) 안 됩니다. 그 요청 안에서 여전히 작업을 끝낼 수 있다면 평범한 결과를 돌려주고, 태스크 없이는 요청을 처리할 수 없을 때만 `-32021`(Missing Required Client Capability)을 `data.requiredCapabilities`와 함께 돌려줍니다. 그 요청에 확장을 선언하지 않은 클라이언트의 `tasks/get`, `tasks/update`, `tasks/cancel`도 `-32021`을 받습니다.
- 태스크를 만들지는 서버가 요청별로 결정합니다. 확장을 선언한 클라이언트는 같은 도구에 대해 평범한 결과든 `resultType: "task"`든 모두 처리할 수 있어야 합니다.
- 이 리비전에서 태스크 확장을 지원하는 것은 `tools/call`뿐입니다.

## CreateTaskResult 필드

| 필드 | 의미 |
|---|---|
| `resultType` | 이 결과에서는 언제나 `"task"` |
| `taskId` | 서버가 만든, 추측 불가능한, 내구적인 식별자 |
| `status` | 생성 시 보통 `"working"` |
| `createdAt`, `lastUpdatedAt` | ISO 8601 타임스탬프 |
| `ttlMs` | 생성으로부터의 만료 시간. 광고된 제한이 없으면 `null` |
| `pollIntervalMs` | 다음 폴링 전에 권장되는 최소 지연 |
| `statusMessage` | 선택. 사람이나 모델을 위한 컨텍스트 |

돌려주기 전에 내구화: `tasks/get`이 이미 해결될 수 있는 상태가 되기 전에는 서버가 `taskId`를 건네주어서는 안 됩니다.

## 폴링과 상태 규칙

- `tasks/get` 자체는 언제나 완료되므로 그 자신의 `resultType`은 `"complete"`입니다. `working`, `input_required`, `completed`, `failed`, `cancelled`를 실어 오는 것은 바깥의 `resultType`이 아니라 안쪽의 `status` 필드입니다.
- `tasks/result`는 없습니다. `completed` 스냅샷은 원래 결과를 `result` 아래에 끼워 넣습니다. `failed` 스냅샷은 JSON-RPC 오류를 `error` 아래에 끼워 넣습니다.
- `tasks/list`도 없습니다. 스테이트리스 원칙이 목록이 안전하게 걸릴 수 있는 세션을 제거했습니다. 이력이 제품 요구 사항이라면 대신 인가된, 필터링된 도메인 도구를 노출하세요.
- `isError: true`를 담은 도구 결과도 여전히 `completed` 태스크입니다. `failed`는 실행 중의 JSON-RPC 프로토콜 오류를 위해 남겨진 것입니다.

## 실행 도중 입력 vs MRTR

| | 태스크 생성 전 | 태스크 실행 중 |
|---|---|---|
| 메커니즘 | 원래 요청 위의 코어 MRTR | 태스크의 `input_required`와 `tasks/update` |
| 클라이언트 동작 | 새 id, `inputResponses`, 에코된 `requestState`로 원래 메서드 재시도 | `inputResponses`를 실어 `tasks/update` 전송. `tools/call`을 재시도하지 않음 |
| 어디서 보이나 | `tools/call` 응답 자체 | `tasks/get` 응답의 `inputRequests` 맵 |

`inputRequests` 키는 태스크 수명 내내 유일합니다. 서버는 모르는 키, 이미 답한 키, 대체된 키에 대한 `inputResponses`를 무시합니다. 클라이언트는 폴링들에 걸쳐 반복되는 키를 거듭 보여 주기 전에 중복을 제거합니다.

## 취소

- `tasks/cancel`은 협조적입니다. 의도를 알리고 빈 `resultType: "complete"` 확인 응답을 돌려줍니다. 작업이 멈췄음을 보장하지 않으며, 태스크는 다른 종료 상태에 도달할 수도 있습니다.
- 태스크에 `notifications/cancelled`를 절대 쓰지 마세요. 그 알림은 진행 중인 요청 하나를 취소합니다. 요청이 이미 `resultType: "task"`를 돌려줬다면 그 요청은 이미 완료된 것이고, 내구적인 작업에 닿을 수 있는 것은 `tasks/cancel`뿐입니다.

## 2025-11-25 실험 기능에서 달라진 것

| 2025-11-25(제거됨) | 2026-07-28 확장 |
|---|---|
| 클라이언트가 `_meta` 태스크 키로 `taskId` 생성 | 서버가 만든 `taskId`를 `CreateTaskResult`로 돌려줌 |
| `notifications/tasks/created`가 준비를 알림 | 태스크를 만드는 결과가 이미 핸들을 실어 옴 |
| 블로킹하는 `tasks/result` 호출 | 같은 `tasks/get` 응답 안에 끼워 넣음 |
| 페이지네이션되는 `tasks/list` | 제거됨. 세션 없이는 안전한 호출자 간 범위가 없음 |
| 처음의 `submitted` 상태 | 태스크는 `working`에서 시작(실행이 즉각적이면 그 이후 상태) |
| 연결 설정에서 협상하는 `tasks` 기능 | 요청별로 선언하는 `io.modelcontextprotocol/tasks`. 연결 설정이라는 것이 존재하지 않음 |

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 4절과 14절.
