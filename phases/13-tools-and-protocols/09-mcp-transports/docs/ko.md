> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# MCP 전송: stdio와 무상태 Streamable HTTP

> 전송은 MCP 메시지를 실어 나릅니다. 빠진 프로토콜 상태를 공급하지는 않습니다. `2026-07-28`에서는 로컬 stdio와 원격 Streamable HTTP 모두 자기 기술적 요청을 실어 나릅니다.

**유형:** Learn(학습)
**언어:** Python
**선수 지식:** 페이즈 13, 레슨 07과 08
**시간:** 약 65분

## 학습 목표

- 로컬 자식 프로세스에는 stdio를, 네트워크 서비스에는 Streamable HTTP를 고를 수 있습니다.
- 현대의 단일 엔드포인트, POST 전용 Streamable HTTP 계약을 구현할 수 있습니다.
- MCP 버전, 메서드, 이름 헤더를 JSON-RPC 본문과 대조해 미러링하고 검증할 수 있습니다.
- 요청 범위 SSE와 수명이 긴 `subscriptions/listen` 스트림을 올바르게 전달할 수 있습니다.
- 레거시 동작을 현대 동작으로 둔갑시키지 않으면서 세션 기반 및 레거시 HTTP+SSE 배포를 마이그레이션할 수 있습니다.

## 문제

이전 Streamable HTTP 리비전들은 프로토콜 협상을 연결과 세션 동작과 결합했습니다. 서버는 `Mcp-Session-Id`를 발행하고, 독립형 GET 스트림을 노출하고, 세션 종료를 위한 DELETE를 받아들이고, `Last-Event-ID`로 SSE를 재개할 수 있었습니다.

MCP `2026-07-28`은 그 메커니즘들을 현대 와이어에서 제거합니다. 프로토콜 버전과 클라이언트 기능이 요청 본문을 타고 가기 때문에, 모든 요청은 어떤 건강한 워커에든 떨어질 수 있습니다. HTTP 헤더는 라우팅과 정책을 위해 선택된 필드를 미러링하지만, 서버는 실행 전에 그 헤더를 본문과 대조해 검증합니다.

결과는 확장하기 쉽고 추론하기 쉽습니다. 동시에 2025 전송을 현재 것으로 가르치는 서버는 잘못된 실패 모델과 보안 모델을 가르치는 것이기도 합니다.

## 개념

### stdio

stdio 바인딩은 클라이언트가 실행한 서브프로세스용입니다:

- 클라이언트는 stdin에 한 줄에 하나의 UTF-8 JSON-RPC 메시지를 씁니다.
- 서버는 stdout에 한 줄에 하나의 UTF-8 JSON-RPC 메시지를 씁니다.
- 서버는 진단을 stderr에 씁니다.
- 서버는 stdin EOF에서 즉시 종료합니다.
- 모든 현대 요청은 `params._meta`에 버전과 클라이언트 기능을 실어 옵니다.

프로세스는 여러 호출에 걸쳐 살 수 있지만 현대 프로토콜 세션은 아닙니다. 예기치 않게 종료하면 진행 중인 요청이 잃어버립니다. 프로세스를 재시작하고, 다시 디스커버리하고, 다시 나열하고, 구독을 다시 열고, 안전한 작업은 새 요청 id로 재시도하세요.

### 2026-07-28의 Streamable HTTP

현대 서버는 POST를 받아들이는 하나의 MCP 엔드포인트(예: `/mcp`)를 노출합니다.

모든 JSON-RPC 요청 또는 알림은 새 HTTP POST입니다. 본문에는 JSON-RPC 메시지 하나가 들어 있습니다. 클라이언트는 서버에게 JSON-RPC 응답을 보내지 않습니다.

요청에 대해 서버는 둘 중 하나를 돌려줍니다:

- JSON-RPC 응답 하나를 담은 `Content-Type: application/json`; 또는
- 그 요청과 관련된 알림들과 그 뒤의 최종 JSON-RPC 응답을 담은 `Content-Type: text/event-stream`.

받아들여진 알림에는 서버가 본문 없는 `202 Accepted`를 돌려줍니다.

클라이언트는 두 응답 타입 모두를 알립니다:

```http
Accept: application/json, text/event-stream
```

