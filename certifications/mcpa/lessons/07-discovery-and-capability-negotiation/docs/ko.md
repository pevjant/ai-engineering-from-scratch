> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 서버 알아보기와 할 수 있는 일 협상하기

> 서버는 `server/discover`를 통해 자신을 한 번 묘사하지만, 모든 요청은 여전히 자기만의 기능(capability)을 선언합니다. 클라이언트가 제공 항목을 물어봤다는 이유만으로 서버에 필요한 것을 가정하지는 않습니다.

**유형:** 레퍼런스
**언어:** Python
**선수 지식:** 레슨 06
**시간:** 약 45분

## 학습 목표

- `server/discover` 요청과 그 `DiscoverResult` 읽기: `supportedVersions`, `capabilities`, `instructions`, `serverInfo`, `ttlMs`, `cacheScope`
- 서버에게 `server/discover` 구현이 필수인 반면 클라이언트가 그것을 호출하는 것은 선택 사항인 이유 설명하기
- `ServerCapabilities`와 `ClientCapabilities`의 모양을 읽고 각 플래그가 무엇을 약속하는지 말하기
- 서버가 그 특정 요청에서 클라이언트가 선언하지 않은 기능에 의존해서는 안 되는 이유, 그리고 `MissingRequiredClientCapabilityError`(`-32021`)가 무엇을 실어 오는지 설명하기
- `UnsupportedProtocolVersionError`(`-32022`)에서 출발해 클라이언트가 서로 지원되는 버전을 고르는 버전 협상 재시도 전체를 따라가기

## 문제 상황

레슨 06은 호스트에게 서버당 클라이언트 하나와 책임의 깔끔한 분할을 주었지만 열린 질문을 남겨 두었습니다. 클라이언트가 한 번도 본 적 없는 서버와 처음 이야기할 때, 준비 대화를 나눠 물어보지 않고 그 서버가 무엇이고 무엇을 할 수 있는지 어떻게 알아낼까? 레슨 04의 상태 비저장 코어는 이미 `initialize` 핸드셰이크와 그 답을 기억하는 세션을 배제했습니다. 모든 요청은 여전히 스스로를 기술해야 합니다.

이것은 양방향으로 작동합니다. 클라이언트는 서버의 정체, 지원 프로토콜 버전, 제공 항목의 모양을 빠르게 알아낼 방법이 필요합니다. 그림을 만들려고 `tools/list`, `resources/list`, `prompts/list`를 따로따로 탐침하는 것보다는 이상적으로 왕복 한 번으로요. 그리고 서버는, 정확히는 연결 상태에 기댈 수 없기 때문에, 클라이언트가 다섯 요청 전에 유도(elicitation)나 샘플링 지원이 어떤 모습인지 물어봤다는 이유로 그 클라이언트가 이번 호출에서 유도 요청을 처리할 의지와 능력이 아직 있다고 가정할 수 없습니다. "서버가 무엇을 제공하는지 배우기"와 "클라이언트가 현재 무엇을 받아들일 수 있는지 증명하기", 이 두 문제는 비슷하게 들리지만 반대 방향으로 흐르며, 2026-07-28은 필드 이름만 훑어 보면 서로 뒤섞기 쉬운 두 개의 서로 다른 메커니즘으로 이들을 해결합니다.

## 개념

`server/discover`가 첫 번째 메커니즘입니다. 서버는 이를 구현해야 합니다(**MUST**). 클라이언트는 이를 호출해도 되고(**MAY**), 실제로 원하는 요청으로 바로 건너뛰었다가 버전 불일치가 돌아오면 그때 처리해도 됩니다. 요청은 표준 `_meta` 외에 아무것도 실지 않습니다.

```json
{
  "jsonrpc": "2.0",
  "id": "discover-1",
  "method": "server/discover",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}
```

