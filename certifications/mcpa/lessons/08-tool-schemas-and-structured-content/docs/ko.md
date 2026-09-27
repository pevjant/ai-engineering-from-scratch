> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 툴 정의 안의 계약

> inputSchema는 모델이 어물쩡 넘어갈 수 있는 제안이 아닙니다. 서버는 핸들러가 실행되기도 전에 인자를 그 스키마로 검사하고, 깨진 인자조차 모델이 읽고 고칠 수 있는 결과로 돌아옵니다.

**유형:** 레퍼런스
**언어:** Python
**선수 지식:** 레슨 07
**시간:** 약 45분

## 학습 목표

- 이름과 설명을 넘어서는 툴 정의의 필드들 — outputSchema, icons, annotations 포함 — 을 말하고, inputSchema가 절대 아니어야 하는 단 하나의 것 말하기
- JSON Schema 2020-12가 inputSchema와 outputSchema의 기본 방언(dialect)인 이유, 스키마가 명시적으로 다른 방언을 선언하는 경우, 그리고 SEP-2106이 스키마가 쓸 수 있는 키워드를 무엇까지 허용하게 풀었는지 설명하기
- structuredContent가 outputSchema에 어떻게 부합(conform)하는지 추적하고, 서버가 그 같은 값을 왜 텍스트 콘텐츠 블록으로도 직렬화하는지 설명하기
- 툴 명명 규칙을 말하고, 여러 서버를 집계하는 호스트가 serverInfo를 믿지 않고 이름에 접두사를 붙이는 이유 설명하기
- 알 수 없는 툴(프로토콜 오류)과 스키마를 통과하지 못한 인자(isError true인 툴 실행 오류)를 분리하고, 두 번째만이 확실하게 모델에게 도달하는 이유 설명하기

## 문제 상황

레슨 07의 디스커버리 단계는 클라이언트에게 툴 목록을 건겨 줍니다. 각 항목에는 이름과 모델이 읽을 수 있는 설명이 붙어 있죠. 하지만 설명은 산문이고, 산문은 프로그램이 인자 객체를 대조 검사할 수 있는 것이 아닙니다. "SKU로 제품을 찾는다"는 말은 독자에게 툴이 무엇을 하는지 알려 주지만, 그 필드가 `sku`인지 `productId`인지, 문자열인지 정수인지, 호출이 그 필드를 아예 빠뜨리면 무슨 일이 일어나야 하는지는 말해 주지 않습니다.

툴 정의는 두 번째, 더 엄격한 부분으로 그 간극을 메웁니다. 바로 inputSchema입니다. 모든 클라이언트와 모든 서버가 같은 방식으로 읽을 수 있는 JSON Schema 객체죠. 그것은 코드 곁에 놓인 문서가 아닙니다. 핸들러의 실행이 허용되기 전에 인자 객체가 갖추어야 할 모양이고, 규격에 맞는 서버는 클라이언트가 인자를 얼마나 꼼꼼히 잘 만들었다고 주장하든 매 호출마다 그것을 검사합니다.

이 검사를 바르게 하는 일이 중요한 두 번째 이유는 시험이 큰 비중을 두는 부분입니다. 스키마 위반과 지어낸 툴 이름은 멀리서 비슷해 보입니다. 둘 다 "호출이 실패했다"는 것이죠. 하지만 MCP 2026-07-28은 이 둘을 와이어 위에서 완전히 다르게 취급합니다. 이 둘을 혼동하는 것은 구현이 저지르는 가장 흔한 실수 중 하나이고, 이 레슨이 쉽지만 틀린 직관 — "모든 잘못된 tools/call은 JSON-RPC 오류로 돌아온다" — 을 바로잡아 주는 지점입니다.

## 개념

