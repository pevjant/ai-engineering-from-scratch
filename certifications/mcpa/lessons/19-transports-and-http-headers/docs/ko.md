> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 전송 방식과 HTTP 헤더 계약

> 전송 방식(transport)은 메시지의 의미를 바꾸지 않고, 메시지가 어떻게 이동하는지만 바꿉니다. stdio는 JSON-RPC 한 줄을 자식 프로세스에 넘기고, Streamable HTTP는 한 번에 메시지 하나를 POST하면서 몇몇 필드를 게이트웨이가 본문을 건드리지 않고도 읽을 수 있는 헤더로 복제해 보여 줍니다.

**유형:** 참조(Reference)
**언어:** Python
**선수 지식:** 레슨 18
**시간:** 약 45분

## 학습 목표

- stdio 전송 방식이 요구하는 대로 줄바꿈으로 구분된 JSON-RPC 메시지를 감싸고(frame) 파싱하고, 중간에 끼어든 줄바꿈 하나가 그 구조를 깨뜨리는 이유를 설명합니다
- Streamable HTTP의 요청과 응답 형태를 묘사합니다: 메시지당 POST 하나, JSON 객체 또는 요청별 SSE 스트림, 받아들인 알림에 대한 `202 Accepted`, 그리고 GET 엔드포인트의 부재
- 필수 HTTP 헤더인 `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`을 만들고 검증하고, base64 센티널(sentinel) 인코딩으로 도구 인자 하나를 `x-mcp-header`를 통해 헤더에 복제합니다
- Origin 검증과 localhost 바인딩이 DNS 리바인딩(rebinding)을 막아 주는 이유와, 현대적 서버가 GET, DELETE, 허용되지 않은 Origin에 대해 무엇을 돌려주는지 설명합니다
- `HeaderMismatch`(`-32020`) 프로토콜 오류와, JSON-RPC 메시지로는 결코 변하지 않는 결과에 전송 계층이 돌려주는 평범한 HTTP 상태 코드를 구별합니다

## 문제 상황

MCP 메시지는 이미 이해에 필요한 모든 것을 품고 있습니다. 메서드, 파라미터, 그리고 `_meta`에 담긴 요청별 메타데이터가 그것입니다. 이 콘텐츠는 클라이언트와 서버 사이에서 바이트가 어떻게 이동하는지와는 무관합니다. 그런데도 그 바이트를 실어 나를 주체가 필요합니다. 메시지 하나와 다음 메시지의 경계를 그어 주고, 연결이 죽었을 때 클라이언트에게 알려 주고, 로드 밸런서나 게이트웨이가 스스로 JSON-RPC 파서로 변신하지 않고도 트래픽을 라우팅하게 해 줘야 합니다. 그것이 전송 방식의 역할이고, MCP 2026-07-28은 정확히 두 가지 표준 전송 방식을 정의합니다. 클라이언트가 띄운 자식 프로세스를 위한 stdio와, 불특정 다수의 클라이언트가 닿을 수 있는 네트워크 서비스를 위한 Streamable HTTP입니다.

전송 방식을 나중에 생각나서 붙이는 부가물로 가르치는 커리큘럼은, 시험이 노리는 바로 그 빈틈을 남깁니다. 레슨 04의 스테이트리스(stateless) 코어는 그 밑바닥의 바인딩이 자기만의 상태를 몰래 끼워 넣지 않는 한 — 세션 id, 재개 가능한 스트림, 연결에서 마지막 요청을 기억하는 서버 같은 것 — 끝까지 제대로 동작합니다. 이 레슨의 모든 규칙은 그 약속을 지키기 위해 존재합니다. 전송 방식은 메시지를 감싸고 전달할 뿐, 그 이상도 이하도 아닙니다.

## 개념

### stdio: 세 스트림을 공유하는 자식 프로세스

