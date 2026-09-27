> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 도구 호출 수명 주기

> 도구 호출은 단일 이벤트가 아닙니다. 정해진 순서의 체크포인트 나열이고, 호출이 정확히 어디서 멈췄는지가 두 오류 채널 중 어느 쪽이 적용되는지, 호출자가 다음에 무엇을 해야 하는지를 말해줍니다.

**유형:** 참고 자료
**사용 언어:** Python
**선수 지식:** 레슨 16
**소요 시간:** 약 45분

## 학습 목표

- 도구 호출이 모든 체크포인트를 지나가는 과정을 짚어봅니다. discover, list, select, confirm, call, validate, execute, result
- 어느 체크포인트가 호스트 애플리케이션 안에만 존재하는지, 어느 것이 실제로 와이어 위에 메시지를 올리는지 구분합니다
- 모르는 도구가 왜 언제나 프로토콜 오류인지, 잘못된 인자는 왜 그 대신 거의 언제나 도구 실행 오류인지 설명합니다
- input_required 결과와 끊어진 스트림 둘 다에 재시도 규칙을 적용합니다. 매번 새로운 JSON-RPC id, 이미 실패한 id는 절대 다시 쓰지 않습니다
- 무턱대고 재발행이 안전한지 판단할 때 idempotentHint를 보장이 아니라 신뢰할 수 없는 힌트로 다룹니다
- 클라이언트가 포기하게 만드는 하드 타임아웃과 호출을 잠시 멈춰둘 뿐인 input_required 결과를 구분합니다

## 문제 상황

에이전트가 서버에게 빌드 상태 폴링, 릴리스 배포, 무언가 검색을 부탁하는 장면을 상상해 보세요. 쉬운 이야기에서 도구 호출은 단일 이벤트입니다. 보내면, 답을 받고, 끝. 실제 호출은 그렇게 작동하지 않습니다. 모델이 도구 쓰기를 결정하는 순간부터 호출자가 최종적으로 행동할 무언가를 손에 넣는 순간까지, 요청은 여러 뚜렷이 다른 체크포인트를 통과하고, 각각은 이야기를 서로 다르게 끝낼 수 있습니다. 모든 실패를 똑같이 다루는 호출자는 계속 잘못된 결정을 내립니다. 몇 번을 보내도 결코 성공하지 못할 호출을 재시도하거나, 인자만 고치면 될 것을 포기하거나, 더 나쁘게는 첫 시도가 이미 처리되었을지도 모르는 부수 효과 있는 호출을 무턱대고 반복합니다.

해법은 호출자의 기지가 아닙니다. 모든 도구 호출이 따르는 고정된 모양을 아는 것입니다. 그래야 "어디서 멈췄나"가 "지금 뭘 해야 하나"에 답해줍니다. 도구의 존재 여부를 확인하는 것도 못 넘긴 호출은, 도구의 핸들러를 돌렸다가 비즈니스 규칙에 부딪힌 호출과 실패 이유가 다르고 필요한 응답도 다릅니다. 이것이 바로 시험의 Interactions and Execution 도메인, 즉 블루프린트에서 가장 큰 단일 도메인이 몇 번이고 반복해서 묻는 구분입니다. 프로토콜 오류인가 도구 실행 오류인가, 그리고 어느 체크포인트에서인가.

## 핵심 개념

2026-07-28 개정판의 도구 호출은 고정된 순서의 여덟 체크포인트를 지나갑니다. discover, list, select, confirm, call, validate, execute, result입니다. 이 중 일부만 와이어 위에 메시지를 올립니다. 나머지 절반은 전적으로 호스트 애플리케이션 안에 살며, JSON-RPC 트래픽만 지켜보는 클라이언트가 결코 직접 볼 수 없지만, 여전히 모델이 허용되는 행동의 모양을 만듭니다.

**Discover와 list**는 와이어 체크포인트이며 둘 다 캐시 가능합니다. `server/discover`를 호출하는 클라이언트는 서버의 지원 버전, 캐퍼빌리티, 선택적인 `instructions`를 알게 되고, 모두 `ttlMs`와 `cacheScope`를 실고 있습니다. 클라이언트 입장에서 이를 호출하는 것은 선택사항이지만, 서버는 구현해야 합니다. `tools/list`는 각 도구의 이름, 설명, `inputSchema`, 어노테이션을 돌려주고, 이것 역시 캐시 가능하며 커넥션별로 달라져서는 안 됩니다(요청에 실린 인가에 따라서는 달라질 수 있습니다). 잘 만들어진 클라이언트는 매 호출 전에 다시 묻는 대신 캐시된 목록을 씁니다. 그래서 "list"와 "call"이 하나가 아니라 별개 체크포인트인 겁니다.

