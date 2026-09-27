# 대화 안의 대화형 인터페이스

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 도구 결과가 텍스트에서 멈출 필요는 없습니다. 서버는 작은 HTML 인터페이스를 가리키고 호스트가 그것을 렌더링하게 할 수 있습니다. 이미 대화가 벌어지고 있는 바로 그 자리에, 샌드박스 처리된 채로요.

**유형:** 참고 자료
**언어:** Python
**선수 지식:** 레슨 30
**시간:** 약 45분

## 학습 목표

- 대화형 인터페이스가 도구의 평범한 텍스트·구조화 콘텐츠 너머에서 무엇을 더하는지 설명하고, 그것을 집어 드는 것이 값을 하는 사용 사례를 알아봅니다
- `io.modelcontextprotocol/ui` 확장을 요청별로 협상하고, 도구의 `_meta.ui.resourceUri`에서 출발한 `ui://` 리소스가 평범한 `resources/read` 호출을 통과하는 과정을 추적합니다
- UI 리소스의 `_meta.ui.csp` 도메인 목록과 `_meta.ui.permissions` 플래그를 읽고, 호스트가 강제해야 할 Content Security Policy — 그 제한적인 기본값까지 포함해 — 를 구성합니다
- 도구의 `visibility`를 강제해서, 에이전트의 도구 목록과 앱 자신의 `tools/call` 요청이 각자 볼 수 있는 것만 보게 합니다
- 샌드박스 처리된 iframe 보안 모델과 앱-호스트 브리지, 그리고 앱이 시작한 도구 호출조차 동의 경계를 넘어야 하는 이유를 설명합니다
- UI 기능이 있는 도구가 확장을 선언하지 않는 호스트에서도 계속 동작하도록 폴백을 설계합니다

## 문제 상황

"지역별 매출 보여 줘"라는 요청에 답하는 대시보드 도구는 숫자 단락을 돌려줄 수도 있고, `structuredContent`에 감싼 작은 표를 돌려줄 수도 있습니다. 그러나 어느 쪽도 사용자가 지역을 클릭해 파고들거나, 막대에 마우스를 올려 정확한 수치를 보거나, 클릭할 때마다 모델에게 도구를 다시 실행해 달라고 부탁하지 않고 지표 사이를 넘나드는 것을 허용하지 않습니다. 설정 도구는 다른 방향에서 같은 천장에 부딪힙니다: "어느 지역, 어느 인스턴스 크기, 오토스케일링 할까 말까"를 주고받는 대화로 풀어내는 것은, 기본값과 검증이 앞에 보이는 양식 하나를 사용자가 한 번에 채우는 것보다 느리고 실수하기 쉽습니다.

텍스트와 구조화 콘텐츠는 여전히 대부분의 도구에 옳은 선택입니다. 그것들이 남기는 간극은 좁지만 실재합니다: 사용자가 읽기만 하는 것이 아니라 탐험하고 싶은 결과, 그리고 한 번에 하나씩 묻는 대신 모든 것이 한눈에 보인 채 내리고 싶은 선택들. MCP Apps는 선택적 확장으로 그 간극을 메웁니다. 새 전송 방식이나 MCP 곁에 우뚝 선 두 번째 프로토콜이 아니요. 이 트랙이 이미 다루는 두 프리미티브 — 도구와 리소스 — 를 재사용하고, 호스트가 가져온 것을 어떻게 렌더링하는지에 대한 규칙 하나를 더할 뿐입니다.

## 핵심 개념