결과인 `DiscoverResult`는 `CacheableResult`이므로 자기 필드들과 함께 항상 `ttlMs`와 `cacheScope`를 실습니다. `supportedVersions`(이후 요청에서 클라이언트가 고를 목록), `capabilities`(`ServerCapabilities` 객체), 그리고 선택적 `instructions` 문자열 — 모델을 위한 자연어 안내이지 툴 설명의 복제품이 아닙니다. 서버 자신의 정체는 `result._meta["io.modelcontextprotocol/serverInfo"]`로 이동하며, 서버가 스스로 보고하는 이름과 버전입니다. 그 필드는 예의 바른 표시이지 자격 증명이 아닙니다. 표시, 로그, 디버깅에만 쓰고 인가나 신뢰 결정을 그것이 주도하게 하지 마세요. 프로토콜이 그것을 검증하는 곳은 어디에도 없습니다.

`ServerCapabilities`는 서버가 제공하는 것을 플래그 집합으로 나열합니다. `tools {listChanged}`, `resources {listChanged, subscribe}`, `prompts {listChanged}`, `completions {}`, `logging {}`(폐기됨, 여전히 존재, 레슨 15에 도달하면 깊이 다룸), 그리고 `extensions {}`(확장 식별자를 설정 객체에 매핑한 것, 레슨 30의 주제). `completions` 같은 기능에 대한 빈 객체는 "지원됨, 보고할 추가 설정 없음"을 의미합니다. 키가 없다는 것은 서버가 그 프리미티브를 전혀 제공하지 않는다는 의미입니다. `ClientCapabilities`는 그 거울상으로, 클라이언트가 무엇을 받아들일 수 있는지 묘사합니다. 레슨 14에서 다루는 두 모드를 위한 `elicitation {form, url}`, `sampling`과 `roots`(둘 다 폐기됨, 마이그레이션 경로는 레슨 15), 그리고 `extensions {}`입니다. 두 모양, 같은 명명 규칙, 반대 방향의 흐름.

필드 이름만 훑어 본 독자가 걸려 넘어지는 부분이 여기 있습니다. `DiscoverResult.capabilities`는 *서버*가 할 수 있는 일로, 한 번 보고되고, 캐시 가능하며, `ttlMs` 힌트가 낡기 전까지는 안심하고 재사용할 수 있습니다. 그것은 *클라이언트*가 현재 무엇을 받아들일 수 있는지에 대해서는 아무 말도 하지 않습니다. 그것은 별개의, 요청별 사실로, discover든 아니든 모든 단일 요청의 `_meta["io.modelcontextprotocol/clientCapabilities"]`에 실립니다. 클라이언트 기능을 사용해야 하는 서버 — 예컨대 툴 호출을 처리하는 도중에 form 모드 유도 질문을 하는 서버 — 는 *그 특정 요청의* `clientCapabilities`를 확인해야 하며, 이전 discover 호출이나 이전 `tools/call`에서 기억해 둔 값으로는 절대 안 됩니다. 이것은 레슨 04의 상태 비저장성이 기능에 그대로 적용된 것입니다. 이전 요청으로부터의 추론은 없습니다. 언제나, 같은 연결 위에서조차.

서버가 현재 요청이 선언하지 않은 기능을 필요로 하면 `MissingRequiredClientCapabilityError`를 반환합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "error": {
    "code": -32021,
    "message": "notify_oncall requires a capability this request did not declare",
    "data": {
      "requiredCapabilities": {
        "elicitation": {}
      }
    }
  }
}
```

`data.requiredCapabilities`는 `ClientCapabilities`와 정확히 같은 모양으로, 빠져 있던 범주들을 이름으로 밝혀서 클라이언트가 추측이 아니라 그것을 선언한 채 재시도할 수 있게 합니다. HTTP에서 이 오류의 상태 코드는 `400 Bad Request`입니다.

버전 선택은 협상의 다른 절반으로, 디스커버리와는 전혀 묶여 있지 않습니다. 어떤 요청이든 이것을 촉발할 수 있습니다. 요청이 서버가 구현하지 않은 프로토콜 버전을 이름으로 밝히면, 서버는 `UnsupportedProtocolVersionError`로 거부해야 합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "error": {
    "code": -32022,
    "message": "Unsupported protocol version",
    "data": {
      "supported": ["2026-07-28"],
      "requested": "2025-11-25"
    }
  }
}
```

