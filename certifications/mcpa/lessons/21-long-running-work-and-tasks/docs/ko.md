> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 오래 걸리는 작업과 태스크 익스텐션

> 몇 분, 몇 시간짜리 작업이 끝날 때까지 연결을 붙잡아 두면, 스테이트리스함이 사들여 준 모든 것이 물거품이 됩니다. 어떤 복제본(replica)도 더 이상 답할 수 없고, 끊어진 연결은 작업 자체를 잃어버립니다. 태스크 익스텐션은 그 막는 호출(blocking call)을 대신 견고한 핸들(durable handle)로 바꿔치기합니다.

**유형:** 참조(Reference)
**언어:** Python
**선수 지식:** 레슨 20
**시간:** 약 45분

## 학습 목표

- 오래 걸리는 작업에 대해 요청을 막아 두는 방식이 실패하는 이유를 설명합니다. 요청과 전송 계층의 타임아웃, 실행 도중 입력을 받을 채널의 부재, 충돌 이후 복구 불가
- 요청별로 `io.modelcontextprotocol/tasks` 익스텐션을 협상합니다. `clientCapabilities.extensions`에 선언하고 `server/discover`로 확인
- 서버 주도의 `CreateTaskResult`(`resultType: "task"`)를 읽고 `tasks/get`으로 폴링하며, RPC 자체의 `resultType`과 태스크의 중첩된 `status`를 구별합니다
- 실행 도중 입력은 `tasks/update`로 공급하고 협조적 취소는 `tasks/cancel`로 요청하며, 둘 다 승인(acknowledgement)만 돌려주는 이유를 설명합니다
- 현재의 익스텐션과 제거된 2025-11-25 실험용 태스크 기능을 구별하고, `tasks/result`와 `tasks/list`를 무엇이 대체했는지 짚습니다
- 주어진 작업에 대해 평범한 호출, 다중 왕복 요청(MRTR), 태스크, 서버 발행 핸들 중에서 골라 봅니다

## 문제 상황

어떤 도구 호출은 요청 하나 안에서 끝나지 못합니다. CI 파이프라인, 일괄 가져오기, 중간에 사람의 승인이 필요한 보고서. 이런 작업은 몇 초, 몇 분, 그 이상이 걸리고, 그 시간 자체는 엔지니어링으로 없앨 결함이 아닙니다. 작업의 마지막 바이트가 끝날 때까지 연결을 붙잡고 있으면 세 가지 실패가 동시에 찾아옵니다.

첫째는 서버 마음대로 설정할 수 없는 타임아웃입니다. 모델과 서버 사이의 클라이언트, 프록시, 로드 밸런서는 각자 하나의 요청이 열려 있을 수 있는 시간에 자기만의 한도를 둡니다. 그 한도 대부분은 평범한 조회용으로 정해졌지, 20분씩 돌아가는 배포 파이프라인을 위해 정해진 것이 아닙니다. 둘째는 막혀 있는 요청에게는 서버가 클라이언트에게 무언가를 물을 채널이 남아 있지 않다는 점입니다. 진행 중에 사람의 승인이 필요해진 도구는 그 요청을 내놓을 곳이 없습니다. MRTR 왕복은 열려 있는 동안 그 요청에 관한 질문에 답할 뿐, 하나의 열린 연결을 몇 시간짜리 대화로 바꿔 주지는 않습니다. 셋째는 내구성(durability)입니다. 클라이언트 프로세스가 재시작하거나 연결이 그냥 끊기면, 막혀 있던 호출은 흔적도 없이 사라집니다. 클라이언트는 작업이 끝났는지 물어볼 수 없으므로, 영원히 기다리거나 이미 돌아가고 있고 이미 부수 효과(실제 배포 같은)를 낼 수도 있는 작업을 다시 제출할 수밖에 없습니다.