확장 식별자는 `io.modelcontextprotocol/ui`입니다. 모든 확장이 협상되는 방식 그대로 협상됩니다. 레슨 30이 확장 일반에 대해 짚어 준 바로 그 요청별 선언이요: 클라이언트는 보내는 요청의 `io.modelcontextprotocol/clientCapabilities.extensions`에 지원을 선언하고, 서버는 `server/discover`의 `capabilities.extensions`에 자기 지원을 선언합니다. 확장 선언은 이전 요청에 의존하지 않습니다. 프로토콜 버전과 다른 모든 기능과 마찬가지로 요청별입니다.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "server/discover",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {"io.modelcontextprotocol/ui": {}}
      }
    }
  }
}
```

확장을 지원하는 서버는 `capabilities.extensions`에 같은 식별자를 이름 대며 답합니다. 이미 광고하는 `tools`와 `resources` 기능들 곁에요. 그 답은 호출자가 무엇을 선언했는지에도 의존하지 않습니다: `server/discover`는 서버가 할 수 있는 것을 보고하고, 클라이언트는 그것을 자신이 지원하는 것과 교집합을 구해 실제로 쓸 수 있는 것을 가려 냅니다. 확장을 선언하지 않은 호스트도 동일한 발견 결과를 받습니다. 그저 자신이 구현하지 않는 확장을 이름 대는 부분에는 아무런 조치도 취하지 않을 뿐입니다.

UI 기능이 있는 도구는 정의에 필드 하나를 더 실습니다: `_meta.ui.resourceUri`. `ui://` 리소스를 가리킵니다. 이것은 도구별 정적 메타데이터로, 모든 클라이언트가 받는 같은 `tools/list` 항목의 일부입니다. 그래서 묻는 사람에 따라 달라지지 않습니다. 도구 정의의 나머지 부분이 그렇듯이요. 결합(binding)이 도구가 호출되기도 전에 보이므로, 호스트는 모델이 도구를 호출하기로 결정한 뒤에야 발견하는 대신 미리 리소스를 내려받아 검토해 둘 수 있습니다.

도구의 `_meta.ui`는 `visibility`도 실을 수 있는데, 필드가 없으면 `["model", "app"]`이 기본입니다. `"model"`에 보이는 도구는 에이전트가 보고 호출을 결정할 수 있는 도구입니다. 레슨 11부터 이 트랙이 다뤄 온 평범한 경우죠. `"app"`에 보이는 도구는 렌더링된 앱 자신이, 브리지를 통해, 모델에게 차례를 내주라고 부탁하지 않고 직접 호출할 수 있는 도구입니다. 둘은 서로 독립적인 관문으로, 호스트가 서로 다른 두 목록에 강제합니다. visibility가 `"model"`을 뺀 도구는 에이전트 자신의 도구 목록에 아예 나타나지 않고, visibility가 `"app"`을 뺀 도구는 모델에게는 평소처럼 보이지만 호스트가 앱이 그 도구를 향해 시도하는 `tools/call`을 거부합니다. 앱 전용 도구 — 그 서버가 앱 자신의 서버와 일치하지 않는 도구 — 를 향한 교차 서버 호출은 visibility와 무관하게 완전히 차단됩니다.