### POST 전용은 진짜 POST 전용

현대 Streamable HTTP에는 독립형 GET 스트림도 DELETE 세션 엔드포인트도 없습니다.

- `GET /mcp`은 `405 Method Not Allowed`를 돌려줍니다.
- `DELETE /mcp`은 `405 Method Not Allowed`를 돌려줍니다.
- `Mcp-Session-Id`는 무시되며 절대 발행되거나 되돌려 말해지지 않습니다.
- `Last-Event-ID`는 무시됩니다. 현대 스트림은 재개 불가이기 때문입니다.

요청 범위 스트림이 최종 응답 전에 끊기면 클라이언트는 그 진행 중 요청을 잃은 것입니다. 재시도가 안전할 때 새 JSON-RPC id로 새 요청을 낼 수 있습니다. 스트림 재개를 시도해서는 안 됩니다.

### 오리진 검증

서버는 DNS 리바인딩을 막기 위해 들어오는 연결의 `Origin`을 검증합니다. 헤더가 있는데 명시적으로 허용되지 않았다면 `403 Forbidden`을 돌려줍니다. 비브라우저 클라이언트는 `Origin`을 생략할 수 있으며, 공식 전송 규칙이 이를 허용합니다.

로컬 서버는 모든 인터페이스가 아니라 `127.0.0.1`에 바인딩해야 합니다. 네트워크 서비스는 여전히 모든 요청에서 인증과 인가가 필요합니다. 오리진 검증은 인증이 아닙니다.

정규화된 설정 뒤에 정확한 오리진 매칭을 쓰세요. `origin.startswith("https://trusted.example")` 같은 접두사 검사는 공격자가 통제하는 접미사를 받아들일 수 있어 안전하지 않습니다.

### 필수 HTTP 메타데이터 헤더

모든 현대 POST 요청에는 다음이 포함됩니다:

```http
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: notes_search
```

헤더 규칙:

- `MCP-Protocol-Version`은 필수이며 `params._meta.io.modelcontextprotocol/protocolVersion`과 같아야 합니다.
- `Mcp-Method`는 필수이며 JSON-RPC `method`와 같아야 합니다.
- `Mcp-Name`은 `tools/call`, `resources/read`, `prompts/get`에 필수입니다.
- `Mcp-Name`은 `params.name`과 같거나, `resources/read`에서는 `params.uri`와 같습니다.
- 헤더 이름은 대소문자를 구분하지 않지만 헤더 값은 대소문자를 구분합니다.

안전하지 않거나 비 ASCII인 `Mcp-Name` 값은 정확한 UTF-8 Base64 센티널을 씁니다:

```text
=?base64?{Base64EncodedValue}?=
```

서버는 그 값을 본문과 비교하기 전에 디코드합니다.

빠진, 잘못된, 어긋난 미러 헤더는 JSON-RPC 코드 `-32020`과 함께 HTTP `400`을 돌려줍니다. 헤더와 본문이 서버가 지원하지 않는 버전으로 일치하면, `{"supported":["2026-07-28"],"requested":"2027-01-01"}` 같은 정확한 에러 데이터와 함께 `-32022`를 담은 HTTP `400`을 돌려줍니다.

알 수 없는 현대 메서드는 JSON-RPC `-32601`과 함께 HTTP `404`를 돌려줍니다. JSON-RPC 본문이 중요한 이유는 이중 시대 클라이언트가 그것으로 현대 에러와 레거시 엔드포인트 미스를 구분하기 때문입니다.

### 요청 범위 SSE

서버는 하나의 오래 걸리는 요청에 SSE를 고를 수 있습니다:

```text
POST tools/call id=41
  <- notifications/progress related to id=41
  <- notifications/progress related to id=41
  <- JSON-RPC response id=41
stream closes
```

서버는 이 스트림에서 독립적인 JSON-RPC 요청을 보내서는 안 됩니다. 샘플링, 일라시테이션(elicitation), 루트 상호작용은 다중 왕복 요청(Multi Round-Trip Request) 결과를 씁니다. 응답 스트림을 닫으면 그 요청이 취소됩니다.

재생을 위한 SSE 이벤트 id를 추가하지 마세요. `Last-Event-ID` 재개는 현대 리비전의 일부가 아닙니다.

