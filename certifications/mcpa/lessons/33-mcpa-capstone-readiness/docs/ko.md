# 하나의 MCP 교환을 처음부터 끝까지 읽기

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 프로덕션(운영 환경) 장애는 자기가 MCPA의 어느 도메인에 속하는지 알려 주지 않습니다. 그저 기록(transcript)을 던져 줄 뿐이고, 그 기록을 단계별로 정확하게 읽어 내는 것이 바로 이 자격증이 시험하는 기술의 전부입니다.

**유형:** 캡스톤
**언어:** Python
**선수 지식:** 레슨 00~32
**시간:** 약 60분

## 학습 목표

- 캐시 힌트가 붙은 디스커버리, 스키마 검사, MRTR 동의 왕복, 태스크, 진행 상황 알림, OAuth 오디언스(audience) 검사, 해시 체인 감사 로그를 모두 담은 2026-07-28 교환 하나를 조립하고, 각 단계가 무엇을 막아 주는지 설명할 수 있습니다
- 프로토콜 오류, 도구 실행 오류, 누락된 캐퍼빌리티(capability) 오류를 눈으로 구분하고, 각각에 맞는 JSON-RPC 코드를 말할 수 있습니다
- 여러 단계로 이루어진 교환에서 하나의 W3C 트레이스 ID가 모든 홉(hop)을 거치는 과정을 추적할 수 있습니다. HTTP로 넘어가고 OAuth 뒤로 들어가는 단 하나의 호출도 포함입니다
- 해시 체인 감사 로그를 검증하고, 항목 하나를 변조하면 그 뒤에 기록된 모든 항목에 정확히 어떤 일이 생기는지 설명할 수 있습니다
- outputs/의 준비도 체크리스트를 이용해, 이 시험이 비중을 두는 모든 도메인이 이 레슨의 기록에서 실제로 해본 구체적인 무언가에 대응한다는 것을 학습 목표별로 하나씩 확인할 수 있습니다

## 문제 상황

온콜(on-call) 엔지니어가 콘솔을 열었는데 서로 맞지 않는 두 줄을 읽습니다. 티켓에는 `checkout-api`를 프로덕션에서 재시작했다고 적혀 있는데, 장애 채널에서는 재시작한 적이 없다고 합니다. 이 불일치는 스스로 "MRTR 문제"라고 이름 붙거나 "보안과 거버넌스 문제"라고 이름 붙지 않습니다. 실마리를 풀려면 기록 하나를 처음부터 끝까지 읽어야 합니다. 재시작 요청이 올바른 형태였는지, 서버가 확인을 요청했는지, 확인 응답이 실제로 서명된 채 변조 없이 돌아왔는지, 호출자가 애초에 그 질문을 볼 수 있게 해 주는 캐퍼빌리티를 갖고 있었는지, 그리고 감사 로그가 이 모든 것과 일치하는지를 말입니다. 이 검사들 하나하나가 MCPA 블루프린트의 서로 다른 도메인, 즉 MCP 기초(MCP Fundamentals), 아키텍처와 구성 요소(Architecture and Components), 상호작용과 실행(Interactions and Execution), 보안과 거버넌스(Security and Governance), 사용 사례와 생태계(Use Cases and Ecosystem)에 속합니다. 그리고 시험에서 가장 어려운 문제들은 정확히 저 불일치처럼 만들어집니다. 정의가 아니라 증상을 주고, 답은 하나의 교환 타임라인 위 특정 지점에 놓이는 것입니다.

이 레슨은 새로운 프로토콜 기능을 소개하지 않습니다. 레슨 00~32가 한 번에 한 주제씩 다룬 내용을, 실제 시스템이 실제로 만들어 내는 단 하나의 산출물로 다시 조립합니다. 하나의 MCP 서버를 상대로 한 장애 대응 워크플로로, 옳아야 하는 곳에서는 옳고 거절해야 하는 곳에서는 거절하며, 모든 거절에는 이유가 붙고 무슨 일이 있었는지에 대한 지속되는 기록이 남습니다. 이 레슨을 그 시험 문제 유형의 리허설로, 그리고 이 자격증이 실제로 인증하는 직무의 리허설로 다루세요. 즉, 도구 호출을 기본으로 절대 신뢰하지 않고, 상대가 와이어(wire) 위에서 직접 말해 주기 전에는 상대에 대해 아무것도 가정하지 않는 시스템을 운영하는 일 말입니다.

