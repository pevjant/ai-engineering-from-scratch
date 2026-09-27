> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# MCP 서버 만들기: 무상태 Python과 TypeScript

> 현대 MCP 서버는 핸드셰이크를 기억하지 않습니다. 모든 요청의 메타데이터를 검증하고, 핸들러 하나를 실행하고, 타입화된 결과 하나를 돌려줍니다.

**유형:** Build(빌드)
**언어:** Python, TypeScript
**선수 지식:** 페이즈 13, 레슨 06
**시간:** 약 85분

## 학습 목표

- MCP `2026-07-28`의 필수 `server/discover`를 구현할 수 있습니다.
- 모든 요청에서 프로토콜 버전과 클라이언트 기능을 검증할 수 있습니다.
- 결정론적 목록 순서로 도구, 리소스, 프롬프트를 노출할 수 있습니다.
- 올바른 결과에 `resultType`, 서버 신원, 캐시 힌트를 붙일 수 있습니다.
- 줄바꿈 구분 stdio 위에서 같은 무상태 계약을 Python과 TypeScript로 서빙할 수 있습니다.

## 문제

첫 메시지 이후 클라이언트 기능을 저장하는 서버는 만들기 쉽고 운영하기 어렵습니다. 같은 프로세스가 연속된 클라이언트를 서빙할 수 있습니다. 원격 요청은 다른 워커에 떨어질 수 있습니다. 낡은 기능 선언이 인가 경계를 넘어 동작을 새어 나가게 할 수 있습니다.

MCP `2026-07-28`은 모든 요청을 자기 기술적으로 만들어 문제의 프로토콜 부분을 해결합니다. 애플리케이션은 여전히 내구성 있는 노트, 작업, 명시적 상태 핸들을 유지할 수 있습니다. 유지할 수 없는 것은 이후 요청의 디코딩 방식을 바꿔 버리는 숨겨진 프로토콜 상태입니다.

이 레슨은 노트 서버를 두 번 만듭니다. Python과 TypeScript 버전은 프로토콜 코어에 각자의 표준 라이브러리만 씁니다. 둘 다 같은 메서드를 노출하고 같은 와이어 계약을 강제합니다.

## 개념

### 현대 디스패치 루프

```text
read one JSON-RPC line
parse the envelope
if it is a notification, do not respond
validate params._meta for this request
route by method
wrap success with resultType and serverInfo
write one JSON-RPC response line
forget request-scoped metadata
```

세 가지 stdio 규칙은 여전히 중요합니다:

- stdout에는 JSON-RPC 메시지만 씁니다. 진단은 stderr로 보냅니다.
- 메시지를 줄바꿈으로 구분하고 각 응답을 플러시합니다.
- stdin이 EOF에 도달하면 즉시 종료합니다.

프로세스 수명은 전송 수명입니다. 현대 MCP 세션이 아닙니다.

### 요청 검증

모든 요청에는 다음이 있어야 합니다.

```json
{
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": {
        "name": "notes-client",
        "version": "1.0.0"
      }
    }
  }
}
```

처음 두 필드는 필수입니다. `clientInfo`는 권장입니다. 신원 모양이 있으면 검증하되, 인증으로 취급하지는 마세요.

버전이 지원되지 않으면 `requested`와 `supported`를 담은 코드 `-32022`를 돌려줍니다. 요청 메타데이터가 빠진 것은 유효하지 않은 params이며 코드 `-32602`입니다. 빠진 필드를 이전 호출로 채우는 일은 절대 없어야 합니다.

### 필수 디스커버리

현대 서버는 `server/discover`를 구현해야 합니다. 완전한 디스커버리 결과에는 지원되는 현대 버전, 기능, 선택적 지침, 캐시 힌트, 그리고 결과 `_meta` 속의 서버 신원이 포함됩니다:

```json
{
  "resultType": "complete",
  "supportedVersions": ["2026-07-28"],
  "capabilities": {
    "tools": {"listChanged": false},
    "resources": {"listChanged": false, "subscribe": false},
    "prompts": {"listChanged": false}
  },
  "ttlMs": 3600000,
  "cacheScope": "public",
  "_meta": {
    "io.modelcontextprotocol/serverInfo": {
      "name": "notes-server",
      "version": "2.0.0"
    }
  }
}
```

디스커버리가 서버의 잠금을 풀지는 않습니다. 클라이언트는 디스커버리를 호출하지 않고도 `tools/list`를 부를 수 있습니다. `tools/list`가 이미 같은 요청 메타데이터를 실고 있기 때문입니다.

### 도구

`tools/list`는 결정론적인 도구 디스크립터 목록을 돌려줍니다. 안정적인 순서는 응답 캐싱을 개선하고 모델 컨텍스트를 안정적으로 유지합니다. 결과에는 `ttlMs`와 `cacheScope`도 필요합니다.

`tools/call`은 콘텐츠 블록과 `isError`를 돌려줍니다. 프로토콜 봉투나 메서드 파라미터가 잘못됐을 때는 JSON-RPC 에러를 씁니다. 유효한 도구 호출이 실행됐는데 도구 자체가 실패했을 때는 `isError: true`를 씁니다.

도구 주석은 여전히 힌트이지 강제가 아닙니다:

- `readOnlyHint`
- `destructiveHint`
- `idempotentHint`
- `openWorldHint`

호스트는 이것을 확인과 표시에 써야 합니다. 서버는 여전히 실제 인가를 강제해야 합니다.

### 리소스

`resources/list`는 안정적인 URI 디스크립터를 돌려줍니다. `resources/read`는 타입화된 콘텐츠를 돌려줍니다. 둘 다 `2026-07-28`에서 캐시 가능하므로 둘 다 `ttlMs`와 `cacheScope`를 포함합니다.

