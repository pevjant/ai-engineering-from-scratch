> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# MCP 모델 입력: 샘플링 마이그레이션과 상태 없는 MRTR

> MCP 2026-07-28은 새 설계에서 샘플링(Sampling)을 폐기(deprecated)로 표시하고 서버→클라이언트 요청 채널을 없앴습니다. 기존 워크플로가 여전히 클라이언트의 모델을 필요로 한다면, 서버는 `input_required` 결과를 돌려주고 클라이언트가 모델 출력을 갖고 원래 요청을 재시도합니다. 추론 루프는 프로토콜 계층에서 명시적이고, 유계이며, 상태 없는(stateless) 구조가 됩니다.

**유형:** Build(만들기)
**언어:** Python
**선수 지식:** 페이즈 13 · 07(MCP 서버), 페이즈 13 · 10(리소스와 프롬프트)
**시간:** 약 75분

## 학습 목표

- MCP 2026-07-28에서 샘플링이 폐기된 이유를 설명하고, 새 서버에는 모델 제공자 직접 연동 기본값을 선택할 수 있습니다.
- `sampling/createMessage`를 다중 왕복 요청(MRTR, Multi Round-Trip Requests)으로 실어 나르는 호환 워크플로를 구현합니다.
- 모든 요청의 `_meta` 객체에 프로토콜 리비전과 클라이언트 역량을 넣습니다.
- `resultType: "input_required"`를 돌려주고, 새로운 JSON-RPC id로 원래 메서드를 재시도합니다.
- `requestState`를 무결성으로 보호하고 주체(principal)·메서드·인자·만료 시각에 묶습니다.
- 역량 검사, 승인, 응답 검증, 라운드 한도로 모델 보조 루프에 제동을 겁니다.

## 프로토콜 이전의 결정

`summarize_repo` 같은 도구는 두 종류의 작업이 필요합니다:

1. 결정론적 작업: 파일 목록 보기, 허용된 파일 읽기, 경로 검증, 콘텐츠 조립.
2. 모델 작업: 대표 파일 고르기와 요약문 작성.

지금은 두 가지 올바른 아키텍처가 있습니다.

### 새 서버: 모델 제공자와 직접 연동

현재의 기본 선택입니다. 서버가 모델 선택, 자격 증명, 예산, 재시도, 관측 가능성(옵저버빌리티)을 모두 소유합니다. MCP 클라이언트에게는 평범한 `tools/call` 결과 하나만 돌려줍니다.

서버가 이미 호스티드 서비스이거나, 호스트의 모델을 쓰는 것보다 예측 가능한 모델 동작이 더 중요할 때 이쪽을 고르세요.

### 기존 샘플링 워크플로: MRTR로 마이그레이션

폐기 유예 기간 동안 샘플링은 여전히 존재합니다. 2026-07-28을 대상으로 하는 서버는 살아있는 `sampling/createMessage` 요청을 클라이언트에 보낼 수 없습니다. 대신 그 요청을 `InputRequiredResult` 안에 심습니다.

"클라이언트의 모델과 자격 증명을 쓰는 것"이 실제 제품 요구사항일 때만 이 호환 경로를 고르세요. 새 구현은 폐기된 샘플링을 채택하면 안 되므로 제거 계획을 기록해 두세요.

## 상태 없는 계약