stdio 바인딩에서 클라이언트는 서버를 자식 프로세스로 띄우고, 양쪽은 그 프로세스의 표준 스트림을 공유합니다. 서버는 `stdin`에서 JSON-RPC 요청과 알림을 읽고, `stdout`에 응답과 알림을 씁니다. 한 줄에 메시지 하나, 중간에 끼어든 줄바꿈은 없습니다. `stdout`에는 유효한 MCP 메시지만 실립니다. 서버가 거기에 JSON-RPC 요청을 쓰는 일은 없습니다. MRTR(레슨 14)가 서버가 먼저 시작하는 모든 요청을 `input_required` 결과로 대체했기 때문입니다. `stderr`는 심각도를 불문한 로그를 위해 자유롭게 쓸 수 있고, 클라이언트는 거기 나타나는 무엇이든 오류라고 단정해선 안 됩니다.

stdio에는 헤더 계층이 없습니다. Streamable HTTP가 헤더로 복제해 보여 주는 모든 메타데이터는 이곳에도 존재하지만, 다른 전송 방식에서와 마찬가지로 오직 `params._meta` 안에 인라인으로만 나타납니다. 진행 중인 요청을 취소하려면 클라이언트가 요청의 id를 밝히는 `notifications/cancelled`를 보냅니다. 그냥 닫아 버릴 요청별 스트림이 없기 때문입니다. 종료는 협조적으로 이루어집니다. 클라이언트가 `stdin`을 닫고 기다린 뒤, 서버가 끝나지 않으면 프로세스 시그널로 격상시킵니다. 서버가 뜻밖에 종료되면 클라이언트는 그것을 다시 띄우고, 진행 중이던 요청을 잃으며, 여전히 원하는 구독에 대해 `subscriptions/listen`을 다시 보냅니다. 프로토콜이 스테이트리스이므로 새로 뜬 프로세스는 죽은 프로세스와 똑같이 유능합니다.

### Streamable HTTP: 하나의 엔드포인트, POST당 메시지 하나

Streamable HTTP 서버는 하나의 MCP 엔드포인트(예: `/mcp`)를 노출하며, 프로토콜 수준에서는 POST만 받고 그 외에는 아무것도 받지 않습니다. 모든 JSON-RPC 요청과 알림은 각자 자기만의 POST가 됩니다. 클라이언트의 `Accept` 헤더는 `application/json`과 `text/event-stream` 둘 다 나열합니다. 서버가 어떤 요청에 JSON 객체 하나로 답할 수도, 그 요청 하나에만 묶인 SSE 스트림으로 답할 수도 있고, 그 스트림은 최종 응답 전에 진행 상황이나 로그 알림을 실어 보낼 수 있기 때문입니다. 서버가 받아들인 알림 POST는 본문 없이 `202 Accepted`를 돌려받습니다. 알림에는 원래 JSON-RPC 응답이 없으므로 답할 것도 없습니다.

이 개정판에는 GET 엔드포인트도, 세션도, 재개 가능성(resumability)도 없습니다. 현대적 서버는 MCP 엔드포인트로 온 GET이나 DELETE에 `405 Method Not Allowed`로 답합니다. 세션 헤더를 만들어 내거나 읽어 보는 일도 없고, 깨진 SSE 스트림에 클라이언트가 재생(replay) id를 들고 다시 접속할 수도 없습니다. 그 요청은 그냥 잃어버리며, 재시도가 안전하다면 새 JSON-RPC id를 붙여 다시 보낼 뿐입니다. 서버가 오래 살아 있는 스트림을 열 때는 `X-Accel-Buffering: no`를 보내 리버스 프록시가 이벤트를 버퍼링하지 않게 하고, 조용한 기간에도 유휴 타임아웃이 연결을 끊지 않도록 가끔 SSE 주석 줄을 킵얼라이브로 흘려 보내는 것이 기대됩니다.