스테이트리스 코어는 이 문제를 오히려 더 날카롭게 만듭니다. 레슨 04에서 기댈 세션이 없는 이유를 다뤘습니다. 요청에 관한 어떤 것도 호출 사이에 기억되지 않으므로, 서버가 조용히 한 작업을 특정 연결에 붙여 두고 나중에 그 자리에서 이어가는 방법이 없습니다. 오래 걸리는 작업은, 스테이트리스함이 다른 모든 것에 대해 이미 답해 주는 바로 그 질문에 대한 명시적인 답이 필요합니다. 이 작업을 요청과 재시작과 복제본들 사이에서 무엇이 식별해 주는가. 그래서 그중 어느 것이든 다시 집어 들 수 있도록 말입니다.

## 개념

MCP는 공식 익스텐션인 `io.modelcontextprotocol/tasks`(SEP-2663)로 그 질문에 답합니다. 이를 지원하는 서버는 자격이 되는 요청에 최종 답변 대신 견고한 핸들, 즉 태스크(task)로 응답할 수 있고, 클라이언트는 그 핸들에 묶인 세 메서드로 폴링하고, 입력을 공급하고, 취소합니다.

협상은 요청별로 이루어지며, 이 프로토콜의 다른 모든 커패시티가 그렇듯이 동작합니다. 클라이언트는 지금 만들고 있는 요청의 `io.modelcontextprotocol/clientCapabilities.extensions`에 익스텐션을 선언하고, 서버는 `server/discover`의 `capabilities.extensions`에 같은 식별자를 광고합니다. 어떤 호출에 선언한 익스텐션이 다음 호출로 이어지지는 않습니다. 이를 기억해 둘 세션이 없으므로, 나중의 `tasks/get` 호출에서도 태스크를 이해하는 처리를 원하는 클라이언트는 그 호출에도 익스텐션을 다시 선언해야 합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "run_build_pipeline",
    "arguments": {"project": "web-storefront", "environment": "production"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {"io.modelcontextprotocol/tasks": {}}
      }
    }
  }
}
```

태스크 생성은 서버 주도입니다. 익스텐션을 선언했다는 것은 클라이언트가 어느 쪽 형태든 받을 준비가 됐다는 뜻일 뿐입니다. 이 특정 호출이 태스크가 될지는 요청별로 서버만이 결정합니다. 익스텐션을 선언한 클라이언트는 정확히 같은 도구에 대해 정상적인 `CallToolResult`를 받을 수도, `CreateTaskResult`를 받을 수도 있고, 때로는 호출마다 다릅니다. 이 개정판에서는 `tools/call`만 태스크 증강(augmentation)을 지원합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "resultType": "task",
    "taskId": "tsk_786512e29e0d",
    "status": "working",
    "statusMessage": "Installing dependencies and running tests.",
    "createdAt": "2026-09-24T10:30:00Z",
    "lastUpdatedAt": "2026-09-24T10:30:00Z",
    "ttlMs": 900000,
    "pollIntervalMs": 2000
  }
}
```

서버는 그 핸들에 대한 `tasks/get`이 이미 해결될 수 있는 상태가 되기 전에는 그 핸들을 보내서는 안 됩니다. 이벤추얼리 일관성 있는(eventually consistent) 저장소라면, 답하기 전에 쓰기가 보이게 될 때까지 기다린다는 뜻입니다. 이 단계를 건너뛰면 클라이언트는 즉시 not found를 보고하는 `taskId`를 받게 되는데, 이는 조금 더 막혀 있는 것보다 더 나쁩니다.

클라이언트는 `tasks/get`으로 폴링하며, 받은 `taskId`만 보냅니다. 여기에 시험이 좋아하는 디테일이 있습니다. `tasks/get` 자체는 완료되는 평범한 요청이므로, 그 자신의 `resultType`은 언제나 `"complete"`입니다. 밑에 있는 작업의 상태 — `working`, `input_required`, `completed`, `failed`, `cancelled` — 는 같은 결과 안의 별도 중첩 필드 `status`에 실려 오지, `resultType`에 실리지 않습니다. 이 둘을 헷갈리는 건 무해해 보이다가 클라이언트가 `resultType: "complete"`를 본 순간 폴링을 멈출 때 문제가 드러납니다. 작업이 아직 돌아가고 있든 말든 모든 폴링에서 그 값은 참이기 때문입니다.

