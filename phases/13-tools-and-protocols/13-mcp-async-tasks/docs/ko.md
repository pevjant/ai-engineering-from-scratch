> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# MCP Tasks 확장: 상태 없는 코어 위의 오래가는 작업

> 상태 없는(stateless) MCP가 모든 연산을 한 요청 안에서 끝내야 한다는 뜻은 아닙니다. 공식 Tasks 확장은 오래 걸리는 작업에 명시적인 오래가는(durable) 핸들을 제공합니다. 서버는 `tools/call`에서 그 핸들을 돌려줄 수 있고, 어떤 인스턴스든 `tasks/get`에 답할 수 있으며, 클라이언트 입력은 프로토콜 세션을 되살리지 않고 `tasks/update`로 도착합니다.

**유형:** Build(만들기)
**언어:** Python
**선수 지식:** 페이즈 13 · 09(트랜스포트), 페이즈 13 · 11(상태 없는 MRTR), 페이즈 13 · 12(일론)
**시간:** 약 90분

## 학습 목표

- 상태 없는 프로토콜 전송과 오래가는 애플리케이션 작업 상태를 구별합니다.
- 요청별 역량과 `server/discover`에서 `io.modelcontextprotocol/tasks` 확장을 협상합니다.
- 오래가는 생성이 끝난 뒤에만 서버 주도의 `CreateTaskResult`, 즉 `resultType: "task"`를 돌려줍니다.
- `tasks/get`으로 폴링하고, `tasks/update`로 작업 입력을 이행하고, `tasks/cancel`로 협조적 취소를 요청합니다.
- 구식인 `tasks/status`, `tasks/result`, `tasks/list` 가정을 제거합니다.
- POST 응답 SSE 스트림 위의 `subscriptions/listen`으로 선택적 작업 알림을 구독합니다.
- 작업 만료, 재시작 복구, 입력 키 중복 제거, 실행 오류를 올바르게 모델링합니다.

## Tasks가 확장인 이유

Tasks는 2025-11-25에서 실험적 코어 기능으로 처음 등장했습니다. 2026년 7월 재설계는 이를 공식 `io.modelcontextprotocol/tasks` 확장으로 옮겼습니다. 덕분에 클라이언트와 서버는 모두를 위해 코어 프로토콜을 키우지 않고도 추가 수명 주기에 옵트인(opt-in)할 수 있습니다.

확장 명세가 Tasks의 현재 공식 보금자리이긴 하지만 여전히 초안(draft) 표면입니다. SDK가 지원하는 확장 버전에 고정(pin)하고, 적합성(conformance) 시나리오를 실행하고, 와이어 어댑터를 워커·저장소 도메인에서 격리하세요.

연산이 다음 성질 중 하나라도 갖고 있다면 작업(task)을 사용하세요:

- 평범한 요청 타임아웃보다 오래 살아남을 수 있다.
- 워커 큐나 외부 잡(job) 시스템이 이미 실행을 소유하고 있다.
- 클라이언트가 자신의 재시작 이후에 복구해야 한다.
- 실행 도중 사용자 또는 모델 입력을 위해 잠시 멈춘다.
- 취소와 오래가는 결과 회수가 제품 요구사항이다.

값싸고 결정론적인 조회에는 작업을 만들지 마세요. 핸들, 영속화, 폴링, 만료, 취소는 모두 실제 비용이 드는 복잡성입니다.

## 상태 없는 코어, 상태 있는 애플리케이션

MCP 2026-07-28은 `initialize`, `notifications/initialized`, 프로토콜 세션, `Mcp-Session-Id`를 제거했습니다. 하지만 이것이 상태 있는 제품을 금지하는 것은 아닙니다.

작업 id는 명시적인 애플리케이션 상태입니다:

- 서버가 돌려주기 전에 영속화합니다.
- 클라이언트는 저장해 두었다가 재시작 후에 다시 폴링할 수 있습니다.
- id는 같은 오래가는 저장소에 묶인 어떤 복제본에도 라우팅될 수 있습니다.
- 모든 작업 메서드에서 권한을 검사합니다.
- 만료와 삭제는 전송 수명이 아니라 작업 필드로 정의됩니다.

이것은 연결에 붙은 숨겨진 상태와 운영적으로 다른 존재입니다.

네 가지 수명을 분리해서 유지하세요:

| 상태 | 수명 | 소속 장소 |
|---|---|---|
| 프로토콜 메타데이터 | 한 요청 | `params._meta`, 호출마다 다시 검증 |
| 전송 작업 | 하나의 stdio 요청 또는 HTTP 응답 | 유계인 마감 시간을 가진 진행 중 코디네이터 |
| MRTR 연속 | 하나의 재시도 시퀀스 | 무결성으로 보호된 `requestState`, 필요 시 재생 통제 |
| 오래가는 작업 | 요청·복제본·재시작·재연결을 가로질러 | 승인된 `taskId`로 키 잡힌 공유 애플리케이션 저장소 |

작업 레코드를 프로세스 메모리로 옮긴다고 MCP가 상태 있어지는 것은 아닙니다. 애플리케이션이 불신뢰해질 뿐입니다. 프로토콜은 상태 없는 채로 있지만, 다른 복제본으로 라우팅된 나중의 `tasks/get`은 레코드를 복구하지 못합니다. 핸들을 돌려주기 전에 영속화하고, 그다음 모든 작업 메서드가 테넌트·주체 검사 아래 같은 공유 레코드를 해석하도록 하세요.

## 역량 협상

클라이언트는 자격 있는 요청마다 지원을 광고합니다:

```json
{
  "_meta": {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {
      "extensions": {
        "io.modelcontextprotocol/tasks": {}
      }
    },
    "io.modelcontextprotocol/clientInfo": {
      "name": "lesson-client",
      "version": "1.0.0"
    }
  }
}
```

서버는 `server/discover`에서 정확한 `supportedVersions`, 역량, `ttlMs`, `cacheScope`를 돌려주며, capabilities 아래 같은 확장을 담습니다. 도구를 광고하므로 필수인 `tools/list`도 구현합니다. 그 결과는 결정론적인 `generate_report` 디스크립터, 유효한 객체형 `inputSchema`, `resultType: "complete"`, 서버 식별 메타데이터, 공개 캐시 힌트를 돌려줍니다.

확장을 선언하지 않은 클라이언트가 작업 메서드를 부르면 `-32021`(Missing Required Client Capability)이 돌아가며, `data.requiredCapabilities`는 `{"extensions":{"io.modelcontextprotocol/tasks":{}}}`로 설정됩니다. 미지원 프로토콜 문자열은 정확한 `supported`·`requested` 데이터와 함께 `-32022`를, 버전이 없거나 문자열이 아니면 `-32602`를 돌려줍니다.

JSON-RPC `id`가 없는 봉투는 알림입니다. 수신자는 처리할 수 있지만 JSON-RPC 결과나 오류를 내보내지 않습니다. Streamable HTTP 어댑터는 수락된 알림에 본문 없는 `202 Accepted`를 돌려줍니다.

현재로서는 `tools/call`만 작업 확장 실행을 지원합니다. 미래의 요청 타입을 위해 저장소를 다시 쓰지 않아도 되게 내부 추상화를 설계하세요.

## 서버 주도 작업 생성

구식 클라이언트 플래그 `params._meta.task.required`는 사라졌습니다. 클라이언트가 확장 지원을 선언하면, 특정 `tools/call`을 작업으로 만들지는 서버가 결정합니다.

요청:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "generate_report",
    "arguments": {"size": "large"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {
          "io.modelcontextprotocol/tasks": {}
        }
      }
    }
  }
}
```

응답:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "task",
    "taskId": "tsk_786512e29e0d",
    "status": "working",
    "statusMessage": "Preparing report outline.",
    "createdAt": "2026-08-21T10:30:00Z",
    "lastUpdatedAt": "2026-08-21T10:30:00Z",
    "ttlMs": 900000,
    "pollIntervalMs": 1000
  }
}
```

그 id에 대한 `tasks/get`이 해석(resolve)될 수 있게 되기 전에는 서버가 이 핸들을 돌려주면 안 됩니다. 결과적 일관성(eventually consistent) 저장소라면 응답 전에 읽기 가시성을 기다리세요. 그렇지 않으면 클라이언트는 그럴듯해 보이는 id를 받자마자 "찾을 수 없음"을 당할 수 있습니다.

작업 응답이 "요청받지 않은(unsolicited)" 것은 클라이언트가 작업 모드를 요청하지 않기 때문입니다. 그러나 협상되지 않은(unnegotiated) 것은 아닙니다. 현재 요청은 여전히 확장을 광고해야 합니다.

## 작업의 형태

모든 작업은 다음을 실어 나릅니다:

- `taskId`: 서버가 생성한 안정적인 식별자;
- `status`: `working`, `input_required`, `completed`, `cancelled`, `failed` 중 하나;
- `createdAt`과 `lastUpdatedAt`: ISO 8601 타임스탬프;
- `ttlMs`: 생성 시점부터의 만료 시간, 광고된 제한이 없으면 `null`;
- 선택적 `pollIntervalMs`: 서버가 현재 제안하는 최소 폴링 주기;
- 선택적 `statusMessage`: 사용자 또는 모델을 위한 컨텍스트.

상태별 필드는 관련될 때만 등장합니다:

- `input_required`는 `inputRequests`를 포함합니다.
- `completed`는 원래 요청의 `result` 형태를 포함합니다.
- `failed`는 JSON-RPC `error` 객체를 포함합니다.

클라이언트는 `pollIntervalMs`를 존중해야 합니다. 서버는 더 공격적인 폴링을 속도 제한할 수 있고 작업 수명 동안 주기를 바꿀 수 있습니다.

## `tasks/get`으로 폴링하기

클라이언트가 현재 스냅샷을 요구합니다:

```http
POST /mcp HTTP/1.1
Content-Type: application/json
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tasks/get
Mcp-Name: tsk_786512e29e0d
```

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tasks/get",
  "params": {
    "taskId": "tsk_786512e29e0d",
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {
          "io.modelcontextprotocol/tasks": {}
        }
      }
    }
  }
}
```

`tasks/get` 자체는 완료되었으므로 그 결과는 항상 `resultType: "complete"`입니다. 그 안에 든 작업은 여전히 `status: "working"`이거나 `status: "input_required"`일 수 있습니다.

이 구분은 흔한 파서 버그를 막아 줍니다:

```text
result.resultType = complete    means the tasks/get RPC finished
result.status = working        means the represented job is still running
```

`tasks/result`라는 호출은 없습니다. 작업이 완료되면 다음 `tasks/get` 응답이 원래 `CallToolResult`를 `result` 아래에 인라인으로 담습니다:

```json
{
  "resultType": "complete",
  "taskId": "tsk_786512e29e0d",
  "status": "completed",
  "createdAt": "2026-08-21T10:30:00Z",
  "lastUpdatedAt": "2026-08-21T10:34:12Z",
  "ttlMs": 900000,
  "result": {
    "resultType": "complete",
    "content": [
      {"type": "text", "text": "Generated large report with approved outline."}
    ],
    "structuredContent": {"size": "large", "approved": true},
    "isError": false,
    "_meta": {
      "io.modelcontextprotocol/serverInfo": {
        "name": "tasks-demo",
        "version": "1.0.0"
      }
    }
  },
  "_meta": {
    "io.modelcontextprotocol/serverInfo": {
      "name": "tasks-demo",
      "version": "1.0.0"
    }
  }
}
```

바깥의 `resultType`은 `tasks/get` RPC가 완료되었다고 말합니다. 안쪽의 `result.resultType`은 원래 도구 호출이 완료되었다고 말합니다. 그 안쪽 판별자는 필수입니다. 안쪽 `CallToolResult`는 자신의 `io.modelcontextprotocol/serverInfo`도 함께 실어야 하며(SHOULD), 이 레슨은 타입 없는 페이로드를 저장하는 대신 그것을 포함합니다.

`tasks/list`도 없습니다. 세션 없는 서버는 어떤 작업이 연결 범위 목록에 속하는지 안전하게 추론할 수 없습니다. 이력이 필요한 애플리케이션은 명시적인 필터와 소유 규칙을 갖춘 승인된 도메인 도구를 노출해야 합니다.

## 작업 실행 도중의 입력

작업 입력과 코어 MRTR은 비슷해 보이지만 서로 다른 연속(continuation)을 사용합니다.

### 작업 생성 전에 입력이 필요한 경우

원래 `tools/call`에서 코어 `resultType: "input_required"`를 돌려줍니다. 클라이언트가 이를 이행하고 그 원래 호출을 재시도합니다. 그 동기적 MRTR 라운드들이 모두 끝난 뒤에만 작업을 생성하세요.

### 작업 생성 후에 입력이 필요한 경우

작업 상태를 `input_required`로 설정합니다. `tasks/get`이 미해결 `inputRequests`를 드러내고, 클라이언트는 `tasks/update`로 응답을 보냅니다. 클라이언트는 원래 `tools/call`을 재시도하지 않습니다.

스냅샷:

```json
{
  "resultType": "complete",
  "taskId": "tsk_786512e29e0d",
  "status": "input_required",
  "createdAt": "2026-08-21T10:30:00Z",
  "lastUpdatedAt": "2026-08-21T10:31:00Z",
  "ttlMs": 900000,
  "inputRequests": {
    "approve_outline": {
      "method": "elicitation/create",
      "params": {
        "mode": "form",
        "message": "Approve the generated report outline?",
        "requestedSchema": {
          "type": "object",
          "properties": {"approved": {"type": "boolean"}},
          "required": ["approved"]
        }
      }
    }
  }
}
```

업데이트:

```http
POST /mcp HTTP/1.1
Content-Type: application/json
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tasks/update
Mcp-Name: tsk_786512e29e0d
```

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tasks/update",
  "params": {
    "taskId": "tsk_786512e29e0d",
    "inputResponses": {
      "approve_outline": {
        "action": "accept",
        "content": {"approved": true}
      }
    },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {
          "io.modelcontextprotocol/tasks": {}
        }
      }
    }
  }
}
```

