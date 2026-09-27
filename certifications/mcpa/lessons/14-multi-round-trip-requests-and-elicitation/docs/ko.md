> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 멀티 라운드 트립 요청(MRTR)과 엘리시테이션(Elicitation)

> 호출 도중에 사용자의 확인이 필요한 서버는 커넥션을 붙잡아 둔 채 기다리지 않습니다. 호출을 끝내고, 클라이언트에게 영수증을 건네고, 완전히 새로운 요청이 첫 번째 요청이 멈춘 지점에서 이어받게 합니다.

**유형:** 참고 자료
**사용 언어:** Python
**선수 지식:** 레슨 13
**소요 시간:** 약 45분

## 학습 목표

- 멀티 라운드 트립 요청(MRTR)이 엘리시테이션, 샘플링, 루츠 같은 서버 주도 요청을 대체한 이유와, 그 거래가 수평 확장된 서버에게 무엇을 사다 주는지 설명합니다
- InputRequiredResult와 그 재시도를 평범한 JSON-RPC 메시지로 읽습니다. inputRequests, inputResponses, 그리고 정확히 에코해야 하는 requestState죠
- 폼 모드 엘리시테이션과 URL 모드 엘리시테이션을 구분하고, 민감한 데이터에는 어느 쪽을 써야 하는지 압니다
- 표준 라이브러리의 hmac과 hashlib로 requestState를 보호해서, 신뢰할 수 없는 클라이언트를 거치면서도 위조 가능한 능력(capability)이 되지 않게 합니다
- 변조되었거나 만료되었거나 잘못 묶인 requestState를 정상과 구분하고, 서버가 각각을 왜 거부해야 하는지 설명합니다

## 문제 상황

배포 도구가 어떤 서비스의 가동 중인 릴리스를 교체하려 합니다. 그 전에 사용자의 yes가 필요합니다. 이 단 하나의 요구사항이 예전에는 올바르게 만들기에 비쌌습니다.

예전 패턴에서는 서버가 원래 요청을 스트림 위에 열어 둔 채, 같은 커넥션을 따라 `elicitation/create` 같은 자기만의 별도 요청을 보냈습니다. 클라이언트는 두 번째 요청으로 답했고, 서버는 그 답을 아직 기다리고 있던 첫 번째 요청과 다시 맞춰야 했습니다. 단일 프로세스가 단일 클라이언트와 대화하는 경우 그 맞추기는 사소합니다. 같은 프로세스가 양쪽 끝을 쥐고 있으니까요. 문제는 서버가 프로세스 하나를 넘어서는 순간 시작됩니다. 로드 밸런서가 확인 절차를, 원래 호출을 쥐고 있던 복제본이 아닌 다른 복제본으로 라우팅해버리면, 서버는 하나의 대화를 이루는 두 조각을 다시 합치기 위해 공유 저장소 계층이나 클라이언트를 한 인스턴스에 고정하는 스티키 라우팅이 필요해집니다. 어느 쪽 해법도 비쌉니다. 공유 저장소는 가용성과 정리 문제를 자체적으로 안고 있는 새 의존성이고, 스티키 라우팅은 상태 없는 복제본 부대가 의지하는 고른 부하 분산을 깨뜨립니다.

그 비용은 흔한 경우에 가장 크게 떨어집니다. 대부분의 도구는 일회용입니다. 배포 도구 자신의 논리 중 "확실한가요?"를 묻는 순간과 "네"를 듣는 순간 사이에 살아남아야 할 것은 아무것도 없습니다. 앞선 레슨들의 상태 없는 코어는 이미, 서버가 요청 사이의 무언가를 기억하기 위해 커넥션에 기대지 못한다고 확립했습니다. 서버 주도 요청은 호출 도중 답이 필요해지는 순간 그 약속을 깨뜨렸습니다. 그 답이 안전하고 빠르게 착지할 수 있는 유일한 곳이 여전히 그 답을 블로킹하며 기다리던 프로세스 안이었기 때문입니다.

## 핵심 개념

멀티 라운드 트립 요청은 서버 주도 요청을 완전히 제거합니다(SEP-2322). 열려 있는 호출 안에서 질문을 던지는 대신, 더 많은 정보가 필요한 서버는 별개 종류의 결과로 호출을 일찍 끝내고, 클라이언트는 서버가 요청한 것을 손에 넣은 뒤 완전히 새롭고 독립적인 요청을 시작합니다. 흐름은 네 단계입니다. 클라이언트가 요청을 보낸다. 서버가 더 필요하다고 판단해 그 요청을 `resultType: "input_required"`로 끝낸다. 클라이언트가 빠진 정보를 모은다. 클라이언트가 답들을 실은 원래 요청을 자기만의 새 id로 재시도한다. 네 번째 단계는 어느 서버 복제본이 첫 단계나 두 번째 단계에 답했는지, 네 번째 단계 자체에 답할지와 아무 상관이 없습니다. 어느 것이든 가능합니다. 필요한 모든 것이 요청과 함께 이동하기 때문입니다.