`tasks/result`는 없습니다. 태스크가 `completed`에 이르면, 바로 다음 `tasks/get` 응답이 원래의 결과를 `result` 아래 인라인으로 실어 옵니다. 요청이 동기적으로 돌려줬을 결과와 정확히 같은 형태입니다. 태스크가 `failed`에 이르면, 같은 응답이 JSON-RPC 오류를 `error` 아래 실어 옵니다. `isError: true`로 끝난 도구 호출은 여전히 `completed`입니다. 호출 자체는 프로토콜 수준에서 성공했기 때문입니다. `failed`는 실행 도중의 JSON-RPC 오류만을 위한 것이고, 평범한 도구 수준 실패를 위한 것이 결코 아닙니다.

`tasks/list`도 없습니다. 2025-11-25 실험판에는 있었지만, 세션이 없는 서버에는 태스크를 나열할 안전한 범위가 없습니다. 목록을 묶어 둘 세션이나 연결이 없다면, 순진한 나열은 모든 호출자의 태스크를 다른 모든 호출자에게 누출하거나, 기본 프로토콜이 정의하지 않는 인가 모델을 발명해야 합니다. 태스크 이력이 필요한 제품은 자기만의, 인가된 필터링 도구를 대신 노출합니다. 범용 나열 호출은 기본적으로 불안전한 채로 출시되는 대신 제거됐습니다.

