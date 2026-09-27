> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 프롬프트 템플릿과 인자 자동 완성

> 프롬프트는 서버가 써서 사용자가 골라 실행하는 템플릿입니다. 그것을 고른 사람이 놀랄 만한 요소는 아무것도 없어야 합니다.

**유형:** 참고 자료
**사용 언어:** Python
**선수 지식:** 레슨 12
**소요 시간:** 약 45분

## 학습 목표

- 프롬프트가 사용자 제어인 이유, 그리고 그것이 모델 제어인 도구 프리미티브, 애플리케이션 주도인 리소스 프리미티브와 어떻게 다른지 설명합니다
- 인자, 페이지네이션 커서, 캐시 힌트를 포함해 `prompts/list`와 `prompts/get`의 요청과 결과를 읽습니다
- 텍스트와 리소스 링크로 `PromptMessage` 콘텐츠를 구성하고, 호출자가 공급한 인자를 템플릿에 치환해 넣습니다
- 모르는 프롬프트 이름, 빠진 필수 인자, 알 수 없는 페이지네이션 커서에 `-32602`를 돌려줍니다
- `ref/prompt`와 `ref/resource` 참조, `context.arguments`, 그리고 100개 값 상한과 `hasMore`를 곁들인 `completion/complete`를 사용합니다

## 문제 상황

사용자가 슬래시 명령어를 입력하게 하는 호스트는 그 명령이 확장될 텍스트를 담아둘 곳이 필요합니다. 템플릿 몇 개를 클라이언트에 하드코딩할 수도 있지만, 그러면 새 템플릿마다 클라이언트 릴리스가 필요하고 두 호스트가 같은 집합에 합의하는 일도 없습니다. 매번 모델에게 문구를 지어내게 할 수도 있지만, 그러면 팀이 한 번 써서 모두가 같은 방식으로 재사용하길 바라는, 그 신중하고 검토를 거친 프롬프트가 실행될 때마다 조금씩 다르게 흘러갑니다.

MCP는 그 텍스트를 서버 위에, 바로 이 목적을 위해 만들어진 프리미티브 뒤에 자리를 마련해 줍니다. 사용자가 의도적으로 고르는 콘텐츠이고, 호스트가 폼으로 바꿀 수 있는 이름 붙은 인자를 갖추고 있죠. 도메인을 소유한 서버(코드 리뷰 정책, 장애 대응 런북, 릴리스 공지)가 문구도 소유하고, MCP를 말하는 모든 클라이언트는 이용 가능한 목록을 뽑아 사용자에게 보여주고, 인자를 수집하고, 같은 템플릿을 같은 방식으로 렌더링할 수 있습니다. 입력은 보통 메뉴나 슬래시 명령어로 일어나지만, 프로토콜은 특정 인터페이스를 강제하지 않습니다. 프로토콜이 고정하는 것은 계약입니다. 프롬프트가 언제 실행될지는 사용자가 정하고, 그 콘텐츠는 클라이언트가 미리 끼워 넣는 것이 아니라 서버가 서빙하는 데이터라는 것 말입니다.

첫 번째 곁에는 더 작은 두 번째 문제가 붙어 있습니다. 템플릿에 인자가 둘 이상이라면 손으로 채우는 일은 느리고 실수하기 쉽습니다. `completion/complete`는 사용자가 타이핑하는 동안 서버가 값을 제안하게 하고, 나중 제안이 앞선 답변을 참고하게 함으로써 그 문제를 풀어줍니다.

## 핵심 개념

제어 모델부터 봅니다. 이 프리미티브에 관한 나머지 전부를 결정하기 때문입니다. 도구는 모델 제어입니다. 모델이 언제 호출할지 정합니다. 리소스는 애플리케이션 주도입니다. 호스트가 어떤 리소스 콘텐츠가 컨텍스트에 들어올지 정합니다. 프롬프트는 사용자 제어입니다. 사용자가 명시적으로 하나를 고르며, 보통은 호스트가 슬래시 명령어로 렌더링하는 메뉴를 통해서죠. 프롬프트의 문구, 인자, 렌더링되는 메시지를 쓰는 것은 여전히 서버입니다. 제어란 언제 실행될지를 누가 정하느냐이지, 무엇이라고 쓰이느냐를 누가 정하느냐가 아닙니다.

