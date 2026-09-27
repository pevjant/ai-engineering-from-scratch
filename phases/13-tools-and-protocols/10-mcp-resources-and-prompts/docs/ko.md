> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# MCP 리소스와 프롬프트: 상태 없는 서버를 위한 주소 지정 가능한 컨텍스트

> 도구는 연산을 수행합니다. 리소스는 주소로 접근할 수 있는 콘텐츠를 드러냅니다. 프롬프트는 사용자가 직접 고른 메시지 템플릿을 묶음으로 제공합니다. 좋은 MCP 서버는 이 세 가지 계약을 서로 분리된 채로 예측 가능하게 유지합니다.

**유형:** Build(만들기)
**언어:** Python
**선수 지식:** 페이즈 13, 레슨 07(MCP 서버 만들기), 페이즈 13, 레슨 09(MCP 트랜스포트)
**시간:** 약 60분

## 학습 목표

- 소비자(호출하는 쪽)의 의도를 보고 도구, 리소스, 프롬프트 중에서 골라낼 수 있습니다.
- 필수 메서드인 `server/discover`를 통해 리소스·프롬프트 표면(제공 범위)을 알립니다.
- 결정론적인 `resources/list`와 `prompts/list` 결과를 만듭니다.
- 사용자별 데이터가 새어 나가지 않게 `ttlMs`와 `cacheScope`를 적용합니다.
- 잘못됐거나 알 수 없는 리소스 URI에 대해 JSON-RPC 오류 `-32602`를 돌려줍니다.
- `subscriptions/listen`의 POST 응답 스트림을 열고, 모든 이벤트를 구독 ID로 짝지어 추적합니다.
- 리소스 콘텐츠와 프롬프트 템플릿을 신뢰할 수 없는 서버 출력으로 다룹니다.

## 소비자에서 출발하기

MCP를 잘못 쓰기 가장 쉬운 길은 구현 코드부터 작성하는 것입니다. 데이터베이스 질의는 "함수가 익숙하니까" 도구가 되고, 재사용 가능한 워크플로는 "파일에 저장되어 있으니까" 리소스가 되고, 프롬프트는 "호스트가 몰래 집어넣을 수 있으니까" 숨겨진 정책이 되어버립니다.

누가 선택하고 무엇을 기대하는지에서 시작하세요.

| 프리미티브 | 주된 의도 | 선택 주체 | 전형적 결과 |
|---|---|---|---|
| 도구 | 연산 수행 | 모델 또는 애플리케이션 | 구조화된 실행 결과 |
| 리소스 | URI로 콘텐츠 읽기 | 호스트, 애플리케이션 또는 사용자 | 텍스트 또는 바이너리 콘텐츠 |
| 프롬프트 | 재사용 가능한 메시지 워크플로 시작 | 호스트 UI를 통한 사용자 | 하나 이상의 프롬프트 메시지 |

`notes://note-1`에 있는 메모는 "주소로 접근 가능한 콘텐츠"이므로 리소스입니다. `delete_note`는 상태를 바꾸므로 도구입니다. `review_note`는 사용자가 준비된 검토 워크플로를 선택하는 것이므로 프롬프트입니다.

"그럴듯해 보이려고" 하나의 연산을 세 가지로 모두 노출하지 마세요. 표면이 하나 늘어날 때마다 디스커버리, 권한 부여, 캐싱, 오류 처리, 테스트, 문서화가 각각 추가로 필요합니다.

## 2026-07-28 상태 없는 봉투(envelope)