툴 정의는 이름, 설명, inputSchema보다 더 많은 것을 실습니다. 전체 집합은 이렇습니다. name, 표시용 선택적 title, description, 선택적 icons, 필수 inputSchema, 선택적 outputSchema, 선택적 annotations(readOnlyHint, destructiveHint 같은 힌트. 서버 자신이 신뢰되지 않는 한 신뢰할 수 없으며, 온전한 매니페스트를 읽는 단계에서 깊이 다룹니다), 그리고 선택적 `_meta`. 그 모든 것을 관통하는 단 하나의 단단한 규칙이 있습니다. inputSchema는 유효한 JSON Schema 객체여야 하고 절대 null이어서는 안 됩니다. 파라미터가 없는 툴을 위한 권장 모양은 `{"type": "object", "additionalProperties": false}`로, 빈 객체만 받아들입니다. `{"type": "object"}`만으로는 아무도 요청하지 않은 속성을 실은 객체조차 여전히 받아들입니다.

inputSchema와 outputSchema는 모두 JSON Schema입니다. 스키마에 `$schema` 필드가 없으면 기본값은 JSON Schema 2020-12입니다. 스키마는 다른 방언을 명시적으로 선언할 수도 있습니다.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {"a": {"type": "number"}},
  "required": ["a"]
}
```

SEP-2106 이전에는 inputSchema가 type, properties, required로 제한되어 oneOf 같은 구성(composition) 키워드를 쓸 수 없었습니다. SEP-2106 이후 inputSchema는 type: object(인자는 언제나 객체입니다)를 유지하되 그 밖의 모든 2020-12 키워드를 허용하고, outputSchema는 아예 유효한 JSON Schema라면 무엇이든 허용합니다. type: object 요구도 없습니다. 툴의 출력은 객체일 수도, 배열일 수도, 원시 값일 수도 있기 때문입니다.

```json
{
  "type": "object",
  "oneOf": [
    {"properties": {"id": {"type": "string"}}, "required": ["id"]},
    {"properties": {"name": {"type": "string"}}, "required": ["name"]}
  ]
}
```

스키마가 임의의 JSON Schema를 실을 수 있게 되면 두 가지 제약이 적용됩니다. 첫째, 네트워크 URI로 해석되는 `$ref` — `#/$defs/Sku` 같은 같은 문서 포인터가 아니라 절대 https 주소 — 는 절대 자동으로 역참조(dereference)되어서는 안 됩니다. 만나는 모든 `$ref`를 페치해 오는 순진한 검증기는 공격자에게 서버가 임의의 호스트로 요청을 보내게 만들 방법을 쥐여 주는 셈입니다. 옵트인(opt-in) 페치 모드가 존재할 수는 있지만 기본값은 꺼져 있어야 하고, 허용 목록(allowlist)에 묶여 있어야 하며, 경계가 있어야 합니다. 둘째, 구성 키워드(anyOf, oneOf, allOf, if/then/else)와 `$defs`는 깊이, 서브스키마 개수, 시간 예산 중 하나로 경계가 있어야 합니다. 병적인(pathological) 스키마가 검증 자체를 서비스 거부 공격으로 바꾸지 못하게 하기 위해서입니다.

outputSchema와 structuredContent는 함께 동작합니다. structuredContent는 객체만이 아니라 어떤 JSON 값이든 될 수 있습니다. outputSchema가 그렇게 말한다면 레코드 배열이나 맨 숫자도 모두 합법입니다. outputSchema가 존재하면 서버는 그것에 부합하는 structuredContent를 반환해야 하고, 텍스트만 읽는 클라이언트와의 호환성을 위해 서버는 그 같은 값을 텍스트 콘텐츠 블록으로도 직렬화해야 합니다.

```json
{
  "content": [{"type": "text", "text": "{\"sku\": \"SKU-100\", \"priceUsd\": 24.99}"}],
  "structuredContent": {"sku": "SKU-100", "priceUsd": 24.99}
}
```

이름에도 규칙이 있습니다. 1자에서 128자, 대소문자 구분, 문자, 숫자, 밑줄, 하이픈, 점으로만 구성, 하나의 서버 안에서 고유. 여러 서버에서 툴을 모아 오는 호스트는 여전히 search 같은 이름에서 충돌할 수 있고, 그래서 serverInfo.name에 기대지 않고 서버 식별자로 이름에 접두사를 붙입니다. 사양은 serverInfo.name의 고유성을 명시적으로 보장하지 않습니다.

