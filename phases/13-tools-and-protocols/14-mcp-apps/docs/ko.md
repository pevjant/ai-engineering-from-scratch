> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 상태 없는 프로토콜 위의 MCP Apps

> 인터랙티브한 결과도 여전히 MCP 도구·리소스 교환입니다. 2026-07-28 코어가 그 교환을 자기완결적으로 만들고, Apps 확장이 샌드박스 처리된 브라우저 표면을 더합니다.

**유형:** Build(만들기)
**언어:** Python
**선수 지식:** 페이즈 13 · 07(MCP 서버), 페이즈 13 · 10(리소스)
**시간:** 약 75분

## 학습 목표

- `server/discover`와 요청별 확장 역량을 통해 MCP Apps를 광고합니다.
- 도구가 호출되기 전에 도구 위에 `ui://` 리소스를 선언합니다.
- 2026-07-28 상태 없는 와이어 위에서 완결된 도구·리소스 결과를 돌려줍니다.
- Apps의 `ui/initialize` 브리지 메시지를 제거된 MCP 코어 핸드셰이크와 분리합니다.
- 오리진(origin) 검증, 샌드박싱, CSP, 최소 권한을 적용합니다.

## 문제

텍스트 결과는 타임라인을 "설명"할 수 있습니다. 하지만 사용자가 필터링하고, 들여다보고, 행동할 수 있는 타임라인을 "줄" 수는 없습니다.

MCP Apps는 선택적 확장으로 이 표현 문제를 해결합니다. 도구 정의가 `ui://` 리소스를 가리킵니다. 호스트는 도구가 실행되기 전에 그 리소스를 내려받아 검토하고, 샌드박스 처리된 iframe에 렌더링하고, 앱의 모든 동작을 JSON-RPC 브리지로 중재합니다.

코어 프로토콜은 2026-07-28에서 바뀌었습니다. 앱을 구식 연결 수명 주기로 감싸지 마세요:

- 코어 `initialize` 요청도 `notifications/initialized` 알림도 없습니다.
- `Mcp-Session-Id` 헤더도 없습니다.
- 모든 요청이 `params._meta`로 프로토콜 버전과 클라이언트 역량을 실어 나릅니다.
- 서버는 `server/discover`를 구현해 클라이언트가 버전, 코어 역량, 확장을 들여다볼 수 있게 합니다.
- 모든 성공 결과에는 `resultType` 판별자가 있습니다.
- Streamable HTTP는 요청당 하나의 POST를 사용합니다. 현대식 GET과 DELETE 진입점은 405를 돌려줍니다.

Apps 브리지에는 여전히 `ui/initialize`라는 메서드가 있습니다. 이것은 iframe postMessage 방언에 속하며, 코어 MCP 세션을 다시 만들지 않습니다.

## 개념

### 두 프로토콜, 하나의 기능

계층을 명시적으로 유지하세요:

1. MCP 코어는 `server/discover`, `tools/list`, `tools/call`, `resources/list`, `resources/read`를 실어 나릅니다.
2. MCP Apps 확장은 UI를 선언하고 iframe↔호스트 브리지를 정의합니다.
3. 브라우저 샌드박스 규칙이 UI가 닿을 수 있는 범위를 제한합니다.