사용자별 노트 데이터에는 `cacheScope: "private"`을 쓰세요. 공유 캐시는 인가 컨텍스트를 넘어 비공개 응답을 재사용해서는 안 됩니다.

현대의 변경 전달은 `resources/subscribe`를 쓰지 않습니다. 클라이언트가 `subscriptions/listen`을 열고 `resourceSubscriptions` 또는 목록 변경 범주를 요청합니다. 레슨 10이 그 흐름을 만듭니다.

### 프롬프트

`prompts/list`는 캐시 가능하고 결정론적입니다. `prompts/get`은 인자와 함께 이름 붙은 프롬프트를 렌더링합니다. 렌더링된 프롬프트 결과는 완전(complete)하지만, 캐시 힌트가 필요한 캐시 가능한 목록/읽기 결과에는 속하지 않습니다.

### 모든 성공 결과는 타입화된다

예제는 모든 성공에 하나의 래퍼를 씁니다:

```python
def complete(payload):
    return {
        "resultType": "complete",
        **payload,
        "_meta": {SERVER_INFO_KEY: SERVER_INFO},
    }
```

목록, 읽기, 디스커버리 핸들러는 `ttlMs`와 `cacheScope`를 더합니다. 이 래퍼를 중앙화하면 어떤 핸들러도 현대 결과 필드를 조용히 빠뜨리지 못합니다.

### 서버가 시작하는 요청 없음

현대 서버는 클라이언트 요청과 관련된 알림이나, 클라이언트가 연 `subscriptions/listen` 스트림 위의 알림은 보낼 수 있습니다. 자기 자신의 JSON-RPC 요청을 보내서는 안 됩니다.

핸들러가 샘플링, 일라시테이션(elicitation), 루트 입력이 필요하면 `input_required` 결과를 돌려줍니다. 클라이언트가 내장된 입력 요청을 이행하고 새 요청 id로 원래 메서드를 재시도합니다. 레슨 11이 그 다중 왕복 요청(Multi Round-Trip Request) 패턴을 다룹니다.

### 명시적인 레거시 호환성

이중 시대 서버는 명확히 분리된 레거시 분기에서 `2025-11-25` 핸드셰이크를 구현할 수도 있습니다. 필수 현대 `_meta` 필드가 있으면 현대 동작을, `initialize`를 받으면 레거시 동작을 고릅니다.

`2026-07-28` 요청을 레거시 핸드셰이크 경로로 흘려 보내지 마세요. 레거시 초기화 결과에 현대 `resultType` 필드를 도장 찍지 마세요. 이 레슨의 코드는 불변 조건이 잘 보이도록 의도적으로 현대 전용입니다.

```figure
t3-dispatch-loop
```

## 활용하기

Python 서버의 유한 데모와 테스트를 실행하세요:

```bash
cd code
python3 main.py --demo
python3 -m unittest discover tests -v
```

TypeScript 포트를 TypeScript 러너로 실행하세요:

```bash
npx tsx main.ts --demo
```

데모는 `server/discover`를 보내고 각 원시 기능을 나열하고, 도구를 호출하고, 미지원 버전 에러를 보여 줍니다. 모든 현대 요청은 메타데이터를 반복합니다. 모든 성공에는 서버 신원이 포함됩니다.

## 출시하기

이 레슨은 `outputs/skill-mcp-server-scaffolder.md`를 출시합니다. 디스커버리 계약, 요청별 검증, 결정론적 캐시 가능 목록, 선택적인 고립된 레거시 어댑터를 갖춘 현대 서버 계획을 만들어 냅니다.

## 연습 문제

1. 한 요청에서 기능을 제거하고, 서버가 이전 요청의 선언을 재사용하지 않음을 증명하세요.
2. `TOOLS`, `PROMPTS`, 노트 삽입 순서를 뒤집으세요. 모든 목록 결과가 안정적으로 유지되는지 확인하세요.
3. 파괴적인 `notes_delete` 도구를 추가하고 실행기 안의 인가 검사를 요구하세요. `destructiveHint`는 UX 힌트로만 유지하세요.
4. `ttlMs`, `cacheScope`, 결정론적 순서를 갖춘 `resources/templates/list`를 추가하세요.
5. `2025-11-25`용 별도의 레거시 어댑터를 만드세요. 현대 요청이 절대 그것으로 들어가지 않음을 증명하는 테스트를 추가하세요.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 무상태 서버 | 프로토콜 세션 기억 없이 각 요청을 그 요청의 메타데이터만으로 처리함 |
| `server/discover` | 버전과 기능을 알리는 필수 현대 메서드 |
| 완전한 결과 | `resultType: "complete"`를 가진 성공적인 현대 결과 |
| 캐시 가능한 결과 | `ttlMs`와 `cacheScope`를 가진 디스커버리, 목록, 리소스 읽기 결과 |
| 결정론적 목록 | 같은 논리적 레지스트리가 같은 항목 순서를 만들어 냄 |
| 서버 신원 | 결과 `_meta`의 권장 `io.modelcontextprotocol/serverInfo` |
| 도구 에러 | `isError: true`와 함께 콘텐츠를 돌려주는 유효한 도구 호출 |
| 프로토콜 에러 | `error`로 돌려주는 잘못된 JSON-RPC 또는 MCP 요청 |

## 더 읽기

- [MCP 사양 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/)
- [MCP 서버 디스커버리](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
- [MCP 도구](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [MCP 리소스](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
- [MCP 프롬프트](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
- [MCP stdio 전송](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