이 프리미티브를 지원하는 서버는 자신의 `server/discover` 결과의 `capabilities` 객체에 `prompts: {"listChanged": true}`를 선언하고, 이후 `prompts/list`에 답해야 합니다. 그 결과는 `resultType: "complete"`와 `prompts` 배열을 실고, `prompts/list`가 여섯 캐시 가능 연산 중 하나이므로 정수 `ttlMs`와 `"public"` 또는 `"private"`인 `cacheScope`도 실습니다. 목록 조회는 페이지네이션을 지원합니다. 요청의 불투명한 `cursor`와, 페이지가 더 남아 있을 때 결과의 불투명한 `nextCursor`입니다. 서버가 발행한 적 없는 커서는 부드러운 실패가 아니라 `-32602` Invalid params입니다. 잘못되었거나 빠진 프롬프트 이름을 다루는 것과 같은 코드죠.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "prompts/list",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}
```

`prompts`의 각 항목은 프롬프트 이름을 밝히고 그 `arguments`를 나열하며, 각 인자는 `name`, `description`, `required` 플래그를 갖습니다. 클라이언트는 사용자가 아무것도 타이핑하기 전에 그 목록에서 바로 폼을 만들 수 있습니다. 템플릿을 해석하려면 클라이언트가 `name`과 문자열들의 `arguments` 맵을 곁들인 `prompts/get`을 보냅니다. 실패 모양은 두 가지가 있고, 시험은 도구 프리미티브와의 차이를 집요하게 묻습니다. 여기에는 `isError` 채널이 없습니다. 프롬프트는 아무것도 실행하지 않고 텍스트를 렌더링할 뿐이기 때문입니다. 모르는 프롬프트 이름도, 빠진 필수 인자도 모두 평범한 JSON-RPC 오류, 즉 `-32602`이지 모델이 떠안아 수습해야 할 부분 결과가 아닙니다. 2026-07-28 개정판은 `prompts/get`이 최종 결과 대신 `InputRequiredResult`로 답하는 것도 허용합니다. 서버가 렌더링을 끝내기 전에 답변 하나를 더 필요로 하는 동안 tools/call을 상태 없이 유지하는, 그 같은 멀티 라운드 트립 모양이죠. 그 메커니즘은 이 트랙의 뒤 레슨에서 자기 몫을 다룹니다.

성공한 `prompts/get` 결과는 `messages`를 실고, 각 메시지는 `"user"`나 `"assistant"` 중 하나인 `role`과 하나의 콘텐츠 블록으로 이룹니다. `text` 블록이 흔한 경우로, 인자 값이 이미 문구에 치환되어 들어 있습니다. 메시지는 대신 `resource_link`, 즉 바이트를 인라인하지 않고 리소스를 가리키는 `uri`, `name`, `mimeType`을 실을 수도 있습니다. 리뷰가 인용은 하되 복제하면 안 되는 스타일 가이드나 런북에 유용하죠. 콘텐츠가 인라인으로 보내기에 충분히 작다면 메시지는 내장 `resource` 블록, 즉 리소스의 `uri`, `mimeType`, 그리고 `text` 또는 base64 `blob`을 메시지 안에 직접 실을 수도 있습니다. 세 콘텐츠 타입 모두 리소스가 쓰는 것과 같은 `audience`와 `priority` 어노테이션을 받아들입니다.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "resultType": "complete",
    "description": "Code review request template",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Review this python snippet for style and correctness. Follow flask community conventions where they apply."
        }
      },
      {
        "role": "user",
        "content": {
          "type": "resource_link",
          "uri": "file:///styleguides/python.md",
          "name": "python-style-guide.md",
          "mimeType": "text/markdown"
        }
      }
    ]
  }
}
```