2026년 7월 프로토콜에는 `initialize` 교환이 없고, `notifications/initialized`도 없고, `Mcp-Session-Id`도 없습니다. 모든 요청이 예전에는 핸드셰이크가 갖고 있던 정보를 직접 실어 나릅니다:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "summarize_repo",
    "arguments": {"audience": "developer"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {"sampling": {}},
      "io.modelcontextprotocol/clientInfo": {
        "name": "lesson-client",
        "version": "1.0.0"
      }
    }
  }
}
```

서버는 요청마다 리비전을 검증합니다. 버전이 없거나 문자열이 아니면 잘못된 파라미터 `-32602`입니다. 지원하지 않는 문자열이라면 정확한 데이터 `{"supported":["2026-07-28"],"requested":"<client version>"}`와 함께 `-32022`를 돌려줍니다. 샘플링 역량이 없다면 `data.requiredCapabilities`를 `{"sampling":{}}`로 설정해 `-32021`을 돌려줍니다.

JSON-RPC `id`가 없는 봉투는 알림(notification)입니다. 수신자는 처리할 수 있지만 성공 응답도 오류 응답도 내보내지 않습니다. Streamable HTTP 어댑터는 수락된 알림에 대해 본문 없는 `202 Accepted`를 돌려줍니다.

서버는 또한 정확한 `supportedVersions` 키, 역량, `ttlMs`, `cacheScope`를 갖춘 `server/discover`를 구현해, 클라이언트가 도구를 호출하기 전에 서버 계약을 학습하고 캐시할 수 있게 합니다. 디스커버리가 `tools`를 알리므로 서버는 필수인 `tools/list`도 구현합니다. 결정론적인 `summarize_repo` 디스크립터에는 유효한 객체형 `inputSchema`, `resultType: "complete"`, 서버 식별 메타데이터, 공개 캐시 힌트가 포함됩니다.

모든 현대식 성공 결과에는 판별자(discriminator)가 있습니다:

- `resultType: "complete"`는 연산이 끝났음을 의미합니다.
- `resultType: "input_required"`는 클라이언트가 포함된 요청들을 이행하고 재시도해야 함을 의미합니다.
- 확장(extension)이 추가 결과 타입을 정의할 수 있습니다. Tasks 확장은 레슨 13에서 `"task"`를 추가합니다.

## MRTR 한 라운드

서버는 요청을 처리하는 도중에 클라이언트를 호출할 수 없습니다. 대신 다음 결과를 돌려줍니다:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "input_required",
    "inputRequests": {
      "pick_files": {
        "method": "sampling/createMessage",
        "params": {
          "messages": [
            {
              "role": "user",
              "content": {
                "type": "text",
                "text": "Choose three representative files and return a JSON array."
              }
            }
          ],
          "systemPrompt": "Return only the requested value.",
          "modelPreferences": {
            "costPriority": 0.8,
            "intelligencePriority": 0.2
          },
          "maxTokens": 400
        }
      }
    },
    "requestState": "opaque-integrity-protected-value"
  }
}
```