`InputRequiredResult`는 선택적 필드 둘을 실으며, 이 모양의 모든 응답은 둘 중 최소 하나를 포함해야 합니다. `inputRequests`는 서버가 고른 문자열 키에서 요청 객체로의 맵이며, 그 요청 객체는 `elicitation/create`, `sampling/createMessage`, `roots/list` 셋 중 정확히 하나여야 합니다. 클라이언트가 이 같은 요청에서 짝이 되는 캐퍼빌리티를 선언하지 않았다면 서버는 그 맵에 요청 타입을 절대 놓아서는 안 됩니다. 도구가 항상 확인을 필요로 하는데 호출자가 `elicitation`을 선언하지 않았다면 올바른 응답은 프로토콜 오류, 즉 `data.requiredCapabilities`에 무엇이 빠졌는지 밝히는 `-32021 MissingRequiredClientCapability`입니다. 캐퍼빌리티 협상 레슨이 소개했던 바로 그 패턴이죠. `input_required` 결과를 받을 수 있는 클라이언트 요청은 세 개뿐입니다. `tools/call`, `prompts/get`, `resources/read`입니다. 그 밖의 모든 요청은 언제나 `complete`로 끝납니다.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "input_required",
    "inputRequests": {
      "confirm": {
        "method": "elicitation/create",
        "params": {
          "mode": "form",
          "message": "Deploy checkout to production? This replaces the running release.",
          "requestedSchema": {
            "type": "object",
            "properties": {"confirmed": {"type": "boolean", "title": "Confirm deploy"}},
            "required": ["confirmed"]
          }
        }
      }
    },
    "requestState": "eyJwcmluY2lwYWwiOiJ1c2VyLWFsaWNlIn0.9f2c...redacted"
  }
}
```

`requestState`는 상태 없는 서버가 아무것도 기억하지 않고도 이 대화를 다시 집어 들게 해주는 필드입니다. 그것을 발행한 서버에게만 의미가 있는 불투명한 문자열입니다. 클라이언트는 그것을 들여다보거나 파싱하거나 단 한 바이트도 바꿔서는 안 됩니다. 재시도 시 클라이언트는 그것을 정확히 그대로 에코하거나, 애초에 서버가 보낸 적 없다면 아예 생략합니다. 그 문자열은 서버가 완전히 신뢰하지 않는 클라이언트를 거쳐 가므로, 명세는 인가, 리소스 접근, 비즈니스 로직에 영향을 주는 순간 그것을 공격자가 제어하는 것으로 다루고, 검증에 실패하는 무엇이든 거부하는 무결성 보호(HMAC 또는 AEAD 암호)를 요구합니다. 좋은 관행은 보호된 페이로드 안에 세 가지를 묶어 넣고 재시도마다 셋 모두 검사합니다. 인증된 주체(principal), 그래야 한 사용자의 확인 토큰을 다른 사람이 재생할 수 없고. 짧은 만료, 그래야 낡은 토큰이 며칠 뒤 되떠오를 수 없고. 원래 요청의 핵심 파라미터에 대한 다이제스트, 그래야 한 호출을 위해 발행된 토큰이 같은 도구 이름에 다른 인자를 가진 다른 호출로 방향을 틀 수 없고. 이 세 검사 중 그 어느 것도 그 자체로 일회성을 보장하지는 않으므로, 토큰이 최대 한 번만 상환되어야 하는 서버는 그 사실을 여전히 서버 쪽에서 추적해야 합니다.

재시도 자체는 새 JSON-RPC id를 가진 새 요청입니다. `input_required`를 받은 호출과 같은 id일 수 없습니다. 둘은 우연히 같은 `name`과 `arguments`를 공유할 뿐인 독립적인 요청들이기 때문입니다. 재시도는 `params.inputResponses`를 추가합니다. 서버가 `inputRequests`에 발행했던 것과 같은 키를 쓰는 맵이고, 각 값은 짝이 되는 결과 타입, 즉 `ElicitResult`, `CreateMessageResult`, `ListRootsResult`입니다.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "deploy_release",
    "arguments": {"service": "checkout", "environment": "production"},
    "inputResponses": {"confirm": {"action": "accept", "content": {"confirmed": true}}},
    "requestState": "eyJwcmluY2lwYWwiOiJ1c2VyLWFsaWNlIn0.9f2c...redacted"
  }
}
```