이제 그 바로잡음입니다. 인자가 inputSchema를 통과하지 못할 때 — 필수 필드가 빠졌거나, 유형이 틀렸거나, enum 밖의 값이거나, 스키마가 금지한 여분 속성일 때 — 그것은 툴 실행 오류입니다. isError: true와 무엇을 고쳐야 하는지 설명하는 content를 담은 정상 결과죠. JSON-RPC 오류가 아니며, 특히 -32602가 아닙니다. 프로토콜 오류 — 서버가 광고한 적 없는 툴 이름에 대한 -32602, 또는 CallToolRequest 스키마 자체를 통과하지 못하는 요청 — 는 모델이 더 나은 인자를 시도해서 고칠 수 없는 문제를 위해 따로 남겨 둔 것입니다. SEP-1303이 구현들이 스키마 실패를 계속 프로토콜 오류로 보고하던 것을 바로잡아 이 분할을 명시했습니다. 클라이언트가 모델에게 확실하게 보여 주는 것은 툴 실행 오류뿐이라서, 프로토콜 오류 안에 숨겨진 검증 실패는 모델이 이유를 배울 방법 없이 같은 실수를 반복하게 만든다는 것이죠.

```figure
mcpa-08-schema-contract
```

## 인터랙티브 랩

그림은 하나의 툴의 inputSchema와 outputSchema를 왼쪽에 놓고, 호출을 핸들러로 통과시키거나 되돌려 보내는 validate 단계를 그 옆에 둡니다. 두 갈래 결말을 따라가 보세요. 스키마 실패는 핸들러에 절대 도달하지 않는 점선 경로 위에서 isError: true를 담은 결과를 만들어 냅니다. 통과하면 핸들러가 실행되고 structuredContent가 그 텍스트 거울(mirror) 옆에 만들어집니다. 오른쪽에는 서버가 광고한 적 없는 이름이 완전히 별개의 경로로 곧장 프로토콜 오류 -32602로 향합니다. 존재하지 않는 툴에는 대조해 볼 스키마가 없기 때문입니다. code/main.py를 열어 실행한 뒤, 출력된 각 응답이 두 경로 중 어느 쪽에서 나왔는지 짝지어 보세요.

```bash
python3 code/main.py
```

전송 기록을 순서대로 읽으세요. 유효한 lookup_product 호출, 그다음 스키마를 실패하는 네 가지 방법(빠진 sku, region enum 밖의 값, 잘못된 유형으로 보낸 sku, 스키마가 금지한 여분 속성), 그다음 파라미터 없는 server_time 툴을 올바르게 호출한 것과 받아들이지 않는 속성을 실어 호출한 것, 마지막으로 서버가 등록한 적 없는 툴을 이름으로 부르는 호출입니다. 스키마 실패는 모두 isError: true 콘텐츠로 돌아옵니다. JSON-RPC 오류로 돌아오는 것은 마지막의 알 수 없는 이름뿐입니다.

## 연습 랩

code/main.py의 build_catalog_server에 세 번째 툴 list_regions을 추가해 보세요. outputSchema가 루트에서 객체가 아니라 문자열 배열을 묘사하도록 하여, SEP-2106이 허용하는 배열과 원시 값 structuredContent에 맞춥니다. 권장되는 무파라미터 형태로 비어 있는 inputSchema를 주고, 핸들러가 평범한 Python 리스트를 반환하게 하세요. 반환한 배열이 새 스키마 기준으로 필수 필드나 유형 오류가 없음을 validate_arguments로 확인하세요(이 레슨의 검증기는 type, properties, required, enum, additionalProperties를 검사합니다. 프로덕션 JSON Schema 라이브러리가 2020-12 어휘 전체로 확장하는 것과 같은 부분집합입니다). 그다음 attempt_network_ref_registration에서 이미 거부된 호스트와 다른 네트워크 호스트를 가리키는 $ref를 inputSchema에 담은 툴을 등록해 보세요. 그 툴을 향한 어떤 호출도 실행되기도 전에 등록이 같은 방식으로 거부되는지 확인하세요.

## 제공되는 산출물

