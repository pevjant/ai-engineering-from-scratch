> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# Model Context Protocol (MCP)

> MCP는 AI 호스트에게 도구, 리소스, 프롬프트를 탐색하고 호출하는 단 하나의 프로토콜을 제공합니다. 2026-07-28 개정판은 이 프로토콜을 상태 비저장(stateless) 구조로 바꿨습니다. 기능(capability)과 버전 정보가 연결에 묶인 핸드셰이크가 아니라 모든 요청에 함께 실려 갑니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 11 · 09(함수 호출), 페이즈 11 · 03(구조화된 출력)
**소요 시간:** 약 75분

## 학습 목표

- MCP 호스트, 클라이언트, 서버, 트랜스포트, 서버 프리미티브를 구분할 수 있습니다.
- MCP 2026-07-28이 요구하는 메타데이터를 갖춘 JSON-RPC 요청을 작성할 수 있습니다.
- `server/discover`로 버전, 식별 정보, 기능을 조회할 수 있습니다.
- 도구, 리소스, 프롬프트에서 타입이 명확하고 캐시를 고려한 결과를 반환할 수 있습니다.
- 최신 상태 비저장 MCP가 핸드셰이크 시절 서버와 어떻게 상호 운용되는지 설명할 수 있습니다.
- 서버를 위해 안전한 상태, 트랜스포트, 승인 경계를 선택할 수 있습니다.

## 문제 상황

여러분의 애플리케이션에는 데이터베이스 조회, 캘린더 작업, 파일 읽기 기능이 필요합니다. 공통 프로토콜이 없다면 똑같은 기능인데도 AI 호스트마다 탐색, 호출, 오류 처리, 트랜스포트, 인가를 제각각 따로 붙여야 합니다.

MCP는 이 통합 행렬을 줄여 줍니다. 서버는 표준 JSON-RPC 인터페이스를 공개하고, 규격을 준수하는 클라이언트는 서버 전용 어댑터 없이도 그 인터페이스를 탐색하고, 모델이나 사용자에게 보여 주고, 호출하고, 결과를 해석할 수 있습니다.

놓치기 쉬운 중요한 경계가 있습니다. MCP는 통신을 표준화할 뿐입니다. 모델이 어떤 도구를 호출해야 할지 정해 주거나, 신뢰할 수 없는 콘텐츠를 안전하게 만들어 주거나, 상태 비저장 요청을 지속되는 애플리케이션 상태로 바꿔 주지는 않습니다. 그 결정은 여전히 여러분의 호스트와 서버가 직접 해야 합니다.

## 개념

![MCP 호스트, 상태 비저장 요청, 서버 프리미티브](../assets/mcp-architecture.svg)

### 세 가지 서버 프리미티브

1. **도구(Tools)**는 호출 가능한 동작입니다. 각 도구는 이름, 설명, JSON Schema 입력, 핸들러를 갖습니다.
2. **리소스(Resources)**는 클라이언트가 읽을 수 있는, 이름과 URI 주소를 가진 콘텐츠입니다.
3. **프롬프트(Prompts)**는 호스트가 사용자에게 노출할 수 있는 재사용 가능한 템플릿입니다.

호스트는 AI 애플리케이션입니다. 그 호스트 안의 MCP 클라이언트가 하나의 서버와 대화하고, 트랜스포트가 둘 사이에서 JSON-RPC 메시지를 실어 나릅니다.

### 핸드셰이크를 대체하는 상태 비저장 요청

