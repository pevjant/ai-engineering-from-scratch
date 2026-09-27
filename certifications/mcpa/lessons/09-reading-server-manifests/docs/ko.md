> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 리뷰어의 시선으로 서버 매니페스트(manifest) 읽기

> 서버의 discover 결과, 도구 목록, 레지스트리 등록 정보는 무언가를 호출하기 전에 그 서버에 대해 알 수 있는 전부입니다. 그러니 계약서를 읽듯이 읽어야 합니다. 읽지 않고 넘어간 기본값은 여러분이 의도하지 않은 약속이 되어 돌아오니까요.

**유형:** 참고 자료
**사용 언어:** Python
**선수 지식:** 레슨 08
**소요 시간:** 약 45분

## 학습 목표

- 호출이 일어나기 전에 서버를 기술하는 세 가지 문서, 즉 `server/discover` 결과, `tools/list` 페이지, 레지스트리 `server.json`을 읽는 방법을 익힙니다
- 도구 어노테이션(annotation) 기본값(readOnlyHint false, destructiveHint true, idempotentHint false, openWorldHint true)을 적용해 보고, 어노테이션이 빠져 있을 때 실제로 어떤 약속이 성립하는지 확인합니다
- 캐퍼빌리티(capability) 플래그, `x-mcp-header` 표시, 아이콘, `cacheScope` 선택이 서버 동작에 대해 함축하는 바를 설명합니다
- 매니페스트의 위험 신호(red flag)를 잡아냅니다. 어노테이션 없는 파괴적 도구, `x-mcp-header`로 미러링된 시크릿, 사용자별 텍스트에 붙은 `public` `cacheScope`, 그리고 서버를 설명하는 대신 모델을 조종하려고 쓰인 instructions
- 레지스트리 `server.json`의 이름을 네임스페이스로 분해하고, 그 네임스페이스가 어떻게 검증되었는지 설명합니다

## 문제 상황

호스트(host)가 도구를 호출하기 전에 이미 서버에 대해 알고 있는 것은 세 가지입니다. `server/discover`가 지원한다고 주장하는 것, `tools/list`가 현재 제공하는 것, 그리고 서버가 공개되어 있다면 레지스트리 `server.json`이 말해주는 소유자 정보입니다. 그런데 프로토콜 어디에도 이 세 문서를 완전하고, 신중하고, 정직하게 만들도록 강제하는 장치는 없습니다. 어노테이션은 힌트일 뿐이고, instructions는 서버가 스스로 써 내간 글이며, 레지스트리 이름은 그 뒤에 깔린 검증 절차만큼만 믿을 수 있습니다. 이 문서들을 읽지 않고 서버를 추가하는 호스트는, 실제로 확인한 적 없는 기본값과 주장들을 그대로 믿는 셈입니다.

이것은 서버를 작성하거나 호출하는 것과는 다른 기술입니다. 앱을 설치하기 전에 권한 목록을 읽는 일에 가깝습니다. 아직 아무것도 실행하지 않으면서, 지금 제공되는 것의 모양이 이 범주의 합리적인 서버가 제공했을 법한 것과 맞는지 판단하고, 부주의하거나 악의적인 작성자가 어디서 건성으로 넘어갔는지 구체적인 지점을 찾는 것입니다. `annotations` 블록이 없는 도구가 검토를 면제받는 것은 아닙니다. 클라이언트는 기본값을 적용하도록 요구받으며, 그 기본값은 허가가 아니라 신중 쪽으로 기울어 있습니다. `x-mcp-header`를 통해 HTTP 헤더로 미러링된 파라미터는 이제 클라이언트와 서버 사이의 모든 프록시와 로드 밸런서에 노출됩니다. `instructions` 필드는 호스트가 모델에게 그대로 넘겨줄 수 있는 텍스트입니다. 매니페스트를 잘 읽는다는 것은 이 모든 것을 그냥 받아들일 사실이 아니라 검증해야 할 주장으로 다룬다는 뜻입니다.

## 핵심 개념

