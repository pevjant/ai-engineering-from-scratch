> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 구독 스트림: 알림(Notifications), 진행 상황, 취소

> 알림은 결코 답장을 받지 못합니다. 그래서 자기 혼자서 자신이 어느 대화에 속하는지 말해야 합니다. 자신을 연 오래 사는 스트림인지, 아니면 자신을 기다리는 그 하나의 요청인지요.

**유형:** 참고 자료
**사용 언어:** Python
**선수 지식:** 레슨 15
**소요 시간:** 약 45분

## 학습 목표

- 알림과 요청을 구분하고, 수신자가 알림에 절대 답해서는 안 되는 이유를 설명합니다
- subscriptions/listen 스트림을 열고, 그 승인 응답을 읽고, 실려 오는 알림을 subscriptionId로 디멀티플렉싱합니다
- 스트림 알림(list changed, resource updated)과 요청 범위 알림(progress, message)을 추측이 아니라 각자가 이동하는 채널로 구분합니다
- 진행 알림의 토큰과 총량을 추적하고, progress 값이 계속 증가해야 하는 이유를 설명합니다
- 각 트랜스포트에서 요청이나 구독을 취소하고, 취소와 이미 배송 중이던 메시지 사이의 경쟁 상태를 다룹니다

## 문제 상황

MCP의 대부분은 요청 하나에 응답 하나입니다. 클라이언트가 물으면 서버가 답하고, 교환은 끝납니다. 하지만 그 모양은 서버가 클라이언트에게 말해야 할 모든 것에 맞지 않습니다. 계속 이어지는 정보가 있습니다. 도구 목록이 바뀌었다든지, 구독한 리소스에 쓰기가 있었다든지, 프롬프트가 추가되었다든지요. 단일 응답은 "계속 이야기를 들려달라"를 실을 수 없습니다. 응답은 자기가 속한 요청을 닫아버리기 때문입니다. 주변 환경적인 정보도 있습니다. 30초 걸리는 호출이 5분의 1쯤 진행됐다고 알려주면 유용하지만, 그 보고는 답이 아니라 답이 아직 계산되는 동안의 해설일 뿐입니다. 그리고 때로는 클라이언트가 요청이나 구독이 이미 돌아가는 중에 마음을 바꾸는데, 취소 플래그를 걸어둘 세션이 없습니다. 레슨 04의 상태 없는 코어 덕에, 서버는 애초에 이 하나의 커넥션을 위한 사적 공간을 열어두고 있지도 않았습니다. 그래서 취소 역시 다른 모든 것과 똑같이 동작해야 합니다. id로 주소가 지정된, 자기 힘으로 서는 메시지로요.

MCP는 계속 이어지는 경우는 클라이언트가 의도적으로 여는 스트림, `subscriptions/listen`으로 답하고, 주변 환경적인 경우는 그것을 만들어낸 그 하나의 요청에 묶인 알림, 즉 `notifications/progress`와(레슨 15에서 다룬 deprecated 로깅 기능에서 온) `notifications/message`로 답합니다. 이 모두는 평범한 JSON-RPC 알림입니다. 메서드와 파라미터가 있고, id는 없으며, 결코 답하지 않죠. 이들을 가르는 것은 어떤 채널이 실어 나르는지, 그리고 여러 개가 동시에 돌아갈 때 수신자가 무엇과 무엇을 어떻게 구분하는지입니다.

## 핵심 개념

알림은 레슨 03의 봉투에서 떠올리듯, `id`가 없는 유일한 JSON-RPC 모양입니다. 특정한 무언가에 대한 답장일 수 없고, 수신자는 답장을 보내서도 안 됩니다. 그 한 줄 규칙만으로도 MCP가 알림에게 서로 다른 두 집이 왜 필요한지 설명됩니다. 요청의 응답 채널은 그 요청이 열려 있는 동안만 존재하므로, 진행 상황처럼 단일 호출에 속한 것들은 자연스럽게 그곳을 탑니다. 반면 단일 호출에 속한 무엇도 "지금 도구 목록이 다르다" 같은 계속 이어지는 변화를 설명할 수 없습니다. 그런 일이 일어나는 시점에 진행 중인 호출이 없을 수도 있으니까요. 그래서 프로토콜은 어떤 요청 하나보다 오래 사는 채널이 필요합니다. 자기만의 요청으로 열어 의도적으로 살려두는 스트림이요.