이 레슨은 MCP 프로토콜 리비전 `2026-07-28`을 대상으로 합니다. 이 프로파일에는 초기화 핸드셰이크도 프로토콜 세션도 없습니다. 모든 요청이 예약된 `_meta` 키를 통해 프로토콜 버전과 클라이언트 역량(capabilities)을 직접 실어 나릅니다.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientInfo": {
        "name": "course-client",
        "version": "1.0.0"
      },
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}
```

서버는 `server/discover`를 반드시 구현해야 합니다. 그 결과에는 지원 버전, 리소스·프롬프트 역량, 구현체 식별 정보, 캐시 힌트가 담깁니다. 클라이언트는 다른 메서드를 곧바로 호출해도 되지만, 디스커버리를 먼저 하면 UI를 만들기 전에 안정적인 스냅샷 한 장을 확보할 수 있습니다.

```json
{
  "resultType": "complete",
  "supportedVersions": ["2026-07-28"],
  "capabilities": {
    "resources": {"listChanged": true, "subscribe": true},
    "prompts": {"listChanged": true}
  },
  "ttlMs": 3600000,
  "cacheScope": "public"
}
```

정상 결과는 `"resultType": "complete"`를 선언합니다. 응답의 `_meta`는 `io.modelcontextprotocol/serverInfo`로 응답한 구현체를 알려 줍니다. 이 정보는 진단에 유용할 뿐, 인증 신원이 아닙니다. 지원하지 않는 리비전이 담긴 요청에는 요청된 리비전과 서버가 지원하는 리비전을 함께 담아 `-32022`를 돌려줍니다.

상태 없는 계약은 설계 직관을 바꿉니다. 하나의 연결에서 이전 호출에 의존하는 목록은 만들 수 없습니다. 자격 증명(credential)이 요청 입력이기 때문에 권한에 따라 보이는 목록이 달라지는 것은 괜찮지만, 연결 이력에 따라 달라지는 것은 안 됩니다.

## 리소스는 안정적인 URI 계약이다

리소스는 URI로 식별되는 콘텐츠입니다. 핸들러보다 URI를 먼저 설계하세요.

좋은 URI의 조건:

- 즐겨찾기에 추가하거나 요청 사이에서 전달하기에 충분히 안정적일 것.
- 서버의 도메인으로 이름공간(namespace)이 나뉘어 있을 것.
- 프로세스 ID나 연결에 의존하지 않을 것.
- 저장소에 접근하기 전에 검증될 것.
- 읽을 때마다 권한 검사를 할 것.

`notes://note-1`은 이름공간이 명시적이기 때문에 그냥 `note-1`보다 낫습니다. 파일 서버는 `file://` URI를 쓸 수 있지만, 심볼릭 링크와 상대 경로 구간을 해석한 뒤에도 설정된 디렉터리 경계를 반드시 검사해야 합니다.

`resources/list`는 호출자가 지금 볼 수 있는 리소스들을 돌려줍니다. URI처럼 안정적인 키로 정렬하세요. 결정론적인 순서는 시끄러운 캐시 미스, 이리저리 바뀌는 스냅샷, 새로고침할 때마다 UI가 점프하는 현상을 막아 줍니다.

```json
{
  "resultType": "complete",
  "resources": [
    {
      "uri": "notes://note-1",
      "name": "Architecture decision",
      "description": "Why the service uses a stateless boundary",
      "mimeType": "text/markdown"
    }
  ],
  "ttlMs": 300000,
  "cacheScope": "public",
  "_meta": {
    "io.modelcontextprotocol/serverInfo": {
      "name": "notes-server",
      "version": "2.0.0"
    }
  }
}
```

`resources/read`는 콘텐츠 아이템을 하나 이상 돌려줍니다. 알 수 없는 URI는 "성공한 빈 읽기"가 아닙니다. 현재 리소스 명세는 잘못되었거나 알 수 없는 리소스 URI를 JSON-RPC의 "잘못된 파라미터", 즉 코드 `-32602`로 분류합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32602,
    "message": "Unknown or invalid resource URI",
    "data": {
      "uri": "notes://missing"
    }
  }
}
```

이 구분 덕분에 클라이언트는 "문서가 비어 있는 정상 상태"와 "대상이 없음"을 구별할 수 있습니다. 또한 대상을 못 찾으면 윗단계로 폭넓게 다시 검색하는 우발적인 폴백(fallback)도 막아 줍니다.

### 리소스 템플릿

리소스 템플릿은 파라미터가 붙은 URI 가족(패턴)을 설명합니다. 실제 항목을 전부 나열하는 비용이 크거나 개수가 무한대에 가까울 때 사용하세요. 예컨대 `notes://projects/{project}/decisions/{decision}`은 모든 결정 항목을 돌려주지 않으면서도 클라이언트에게 유효한 주소를 어떻게 만드는지 알려 줍니다.

템플릿을 쓴다고 검증이 약해지는 것은 아닙니다. 변수를 파싱하고, 권한 검사를 적용하고, 길이와 문자 제한을 강제하고, 타입이 있는 파라미터로 저장소 질의를 구성하세요. 임의의 URI 뒷부분을 파일시스템 경로나 데이터베이스 문장에 이어 붙이는 일은 절대 없어야 합니다.