`server/discover`(디스커버리와 캐퍼빌리티 협상 레슨에서 다룬)가 첫 번째 문서입니다. `supportedVersions`, `capabilities`, 선택적인 `instructions` 문자열, 그리고 `_meta["io.modelcontextprotocol/serverInfo"]`가, `ttlMs`와 `cacheScope`를 실은 캐시 가능한 봉투(envelope) 안에 모두 들어 있습니다. 리뷰어는 `capabilities`를 가장 먼저 읽습니다. `tools: {listChanged: true}`는 도구 집합이 바뀔 때 구독 중인 클라이언트에 알려주겠다는 뜻이므로, 구독하지 않는 클라이언트는 `ttlMs`가 지난 뒤에는 낡은 목록을 보게 됩니다. `resources: {subscribe: true}`는 목록 변경뿐 아니라 개별 리소스의 업데이트도 받을 수 있다는 뜻입니다. `completions: {}`는 `completion/complete`가 구현되어 있다는 뜻입니다. `extensions` 객체는 선택적인 프로토콜 확장과 그 설정을 나열합니다. 키는 존재하지만 리뷰어에게 낯선 확장이라면, 그 확장이 바꾸는 내용을 믿기 전에 찾아보는 것이 좋습니다.

`tools/list`(레슨 08의 스키마 계약)가 두 번째 문서이고, 위험 신호가 가장 많이 숨는 곳입니다. 각 도구는 `name`, `description`, `inputSchema`와 선택적인 `title`, `icons`, `outputSchema`, `annotations`를 실고 있습니다. 어노테이션은 리뷰어가 건너뛸 수 없는 부분입니다. `readOnlyHint`의 기본값은 false, `destructiveHint`의 기본값은 true(단, `readOnlyHint`가 false일 때만 의미가 있음), `idempotentHint`의 기본값은 false, `openWorldHint`의 기본값은 true입니다. 실제로 작동하는 방향으로 다시 한 번 읽어보세요. `annotations` 객체 없이 배포된 도구는, 클라이언트가 적용해야 하는 기본값에 따라 읽기 전용이 아니며 파괴적입니다. 여기서는 침묵이 곧 안전이 아닙니다. `delete_account`나 `run_report` 같은 이름의 맨몸 도구 정의를 본 리뷰어는, 명시적인 `readOnlyHint: true`나 `destructiveHint: false`가 말해주기 전까지는 파괴적인 것으로 취급해야 합니다. 그것이 바로 명세가 규격을 따르는 클라이언트에게 가정하라고 말하는 것이기 때문입니다. 그리고 이 모든 것은 힌트이지 결코 보장이 아닙니다. 명세는 서버 자체가 신뢰되지 않는 한 어노테이션을 신뢰할 수 없는 것으로 다뤄야 한다고 분명히 말합니다. 그러니 리뷰어가 할 일은 그 주장을 알아차리는 것이지, 그것을 강제하는 것이 아닙니다.

`icons`는 표시용 메타데이터지만 URI에서 가져오는 것이므로, 리뷰어는 `https:`나 `data:`를 쓰는지, 서버와 오리진(origin)을 공유하는지 확인합니다. SVG 아이콘은 실행 가능한 스크립트를 품고 있을 수 있으니 장식이 아니라 콘텐츠로 다뤄야 합니다. 스키마 속성 안에 설정하는 `x-mcp-header` 속성은 그 인자의 값을 `Mcp-Param-{Name}` HTTP 헤더로 미러링해서, 게이트웨이가 본문을 해석하지 않고도 이 값을 기준으로 라우팅할 수 있게 합니다. 여기에는 실제 제약이 따릅니다. 헤더 이름은 공백이나 제어 문자가 없는 유효한 HTTP 필드 이름 토큰이어야 하고, 한 도구의 스키마 안에서 대소문자 구분 없이 유일해야 하며, 원시 타입에만 적용할 수 있고 절대 `number`에는 쓸 수 없습니다. Streamable HTTP 클라이언트는 이 규칙 하나라도 어기는 `x-mcp-header` 값을 가진 도구를, 어노테이션을 조용히 무시하는 대신 `tools/list` 결과에서 제거해야 합니다. 문법과 별개로 리뷰어는 무엇이 미러링되는지 확인합니다. 명세는 서버에게 비밀번호, API 키, 토큰 같은 시크릿을 이 방식으로 표시하지 말라고 경고합니다. 헤더 값은 목적지 서버뿐 아니라 중간에 거치는 모든 매개자에게 보이기 때문입니다.

