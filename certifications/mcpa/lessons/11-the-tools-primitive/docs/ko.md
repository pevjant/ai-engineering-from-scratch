> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 도구 프리미티브(primitive): 동작 호출과 결과 읽기

> 도구 호출은 다른 요청과 다를 바 없는 요청입니다. 이 레슨 하나를 독차지하게 만드는 것은 결과가 되돌려줄 수 있는 모든 것입니다. 일반 텍스트, 이미지, 오디오, 리소스 링크, 혹은 통째로 박혀 들어온 리소스까지, 각각 누구를 위한 것이고 얼마나 신선한지에 대한 힌트가 붙어 있죠.

**유형:** 참고 자료
**사용 언어:** Python
**선수 지식:** 레슨 10
**소요 시간:** 약 45분

## 학습 목표

- `tools/list` 페이지에서 페이지네이션과 캐싱 힌트를 읽고, 클라이언트가 받는 도구 목록이 어떤 커넥션이 요청했는지에 의존해서는 안 되는 이유를 설명합니다
- 도구를 호출하고 `CallToolResult`를 세 필드로 분해해 읽습니다. `content`, `structuredContent`, `isError`
- 도구 결과가 실을 수 있는 각 콘텐츠 블록 타입(text, image, audio, 리소스 링크, 내장 리소스)과 각자의 어노테이션이 묘사하는 것을 식별합니다
- 서버가 annotations 객체를 생략했을 때 각 도구 어노테이션의 기본값을 적용하고, 그 기본값이 관대함보다 신중함으로 기우는 이유를 설명합니다
- 서버의 도구 목록에 변화가 생겼을 때 그것이 이미 `subscriptions/listen` 스트림을 열어둔 클라이언트에게 어떻게 전달되는지 추적합니다

## 문제 상황

서버는 도구를 하나만 노출할 수도, 수백 개를 노출할 수도 있습니다. `tools/list`가 매번 페이지 나눔 없이 한 덩어리로 전체 집합을 돌려주고, 응답이 그 답이 얼마나 오래 유효한지에 대한 아무 약속도 실지 않는다면, 모델의 모든 턴은 아무 이득 없이 카탈로그 전체를 다시 가져오거나 이미 낡았을지 모르는 사본을 근거로 행동하게 됩니다. 요청이나 응답 어디에도 어느 쪽이 안전한 선택인지 클라이언트에게 알려주는 것은 없습니다.

도구 호출은 같은 문제의 더 날카로운 버전을 던집니다. 도구의 임무는 문장을 말하는 것일 수도, 그림을 그리는 것일 수도, 파일의 실제 바이트를 돌려주는 것일 수도 있는데, "문자열 하나를 돌려준다"는 단일 계약으로는 그중 아무것도 정직하게 묘사할 수 없습니다. 모든 결과가 한 모양으로 몰리면, 클라이언트는 돌려받은 텍스트가 모델이 읽을 것인지, 사용자가 볼 것인지, 아니면 리소스가 스스로 가져올 것인지 추측해야 하고, 완전히 실패한 호출과 모델이 아직 읽고 고쳐야 할 무언가를 돌려준 호출을 깔끔하게 구분할 방법도 없습니다.

2026-07-28 개정판은 같은 직관으로 두 문제 모두에 답합니다. 클라이언트가 추측할 필요가 아예 없도록 와이어에 충분한 구조를 부여하는 것입니다. 페이지네이션과 캐싱 힌트는 목록에 실리고, 콘텐츠는 블록 단위로 타입이 붙어 돌아오며, 호출의 실패 양상은 역으로 해부할 모양이 아니라 확인할 필드 하나가 됩니다.

## 핵심 개념