클라이언트는 자신이 샘플링을 지원하는지 확인하고, 승인 정책과 모델 정책을 적용한 뒤, 모델 응답을 얻습니다. 그다음 다른 JSON-RPC id로 새 요청을 보냅니다:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "summarize_repo",
    "arguments": {"audience": "developer"},
    "inputResponses": {
      "pick_files": {
        "role": "assistant",
        "content": {
          "type": "text",
          "text": "[\"README.md\", \"server.py\", \"docs/intro.md\"]"
        },
        "model": "host-model",
        "stopReason": "endTurn"
      }
    },
    "requestState": "opaque-integrity-protected-value",
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {"sampling": {}}
    }
  }
}
```

재시도는 프로토콜 세션의 연속이 아닙니다. 원래 메서드와 인자를 반복하고, 이번 라운드의 `inputResponses`만 추가하고, `requestState`를 한 바이트까지 그대로 되돌려 보내는 새 요청입니다.

MRTR은 `tools/call`, `prompts/get`, `resources/read`에서만 허용됩니다. 서버가 무관한 메서드에서 `input_required`를 돌려주면 안 됩니다.

## 다중 라운드 상태

이 레슨에는 두 번의 모델 호출이 필요합니다:

1. `pick_files`는 JSON 배열을 돌려줍니다.
2. `summary`는 최종 산문을 돌려줍니다.

각 재시도는 그 라운드의 응답만 실어 나릅니다. 그래서 서버는 페이즈와 검증된 중간 데이터를 다음 `requestState`에 넣습니다.

그 값을 공격자가 조작할 수 있는 값으로 취급하세요. 페이스 이름을 그냥 서명하는 것으로는 부족합니다. 상태를 다음에 묶으세요:

- 인증된 주체(principal) — 스스로 보고한 `clientInfo`가 아님;
- 최초 메서드;
- 원래 인자의 다이제스트;
- 짧은 만료 시간;
- 현재 페이즈와 검증된 중간값.

기밀성이 필요 없으면 HMAC을 쓰세요. 클라이언트가 상태를 읽어서는 안 되면 인증된 암호화(authenticated encryption)를 쓰세요. 나쁜 서명, 만료된 값, 바뀐 주체, 바뀐 인자는 `-32602`로 거부합니다.

클라이언트는 `requestState`를 파싱하거나 수정해서는 안 됩니다. 클라이언트의 유일한 임무는 재시도 때 정확한 문자열을 그대로 되돌려 보내는 것입니다.

## 모델 선호도는 힌트일 뿐이다

`costPriority`, `speedPriority`, `intelligencePriority`는 독립적인 선호도입니다. 확률 분포가 아니므로 합이 1일 필요도 없습니다. 모델 정책의 소유자는 클라이언트이므로 클라이언트는 이를 무시해도 됩니다.

레거시 샘플링 흐름을 유지 관리한다면 `includeContext`는 `"none"`으로 두세요. 다른 컨텍스트 모드는 유출 위험을 키우며 그 자체로 폐기 대상입니다. 요청에는 최소한의 명시적 컨텍스트만 넘기세요.

## 안전 불변식

포함된 샘플링 요청에 대한 신뢰 경계는 클라이언트입니다.

- 정책상 승인이 필요하다면, 서버가 모델에게 무엇을 시키려 하는지 사용자에게 보여 주세요.
- MRTR 라운드 수에 상한을 두세요. 그렇지 않으면 악의적인 서버가 모델 비용 소모 루프를 만들 수 있습니다.
- 샘플링 응답을 파일 이름, URL, 도구 입력으로 쓰기 전에 반드시 검증하세요.
- 라운드당 바이트와 토큰 수를 제한하세요.
- 현재 클라이언트 역량에 선언되지 않은 입력 요청은 거부하세요.
- 모델 출력이 권한 결정에 들어가지 않게 하세요.
- 민감한 프롬프트 내용은 로그에 남기지 않으면서 최초 메서드와 입력 요청 키는 기록하세요.

`clientInfo`와 `serverInfo`는 표시·진단용 메타데이터입니다. 어느 쪽도 인증된 신원으로 쓰지 마세요.

```figure
t3-sampling-flip
```

## 만들기

`code/main.py`는 서드파티 패키지 없이 두 라운드 전체 흐름을 구현합니다:

- `server/discover`는 `supportedVersions`를 돌려주고 도구 지원을 알리며 캐시 힌트를 돌려줍니다.
- `tools/list`는 객체형 입력 스키마를 갖춘 결정론적·캐시 가능한 `summarize_repo` 디스크립터를 돌려줍니다.
- `tools/call`은 요청별 메타데이터를 검증합니다.
- 첫 결과는 파일 선택을 위한 `sampling/createMessage`를 포함합니다.
- 첫 재시도에서는 모델 결과를 검증하고 두 번째 요청을 포함합니다.
- HMAC으로 보호된 `requestState`가 독립된 요청들 사이에서 페이즈를 전달합니다.
- 최종 결과는 `resultType: "complete"`를 사용합니다.

가짜 호스트 모델 덕분에 예제가 결정론적으로 동작합니다. 실제 호스트에 연결할 때는 `fake_host_model`만 교체하세요. 서버 쪽 상태 기계는 결정론적이고 테스트 가능하게 유지해야 합니다.

## 사용하기

저장소 루트에서:

```bash
cd phases/13-tools-and-protocols/11-mcp-sampling/code
python3 main.py
python3 -m unittest discover tests -v
```

기대 체크포인트:

- 디스커버리가 `ttlMs`와 `cacheScope`를 갖춘 complete 결과를 돌려줍니다.
- 도구 디스커버리가 `resultType`, 서버 식별, 캐시 힌트를 갖춘 동일한 정렬된 디스크립터를 돌려줍니다.
- 역량 누락과 미지원 버전이 정확한 `-32021`, `-32022` 오류 데이터를 사용합니다.
- id 없는 알림은 JSON-RPC 응답을 만들지 않습니다.
- 요청 id가 `[1, 2, 3]`이어서 각 MRTR 라운드가 독립적임을 증명합니다.
- 처음 두 결과는 `input_required`입니다.
- 최종 결과는 `complete`이며 선택된 파일들과 요약을 담고 있습니다.
- 재시도에서 원래 인자를 바꾸면 요청 상태 검사에 실패합니다.

## 출시하기

`outputs/skill-sampling-loop-designer.md`는 이제 마이그레이션 플래너입니다. 먼저 샘플링을 없애고 모델 직접 연동으로 갈아탈지 결정합니다. 호환이 필요하다면 MRTR 라운드, 상태 바인딩, 역량 게이트, 예산, 검증, 제거 계획을 산출합니다.

## 연습 문제

1. 파일 선택 응답을 잘못된 JSON으로 바꾸세요. 서버가 모델 출력을 믿지 않고 `-32602`를 돌려주는지 확인합니다.
2. 첫 호출과 재시도 사이에서 `audience`를 바꾸세요. 봉인된 상태가 요청 간 재사용을 어떻게 막는지 설명합니다.
3. 요약을 비평(critique)하도록 호스트에 요구하는 세 번째 라운드를 추가하세요. 이전 요약을 서명된 상태 안에 실어 나르고, 전체 흐름을 세 라운드로 제한합니다.
4. 가짜 호스트 콜백을 서버 소유의 모델 어댑터로 교체해 샘플링을 제거하세요. 승인, 과금, 관측 책임 중 어떤 것들이 서버로 옮겨가는지 목록화합니다.
5. 마감 시각에서 1초 지난 상태 값으로 만료 테스트를 추가하세요.

## 핵심 용어

| 용어 | 2026-07-28에서의 의미 |
|------|------------------------|
| 샘플링(Sampling) | 클라이언트의 모델에게 완성(completion)을 요구하던 폐기된 기능 |
| MRTR | 요청 도중 클라이언트 입력이 필요할 때 쓰는 상태 없는 재시도 패턴 |
| `InputRequiredResult` | `resultType: "input_required"`인 결과 |
| `inputRequests` | 포함된 elicitation·샘플링·루츠 요청의 서버 할당 맵 |
| `inputResponses` | `inputRequests`와 같은 키를 쓰는, 이번 라운드의 클라이언트 결과 |
| `requestState` | 클라이언트가 그대로 되돌려 보내고 서버가 검증하는 불투명(opaque) 서버 상태 |
| `resultType` | 현대적 MCP 결과에 필수인 판별자 |
| 모델 직접 연동 | 모델 추론이 필요한 새 서버에 권장되는 대체 방식 |
| 역량 게이트(Capability gate) | 클라이언트가 광고하지 않은 포함 요청을 보내지 못하게 막는 규칙 |
| 루프 예산(Loop budget) | 연산에 허용되는 최대 라운드·토큰·바이트·시간·비용 |

## 레거시 호환성

2025-11-25에 고정된 클라이언트는 살아있는 연결 위에서 구식 서버 주도 `sampling/createMessage` 흐름을 여전히 쓸 수 있습니다. 그 동작은 버전별 어댑터 안에만 두세요. 세션 기반 경로를 2026-07-28 서버의 아키텍처로 삼지 마세요.

공식 SDK는 구형 피어를 위해 현대식 `input_required` 핸들러를 번역해 줄 수 있습니다. 그 심(shim)은 호환성 경계일 뿐, 새로운 세션 의존 로직을 추가할 허가가 아닙니다.

## 더 읽을거리

- [MCP 2026-07-28 Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [MCP Sampling deprecation](https://modelcontextprotocol.io/seps/2577-deprecate-roots-sampling-and-logging)
- [MCP 2026-07-28 server discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
