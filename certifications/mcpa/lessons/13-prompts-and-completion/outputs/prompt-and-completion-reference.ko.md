> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [prompt-and-completion-reference.md](prompt-and-completion-reference.md)

# 프롬프트와 Completion 참고 자료

MCPA '상호작용과 실행' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## prompts/list

- 캐시 가능하고 페이지네이션됩니다: `resultType: "complete"` 결과는 `ttlMs`(정수, 0 이상)와 `cacheScope`(`public` 또는 `private`)를 실어 옵니다.
- 요청은 선택적인 불투명한(opaque) `cursor`를 받고, 결과는 다른 페이지가 남아 있을 때만 `nextCursor`를 포함합니다.
- 연결마다 달라져서는 안 되고, 요청의 인가에 따라 달라질 수는 있습니다.
- 알아들을 수 없는 커서는 `-32602`이지, 조용히 첫 페이지로 떨어지는 게 아닙니다.

## prompts/get

- 요청: `name`과 문자열 `arguments` 맵.
- 캐시 가능한 여섯 연산에 포함되지 않습니다: 결과에 `ttlMs`도 `cacheScope`도 없습니다.
- 최종 결과 대신 `InputRequiredResult`로 답할 수 있습니다(다중 왕복 요청, MRTR).
- 결과는 `description`과 `messages`를 실으며, 각 메시지는 `role`(`user` 또는 `assistant`)에 콘텐츠 블록 하나입니다.

## PromptMessage 콘텐츠 타입

| 타입 | 실어 옮기는 것 | 일반적인 용도 |
|------|---------|-------------|
| `text` | `text` | 렌더링된 지시문. 인자는 이미 치환됨 |
| `image` | base64 `data`, `mimeType` | 메시지 안에 끼워 넣은 시각적 컨텍스트 |
| `audio` | base64 `data`, `mimeType` | 메시지 안에 끼워 넣은 오디오 컨텍스트 |
| `resource_link` | `uri`, `name`, 선택적 `description`, `mimeType` | 바이트를 넣지 않고 리소스를 가리킴 |
| `resource`(임베디드) | `uri`, `mimeType`, `text` 또는 `blob` | 작은 리소스 내용을 메시지에 직접 전송 |

## 오류

| 상황 | 코드 |
|-----------|------|
| 모르는 프롬프트 이름 | `-32602` |
| 필수 인자 누락 | `-32602` |
| 알아들을 수 없는 페이지네이션 커서 | `-32602` |
| 서버 내부 실패 | `-32603` |

프롬프트에는 도구식 `isError` 채널이 없습니다. 템플릿 렌더링은 아무것도 실행하지 않으므로, 잘못된 이름이나 빠진 인자는 언제나 프로토콜 오류지 모델이 나중에 뜯어고칠 부분 결과가 아닙니다.

## completion/complete

- 요청: `ref`(이름으로 `ref/prompt`, 또는 URI나 URI 템플릿으로 `ref/resource`), `argument`(`name`, `value`), 선택적 `context.arguments`(이미 확정된 인자 이름과 값).
- 결과: `completion.values`(최대 100개, 순위 매겨짐), 선택적 `total`, 그리고 `hasMore`.
- 실제 일치 수가 100을 넘으면 `hasMore`는 무조건 `true`입니다. 클라이언트가 어떻게 거기까지 도달했든 상관없습니다.
- 캐시 불가: 결과에 `ttlMs`도 `cacheScope`도 없습니다.
- 서버가 `server/discover`에서 `completions: {}` 기능을 선언해야 합니다.

## 참조 타입

| 타입 | 예 |
|------|---------|
| `ref/prompt` | `{"type": "ref/prompt", "name": "code_review"}` |
| `ref/resource` | `{"type": "ref/resource", "uri": "file:///src/{path}"}` |

## 시험을 위해 기억하기

- 프롬프트는 사용자가 통제하고, 도구는 모델이 통제하고, 리소스는 애플리케이션이 이끕니다.
- `prompts/list`는 캐시 가능하고, `prompts/get`과 `completion/complete`은 캐시 불가입니다.
- 모르는 프롬프트, 빠진 필수 인자, 잘못된 커서가 모두 `-32602`입니다.
- `context.arguments`는 사용자가 이미 준 답으로 completion 범위를 좁히는 것이지, 새 답을 만드는 게 아닙니다.
- 100개 상한과 `hasMore`는 페이지네이션 커서와 무관합니다. completion은 커서를 절대 쓰지 않습니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`.