### 콘텐츠는 신뢰할 수 있는 지시가 아니다

리소스 텍스트에는 프롬프트 인젝션, 비밀값, 그릇된 명령, 깨진 마크업이 들어 있을 수 있습니다. 호스트는 출처(provenance)를 보존하고 리소스 콘텐츠를 "데이터"로 취급해야 합니다. 서버는 콘텐츠 크기를 제한하고, 정확한 MIME 타입을 돌려주고, 호출자가 접근할 수 없는 필드는 가리고, 관련 없는 레코드가 함께 반환되지 않도록 해야 합니다.

## 프롬프트는 사용자가 제어하는 템플릿이다

MCP 프롬프트는 사용자가 명시적으로 선택하도록 설계되었습니다. 호스트는 이를 슬래시 명령, 메뉴 항목, 워크플로 버튼 등으로 보여 줄 수 있습니다. 프로토콜은 특정 UI를 강제하지 않습니다.

`prompts/list`는 같은 요청 권한에 대해 결정론적이어야 합니다. 각 프롬프트에는 안정적인 이름, 유용한 설명, 그리고 `prompts/get` 전에 호스트가 입력을 모을 수 있게 해 주는 인자 선언이 필요합니다.

```json
{
  "resultType": "complete",
  "prompts": [
    {
      "name": "review_note",
      "title": "Review a note",
      "description": "Review one note for a named concern",
      "arguments": [
        {
          "name": "uri",
          "description": "The note resource URI",
          "required": true
        }
      ]
    }
  ],
  "ttlMs": 600000,
  "cacheScope": "public"
}
```

`prompts/get`은 인자를 메시지로 풀어 줍니다. 이것이 호스트의 시스템 지시를 대체하는 것은 아닙니다. 반환된 메시지를 어떻게 모델 컨텍스트에 넣을지는 호스트가 결정하고, 호스트 자신의 신뢰할 수 있는 정책을 더 높은 우선순위로 유지합니다.

프롬프트 인자도 서버 경계에서 검증하세요. 프롬프트에 넘어오는 URI는 직접 리소스를 읽을 때와 동일한 권한 검사를 통과해야 합니다. 프롬프트를 리소스 접근을 우회하는 뒷문(side channel)으로 만들지 마세요.

## 캐시 힌트는 정확성의 일부다

`ttlMs`는 클라이언트에게 그 결과를 얼마나 오래 재사용해도 되는지 알려 줍니다. `cacheScope`는 캐시된 값을 누구와 공유할 수 있는지를 설명합니다.

| 범위 | 의미 | 전형적 사용처 |
|---|---|---|
| `public` | 권한이 허용한다면 사용자와 무관하게 재사용 가능 | 공개 프롬프트 카탈로그 |
| `private` | 요청한 사용자나 자격 증명 컨텍스트에 묶임 | 사용자 소유의 메모 콘텐츠 |

TTL은 데이터의 변화 속도와 오래된 데이터가 입히는 피해 크기로 고르세요. 공개 프롬프트 카탈로그라면 5분이 어울릴 수 있고, 비공개 메모 읽기는 1분을 쓸 수 있습니다.

MCP가 `cacheScope` 값으로 정의하는 것은 `public`과 `private` 두 가지뿐입니다. 비밀값이 들어 있거나 빠르게 바뀌는 결과라면 `cacheScope: "private"`와 `ttlMs: 0`을 돌려주고, 더 엄격한 no-store 규칙은 호스트 캐시 정책에서 적용하세요. `no-store` 자체는 MCP의 `cacheScope` 값이 아닙니다.

캐시 힌트는 권한 검사를 대신하지 못합니다. 캐시 키에는 가시성을 바꾸는 모든 요청 차원(테넌트, 사용자, 스코프, 로캘, 페이지네이션 커서 등)이 들어가야 합니다. 공유 캐시가 그런 차원들을 안전하게 표현할 수 없다면 TTL 0짜리 `private`에 호스트 수준 no-store 정책을 쓰세요.

## 구독은 클라이언트가 여는 응답 스트림을 쓴다