MCP 2026-07-28은 `initialize`와 `notifications/initialized`를 없앴고, 프로토콜 수준의 세션도 없앴습니다. 이제 모든 요청이 자신을 해석하는 데 필요한 맥락을 `params._meta`에 직접 실어 나릅니다:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": {
        "name": "lesson-client",
        "version": "1.0.0"
      }
    }
  }
}
```

프로토콜 버전과 클라이언트 기능(capability)은 필수입니다. 클라이언트 식별 정보는 권장입니다. `_meta`가 없거나, 필수 필드가 빠졌거나, 필수 필드의 타입이 틀리면 잘못된 형식으로 보고 Invalid Params(`-32602`)를 반환합니다. 형식은 맞지만 서버가 지원하지 않는 버전 문자열이라면 `UnsupportedProtocolVersionError`(`-32022`)를 반환합니다. 서버는 이전 협상 기록을 다시 찾아보지 않고도 유효한 요청을 처리할 수 있습니다.

상태 비저장이라고 해서 애플리케이션이 상태를 절대 가질 수 없다는 뜻은 아닙니다. 상태가 MCP 연결이나 `Mcp-Session-Id` 뒤에 숨겨지지 않아야 한다는 뜻입니다. 워크플로에 연속성이 필요하면 서버가 불투명한(opaque) 핸들을 발급하고, 클라이언트가 이후 호출에서 그 핸들을 평범한 도구 인자로 전달하면 됩니다. 인가 확인은 여전히 요청마다 이뤄져야 합니다.

### 디스커버리와 버전 선택

모든 최신 서버는 `server/discover`를 구현합니다. 그 결과는 지원 버전, 기능, 서버 식별 정보를 알려 줍니다:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "complete",
    "supportedVersions": ["2026-07-28"],
    "capabilities": {
      "tools": {},
      "resources": {},
      "prompts": {}
    },
    "ttlMs": 3600000,
    "cacheScope": "public",
    "_meta": {
      "io.modelcontextprotocol/serverInfo": {
        "name": "demo-server",
        "version": "1.0.0"
      }
    }
  }
}
```

클라이언트가 다른 메서드를 바로 호출하고 버전 오류를 처리하는 것도 가능하지만, 디스커버리를 사용하면 기능 표시와 버전 선택이 명확해집니다. 지원하지 않는 버전은 코드 `-32022`인 `UnsupportedProtocolVersionError`를 반환하며, 그 데이터에는 서버 개정판 목록인 `supported`와 거절된 개정판인 `requested`가 들어 있습니다.

stdio에서는 두 시대를 모두 다루는(dual-era) 클라이언트가 `server/discover`로 상대를 살펴봅니다. 디스커버리 결과가 돌아오거나 `UnsupportedProtocolVersionError` 같은 인식 가능한 최신 오류가 돌아오면 최신 서버입니다. 최신 방식으로 인식되지 않는 오류나 타임아웃이라면 2025-11-25 `initialize` 흐름으로 폴백(fallback)해도 됩니다. 구식 동작은 호환성 코드일 뿐, 최신 기본값이 아닙니다.

### 결과는 명시적입니다

2026-07-28 코어 결과는 모두 `resultType`을 갖습니다:

- `complete`는 작업이 끝났다는 뜻입니다.
- `input_required`는 서버가 다중 왕복 요청(MRTR, Multi Round-Trip Requests) 패턴으로 왕복을 한 번 더 해야 한다는 뜻입니다. 코어 서버는 `tools/call`, `resources/read`, `prompts/get`에서만 이 값을 반환할 수 있습니다.

클라이언트는 `resultType`이 빠진 구버전(레거시) 결과를 `complete`로 취급해야 합니다.

서버는 모든 결과의 `_meta`에 `io.modelcontextprotocol/serverInfo`를 넣는 것이 좋습니다. 이 식별 정보는 스스로 보고한 것으로, 표시·로깅·디버깅용이지 보안 판단의 근거로 쓰면 안 됩니다.

목록(list)과 읽기(read) 결과에는 `ttlMs`와 `cacheScope`도 실려 옵니다. `tools/list` 순서가 항상 일정하고 신선도 힌트가 함께 있으면 클라이언트가 디스커버리 결과를 안전하게 캐시할 수 있고 프롬프트 캐시 안정성도 좋아집니다. `cacheScope: public`이면 캐시를 공유할 수 있고, `private`이면 호출한 맥락 안에서만 재사용할 수 있습니다.

### 와이어 포맷과 트랜스포트

MCP는 stdio 또는 Streamable HTTP 위에서 JSON-RPC 2.0을 사용합니다.