**Select와 confirm**은 와이어에 전혀 닿지 않습니다. Select는 모델이 자기 컨텍스트에 이미 있는 설명과 스키마를 근거로 어떤 도구를 호출할지 고르는 것이고, Confirm은 호스트가 그 선택을 곧장 실행할지 먼저 사람에게 물을지 결정하는 것입니다. 명세가 SHOULD로 규정하는 것이지 프로토콜 메시지가 아닙니다. 애플리케이션은 어떤 도구가 노출되는지 분명히 하고, 호출 전에 입력을 보여주고, 민감한 작업은 확인 뒤에 막아두어야 합니다. `destructiveHint` 같은 어노테이션이 그 관문에 정보를 주지만, 이것들은 힌트일 뿐, 서버 자체가 신뢰되지 않는 한 신뢰할 수 없고, 결코 강제되는 보장이 아닙니다. 사람이 거부하면 수명 주기는 그저 여기서 끝납니다. `tools/call`이 끝까지 보내지지 않으므로 validate나 execute가 할 일은 없습니다.

**Call**은 `tools/call` 요청이 실제로 나가는 순간입니다. 이 개정판의 모든 요청처럼 이전 핸드셰이크에 기대지 않고 자기만의 메타데이터를 실습니다:

```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "method": "tools/call",
  "params": {
    "name": "get_build_status",
    "arguments": {"build_id": "bld_7"},
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "progressToken": "pt-9"
    }
  }
}
```

**Validate**는 그 요청이 도착한 뒤 서버가 수행하는 첫 체크포인트이며, 정확히 한 가지 질문을 던집니다. 이 도구는 서버가 실제로 노출하는 것인가? 인자에 대해서는 아직 아무것도 중요하지 않습니다. 이름이 서버 목록의 어떤 것과도 맞지 않으면 호출은 바로 여기서 프로토콜 오류로 끝나며, 언제나 `-32602`이지 결코 `-32601`이 아닙니다. JSON-RPC 메서드(`tools/call` 자신)는 완벽하게 잘 알려져 있었고, 그 안의 도구 이름만 모르는 것이었으니까요:

```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "error": {"code": -32602, "message": "Unknown tool: delete_all_builds"}
}
```

validate에 실패한 호출은 execute에 절대 도달하지 않고, `result`를 아예 만들어내지 못하며 `error`만 남깁니다. 이것은 곱씹을 가치가 있습니다. 전체 오류 분류학은 뒤 레슨에 속하지만, validate 대 execute의 분할이야말로 도구 오류에 관한 거의 모든 시험 문제가 실제로 묻는 구분입니다.

**Execute**는 validate가 도구의 존재를 확인한 뒤에야 시작되며, 거기서부터의 전부를 커버합니다. 공급된 인자를 도구 자신의 `inputSchema`로 검사하고, 그다음 실제로 핸들러를 돌리는 것까지요. 빠졌거나 잘못된 형태의 인자는 validate가 아니라 여기서 잡히고, 모델이 읽고 행동에 옮길 수 있는 콘텐츠를 실은 정상적인 complete 결과, 즉 `isError: true`로 돌아옵니다:

```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "result": {
    "resultType": "complete",
    "content": [{"type": "text", "text": "Missing required argument(s): environment."}],
    "isError": true
  }
}
```

가장 자주 시험되는 규칙이 이것입니다. 모르는 도구는 validate에서의 프로토콜 오류이지만, 스키마 위반, 업스트림 API 실패, 비즈니스 규칙 위반은 모두 execute 도중에 만들어지는 도구 실행 오류입니다. 모델은 후자를 스스로 고칠 수 있지만 전자로는 쓸모 있는 일을 아무것도 못 하기 때문입니다. 알아둘 만한 예외가 하나 있습니다. execute가 입력이나 비즈니스 문제가 아니라 진짜 예상치 못한 서버 고장에 부딪혔다면, 그것은 여전히 프로토콜 오류, `-32603`으로 보고됩니다. 호출자의 다음 시도가 고칠 수 있는 것이 아니기 때문입니다. 요청이 `progressToken`을 선언했다면, execute는 `notifications/progress`가 흐를 수 있는 자리이기도 합니다. 각각은 같은 토큰과 엄격히 증가하는 `progress` 값, 선택적인 `total`과 `message` 필드를 실으며, 그 요청의 응답 스트림 위에서만 흐르고 그 밖의 어디에도 흐르지 않습니다.