그 리소스를 가져오는 데는 특별한 메서드가 없습니다. 호스트는 다른 어떤 리소스를 읽듯 `resources/read`로 읽고, 결과는 `mimeType`이 정확히 `text/html;profile=mcp-app`으로 설정되어 있어야 합니다. 그 profile 매개변수가 문서를 브라우저가 우연히 열 수 있는 아무 HTML 페이지가 아니라 렌더링 가능한 앱으로 표시하는 것입니다. 평범한 `text/html`로 답하는 리소스는 마크업이 아무리 잘 갖춰져도 그것이 아니고, 신중한 호스트는 `ui://` 스킴만 믿지 않고 매 가져오기마다 mime 타입을 검사합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "resultType": "complete",
    "contents": [
      {
        "uri": "ui://dashboard/sales-by-region.html",
        "mimeType": "text/html;profile=mcp-app",
        "text": "<!doctype html>...",
        "_meta": {
          "ui": {
            "csp": {
              "connectDomains": ["https://api.sales-metrics.example"],
              "resourceDomains": ["https://cdn.trusted-charts.example"]
            },
            "permissions": {"camera": {}, "geolocation": {}},
            "prefersBorder": true
          }
        }
      }
    ],
    "ttlMs": 60000,
    "cacheScope": "public"
  }
}
```

같은 리소스가 호스트가 어떻게 렌더링해도 되는지를 다스리는 필드들을 실는데, 전부 `_meta.ui` 안에 있습니다. `csp`는 평평한 목록이 아니라 객체입니다: `connectDomains`는 fetch, XHR, WebSocket을 덮고, `resourceDomains`는 스크립트·스타일·이미지·폰트를 덮으며, `frameDomains`는 중첩 iframe을, `baseUriDomains`는 문서 자신의 base URI를 덮습니다. 모든 키는 선택 사항입니다. 호스트는 반드시(MUST) 리소스가 선언한 도메인들 정확히로 Content Security Policy를 구성하고, 리소스가 이름 대지 않은 도메인을 허용해서는 안 됩니다(MUST NOT). 도메인을 선언하는 것이 그것을 얻는 것과 같지는 않습니다. 호스트는 자기 정책 문제로 실제로 존중할 것을 더 제한해도 됩니다(MAY). 회선이 실패해서가 아니요요. `csp`가 아예 생략되면 호스트는 반드시 제한적인 기본값으로 폴백해야 합니다. 같은 오리진 콘텐츠와 인라인 스타일·스크립트만 허용하고 아웃바운드 연결은 전혀 없는 값이죠. `frameDomains`가 없으면 항상 `frame-src 'none'`을 뜻하고, `baseUriDomains`가 없으면 항상 `base-uri 'self'`를 뜻합니다. `csp`의 나머지가 있든 없든요. 호스트는 나중 보안 검토를 위해 최종 구성한 CSP를 기록해 두는 것이 좋습니다(SHOULD).

`permissions`는 두 번째 객체로, 기능당 하나의 선택적 빈 객체 플래그입니다: `camera`, `microphone`, `geolocation`, `clipboardWrite`. 호스트는 iframe의 `allow` 속성을 그에 맞게 설정해 이것들을 존중해도 되고(MAY), 앱은 요청한 권한이 실제로 부여됐다고 가정해서는 안 됩니다(SHOULD NOT). 권한 프롬프트가 거부될 때 웹 페이지가 그러듯 성능을 낮춥니다. 렌더링은 mime 타입에서 기다리듯 권한에서 기다리지 않습니다: 호스트가 부여하지 않을 권한을 요구하는 리소스도 그 능력 없이 그냥 렌더링됩니다.

일단 렌더링되면 앱과 호스트는 자기들만의 JSON-RPC 방언으로 이야기합니다. `postMessage` 위를 타고 가고, 이 커리큘럼이 평소 다루는 클라이언트-서버 연결 위를 타고 가지 않습니다. 그 메시지 일부는 핵심 프로토콜과 이름을 공유합니다 — `tools/call` 같은 것. 대부분은 새 것이고 `ui/` 접두사가 붙습니다. `ui/initialize` 같은 것이요. 하나의 iframe과 그것을 담는 호스트 프레임 사이의 채널을 세우는 메시지죠. 그 로컬 핸드셰이크는 2026-07-28에는 존재하지 않는 핵심 `initialize` 요청과 무관합니다. 프로토콜 버전을 협상하지도, 세션을 만들지도, 레슨 04부터 이 트랙이 다뤄 온 상태 없는(stateless) 클라이언트-서버 회선을 건드리지도 않습니다. 호스트가 웹 페이지라면 뷰와 직접 이야기해서도 안 됩니다(MUST NOT): 뷰를 자신과 다른 오리진의 중간 샌드박스 프록시로 감싸고, 그 프록시가 실제로 브리지 메시지를 양방향으로 전달합니다.

그 브리지를 통해 앱은 호스트에게 자기를 대신한 도구 호출을 부탁할 수 있습니다. 다만 애초에 visibility에 `"app"`을 포함하는 도구에 한해서요. 결정하는 것은 여전히 호스트입니다: 같은 동의를 거친 뒤에야 — 사용자가 어떤 도구 호출에든 적용할 그 동의 — 새로운 id와 온전한 `_meta`로 요청을 평범한 `tools/call`로 서버에 전달하고, 완전히 거절할 수도 있습니다. iframe은 자기 결과가 큰 행동을 스스로 승인할 수 없습니다. 물을 수 있을 뿐이고, 호스트가 답합니다.

평범한 링크된 웹페이지 대신 앱을 고르는 것에 대한 보안 논거의 형태도 이것입니다. iframe은 호스트 페이지의 쿠키, 로컬 스토리지, DOM을 읽을 수 없고, 부모 페이지를 탐색하거나 그 컨텍스트에서 스크립트를 돌릴 수 없습니다. 모든 특권 동작은 중개되는 브리지를 넘어야 합니다. 그 고립 덕분에 호스트는 한 줄 한 줄 감사하지 않은 서버의 앱을 안전하게 렌더링할 수 있습니다. 이미 신뢰할 수 없는 도구 결과와 리소스 텍스트를, 모델이나 사용자가 최종적으로 하는 일을 지시하지 못하게 하면서 렌더링하듯이요. 레슨 22가 이미 세워 놓은 신뢰 경계 규율입니다.

이 모든 것은 도구가 계속 동작하기 위해 필수가 아닙니다. UI 기능이 있는 도구는 모든 `tools/call`에서 여전히 유용한 `content` 텍스트 답을 돌려주고, 확장을 선언하지 않은 호스트는 그저 `ui://` 리소스를 읽지 않을 뿐입니다: 그 텍스트를 다른 어떤 도구에서 그러듯 쓰고, 확장 자신의 규칙이 적용됩니다 — 지원 없는 쪽은 요청이 실패하는 대신 핵심 동작으로 폴백한다.