엘리시테이션 자체에는 두 모드가 있습니다. 폼 모드는 클라이언트가 원시 타입 속성의 평면적 객체로 제한된 `requestedSchema`를 통해 구조화된 데이터를 수집하게 합니다. 문자열, 숫자, 불리언, 단일 또는 다중 선택 열거형까지, 중첩은 없습니다. URL 모드는 사용자를 클라이언트가 결코 렌더링하지도 들여다보지도 않는 페이지로 보냅니다. 서드파티 OAuth 흐름이나 결제 폼 같은 상호작용을 위한 것이죠. 서버는 비밀번호, API 키, 토큰, 결제 정보에는 URL 모드를 써야 하고 결코 폼 모드를 써서는 안 됩니다. 모든 `ElicitResult`는 세 동작 중 하나를 보고합니다. `accept`(폼 모드라면 `content`와 함께), `decline`, `cancel`입니다. 2026-07-28 이전에는 URL 모드 엘리시테이션이 자체적인 `elicitationId`도 실었고, 서버는 대역 외 단계가 끝났을 때 `notifications/elicitation/complete` 알림을 보낼 수 있었으며, URL 엘리시테이션이 필요하다는 신호를 위한 오류 코드 `-32042`도 있었습니다. 셋 모두 제거되었습니다. 모든 MRTR 교환이 이미 쓰는, requestState를 실은 평범한 재시도만으로 서버가 결과를 알 수 있으니, 여분의 장치는 사라진 겁니다.

```figure
mcpa-14-mrtr
```

## 인터랙티브 랩

그림은 클라이언트와 서버를 두 레인으로 펼쳐놓고 하나의 배포 시도가 두 번의 왕복을 건너가는 과정을 따라갑니다. 첫 화살표는 평범한 `tools/call`입니다. 응답은 블로킹하는 대신 그 요청을 `input_required`로 끝냅니다. 노트 하나가 클라이언트가 자리를 비워 사용자의 답을 모으는 동안의 간극을 표시합니다. 두 번째 화살표는 `inputResponses`와 첫 응답의 `requestState` 문자열을 그대로 실은 새롭고 독립적인 `tools/call`이고, 마지막 화살표는 평범한 `complete` 결과입니다. 간극을 건너는 것은 클라이언트가 돌려보내기로 선택한 것뿐이며, 두 요청을 가로지르는 서버 쪽 기억은 없습니다.

## 실습 랩

`code/main.py`를 열어 보세요. `DeployServer`는 도구 하나, `deploy_release`를 노출합니다. 실행 전에 항상 확인을 요구하며, 폼 모드 엘리시테이션과 `hmac`과 `hashlib`만으로 만든 HMAC 보호 `requestState`를 씁니다. `mint_request_state`는 주체, 이 레슨의 추상적인 클록 틱으로 잰 만료, 그리고 도구 이름과 인자의 SHA-256 해시인 `digest_request`를 담은 페이로드에 서명합니다. `verify_request_state`는 `hmac.compare_digest`로 서명을 다시 계산한 뒤 주체, 만료, 다이제스트를 차례로 검사하고, 마지막으로 토큰의 nonce가 이미 소비되지 않았는지 검사합니다.

```bash
python3 code/main.py
```

실행하고 여섯 가지 결과를 찾아보세요. `elicitation` 캐퍼빌리티를 한 번도 선언하지 않은 게스트 클라이언트는 서버가 쓸 수 없는 `inputRequests` 항목을 만들기도 전에 `-32021`로 즉시 거부됩니다. Alice가 배포를 확인하면 재시도가 `structuredContent.deployed` true로 완료됩니다. Alice가 다른 배포를 거절하면 재시도는 그래도 완료됩니다. `isError` false로요. 거절은 실패가 아니라 정상적인 결과이고, 배포되는 것은 아무것도 없습니다. 그다음은 네 가지 일부러 만든 반례가 옵니다. 각각은 트랜스크립트에서 `violation`으로 감싸 있어서 와이어 검사기가 깨진 입력의 시연을 레슨의 버그로 오해하지 않습니다. `requestState` 서명이 한 글자 뒤집힌 재시도, 상태의 짧은 만료가 지난 뒤 도착하는 재시도, 서버가 Alice를 위해 발행한 상태를 Mallory가 재생하는 재시도, 그리고 Alice 자신의 유효한 상태를 유지하면서 대상 환경을 몰래 바꿔치기한 재시도입니다. 이 넷은 모두 도구 실행 오류, 즉 `isError: true`로 돌아오며 일상 언어의 이유가 붙습니다. 이 트랙의 다른 곳에서 만료된 핸들이 쓰는 것과 같은 채널이죠. 명세는 검증에 실패한 상태를 거부하라고 요구할 뿐 채널은 이름 짓지 않습니다. 이 랩은 모델이 복구할 수 있도록 도구 실행 오류를 택했고, 서버가 다시 묻는 새로운 `input_required` 결과로 답하는 것도 똑같이 가능합니다. 그 응답을 읽은 모델은 새 확인을 위해 도구를 다시 호출할 수 있습니다. 위조된 서명을 고칠 수는 없지만, 불투명한 실패에 갇히는 대신 깔끔하게 재시도할 수는 있습니다.

