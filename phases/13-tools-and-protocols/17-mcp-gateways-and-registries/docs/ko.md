> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 상태 비저장 MCP 게이트웨이와 레지스트리 심사

> 게이트웨이는 모든 경로를 명시적으로 만들어야 합니다. 2026-07-28 프로토콜은 전송 세션 없이도 메서드, 이름, 버전, capability, 식별, 캐시, 트레이스 경계를 제공합니다.

**유형:** Learn
**언어:** Python
**선수 지식:** 페이즈 13 · 15(보안), 페이즈 13 · 16(인가)
**소요 시간:** 약 75분

## 학습 목표

- 세션 어피니티 없이 여러 MCP 서버를 하나의 2026-07-28 엔드포인트 뒤에 모을 수 있다.
- 정책이나 전달에 앞서 요청별 메타데이터와 라우팅 헤더를 검증할 수 있다.
- 안정적인 네임스페이스, 결정적(deterministic) 순서, 디스크립터 핀, RBAC, private 캐싱으로 도구를 병합할 수 있다.
- 레지스트리 레코드를, 여전히 심사 정책이 필요한 탐색 증빙으로 다룰 수 있다.
- 요청 범위(request-scoped) SSE, `subscriptions/listen`, MRTR 재시도, Tasks 확장 호출을 올바르게 라우팅할 수 있다.
- 구형 핸드셰이크와 세션 지원을 현대적 경로에서 격리할 수 있다.

## 문제 상황

클라이언트 하나를 서버 하나에 직접 연결하는 건 간단합니다. 더 큰 배포에서는 더 어려운 질문에 대한 일관된 답이 필요합니다:

- 어떤 서버들이 허용되는가?
- 어떤 주체(principal)가 각 도구를 보고 호출할 수 있는가?
- 두 백엔드가 같은 이름을 노출하면 어떻게 되는가?
- 디스크립터 변경은 어떻게 검토되는가?
- 속도 제한과 감사 이벤트는 어디에 적용되는가?
- 다음 요청을 어떤 인스턴스든 처리할 수 있는가?

게이트웨이는 클라이언트와 백엔드 MCP 서버 사이에 앉습니다. 하나의 MCP 엔드포인트를 제시하고, 공통으로 적용되는(cross-cutting) 정책을 적용하고, 승인된 요청을 전달합니다.

구형 게이트웨이 설계는 흔히 하나의 클라이언트 세션을 여러 백엔드 세션으로 멀티플렉싱하고 `Mcp-Session-Id`를 재작성했습니다. 그것은 레거시 호환성 설계입니다. 2026-07-28 코어에는 프로토콜 세션이 없습니다.

## 개념

### 현대적 게이트웨이 경로

요청 하나하나마다:

1. 전송 계층 인가로부터 주체를 인증합니다.
2. `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`, `params._meta`를 검증합니다.
3. 주체, 리소스, 메서드, 도구, 인자를 인가합니다.
4. 디스크립터, 레지스트리, 속도 제한, 데이터 정책을 적용합니다.
5. 선택된 백엔드를 위한 새로운 자기 완결적 요청을 만듭니다.
6. 백엔드 결과를 검증하고 게이트웨이 결과를 돌려줍니다.
7. 시크릿을 로그에 남기지 않으면서 감사 이벤트를 기록합니다.

어떤 단계도 숨겨진 프로토콜 세션을 필요로 하지 않습니다. 애플리케이션 상태는 여전히 데이터베이스, 명시적 핸들, Tasks, 무결성이 보호된 MRTR 상태에 존재할 수 있습니다.

### 런타임 정책이 게이트웨이의 1차 결정이다

심사(admission)는 어떤 백엔드 버전이 게이트웨이에 들어올 수 있는지를 결정합니다. 살아 있는 호출을 인가하는 것은 아닙니다. 모든 요청에 대해 게이트웨이는 인증된 주체, 발급자와 리소스, 테넌트, 매칭된 메서드와 이름, 정규화된 인자, 심사를 통과한 디스크립터 핀, 현재 백엔드 상태, capability 교집합, 데이터 분류, 속도 제한 상태, 행위에 묶인 승인이 있다면 그것까지 고려해 정책을 다시 계산합니다.

