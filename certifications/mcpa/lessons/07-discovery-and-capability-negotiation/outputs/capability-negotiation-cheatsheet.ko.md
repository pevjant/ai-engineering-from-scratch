> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [capability-negotiation-cheatsheet.md](capability-negotiation-cheatsheet.md)

# 기능 협상 치트 시트

MCPA '아키텍처와 구성 요소' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## server/discover 한눈에 보기

| 필드 | 위치 | 의미 |
|-------|-------|---------|
| `supportedVersions` | result | 서버가 받아들이는 프로토콜 버전. 이후 요청에 하나를 고르세요 |
| `capabilities` | result | `ServerCapabilities` 객체: 서버가 제공하는 것들 |
| `instructions` | result, 선택 | 모델을 위한 자연어 안내. 도구 설명의 복사본이 아님 |
| `io.modelcontextprotocol/serverInfo` | `result._meta` | 스스로 보고한 이름과 버전. 표시와 로그 전용 |
| `ttlMs` | result | 밀리초 단위 신선도 힌트. `DiscoverResult`는 `CacheableResult`임 |
| `cacheScope` | result | `public` 또는 `private`. 그 자체로 접근 통제가 되지는 않음 |

구현: 모든 서버에 필수. 호출: 클라이언트에게는 선택. 클라이언트는 아무 요청이나 바로 보내고, 버전 오류가 돌아오면 그때 처리해도 됩니다.

## ServerCapabilities와 ClientCapabilities 나란히 보기

| ServerCapabilities 키 | 의미 | ClientCapabilities 키 | 의미 |
|---|---|---|---|
| `tools {listChanged}` | 도구 제공, 변화 시 알림 가능 | `elicitation {form, url}` | 폼 또는 URL 모드 일러시테이션에 응답 가능 |
| `resources {listChanged, subscribe}` | 리소스 제공, 알림 또는 구독 수용 가능 | `sampling`(폐기됨) | LLM completion을 서버에 돌려줄 수 있음 |
| `prompts {listChanged}` | 프롬프트 템플릿 제공 | `roots`(폐기됨) | 루트 디렉터리 목록을 제공 가능 |
| `completions {}` | 인자 completion 제공 | `extensions {}` | 이름 붙은 클라이언트 측 확장 지원 |
| `logging {}`(폐기됨) | 로그 알림 발행 가능 | | |
| `extensions {}` | 이름 붙은 서버 측 확장 지원 | | |

빈 객체는 '추가로 설정할 것 없이 지원함'이라는 뜻입니다. 키가 아예 없으면 그 프리미티브나 기능을 전혀 제공하지 않는다는 뜻입니다.

## 협상 규칙

`DiscoverResult.capabilities`는 서버를 딱 한 번, 캐시 가능한 형태로 설명합니다. 특정 클라이언트 요청이 무엇을 받아들일 수 있는지에 관해서는 아무 말도 하지 않습니다. `_meta["io.modelcontextprotocol/clientCapabilities"]`는 클라이언트를 설명하며, 모든 요청에 빠짐없이, 정확하게, 최신 상태로 들어 있어야 합니다. 서버는 이전 호출에서 이를 유추하면 안 되기 때문입니다. 같은 연결 위라도 마찬가지입니다.

## MissingRequiredClientCapabilityError (-32021)

- 요청을 처리하려면 어떤 기능이 필요한데 그 요청 자신의 `clientCapabilities`가 그 기능을 선언하지 않았을 때 돌아옵니다.
- `data.requiredCapabilities`는 `ClientCapabilities`와 같은 모양으로, 정확히 무엇이 빠졌는지 알려 줍니다.
- HTTP 상태: `400 Bad Request`.
- 해결: 같은 요청을, 그 요청 자신의 `_meta`에 기능을 선언해서 재시도합니다. 다른 요청이 아니라요.

## UnsupportedProtocolVersionError (-32022)

- 요청이 서버가 구현하지 않은 프로토콜 버전을 지목했을 때 돌아옵니다.
- `data.supported`는 서버가 받아들이는 버전들을 나열하고, `data.requested`는 요청받은 버전을 그대로 돌려줍니다.
- HTTP 상태: `400 Bad Request`.
- 해결: 새 요청 id로, `data.supported`에서 가져온 버전을 써서 재시도합니다.
- modern 전용 서버라도 legacy `initialize` 요청을 거부할 때는 자신이 지원하는 버전들을 알려 줘야 합니다. legacy 클라이언트는 스스로 최신으로 넘어갈 수 없기 때문입니다.

## 재시도 체크리스트

1. 오류의 `data`를 읽으세요. 재시도할 버전이나 기능을 추측하지 마세요.
2. 재시도에는 완전히 새로운 JSON-RPC id를 발급하세요. 실패한 요청의 id를 재사용하지 마세요.
3. 오류가 요구한 것만 바꾸고 요청의 나머지는 그대로 두세요.
4. `-32021`이나 `-32022` 응답을 정상 결과인 것처럼 캐시하지 마세요.
5. 이후 요청이 이전 요청에 선언된 것을 물려받는다고 가정하지 마세요.

## 시험을 위해 기억하기

- `server/discover`는 구현이 필수, 호출은 선택입니다.
- 모르는 도구는 `-32602`, 모르는 메서드는 `-32601`, 빠진 기능은 `-32021`, 지원 안 하는 버전은 `-32022`입니다.
- `serverInfo`와 `clientInfo`는 스스로 보고한 값으로, 표시와 로깅용일 뿐 보안 판단용이 절대 아닙니다.
- modern `_meta` 형태로 더 오래된 실제 프로토콜 버전을 요청하는 것은 legacy 클라이언트인 것과 다릅니다. legacy 클라이언트는 대신 `initialize`를 보냅니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 6절.