- 요청은 `jsonrpc`, `id`, `method`, `params`를 갖습니다.
- 응답은 짝이 되는 `id`와 `result` 또는 `error`를 갖습니다.
- 알림(notification)은 `id`가 없고 응답을 기대하지 않습니다.

최신 Streamable HTTP는 POST를 받는 엔드포인트 하나를 노출합니다. JSON-RPC 메시지 하나당 POST 하나씩 보냅니다. 요청 POST에는 JSON 객체 하나가 돌아오거나, 최종 응답으로 끝나는 요청 범위(request-scoped)의 SSE(Server-Sent Events) 스트림이 돌아옵니다. 정상 접수된 알림 POST는 응답 본문 없이 HTTP 202를 받습니다. 이 코어 개정판은 Streamable HTTP 위의 클라이언트→서버 알림을 정의하지 않습니다.

2026-07-28에는 독립적인 MCP GET 스트림, DELETE 세션 엔드포인트, `Mcp-Session-Id`, `Last-Event-ID` 재생(replay)이 없습니다. 오래 유지되는 변경 알림은 `subscriptions/listen` POST를 사용하며, 그 응답은 SSE 스트림으로 열린 채 유지됩니다.

### 서버 주도 요청 없이 클라이언트 입력 받기

구버전에서는 서버가 스트림을 통해 `sampling/createMessage`, `roots/list`, `elicitation/create` 같은 요청을 보낼 수 있었습니다. 현재 프로토콜은 대신 다중 왕복 요청(Multi Round-Trip Requests, MRTR)을 사용합니다. 대상이 되는 도구 호출, 리소스 읽기, 프롬프트 조회는 `resultType: input_required`를 반환하며, `inputRequests`와 `requestState` 중 최소 하나를 함께 실어 보냅니다. 클라이언트는 요청된 입력을 모아서 새 JSON-RPC ID와 그에 맞는 `inputResponses`로 원래 메서드를 재시도하고, `requestState`가 주어졌다면 그 값을 그대로 되돌려 보냅니다. `inputRequests`가 없었다면 재시도에서 `inputResponses`는 생략합니다.

Roots, Sampling, Logging은 아직 동작하지만 지원 중단(deprecated) 대상이므로 새 구현은 채택하지 않는 것이 좋습니다. 기존의 Roots나 Sampling 요청은 MRTR `inputRequests` 안에 담겨 다니며, 독립적인 서버→클라이언트 JSON-RPC 요청으로는 절대 전송되지 않습니다. 대신 명시적인 파일·디렉터리 파라미터, 리소스 URI, 서버 설정, 모델 제공사와의 직접 통합을 사용하세요. stdio 진단 메시지는 stderr로, 프로덕션(운영 환경) 텔레메트리는 OpenTelemetry를 사용하세요.

```figure
mcp-nxm-collapse
```

## 직접 만들어 보기

### 단계 1: 서버 인터페이스 등록하기

요청 규약은 바뀌었지만 등록 방법은 여전히 단순합니다:

```python
server = MCPServer("demo-server")

@server.tool(
    "add",
    "Add two integers.",
    {
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"}
        },
        "required": ["a", "b"]
    }
)
def add(a: int, b: int) -> dict:
    return {"sum": a + b}
```

저장소에 포함된 `code/main.py` 구현은 리소스와 프롬프트도 함께 등록합니다. 일부러 표준 라이브러리만 사용해서, 프로토콜을 SDK에 맡기지 않고 각 메시지 봉투(envelope)를 직접 볼 수 있게 했습니다.

### 단계 2: 모든 요청에 메타데이터 붙이기

```python
def request(method, params=None):
    body_params = dict(params or {})
    body_params["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {
            "name": "demo-client",
            "version": "1.0.0"
        }
    }
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": body_params
    }
```

이 메타데이터를 연결 객체에만 넣어 두고 재사용하면 안 됩니다. 서버는 요청마다 이를 검증합니다.

### 단계 3: (선택) 목록 조회 전에 디스커버리 먼저 하기

`server/discover`를 호출해 지원 버전을 고른 뒤 `tools/list`를 호출합니다. 버전을 이미 알고 있고 `-32022`를 처리할 수 있다면 바로 `tools/list`를 호출해도 됩니다.