클라이언트는 `tools/list`로 서버가 무엇을 할 수 있는지 묻습니다. 요청은 이전 페이지에서 복사해 온 불투명한 `cursor`를 실을 수 있고, 맨 첫 요청은 이를 생략합니다. `tools/list`는 캐시 가능한 연산 중 하나이므로, `"complete"` 결과는 항상 정수 `ttlMs`와 `"public"` 또는 `"private"`인 `cacheScope`를 실으며, 도구가 더 남아 있다면 `nextCursor`도 함께 실립니다. 클라이언트가 들여다보지 않고 그대로 돌려보내는 또 하나의 불투명한 문자열이죠.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "resultType": "complete",
    "tools": [
      {"name": "get_readme_link", "description": "Point at the project README instead of inlining it.", "inputSchema": {"type": "object", "additionalProperties": false}}
    ],
    "nextCursor": "",
    "ttlMs": 300000,
    "cacheScope": "public"
  }
}
```

그 `nextCursor`가 빈 문자열인 것은 일부러입니다. 빈 문자열은 "더 없음"을 뜻하는 센티널이 아니라 유효한 커서 값입니다. `if result.get("nextCursor")`로 계속 페이징할지 판단하는 클라이언트는 한 페이지를 미리 멈춰버립니다. 대부분의 언어에서 빈 문자열은 거짓 같은 값(falsy)이기 때문입니다. 유일하게 올바른 검사는 키가 존재하기는 하는지입니다. 페이지네이션 자체는 처음부터 끝까지 서버의 구현 디테일입니다. 커서를 파싱하거나 디코딩하거나 증가시키는 클라이언트는, 다음 서버 버전이 예고 없이 얼마든지 바꿀 수 있는 것에 기대고 있는 셈입니다. 같은 규율이 목록의 내용에도 적용됩니다. 바뀌지 않은 도구 집합에 대해 서로 무관한 세 커넥션에서 `tools/list`를 세 번 호출하면 같은 순서로 완전히 동일하게 돌아와야 합니다. 집합이 달라질 수 있는 유일한 이유는 요청에 실린 인가가 그 호출자가 볼 수 있는 것을 바꾸었을 때뿐이며, 커넥션이 우연히 기억하고 있는 것 때문이어서는 안 됩니다.

도구 하나를 호출하는 것이 `tools/call`이며, `params`에 `name`과 `arguments`가 들어갑니다. 돌아오는 것은 무엇이든 `CallToolResult`입니다. 절대 빠지지 않는 `content` 리스트, 선택적인 `structuredContent` 값, 선택적인 `isError`입니다. 결과에 `isError`가 없다는 것은 호출이 성공했다는 뜻이고, `true`만이 도구가 자기 임무를 수행하는 중에 부딪힌 문제를 표시합니다. `outputSchema`까지 정의하는 도구는 구조화된 답을 `structuredContent`에 넣고, 텍스트만 읽는 클라이언트도 데이터를 받을 수 있도록 같은 값을 직렬화해서 `content` 안의 텍스트 블록으로 미러링합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "resultType": "complete",
    "content": [{"type": "text", "text": "{\"id\": \"TCK-9\", \"title\": \"VPN drops every hour\", \"status\": \"open\"}"}],
    "structuredContent": {"id": "TCK-9", "title": "VPN drops every hour", "status": "open"}
  }
}
```

`content`가 리스트인 이유는 하나의 호출이 한 번에 여러 종류의 것을 돌려줄 수 있기 때문이고, 다섯 블록 타입이 명세가 정의하는 모든 경우를 커버합니다. `text` 블록은 `text`를 실습니다. `image` 블록은 base64 `data`와 `mimeType`을 실습니다. `audio` 블록은 소리를 위해 같은 두 필드를 실습니다. `resource_link` 블록은 리소스를 인라인으로 넣는 대신 `uri`와 `name`으로 가리키며, 콘텐츠가 크거나 모델이 읽을 필요가 아예 없을 때 유용합니다. `resource` 블록은 리소스 자신의 내용물(`uri`, `mimeType`, 그리고 `text` 또는 `blob`)을 결과 안에 직접 박아 넣습니다. 이 블록들 중 무엇이든 자체적인 `annotations`를 실을 수 있습니다. 블록이 누구를 위한 것인지(`user`, `assistant`, 혹은 둘 다)를 밝히는 `audience`, 0과 1 사이의 `priority`, `lastModified` 타임스탬프가 그것입니다. 이 콘텐츠 어노테이션들은 블록의 다른 필드들 곁에, 즉 `data`나 `resource`의 형제로 놓이지 절대 한 단계 더 깊이 중첩되지 않습니다. 내장 리소스의 어노테이션이 그 `resource` 객체 안에 있는지 쉽게 착각하지만 실제로는 스키마상 그 옆에 놓이기 때문에, 이 배치는 두 번 읽어볼 가치가 있습니다.

```json
{
  "type": "resource",
  "resource": {"uri": "config://release-desk/thresholds", "mimeType": "application/json", "text": "{\"maxOpenIncidents\": 5}"},
  "annotations": {"audience": ["user", "assistant"], "priority": 0.7, "lastModified": "2026-07-01T00:00:00Z"}
}
```