클라이언트는 `data.supported`에서 버전 하나를 골라 새 id로 같은 요청을 재시도해야 합니다. 이것이 무엇이 아닌지 주목하세요. 현대식 `_meta` 모양을 통해 더 오래된 실제 개정판 문자열을 요청하는 것은 구버전 클라이언트가 되는 것이 아닙니다. 구버전 클라이언트는 요청별 메타데이터 대신 `initialize` 요청을 보냅니다. 그것은 메시지 모양으로 정의되는 시대(era)이지 버전 번호가 아닙니다. 구버전 클라이언트로부터 실제 `initialize` 요청을 받은 modern 전용 서버는 돌려 보내는 오류 안에 자기 지원 버전들을 여전히 이름으로 밝혀야 합니다. 구버전 클라이언트가 사용자에게 보여 줄 수 있는 유일한 진단 정보이며, 레슨 05의 시대 모델이 어디서나 기대하는 바로 그 규율입니다.

```figure
mcpa-07-discover
```

## 인터랙티브 랩

그림은 두 메커니즘을 시각적으로 분리합니다. 위쪽 레인은 `server/discover`를 보여 줍니다. 클라이언트에게 선택 사항이며, 지원 버전, 기능, 안내, 캐시 힌트를 한 번의 왕복으로 함께 돌려줍니다. 아래쪽 레인은 디스커버리가 실행되었든 아니든 모든 `tools/call`에서 일어나는 일을 보여 줍니다. 요청 자신의 `clientCapabilities`가 새로 확인됩니다. 아무것도 선언하지 않으면 유도가 필요한 툴이 `-32021`로 돌아오며 빠진 것이 정확히 무엇인지 이름으로 밝힙니다. 그 요청에서 그것을 선언하면 같은 호출이 완료됩니다. 첫 성공한 discover 호출에 관한 무엇도 두 번째 레인으로 이월되지 않습니다.

## 연습 랩

`code/main.py`를 열어 보세요. `DeployServer`는 `server/discover`와 하나의 게이트된 툴인 `notify_oncall`을 구현합니다. `notify_oncall`의 정의는 실행되기 전에 `elicitation` 기능이 필요하다고 말하며, 아무것도 필요로 하지 않는 게이트 없는 툴 `list_incidents`도 함께 있습니다.

```bash
python3 code/main.py
```

출력된 교환을 순서대로 읽으세요. 첫 번째 쌍은 평범한 `server/discover`로, `supportedVersions`, `capabilities`, `instructions`, 캐시 힌트를 반환합니다. 두 번째 쌍은 `clientCapabilities: {}`로 `notify_oncall`을 호출하고 `elicitation`을 이름으로 밝히는 `data.requiredCapabilities`와 함께 `-32021`을 돌려받습니다. 세 번째 쌍은 같은 호출을 반복하되, 이번에는 그 요청의 `_meta`에 `elicitation`을 선언하며 정상적으로 완료됩니다. 네 번째 쌍은 서버에 없는 툴 이름인 `close_all_incidents`를 호출하는데, 이것은 기능 문제가 아니라 프로토콜 오류 `-32602`입니다. 마지막 두 쌍은 버전 협상을 보여 줍니다. `2025-11-25`를 요구하는 `server/discover`가 `data.supported`로 `["2026-07-28"]`을 이름 밝히며 `-32022`로 돌아오고, 클라이언트의 다음 호출은 그 버전을 골라 새 요청 id로 성공합니다. `elicitation`을 한 번 선언한 뒤 이후 호출에서 빼먹어 보세요. 서버는 다시 거부합니다. 이전 선언을 기억한 적이 없기 때문입니다.