인자 여러 개를 손으로 채우는 일은 지루하므로, `completions: {}` 캐퍼빌리티를 선언한 서버는 `completion/complete`에 답합니다. 요청은 `ref`를 통해 무엇이 완성되는 중인지 밝힙니다. 프롬프트 인자라면 `{"type": "ref/prompt", "name": "code_review"}`, 리소스 템플릿의 변수라면 `{"type": "ref/resource", "uri": "file:///src/{path}"}`입니다. 요청은 지금 타이핑 중인 `argument`, 즉 `{"name": ..., "value": ...}`를 실고, 사용자가 같은 폼에서 앞서 이미 답한 이름-값 짝의 맵인 선택적 `context.arguments`도 실 수 있습니다. 자동 완성 결과는 결코 100개를 넘는 `values`를 나열하지 않습니다. 실제 일치 개수가 더 크면 전체 `total`을 보고하고 `hasMore`를 true로 설정해서, 클라이언트가 목록이 다 떨어진 게 아니라 잘렸다는 것을 알게 합니다. `prompts/get`과 `completion/complete`은 모두 여섯 캐시 가능 연산에 속하지 않으므로 결과가 `ttlMs`나 `cacheScope`를 실지 않습니다. 흔히 빠지는 시험 함정이죠. 캐싱은 인자별 답변의 속성이 아니라 안정적인 목록의 속성입니다.

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "resultType": "complete",
    "completion": {
      "values": ["falcon", "fastapi"],
      "total": 2,
      "hasMore": false
    }
  }
}
```

두 번째 인자가 첫 번째 인자로 좁혀지는 것이야말로 `context.arguments`의 존재 이유입니다. 이것이 없으면 서버는 지금까지 타이핑된 접두사에서만 추측할 수 있어서, 사용자가 이미 어떤 언어를 골랐는지와 무관하게 글자만 맞는 후보는 모두 후보군에 들어옵니다. `context.arguments`가 `{"language": "python"}`을 실고 있으면, 프레임워크 제안을 하는 서버는 JavaScript와 Java 항목을 걷어내고 실제로 해당하는 것만 돌려줄 수 있습니다. 자동 완성 후보는 도구 어노테이션처럼 제안이지 접근 제어가 아닙니다. 클라이언트는 사용자가 궁극적으로 제출하는 무엇이든 프롬프트 자신의 규칙으로 여전히 검증해야 합니다.

2026-07-28 이전에는 `prompts/list` 같은 목록 결과에 필수 캐싱 필드가 아예 없었습니다. `ttlMs`도 `cacheScope`도 없는 `prompts/list` 결과를 받은 이중 시대(dual-era) 클라이언트는 기본 신선도 윈도우를 가정하는 대신, 그것을 캐시하지 않는 일회용 답변으로 다뤄야 합니다.

```figure
mcpa-13-prompt-template
```

## 인터랙티브 랩

그림의 왼쪽 열은 `prompts/get` 호출 하나를 처음부터 끝까지 따라갑니다. 템플릿의 `{language}`와 `{framework}` 자리표시자, 그 호출에 공급된 인자, 그리고 돌아오는 렌더링된 텍스트입니다. 오른쪽 열은 `framework` 인자에 대해 같은 타이핑된 접두사로 `completion/complete`을 두 번 실행합니다. 한 번은 `context.arguments` 없이, 또 한 번은 클라이언트가 사용자가 이미 골랐던 언어를 서버에게 알려준 뒤에요. 두 호출 사이에서 후보 목록이 줄어드는 것은 서버가 이제 그 언어에 속하지 않는 프레임워크를 배제할 수 있기 때문입니다. 어느 열에도 캐시 힌트가 보이지 않습니다. `prompts/get`도 `completion/complete`도 그것을 실지 않기 때문입니다.

## 실습 랩

`code/main.py`를 열어 보세요. 표준 라이브러리만으로 만든 프롬프트 서버로, `code_review`와 `bug_triage` 두 프롬프트를 페이지당 하나씩 나열해서 `prompts/list`가 커서와 `nextCursor`를 곁들인 진짜 페이지네이션을 시연합니다. 144개 소스 파일 경로의 가상 카탈로그가 `ref/resource` 자동 완성을 뒷받침해서, 100개 값 상한과 `hasMore`가 모조가 아니라 실제로 한도를 넘는 개수에서 나옵니다.

```bash
python3 code/main.py
```

출력된 교환들을 개념 섹션과 대조하며 읽어 보세요. 두 `prompts/list` 호출을 찾고, 두 번째 호출이 첫 번째의 `nextCursor`를 사용해 나머지 프롬프트를 자체 `nextCursor` 없이 돌려주는 모습, 즉 목록이 소진되었다는 표시를 확인하세요. 세 번째 `prompts/list` 호출도 찾아보세요. 서버가 발행한 적 없는 커서를 보냈다가 `-32602`를 받습니다. `code_review`의 `prompts/get` 호출도 찾아보세요. 그 결과에는 메시지가 두 개 있습니다. `python`과 `flask`가 이미 치환된 `text` 블록과, 리뷰가 인용해야 할 스타일 가이드를 가리키는 `resource_link`죠. 그다음 두 실패 호출을 찾으세요. 인자가 아예 없는 `prompts/get`과 존재하지 않는 프롬프트 이름을 부르는 호출, 둘 다 `-32602`입니다. 마지막으로 두 `framework` 자동 완성을 비교하세요. `context` 없는 첫 번째는 JavaScript에 속한 것 하나를 포함해 일치 세 개를 돌려주고, `context.arguments`가 `{"language": "python"}`으로 설정된 두 번째는 Python에 속한 둘만 돌려줍니다. 마지막 두 호출은 `ref/resource` 경로 인자를 완성합니다. 처음엔 빈 접두사로(가능한 144개 경로 중 100개, `hasMore` true), 그다음엔 `auth/` 접두사로(18개 중 18개, `hasMore` false)요. 접두사를 바꾸거나 세 번째 프롬프트를 추가하고 다시 실행하면 페이지네이션과 자동 완성이 어떻게 반응하는지 볼 수 있습니다.

## 제공되는 산출물

`outputs/prompt-and-completion-reference.md`는 프롬프트와 자동 완성 표면을 위한 한 페이지 참고 자료입니다. 요청과 결과 모양, `PromptMessage`가 실을 수 있는 콘텐츠 타입, 오류 표, 그리고 상한을 곁들인 자동 완성 참조 타입들이 담겨 있습니다. 검토 중인 서버의 옆에 두고, 그 서버의 `prompts/get` 오류와 `completion/complete`의 상한 및 `hasMore` 동작을 한눈에 확인하세요.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검사합니다. `prompts/list`가 페이지네이션하며 캐시 힌트를 실는지, 알 수 없는 커서가 거부되는지, `prompts/get`이 인자를 텍스트 블록에 치환하고 리소스 링크를 붙이는지, 빠진 필수 인자와 모르는 프롬프트 이름이 둘 다 `-32602`로 돌아오는지, 자동 완성 결과가 100개 값에서 상한이 걸리고 더 있을 때 `hasMore`를 설정하는지, 더 좁은 접두사는 다시 상한 아래로 내려오는지, `context.arguments`가 후보 집합을 실측 가능하게 줄이는지, 그리고 시나리오의 모든 요청이 프로토콜 메타데이터를 실고 있는지입니다. 저장소의 와이어 검사기도 이 레슨의 트랜스크립트를 2026-07-28 규칙에 대해 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/13-prompts-and-completion
```