별도의 어노테이션 집합은 어떤 결과의 콘텐츠가 아니라 도구 자신을 묘사합니다. `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`, 그리고 표시용 `title`입니다. 이 중 그 어느 것도 보장이 아닙니다. 클라이언트는 서버 자체가 신뢰되지 않는 한 이들을 신뢰할 수 없는 것으로 다뤄야 하고, 도구에 대해 아무 말도 하지 않는 서버라도 클라이언트에게는 기본값이라는 안전망이 남습니다. `readOnlyHint` false, `destructiveHint` true(`readOnlyHint`가 false일 때만 의미 있음), `idempotentHint` false, `openWorldHint` true입니다. 이 기본값들은 일부러 신중 쪽으로 기웁니다. 어노테이션이 아예 없는 도구는 두 번 호출했을 때 두 번째가 다르게 동작할지도 모르는 것으로 취급됩니다. 그럴 가능성이 높아서가 아니라, 그렇지 않다고 알려준 것이 아무것도 없기 때문입니다.

`tools: {listChanged: true}`를 선언한 서버는 도구 집합이 바뀔 때 알려주겠다고 약속하며, 그 알림을 커넥션 전체가 아니라 스트림 위에서 전합니다. 클라이언트는 `subscriptions/listen`으로 스트림을 열며 `params.notifications`에 `toolsListChanged`를 명시합니다. 돌아오는 첫 메시지는 언제나 `notifications/subscriptions/acknowledged`로, 서버가 지키기로 동의한 요청 타입들을 에코하고, `_meta`에 `io.modelcontextprotocol/subscriptionId`로 listen 요청 자신의 `id`와 같은 값을 태그합니다. 그 스트림 위의 이후 모든 `notifications/tools/list_changed`는 같은 구독 id를 실으므로, 열어둔 스트림이 여러 개인 클라이언트도 방금 어느 것이 말을 했는지 압니다. 알림 자신은 목록을 실지 않고, 낡았다는 말만 실습니다. 클라이언트는 평범한 `tools/list`로 다시 가져옵니다.

```figure
mcpa-11-tool-call
```

## 인터랙티브 랩

그림은 `tools/call` 한 번의 왕복을 보여줍니다. 요청이 한쪽으로 나가고, `CallToolResult`가 반대쪽으로 돌아오며, 화살표 아래에는 그 결과의 `content` 배열이 조합할 수 있는 다섯 콘텐츠 블록 타입이 놓입니다. 그 밑에는 같은 결과의 `isError` 필드가 두 갈래로 갈라집니다. 생략되거나 false면 호출이 잘 끝났다는 뜻이고, true면 도구가 모델이 읽고 대응할 수 있는 문제에 부딪혔다는 뜻입니다. 그림의 어느 것도 특정 서버에만 고유한 게 아닙니다. 도구가 문장을 말했든, 배지를 그렸든, 아직 아무도 읽을 필요 없는 파일의 링크를 돌려줬든 같은 모양이 적용됩니다.

## 실습 랩

`code/main.py`를 열어 보세요. 이 코드는 도구 여섯 개, 즉 각 콘텐츠 블록 타입마다 하나씩과 구조화된 티켓 요약 하나를 갖춘 `release-desk` 서버 하나를 만들고, 페이지당 도구 두 개씩 세 페이지에 걸쳐 나열합니다. 가운데 페이지는 일부러 빈 문자열 커서로 끝납니다.

```bash
python3 code/main.py
```

출력된 페이지들을 개념 섹션과 대조하며 읽어 보세요. 처음 두 페이지는 각각 클라이언트가 해석하지 않는 `nextCursor`로 끝나고, 세 번째 페이지만 `nextCursor` 키가 아예 없이 끝납니다. 페이지네이션이 실제로 끝났다는 유일한 신호죠. 그다음 파일 상단 근처의 `render_for_audience`를 찾아, `render_badge`가 자기 블록에 붙인 `annotations.audience` 리스트 그대로 `"assistant"`용으로 렌더링된 패스에서는 배지 이미지가 빠지고 `"user"`용에는 남는지 지켜보세요. 마지막으로 트랜스크립트 끝 근처의 `subscriptions/listen` 교환을 보세요. 승인 응답(acknowledgment)이 오고, 일곱 번째 도구 `triage_incident`가 스트림 도중에 등록되는 순간 `notifications/tools/list_changed`가 오고, 이번엔 네 번째 페이지가 필요해진 새로운 `tools/list` 순회가 이어집니다. `build_tool_server`에 여덟 번째 도구를 직접 추가하고 다시 실행해 보면, 클라이언트 코드는 한 줄도 건드리지 않은 채 페이지 분할과 `effective_tool_annotations` 기본값이 모두 맞춰 조정되는지 확인할 수 있습니다.