확장 식별자는 `io.modelcontextprotocol/ui`입니다. 양쪽 피어 모두 옵트인합니다. 클라이언트는 요청마다 capabilities 객체 안에 확장 지원을 실어 보냅니다:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "server/discover",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {
          "io.modelcontextprotocol/ui": {}
        }
      },
      "io.modelcontextprotocol/clientInfo": {
        "name": "timeline-host",
        "version": "1.0.0"
      }
    }
  }
}
```

`clientInfo`는 진단을 위해 권장됩니다. 스스로 보고한 데이터일 뿐, 권한 부여 신원이 아닙니다.

### 렌더링 전에 디스커버리

서버의 디스커버리 결과가 확장을 광고합니다:

```json
{
  "resultType": "complete",
  "supportedVersions": ["2026-07-28"],
  "capabilities": {
    "tools": {},
    "resources": {},
    "extensions": {
      "io.modelcontextprotocol/ui": {}
    }
  },
  "ttlMs": 300000,
  "cacheScope": "public",
  "_meta": {
    "io.modelcontextprotocol/serverInfo": {
      "name": "timeline-app-server",
      "version": "2.0.0"
    }
  }
}
```

서버는 디스커버리를 지원해야 합니다. 클라이언트는 모든 동작 전에 디스커버리를 부를 의무는 없습니다. 각 동작이 자기 역량을 실어 나르기 때문입니다.

### 도구 정의에 UI를 선언한다

현대의 Apps 계약은 `tools/list`에서 UI를 도구에 묶습니다:

```json
{
  "name": "notes_timeline",
  "description": "Render a timeline of notes.",
  "inputSchema": {
    "type": "object",
    "properties": {}
  },
  "_meta": {
    "ui": {
      "resourceUri": "ui://notes/timeline.html"
    }
  }
}
```

이것은 의도적으로 호출 전(pre-call) 메타데이터입니다. 호스트는 결과가 표시를 요구하기 전에 HTML을 미리 내려받고, 캐시하고, 보안 검토할 수 있습니다. 구식 평평한(flat) 메타데이터 키는 호환 코드가 받아들일 수 있지만, 새 서버는 중첩된 `_meta.ui.resourceUri` 형태를 내보내야 합니다.

`tools/list`는 현재 코어에서 캐시 가능합니다. 결정론적 정렬, `ttlMs`, `cacheScope`를 포함하세요. 보이는 도구가 사용자나 토큰에 따라 달라진다면 `private`을 쓰세요.

### 데이터를 돌려주고, 뷰 바인딩은 호스트에 맡긴다

도구 호출은 평범한 콘텐츠와 구조화된 데이터를 돌려줍니다:

```json
{
  "resultType": "complete",
  "content": [
    {"type": "text", "text": "Timeline ready."}
  ],
  "structuredContent": {
    "notes": [
      {"id": "note-1", "title": "Discover", "created": "2026-07-28"}
    ]
  },
  "isError": false
}
```

호스트는 어떤 뷰가 도구에 속하는지 이미 알고 있습니다. URI를 반복하려고 새 콘텐츠 블록을 발명하지 마세요.

### 앱을 리소스로 서빙한다

서버는 디스커버리에서 `resources`를 광고하므로, 필수인 `resources/list` 연산도 구현합니다. 결정론적 목록 항목에는 정규(canonical) URI, 안정적인 이름, 설명, MIME 타입이 들어갑니다. 목록 결과에는 결정론적 도구 목록과 마찬가지로 `resultType`, 서버 식별 메타데이터, `ttlMs`, `cacheScope`가 포함됩니다.

호스트는 `resources/read`를 보냅니다. Streamable HTTP에서 요청은 다음과 같습니다:

```text
POST /mcp
MCP-Protocol-Version: 2026-07-28
Mcp-Method: resources/read
Mcp-Name: ui://notes/timeline.html
```

헤더 값과 JSON-RPC 본문은 서로 일치해야 합니다. 어긋나면 프로토콜 오류 `-32020`입니다.

결과에는 HTML 리소스와 캐시 힌트가 담깁니다:

```json
{
  "resultType": "complete",
  "contents": [
    {
      "uri": "ui://notes/timeline.html",
      "mimeType": "text/html;profile=mcp-app",
      "text": "<!doctype html>...",
      "_meta": {
        "ui": {
          "csp": {
            "connectDomains": [],
            "resourceDomains": [],
            "frameDomains": [],
            "baseUriDomains": []
          },
          "permissions": {}
        }
      }
    }
  ],
  "ttlMs": 60000,
  "cacheScope": "public"
}
```

### UI 리소스는 실행 가능한 콘텐츠로 캐시한다

앱 리소스는 평범한 산문과 호환되지 않습니다. 그 캐시 항목은 브리지 코드를 실행하고, 도구 데이터를 렌더링하고, 호스트 중재 동작을 요구할 수 있습니다. 캐시 키는 정규 `ui://` URI, 승인된 서버 식별과 버전, 리소스 콘텐츠 다이제스트, 그리고 `cacheScope`가 private일 때는 권한 컨텍스트로 구성하세요. URI가 같아도 HTML이나 정책 메타데이터가 다를 수 있으므로, 비공개 앱 리소스를 주체(principal)들 사이에서 재사용하지 마세요.