현대의 구독 패턴은 예전의 `resources/subscribe` RPC와 구식 HTTP GET 이벤트 엔드포인트를 대체합니다.

클라이언트는 `subscriptions/listen`을 평범한 JSON-RPC 요청으로 보냅니다. Streamable HTTP에서는 응답이 SSE 스트림으로 열린 채 유지되는 POST입니다. `notifications` 객체는 허용 목록(allowlist)입니다. 서버는 요청되지 않은 알림 타입을 전달해서는 안 됩니다.

```json
{
  "jsonrpc": "2.0",
  "id": 17,
  "method": "subscriptions/listen",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": {
        "name": "course-client",
        "version": "1.0.0"
      }
    },
    "notifications": {
      "resourcesListChanged": true,
      "promptsListChanged": true,
      "resourceSubscriptions": [
        "notes://note-1"
      ]
    }
  }
}
```

요청 ID가 곧 구독 ID입니다. 요청된 이벤트가 오기 전에 서버는 먼저 `notifications/subscriptions/acknowledged`를 보냅니다. 이 응답의 필터에는 서버가 실제로 수락한 부분집합만 들어 있습니다.

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/subscriptions/acknowledged",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/subscriptionId": 17
    },
    "notifications": {
      "resourcesListChanged": true,
      "resourceSubscriptions": [
        "notes://note-1"
      ]
    }
  }
}
```

그 뒤에 오는 모든 이벤트는 같은 메타데이터를 실어 나릅니다.

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/subscriptionId": 17
    },
    "uri": "notes://note-1"
  }
}
```

알림은 "리소스가 바뀌었다"고만 말합니다. 클라이언트는 `resources/read`로 다시 읽어야 하며, 이때도 현재 권한 검사를 거칩니다. 이벤트 안에 새 문서가 들어 있다고 가정하지 않습니다.

여러 구독이 하나의 stdio 채널을 공유할 수 있습니다. 구독 ID 덕분에 클라이언트는 이들을 구별해 분배할 수 있습니다. HTTP에서는 응답 스트림을 닫으면 구독이 취소됩니다. 스트림을 우아하게(gracefully) 끝내는 서버는 원래 요청과 짝지어진 마지막 `resultType: "complete"` 응답을 돌려줍니다.

구독 스트림을 프로토콜 세션처럼 쓰지 마세요. 그다음 읽기 요청은 여전히 완결된 요청이며, 건강한(정상 동작하는) 서버 인스턴스 어디에나 도달할 수 있습니다.

```figure
t3-primitive-sort
```

## 인터랙티브 실습

피규어를 이용해 프로젝트 트래커의 다섯 가지 기능 — 이슈 상세, 이슈 생성, 스프린트 리뷰 템플릿, 프로젝트 정책, 이슈 종료 — 을 분류해 보세요. 그다음 어떤 목록은 공개적으로 캐시할 수 있고, 어떤 읽기는 비공개로 남아야 하는지, 어떤 리소스는 갱신 알림을 받을 가치가 있는지 판단하세요.

모든 분류마다 "누가 선택하는가"를 밝히세요. 모델이 동작을 수행한다면 도구입니다. 호스트가 URI로 주소 지정된 콘텐츠를 읽는다면 리소스입니다. 사용자가 준비된 메시지 워크플로를 시작한다면 프롬프트입니다.

## 실습(Practice Lab)

저장소 루트에서 시뮬레이터를 실행하세요:

```bash
cd phases/13-tools-and-protocols/10-mcp-resources-and-prompts/code
python3 main.py
python3 -m unittest discover tests -v
```

트랜스크립트를 다음 순서로 확인하세요:

1. `server/discover`가 현재 리비전과 두 역량을 모두 알리는지 확인합니다.
2. 두 목록 결과가 정렬되어 있고 `resultType: "complete"`를 쓰는지 확인합니다.
3. 목록과 읽기 결과가 의도한 캐시 힌트를 갖고 있는지 확인합니다.
4. 읽기 URI를 `notes://missing`으로 바꾸고 `-32602`를 관찰합니다.
5. 구독 승인(acknowledgment)이 리소스 이벤트보다 먼저 오는지 확인합니다.
6. 이벤트와 우아한 종료 모두 구독 ID `5`를 실고 있는지 확인합니다.

