> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [notification-routing-table.md](notification-routing-table.md)

# 알림 라우팅 표

MCPA '상호작용과 실행' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## 두 개의 채널, 절대 섞이지 않음

| 채널 | 열리는 방법 | 모든 메시지에 붙는 태그 | 알림 메서드 |
|---|---|---|---|
| 리슨 스트림 | `subscriptions/listen`(하나의 요청) | `_meta["io.modelcontextprotocol/subscriptionId"]`, 리슨 요청 id와 동일 | `notifications/subscriptions/acknowledged`, `notifications/tools/list_changed`, `notifications/prompts/list_changed`, `notifications/resources/list_changed`, `notifications/resources/updated` |
| 요청 자신의 응답 | 어떤 평범한 요청이든 | 요청 간 공유되는 것 없음. `progress`는 `progressToken`을 실고, `message`는 그 요청 자신의 `logLevel`을 요구 | `notifications/progress`, `notifications/message` |

## 구독 열고 닫기

1. 클라이언트가 `notifications` 필터를 실어 `subscriptions/listen`을 보냅니다: `toolsListChanged`, `promptsListChanged`, `resourcesListChanged`(불리언)와 `resourceSubscriptions`(URI 목록).
2. 서버가 그 스트림에서 처음 보내는 답은 `notifications/subscriptions/acknowledged`이며, 허용된 필터의 부분집합과 구독 id(리슨 요청 자신의 id와 동일)를 그대로 돌려줍니다. 그 전에는 아무것도 보내지 않습니다.
3. 스트림 위의 이후 모든 메시지는 같은 구독 id를 반복합니다. 클라이언트가 하나의 채널을 공유하는 여러 열린 구독을 역다중화(demultiplex)하는 방법이 이것입니다.
4. 구독은 클라이언트의 취소(HTTP에서 SSE 스트림 닫기, stdio에서 `notifications/cancelled` 전송), 서버가 시작한 우아한 종료(원래 리슨 요청 위의 `complete` 결과, `_meta`에 구독 id), 또는 갑작스러운 전송 끊김(아무 메시지도 없음)으로 끝납니다.
5. stdio에서는 충돌이나 재시작 뒤의 재연결이 아무 기억도 갖지 않습니다. 클라이언트가 아직 원하는 모든 스트림을 다시 만들려면 새 id로 `subscriptions/listen`을 다시 보냅니다.

## 진행 상황(Progress)

- 클라이언트는 `_meta.progressToken`(문자열 또는 정수, 자신의 활성 요청들 사이에서 유일)으로 수신에 동의합니다.
- `progress`는 모든 알림에서 엄격하게 증가해야 합니다. `total`을 모르더라도 마찬가지입니다. `total`과 `message`는 선택입니다.
- 요청이 완료되면 알림도 멈춥니다. 양쪽 모두 채널을 범람시키기보다 속도 제한을 하는 것이 좋습니다.
- 진행 알림은 구독 id를 절대 실지 않고 리슨 스트림에 절대 나타나지 않습니다.

## 전송 방식별 취소

| 전송 방식 | 클라이언트가 취소하는 방법 | 서버가 보내는 것 |
|---|---|---|
| Streamable HTTP | 요청의 SSE 응답 스트림을 닫음 | 아무것도 없음. 닫힌 스트림 그 자체가 취소 신호 |
| stdio | `requestId`와 선택적 `reason`을 실어 `notifications/cancelled` 전송 | 평범한 요청에 대해선 아무것도 없음. `notifications/cancelled`는 서버가 종료하려는 리슨 스트림을 해체할 때만 |

## 경쟁 상태는 오류가 아니라 평범한 일

취소가 효력을 갖기 전에 만들어진 메시지는, 수신자가 이미 그 요청 추적을 멈춘 뒤에 도착할 수 있습니다. 어느 쪽도 이걸 실패로 취급하지 않습니다. 발신자는 취소할 것이 이미 없다는 걸 알게 될 수 있고, 수신자는 더 이상 인식하지 못하는 메시지를 어딘가로 보내는 대신 그냥 버립니다.

## 시험을 위해 기억하기

- 진행 알림과 폐기된 로깅 `message` 알림은 구독 id를 절대 실지 않습니다. 구독 알림은 언제나 실습니다.
- 서버가 `notifications/cancelled`를 시작할 수 있는 이유는 정확히 하나뿐입니다: 자신이 끝내려는 구독 스트림을 해체할 때. 그 외의 용도로는 절대 아닙니다.
- `resources/subscribe`와 `resources/unsubscribe`는 2026-07-28에 존재하지 않습니다. 리소스는 `subscriptions/listen`에 `resourceSubscriptions`를 써서 지켜봅니다.
- stdio 프로세스를 닫는 것 자체는 취소가 아닙니다. stdio에서 취소는 언제나 그 요청을 지목하는 명시적인 `notifications/cancelled` 메시지입니다.
- 우아한 종료 결과와 갑작스러운 전송 끊김은 서로 다른 신호입니다. 구독이 깨끗하게 끝났다고 클라이언트에게 말해 주는 건 전자뿐입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 8절.