캐시 항목은 `ttlMs`가 만료되거나, 도구의 `_meta.ui.resourceUri` 바인딩이 바뀌거나, 서버 버전이나 승인된 디스크립터 핀이 바뀌거나, 승인된 리소스 변경 구독이 그 URI를 가리킬 때 무효화하세요. 다시 마운트하기 전에 재내려받기와 CSP·권한 검토를 다시 적용하세요. 낡은(stale) iframe이 단지 새 리소스 버전이 아직 로드되지 않았다는 이유로 더 넓은 권한을 유지해서는 안 됩니다.

### 기능 정책 이전에 와이어 모호성을 거부한다

검증에는 의도된 순서가 있습니다. 먼저 JSON-RPC 형태를 검증하고 문자열 프로토콜 메타데이터와 객체형 클라이언트 역량 맵을 요구합니다. 다음으로 라우팅 헤더와 본문을 비교합니다. 그런 다음에야 일치한 프로토콜 버전이 지원되는지 판단합니다. 이 순서는 프록시와 서버가 서로 다른 요청으로 해석하는 사고를 막아 줍니다.

| 조건 | HTTP | JSON-RPC 오류 |
|-----------|------|----------------|
| 헤더와 본문의 버전·메서드·이름 불일치 | 400 | `-32020` |
| 헤더와 본문이 미지원 버전으로 일치 | 400 | `-32022`, `data`는 정확히 `{"supported":["2026-07-28"],"requested":"<actual>"}` |
| `resources/read`에 Apps 확장 역량이 없음 | 400 | `-32021`, `data.requiredCapabilities.extensions.io.modelcontextprotocol/ui` 포함 |
| 알 수 없는 메서드 | 404 | `-32601` |

JSON-RPC 알림에는 `id`가 없으므로 서버는 알림에 절대 JSON-RPC 응답을 내보내지 않습니다. 수락된 HTTP 알림은 빈 본문의 202를 돌려줍니다. 오류가 HTTP 상태를 바꿀 수는 있어도, 알림에 JSON-RPC 오류 본문을 만들 수는 없습니다.

### 샌드박스는 경계이지 신뢰 판정이 아니다

호스트가 iframe을 통제합니다. 앱은 호스트의 쿠키, 로컬 스토리지, 페이지 DOM을 직접 읽을 수 없습니다. 모든 권한 작업은 브리지를 넘어야 합니다.

다음 기본값을 쓰세요:

- CSP 도메인 목록을 모두 비워 두고, 앱이 필요로 하는 오리진만 추가하세요. fetch·XHR·WebSocket에는 `connectDomains`, 스크립트·스타일·이미지·폰트에는 `resourceDomains`를 씁니다.
- 실현 가능하면 코드와 데이터를 함께 번들하세요.
- 눈에 보이는 기능이 필요로 하지 않는 한 카메라, 마이크, 위치 권한을 요청하지 마세요.
- `postMessage`를 정확한 피어 오리진에 고정(pin)하고 다른 모든 오리진의 이벤트를 거부하세요.
- 도구 인자, 도구 결과, 리소스 텍스트, 브리지 메시지를 신뢰할 수 없는 입력으로 다루세요.
- 사용자 동의는 호스트에 두세요. iframe은 스스로 결과가 큰(consequential) 동작을 승인할 수 없습니다.

튜토리얼의 고정된 `sandbox` 속성을 모든 호스트에 복사하지 마세요. 호스트는 앱의 오리진 모델과 자신의 격리 설계에 따라 플래그를 골라야 합니다.

허용된 도메인도 여전히 유출 경로입니다. `connectDomains: ["https://api.example.com"]`은 앱 안에서 실행되는 모든 스크립트가 허용된 데이터를 그곳으로 보낼 수 있다는 뜻입니다. 정확한 오리진 매칭은 목적지 혼동을 막을 뿐, 페이로드가 적절한지는 판단하지 못합니다. 연결 접근은 기본값으로 비워 두고, 베어러 토큰을 iframe에 두지 말고, 실현 가능하면 좁은 연산을 호스트를 통해 프록시하고, 응답·요청 크기를 제한하며, 어떤 사용자 동작이 각 외부 요청을 낳았는지 감사하세요. `resourceDomains`는 `connectDomains`와 별도로 다루세요. 폰트나 스크립트를 로드할 권한이 임의의 데이터 업로드 권한을 줘서는 안 됩니다.

### Apps 브리지에는 자체 수명 주기가 있다

