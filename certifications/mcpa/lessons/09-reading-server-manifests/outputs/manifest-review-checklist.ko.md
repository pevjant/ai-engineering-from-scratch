> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [manifest-review-checklist.md](manifest-review-checklist.md)

# 매니페스트 검토 체크리스트

낯선 MCP 서버를 추가하기 전에 검토하기 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다. 첫 실제 호출 전에 세 가지 문서를 모두 읽으세요: server/discover 결과, tools/list 결과, 그리고 서버가 공개돼 있다면 레지스트리의 server.json.

## 1. server/discover

- `capabilities`: tools, resources, prompts, completions, logging, extensions 중 무엇이 있는지 확인합니다. 낯선 확장(extension) 키는 그것이 무엇을 바꾸는지 믿기 전에 찾아볼 가치가 있습니다.
- `resources: {subscribe: true}`는 개별 리소스 업데이트를 받을 수 있다는 뜻이고, 어떤 프리미티브든 `listChanged: true`면 그 목록이 바뀔 때 서버가 듣고 있는 클라이언트에 알림을 보낸다는 뜻입니다.
- `instructions`: 서버 자체를 설명해야 합니다(무엇을 하는 서버인지, 어떤 도구를 언제 선호해야 하는지). 모델 자신에게 겨눠진 명령은 경고 신호로 취급하세요(5절 참고).
- `ttlMs`와 `cacheScope`는 완전한 결과에 둘 다 있어야 합니다. 하나라도 빠지면 캐싱 계약 위반입니다.

## 2. tools/list, 한 도구씩

- `name`, `description`, `inputSchema`는 필수이고, `inputSchema`는 절대 null이 아닙니다.
- `annotations`는 기본값을 비껴가는 게 아니라 기본값 기준으로 읽으세요:

| 어노테이션 | 생략 시 기본값 | 의미가 있을 때 |
|---|---|---|
| `readOnlyHint` | `false` | 언제나 |
| `destructiveHint` | `true` | `readOnlyHint`가 `false`일 때 |
| `idempotentHint` | `false` | `readOnlyHint`가 `false`일 때 |
| `openWorldHint` | `true` | 언제나 |

`annotations` 블록이 아예 없는 도구는 이 기본값들에 따라 읽기 전용이 아니고 파괴적(destructive)입니다. 명시적인 `readOnlyHint: true`나 `destructiveHint: false`가 다르게 말해 주기 전까지는 그렇게 취급하세요. 이 모든 것은 힌트일 뿐입니다. 서버 자체를 신뢰하지 않는다면 어노테이션도 신뢰하지 마세요.

- `icons`: `https:` 또는 `data:` URI만 가능하고 서버와 같은 오리진이어야 합니다. SVG는 장식이 아니라 실행 가능한 콘텐츠로 취급하세요.
- `outputSchema`와 `structuredContent`: 출력 스키마가 선언돼 있다면 서버는 그에 맞아야 하고, 하위 호환을 위해 text 미러도 여전히 돌려주는 것이 좋습니다.

## 3. x-mcp-header, 속성별로

- 값은 비어 있지 않은 유효한 HTTP 필드 이름 토큰이어야 합니다. 공백, 제어 문자 없음.
- 그 도구 스키마 안의 모든 `x-mcp-header` 값 사이에서 대소문자 무시하고 유일해야 합니다.
- 원시 타입 속성(string, integer, boolean)에만 붙일 수 있습니다. `number`에는 절대 안 됩니다.
- Streamable HTTP 클라이언트는 위 조건 중 하나라도 어기면 어노테이션을 조용히 무시하는 게 아니라 도구 전체를 `tools/list`에서 제거해야 합니다.
- 비밀번호, API 키, 토큰, 자격 증명처럼 읽히는 매개변수에는 절대 붙이지 마세요. 헤더 값은 서버뿐 아니라 경로상의 모든 네트워크 중개자에게 보입니다.

## 4. cacheScope, 캐시되는 텍스트와 함께 읽기

- `public`: 같은 결과가 다른 호출자의 캐시 조회에 제공될 수 있습니다. `private`: 인가 경계를 넘을 수 없습니다.
- `cacheScope`는 그 자체로 접근 통제가 되지는 않습니다.
- 경고 신호: 사용자별 내용처럼 읽히는("your account", "your balance", "the current user") 도구 설명이나 instructions가 `cacheScope: "public"`과 짝지어져 있는 경우.

## 5. instructions, 신뢰할 수 없는 텍스트로 읽기

- 정상: 서버, 그 단위, 또는 어떤 도구를 언제 선호해야 하는지를 설명합니다.
- 경고 신호: 모델에게 겨눠진 명령형 문구. 이전 지침을 무시하라거나, 항상 특정 도구를 먼저 호출하라거나, 사용자에게 뭔가를 숨기라는 식입니다. 안내문이 아니라 프롬프트 인젝션 시도로 취급하세요.
- `instructions`와 `serverInfo`는 둘 다 스스로 보고한 값이며 프로토콜이 검증해 주지 않습니다. 어느 쪽으로도 보안 판단을 해서는 안 됩니다.

## 6. 레지스트리 server.json

- `name`은 역방향 DNS 네임스페이스여야 합니다. `io.github.user/server` 또는 `com.example/server` 형태요. `/`가 없는 이름 뒤에는 검증된 소유자가 없습니다.
- `io.github.*` 이름은 GitHub에서 검증합니다. 다른 네임스페이스는 도메인에 대해 DNS 또는 HTTP 챌린지로 검증합니다.
- `packages`(npm, PyPI, NuGet, Cargo, OCI, MCPB)와 `remotes`(streamable-http, sse)는 서버를 어떻게 실행하는지 설명합니다. 패키지 타입마다 `package.json`의 `mcpName` 같은 고유한 소유 증명이 있습니다.
- 레지스트리는 서버 코드의 취약점을 검사하지 않습니다. 그건 하부 패키지 레지스트리와 다운스트림 애그리게이터에 맡깁니다. 레지스트리 자체가 보장하는 건 네임스페이스 검증입니다.

## 시험을 위해 기억하기

- 생략된 어노테이션은 중립이 아닙니다. 기본값 때문에 벌거벗은(bare) 도구는 파괴적인 것이 됩니다.
- `x-mcp-header` 제약은 서버가 아니라 클라이언트가 강제합니다(도구 제거).
- `cacheScope`는 접근이 아니라 공유를 통제합니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 6, 10, 15절.