## 제공되는 산출물

`outputs/tool-result-anatomy.md`는 시험에서 이 레슨 몫을 위한 한 페이지 참고 자료입니다. `tools/list`의 페이지네이션과 캐싱 필드, `CallToolResult`의 모양, 다섯 콘텐츠 블록 타입 전부의 필수 필드 표, 도구 어노테이션 기본값, 그리고 listChanged 흐름의 한 줄 요약이 담겨 있습니다. 실제 서버의 도구 정의를 처음 몇 번 검토할 때 옆에 두세요. 모든 행이 이 레슨 코드가 실제로 설정하는 필드로 거슬러 올라갑니다.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검사합니다. 모든 콘텐츠 블록 타입이 잘 갖춰진 형태로 돌아오는지, `resource_link`가 항상 `uri`와 `name`을 실는지, 내장 리소스가 `annotations`를 `resource` 객체 안이 아니라 그 옆에 두는지, 청자(audience)로 콘텐츠를 거르면 다른 사람을 위한 블록이 실제로 걸러지는지, 정상 성공에서 `isError`가 계속 없는 채로 남는지, `tools/list`가 빈 문자열 커서를 만났을 때 일찍 멈추지 않고 올바르게 페이징하는지, 모르는 커서는 거부되는지, 메타데이터가 빠진 요청은 거부되는지, 도구 목록이 서로 무관한 두 커넥션에서 동일한지, 생략된 도구 어노테이션이 문서화된 기본값으로 해석되는지, 그리고 `subscriptions/listen` 스트림이 변화를 보고하기 전에 승인 응답을 먼저 보내는지입니다. 저장소의 와이어 검사기도 이 레슨의 트랜스크립트를 2026-07-28 규칙에 대해 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/11-the-tools-primitive
```

## 캡스톤 연계

캡스톤의 단일 긴 교환은 도구를 호출하고, 인자를 스키마로 검증하고, `isError` 결과를 읽어서 고쳐진 재시도로 이어갑니다. 두 동작 모두 이 레슨의 `CallToolResult`이며, 호출이 홀로 있든 더 긴 스크립트 안에 있든 같은 방식으로 읽힙니다. `content`는 모델이 보는 것이고, `structuredContent`는 프로그램이 텍스트를 다시 파싱하지 않고도 믿을 수 있는 것이며, `isError`는 잘못된 요청과 설명할 가치가 있는 문제에 부딪힌 도구를 가르는 선입니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 도구(Tool) | 서버가 이름으로 노출하는, 모델이 제어하고 스키마로 타입이 정해진 동작 |
| `tools/list` | 서버의 도구를 열거하는, 페이지네이션되고 캐시 가능한 요청 |
| `tools/call` | 이름과 인자로 도구 하나를 호출하는 요청 |
| `CallToolResult` | 도구 호출의 결과 모양. `content`, 선택적 `structuredContent`, 선택적 `isError` |
| 콘텐츠 블록 | 도구 결과 `content` 리스트의 한 항목. text, image, audio, 리소스 링크 또는 내장 리소스 |
| `resource_link` | 리소스를 인라인하지 않고 URI로 가리키는 콘텐츠 블록 |
| 콘텐츠 어노테이션 | 콘텐츠 블록의 `audience`, `priority`, `lastModified`. 누가 봐야 하고 얼마나 신선한지를 묘사한다 |
| 도구 어노테이션 | `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`. 도구 동작에 대한 신뢰할 수 없는 힌트 |
| `nextCursor` | 도구가 더 남아 있을 때 페이지네이션 결과가 실는 불투명한 토큰. 참 같은지(falsy 여부)가 아니라 존재 여부가 기준 |
| `subscriptions/listen` | 서버가 `notifications/tools/list_changed`를 알릴 스트림을 여는 요청 |

## 더 읽을거리

- [MCP 명세 2026-07-28, Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [MCP 명세 2026-07-28, Subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)
- [MCP 명세 2026-07-28, 스키마 참조](https://modelcontextprotocol.io/specification/2026-07-28/schema)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 10절
- `phases/13-tools-and-protocols/07-building-an-mcp-server`와 `phases/13-tools-and-protocols/28-mcp-tool-contracts-and-content`, 도구 계약과 콘텐츠 처리를 깊게 다루는 단계
