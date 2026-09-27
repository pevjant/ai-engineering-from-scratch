> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 명시적 범위와 상태 없는 일론(Elicitation)

> 루츠(Roots)는 MCP 2026-07-28에서 폐기되었으며, 애초에 보안 샌드박스도 아니었습니다. 범위는 눈에 보이는 도구 인자나 리소스 URI에 넣고 서버에서 권한 검사를 하며, 도구가 정말 사용자 입력을 필요로 할 때는 MRTR을 사용하세요. 사용자는 결정을 보고, 모델은 핸들(handle)을 보고, 어떤 서버 인스턴스든 재시도를 처리할 수 있습니다.

**유형:** Build(만들기)
**언어:** Python
**선수 지식:** 페이즈 13 · 07(MCP 서버), 페이즈 13 · 11(상태 없는 MRTR)
**시간:** 약 60분

## 학습 목표

- 폐기된 루츠를 명시적 워크스페이스 파라미터, 리소스 URI, 서버 설정으로 대체합니다.
- 범위 힌트를 권한 부여, 경로 포함(containment) 검사, 운영체제 샌드박스와 분리합니다.
- 폼 모드 `elicitation/create`를 MRTR `input_required` 결과로 전달합니다.
- 요청별 클라이언트 역량에 일론(elicitation) 지원을 광고하고, 지원하지 않는 모드는 거부합니다.
- `accept`, `decline`, `cancel`을 서로 다른 결과로 검증합니다.
- 파괴적(되돌릴 수 없는) 확인을 인증된 주체, 원래 인자, 후보 집합, 만료에 묶습니다.

## 비슷해 보이는 두 문제

메모 도구가 이 요청을 받았습니다: "옛 TPS 보고서를 삭제해 줘."

서버는 서로 다른 두 질문에 답해야 합니다.

1. 이 연산이 어떤 워크스페이스를 건드릴 수 있는가?
2. 세 개의 일치하는 메모 중 사용자가 말한 것은 어느 것인가?

첫째는 범위와 권한 부여입니다. 둘째는 인터랙티브한 모호성 해소입니다. 이 둘을 섞으면 위험한 설계가 태어납니다. 예컨대 "클라이언트가 준 폴더"를 "그 안의 모든 것을 지울 수 있다는 증거"로 취급하는 식입니다.

## 루츠는 마이그레이션 표면일 뿐이다

이전 MCP 리비전에서는 클라이언트가 루츠를 광고하고 목록이 바뀌면 서버에 알릴 수 있었습니다. 루츠는 참고용 힌트였습니다. 서버 프로세스가 무엇을 읽을 수 있는지 제한하지 않았고, 호출자를 인증하지 않았으며, 운영체제 샌드박스도 만들지 않았습니다.

MCP 2026-07-28은 새 설계에서 `roots/list`와 `notifications/roots/list_changed`를 폐기합니다. 다음 명시적 대체 중 하나를 선호하세요:

- 호출마다 범위가 달라진다면 `workspaceUri` 또는 `directory` 도구 인자.
- 연산이 이미 리소스를 대상으로 한다면 리소스 URI.
- 하나의 배포가 하나의 고정 워크스페이스를 소유한다면 서버 설정.
- 코드가 기술적으로 탈출할 수 없어야 한다면 프로세스 샌드박스 또는 감옥화(jailed)된 파일시스템.

기존 2026-07-28 통합이 유예 기간 동안 여전히 `roots/list`를 필요로 한다면, 서버는 이를 MRTR `inputRequests` 안에 심습니다. 살아있는 역방향 요청을 보내서는 안 됩니다. 이것은 마이그레이션 어댑터일 뿐이며, 새 핸들러는 명시적 범위를 받아들여야 합니다.

모델은 명시적 핸들을 보고 반복할 수 있습니다. 숨겨진 전송 세션 범위는 검사, 재생, 감사, 라우팅이 모두 더 어렵습니다.

### 3계층 규칙

명시적인 URI라고 스스로 권한을 얻지는 못합니다. 세 계층을 모두 강제하세요:

1. **권한 부여:** 이 인증된 주체가 이 워크스페이스를 쓸 수 있는가?
2. **포함(containment):** 정규화된 대상 URI가 승인된 워크스페이스 경계 안에 머무는가?
3. **샌드박스:** 침해된 서버가 탈출하려 할 때 운영체제가 막을 수 있는가?

실행 가능한 서버는 승인된 워크스페이스 URI의 허용 목록을 유지하고, 퍼센트 인코딩된 경로를 정규화하고, 실제 경로 구성 요소(path component) 경계를 검사하며, 삭제 직전에 포함 검사를 다시 수행합니다.

순진한 문자열 접두사 검사는 틀립니다:

```text
allowed:   file:///work/notes
attacker:  file:///work/notes-evil/secret.md
traversal: file:///work/notes/%2e%2e/private.md
```

두 악의적인 경로 모두 오해를 부르는 문자열로 시작합니다. 먼저 정규화한 뒤 경로 구성 요소를 비교하세요. 프로덕션(운영 환경) 파일시스템 서버는 심볼릭 링크 경쟁(race)과 플랫폼별 경로 의미론도 방어해야 합니다.

## 일론은 여전히 존재하지만, 전달 방식이 바뀌었다

일론(elicitation)은 `tools/call`, `prompts/get`, `resources/read` 도중 사용자 입력을 모으는 현재의 클라이언트 기능입니다. 메서드 이름은 여전히 `elicitation/create`입니다. 바뀐 것은 와이어 흐름의 방향입니다.

2026-07-28 서버는 역방향 JSON-RPC 요청을 보내지 않습니다. 대신 `InputRequiredResult`를 돌려줍니다:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "input_required",
    "inputRequests": {
      "delete_choice": {
        "method": "elicitation/create",
        "params": {
          "mode": "form",
          "message": "Choose one matching note and confirm deletion.",
          "requestedSchema": {
            "type": "object",
            "properties": {
              "note_id": {
                "type": "string",
                "enum": ["note-3", "note-7", "note-14"]
              },
              "confirm": {"type": "boolean"}
            },
            "required": ["note_id", "confirm"]
          }
        }
      }
    },
    "requestState": "integrity-protected-delete-state"
  }
}
```

호스트가 폼을 렌더링합니다. 사용자는 수락하거나, 명시적으로 거부하거나, 창을 닫을 수 있습니다. 그런 다음 클라이언트는 새 id로 원래 `tools/call`을 재시도합니다:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "notes_delete",
    "arguments": {
      "workspaceUri": "file:///Users/alice/Documents/Notes",
      "title": "TPS report"
    },
    "inputResponses": {
      "delete_choice": {
        "action": "accept",
        "content": {"note_id": "note-14", "confirm": true}
      }
    },
    "requestState": "integrity-protected-delete-state",
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "elicitation": {"form": {}}
      }
    }
  }
}
```

두 호출 사이에 프로토콜 세션은 없습니다. 서버는 되돌려 받은 상태를 검증하고, 응답이 기대 스키마에 맞는지 확인하고, 선택된 메모가 서명된 후보 집합에 있었는지 확인하고, 워크스페이스 권한을 다시 검사하고, 포함 검사를 다시 하고, 그러고 나서 삭제합니다.

## 역량 협상은 요청별이다

폼 모드 일론을 지원하는 클라이언트는 다음을 선언합니다:

```json
{
  "io.modelcontextprotocol/clientCapabilities": {
    "elicitation": {"form": {}}
  }
}
```

빈 일론 역량인 `"elicitation": {}`은 호환성을 위해 폼 전용 지원과 동등하게 취급됩니다. 명시적인 `"elicitation": {"form": {}}`도 폼 모드를 지원합니다. URL 전용 선언인 `"elicitation": {"url": {}}`은 그렇지 않습니다. 서버는 현재 요청의 역량에 없는 모드를 절대 포함하지 말아야 합니다. 이전 요청이 그것을 광고했더라도 마찬가지입니다.