`subscriptions/listen`이 그 스트림을 엽니다. 클라이언트가 평범한 요청을 보내는데, `params.notifications` 필드가 필터입니다. `toolsListChanged`, `promptsListChanged`, `resourcesListChanged`는 불리언이고, `resourceSubscriptions`는 업데이트를 지켜볼 URI의 리스트입니다. 서버는 클라이언트가 요청하지 않은 알림 타입을 결코 보내서는 안 되고, 아예 지원하지 않는 타입이라면 요청받은 것보다 적게 허가해도 됩니다.

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "subscriptions/listen",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    },
    "notifications": {
      "toolsListChanged": true,
      "resourceSubscriptions": ["file:///project/config.json"]
    }
  }
}
```

서버가 그 스트림 위로 돌려보내는 맨 첫 메시지는 무엇보다도 `notifications/subscriptions/acknowledged`입니다. 서버가 실제로 지키는 필터의 부분집합을 실고, `_meta["io.modelcontextprotocol/subscriptionId"]`에는 스트림을 연 `subscriptions/listen` 요청의 id, 여기서는 `7`을 실습니다. 디멀티플렉싱 체계는 이게 전부입니다. 이 스트림에 속한 이후 모든 메시지, 즉 승인 응답과 그 뒤의 모든 알림이 같은 구독 id를 반복해서 실습니다. 하나의 stdio 채널 위에 구독 둘을 열었거나 별개의 HTTP 스트림들 위에 여러 구독을 연 클라이언트는 오직 이 필드를 읽어서 구분합니다. 트랜스포트 커넥션은 구독이 아니고, 구독은 커넥션이 아니기 때문입니다.

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/subscriptions/acknowledged",
  "params": {
    "_meta": {"io.modelcontextprotocol/subscriptionId": 7},
    "notifications": {"toolsListChanged": true, "resourceSubscriptions": ["file:///project/config.json"]}
  }
}
```

승인 응답 다음에는 알림 메서드 넷이 더 같은 스트림 위를 다닐 수 있고, 언제나 같은 방식으로 태그됩니다. `notifications/tools/list_changed`, `notifications/prompts/list_changed`, `notifications/resources/list_changed`, 그리고 바뀐 `uri`를 실는 `notifications/resources/updated`입니다. 그 밖의 어떤 것도 그곳에 속하지 않습니다. `notifications/progress`와 `notifications/message`는 요청 범위입니다. 자신을 요청한 그 하나의 호출에만 응답하고, 결코 구독에 응답하지 않으며, 구독 id를 절대 실지 않습니다. Progress는 대신 `progressToken`을 실는데, 클라이언트가 고른 값으로 자기 활성 요청들 사이에서 유일해야 합니다. 거기에 더해 총량을 모를 때조차 알림마다 엄격히 증가해야 하는 `progress` 숫자와, 선택적인 `total`과 사람이 읽을 수 있는 `message` 필드가 붙습니다. 서버는 진행 상황을 원하는 속도로 보낼 수도, 아예 안 보낼 수도 있지만, 요청이 끝나면 반드시 멈춰야 하고, 양쪽 모두 채널을 홍수내기보다 속도를 제한해야 합니다. 레슨 15의 deprecated 로깅 알림인 `notifications/message`는 자기 `_meta`에 로그 레벨을 설정한 요청 위에만 나타납니다. 그 키가 없다면 서버는 보내서는 안 됩니다.

취소는 메시지 모양이 아니라 트랜스포트로 갈립니다. Streamable HTTP에서는 요청의 SSE 응답 스트림을 닫는 것 자체가 취소 신호입니다. 알림이 보내지지도, 기대되지도 않습니다. 닫을 요청별 스트림이 따로 없는 stdio에서는 클라이언트가 멈추고 싶은 `requestId`와 선택적 `reason`을 곁들인 `notifications/cancelled`를 보냅니다. 서버가 스스로 `notifications/cancelled`를 만드는 유일한 경우는 자신이 끝내려는 `subscriptions/listen` 스트림을 철거할 때입니다. 서버는 다른 어떤 목적으로도 그 알림을 보내서는 안 되므로, 서버로부터 온 것을 보는 것 자체가 방금 어떤 종류의 스트림이 닫혔는지에 대한 강한 신호입니다.