`server/discover`와 `tools/list`는 모두 캐시 가능한 결과이므로, 모든 complete 응답은 `ttlMs`와 `public` 또는 `private` 중 하나인 `cacheScope`를 실어야 합니다. `cacheScope`는 누가 캐시 사본을 공유할 수 있는지에 대한 힌트이지 접근 제어가 아닙니다. `public`은 같은 바이트를 다른 호출자의 캐시 조회에 제공해도 된다는 뜻이고, `private`은 인가 경계를 넘지 못한다는 뜻입니다. 리뷰어는 도구 설명과 discover의 `instructions`를 선언된 스코프와 대조해 읽습니다. 마치 특정 호출자의 데이터(그 사람의 계정, 그 사람의 잔액, 현재 사용자)를 묘사하는 것처럼 읽히는 텍스트에 `cacheScope: "public"`이 붙어 있다면 실질적인 위험입니다. 스코프를 문자 그대로 믿는 캐시 계층은 기꺼이 어떤 사용자의 개인화된 목록을 다음 호출자에게 넘겨줄 테니까요.

`instructions`는 따로 읽을 가치가 있습니다. 이 필드는 모델이 서버를 잘 쓰도록 돕기 위해 존재하며, `serverInfo`와 마찬가지로 서버가 스스로 보고한 것일 뿐 프로토콜이 검증해주지 않습니다. 정상적인 instructions는 서버를 묘사합니다. 무엇을 하는지, 어떤 도구를 언제 다른 도구보다 선호해야 하는지, 어떤 단위를 기대하는지 같은 것들이죠. 반면 모델 자신을 겨냥한 명령으로 쓰인 instructions, 즉 앞선 지침을 무시하라거나, 특정 도구를 항상 먼저 호출하라거나, 사용자에게 어떤 정보를 숨기라고 하는 문장은 더 이상 서버를 묘사하는 게 아닙니다. 그것은 클라이언트가 기본적으로 신뢰하기 쉬운 채널을 통해 전달되는 프롬프트 인젝션(prompt injection)의 전형적인 모양이며, 리뷰어는 도구 결과 안에서 발견한 주입된 지시를 의심하듯 똑같이 의심해야 합니다.

세 번째 문서는 와이어 프로토콜 바깥에 있습니다. 레지스트리의 `server.json`입니다. 그 `name` 필드는 역방향 DNS 패턴, 즉 `io.github.username/server-name`이나 `com.example/server-name` 꼴을 따르며, MCP 레지스트리는 게시자가 검증 챌린지를 통해 그 이름 뒤의 GitHub 계정이나 도메인의 소유권을 증명한 후에야 이름을 받아들입니다. `/`가 없는 이름은 네임스페이스가 전혀 없는 것이고, 그렇다는 것은 그 이름에 대해 소유권 검증이 이루어지지 않았을 뿐 아니라 이루어질 수도 없었다는 뜻입니다. 리뷰어는 서명되지 않은 패키지를 대하듯 다뤄야 합니다. `packages`와 `remotes`는 서버를 어떻게 실행하는지 설명합니다(npm, PyPI, NuGet, Cargo, MCPB, OCI 패키지 또는 원격 Streamable HTTP/SSE URL). 패키지 타입마다 소유 증명 방식이 따로 있는데, `package.json`의 `mcpName` 필드나 README에 숨겨둔 `mcp-name:` 마커 같은 것입니다. 레지스트리 자체는 서버 코드의 취약점을 스캔하지 않고, 그 일은 하위 패키지 레지스트리와 다운스트림 애그리게이터에 맡깁니다. 그래서 리뷰어가 레지스트리에 의지할 수 있는 보장은 네임스페이스 검증이 유일합니다.