outputs/tool-schema-reference.md는 한 페이지짜리 참조 자료입니다. 툴 정의의 모든 필드, JSON Schema 방언과 $ref 규칙, outputSchema와 structuredContent 계약, 툴 명명 규칙, 그리고 두 오류 채널을 각각의 구체적 예와 대조한 표가 담겨 있습니다. 낯선 서버의 tools/list 결과 옆에 펼쳐 두세요. 보내려는 호출이 통과할지 빠르게 판단할 때 필요합니다.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요.

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 확인합니다. 유효한 인자가 outputSchema 기준 검증을 스스로 통과하는 structuredContent를 만드는지. 빠진 필수 필드, 틀린 유형, enum 위반, 금지된 여분 속성이 모두 JSON-RPC 오류가 아니라 isError: true로 돌아오는지. 무파라미터 스키마가 빈 객체는 받아들이고 여분 속성이 있는 객체는 거부하는지. 알 수 없는 툴 이름이 isError가 아니라 프로토콜 오류로 돌아오는지. 네트워크 $ref가 등록 단계에서 거부되는지. 그리고 툴 명명 규칙이 옳은 이름을 받아들이고 틀린 이름을 거부하는지. 저장소의 와이어 체커도 이 레슨의 전송 기록을 2026-07-28 규칙에 맞춰 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/08-tool-schemas-and-structured-content
```

## 캡스톤 연결

캡스톤 리뷰는 여러분이 조립한 생태계의 모든 툴을 방어하라고 요구합니다. 그리고 "스키마가 잡아 줄 것"이라는 말은 스키마가 정밀하고 서버가 그것을 실제로 프로토콜 오류가 아니라 툴 실행 오류로 강제할 때만 참입니다. 클라이언트가 모델에게 숨길 수도 있는 프로토콜 오류가 아니라요. 캡스톤 설계의 어떤 툴이 사용자 입력을 받거나 공유 스키마 조각을 참조할 때는 명명 규칙과 $ref 거부를 꺼내 오고, 핸들러가 발견한 문제를 어떻게 보고할지 결정할 때는 언제나 두 채널 오류 분할을 꺼내 오세요.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| inputSchema | 툴 정의의 필수 JSON Schema 객체. 유효한 인자 객체가 만족해야 하는 조건 |
| outputSchema | structuredContent가 부합해야 하는 선택적 JSON Schema 객체 |
| structuredContent | 툴 결과가 반환하는 임의의 JSON 값. outputSchema가 존재하면 그에 따라 검증된다 |
| additionalProperties | false로 설정하면 선언되지 않은 속성을 실은 인자 객체를 거부하는 스키마 키워드 |
| $ref | 다른 위치를 가리킬 수 있는 스키마 키워드. 네트워크 URI 대상은 절대 자동 역참조하면 안 된다 |
| 툴 실행 오류 | isError true를 담은 정상 결과. 스키마 실패처럼 모델이 읽고 고칠 수 있는 문제를 보고한다 |
| 프로토콜 오류 | -32602 같은 JSON-RPC 오류. 알 수 없는 툴 이름처럼 인자 조정으로 모델이 고칠 수 없는 문제를 보고한다 |
| 툴 명명 규칙 | 1~128자, 대소문자 구분, 문자·숫자·밑줄·하이픈·점만 허용, 서버 안에서 고유 |

## 더 읽기

- [MCP 사양 2026-07-28, Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) — 이 레슨이 다루는 규범적 필드, 스키마 규칙, 오류 처리
- [MCP 사양 2026-07-28, JSON Schema 사용](https://modelcontextprotocol.io/specification/2026-07-28/basic/index#json-schema-usage) — 방언과 $ref 해석 규칙
- [SEP-2106, tools inputSchema와 outputSchema가 JSON Schema 2020-12에 부합](https://modelcontextprotocol.io/seps/2106-json-schema-2020-12)
- [SEP-1303, 입력 검증 오류를 툴 실행 오류로](https://modelcontextprotocol.io/seps/1303-input-validation-errors-as-tool-execution-errors)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md` 5, 10절
- `phases/13-tools-and-protocols/05-tool-schema-design` — 모델 선택을 위한 명명과 파라미터 설계
- `phases/13-tools-and-protocols/28-mcp-tool-contracts-and-content` — JSON Schema 런타임 경계와 콘텐츠 블록