구독은 우아하게 끝날 수도 있습니다. 그 `subscriptions/listen` 요청은 형식적으로는 스트림이 살아 있는 동안 내내 열려 있는 JSON-RPC 요청입니다. 서버가 종료 중일 때처럼 자기 주도로 구독을 끝내기로 하면, 스트림을 닫기 전에 그 원래 요청에 결과로 답해야 합니다. `resultType` complete, `_meta`에는 같은 구독 id를 실어서요. 그 결과 덕에 클라이언트는 "이 스트림은 깔끔하게 끝났다"와 "트랜스포트가 그냥 증발했다"를 구분할 수 있습니다. 후자는 그런 메시지를 전혀 실지 않으니까요. 취소와 전달은 동시에 일어나는 두 가지 독립적인 일이라서, 취소가 효력을 발휘하기 몇 순간 전에 만들어진 알림이 수신자가 이미 그 id 추적을 멈춘 뒤에 도착할 수도 있습니다. 양쪽 다 이를 오류로 취급하기보다 감내하는 것이 기대됩니다. 보내는 쪽은 이제 취소할 것이 없을 수 있고, 받는 쪽은 더 이상 알아보지 못하는 메시지를 어디로도 라우팅하지 않고 그냥 버리면 됩니다.

상태 없음의 또 하나의 귀결이 여기서 직접 드러납니다. stdio 프로세스가 재시작하면 새 서버 프로세스는 옛 프로세스가 열어둔 구독에 대한 기억을 하나도 갖고 있지 않습니다. 클라이언트는 아직 원하는 각 스트림을 다시 세우려면 새 id를 곁들여 `subscriptions/listen`을 다시 보내야 합니다. 아무것도 재개되지 않고, 재시작 이전의 것은 아무것도 재생되지 않습니다. 서버가 그것을 담아둘 세션이 없었으니까요.

```figure
mcpa-16-subscription-stream
```

## 인터랙티브 랩

그림은 클라이언트와 서버를 나란히 놓고 하나의 시나리오가 페이지를 따라 내려가는 과정을 따라갑니다. `subscriptions/listen` 요청 두 개가 열리고, 각각 먼저 자기 id를 `_meta`에 실은 승인 응답을 받으며, 뒤따르는 알림들도 같은 방식으로 태그됩니다. 그래서 tools-and-config 구독과 resources-only 구독은 같은 채널을 공유하면서도 절대 뒤섞이지 않습니다. 그 아래 별개의 `tools/call`이 자기만의 요청과 응답을 돌리며 그 사이에 자기만의 진행 틱을 흘립니다. 그 세 개의 진행 알림 중 어느 것도 구독 id를 실지 않습니다. 그것들은 어느 스트림도 아니라 그 호출에 속하기 때문입니다. 바닥 근처에서 클라이언트가 두 번째 구독을 취소하고, 이미 배송 중이던 그 구독의 엉뚱한 업데이트가 어차피 도착하지만 전달되는 대신 버려집니다. 그림을 먼저 모양을 보고 한 번 읽은 뒤, 어떤 필드, 즉 구독 id인지 진행 토큰인지를 추적해서 이 채널들을 절대 뒤섞지 않게 만드는 코드를 쓸 수 있는지 확인해 보세요.

## 실습 랩

`code/main.py`를 열어 보세요. `SubscriptionServer`는 열려 있는 각 `subscriptions/listen` 요청을 실제로 허가한 알림 타입을 곁들인 `Subscription`으로 추적하고, `resource_updated`, `list_changed`, `cancel`, `close_gracefully`를 스트림 메시지를 만들어내는 유일한 방법으로 노출합니다. 각각은 구독이 닫혔거나 그 타입을 한 번도 허가받지 못했다면 무엇도 내보내기를 거부합니다. `call_long_job`은 평범한 `tools/call`에 답하고, 요청이 `progressToken`을 실었다면 최종 결과와 함께 짧은 진행 알림 행렬을 돌려주며, 어떤 구독과도 완전히 별개입니다. `SubscriberClient`는 `subscriptions/listen`을 보내고 승인 응답을 기록하며, 이후 모든 것을 `receive_stream`으로 디멀티플렉싱합니다. 이 메서드는 클라이언트가 로컬에서 여전히 알아보는 구독 id를 가진 알림만 받아들입니다.

```bash
python3 code/main.py
```