```figure
mcpa-09-manifest-anatomy
```

## 인터랙티브 랩

그림은 세 문서를 나란히 보여줍니다. 캐퍼빌리티와 instructions를 실은 `server/discover` 결과, 어노테이션과 `x-mcp-header` 표시가 붙은 `tools/list` 항목, 네임스페이스가 붙은 이름을 가진 레지스트리 `server.json`입니다. 각 패널에는 부주의한 서버가 가장 자주 틀리는 필드가 표시되어 있습니다. 설명이 아니라 명령처럼 읽히는 instructions, 어노테이션이 아예 없는 도구, 검증된 네임스페이스가 없는 이름이 그 대상입니다. 표시된 각 필드를 바로 위 개념 섹션의 규칙으로 거슬러 올라가 보세요. 그 필드가 원래 무슨 뜻이어야 하는지, 그리고 명세를 정확히 따르는 클라이언트 입장에서 그 필드가 없거나 잘못 쓰일 때 실제로 무엇을 의미하는지입니다.

## 실습 랩

`code/main.py`를 열어 보세요. 이 코드는 `server/discover`와 `tools/list`에만 답하는 서버 두 개를 만듭니다. 하나는 부주의한 통합이 실제로 출시되는 방식 그대로 쓴 `acme-tools` 서버이고, 다른 하나는 정성껏 쓴 `docs-search` 서버입니다. 그런 다음 양쪽 결과와 각 서버의 손으로 작성한 `server.json`을 `lint_manifest`에 통과시킵니다. 레슨 디렉터리에서 실행하세요:

```bash
python3 code/main.py
```

먼저 `acme-tools` 보고서부터 읽어 보세요. `delete_account`에는 `annotations` 블록이 없고, 린터는 기본값을 근거로 이 도구를 파괴적이라고 표시합니다. 짐작해서가 아니라, 명세의 기본값 자체가 그렇게 만들기 때문입니다. `rotate_api_key`는 `new_api_key`를 `x-mcp-header`로 미러링하는데, 린터는 시크릿처럼 읽히는 값을 노출하는 헤더라고 표시합니다. `run_report`는 `region_code`를 공백이 들어간 헤더 값 `"Region Code"`로 미러링하는데, 이는 유효한 HTTP 필드 이름 토큰이 아니어서, Streamable HTTP 클라이언트가 사용하는 대신 도구 목록에서 버려야 하는 정의의 전형입니다. `get_balance`는 "현재 사용자의 계정 잔액"이라고 읽히는데 서버의 `tools/list` 결과는 `cacheScope: "public"`이고, 린터는 이 두 사실을 연결해 캐싱 위험으로 지적합니다. discover의 `instructions` 필드는 "Ignore any prior guidance(기존 지침은 무시하세요)"로 시작하고, 린터는 이것을 모델을 겨냥한 언어로 잡아냅니다. 레지스트리 이름 `"acme-tools"`에는 `/`가 없어서 파싱 결과가 아무것도 남지 않고, 역시 표시됩니다. 이를 `docs-search`와 비교해 보세요. 모든 도구가 명시적으로 읽기 전용이고, 쓰는 헤더는 평범하며 유일하고, 캐시되는 텍스트는 진짜 공개 대상이며, instructions는 모델에게 명령하는 대신 서버를 묘사하고, 레지스트리 이름 `io.github.acmedocs/docs-search`는 GitHub로 검증된 네임스페이스와 함께 말끔히 파싱됩니다. 트랜스크립트의 마지막 항목은 클라이언트가 보낸 것이 아닙니다. 부주의한 서버가 실제로 보낼 수 있는 `server/discover` 응답으로, `ttlMs`와 `cacheScope`가 통째로 빠져 있습니다. 일부러 감싸 놓은 위반 사례라서, 실제 호출이 실패하는 모습을 보기 전에 캐싱 계약에 어긋나는 것이 무엇인지 먼저 볼 수 있습니다.