Origin 검증이 존재하는 이유는 하나입니다. `127.0.0.1`에 묶인 MCP 서버도 서버가 누가 물어보는지 확인하지 않으면 DNS 리바인딩을 통해 악성 웹페이지로부터 닿을 수 있기 때문입니다. `Origin` 헤더가 있고 서버가 허용하는 목록에 없다면 `403 Forbidden`으로 답합니다. 브라우저가 아닌 HTTP 클라이언트처럼 `Origin`이 아예 없는 클라이언트는 그 자체로 수상한 것이 아닙니다. 이 모든 것은 인증이 아닙니다. 서버는 Origin 검증 위에 자기만의 베어러 토큰 검사를 여전히 갖춰야 합니다.

### 헤더 거울과 그 계약

Streamable HTTP는 본문의 몇몇 필드를 헤더로 복제해 보여 줍니다. 게이트웨이나 로드 밸런서가 JSON을 파싱하지 않고도 MCP 트래픽을 라우팅할 수 있게 하기 위해서입니다. 모든 POST는 `MCP-Protocol-Version`을 실으며, 이 값은 `params._meta["io.modelcontextprotocol/protocolVersion"]`과 같아야 합니다. 모든 요청은 JSON-RPC `method`와 같은 `Mcp-Method`를 실립니다. `tools/call`, `resources/read`, `prompts/get` 요청은 또한 `Mcp-Name`을 실립니다. 이는 `params.name`과 같거나, 리소스 읽기라면 `params.uri`와 같습니다. 이 헤더들 중 하나라도 본문과 어긋나거나 빠져 있는 것을 발견한 서버는 HTTP `400`과 코드 `-32020`(`HeaderMismatch`)인 JSON-RPC 오류로 요청을 거절합니다. 이건 권고가 아닙니다. 서로 다른 네트워크 구성 요소는 어느 쪽이 진짜 값인지 의견이 갈릴 수 있습니다. 헤더를 보고 라우팅하는 게이트웨이, 본문을 실행하는 서버. 그 틈이야말로 공격자가 열려고 시도할 지점입니다.

도구는 한 걸음 더 나아가, 자기 인자 중 하나를 헤더로 복제해 달라고 클라이언트에게 부탁할 수 있습니다. 그 속성의 스키마에 `x-mcp-header`를 사용합니다. `"x-mcp-header": "Region"` 표시가 붙은 파라미터는 헤더 `Mcp-Param-Region`이 되며, 본문의 `arguments.region`이 담은 것과 같은 값을 실립니다. 헤더 값은 보이는 ASCII여야 하므로, 그렇지 않은 값 — 비 ASCII 문자, 제어 문자, 앞뒤 공백, 아니면 우연히도 센티널처럼 보이는 값 — 은 회선에 오르기 전에 `=?base64?{value}?=`로 base64 인코딩되고, 서버는 본문과 비교하기 전에 그 센티널을 디코딩합니다. 헤더 이름은 대소문자를 구분하지 않고, 헤더 값 — 메서드 이름과 도구 이름 포함 — 은 대소문자를 구분합니다. 복제에는 나름의 한계도 있습니다. 정수, 문자열, 불리언 파라미터 중 스키마 루트에서 정적으로 도달 가능한 것에만 적용되며, `number`에는 절대 적용되지 않습니다. Streamable HTTP의 클라이언트는 `x-mcp-header` 값이 이 제약을 깨는 도구를 호출하는 대신 자기 `tools/list` 결과에서 제외해야 합니다. 그리고 서버 개발자는 API 키나 토큰 같은 민감한 파라미터에 표시를 달아서는 안 됩니다. 헤더 값은 그 길목의 모든 프록시, 로드 밸런서, 로그에 그대로 드러나기 때문입니다.

신뢰할 수 있는 바이트 스트림 위에서 돌아가는 커스텀 전송 방식은 새 구조를 발명하기보다 stdio 프레이밍을 재사용합니다. stdio는 이미 스트림 위의 줄바꿈 구분 JSON-RPC이기 때문입니다. 2024-11-05의 오래된 HTTP+SSE 전송 방식은 Deprecated입니다. 새 서버는 이를 채택하지 말아야 하고, 기존 서버는 Streamable HTTP로 이전해야 합니다.