출력된 트랜스크립트를 개념 섹션과 대조하며 읽어 보세요. 승인 응답 둘을 찾아 각 구독 id가 자신을 만들어낸 `subscriptions/listen` 요청의 id와 같은지 확인하세요. `run_build` 호출의 진행 알림 셋을 찾아 어느 것도 `_meta`를 아예 실지 않는지 확인하세요. 끝 근처의 취소와 그 바로 뒤의 감싼 항목, 방금 취소된 구독을 위한 `resources/updated` 알림도 찾아보세요. 클라이언트가 전달하지 않고 버려야 하기 때문에 일부러 만든 위반으로 표시되어 있습니다. 그다음 `promptsListChanged`에 대한 세 번째 구독을 열어 보고, 그것에 대해 `list_changed`를 호출해 `None`이 돌아오는 모습을 지켜보세요. 이 서버는 이를 허가할 prompts 캐퍼빌리티를 한 번도 선언하지 않았기 때문입니다.

## 제공되는 산출물

`outputs/notification-routing-table.md`는 이 레슨의 모든 알림 메서드를 채널, 필수 필드, 그리고 그것을 지배하는 규칙에 매핑한 한 페이지 참고 자료입니다. 어느 넷이 listen 스트림 위에서만 나타나는지, 어느 둘이 요청 범위인지 그 이유는 무엇인지, 그리고 무언가를 취소하고 싶을 때 클라이언트가 각 트랜스포트에서 무엇을 해야 하는지요. 뒤 레슨의 오류 코드 표 옆에 두세요. 시간에 쫓겨 트랜스크립트의 알림을 해석해야 할 때 손이 가는 두 참고 자료가 됩니다.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검사합니다. 승인 응답이 스트림 위의 첫 메시지이며 listen 요청의 id를 구독 id로 실는지, 승인 응답이 서버가 실제로 허가하는 알림 타입만 에코하는지, 요청되지 않았거나 허가되지 않은 타입은 결코 보내지지 않는지, 진행 값이 엄격히 증가하며 구독 id를 결코 실지 않는 반면 진짜 스트림 알림은 언제나 실는지, 구독을 취소하면 서버가 그 이상 아무것도 만들어내지 않는지, 취소가 착지했을 때 이미 배송 중이던 메시지가 전달되는 대신 버려지는지, 우아한 종료 결과가 구독 id를 실며 두 번 닫기는 아무 일도 하지 않는지, 그리고 동시에 열린 두 구독이 id로 올바르게 디멀티플렉싱되는지입니다. 저장소의 와이어 검사기도 이 레슨의 트랜스크립트를 2026-07-28 규칙에 대해 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/16-notifications-and-subscriptions
```

## 캡스톤 연계

캡스톤의 장기 실행 단계에는 정확히 이 어휘가 필요합니다. 구독이 아닌 progress를 실은 호출은, `taskId`가 없다는 점으로 뒤 레슨의 tasks 확장과 구분되고, listen 스트림의 알림은 추측이 아니라 구독 id로 라우팅해야 합니다. 캡스톤 시나리오가 도중에 무언가를 취소할 때는, 와이어 위에 어떤 메시지가 나타날지(나타난다면)를 결정하는 것이 이 레슨의 트랜스포트 분할입니다. HTTP에서의 SSE 스트림 닫기와 stdio에서의 `notifications/cancelled` 알림, 그 둘의 차이죠.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 알림(Notification) | id가 없어 결코 답하지 않는 JSON-RPC 메시지 |
| `subscriptions/listen` | 오래 사는 알림 스트림을 여는 요청 |
| 구독 id | listen 요청 자신의 id. 그 스트림이 실는 모든 메시지가 이를 에코한다 |
| 스트림 알림 | `list_changed` 또는 `resources/updated`. listen 스트림 위에서만 전달된다 |
| 요청 범위 알림 | `progress` 또는 `message`. 자신이 묘사하는 요청의 응답 채널 위에서만 전달된다 |
| `progressToken` | 클라이언트가 고른 값으로, 활성 요청들 사이에서 유일하며 진행 업데이트를 한 호출에 묶는다 |
| 우아한 종료 | 깔끔한 끝을 알리는 원래 listen 요청 위의 `complete` 결과. 갑작스러운 트랜스포트 단절과 다르다 |
| `notifications/cancelled` | stdio 취소 메시지. 서버가 이것을 쓸 수 있는 유일한 목적은 listen 스트림 철거다 |

## 더 읽을거리

- [MCP 메시지 패턴](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns), 요청, MRTR, 구독-알림의 개요
- [Subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)
- [Progress](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/progress)
- [Cancellation](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 8절
- `phases/13-tools-and-protocols/29-mcp-reliability-cancellation-and-flow-control`, 같은 메시지들을 둘러싼 타임아웃과 흐름 제어를 더 깊게 다루는 단계