## 제공되는 산출물

`outputs/mrtr-implementation-checklist.md`가 한 페이지 버전입니다. `input_required`로 호출을 끝낼 때 서버가 해야 하는 것과 하면 안 되는 것, `requestState`를 보호하는 방법, 클라이언트가 그 대가로 갚아야 할 것, 폼 모드와 URL 모드를 고르는 표, 그리고 시험 전에 다시 읽어둘 만한 함정들이 담겨 있습니다.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨이 주장하는 동작들을 검사합니다. 새 호출이 `inputRequests`와 `requestState`를 실은 `input_required`를 돌려주는지, 새 id와 승인된 확인을 곁들인 재시도가 완료되며 배포를 기록하는지, 재시도가 `requestState`를 바이트 단위로 에코하는지, 거절이 아무것도 배포하지 않고 완료되는지, 변조된 서명, 만료된 상태, 다른 주체의 상태, 다른 인자로 방향을 튼 상태가 각각 도구 실행 오류로 거부되는지, 상환된 상태는 두 번 쓸 수 없는지, `elicitation` 캐퍼빌리티 없는 클라이언트는 자신이 답할 수 없는 `inputRequests` 항목을 결코 받지 않는지, 그리고 빠진 필수 인자가 프로토콜 오류가 아니라 도구 실행 오류인지입니다. 저장소의 와이어 검사기는 같은 트랜스크립트를 2026-07-28 규칙에 대해 곧장 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/14-multi-round-trip-requests-and-elicitation
```

## 캡스톤 연계

캡스톤의 단일 엔드투엔드 교환에는 동의를 위한 MRTR 엘리시테이션이 포함되며, 이 레슨이 만드는 것과 같은 종류의 `requestState`로 보호됩니다. 주체와 만료, 그것이 속한 요청의 다이제스트에 묶여 있고, 변조 시도는 워크스루의 일부로 거부됩니다. 여기 있는 모든 것, 네 단계 흐름, 새 id 규칙, 정확한 에코, 프로토콜 오류와 도구 실행 오류의 구분이 바로 그 마지막 장면이 여러분이 이미 완벽히 안다고 가정하는 내용입니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| MRTR | 멀티 라운드 트립 요청. 서버 주도 요청을 밀어넣는 대신 호출을 input_required로 끝내는 패턴 |
| InputRequiredResult | resultType이 input_required인 결과. inputRequests와 requestState 중 하나 이상을 실는다 |
| inputRequests | 서버가 고른 키에서 elicitation/create, sampling/createMessage, roots/list 요청으로의 맵 |
| inputResponses | 클라이언트의 재시도 필드. inputRequests와 같은 방식으로 키가 매겨진 답들을 실는다 |
| requestState | 서버가 발행한 불투명한 문자열. 클라이언트는 정확히 에코해야 하고 해석해서는 안 된다 |
| 폼 모드 엘리시테이션 | 평면적인 requestedSchema로 검증되는, 대역 내 구조화 데이터 수집 |
| URL 모드 엘리시테이션 | 클라이언트가 들여다보지 않는 URL에서의 대역 외 상호작용. 민감한 데이터에 필수 |
| ElicitResult 동작 | accept, decline, cancel 셋 중 하나. 모두 서버가 처리해야 하는 정상적인 결과 |
| 주체 바인딩 | requestState를 인증된 호출자에게 묶어 다른 사람이 재생하지 못하게 하는 것 |
| 일회성 강제 | 상환된 requestState의 nonce가 두 번 쓰일 수 없게 하는 서버 쪽 검사 |

## 더 읽을거리

- [멀티 라운드 트립 요청](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [엘리시테이션(Elicitation)](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation)
- [SEP-2322: 멀티 라운드 트립 요청](https://modelcontextprotocol.io/seps/2322-MRTR)
- [SEP-1036: 안전한 대역 외 상호작용을 위한 URL 모드 엘리시테이션](https://modelcontextprotocol.io/seps/1036-url-mode-elicitation-for-secure-out-of-band-intera)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 7, 11절
- `phases/13-tools-and-protocols/12-mcp-roots-and-elicitation`, 서버 작성자 쪽에서 엘리시테이션을 짚어보는 단계