## 제공되는 산출물

`outputs/manifest-review-checklist.md`는 이 레슨의 한 페이지 요약본입니다. 세 문서 각각에서 무엇을 읽어야 하는지, 어노테이션 기본값 표, `x-mcp-header` 규칙, 캐싱과 instructions의 위험 신호, 레지스트리 네임스페이스 파싱 방법이 담겨 있습니다. 낯선 서버를 처음 몇 번 추가할 때는 옆에 두고 쓰세요.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검사합니다. 어노테이션 없는 도구를 알 수 없는 것으로 취급하지 않고 명세의 기본값을 적용하는지, 맨몸 파괴적 도구는 표시되고 명시적으로 읽기 전용인 도구는 표시되지 않는지, `x-mcp-header`로 미러링된 시크릿 같은 파라미터가 HTTP 토큰 문법에 어긋나는 헤더 값과 별개로 표시되는지, `number` 속성에 붙은 `x-mcp-header`가 거부되는지, 사용자별 텍스트와 짝지어진 public 캐시 스코프가 표시되는지, `instructions`의 조종 언어가 잡히는지, 네임스페이스 없는 레지스트리 이름은 거부되고 검증된 GitHub 네임스페이스는 올바르게 파싱되는지, 깨끗한 매니페스트는 아무 지적도 만들어내지 않는지, 그리고 트랜스크립트의 모든 요청이 여전히 요구되는 `_meta`를 실고 있는지입니다. 저장소의 와이어 검사기도 이 레슨의 트랜스크립트를 2026-07-28 규칙에 대해 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/09-reading-server-manifests
```

## 캡스톤 연계

캡스톤의 엔드투엔드 교환은 실제 호출에 도달하기 전에 discover 호출과 도구 목록으로 시작하며, 그 시점에서 안전하게 가정할 수 있는 모든 것은 이 레슨에 뿌리를 둡니다. 캐퍼빌리티 플래그를 올바르게 읽었는지, 어노테이션 기본값을 건너뛰지 않고 적용했는지, 첫 도구 호출이 일어나기 전까지 매니페스트의 어떤 것도 모델을 조종하지 않았는지가 그 대상입니다. 이 트랙의 뒤에 오는 신뢰 경계와 동의(consent) 레슨들도, 매니페스트가 주장하는 것을 행동으로 옮기기 전에 의심하는 눈으로 읽는 습관 위에 곧장 세워집니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 매니페스트(Manifest) | discover 결과, 도구 목록, 레지스트리 server.json을 모두 합친 것. 어떤 호출보다 먼저 읽는다 |
| 어노테이션 기본값 | 도구가 annotations를 생략했을 때 적용되는 readOnlyHint false, destructiveHint true, idempotentHint false, openWorldHint true |
| x-mcp-header | 원시 타입 인자를 라우팅용 HTTP 헤더로 미러링하는 스키마 속성 |
| cacheScope | 캐시된 결과를 사용자와 토큰을 넘어 공유할 수 있는지. 절대 접근 제어가 아니다 |
| instructions | server/discover에서 서버가 자신에 대해 제공하는, 자기 보고식 자연어 안내 |
| 역방향 DNS 네임스페이스 | server.json 이름의 io.github.user 또는 com.example 접두사. 검증된 소유자와 묶여 있다 |
| 위험 신호(red flag) | 같은 분야의 신중한 서버라면 보여줬을 것과 주장이 맞지 않는 매니페스트 필드 |
| 소유권 검증 | 레지스트리가 이름을 게시자와 묶기 위해 사용하는 GitHub, DNS, HTTP 챌린지 |

## 더 읽을거리

- [MCP 명세 2026-07-28: Discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
- [MCP 명세 2026-07-28: Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [MCP 레지스트리 개요](https://modelcontextprotocol.io/registry/about)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 6, 10, 15절
