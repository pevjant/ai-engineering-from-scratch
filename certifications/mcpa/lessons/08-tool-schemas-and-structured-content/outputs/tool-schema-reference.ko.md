> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [tool-schema-reference.md](tool-schema-reference.md)

# 도구 스키마 참고 자료

MCPA '아키텍처와 구성 요소' 도메인을 위한 한 페이지 참고 자료입니다. 도구 정의 안의 필드들, inputSchema와 outputSchema를 다스리는 JSON Schema 규칙, 그리고 규격을 따르는 2026-07-28 서버가 분리해 두는 두 개의 오류 채널을 다룹니다.

## 도구 정의의 필드들

- **name**: 한 서버 안에서 유일. 아래 이름 규칙 참고.
- **title**: 선택. 사람이 읽는 표시용 이름.
- **description**: 모델이 관련성을 판단할 때 읽는 자연어 텍스트.
- **icons**: 선택. https 또는 data URI만 가능하며 서버와 같은 오리진이어야 함.
- **inputSchema**: JSON Schema 객체. 필수이며 절대 null이 아니어야 함.
- **outputSchema**: 선택. structuredContent를 제약하는 JSON Schema 객체.
- **annotations**: 선택적 힌트(readOnlyHint, destructiveHint, idempotentHint, openWorldHint). 서버 자체를 신뢰하지 않는다면 신뢰하지 않는 것이 원칙.

## JSON Schema 방언(dialect)

- `$schema` 필드가 없으면 스키마는 JSON Schema 2020-12를 기본으로 삼습니다.
- 스키마는 `$schema`로 다른 방언을 명시적으로 선언할 수 있습니다.
- SEP-2106 이후, inputSchema는 `type: object`를 유지하되 그 밖의 2020-12 키워드(`oneOf`, `anyOf`, `allOf`, `if`/`then`/`else`, `$defs`)를 허용합니다. outputSchema는 `type: object` 요구 없이 어떤 유효한 JSON Schema든 허용합니다.
- 파라미터 없는 도구: `{"type": "object", "additionalProperties": false}` 형태가 권장됩니다. 빈 객체만 받아들입니다.

## $ref 규칙

- 네트워크 URI로 풀리는 `$ref`를 자동으로 역참조(dereference)하지 마세요. 자동으로 따라가도 안전한 건 `#/$defs/Foo` 같은 같은 문서 안의 포인터뿐입니다.
- 네트워크 가져오기(fetch) 모드를 아예 제공한다면, 기본은 비활성이어야 하고 허용 목록(allowlist)·시간 제한·크기 제한이 있어야 합니다.
- 풀리지 않은 외부 `$ref` 때문에 검증에 실패하는 스키마는 관대하게 통과시키지 말고 거부해야 합니다.
- 조합 키워드(`anyOf`, `oneOf`, `allOf`, `if`/`then`/`else`)와 `$defs`는 서비스 거부 공격에 대비해 깊이·서브스키마 수·시간 예산 등으로 상한을 두는 게 좋습니다.

## outputSchema와 structuredContent

- `structuredContent`는 어떤 JSON 값이든 받습니다. 객체, 배열, 문자열, 숫자, 불리언, null 모두 가능합니다.
- outputSchema가 있으면 서버는 그에 맞는 structuredContent를 돌려줘야 하고, 클라이언트는 이를 검증하는 것이 좋습니다.
- 호환성을 위해 structuredContent를 돌려주는 도구는 같은 값을 `text` 콘텐츠 블록에도 직렬화해서 넣어 주는 것이 좋습니다.

## 도구 이름 규칙

- 1자부터 128자까지, 대소문자를 구분합니다.
- 허용되는 문자: `A-Z`, `a-z`, `0-9`, 밑줄, 하이픈, 점.
- 공백, 쉼표, 그 밖의 특수 문자는 안 됩니다.
- 한 서버 안에서 유일해야 합니다. 애그리게이터는 이름 앞에 서버 식별자를 붙이는데, `serverInfo.name`은 유일하다고 보장되지 않기 때문입니다.

## 두 개의 오류 채널

| 상황 | 채널 | 예 |
|---|---|---|
| 지목된 도구가 이 서버에 존재하지 않음 | JSON-RPC 오류 | `-32602` Invalid params |
| 요청 자체가 CallToolRequest 스키마를 통과하지 못함 | JSON-RPC 오류 | `-32602` Invalid params |
| 인자가 도구 자신의 inputSchema를 통과하지 못함 | 도구 실행 오류 | `isError: true`를 담은 결과 |
| 핸들러 내부의 비즈니스 규칙이 호출을 거부함 | 도구 실행 오류 | `isError: true`를 담은 결과 |

스키마에 맞지 않는 인자는 결코 `-32602`가 아닙니다. 그 코드는 서버가 실행 시도조차 할 수 없는 요청, 예컨대 서버가 광고한 적 없는 도구 이름을 위한 것입니다. 모델이 다른 인자로 다시 시도해서 고칠 수 있는 것은 전부 `isError: true`를 담은 정상 결과로 가야 합니다. 모델의 컨텍스트에 확실히 닿는 채널은 그쪽뿐이기 때문입니다(SEP-1303).

## 이 도메인의 시험 사실

- 아키텍처와 구성 요소는 MCPA 블루프린트의 일부입니다.
- 시험은 MCP 명세 2026-07-28에 맞춰져 있습니다.
- 출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 5절과 10절.