## 제공되는 산출물

`outputs/capability-negotiation-cheatsheet.md`는 `DiscoverResult` 필드 표, 나란히 놓인 `ServerCapabilities`와 `ClientCapabilities` 모양, `-32021`과 `-32022`의 데이터 모양, 그리고 짧은 재시도 체크리스트를 모으며, 모두 브리프를 인용합니다.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요.

```bash
python3 -m unittest discover code/tests
```

테스트는 다음을 확인합니다. `server/discover`가 `supportedVersions`, 온전한 `capabilities` 객체, `instructions`, 캐시 힌트를 반환하는지. 필수 기능이 빠진 호출이 그것을 이름 밝히며 `-32021`로 돌아오는지. 재시도하는 요청에 그 기능을 선언하면 호출이 완료되는지. 추가로 필요한 것이 없는 툴은 아무것도 선언하지 않아도 되는지. 알 수 없는 툴은 `-32602`인 반면 알 수 없는 메서드는 `-32601`인지. 버전 불일치가 `supported`와 `requested`를 둘 다 이름 밝히는지. 클라이언트의 재시도가 새 id를 쓰는지. 그리고 `_meta`가 통째로 빠진 요청이 거부되는지. 저장소의 와이어 체커는 같은 전송 기록을 2026-07-28 규칙에 직접 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/07-discovery-and-capability-negotiation
```

## 캡스톤 연결

캡스톤의 첫 수는 `server/discover` 호출로, 그 교환의 나머지가 존중하는 캐시 힌트를 반환합니다. 이어지는 툴 호출은 클라이언트가 그 특정 요청에서 올바른 기능을 선언했기 때문에만 성공하고, 그다음 MRTR 유도 교환은 정확히 그 선언에 게이트되어 있습니다. 모든 단계가 이 레슨이 긋는 분할 위에 서 있습니다. 디스커버리는 서버를 한 번, 캐시 가능하게 묘사하고, 기능 선언은 클라이언트를 모든 요청에서 새로 묘사한다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| `server/discover` | 서버가 자신의 버전, 기능, 정체를 광고하기 위해 반드시 구현해야 하는 요청 |
| `DiscoverResult` | 디스커버리의 캐시 가능한 결과. `supportedVersions`, `capabilities`, 선택적 `instructions`, `ttlMs`, `cacheScope` |
| `ServerCapabilities` | 서버가 제공하는 것: tools, resources, prompts, completions, logging, extensions |
| `ClientCapabilities` | 클라이언트가 요청에서 받아들일 수 있는 것: elicitation, sampling, roots, extensions |
| `serverInfo` | 서버가 자기 보고한 이름과 버전. 표시와 로깅용이며 보안 결정용이 절대 아니다 |
| `MissingRequiredClientCapabilityError` | `-32021`. 요청이 자기 `clientCapabilities`가 선언하지 않은 기능을 필요로 할 때 반환 |
| `UnsupportedProtocolVersionError` | `-32022`. 요청이 서버가 구현하지 않은 버전을 이름 밝힐 때 `data.supported`와 `data.requested`와 함께 반환 |
| 요청별 협상(per-request negotiation) | 기능과 버전 사실은 현재 요청에서만 읽고 이전 요청으로부터 결코 추론하지 않는 규칙 |

## 더 읽기

- [디스커버리: server/discover](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
- [버저닝과 호환성](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)
- [베이스 프로토콜 개요와 _meta 규칙](https://modelcontextprotocol.io/specification/2026-07-28/basic/index)
- [스키마 참조: DiscoverResult, ClientCapabilities, ServerCapabilities](https://modelcontextprotocol.io/specification/2026-07-28/schema#discoverresult)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md` 6절