```figure
mcpa-31-app-sandbox
```

## 인터랙티브 랩

그림은 하나의 도구 호출이 두 갈래를 동시에 지나가는 과정을 따라갑니다. 왼쪽에서는 확장을 선언한 호스트가 평범한 `resources/read`로 도구의 `_meta.ui.resourceUri`를 읽고, mime 타입을 검사하고, 선언된 도메인들로 — 자기 정책으로 더 좁혀서 — Content Security Policy를 구성한 뒤 샌드박스 처리된 iframe 안에서 렌더링합니다. 점선은 앱이 시작한 도구 호출이 서버에 닿기 전에, 도구 자신의 visibility 위에 얹혀 여전히 통과해야 하는 동의 관문을 표시합니다. 오른쪽에서는 확장을 선언하지 않은 호스트가 평범한 `tools/call`에서 멈추고 같은 도구의 텍스트 콘텐츠를 렌더링합니다. 리소스는 전혀 건드리지 않고요.

## 실습 랩

`code/main.py`를 열어 보세요. 하나의 서버가 하나의 대시보드 뷰에 묶인 세 도구를 노출합니다: `sales_by_region`(기본 visibility, model과 app 양쪽), `refresh_sales_view`(`visibility: ["app"]`, 에이전트에게 숨김), `export_sales_report`(`visibility: ["model"]`, 앱 안에서 도달 불가). 리소스도 넷을 노출합니다: 도구의 진짜 `ui://` 뷰, 앱 프로필 대신 평범한 `text/html`로 답하는 `legacy-widget` 리소스, 호스트 자신의 정책 밖 도메인을 CSP에 이름 대는 `scripts-widget` 리소스, `csp`를 아예 생략하는 `minimal-widget` 리소스.

```bash
python3 code/main.py
```

`HostAppLoader.load`는 같은 도구와 인자에 대해 전체 결정을 두 번 돌립니다. 확장을 선언한 채로 한 번, 선언하지 않은 채로 한 번요. 그래서 인쇄된 두 계획은 직접 비교할 수 있습니다: 하나는 실제 `resources/read`에서 만들어진 `{"mode": "app", ...}`로, 구성된 `csp` 문자열과, 리소스가 요구한 것의 진부분집합인 `grantedPermissions` 목록을 실고, 다른 하나는 그 호출 자체를 아예 발행하지 않는 `{"mode": "text", ...}`입니다. `review_app_resource`와 `build_csp`는 결함이 있고 최소화된 리소스에 별도로 돌며, 평범한 텍스트로 각각이 어느 검사를 실패하는지, 또는 어느 기본값이 적용되는지 설명합니다. 아래쪽에서 `request_tool_call_from_app`은 독립적인 두 관문을 보여 줍니다: `export_sales_report`를 향한 호출은 동의가 고려되기도 전에 visibility에 `"app"`이 없다는 이유로 거부되고, `refresh_sales_view`를 향한 호출은 거절당하면 반려되고 승인되면 새 id로 전달됩니다. 같은 도구에 대한 두 `tools/call` 항목을 비교하고, 모든 요청이 여전히 자기 `_meta` — 확장 선언 포함 — 를 실으며, 그 사이에 기억되는 것이 아무것도 없음을 확인하세요.

## 완성 산출물

`outputs/mcp-apps-review-checklist.md`는 한 페이지짜리 검토 체크리스트입니다: `ui://` 리소스를 렌더링할 만큼 신뢰하기 전에 확인할 것, UI 기능이 있는 도구가 반드시 유지해야 할 폴백, 그리고 각 검사의 결과를 렌더링·폴백·거부로 연결하는 짧은 결정 표. 도구가 `_meta.ui`를 선언할 때 서버의 도구 설명 곁에 두세요.