**Result**는 execute가 착지하는 곳입니다. `resultType`은 `"complete"`(`isError` 설정 여부와 무관)이거나 `"input_required"`인데, 이 수명 주기가 돌려줄 수 있는 값은 이 둘뿐입니다. `input_required`는 끝이 아닙니다. `inputRequests`, `requestState`, 혹은 둘 다를 실으며, 클라이언트는 완전히 새로운 JSON-RPC id로 같은 논리적 호출을 재시도하고, `inputResponses`는 맞게 키가 매겨지고, `requestState`는 주어진 대로 정확히 에코하면서 답합니다(앞선 레슨들의 멀티 라운드 트립 패턴입니다. HMAC 같은 것으로 그 상태를 보호하는 것은 엘리시테이션 레슨이 깊게 다루고, 여기서는 수명 주기가 초점으로 남도록 일부러 단순하게 둡니다). 그 재시도는 call, validate, execute, result를 전부 다시 돌기 때문에, **retry**와 **final**이 루프 옆에 서 있는 게 아니라 루프를 닫습니다. retry는 이력을 가진 call일 뿐이고, final은 실제로 붙어 남는 결과, 즉 `complete`이거나 호출자가 포기하는 지점이니까요.

포기에도 저만의 모양이 있습니다. 서버는 모든 요청에 타임아웃을 두어야 합니다. 진행 알림이 계속 도착하는 동안에도 적용되는 하드 최대치를요. 진행이 일이 벌어지고 있다는 증거이지 제때 끝난다는 증거는 아니기 때문입니다. 취소는 트랜스포트에 따라 다릅니다. Streamable HTTP에서는 요청의 스트림을 닫는 것이 취소이고 메시지는 필요 없습니다. stdio에서는 클라이언트가 `requestId`와(선택적으로) 이유를 밝힌 `notifications/cancelled`를 보냅니다. 타임아웃도 취소도 그 자체의 resultType을 만들어내는 일은 결코 없습니다. `"cancelled"`나 `"timed_out"` 같은 값은 없습니다. 서버는 그저 호출자가 여전히 신경 쓰는 결과를 보낼 기회를 영원히 얻지 못하고, 이미 요청을 포기한 클라이언트는 그 뒤에 도착하는 어떤 응답도 무시해야 합니다.

끊어진 스트림은 관련 있지만 별개인 실패입니다. 요청은 보내졌는데 성공이든 오류이든 어떤 응답도 도착하기 전에 커넥션이 죽은 것입니다. 이 개정판에는 재개 가능성에 관한 것이 하나도 남아 있지 않습니다(`Last-Event-ID`도, SSE 재생도 없음). 그래서 호출자의 유일한 선택지는 새 id로 호출을 재발행하는 것입니다. 무턱대고 하는 것이 안전한지는 `idempotentHint`에 달려 있는데, 그 어노테이션은 어디까지나 힌트이므로 신중한 클라이언트는 비멱등 도구를 다르게 다룹니다. 부수 효과 있는 호출을 맹신으로 반복하는 대신, 잘 설계된 서버는 첫 단계에서 명시적이고 불투명한 핸들을 돌려주고(상태 없는 코어 레슨의 패턴), 끊어진 스트림 뒤의 재발행을 포함한 이후 체크포인트들이 이미 일어났을지도 모르는 동작을 조용히 반복하는 대신 그 핸들로 작동하게 합니다.

```figure
mcpa-17-lifecycle
```

## 인터랙티브 랩

그림은 여덟 체크포인트를 위에서 아래로 사슬처럼 깔고, 두 오류 분기가 일어나는 자리에서 정확히 떨어져 나갑니다. validate는 `-32602`로 갈라지고(프로토콜 오류, execute 없음, result 없음), execute는 `isError`로 갈라집니다(도구 실행 오류, 그래도 complete 결과). Result 자체는 두 번 갈라집니다. complete는 이야기를 끝내고, input_required는 새 id를 실어 call 위로 거슬러 올라갑니다. 다이어그램 전체에서 유일한 뒤로 가는 모서리죠. select와 confirm은 사슬 안에 있지만 어느 오류 분기에도 나타나지 않는다는 점에 주목하세요. 둘은 애초에 JSON-RPC 메시지를 만들어내지 않으므로 프로토콜 오류나 도구 실행 오류로 실패할 수 없습니다. confirm에서의 거부는 그저 call 이전에 이야기를 끝낼 뿐입니다.

## 실습 랩

레슨 디렉터리에서 모듈을 실행하세요:

```bash
python3 code/main.py
```

출력되는 각 줄은 한 시나리오의 단계 추적과 그것이 어떻게 끝났는지입니다. 출력의 모든 화살표를 그림과 대조해 보세요. `happy_path`는 진행 상황을 가운데 두고 전체 사슬을 한 번 돌리고, `needs_input_then_retry`는 call, validate, execute, result를 두 번째로 도는 루프를 보여주며, `confirmation_denied`는 confirm 뒤에서 call 없이 멈추고, `unknown_tool`은 validate 뒤에서 멈추고, `invalid_arguments`는 execute에 도달해 isError로 돌아오고, `broken_stream_reissue`는 같은 빌드 핸들에 대해 서로 다른 id 두 개로 두 번 호출하고, `timeout_then_cancel`은 완료에 도달하지 못하는 진행 상황 뒤에 포기한 뒤 늦게 도착한 응답을 무시하며, `internal_fault`는 execute에서 표면화된 예상치 못한 서버 오류가 isError가 아니라 프로토콜 오류로 나타나는 모습을 보여줍니다.