이 순서가 중요합니다. 레지스트리 레코드는 사용자의 역할이 철회된 뒤에도 활성 상태로 남을 수 있습니다. 디스크립터는 핀으로 고정된 채로, 목적지 인자가 테넌트 경계를 넘을 수 있습니다. 백엔드는 승인된 채로, 사고 대응 정책이 상태를 바꾸는 호출을 격리할 수 있습니다. 따라서 런타임 정책이 1차 허용/거부 결정이고, 레지스트리와 디스크립터 증빙은 그 입력입니다.

연결이나 제거된 세션 식별자 아래에 허용 결정을 캐시하지 마세요. 정책을 사용할 수 없다면 작업 등급별로 선언된 실패 정책을 따르세요. 안전한 기본값은 상태 변경과 민감한 읽기에 대해 fail closed(거부로 실패)하는 것이고, 명시적으로 승인된 공개 읽기 경로만 위험 모델이 허용할 때 짧은 수명의 마지막으로 알려진 정책(last-known policy)을 쓸 수 있습니다. 어떤 정책 버전과 실패 경로가 결정을 만들었는지 기록하고, 돌려주기 전에 백엔드 결과를 검증하세요.

### POST 엔드포인트 하나

현대적 Streamable HTTP는 JSON-RPC 메시지 하나하나를 POST로 보냅니다:

```text
POST /mcp
Authorization: Bearer <gateway-token>
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: notes.search
Accept: application/json, text/event-stream
```

게이트웨이는 그 POST에 대해 JSON 또는 요청 범위 SSE를 돌려줄 수 있습니다. 현대적 요청에 대한 GET과 DELETE는 405를 돌려줍니다. `Mcp-Session-Id`와 `Last-Event-ID`는 권한, 어피니티, 리플레이 동작을 만들어 내지 않습니다.

헤더와 본문의 값은 서로 일치해야 합니다. 불일치하면 백엔드를 찾아보기 전에 `-32020`으로 거부하세요. 이렇게 하면 로드 밸런서, 게이트웨이, 속도 제한기가 전체 본문을 파싱하지 않고도 라우팅하면서 엔드투엔드 무결성을 유지할 수 있습니다.

정확히 하나의 순서로 검증하세요: JSON-RPC와 메타데이터 타입 검사 → 헤더와 본문의 일치 여부 → 매칭된 버전의 지원 여부. 불일치는 HTTP 400과 `-32020`을 돌려줍니다. 헤더와 본문이 일치하긴 하는데 지원하지 않는 버전이라면, HTTP 400과 `-32022`, 그리고 정확히 `{"supported":["2026-07-28"],"requested":"<actual>"}`인 `data`를 돌려줍니다. 알 수 없는 메서드는 HTTP 404와 `-32601`을 돌려줍니다.

`ProtocolError`는 선택적 `data`를 담고, 게이트웨이는 그것을 JSON-RPC 에러 객체로 직렬화합니다. 알림(notification)에는 `id`가 없으므로 JSON-RPC 성공이나 에러 응답을 절대 받지 않습니다. 받아들여진 HTTP 알림은 빈 본문과 함께 202를 돌려줍니다.

### 모든 계층에서 탐색 구현하기

게이트웨이는 클라이언트를 위해 `server/discover`를 구현합니다. 또한 각 백엔드도 탐색해서 프로토콜 버전, capability, 확장을 파악합니다.

게이트웨이 결과 예제:

```json
{
  "resultType": "complete",
  "supportedVersions": ["2026-07-28"],
  "capabilities": {
    "tools": {"listChanged": true}
  },
  "ttlMs": 30000,
  "cacheScope": "private",
  "_meta": {
    "io.modelcontextprotocol/serverInfo": {
      "name": "enterprise-gateway",
      "version": "2.0.0"
    }
  }
}
```

게이트웨이가 엔드투엔드로 책임질 수 있는 capability 교집합만 광고하세요. 백엔드 기능이 자동으로 노출해도 안전한 것은 아닙니다. 백엔드 경로가 없는 게이트웨이 기능은 광고해도 쓸모가 없습니다.

`serverInfo`는 스스로 보고하는 표시·진단 데이터입니다. 레지스트리나 퍼블리셔 증명으로 사용하지 마세요.

### 요청별 클라이언트 capability

전달되는 모든 요청에는 현재의 `_meta` 봉투가 필요합니다:

```json
{
  "io.modelcontextprotocol/protocolVersion": "2026-07-28",
  "io.modelcontextprotocol/clientCapabilities": {},
  "io.modelcontextprotocol/clientInfo": {
    "name": "enterprise-gateway",
    "version": "1.0.0"
  }
}
```

바깥쪽 클라이언트의 capability를 백엔드에 무작정 복사하지 마세요. 백엔드 입장에서 클라이언트는 게이트웨이입니다. 게이트웨이가 올바르게 중개할 기능만 광고하세요.

### 결정적 네임스페이싱

백엔드 도구들을 안정적인 공개 이름 아래 병합합니다:

```text
notes.search
notes.create
issues.list
issues.open
```

공개 이름에서 백엔드와 원래 도구 이름으로 가는 매핑을 유지하세요. 충돌이 나면 첫 번째나 마지막을 고르는 식으로 결정하지 마세요. 공개 이름은 승인과 감사 계약의 일부이므로, 바꾸는 것은 마이그레이션입니다.

`tools/list`는 결정적이어야 합니다. 가시성이 주체에 따라 다르다면 `cacheScope: private`을 돌려주세요. 상한이 있는 `ttlMs`는 사용자별 목록이 인가 컨텍스트를 넘어 새어 나가지 않게 하면서 백엔드 탐색 부하를 줄여 줍니다.

노출되는 모든 도구 디스크립터는 안정적인 이름, 설명, 객체 루트 `inputSchema`를 포함합니다. 네임스페이싱이 필수 디스크립터 필드를 제거할 수는 없습니다. 완전한 목록 결과에는 `resultType`, 서버 식별 메타데이터, 캐시 힌트도 포함됩니다.

### 승인된 디스크립터를 핀으로 고정하기

심사 시점에 완전한 디스크립터를 캐노니컬화(canonicalize)하고 그 다이제스트를 정규화된 공개 이름 아래 저장합니다. 목록과 호출 시점에 살아 있는 디스크립터를 승인된 다이제스트와 비교합니다.

바뀌었다면:

- `tools/list`에서 제거합니다.
- 직접 호출을 거부합니다.
- 감사 이벤트를 발생시킵니다.
- 핀을 업데이트하기 전에 정책 또는 사람의 재승인을 요구합니다.

게이트웨이는 유용한 중앙 집행 지점이지만, 처음 본 디스크립터를 안전하게 만들어 주지는 않습니다. 초기 검토는 여전히 필요합니다.

### 레지스트리는 탐색을 돕지, 결정하지 않는다