```http
POST /mcp HTTP/1.1
Content-Type: application/json
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: run_report
Mcp-Param-Region: us-west1

{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "run_report", "arguments": {"region": "us-west1", "dataset": "signups"}, "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}}
```

```json
{"jsonrpc": "2.0", "id": 7, "error": {"code": -32020, "message": "Header mismatch: Mcp-Method", "data": {"headers": ["Mcp-Method"]}}}
```

```figure
mcpa-19-transports
```

## 인터랙티브 랩

이 그림은 stdio와 Streamable HTTP를 나란히 놓습니다. 왼쪽에서는 클라이언트와 서버가 `stdin`, `stdout`, 그리고 점선의 `stderr` 위에서 줄을 주고받으며, 헤더 계층은 전혀 없습니다. 모든 필드는 `_meta` 안에 삽니다. 오른쪽에서는 클라이언트가 하나의 엔드포인트로 POST하고 서버가 응답을 돌려보냅니다. 화살표에는 작은 체크포인트가 실려 있는데, 서버가 여기서 복제된 헤더를 본문과 겨뎨 보고, 불일치가 나면 도구에 닿기 전에 `400`과 `-32020`으로 변합니다. 하나의 호출을 두 경로로 각각 따라가 보세요. JSON-RPC 본문은 거의 변하지 않고, 그 주위의 봉투(envelope)만 바뀐다는 점을 알아차리게 됩니다.

## 실습 랩

`code/main.py`를 열어 보세요. 이 코드는 `region` 인자에 `x-mcp-header: Region` 표시가 붙은 `run_report` 도구를 가진 서버 하나를 만들고, 같은 호출을 세 가지 방식으로 밀어붙입니다. `call_stdio`는 자식 프로세스가 보는 그대로, 프레이밍은 `frame_message`와 `parse_frames`를 통해, 요청을 서버에 곧장 보냅니다. `call_http`는 `build_http_headers`로 복제된 헤더를 만들고, `handle_http_request`로 검증한 뒤에야 서버로 디스패치하며, 요청과 응답을 `{"http": {...}, "message": {...}}`로 감싸서 기록합니다. `call_http_with_header_mismatch`는 같은 요청을 받아 `Mcp-Method` 헤더만 `prompts/get`으로 바꾸고, 그 결과인 `400`과 `-32020`을 보여 줍니다. 그 항목은 `"violation"`으로 감싸여 있어서, 전사 검사기는 그 일부러 틀린 헤더의 검증을 건너뛰고 그 뒤에 이어지는 오류 응답을 대신 검사합니다.

```bash
python3 code/main.py
```

JSON-RPC 메시지로는 결코 변하지 않는 결과들 — GET이나 DELETE에 대한 `405`, 허용되지 않은 Origin에 대한 `403`, 받아들인 알림에 대한 본문 없는 `202` — 는 전사에 전혀 나타나지 않습니다. 이를 표현할 `result`나 `error` 객체가 없기 때문입니다. 이들은 `handle_http_get_or_delete`, `validate_origin`, `handle_http_notification` 안에, 그리고 각각을 직접 시험하는 테스트 속에 살아 있습니다. `region` 인자를 쉼표나 비 ASCII 문자가 들어간 값으로 바꾸고 다시 실행해 보세요. `encode_header_value`가 base64 센티널로 갈아타는 것과, `decode_header_value`가 그것을 정확히 되돌리는 것을 확인할 수 있습니다.

## 완성된 산출물

`outputs/transport-selection-guide.md`는 한 페이지 참조 자료입니다. stdio와 Streamable HTTP 중 언제 무엇에 손을 뻗을지, 출처 필드와 required-for 열까지 갖춘 정확한 헤더 표, base64 센티널 규칙, 그리고 GET, DELETE, 잘못된 Origin, 헤더 불일치, 받아들인 알림에 대한 상태 코드 의사결정 목록을 담고 있습니다.