## 개념

`code/main.py`는 `incident-console` 서버를 상대로 한 건의 장애를 재현하며, 모든 단계는 이 트랙이 이미 가르친 사실 하나에 대응합니다. 이제는 따로따로가 아니라 함께 동작하는 모습으로 보는 것이죠.

기록은 프로토콜 버저닝, 즉 레슨 04와 레슨 05의 영역에서 시작합니다. 실수로 `2025-11-25`로 설정된 클라이언트가 `server/discover`를 호출하면 `UnsupportedProtocolVersionError`, 코드 `-32022`를 받고, `data.supported`에는 서버가 실제로 말할 줄 아는 모든 버전이 적혀 있습니다. 탓할 핸드셰이크도 없고, 이전 호출에서 버전을 기억해 둘 세션도 없습니다. 모든 요청이 `params._meta`에 자기 프로토콜 버전을 직접 밝히기 때문에, 수정 방법은 그냥 올바른 버전으로 다시 물어보는 것뿐입니다. 수정된 `server/discover`는 캐시 가능한 `DiscoverResult`를 돌려 줍니다. `supportedVersions`, `capabilities`(여기에는 `extensions: {"io.modelcontextprotocol/tasks": {}}`도 포함되는데, 미리 선언해 두어야 클라이언트가 태스크를 시도해 보기 전에 태스크라는 것이 가능하다는 사실을 알 수 있습니다), `ttlMs`, 그리고 `cacheScope: "public"`입니다. 레슨 20이 깊게 다룬 바로 그 신선도 계약이죠.

```json
{
  "jsonrpc": "2.0", "id": 2,
  "result": {
    "resultType": "complete",
    "supportedVersions": ["2026-07-28"],
    "capabilities": {"tools": {"listChanged": false}, "extensions": {"io.modelcontextprotocol/tasks": {}}},
    "ttlMs": 600000, "cacheScope": "public"
  }
}
```

`tools/list`와 첫 번째 실제 호출인 읽기 전용 플릿(fleet) 스캔은 아키텍처와 상호작용 흐름을 함께 다룹니다. 각 도구가 광고하는 스키마가 클라이언트가 가진 유일한 계약이고, 서버가 등록한 적 없는 도구를 요청하면 `-32601`이 아니라 `-32602`로 돌아옵니다. 오류 분류 전체에서 시험에 가장 많이 나오는 구분점입니다. `-32601`은 서버가 정말로 들어 본 적 없는 JSON-RPC 메서드에만 쓰이며, 이 레슨에서도 일부러 `tools/call`을 `tools/execute`로 잘못 써서 한 번 트리거합니다. 스캔 요청이 `_meta.progressToken`을 설정했기 때문에, 서버는 최종 결과 전에 잠깐 `notifications/progress`를 이어서 보냅니다. 이것은 어떤 구독과도 무관하고 요청이 끝나는 순간 사라지며, 레슨 16이 `subscriptions/listen`과 구분했던 바로 그 요청 범위(request-scoped) 채널입니다.