## 캡스톤 연계

캡스톤의 엔드투엔드 교환은 서버를 발견하고, 도구를 호출하고, 동의 절차를 밟지만, 현실적인 호스트는 자유 텍스트를 타이핑하는 대신 검토를 거친 템플릿을 손이 닿는 곳에 두고, 채워 넣는 동안 자동 완성도 제공합니다. 캡스톤이 어떤 상호작용이 도구 대신 프롬프트를 쓴 이유를 정당화하라고 하면, 제어 관점에서 답하세요. 사용자가 의도적으로 골랐고, 서버가 문구를 작성했으며, 렌더링은 도구 호출처럼 상태를 바꾸는 일이 전혀 없다는 것으로요.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 프롬프트(Prompt) | 사용자 제어이며 서버가 작성한, 이름 붙은 인자를 가진 메시지 템플릿 |
| `prompts/list` | 현재 호출자에게 보이는 프롬프트를 돌려주는, 캐시 가능하고 페이지네이션되는 요청 |
| `prompts/get` | 하나의 프롬프트 메시지를 인자 치환과 함께 렌더링하는 요청 |
| `PromptMessage` | `role`과 하나의 콘텐츠 블록. text, image, audio, 리소스 링크 또는 내장 리소스 |
| `resource_link` | 바이트를 인라인하지 않고 URI로 리소스를 가리키는 콘텐츠 블록 |
| `completion/complete` | 하나의 프롬프트 또는 리소스 템플릿 인자에 대한 순위 매겨진 제안을 돌려주는 요청 |
| `ref/prompt` | 완성 중인 인자가 속한 프롬프트를 밝히는 자동 완성 참조 |
| `ref/resource` | 완성 중인 리소스 URI 또는 템플릿을 밝히는 자동 완성 참조 |
| `context.arguments` | 이후 완성을 좁히려고 클라이언트가 보내는, 이미 해석된 인자 값들 |
| `hasMore` | `total`이 100개 값 상한을 넘을 때마다 true가 되는 자동 완성 플래그 |

## 더 읽을거리

- [MCP 명세 2026-07-28: Prompts](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
- [MCP 명세 2026-07-28: Completion](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/completion)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 10절
- `phases/13-tools-and-protocols/10-mcp-resources-and-prompts`, 리소스와 프롬프트 프리미티브를 깊게 다루는 단계