태스크는 생성 시점에는 필요하지 않았던 입력 때문에 실행 도중 멈출 수 있습니다. 그 상태가 `input_required`가 되면, 같은 `tasks/get` 응답이 `inputRequests` 맵을 하나 얻습니다. 각 항목은 MRTR 요청 하나와 같은 형태입니다. `elicitation/create`, `sampling/createMessage`, `roots/list`. 클라이언트는 같은 방식으로 키가 매겨진 `inputResponses`를 `tasks/update`로 보내 답하고, 빈 승인(acknowledgement)만 돌려받습니다. 갱신된 상태는 그 응답에 나타나는 것이 아니라 다음 폴링에 나타납니다. 형태는 흡사해 보여도 이것은 코어 MRTR과는 다른 이어가기(continuation)입니다. MRTR은 원래 요청을 새 id로 재시도하지만, `tasks/update`는 `taskId`를 겨냥한 자기만의 메서드이고, 클라이언트는 원래의 `tools/call`을 다시 보내지 않습니다. 각 `inputRequests` 키는 태스크의 수명 내내 고유하게 유지되므로, 서버는 발행한 적 없거나 이미 충족한 키에 대한 응답을 무시하고, 클라이언트는 반복 폴링 사이에서 이미 사용자에게 보여 준 키를 중복 제거합니다.

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tasks/update",
  "params": {
    "taskId": "tsk_786512e29e0d",
    "inputResponses": {
      "approve_deploy": {"action": "accept", "content": {"approved": true}}
    },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {
        "extensions": {"io.modelcontextprotocol/tasks": {}}
      }
    }
  }
}
```

취소도 같은 방식입니다. `tasks/cancel`은 `taskId`만 보내고 빈 승인을 돌려받습니다. 이것은 협조적(cooperative)이며 보장이 아닙니다. 서버는 의도를 기록하지만 작업을 여전히 끝까지 마칠 수도 있는데, 중간에 멈추는 것이 안전하지 않거나 불가능할 수 있기 때문입니다. 여기서 `notifications/cancelled`에 손을 뻗지 마세요. 그 알림은 자기 전송 스트림 위의 아직 열려 있는 요청 하나를 해체하는 것이고, 태스크의 원래 요청은 `resultType: "task"`가 된 순간 이미 돌아왔습니다. 그런 방식으로 취소할 열린 요청이 더 이상 남아 있지 않습니다. 일단 태스크가 존재하기 시작하면, 견고한 작업으로 가는 유일한 길은 `tasks/cancel`뿐입니다.

그 특정 요청에서 익스텐션을 선언하지 않은 클라이언트가 태스크 메서드를 부르면 `-32021`을 받습니다(Missing Required Client Capability). 익스텐션이 `data.requiredCapabilities`에 이름을 올라 갑니다. 알 수 없거나 만료된 `taskId`는 `-32602`를 받는데, 레슨 18이 잘못된 형태의 요청에 대해 소개한 바로 그 코드입니다. `tasks/get`, `tasks/update`, `tasks/cancel`은 평범한 JSON-RPC 요청이고, 요청별 메타데이터를 포함해 이 프로토콜의 다른 모든 것과 똑같은 규칙의 대상이기 때문입니다.

네 패턴 사이의 선택은 결국 무엇이 현재 요청보다 오래 살아남아야 하는가로 귀결됩니다. 작업이 빠르고 결정적이라면 평범한 호출로 충분합니다. 서버가 이미 답하고 있는 요청을 끝내기 위해 딱 한 번의 짧은 답만 필요하다면 MRTR 왕복(레슨 14)으로 충분합니다. 작업이 타임아웃보다 오래 살아남을 수 있거나, 도중에 입력을 위해 멈출 수 있거나, 클라이언트 재시작이나 의도적 취소를 견뎌야 한다면 태스크가 그 복잡성 값을 합니다. 서버 발행 핸들(레슨 04의 패턴)은 전혀 다른 문제를 풉니다. 장바구니나 열린 세션 같은 호출을 넘나드는 애플리케이션 상태를 평범한 도구 인자로 전달합니다. `taskId`는 우연히도 같은 발상의 한 사례일 뿐이며, 상태를 무한히 열어 두는 것이 아니라 지연된 작업 한 단위를 폴링하기 위해 전용으로 만들어진 것입니다.

```figure
mcpa-21-task-states
```

## 인터랙티브 랩

이 그림은 태스크가 도달할 수 있는 모든 상태와 각 이동을 몰아가는 호출을 펼쳐 놓습니다. `working`에서 `input_required`로 가는 길을 따라가 보세요. 그 경계는 클라이언트가 보낸 요청이 아니라 서버가 결정한 것으로 이름이 붙습니다. 그다음 돌아오는 경계를 따라 내려가 보세요. 클라이언트가 실제로 보내는 유일한 요청, `tasks/update`로 이름이 붙어 있습니다. 오른쪽에서는 세 개의 최종 상태가 `working`에서 갈라져 나옵니다. 작업이 끝나서 완료, 클라이언트가 물어서 취소, 프로토콜 오류가 실행을 가로막아서 실패. 셋 모두 최종(terminal)임을 표시하려고 점선 테두리로 그려져 있습니다. 일단 태스크가 하나에 도달하면, `tasks/get`은 그 같은 스냅샷을 계속 돌려줍니다.

## 실습 랩

`code/main.py`를 열어 보세요. `run_build_pipeline`은 어느 쪽이든 같은 입력 스키마와 같은 작업을 가진 도구 하나입니다. 설치하고, 테스트하고, 승인되면 프로젝트를 환경에 배포합니다. 달라지는 것은 오직 호출자가 `io.modelcontextprotocol/tasks`를 선언했는지 여부뿐입니다.

```bash
python3 code/main.py
```

출력되는 교환을 위의 개념 절과 겨뎌 읽어 보세요. 익스텐션 없이 보낸 호출은 동기적으로 끝나며 승인을 위해서는 익스텐션이 필요하다고 보고합니다. 익스텐션과 함께 보낸 호출은 즉시 `resultType: "task"`를 돌려받습니다. 이 랩은 백그라운드 스레드에서 자는 대신, 폴링 사이에 태스크를 명시적으로 앞당깁니다. 실제 워커가 별개의 요청들 사이에서 나아가는 방식 그대로이므로, 전사 속 모든 상태 전이는 결정적이고 반복 가능합니다. 하나의 `taskId`를 첫 `working` 폴링에서부터 `input_required`를 거쳐, `{"approved": true}`를 공급하는 `tasks/update`를 지나, 마지막 `completed` 폴링까지 따라가 보세요. 그리고 거기의 중첩된 `result`를 익스텐션 없는 호출이 직접 돌려준 것과 비교해 보세요. 그다음 두 오류를 찾아 보세요. 한 번도 만들어진 적 없는 `taskId`에 대한 `tasks/get`은 `-32602`로 돌아오고, 같은 유효한 `taskId`라도 익스텐션 선언을 빠뜨린 클라이언트가 폴링하면 `-32021`로 돌아옵니다.

## 완성된 산출물

`outputs/long-running-work-patterns.md`는 의사결정 참조 자료입니다. 평범한 호출, MRTR 왕복, 태스크, 서버 발행 핸들 중 언제 무엇에 손을 뻗을지, 커패시티 협상 체크리스트, `CreateTaskResult` 필드들, 폴링과 상태 규칙(`tasks/get` 대 중첩 `status` 구분 포함), 그리고 2025-11-25 실험용 메서드들이 무엇으로 대체됐는지의 표를 담고 있습니다. 도구가 호출자의 인내심이나 전송 계층의 타임아웃이 닳기 전에 돌아오지 못할 수 있을 때, 서버의 도구 설명 옆에 두면 좋습니다.

## 확인해 보기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검증합니다. 익스텐션 없는 호출은 여전히 정상 결과를 돌려줌, 익스텐션 있는 호출은 태스크 핸들을 돌려줌, 폴링은 상태가 실제로 `working`에서 `input_required`로 나아가는 것을 보여 줌, `input_required` 스냅샷은 형태가 갖춰진 `inputRequests` 항목을 드러냄, `tasks/update`가 태스크를 재개함, `completed` 스냅샷은 원래 결과 형태를 인라인으로 실음, `tasks/cancel`은 working 중인 태스크를 `cancelled`로 옮김, 알 수 없는 `taskId`는 프로토콜 오류임, 그리고 선언된 커패시티 없이 같은 태스크 메서드를 부르면 대신 `-32021`이 됨. 저장소의 와이어 검사기도 레슨의 전사를 2026-07-28 규칙으로 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/21-long-running-work-and-tasks
```