레지스트리 `server.json`은 발행 메타데이터를 제공합니다. 패키지 기반 레코드는 이렇게 생겼을 수 있습니다:

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "com.example/notes",
  "description": "Example notes MCP server.",
  "version": "1.0.0",
  "packages": [
    {
      "registryType": "npm",
      "identifier": "@example/notes-mcp",
      "version": "1.0.0",
      "transport": {"type": "stdio"}
    }
  ]
}
```

발행 메타데이터는 게이트웨이의 보안 결정을 대신해 주지 않습니다. 검증된 퍼블리셔와 출처(provenance) 증빙은 별도의 심사 상태에 보관하세요:

```json
{
  "registryName": "com.example/notes",
  "registryVersion": "1.0.0",
  "publisher": {"namespace": "com.example", "status": "verified"},
  "provenance": {
    "source": "registry.modelcontextprotocol.io",
    "recordId": "com.example/notes@1.0.0"
  },
  "admission": {"status": "approved", "reviewedBy": "gateway-policy"}
}
```

게이트웨이는 `server.json` 형태를 검사하고 그것을 이 외부 상태와 조인합니다. 그래도 게이트웨이에는 심사 정책이 필요합니다.

심사를 통과하는 각 백엔드에 대해 기록할 항목:

- 정확한 레지스트리와 레코드 식별자.
- 검증된 퍼블리셔 네임스페이스 또는 도메인 증빙.
- 허용된 전송 방식과 엔드포인트.
- 핀으로 고정된 버전 또는 승인된 업그레이드 정책.
- 아티팩트 또는 디스크립터 다이제스트.
- 인가 발급자와 리소스.
- 검토자, 승인 시각, 만료.

표시 이름이 익숙한 제품과 닮았다고 해서 그 서버를 받아들이지 마세요. 레지스트리에 등재되어 있다는 것을 운영 보안 검토로 취급하지 마세요. 사설 서버도 공개 레지스트리에 한 번도 나오지 않았더라도 같은 증빙 스키마를 통해 심사받을 수 있습니다.

이 레슨은 게이트웨이 심(seam)을 구현합니다: 백엔드가 라우팅 가능해지기 전에 발행 증빙을 로컬 심사와 조인합니다. [레슨 30: MCP 레지스트리 공급망, 심사, 드리프트, 롤백](../../30-mcp-registry-supply-chain-and-drift/docs/en.md)은 정확한 네임스페이스 증명, 아티팩트 출처, 불변 핀, 실시간 디스크립터 드리프트, 레지스트리 상태 재조정, 변조 방지 심사 원장, 증빙 기반 롤백을 위한 완전한 컨트롤 플레인을 구축합니다. 그 공급망 상태는 위의 요청별 런타임 결정과 분리해 두세요.

### 자격 증명 중개

게이트웨이는 자기 호출자를 인증하고, 별도로 백엔드에 대해 자신을 인증합니다. 백엔드 자격 증명은 절대 클라이언트로 가지 않습니다.

다음 바인딩을 명시적으로 유지하세요:

```text
outer principal -> gateway role and policy
backend issuer + resource -> backend registration and token
```

바깥쪽 게이트웨이 토큰을 백엔드로 절대 전달하지 마세요. 백엔드 토큰을 다른 발급자나 리소스에서 절대 재사용하지 마세요. 어떤 도구가 최종 사용자를 대신해 동작한다면, 공유 서비스 자격 증명으로 사용자를 사칭하는 대신 설계된 교환(exchange)이나 클레임 모델로 그 위임을 보존하세요.

### 세션 없이 속도 제한하기

제한을 인증된 주체, 발급자, 리소스, 공개 도구, 비용 등급, 시간 윈도우를 키로 매기세요. 세션 id는 존재하지 않고, 설령 존재하더라도 돌리기 쉬운 값입니다.

비용이 큰 작업을 소비하기 전에 값싼 검증을 먼저 적용하세요. 거부된 호출이 남용(abuse) 제한에 먹힐지, 비즈니스 쿼터에 먹힐지, 둘 다에 먹힐지 결정하세요.

### 결정 체인을 감사하기

호출 하나를 재구성할 수 있을 만큼 기록하세요:

- 요청과 트레이스 식별자.
- 인증된 주체와 발급자.
- 공개 도구와 백엔드 경로.
- 디스크립터 핀 버전.
- 정책 결정과 그 이유.
- 지연 시간과 결과 등급.
- 해당하면 MRTR 라운드 또는 작업 식별자.

베어러 토큰, 인가 코드, 리프레시 토큰, 원본 시크릿, 불필요한 민감 인자는 마스킹하세요.

### 요청 범위 SSE

평범한 POST는 그 하나의 요청 동안 작업이 스트리밍될 때 요청 범위 SSE를 돌려줄 수 있습니다. 응답 스트림을 닫으면 진행 중인 그 현대적 HTTP 요청이 취소됩니다.

별도의 GET 스트림을 만들지 말고 Last-Event-ID 리플레이를 약속하지 마세요. 그것들은 더 오래된 전송 가정입니다.

### 장기 변경 알림

목록과 리소스 변경 알림을 위해, 현재 클라이언트는 POST로 `subscriptions/listen`을 보내고 SSE 응답을 받습니다. 알림 필터는 정확히 `toolsListChanged`, `promptsListChanged`, `resourcesListChanged`, `resourceSubscriptions`라는 평면(flat) 필드를 사용합니다:

```json
{
  "jsonrpc": "2.0",
  "id": "listen-tools",
  "method": "subscriptions/listen",
  "params": {
    "notifications": {
      "toolsListChanged": true
    },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}
```

첫 번째 이벤트가 지원되는 부분집합을 확인(acknowledge)합니다. 구독 식별자는 스트림을 연 요청의 JSON-RPC id입니다:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/subscriptions/acknowledged",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/subscriptionId": "listen-tools"
    },
    "notifications": {
      "toolsListChanged": true
    }
  }
}
```

게이트웨이는 그다음 확인된 변경 유형만 전달합니다. 그 스트림 위의 모든 알림은 `params._meta`에 같은 `io.modelcontextprotocol/subscriptionId`를 실습니다. 자동 리플레이나 자동 재청취(re-listen)는 없습니다. 재연결 시 클라이언트는 구독을 다시 열고 의존하던 목록들을 새로 고칩니다. 서버가 시작한 정상 종료는 같은 구독 id가 붙은 최종 complete 결과를 돌려줍니다.

현대적 경로는 `resources/subscribe`, `resources/unsubscribe`, 요청하지 않은 독립 GET 스트리밍을 대체합니다. 그것들은 버전 게이트가 있는 구형 경로에만 남겨 두세요.

### 게이트웨이를 통과하는 MRTR

백엔드가 `resultType: input_required`를 돌려주면, 게이트웨이는 바깥쪽 클라이언트가 필요한 입력 요청을 지원할 때만 그 결과를 전달할 수 있습니다. 게이트웨이가 의도적으로 상호작용을 종료하고 다시 발급하는 경우가 아니라면 `requestState`를 바이트 단위로 보존하세요.

클라이언트는 새 JSON-RPC id와 `inputResponses`를 들고 원래 공개 도구를 재시도합니다. 게이트웨이는 재시도를 재인가하고, 같은 공개 경로인지 검사한 뒤, 새 백엔드 요청을 전달합니다. 이전 라운드가 무제한 승인을 부여했다고 가정해서는 안 됩니다.

### Tasks 확장 라우팅

Tasks는 `io.modelcontextprotocol/tasks`로 식별되는 공식 확장입니다. 코어 세션의 대체품이 아닙니다.

클라이언트는 요청별 클라이언트 capability 안에 이 확장을 선언하고, 게이트웨이는 라이프사이클을 엔드투엔드로 보존할 수 있을 때만 탐색에서 그것을 광고합니다. 지원되는 `tools/call`에 대해 백엔드만이 평범한 결과를 돌려줄지 `resultType: task`를 돌려줄지 결정합니다. 작업 결과는 `taskId`, `status`, 타임스탬프, `ttlMs`, 선택적 `pollIntervalMs`를 결과 안에 직접 실습니다. 그 결과를 보내기 전에 작업이 이미 영속적으로 읽힐 수 있어야 합니다.

게이트웨이는 불투명한(opaque) 작업 식별자에 대해 인증된 주체와 백엔드 경로를 기록합니다. 이후의 `tasks/get`, `tasks/update`, `tasks/cancel` 호출은 `params.taskId`를 `Mcp-Name`으로 사용하므로, 중개자에게 라우팅 키를 줍니다. `tasks/get`은 현재 작업 상태와 함께 `resultType: complete`를 돌려주고, 종료 상태에서 최종 결과나 프로토콜 에러를 인라인합니다. `tasks/update`는 미해결 작업 입력에 대해 키가 매겨진 `inputResponses`를 보내고 빈 complete 확인 응답을 돌려줍니다. `tasks/cancel`은 협조적 의도로서 빈 complete 확인 응답을 돌려줄 뿐, 작업이 멈춘다는 보장이 아닙니다.

새로운 `tasks/list`나 `tasks/result` 메서드를 구현하지 마세요. 그것들은 구형 실험 모델에 속합니다. 입력이 필요한 작업은 `tasks/get`을 통해 완전한 내장 요청을 노출하고, 클라이언트는 원래 도구 호출을 재시도하는 게 아니라 `tasks/update`로 그것들에 답합니다. 클라이언트는 여전히 제안된 간격으로 폴링하고, 작업 생성은 서버 주도로 남습니다.

영속적인 작업 경로 상태는 작업 핸들을 키로 하는 애플리케이션 데이터이지, 프로토콜 세션이 아닙니다.

### 호환성 경계

게이트웨이가 구형 클라이언트나 백엔드를 서빙해야 한다면:

- 시대(era)를 명시적으로 감지합니다.
- 초기화, 전송 세션, GET 스트림, 리소스 구독, 구형 작업 어휘는 레거시 어댑터 안에 둡니다.
- 레거시 세션 id가 현대적 라우팅이나 인가로 새어 나가지 않게 합니다.
- 조용한 격하(downgrade)보다 상한이 있는 탐색 프로브와 명시적 폴백 정책을 선호합니다.

```figure
t3-gateway-funnel
```

## 빌드하기

`code/main.py`는 인프로세스 프로토콜 게이트웨이와 두 개의 백엔드 서버를 구현합니다. 각 백엔드는 새로운 현재 프로토콜 요청을 받습니다. 게이트웨이는 탐색, 사용자 필터링이 적용된 결정적 `tools/list`, 네임스페이스 라우팅, 레지스트리 `server.json`과 외부 심사 상태, 디스크립터 핀, RBAC, 주체 키 기반 속도 제한, 감사 결정, 모델링된 `subscriptions/listen` SSE 확인 응답을 제공합니다.

모델은 파싱된 요청 본문, 라우팅 헤더, 인증된 베어러 신원을 받습니다. 완전한 HTTP 어댑터가 아니므로 `Content-Type`이나 전체 `Accept` 계약을 파싱하지 않습니다. 레슨 09의 Streamable HTTP 어댑터에 연결하세요. 그 어댑터는 `Content-Type: application/json`과 `application/json`과 `text/event-stream`을 모두 포함하는 `Accept` 값을 요구합니다.

실행 방법:

```bash
cd phases/13-tools-and-protocols/17-mcp-gateways-and-registries
python3 code/main.py
python3 -m unittest discover code/tests -v
```

데모는 바깥쪽 요청 id와 새 백엔드 요청 id를 출력해 상태 비저장 홉(hop)이 보이게 합니다.

## 활용하기

인프로세스 백엔드 객체를 실제 현재 프로토콜 클라이언트로 교체하세요. 같은 심(seam)을 유지하세요:

- 연결 전에 심사 레코드.
- capability 노출 전에 백엔드 탐색.
- 인가 전에 정규화된 공개 이름.
- 목록이나 호출 전에 디스크립터 핀.
- 전달 전에 요청별 새 메타데이터.
- 돌려주기 전에 결과 검증.

## 출시하기

이 레슨은 `outputs/skill-gateway-bootstrap.md`를 출시합니다. 이 스킬은 인그레스, 탐색, 심사, 네임스페이스, 인가, 캐싱, 스트리밍, 구독, MRTR, Tasks, 관측 가능성(옵저버빌리티), 레거시 격리를 아우르는 현대적 게이트웨이 설계를 산출합니다.

## 연습 문제

1. 바깥쪽과 전달되는 요청 메타데이터에 트레이스 컨텍스트를 추가하고, 그 상관관계를 감사 이벤트에 기록하세요.
2. Tasks를 지원하는 백엔드를 추가하고, `Mcp-Name`의 작업 id로 `tasks/get`을 라우팅하세요.
3. 백엔드 디스크립터 하나를 바꾸고, 탐색과 직접 호출 둘 다 막히는지 증명하세요.
4. 주체별 서버 capability를 추가하고, 탐색이 private으로 캐시돼야 하는 이유를 설명하세요.
5. 현대적 `Gateway` 클래스에 어떤 레거시 상태도 추가하지 않으면서 레거시 어댑터 인터페이스를 작성하세요.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| MCP 게이트웨이 | 클라이언트와 백엔드 MCP 서버 사이의 정책·라우팅 서버 |
| 심사 레코드 | 한 백엔드의 게이트웨이 진입을 허용하는 증빙과 정책 결정 |
| 정규화된 도구 이름 | `notes.search` 같은 안정적인 공개 경로 |
| 디스크립터 핀 | 탐색과 디스패치 동안 검사되는 승인된 다이제스트 |
| private 캐시 스코프 | 하나의 인가 컨텍스트로 제한된 캐시 결과 |
| 요청 범위 SSE | 하나의 POST 요청에 붙는 스트리밍 응답 |
| `subscriptions/listen` | 선택한 장기 변경 알림을 위한 클라이언트 개설 SSE 스트림 |
| 작업 경로 | 불투명한 작업 id에서 그 백엔드로 가는 애플리케이션 매핑 |
| 레거시 어댑터 | 구형 핸드셰이크와 세션 동작을 위한 명시적 버전 게이트 경계 |

## 더 읽을거리

- [Streamable HTTP 전송](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [서버 탐색](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
- [공식 레지스트리 server.json 요구 사항](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md)
- [MCP Tasks 확장](https://tasks.extensions.modelcontextprotocol.io/specification/draft/tasks)