`restart_service` 시퀀스는 세 개의 도메인이 하나의 도구 안에서 만나는 자리입니다. `environment`가 빠진 호출은 `isError: true`가 붙은 정상 결과를 받습니다. 모델이 읽고 고칠 수 있는 도구 실행 오류일 뿐, 절대 프로토콜 오류가 아닙니다. 인자가 잘못됐을 뿐 요청 자체는 합법적인 JSON-RPC였기 때문입니다(레슨 08, 레슨 18). `elicitation` 캐퍼빌리티를 선언한 적 없는 읽기 전용 콘솔이 보낸 수정된 호출은 `-32021`, `MissingRequiredClientCapability`로 거절되면서 무엇이 빠졌는지 정확히 알려 줍니다. 서버는 특정 요청이 선언하지 않은 캐퍼빌리티를 절대 가정해선 안 되기 때문입니다(레슨 07). 두 검사를 모두 통과했을 때에만 서버가 MRTR 왕복을 엽니다. `resultType: "input_required"`, 하나의 `elicitation/create` 호출을 이름으로 담은 `inputRequests` 맵, 그리고 편의를 위해 만든 문자열이 아니라 HMAC으로 서명되고 주체(principal)에 묶인 일회용 토큰인 `requestState`입니다(레슨 14, 레슨 22). 재시도는 완전히 새로운 JSON-RPC id를 써야 하고, 그 `requestState`를 바이트 단위로 그대로 되돌려 줘야 합니다.

```json
{
  "jsonrpc": "2.0", "id": 10, "method": "tools/call",
  "params": {
    "name": "restart_service",
    "arguments": {"service": "checkout-api", "environment": "production"},
    "inputResponses": {"confirm": {"action": "accept", "content": {"confirmed": true}}},
    "requestState": "eyJwcmluY2lwYWwiOiJhbGljZS1vbmNhbGwi...9f1c2a"
  }
}
```

이 레슨은 그 재시도를 일부러 망가뜨린 버전도 보냅니다. 서버가 발급한 뒤에 서명 한 글자를 바꿔 버린 것이죠. 와이어 검사기가 실제 트래픽이 아니라 풀어 본 반례(counterexample)임을 알 수 있도록, 기록에는 `violation`으로 감싸 담깁니다. 서버 자체의 HMAC 검증이 이를 거절하면서 정확히 무엇이 실패했는지 밝히는 도구 실행 오류를 돌려 줍니다. 이것이 실무에서 "보호된다"가 의미해야 하는 바입니다. 단순히 존재하는 것만이 아니라, 변조되면 드러난다는 것.

`run_full_diagnostics`는 태스크 확장, 즉 레슨 21의 주제가 빛을 발하는 자리입니다. 완전히 동일한 도구 호출이 단 하나의 조건, 즉 그 특정 요청이 `clientCapabilities.extensions`에 `io.modelcontextprotocol/tasks`를 선언했는지에 따라 다르게 동작합니다. 선언하지 않으면 다른 도구처럼 동기적으로 끝까지 실행되고 `resultType: "complete"`를 돌려 줍니다. 선언하면, 그것도 오직 서버가 `server/discover`에서 그 확장을 광고했기 때문에만, 즉시 `resultType: "task"`를 돌려 주고 클라이언트가 `tasks/get`으로 폴링하는 `taskId`를 줍니다. 모르는 id를 폴링하면 `-32602`이고, 폴링 요청 자체가 확장 선언을 잊으면 `-32021`입니다. 다른 메서드에 적용된 정확히 같은 캐퍼빌리티 규칙이죠. 두 번째 태스크에 대한 `tasks/cancel`은 협조적(cooperative)입니다. 지금은 확인 응답을 주고 다음 폴링에서 `cancelled` 상태를 주는 것이며, 절대 `notifications/cancelled`가 아닙니다. 이 리비전에서 `notifications/cancelled`는 `subscriptions/listen` 스트림을 해체할 때, stdio에서는 아직 열려 있는 요청 하나를 취소할 때만 쓰입니다.