성공 응답은 빈 승인(acknowledgement)에 `resultType: "complete"`를 더한 것입니다. 상태 변화는 결과적 일관성일 수 있으므로 클라이언트는 폴링이나 리스닝을 계속합니다.

각 `inputRequests` 키는 작업 수명 전체에서 유일해야 합니다. 반복되는 `tasks/get` 스냅샷은 같은 미해결 키를 보여 줄 수 있습니다. 클라이언트는 UI에서 중복을 제거하고, 서버는 알 수 없거나 대체되었거나 이미 이행된 키에 대한 응답을 무시합니다. 부분 업데이트는 모든 필수 키에 응답할 때까지 작업을 `input_required`로 남겨 둘 수 있습니다.

## 취소는 협조적이다

`tasks/cancel`은 의도를 알리고 빈 complete 승인을 돌려줍니다. 그 승인이 워커가 멈췄다는 보장은 아닙니다. 작업이 먼저 끝나거나, 취소를 무시하거나, 나중에 전환될 수 있습니다.

```http
POST /mcp HTTP/1.1
Content-Type: application/json
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tasks/cancel
Mcp-Name: tsk_786512e29e0d
```

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tasks/cancel",
  "params": {
    "taskId": "tsk_786512e29e0d",
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {
          "io.modelcontextprotocol/tasks": {}
        }
      }
    }
  }
}
```

세 작업 메서드 모두에서 `Mcp-Name`은 `params.taskId`를 반영합니다. JSON-RPC 메서드 이름을 반복하지 않습니다. `code/main.py`는 이 규칙을 `make_http_request`에서 중앙화합니다.

이 레슨의 워커는 취소를 즉시 존중해 반복 호출이 멱등(idempotent)하게 만듭니다. 그래도 프로덕션 클라이언트는 취소를 협조적이라고 다루고, 승인만 보고 최종 작업 상태를 추론해서는 안 됩니다.

작업을 취소하는 데 `notifications/cancelled`를 쓰지 마세요. 그 알림은 요청 취소에 속하며, 오래가는 Tasks가 아닙니다.

이 구별은 라우팅 경계에서 중요합니다. 요청 취소는 하나의 진행 중 JSON-RPC 연산 또는 그 요청 범위의 HTTP 응답을 겨냥합니다. `tools/call`이 이미 `resultType: "task"`를 돌려줬다면 그 요청은 완료된 것이고, 그 전송을 닫는 것으로 오래가는 잡을 이름으로 지목하거나 멈추게 할 수 없습니다. `tasks/cancel`은 새로운 승인된 RPC입니다. `params.taskId`를 실고, 그 id를 `Mcp-Name`에 반영하고, 작업을 소유한 백엔드를 찾아내고, 협조적 취소 의도를 기록하고, 워커가 멈췄다고 주장하지 않은 채 승인을 돌려줍니다.

그러므로 게이트웨이는 요청 코디네이터와 작업 경로를 다른 테이블에 유지해야 합니다. 요청 테이블은 응답이 끝나면 사라질 수 있습니다. 작업 경로는 종결 상태와 보존 만료까지 살아남아야 합니다. [레슨 29: MCP 신뢰성, 취소, 흐름 제어](../../29-mcp-reliability-cancellation-and-flow-control/docs/en.md)가 두 경로 모두에 대한 경쟁, 타임아웃, 멱등성, 백프레셔, 재시도 규칙을 다룹니다.

## 선택적 알림

폴링이 기본값입니다. 푸시 업데이트를 원하는 클라이언트는 작업 id와 함께 `subscriptions/listen`을 보냅니다. Streamable HTTP에서는 응답이 요청 범위 SSE 스트림인 POST입니다. 독립적인 GET 이벤트 스트림도 없고, 유지해야 할 프로토콜 세션도 없습니다.

서버는 `notifications/subscriptions/acknowledged`로 수락된 id를 승인하고, 그다음 `notifications/tasks`로 전체 스냅샷을 보낼 수 있습니다. 승인과 모든 작업 알림은 `subscriptions/listen` 요청 id와 같은 `io.modelcontextprotocol/subscriptionId`를 `_meta`에 실습니다. 각 작업 알림은 그 외에는 그 순간의 `tasks/get` 결과와 동등합니다.

클라이언트는 여전히 Tasks 확장을 선언해야 합니다. 이벤트 재생이나 `Last-Event-ID`에 의존하기보다는 오래가는 작업 id로 재접속·재개해야 합니다.

## 실패 의미론

두 오류 계층을 올바르게 쓰세요.

### 프로토콜 오류

잘못된 메서드 파라미터나 알 수 없는 작업 id는 JSON-RPC 오류, 보통 `-32602`를 돌려줍니다. 확장 지원이 없으면 필수 역량 객체와 함께 `-32021`을 돌려줍니다.

### 작업 실행 결과

- `isError: true`인 정상 도구 결과는 여전히 `completed` 작업입니다. 도구 호출이 정의된 결과를 산출했기 때문입니다.
- 지연 실행 도중의 JSON-RPC 오류는 작업을 `failed`로 만들고 그 JSON-RPC 오류를 `error` 아래 저장합니다.
- 사용자 거부는 `cancelled`, 완결된 거부 결과 또는 다른 도메인별 안전 결과를 낳을 수 있습니다. 선택을 문서화하세요.

## 내구성, 만료, 소유권

최소한 작업 id, 상태, 타임스탬프, ttl, 폴링 주기, 원래 연산 소유권, 결과 또는 오류, 미해결 입력 요청, 그리고 발급된 모든 입력 키를 영속화하세요.

저장소 키는 권위 있는(authoritative) 테넌트와 주체를 포함하거나 해석할 수 있어야 합니다. 작업 id를 안다는 것이 접근 권한을 주어서는 안 됩니다. 모든 `tasks/get`, `tasks/update`, `tasks/cancel`, 구독에서 소유권을 검사하세요.

`ttlMs`는 생성 시점부터 측정되며 바뀔 수 있습니다. 클라이언트는 작업이 더 이상 관찰 가능한 업데이트를 만들지 않을 때 이것을 안전망(backstop)으로 취급할 수 있습니다. 서버는 만료된 작업을 실패 처리했다가 나중에 삭제할 수 있습니다. "완료 후 그만큼의 밀리초 동안 완료 결과를 보존하겠다는 약속"으로 설명하지 마세요.

원자적 쓰기나 트랜잭션을 사용하세요. 이 레슨은 임시 파일을 쓰고 원자적으로 이름을 바꿉니다. 다중 복제본 서비스는 공유 오래가는 저장소와 워커 임대(lease) 또는 동등한 동시성 제어를 사용해야 합니다.

```figure
tp-task-lifecycle
```

## 만들기

`code/main.py`는 결정론적인 작업 서비스를 구현합니다:

- `server/discover`는 `supportedVersions`, 캐시 힌트, Tasks 확장을 돌려줍니다.
- `tools/list`는 유효한 입력 스키마를 갖춘 결정론적·캐시 가능한 `generate_report` 디스크립터를 돌려줍니다.
- `tools/call`은 `resultType: "task"`를 돌려주기 전에 작업을 생성하고 영속화합니다.
- 새 서비스 인스턴스가 같은 작업을 다시 불러와 재시작 복구를 시연합니다.
- `tasks/get`은 완전한 작업 스냅샷을 돌려줍니다.
- 워커가 `working`에서 `input_required`로 이동합니다.
- `tasks/update`가 폼 응답을 받아 빈 complete 승인을 돌려줍니다.
- 워커가 자체 `resultType`과 서버 식별을 갖춘 안쪽 `CallToolResult`를 저장한 뒤 `completed`로 전환합니다.
- `tasks/cancel`은 이 구현에서 멱등입니다.
- HTTP 빌더는 `tasks/get`, `tasks/update`, `tasks/cancel`에 대해 `Mcp-Name`을 `params.taskId`로 설정합니다.
- 알림 헬퍼는 `notifications/subscriptions/acknowledged`와 `notifications/tasks`를 쓰며, 둘 다 listen 요청 id가 붙습니다.
- id 없는 알림은 JSON-RPC 응답을 만들지 않습니다.

워커는 백그라운드 스레드에서 잠자는 대신 명시적으로 전진합니다. 덕분에 모든 상태 전환이 결정론적이고, 프로토콜 예제가 큐 역학과 분리됩니다.

## 사용하기

저장소 루트에서:

```bash
cd phases/13-tools-and-protocols/13-mcp-async-tasks/code
python3 main.py
python3 -m unittest discover tests -v
```

기대 결과 시퀀스:

```text
id=0 resultType=complete status=ack
id=1 resultType=task status=working
id=2 resultType=complete status=working
id=3 resultType=complete status=input_required
id=4 resultType=complete status=ack
id=5 resultType=complete status=completed
```

또한 현대 서비스에서 `tasks/status`, `tasks/result`, `tasks/list`가 method-not-found를 돌려주는지 확인하세요.
`tools/list`가 결정론적인지, 그리고 모든 현재 HTTP 작업 메서드가 `Mcp-Name`으로 자신의 작업 id를 반영하는지 확인하세요.

## 출시하기

`outputs/skill-task-store-designer.md`는 이제 확장을 인식하는 설계를 산출합니다: 역량 협상, 반환 전 영속화 생성, 현재 메서드, 입력 업데이트 흐름, 소유권, 만료, 취소, 구독, 제거된 실험 메서드로부터의 마이그레이션.

## 연습 문제

1. 두 번째 미해결 입력 키를 추가하세요. 부분 `tasks/update`를 보내고 두 키 모두에 응답할 때까지 작업이 `input_required`로 남음을 증명합니다.
2. 저장소에 테넌트 소유권을 추가하고, 잘못된 인증된 주체가 제출한 유효한 작업 id를 거부합니다.
3. 만료가 있는 워커 임대(lease)를 추가하세요. 두 서비스 인스턴스가 같은 작업을 동시에 완료할 수 없음을 시연합니다.
4. `subscriptions/listen`을 위한 POST 응답 SSE 어댑터를 구현하세요. GET, `Last-Event-ID`, 세션 헤더를 추가하지 마세요.
5. 만료 정리를 추가하세요. 다른 테넌트의 작업 존재 여부를 새지 않으면서 만료된 작업과 형식이 잘못된 작업 id를 구별합니다.

## 핵심 용어

| 용어 | 현재 확장에서의 의미 |
|------|----------------------------------|
| Tasks 확장 | 오래가는 비동기 작업을 위한 선택적 `io.modelcontextprotocol/tasks` 역량 |
| `CreateTaskResult` | 자격 있는 요청에 대한 서버 주도 `resultType: "task"` 응답 |
| `tasks/get` | 종결 결과나 대기 입력을 포함한 전체 현재 작업 스냅샷 폴링 |
| `tasks/update` | 작업의 미해결 `inputRequests`에 대한 응답 제출 |
| `tasks/cancel` | 협조적 취소 의도 승인 |
| `input_required` | 클라이언트 입력이 대기 중임을 나타내는 작업 상태 |
| `pollIntervalMs` | 다음 폴링 전 서버 제안 최소 지연 |
| `ttlMs` | 작업 생성부터 측정한 만료 시간 |
| 반환 전 영속화(Durable-before-return) | 핸들을 보내기 전에 작업 id가 해석 가능해야 한다는 규칙 |
| `notifications/tasks` | 구독된 SSE 응답으로 전달되는 선택적 전체 작업 스냅샷 |

## 레거시 호환성

2025-11-25 실험 표면은 클라이언트 요청 작업 확장, `tasks/status`, `tasks/result`, 선택적 `tasks/list`를 사용했습니다. 그 이름들은 고정된 레거시 어댑터 안에만 두세요. 현재 클라이언트는 확장 역량을 쓰고, 서버 주도 핸들을 받고, `tasks/get`을 폴링하고, `tasks/update`로 입력을 공급하고, 작업 스냅샷에서 최종 결과를 읽습니다.

## 더 읽을거리

- [Official MCP Tasks extension](https://tasks.extensions.modelcontextprotocol.io/specification/draft/tasks)
- [MCP 2026-07-28 Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [MCP 2026-07-28 Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