Apps 브리지는 `postMessage` 위의 JSON-RPC 방언입니다. `ui/initialize`와 `ui/*` 알림을 주고받을 수 있고, `tools/call` 같은 코어처럼 보이는 메서드를 프록시할 수 있습니다.

뷰(View)는 `appInfo`와 `appCapabilities` 객체로 `ui/initialize`를 보냅니다. 호스트는 자신의 역량과 호스트 컨텍스트를 돌려줍니다. 그 응답 이후에만 뷰가 `ui/notifications/initialized`를 보냅니다. 호스트는 이 Apps 알림을 기다린 뒤에야 뷰에게 메시지를 보내야 합니다.

그 로컬 핸드셰이크는 하나의 iframe과 하나의 호스트 프레임 사이에 브리지를 만들 뿐입니다. MCP 프로토콜 버전을 협상하지 않고, 서버 상태를 만들지 않고, 전송 세션을 발급하지 않습니다. 정확한 접두사에 주목하세요. 코어 `notifications/initialized`는 제거되었고, Apps의 `ui/notifications/initialized`는 남아 있습니다. 브리지된 도구 호출이 만든 코어 요청은 새 JSON-RPC id와 완전한 요청 메타데이터를 갖춘 새로운 자기완결적 요청입니다.

### 호스트 컨텍스트, 동작, 권한 회수

브리지 초기화 이후에도 권위는 호스트에 남습니다. 뷰는 도구 동작, 내비게이션, 클립보드 사용 또는 다른 권한 효과를 호스트가 광고한 역량을 통해서만 요구할 수 있습니다. 호스트는 타입이 지정된 요청, 현재 사용자, 대상, 인자를 검증하고, 승인 정책을 적용하며, 거부할 수 있습니다. 버튼 클릭과 유효한 브리지 메시지는 의도를 표현할 뿐, 권한을 부여하지 않습니다.

테마, 크기, 접근성은 일회성 렌더 입력이 아니라 변하는 호스트 컨텍스트로 다루세요:

- 호스트가 제공한 색·타이포그래피 토큰을 적용하고, 테마나 명암 선호가 바뀌면 반응합니다.
- 뷰가 원하는 크기를 보고하게 하되, iframe 크기는 호스트가 상한을 두고 적용해 콘텐츠가 레이아웃을 탈출하거나 기만적인 오버레이를 만들지 못하게 합니다.
- iframe 안에서 키보드 순서, 보이는 포커스, 접근 가능한 이름, 스크린 리더 상태, 충분한 명암, 확대, 모션 줄이기 동작을 보존하세요.
- 크기 조절과 재렌더링 이후에도 호스트 컨트롤과 뷰 컨트롤 사이의 포커스 이동을 다시 테스트하세요.

사용자가 계정을 바꾸거나, 정책이 바뀌거나, 서버가 격리되거나, 호스트가 동의를 좁히는 동안에도 앱이 열려 있으면 역량을 회수할 수 있습니다. 역량과 권한은 `ui/initialize` 때만이 아니라 동작 시점에 검사하세요. 회수 시에는 대기 중인 권한 호출을 거부하고, 정책에 더 이상 맞지 않는 네트워크 활동을 멈추고, 민감하게 렌더링된 상태를 지우고, UI 리소스 자체가 더 이상 승인되지 않으면 리마운트하거나 텍스트로 폴백하세요. 뷰는 거부를 정상 결과로 다뤄야 하며, 호스트가 굴복할 때까지 재시도해서는 안 됩니다.

### 폴백도 계약의 일부다

Apps를 아는 서버라도 UI 확장을 광고하지 않는 호스트를 섬길 수 있습니다:

- `tools/list`에서 `_meta.ui` 없이 같은 도구를 돌려줍니다.
- `tools/call`에는 유용한 텍스트 결과를 유지합니다.
- UI에 대한 `resources/read`는 역량 누락 오류로 거부합니다.
- 도구 완료 여부를 판단할 때 iframe이 존재한다고 가정하지 않습니다.

```figure
t3-ui-sandbox
```

## 만들기

`code/main.py`는 SDK 없이 작은 프로세스 내 프로토콜 모델을 만듭니다. 현재 요청 봉투와 Streamable HTTP 라우팅 값을 검증하고, `server/discover`로 Apps를 광고하고, 도구와 리소스를 나열하고, 도구를 실행하고, 자기완결적인 HTML 리소스를 서빙합니다.