### 수명이 긴 변경은 subscriptions/listen을 쓴다

변경 알림은 독립형 GET이 아니라 클라이언트가 연 요청을 씁니다:

```json
{
  "jsonrpc": "2.0",
  "id": "listen-1",
  "method": "subscriptions/listen",
  "params": {
    "notifications": {
      "toolsListChanged": true,
      "resourceSubscriptions": ["notes://note-1"]
    },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": {
        "name": "course-client",
        "version": "1.0.0"
      }
    }
  }
}
```

POST 응답은 수명이 긴 SSE 스트림입니다. 첫 프로토콜 메시지는 `notifications/subscriptions/acknowledged`입니다. 승인, 모든 변경 알림, 최종 결과는 `_meta`에 listen 요청 id와 같은 `io.modelcontextprotocol/subscriptionId`를 실어 옵니다. 서버는 SSE 주석을 keepalive로 내보낼 수 있습니다. 스트림이 끊기면 클라이언트는 새 요청 id로 `subscriptions/listen`을 다시 발행하고 영향받은 데이터를 다시 가져옵니다.

`resources/subscribe`과 `resources/unsubscribe`은 레거시 시대의 것입니다. 현대 연결에서 쓰지 마세요.

### 명시적인 애플리케이션 상태

프로토콜 세션 제거가 상태를 가진 워크플로를 금지하지는 않습니다. 서버는 불투명한 상태 핸들을 발행해 평범한 도구 결과로 돌려줄 수 있습니다. 클라이언트는 이후 호출에서 그 핸들을 명시적 인자로 넘깁니다.

핸들을 인증된 주체에 묶고, 추측 불가능하게 만들고, 만료시키고, 모든 사용을 인가하세요. 이렇게 하면 상태가 전송 친화성에 숨는 대신 애플리케이션 계층에서 보입니다.

숨겨진 레플리카 상태가 만드는 실패는 기계적입니다:

1. 요청 A가 레플리카 1에 도달해 그 프로세스의 메모리에 초안을 만듭니다.
2. 응답은 초안 핸들을 돌려주지 않습니다. 구현이 연결이 초안을 식별한다고 가정하기 때문입니다.
3. 요청 B는 새로운 POST이고 레플리카 2에 도달합니다.
4. 레플리카 2에는 유효한 프로토콜 메타데이터가 있지만 초안의 이름을 짓거나 로드할 방법이 없어, 워크플로가 실패하거나 잘못된 로컬 객체를 읽습니다.
5. 스티키 라우팅이 증상을 고치는 것처럼 보이다가, 재시작, 배포, 재스케줄, 페일오버가 다음 요청을 옮기는 순간 무너집니다.

올바른 경계는 두 부분입니다. 프로토콜 컨텍스트는 각 요청 안에 머뭅니다. 내구성 있는 애플리케이션 상태는 클라이언트에게 돌려주는 서버 발행 핸들 아래에서 공유 저장소에 삽니다. 다음 호출이 그 핸들을 공급하면 어떤 레플리카든 같은 레코드를 로드하고, 인가가 그 레코드를 인증된 주체와 테넌트에 묶습니다. 레플리카 메모리는 레코드를 캐시할 수 있지만, 정확성에 필요한 유일한 사본일 수는 없습니다.

상태 메커니즘은 수명으로 고르세요. 요청 지역 변수는 한 호출을 서빙할 수 있습니다. 짧은 MRTR 연속은 무결성이 보호되는 `requestState`를 쓸 수 있습니다. 초안이나 내구성 있는 태스크에는 명시적 핸들에 공유 지속성, 만료, 동시성 제어, 멱등성이 더해져야 합니다. 그 어떤 객체도 MCP 프로토콜 세션이 아닙니다.

### HTTP 이중 시대 호환성

현대와 레거시 서버를 모두 지원하는 클라이언트는 현대 POST를 먼저 시도합니다. HTTP `400`, `404`, `405`를 받으면 본문을 들여다봅니다:

- 인식되는 현대 JSON-RPC 에러는 서버가 현대임을 증명합니다. 요청을 교정하거나 알려진 버전으로 재시도하세요. 다운그레이드하지 마세요.
- 빈 본문이나 인식되지 않는 응답은 레거시 HTTP+SSE 서버를 가리킬 수 있습니다. 그때에만 낡은 GET 엔드포인트를 시도하고 그 레거시 `endpoint` 이벤트를 기대하세요.