데모는 도구 목록을 이름 순으로 돌려주고 `ttlMs`, `cacheScope`, `resultType`, 서버 식별 정보를 붙입니다. 도구 호출은 출력이 현재 상태에 따라 달라질 수 있으므로 `complete`이면서 캐시 불가능한 결과로 반환됩니다.

### 단계 4: 같은 요청을 HTTP로 옮기기

원격 `tools/call` POST에는 JSON-RPC 본문과 짝을 이루는 헤더가 포함됩니다:

```http
POST /mcp HTTP/1.1
Content-Type: application/json
Accept: application/json, text/event-stream
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: add
```

`MCP-Protocol-Version` 헤더는 `_meta`의 버전과 일치해야 합니다. `Mcp-Method`는 모든 JSON-RPC 요청에 필수이며 `method`와 일치해야 합니다. `Mcp-Name`은 `tools/call`, `resources/read`, `prompts/get`에서만 필수이며, 각각 도구 이름, 리소스 URI, 프롬프트 이름과 일치해야 합니다. 필수 헤더가 없거나 값이 일치하지 않으면 `HeaderMismatch` 코드 `-32020`과 함께 HTTP 400이 반환됩니다.

### 단계 5: 프로토콜 상태 밖에서 안전하게 지키기

- 모든 HTTP 요청에서 인가(authorization)와 오디언스(audience)를 검증합니다.
- 로컬 서버는 localhost에 바인딩하고, Streamable HTTP에서는 `Origin`을 검증합니다.
- 상태를 바꾸는 도구에는 `destructiveHint: true`를 표시하고 호스트 승인을 요구합니다.
- 지원 중단된 Roots에 의존하는 대신 디렉터리와 파일 범위를 명시적으로 전달합니다.
- 리소스와 도구 출력은 신뢰할 수 없는 데이터로 취급합니다.
- stdio에서는 stdout을 JSON-RPC 전용으로 남겨 두고, 진단 메시지는 stderr에 씁니다.

## 사용해 보기

레슨 디렉터리에서 실행합니다:

```bash
python3 code/main.py
cd code
python3 -m unittest discover tests -v
```

첫 줄은 프로토콜 `2026-07-28`에서 `demo-server`를 찾았다고 보고해야 합니다. 그다음 `MCPClient.request`를 살펴보세요. 매 호출마다 `_meta`를 다시 만들어 붙입니다. 요청 하나에서 메타데이터를 지우고 서버가 이를 거절하는지 확인해 보세요.

## 출시하기

`outputs/skill-mcp-server-designer.md`는 하나의 도메인을 상태 비저장 MCP 설계로 바꿔 줍니다. 이 스킬의 통과 기준에는 디스커버리 결과, 요청별 메타데이터 정책, 결정론적이면서 캐시를 고려한 목록, 명시적인 상태 핸들, 트랜스포트 헤더, 인가, 승인 규칙이 요구됩니다.

## MCP 심화 학습 이어가기

이 레슨은 프로토콜 모델을 다룹니다. 페이즈 13에서는 프로덕션(운영 환경)에서 만나는 네 가지 경계를 별개의 "만들고 검증하는" 레슨으로 나눠 다룹니다:

1. [MCP 도구 계약과 콘텐츠](../../../13-tools-and-protocols/28-mcp-tool-contracts-and-content/docs/en.md) — 닫힌 입력 스키마, 구조화된 콘텐츠, 라우팅 메타데이터, 불투명한 페이지네이션, 완료 승인, 프로토콜 오류와 도구 도메인 오류의 차이를 다룹니다.
2. [MCP 신뢰성, 취소, 흐름 제어](../../../13-tools-and-protocols/29-mcp-reliability-cancellation-and-flow-control/docs/en.md) — 요청 취소, 지속 작업 취소, 데드라인, 멱등성(idempotency), 백프레셔(backpressure), 프록시 버퍼링, 재연결 동작을 다룹니다.
3. [MCP 레지스트리 공급망, 어드미션, 드리프트, 롤백](../../../13-tools-and-protocols/30-mcp-registry-supply-chain-and-drift/docs/en.md) — 네임스페이스 증명, 산출물 출처(provenance), 불변 핀(immutable pin), 라이브 드리프트, 레지스트리 상태, 어드미션 증거, 롤백을 다룹니다.
4. [MCP 적합성 엔지니어링](../../../13-tools-and-protocols/31-mcp-conformance-versioning-and-operations/docs/en.md) — 골든 및 네거티브 와이어 트랜스크립트, 엄격한 버전 시대 구분, SDK 차이 분석, 프록시 증거, 마스킹(redaction), 헬스 게이트, 릴리스 롤백을 다룹니다.