## 확인해 보기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검증합니다. stdio 프레임이 `parse_frames`를 통과해 왕복함, 중간에 줄바꿈이 끼어든 예쁘게 찍은(pretty-printed) 메시지는 거부됨, `tools/call`의 복제된 헤더가 `x-mcp-header` 파라미터까지 포함해 본문과 정확히 일치함, base64 센티널 인코딩이 명세의 직접 계산 예제와 맞고 원래 값으로 디코딩됨, `Mcp-Name`은 `resources/read`에서는 `params.uri`에서 나오고 이름 필드가 없는 메서드에서는 생략됨, 일치하는 헤더는 검증을 통과하고 바뀐 `Mcp-Method` 헤더는 `-32020`과 함께 `400`으로 돌아옴, 허용되지 않은 Origin은 `403`인 반면 허용되거나 아예 없는 Origin은 그렇지 않음, GET과 DELETE는 둘 다 `405`, 받아들인 알림은 `202`, 그리고 전사 속 고의의 불일치 예제는 위반(violation)으로 감싸져 바로 뒤에 진짜 오류 응답이 이어짐. 저장소의 와이어 검사기도 레슨의 전사를 2026-07-28 규칙으로 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/19-transports-and-http-headers
```

## 캡스톤 연계

캡스톤의 엔드투엔드 교환은 어떤 전송 방식 위에서든 이동해야 하고, 그것이 실은 모든 헤더는 이 레슨이 세운 똑같은 '본문이 진실' 규칙을 만족해야 합니다. 복제된 필드는 라우팅을 위해 존재할 뿐, 두 번째 권위의 원천으로 존재하는 게 아닙니다. 캡스톤 시나리오가 요청을 회선 수준에서 검증할 때, 그것은 여기서 여러분이 구현한 바로 그 헤더 대 본문 비교를 돌리는 것이고, 깨진 스트림을 단순히 재개할 수 없는 이유를 논할 때, 그것은 이 레슨의 stdio 재시작과 HTTP 재전송이 모두 의지하는 바로 그 스테이트리스함에 기대는 것입니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| stdio | 클라이언트가 서버를 자식 프로세스로 띄우고 대화할 때 쓰는 전송 바인딩 |
| Streamable HTTP | 모든 JSON-RPC 메시지가 하나의 MCP 엔드포인트로 보내는 자기만의 POST가 되는 전송 바인딩 |
| 프레임(frame) | stdio에서 줄바꿈으로 구분된 JSON-RPC 메시지 하나. 중간에 끼어든 줄바꿈을 절대 품지 않음 |
| `MCP-Protocol-Version` | 요청의 `_meta` 프로토콜 버전과 같아야 하는 필수 헤더 |
| `Mcp-Method` | 요청의 JSON-RPC `method`를 복제하는 필수 헤더 |
| `Mcp-Name` | `tools/call`, `resources/read`, `prompts/get`에서 `params.name` 또는 `params.uri`를 복제하는 헤더 |
| `x-mcp-header` | 인자 하나를 `Mcp-Param-{Name}` 헤더로 복제하게 만드는 도구 스키마 주석 |
| Base64 센티널 | 헤더 값이 안전한 평범한 ASCII가 아닐 때 쓰는 `=?base64?{value}?=` 인코딩 |
| `HeaderMismatch` | 복제된 헤더가 본문과 어긋날 때 서버가 HTTP `400`과 함께 돌려주는 `-32020` 오류 |
| Origin 검증 | DNS 리바인딩을 막기 위해 허용되지 않은 `Origin` 헤더를 `403`으로 거절하는 검사 |

## 더 읽을거리

- [전송 방식 개요](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [stdio 전송 방식](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
- [Streamable HTTP 전송 방식](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [도구 정의: x-mcp-header](https://modelcontextprotocol.io/specification/2026-07-28/server/tools#x-mcp-header)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 9절
- `phases/13-tools-and-protocols/09-mcp-transports`. 같은 POST 전용 계약을 더 깊이 다룹니다