## 캡스톤 연계

캡스톤의 감사(audit)를 거치는 도구 호출은 평범한 호출이 아니라 태스크가 될 만큼 오래 돌아가거나 충분한 도중 승인을 필요로 할 수 있습니다. 그렇게 될 때, 이 레슨의 같은 네 질문이 그대로 적용됩니다. 클라이언트가 이 요청에 익스텐션을 선언했는가, 서버가 이를 광고했는가, 핸들이 돌려지기 전에 견고한가, 모든 폴링이 래퍼 자신의 `resultType`과 작업의 중첩된 `status`를 구별하는가.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| `io.modelcontextprotocol/tasks` | 견고하고 서버 주도인 비동기 작업을 위한 공식 익스텐션 식별자 |
| `CreateTaskResult` | 서버가 정상 결과 대신 돌려줄 수 있는 `resultType: "task"` 응답 |
| `tasks/get` | `taskId`로 하나의 태스크에 대한 전체 최신 스냅샷을 폴링함 |
| `tasks/update` | 태스크의 처리 대기 중인 `inputRequests`에 `inputResponses`를 제출함 |
| `tasks/cancel` | 하나의 태스크에 대해 협조적 취소 의사를 전달함 |
| `input_required` | 서버가 계속하려면 클라이언트의 입력이 필요하다는 뜻의 태스크 상태 |
| `pollIntervalMs` | 서버가 지금 제안하는 폴링 사이 최소 지연 |
| `ttlMs` | 태스크 생성 시점부터 잰 만료 시간 |
| 반환 전 견고성(durable before return) | `taskId`가 클라이언트에 건네지기 전에 이미 해결 가능해야 한다는 규칙 |
| 협조적 취소 | `tasks/cancel`은 의도를 기록할 뿐, 서버가 작업을 멈출 의무는 없음 |

## 더 읽을거리

- [태스크, MCP 익스텐션](https://modelcontextprotocol.io/extensions/tasks/overview)
- [SEP-2663: 태스크 익스텐션](https://modelcontextprotocol.io/seps/2663-tasks-extension)
- [SEP-1686: 태스크 (2025-11-25 실험판, 역사 기록)](https://modelcontextprotocol.io/seps/1686-tasks)
- [스테이트풀 도구, MCP 명세 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/server/tools#stateful-tools)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 4절과 14절
- `phases/13-tools-and-protocols/13-mcp-async-tasks`. 재시작 복구와 공유 견고 저장소를 갖춘 태스크 기반 워커를 만들어 봅니다