서버가 팀이나 신뢰 경계를 넘어야 한다면 이 레슨들을 순서대로 학습하세요. 네 레슨을 마치면 "메서드가 동작한다"에서 "배포 이후에도 계약이 안전하고 진단 가능한 상태로 유지된다"로 한 단계 올라서게 됩니다.

## 연습 문제

1. `subtract` 도구를 추가하고 `tools/list`가 여전히 알파벳 순으로 정렬되는지 확인합니다.
2. 프로토콜 버전 키를 지우고 Invalid Params(`-32602`)가 돌아오는지 확인합니다. 그다음 형식은 맞지만 지원하지 않는 버전 `2025-11-25`를 보내 `-32022`를 확인하고, `requested`가 그 개정판을 그대로 돌려주는지 확인한 뒤 `supported`에서 하나를 고릅니다.
3. 생성 작업에 서버가 발급한 `draftId`를 추가하고, 업데이트에서는 그 값을 인자로 요구하게 만듭니다. 이것이 프로토콜 세션이 아니라 애플리케이션 상태인 이유를 설명합니다.
4. 사용자 확인이 필요한 도구에서 `input_required`를 반환하게 만듭니다. 서버→클라이언트 JSON-RPC 요청을 새로 만드는 대신, 새 ID와 `inputResponses` 항목, 원본 그대로의 `requestState`로 원래 호출을 재시도합니다.
5. 두 시대를 모두 다루는 stdio 클라이언트를 설계해 봅니다. 결과가 돌아오거나 인식 가능한 최신 오류가 있으면 최신 서버로 취급하고, 인식할 수 없는 오류나 타임아웃일 때만 `initialize` 폴백을 허용합니다.

## 핵심 용어

| 용어 | 흔히 하는 말 | 실제 의미 |
|------|-----------------|------------------------|
| MCP | "LLM용 도구 프로토콜" | 서버 디스커버리, 도구, 리소스, 프롬프트, 확장을 위한 JSON-RPC 프로토콜 |
| 호스트(Host) | "AI 앱" | 모델과 UI를 소유하고 하나 이상의 MCP 클라이언트를 탑재 |
| 클라이언트(Client) | "커넥터" | 호스트를 대신해 한 서버와 MCP로 대화 |
| 상태 비저장 MCP | "세션 없음" | 모든 요청이 버전과 기능을 실어 나르며, 연결을 키로 하는 프로토콜 상태가 없음 |
| `server/discover` | "기능 탐색 요청" | 버전, 기능, 식별 정보를 알려 주는 필수 서버 메서드 |
| `resultType` | "결과 상태" | 결과가 `complete`인지 `input_required`인지 표시 |
| 상태 핸들 | "워크플로 ID" | 서버가 발급해 평범한 인자로 전달되는 애플리케이션 식별자 |
| Streamable HTTP | "원격 트랜스포트" | JSON 또는 요청 범위 SSE 응답을 돌려주는 POST 엔드포인트 하나 |
| MRTR | "묻고 다시 시도" | 입력 요청을 결과에 담아 보내고, 원래 작업을 재시도하는 패턴 |

## 더 읽을거리

- [MCP 2026-07-28 주요 변경 사항](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [MCP 서버 디스커버리](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
- [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [MCP 다중 왕복 요청(Multi Round-Trip Requests)](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [MCP 지원 중단 기능](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)