이 기록에서 단 하나의 호출, `acknowledge_incident`은 일부러 다르게 만들어져 있습니다. Streamable HTTP로 전송되며, 그 아래 있는 JSON-RPC 본문과 반드시 일치해야 하는 `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name` 헤더를 실어 나르고, 레슨 12의 stdio 예제들이 의존하던 환경 변수 자격 증명이 아니라 OAuth 2.1 뒤에 자리합니다(레슨 19, 레슨 23). 다른 리소스 서버용으로 발급된 베어러(bearer) 토큰은 요청이 JSON-RPC 처리에 닿기도 전에 `401`로 거절됩니다. 오디언스 검증은 선택 사항이 아니고, 서버는 자기를 위해 발급되지 않은 토큰을 절대 받아서는 안 되기 때문입니다. 올바른 스코프(scope)를 가진 토큰으로 보낸 동일한 호출은 성공합니다. 여기가 이 레슨이 일부러 모든 요청에 OAuth를 강요하지 않는 유일한 지점이기도 합니다. stdio는 아예 OAuth 흐름을 돌리면 안 되고(SHOULD NOT), 그 모델을 나머지 교환에 섞어 버리면 인가(authorization)가 실제로 어디에 속하는지에 대해 잘못된 교훈을 주게 됩니다.

이 단계들 하나하나의 밑바닥에는 같은 W3C `traceparent`가 흐릅니다. 모든 요청의 `_meta`를 통해 이어지며, 끊기지 않는 하나의 트레이스 ID를 유지하고 각 홉마다 새로운 스팬(span)을 가집니다. 그리고 같은 해시 체인 감사 로그도 흐릅니다. 결정 하나당 항목 하나씩, 각 항목의 해시가 바로 앞 항목을 덮습니다(레슨 27). 사후에 항목 하나를, 버전이든 결과든 무엇이든 수정하면 `verify()`가 정확히 그 인덱스부터 실패합니다. 그 뒤 항목들이 더 이상 맞지 않는 해시에 묶여 있었기 때문입니다. 이것이 로그를 서식 있는 print 문이 아니라 기록으로 만들어 주는 것입니다.

```figure
mcpa-33-capstone-flow
```

## 인터랙티브 랩

그림은 이와 같은 흐름을 그립니다. 디스커버리가 스키마 검사로 이어지고, 스키마 검사가 MRTR 동의로, 동의가 폴링하는 태스크로, 그리고 결과로 이어집니다. 아래의 점선은 모든 홉을 끝까지 살아남는 그 하나의 트레이스 ID를, 작게 사슬처럼 이어진 상자들은 마지막에 검증되는 감사 로그를 나타냅니다. 랩을 실행하고 출력되는 줄을 순서대로 그림과 비교해 보세요.

```bash
python3 code/main.py
```

어떤 비즈니스 로직도 돌기 전에 호출의 결과를 가르는 네 순간을 주목하세요. 버전이 수정되기 전 맨 위의 `-32022`, 빠진 `environment` 인자에 대한 `isError: true`, `elicitation`을 선언한 적 없는 콘솔에 대한 `-32021`, 그리고 그 두 검사가 이미 통과한 뒤에만 나타나는 `input_required` 결과입니다. 그다음 마지막에 감사 로그가 출력되는 것, 이어서 `verify()`가 `True`를 돌려 주는 것, 그다음 항목 하나를 그 자리에서 수정하자 `verify()`가 같은 인덱스에서 실패하는 것을 지켜 보세요. `alice`의 `run_full_diagnostics` 호출이 선언하는 캐퍼빌리티를 바꿔 보고, 다시 실행하기 전에 `resultType: "task"`가 나올지 평범한 동기 결과가 나올지 예측해 보세요.

## 실습 랩

`code/`에서 파이썬 셸을 열고 `import main`을 실행합니다. `server = main.build_server()`로 새 서버를 만들고 `client = main.Client("alice-oncall", server)`로 클라이언트를 만듭니다. `capabilities={}`로 `restart_service`를 호출해 `-32021`이 돌아오는지 확인한 다음, `capabilities=main.ELICIT_CAPS`를 더해 같은 호출이 이번엔 `input_required`를 돌려 주는지 확인합니다. 그 결과에서 `requestState`를 꺼내 기록에서처럼 마지막 글자를 바꾸고, 손으로 직접 재시도해 보세요. 조용히 성공하는 것이 아니라 서명 실패를 이름으로 밝히는 `isError` 결과가 보여야 합니다. 마지막으로 태스크를 하나 만들고 한 번 폴링한 뒤, `server.audit.entries` 안으로 들어가 이미 기록된 항목의 필드 하나를 바꿔 봅니다. `server.audit.verify()`를 바꾸기 전과 후에 각각 호출하세요. 보고되는 인덱스는 정확히 당신이 건드린 항목이어야 하고, 절대 그 앞 항목이거나 목록 끝이면 안 됩니다. 수정된 항목 뒤의 모든 항목이 더 이상 존재하지 않는 값으로 해시되어 있었기 때문입니다.