그다음 이 디렉터리에서 셸을 열고 한 시나리오를 손으로 밟아 가 보세요:

```python
import sys; sys.path.insert(0, "code")
import main
server, client = main.LifecycleServer(), None
client = main.Client(server)
run = main.run_needs_input_then_retry(server, client)
print(run.stages)
print(run.final)
```

`main.py`에서 `publish_release`의 필수 인자를 바꾸거나, `run_timeout_then_cancel`의 폴링 예산이 허용하는 것보다 많은 틱을 가진 빌드를 심어두고 다시 실행하면 단계 추적이 모양을 바꾸는 모습을 볼 수 있습니다.

## 제공되는 산출물

`outputs/tool-lifecycle-state-chart.md`는 한 페이지 상태 차트입니다. 모든 체크포인트, 와이어에 보이는지 호스트 전용인지, 어떤 오류 채널로 끝날 수 있는지, 그리고 호출이 멈추거나 깨질 수 있는 각 방식마다의 정확한 재시도 규칙이 담겨 있습니다. 클라이언트나 서버 구현 옆에 두고 "여기서 무슨 일이 일어나야 하지"의 참고 자료로 쓰세요.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검사합니다. happy path의 단계들이 문서화된 순서로 일어나는지, input_required 결과 뒤에 새 id로 완료되는 재시도가 이어지는지, 확인 거부가 call 이전에 멈추는지, 모르는 도구가 validate에서 `-32602`로 실패하는지, 스키마 위반이 execute에서 isError로 착지하는지, 끊어진 스트림이 같은 핸들을 향해 새 id로 재발행되는지, 하드 타임아웃이 요청을 취소하고 그 뒤의 늦은 응답이 무시되는지, execute에서의 예상치 못한 서버 고장이 isError가 아니라 여전히 프로토콜 오류인지, `tools/list`가 결정론적 순서를 유지하는지, 그리고 모든 요청과 결과가 이 개정판이 요구하는 필드들을 실고 있는지입니다. 저장소의 와이어 검사기는 이 레슨의 트랜스크립트를 같은 규칙에 대해 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/17-tool-invocation-lifecycle
```

## 캡스톤 연계

캡스톤의 엔드투엔드 교환은 이 수명 주기를 실제로 돌려본 것입니다. 앞에서 discover와 list, 스키마 검증이 필요한 인자의 호출, 새 id로 답하는 input_required 일시 정지, 진행 상황과 있을 수 있는 취소, 그리고 감사 추적이 다시 가리킬 수 있는 최종 결과가 있습니다. 캡스톤이 어떤 설계가 재시도했거나 포기했거나 그렇게 오류를 보고한 이유를 정당화하라고 하면, 답은 언제나 "이게 어느 체크포인트였나"입니다. 이 레슨이 자동으로 만들어주는 바로 그 질문이죠.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 체크포인트 | 도구 호출이 지나가는 여덟 고정 지점 중 하나. discover부터 result까지 |
| Validate | 이름 붙은 도구가 존재하는지만 묻는 체크포인트. 여기서의 실패는 언제나 프로토콜 오류다 |
| Execute | 인자를 검사하고 핸들러를 돌리는 체크포인트. 여기서의 실패는 거의 언제나 도구 실행 오류다 |
| 프로토콜 오류 | JSON-RPC `error`. 모델이 재시도에 활용할 수 있는 콘텐츠가 결코 아니다 |
| 도구 실행 오류 | `isError: true`인 complete 결과. 모델이 읽고 고칠 수 있는 콘텐츠다 |
| Retry | MRTR 연속 동작. 새 JSON-RPC id, 맞게 키가 매겨진 `inputResponses`, 정확히 에코된 `requestState` |
| Reissue | 끊어진 스트림 뒤에 새 id로 호출을 다시 보내는 것. 이 트랜스포트에서는 재개 가능한 것이 아무것도 없다 |
| idempotentHint | 호출을 반복해도 안전한지에 대한 신뢰할 수 없는 힌트. 강제된 보장이 아니다 |

## 더 읽을거리

- [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools), 특히 Error Handling과 Stateful Tools
- [멀티 라운드 트립 요청](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [Cancellation](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation)과 [Progress](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/progress)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 5, 7, 8절
- `phases/13-tools-and-protocols/29-mcp-reliability-cancellation-and-flow-control`, 타임아웃, 취소, 흐름 제어를 깊게 다루는 단계