모든 요청은 `io.modelcontextprotocol/protocolVersion`도 실어 나릅니다. 버전이 없거나 문자열이 아니면 `-32602`를 돌려줍니다. 지원하지 않는 문자열이라면 정확한 `supported`·`requested` 데이터와 함께 `-32022`를 돌려줍니다. 일론 지원이 없거나 URL 전용이라면 `data.requiredCapabilities`를 `{"elicitation":{"form":{}}}`로 설정해 `-32021`을 돌려줍니다.

JSON-RPC `id`가 없는 봉투는 알림입니다. JSON-RPC 성공이나 오류 응답을 내보내지 않고 처리하세요. Streamable HTTP에서 수락된 알림은 본문 없는 `202 Accepted`를 받습니다.

`clientInfo`는 진단을 위해 포함하는 것이 좋지만, 스스로 보고한 값이므로 권한 부여를 위한 사용자 식별로 쓸 수 없습니다.

서버는 `server/discover`를 구현하고 `resultType: "complete"`와 함께 `supportedVersions`, 역량, `ttlMs`, `cacheScope`를 돌려줍니다. 이 현대적 설계에서는 루츠를 광고하지 않습니다. 도구를 광고하므로 필수인 `tools/list`도 구현합니다. 그 결과는 결정론적인 `notes_delete` 디스크립터, 유효한 객체형 `inputSchema`, 서버 식별 메타데이터, 공개 캐시 힌트를 돌려줍니다.

## 폼 모드

폼 모드는 쓰기 쉬운 대화상자를 위해 설계된 제한적인 JSON Schema를 사용합니다. 루트는 객체이고 그 속성은 평평한(flat) 원시 타입 필드 또는 지원되는 enum 배열입니다. 깊게 중첩된 객체나 범용 문서 스키마는 확인 대화상자에 어울리지 않습니다.

폼 모드를 쓰는 경우:

- 여러 후보 중 하나를 고를 때;
- 파괴적 연산을 확인할 때;
- 민감하지 않은 선호도를 수집할 때;
- 모델이 아니라 사용자가 결정해야 하는 소수의 값을 모을 때.

폼 모드로 비밀번호, API 키, 접근 토큰, 결제 자격 증명을 받으면 안 됩니다. 그런 비밀값은 MCP 클라이언트를 통과해 로그나 모델 컨텍스트까지 흘러갈 수 있습니다.

서버는 반환된 콘텐츠를 다시 검증합니다. 클라이언트 쪽 폼 검증은 UX를 개선할 뿐 신뢰를 만들지는 못합니다.

## URL 모드

URL 모드는 대역 외(out-of-band) 상호작용을 위한 보안 웹 URL을 보냅니다:

```json
{
  "method": "elicitation/create",
  "params": {
    "mode": "url",
    "message": "Connect the report service to continue.",
    "url": "https://mcp.example.com/connect/report-service"
  }
}
```

민감한 정보가 서버가 제어하는 웹 흐름으로 직접 가야 할 때, 예컨대 서드파티 인증에 사용하세요. 클라이언트는 전체 목적지를 보여 주고 열기 전에 동의를 받습니다. URL을 미리 내려받아서(prefetch)는 안 됩니다.

`accept` 응답은 사용자가 URL을 여는 데 동의했다는 뜻입니다. 외부 흐름이 완료되었음을 증명하지는 않습니다. 재시도 때 서버는 자신의 상태를 확인해 완료하거나 또 다른 `input_required` 결과를 돌려줍니다.

URL 일론은 MCP 클라이언트와 MCP 서버 사이의 권한 부여를 대체하지 않습니다. 이것은 MCP 서버가 사용자를 대신해 수행해야 하는 외부 상호작용을 위한 것입니다. 서버는 브라우저 사용자를 MCP 연산을 시작한 것과 동일한 인증된 주체에 묶어야 합니다.

## 응답 분기

동작들을 별명(alias)이 아니라 제품 결정으로 다루세요:

| 동작 | 의미 | 안전한 서버 동작 |
|--------|---------|----------------------|
| `accept` | 사용자가 상호작용을 제출함 | 콘텐츠를 검증하고 계속 진행 |
| `decline` | 사용자가 명시적으로 거부함 | 오류가 아닌, 완결된 거부 결과를 반환 |
| `cancel` | 사용자가 닫았거나 끝내지 못함 | 안전하게 중단하고 나중에 재시도 허용 |

콘텐츠가 없는 것을 동의로 해석하지 마세요. decline을 반복 프롬프트 루프로 바꾸지도 마세요.

## 파괴적 MRTR 상태 보호

후보 목록이 프롬프트나 서명되지 않은 Base64 값에만 살아 있어서는 안 됩니다. 클라이언트는 돌려보내는 모든 것을 통제합니다.

이 레슨은 다음을 담은 상태 페이로드에 서명합니다:

- 인증된 주체;
- 최초 메서드;
- `workspaceUri`와 `title`의 다이제스트;
- 폼에 보여 준 허용된 메모 id들;
- 연산 페이즈;
- 짧은 만료 시간.

변경(mutation) 전에 서버는 살아있는 메모 레코드도 확인합니다. 이것은 삭제 경쟁(race)과, 폼을 보여 준 뒤 대상이 워크스페이스 밖으로 옮겨진 경우를 잡아 냅니다.

1회성 금융 동작이나 되돌릴 수 없는 동작에는 HMAC만으로는 만료 안에서 유효한 상태가 재생(replay)되는 것을 막을 수 없습니다. 모든 핸들러 인스턴스가 공유하는 재생 저장소(replay store)에 논스(nonce)를 정확히 한 번만 소비하도록 저장하세요. 이 레슨은 유계이고 TTL로 정리되는 저장소를 주입하고, 메모리 내 삭제를 수행하는 동안 원자적 클레임(claim)을 유지합니다. 프로덕션 데이터베이스는 논스 클레임과 변경을 하나의 트랜잭션 또는 동등한 조건부 쓰기 경계로 묶어야 합니다.

논스를 클레임하기 전에 상호작용을 검증하세요. 형식이 잘못된 응답이나 `cancel`은 아무 변경도 하지 않으며 상태는 만료될 때까지 재시도 가능하게 남습니다. 명시적인 `decline`은 종결(terminal)이므로, 이 레슨은 아무것도 삭제하지 않으면서 논스를 소비합니다.

```figure
t3-roots-boundary
```

## 만들기

`code/main.py`는 현대적인 `notes_delete` 도구를 시연합니다:

- `tools/list`는 필요한 워크스페이스·제목 스키마를 갖춘 결정론적·캐시 가능한 디스크립터를 돌려줍니다.
- 범위는 명시적인 `workspaceUri` 인자입니다.
- 서버 설정이 레슨 주체에 대해 그 워크스페이스를 승인합니다.
- URI 정규화가 접두사 혼동과 인코딩된 경로 순회(traversal)를 거부합니다.
- 모든 파괴적 삭제에는 폼 모드 일론이 필요합니다.
- 일론은 `resultType: "input_required"` 안을 이동합니다.
- 서명된 `requestState`가 정확한 후보 목록과 원래 인자에 묶입니다.
- 주입된 재생 저장소가 같은 수락 또는 거절 상태를 서버 인스턴스들 사이에서 거부합니다.
- 재시도는 새 요청 id를 쓰고 `resultType: "complete"`를 돌려줍니다.

데이터 저장소는 메모리에 있어 프로토콜 동작을 쉽게 들여다볼 수 있습니다. 데이터베이스를 쓰더라도 보안 규칙은 동일합니다.

## 사용하기

저장소 루트에서:

```bash
cd phases/13-tools-and-protocols/12-mcp-roots-and-elicitation/code
python3 main.py
python3 -m unittest discover tests -v
```

기대 체크포인트:

- 디스커버리가 루츠 없이 도구를 광고합니다.
- 도구 디스커버리가 `resultType`, 서버 식별, 캐시 힌트와 함께 `notes_delete`를 돌려줍니다.
- 요청 id `1`이 `inputRequests.delete_choice` 안의 폼을 돌려줍니다.
- 요청 id `2`가 서명된 상태를 되돌려 보내고 삭제를 완료합니다.
- 접두사 경로와 인코딩된 순회 경로 모두 포함 검사에 실패합니다.
- 바뀐 제목은 원래 확인 상태를 재사용할 수 없습니다.
- decline은 메모를 변경하지 않고 둡니다.
- 메모와 재생 상태를 공유하는 두 서버 객체가 하나의 확인을 동시에 실행할 수 없습니다.
- 빈 선언과 명시적 폼 선언은 동작하고, URL 전용 지원은 정확한 `-32021` 폼 요구사항을 돌려줍니다.
- 미지원 버전 실패는 정확한 `-32022` 데이터 형태를 사용합니다.
- id 없는 알림은 JSON-RPC 응답을 만들지 않습니다.

## 출시하기

`outputs/skill-elicitation-form-designer.md`는 명시적 범위, 권한 검사, MRTR 폼, 응답 분기, 상태 바인딩을 설계합니다. 폐기된 루츠를 샌드박스처럼 다루거나 폼 모드로 비밀값을 수집하는 것을 거부합니다.

## 연습 문제

1. 메모리 재생 저장소를 SQLite로 교체하세요. 논스 클레임과 메모 삭제에 하나의 트랜잭션을 쓰고, 두 프로세스가 모두 커밋할 수 없음을 증명합니다.
2. `url` 역량 협상과 대역 외 셋업 흐름을 추가하세요. 서드파티 자격 증명이 `inputResponses`에 들어오지 않게 유지합니다.
3. 메모리 메모 맵을 임시 SQLite 데이터베이스로 교체하세요. 변경 트랜잭션 안에서 권한과 포함 검사를 다시 수행합니다.
4. 실제 파일시스템 구현을 위한 심볼릭 링크 정책을 추가하세요. URI의 어휘적(lexical) 포함 검사만으로는 심볼릭 링크 탈출을 막을 수 없는 이유를 설명합니다.
5. 현대적 MRTR 핸들러 출력을 레거시 서버 주도 일론으로 매핑하는 2025-11-25 어댑터를 설계하세요. 현재 핸들러에서 격리된 채로 유지합니다.

## 핵심 용어

| 용어 | 2026-07-28에서의 의미 |
|------|------------------------|
| 루츠(Roots) | 폐기된 참고용 워크스페이스 힌트. 권한 부여도 샌드박싱도 아님 |
| 명시적 범위(Explicit scope) | 요청 인자에 드러나는 워크스페이스·디렉터리·리소스 핸들 |
| 포함(Containment) | 대상을 경계 안에 가두는 정규화된 경로 구성 요소 검사 |
| 일론(Elicitation) | MCP 연산 도중 사용자 입력을 얻는 클라이언트 기능 |
| 폼 모드(Form mode) | 제한된 평평한(flat) 스키마를 쓰는 대역 내(in-band) 구조화 사용자 입력 |
| URL 모드(URL mode) | 민감하거나 외부인 워크플로를 위한 대역 외 상호작용 |
| MRTR | 상태 없는 input-required 결과와 그에 따른 새로운 재시도 |
| `requestState` | 그대로 되돌려 보내지고 서버가 무결성을 검사하는 불투명 상태 |
| 거부(Decline) | 사용자의 명시적 거절 |
| 취소(Cancel) | 승인 없이 닫히거나 끝마치지 못한 상호작용 |

## 레거시 호환성

2025-11-25에 고정된 피어에는 `roots/list`, `notifications/roots/list_changed`, 살아있는 서버 주도 `elicitation/create`가 여전히 존재할 수 있습니다. 그 어댑터에는 레거시라는 라벨을 붙이세요. 레거시 루츠 목록이 서버 권한 검사를 우회하게 하지 말고, 프로토콜 세션 가정을 현대 핸들러에 끌어들이지 마세요.

## 더 읽을거리

- [MCP 2026-07-28 Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation)
- [MCP 2026-07-28 Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [MCP 2026-07-28 Roots deprecation](https://modelcontextprotocol.io/specification/2026-07-28/client/roots)
- [MCP 2026-07-28 server discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