서버는 마이그레이션 중 두 시대를 모두 지원할 수 있습니다. 현대 메타데이터는 POST 전용 현대 구현으로 라우팅하고, 낡은 클라이언트를 위해 별도의 레거시 엔드포인트를 유지하면 됩니다. 레거시 GET, DELETE, 세션 id, 재생 동작을 `2026-07-28`의 일부로 묘사하는 일은 절대 없어야 합니다.

```figure
tp-transport-handshake
```

## 활용하기

`code/main.py`는 Python 표준 라이브러리로 유한하고 현대적인 Streamable HTTP 서버를 구현합니다. 오리진과 미러 헤더를 검증하고, 제거된 세션 헤더를 무시하고, 정상 호출에는 JSON을 돌려주고, 유한한 `subscriptions/listen` SSE 스트림을 시연합니다.

```bash
cd code
python3 main.py --probe
python3 -m unittest discover tests -v
```

탐침(probe)이 확인하는 것들:

- 잘못된 오리진은 거부됩니다;
- 디스커버리는 세션 id 없이 성공합니다;
- `Mcp-Session-Id`와 `Last-Event-ID`는 무시됩니다;
- 헤더 불일치는 `-32020`을 돌려줍니다;
- 미지원 버전은 정확한 `supported`와 `requested` 데이터와 함께 `-32022`를 돌려줍니다;
- 받아들여진 id 없는 알림은 본문 없는 HTTP `202`를 돌려줍니다;
- GET과 DELETE는 `405`를 돌려줍니다;
- `subscriptions/listen`은 POST 응답 스트림이며, 그 승인, 알림, 최종 결과가 구독 id를 실어 옵니다.

## 출시하기

이 레슨은 `outputs/skill-mcp-transport-migrator.md`를 출시합니다. 현대 프로토콜 세션을 제거하고, 헤더-본문 검증을 추가하고, 독립형 GET을 `subscriptions/listen`으로 바꾸고, 레거시 브리지가 있다면 눈에 띄게 분리해 둡니다.

## 연습 문제

1. POST에서 `Mcp-Method`를 제거하세요. HTTP `400`과 에러 `-32020`을 확인하세요.
2. 헤더와 본문 버전을 일치시켜 `2027-01-01`로 보내세요. HTTP `400`, 에러 `-32022`, 정확한 데이터 `{"supported":["2026-07-28"],"requested":"2027-01-01"}`를 확인하세요.
3. 비 ASCII 리소스 URI에 대해 Base64 센티널 `Mcp-Name`을 보내세요. 디코드된 값이 `params.uri`와 비교되는지 확인하세요.
4. 유한한 listen 스트림을 최종 응답 전에 끊으세요. 새 JSON-RPC id로 다시 발행하고 도구를 다시 가져오세요.
5. ping 도구에 명시적인 워크플로 핸들을 추가하세요. 연결 친화성 없이 인가 주체에 묶으세요.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| stdio | 클라이언트가 실행한 서브프로세스 위의 줄바꿈 구분 JSON-RPC |
| Streamable HTTP | 각 현대 메시지가 새 POST인 단일 엔드포인트 |
| 요청 범위 SSE | 관련 알림과 최종 응답을 담은 POST 응답 스트림 |
| `subscriptions/listen` | 옵트인한 변경 알림을 위한 수명이 긴 POST 요청 |
| 헤더 불일치 | 미러 헤더가 본문과 어긋날 때의 HTTP `400`과 JSON-RPC `-32020` |
| 오리진 검증 | 들어오는 연결의 DNS 리바인딩 방어. 인증이 아님 |
| 명시적 상태 핸들 | 숨겨진 세션 상태 대신 평범한 인자로 넘기는 애플리케이션 토큰 |
| 레거시 브리지 | 호환성만을 위해 남겨 둔 별도의 이전 시대 동작 |

## 더 읽기

- [MCP 전송 개요](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [MCP stdio 전송](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
- [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [MCP 구독](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)
- [MCP 2026-07-28 변경 로그](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