## 산출물

`outputs/mcpa-readiness-checklist.md`는 이 트랙의 시험 전날용 문서입니다. `certifications/mcpa/tracks/mcpa-f.json`의 18개 학습 목표 전부를, 비중이 있는 다섯 도메인별로 묶고, 각각을 가리킬 수 있는 구체적인 무언가로 바꿔 놓았습니다. 가리킬 대상은 이 레슨의 기록 안에 있거나 그 목표를 처음 가르친 이전 레슨 안에 있습니다. 이 레슨을 마친 직후, 교환이 아직 생생할 때 한 번 훑고, 시험을 보기 전날 밤에 한 번 더 훑으세요. 전날 밤에는 새로 배우는 것이 아니라 빠르게 떠올리는 것이 목적입니다.

## 직접 확인하기

레슨 디렉터리에서 테스트를 실행합니다:

```bash
python3 -m unittest discover code/tests
```

테스트는 위의 주장들을 직접 검사합니다. 기록의 모든 요청이 프로토콜 버전과 캐퍼빌리티를 담은 `_meta`를 실는 것, 모르는 도구는 항상 `-32602`이고 모르는 메서드는 항상 `-32601`인 것, 스키마에 맞지 않는 `restart_service` 호출은 도구 실행 오류였다가 고쳐진 재시도가 `input_required`에 닿는 것, `elicitation`이 없는 호출자는 `-32021`을 받는 것, 받아들여진 MRTR 재시도는 새 id를 쓰고 `requestState`를 정확히 되돌려 주는 것, 변조된 `requestState`는 거절되는 것, `run_full_diagnostics`는 그 특정 요청이 확장을 선언할 때만 태스크가 되는 것, 태스크는 폴링으로 완료되고 협조적으로 취소되는 것, `tasks/get` 자체가 캐퍼빌리티 규칙을 집행하는 것, 다른 오디언스용 토큰은 거절되고 올바른 스코프의 토큰은 성공하는 것, 하나의 트레이스 ID가 `traceparent`를 실은 모든 홉에서 살아남는 것, 감사 로그가 검증에 통과하고 변조는 변조된 인덱스에서 잡히는 것, 그리고 기록이 레거시 메서드나 은퇴한 오류 코드를 결코 쓰지 않는 것입니다. 저장소의 와이어 검사기가 같은 기록을 2026-07-28 규칙으로 직접 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/33-mcpa-capstone-readiness
```

## 캡스톤 연결

블루프린트의 모든 도메인이 별도의 연습문제가 아니라 이 하나의 교환 안에서 한 단계로 나타납니다. MCP 기초(MCP Fundamentals)는 맨 위의 버전 협상과, 모든 것의 밑에 깔린 무상태(stateless) 가정입니다. 어떤 요청도 이전 요청이 만들어 둔 것에 기대면 안 된다는 원칙이죠. 아키텍처와 구성 요소(Architecture and Components)는 `restart_service`가 검사당하는 도구 스키마와, `scan_fleet_health`가 발견된 통로인 `tools/list` 응답입니다. 상호작용과 실행(Interactions and Execution)은 이 기록이 일부러 다루는 오류 분류 전체입니다. 모르는 도구에 `-32602`, 모르는 메서드에 `-32601`, 빠진 캐퍼빌리티에 `-32021`, 잘못된 인자에 `isError: true`, 동의에 `input_required`, 한 요청보다 오래 살아남을 수 있는 작업에 `task`, 그리고 그것을 요청한 요청에만 범위가 한정된 진행 알림이죠. 보안과 거버넌스(Security and Governance)는 HMAC으로 서명된 `requestState`, 외부 토큰이 JSON-RPC에 닿기도 전에 거절하는 OAuth 오디언스 검사, 그리고 "우리는 모든 것을 기록한다"를 실제로 검증 가능한 무언가로 바꿔 주는 해시 체인 감사 로그입니다. 사용 사례와 생태계(Use Cases and Ecosystem)는 이 모든 것이 교과서 밖에서 중요한 이유입니다. 온콜 콘솔, 폭발 반경이 있는 재시작 도구, 태스크 핸들이 필요할 만큼 긴 진단 작업, 그리고 실제 인가 뒤에 막힌 장애 확인 처리 말입니다. 데모를 넘어선 팀들이 MCP 서버 뒤에 실제로 만드는 것이 바로 이것입니다.

이 레슨 다음에 오는 것은 또 다른 레슨이 아닙니다. 준비도 체크리스트이고, 그다음은 시험 그 자체이며, 그다음은 이 교환이 공부할 다이어그램이 아니라 당신이 올바르게 운영할 책임이 있는 의존성인 시스템입니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 프로토콜 오류 | 잘못된 형태이거나 처리 불가능한 요청에 대한 JSON-RPC 오류. 모르는 도구(`-32602`)나 모르는 메서드(`-32601`) 등 |
| 도구 실행 오류 | `isError: true`가 붙은 정상 결과로, 빠진 인자 같이 모델이 읽고 고칠 수 있는 문제를 보고함 |
| MissingRequiredClientCapability | 코드 `-32021`. 요청이 `elicitation` 같은 캐퍼빌리티를 필요로 하는데 그 요청이 선언하지 않았을 때 돌아옴 |
| MRTR | 다중 왕복 요청(Multi Round-Trip Request). `input_required` 결과에 이어, 새 id와 `inputResponses`, 그리고 그대로 되돌려 준 `requestState`를 실어 재시도하는 방식 |
| requestState | `input_required` 결과 안에 담겨 돌아오는, 공격자가 만질 수 있는 입력. 인가를 결정하는 데 쓰일 때는 반드시 서명, 주체 바인딩, 일회성이 보장되어야 함 |
| 태스크 확장 | `io.modelcontextprotocol/tasks`. 양쪽 모두 그 요청에서 선언했을 때에만 `tools/call`을 오래 살아있고 폴링 가능한 `taskId`로 바꿔 줌 |
| 정준(canonical) 리소스 URI | 서버가 OAuth 액세스 토큰을 받아들이기 전에 검사하는 정확한 오디언스. 다른 오디언스용으로 발급된 토큰은 항상 거절됨 |
| traceparent | `_meta`에 실려 다니는 W3C 트레이스 컨텍스트 필드. 교환 하나당 트레이스 ID 하나, 각 홉마다 새 스팬 ID |
| 해시 체인 감사 로그 | 추가 전용(append-only) 기록으로, 각 항목의 해시가 바로 앞 항목을 덮음. 항목을 수정, 삽입, 삭제하면 체인을 다시 계산해 탐지 가능 |

## 더 읽을 거리

- [MCP 명세 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) — 이 교환이 만들어진 근거인 전체 명세
- [MCP 아키텍처 개요](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture) — 이 기록이 연기하는 역할들에 대해
- [2025-11-25 이후 MCP 변경 로그](https://modelcontextprotocol.io/specification/2026-07-28/changelog) — 무상태 코어가 무엇을 대체했는지
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 모든 섹션 — 이 트랙 전체가 기반을 둔 프로토콜 1차 자료
- `phases/13-tools-and-protocols/23-capstone-tool-ecosystem` — 전체 도구 생태계를 다른 범위로 두 번째 만들어 본 사례
- MCPA 인증 페이지(training.linuxfoundation.org/certification/model-context-protocol-associate-mcpa) — 시험의 공식 형식, 시간, 도메인 비중