## 확인하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 확인합니다: 확장은 양쪽이 모두 선언할 때만 협상된다, 도구의 UI 결합은 묻는 사람이 누구든 `tools/list`에 나타난다, 생략된 `visibility`는 `"model"`과 `"app"` 양쪽이 기본이다, 에이전트 자신의 도구 목록은 앱 전용 도구를 제외한다, 확장을 아는 호스트는 정확히 하나의 `resources/read`로 리소스를 해석한다, 확장 없는 호스트는 텍스트로 폴백하며 그 호출을 아예 건너뛴다, mime 타입이 틀린 리소스는 읽기 자체가 성공하더라도 거부된다, CSP가 호스트 정책 밖 도메인을 이름 대는 리소스는 거부되며 어느 도메인인지 말한다, `build_csp`는 선언된 도메인들로 올바른 지시문을 구성하고 `csp`가 생략되면 제한적 기본값으로 폴백한다, 부여된 권한은 호스트 자신의 정책을 절대 넘지 않는다, 거절된 앱 시작 도구 호출은 회선에 절대 닿지 않는다, 승인된 것은 새 id로 전달된다, visibility가 `"app"`을 제외하는 도구를 향한 호출은 동의를 묻기도 전에 거부된다, 알려지지 않은 리소스는 프로토콜 오류이다, 그리고 모든 캐시 가능 결과는 `ttlMs`와 `cacheScope`를 실는다. 저장소의 와이어 검사기도 이 레슨의 실행 기록을 2026-07-28 규칙과 대조해 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/31-mcp-apps
```

## 캡스톤 연결

캡스톤의 엔드투엔드 교환은 그 호출들 사이에 UI 기능이 있는 도구를 포함할 수 있고, 이 레슨이 제기하는 모든 질문이 거기서도 여전히 적용됩니다: 이 요청에서 확장이 실제로 협상됐는가, 무언가 렌더링되기 전에 가져온 리소스가 정확한 mime 타입을 실었는가, 그리고 앱이 시작한 호출이 캡스톤이 이미 다른 모든 도구 호출에 강제하는 바로 그 동의 관문을 여전히 넘는가.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| MCP Apps | 도구가 호스트가 렌더링하는 대화형 HTML 인터페이스를 가리킬 수 있게 하는 선택적 확장 |
| `io.modelcontextprotocol/ui` | 클라이언트와 서버가 MCP Apps를 협상하려고 선언하는 확장 식별자 |
| `ui://` | 앱의 UI 리소스를 위해 예약된 URI 스킴 |
| `_meta.ui.resourceUri` | 도구 정의에서 그 도구의 `ui://` 리소스를 가리키는 필드 |
| `text/html;profile=mcp-app` | 가져온 리소스를 렌더링 가능한 앱으로 표시하는 정확한 mime 타입 |
| `_meta.ui.csp` | 호스트가 Content Security Policy를 구성하는 근거가 되는 선택적 도메인 목록들(`connectDomains`, `resourceDomains`, `frameDomains`, `baseUriDomains`)의 객체 |
| `_meta.ui.permissions` | 호스트가 존중할 수 있는 선택적 빈 객체 플래그들(`camera`, `microphone`, `geolocation`, `clipboardWrite`)의 객체 |
| `visibility` | 도구의 `_meta.ui` 배열. 기본 `["model", "app"]`. 에이전트의 도구 목록과 앱 자신의 `tools/call` 요청을 각각 따로 관문 친다 |
| 샌드박스 iframe(Sandboxed iframe) | 호스트가 앱을 렌더링하는 고립된 프레임. 호스트 페이지에 직접 접근할 수 없다 |
| 샌드박스 프록시(Sandbox proxy) | 웹 호스트가 자신과 렌더링된 뷰 사이에 반드시 써야 할(MUST) 다른 오리진의 중개자 |
| 앱-호스트 브리지(App-to-host bridge) | 앱과 호스트가 쓰는 `postMessage` 위의 JSON-RPC 방언. 클라이언트-서버 회선과는 별개다 |
| 텍스트 폴백(Text fallback) | UI 기능이 있는 도구가 확장 없는 호스트에게 여전히 돌려주는 평범한 `content` 결과 |

## 더 읽기

- [MCP Apps 개요](https://modelcontextprotocol.io/extensions/apps/overview)
- [MCP App 만들기](https://modelcontextprotocol.io/extensions/apps/build)
- [SEP-1865: MCP Apps, MCP를 위한 대화형 사용자 인터페이스](https://modelcontextprotocol.io/seps/1865-mcp-apps-interactive-user-interfaces-for-mcp)
- [MCP Apps 사양, 2026-01-26](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 14절
- `phases/13-tools-and-protocols/14-mcp-apps`, 같은 확장을 둘러싸고 완전한 요청·리소스 서버와 더 엄격한 Streamable HTTP 어댑터를 만드는 글