이 파이썬 모델은 실제 HTTP 연결을 열지 않습니다. SDK가 요청 범위(request-scoped)의 응답 스트림에 올려야 할 메시지들을 표현할 뿐입니다. 프로덕션(운영 환경)에서는 프레이밍과 전송을 위해 공식 SDK를 사용하세요.

## 산출물

`outputs/skill-primitive-splitter.md`는 MCP 프리미티브 선택을 위한 재사용 가능한 설계 리뷰입니다. 결정론적 디스커버리, 캐시 범위, 잘못된 URI 동작, 현대적 구독 필터까지 검사합니다.

이 레슨은 또한 `assets/primitive-split.svg`를 함께 제공합니다. 프리미티브와 구독 경계를 그린 정적 버전으로, 오프라인 학습용입니다.

## 확인하기

```bash
cd phases/13-tools-and-protocols/10-mcp-resources-and-prompts/code
python3 main.py
python3 -m unittest discover tests -v
```

기대 결과: 메인 프로그램이 JSON 트랜스크립트를 출력하고, 테스트 명령이 최소 12개 이상의 테스트 통과를 보고합니다.

## 캡스톤 연계

캡스톤 서버가 동작(액션)과 함께 주소 지정 가능한 지식을 노출할 때 이 계약을 사용하세요. 결정론적인 카탈로그 스냅샷 하나, 권한 검사를 거친 리소스 읽기 하나, 프롬프트 해석 하나, 잘못된 URI 사례 하나, 구독 트랜스크립트 하나를 포함하세요.

증거물은 다음을 보여 줘야 합니다. 어떤 목록도 연결 이력에 의존하지 않는다는 것, 그리고 구독 이벤트가 절대로 하부 리소스에 대한 접근 권한을 부여하지 않는다는 것.

## 연습 문제

1. `notes://projects/{project}/notes/{id}` 리소스 템플릿을 추가하고 두 변수를 모두 검증하세요.
2. 결정론적 순서를 유지하면서 `resources/list`에 페이지네이션을 추가하세요.
3. 하나의 리소스를 `cacheScope: "private"`, `ttlMs: 0`으로 바꾸고, 호스트 수준 no-store 정책을 추가한 뒤, 두 통제를 모두 정당화하는 위협을 설명하세요.
4. 프롬프트 목록 변경 구독을 추가하고, 필터에 `promptsListChanged`가 없으면 어떤 이벤트도 오지 않음을 증명하세요.
5. 두 개의 동시 구독을 만들고 각 이벤트가 올바른 요청 ID를 실고 있음을 증명하세요.
6. 읽기 핸들러에 권한 주체(subject)를 추가하고, 캐시 항목이 주체를 넘어 재사용될 수 없음을 증명하세요.

## 핵심 용어

- **리소스(Resource):** MCP 서버가 노출하는, URI로 주소 지정된 콘텐츠.
- **프롬프트(Prompt):** MCP 서버가 노출하는, 사용자가 제어하는 메시지 템플릿.
- **결정론적 목록(Deterministic list):** 같은 요청 입력에 대해 구성원과 순서가 안정적인 디스커버리 결과.
- **`ttlMs`:** 캐시 신선도 유지 시간(밀리초).
- **`cacheScope`:** 캐시된 결과의 공유 경계.
- **`subscriptions/listen`:** 응답 스트림이 명시적으로 필터링된 알림을 전달하는 장수(long-lived) 요청.
- **구독 ID(Subscription ID):** 최초 listen 요청의 ID이며, 알림 메타데이터에 반복해서 등장.
- **잘못된 파라미터(Invalid parameters):** JSON-RPC 오류 `-32602`. 잘못되었거나 알 수 없는 리소스 URI에 사용.
- **지원되지 않는 프로토콜 버전:** JSON-RPC 오류 `-32022`. `supported`와 `requested` 리비전을 함께 포함.
- **`server/discover`:** 지원 리비전, 역량, 식별 정보, 선택적 캐시 힌트를 돌려주는 필수 서버 메서드.

## 더 읽을거리

- [MCP 2026-07-28 Resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
- [MCP 2026-07-28 Prompts](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
- [MCP 2026-07-28 Subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)
- [MCP 2026-07-28 Caching](https://modelcontextprotocol.io/specification/2026-07-28/basic/utilities/caching)