이 모델은 이미 파싱된 본문과 라우팅 헤더를 받습니다. 완전한 HTTP 어댑터가 아니며 `Content-Type`이나 `Accept`를 파싱하지 않습니다. `Content-Type: application/json`과 `application/json`과 `text/event-stream`을 모두 포함하는 `Accept` 값을 요구하는 완전한 Streamable HTTP 어댑터는 레슨 09를 사용하세요.

실행:

```bash
cd phases/13-tools-and-protocols/14-mcp-apps
python3 code/main.py
python3 -m unittest discover code/tests -v
```

출력에서 네 가지를 확인하세요:

1. 모든 호출이 독립적입니다.
2. 모든 요청이 `_meta` 역량을 갖습니다.
3. `resources/list`가 어떤 리소스 읽기보다 먼저 안정적인 디스크립터를 돌려줍니다.
4. 모든 결과가 `resultType`과 서버 식별 메타데이터를 갖습니다.
5. 어떤 코어 세션 식별자도 등장하지 않습니다.

## 사용하기

`server/discover`부터 시작하세요. 서버 확장 맵에 `io.modelcontextprotocol/ui`가 나타나는지 확인합니다. 그다음 `tools/list`를 두 번 부르세요. 한 번은 Apps 역량과 함께, 한 번은 없이. 첫 응답은 리소스를 선언합니다. 두 번째는 여전히 쓸 수 있는 텍스트 전용 도구로 남습니다.

`ui://notes/timeline.html`을 읽으세요. HTML에서 `hostOrigin`과 `event.origin` 가드를 찾으세요. 그 두 줄이 브리지가 와일드카드 대상을 쓰지 않는다는 최소한의 눈에 보이는 증거입니다.

## 출시하기

이 레슨은 `outputs/skill-mcp-apps-spec.md`를 제공합니다. 프레임워크 코드를 쓰기 전에 앱 계약을 검토하는 데 사용하세요. 작성자에게 현재 코어 봉투, 확장 협상, 폴백, UI 리소스, 캐시 정책, CSP, 권한, 브리지 메서드, 동의 경계를 명시하도록 강제합니다.

## 연습 문제

1. 클라이언트 역량을 빈 확장 맵으로 바꾸세요. `tools/list`가 도구는 유지하되 UI 바인딩을 제거하는지 확인합니다.
2. 타임라인을 읽는 본문과 함께 `Mcp-Name: ui://notes/other.html`을 보내세요. 오류 `-32020`을 확인합니다.
3. 리소스를 `cacheScope: private`으로 바꾸세요. 그것을 정당화하는 사용자별 조건을 설명합니다.
4. 스크립트를 `https://static.example.com/app.js`로 옮기세요. 그 오리진을 `resourceDomains`에 추가하고 새로 생기는 공급망 위험을 설명합니다.
5. `notes_open` 도구를 추가하고 버튼 클릭을 호스트를 통해 라우팅하세요. 사용자 승인은 호스트에 유지합니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| MCP Apps | MCP 호스트가 렌더링하는 인터랙티브 HTML을 위한 선택적 확장 |
| `io.modelcontextprotocol/ui` | 양쪽 피어가 광고하는 확장 식별자 |
| `ui://` | 앱의 UI 템플릿을 위한 리소스 스킴 |
| `text/html;profile=mcp-app` | MCP 앱 HTML을 위한 MIME 타입 |
| `server/discover` | 프로토콜·역량 디스커버리를 위한 현재 RPC |
| `resources/list` | 서버가 리소스를 광고할 때 필수인 리소스 나열 메서드 |
| `resultType` | 현대적 성공 결과에 필수인 판별자 |
| `ui/initialize` | 첫 Apps 브리지 요청. 제거된 코어 초기화와 별개 |
| `ui/notifications/initialized` | 호스트 응답 이후에 뷰가 보내는 Apps 준비 완료 알림 |
| CSP | 스크립트·스타일·이미지·네트워크 오리진을 제한하는 브라우저 정책 |
| 텍스트 폴백 | Apps 지원이 없는 호스트를 위해 유지되는 도구 동작 |

## 더 읽을거리

- [MCP 2026-07-28 base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic)
- [MCP Apps overview](https://modelcontextprotocol.io/extensions/apps/overview)
- [MCP Apps build guide](https://modelcontextprotocol.io/extensions/apps/build)
- [Official extension support matrix](https://modelcontextprotocol.io/extensions/client-matrix)
