> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 지원 종료(Deprecated), 삭제(Removed)가 아니다: 루츠, 샘플링, 로깅

> MCP 2026-07-28에서 지원 종료(deprecated)는 사라졌다는 뜻이 아닙니다. 루츠, 샘플링, 로깅은 여전히 예전과 완전히 똑같이 응답하고, 열두 달 시계가 막 돌기 시작했을 뿐입니다.

**유형:** 참고 자료
**사용 언어:** Python
**선수 지식:** 레슨 14
**소요 시간:** 약 45분

## 학습 목표

- MCP 기능 수명 주기에서 Deprecated 기능과 Removed 기능을 구분합니다. 열두 달 최소 윈도우와 가장 이른 제거 시점이 어떻게 계산되는지 포함해서요
- 루츠와 샘플링이 이제 어떻게 MRTR 입력 요청으로 이동하며, 호출자가 그 요청에서 선언해야 하는 클라이언트 캐퍼빌리티로 관문이 쳐져 있는지 추적합니다
- 로깅이 요청별 `io.modelcontextprotocol/logLevel` 키로 이동한 이유와, 서버가 `notifications/message`를 보내도 되는 때와 안 되는 때를 설명합니다
- 각 Deprecated 기능의 마이그레이션 경로를 말합니다. 루츠, 샘플링, 로깅, 동적 클라이언트 등록, 스코프가 붙은 `includeContext`, HTTP+SSE
- 2026-07-28이 실제로 삭제한 소수의 메서드들(`logging/setLevel`, `notifications/roots/list_changed` 등)을 알아보고, 상태 없는 코어가 왜 그것들을 유지할 수 없었는지 설명합니다

## 문제 상황

"deprecated"를 "사라짐"의 동의어로 다루는 수험생은 MCPA 문제의 예측 가능한 한 부분을 놓치고, "영구적인 비계니까 무시하면 된다"고 다루는 수험생은 다른 부분을 놓칩니다. MCP 2026-07-28은 클라이언트를 향한 기능 세 가지, 루츠, 샘플링, 로깅을 한꺼번에 deprecated로 표시하는 한편, 같은 개정판에서 훨씬 작고 다른 메서드 집합은 완전히 삭제했습니다. 두 목록은 겹치지 않고, 시험은 바로 그 간극에 기댑니다. `roots/list`나 `sampling/createMessage`를 요구하는 `input_required` 결과를 여는 도구 호출은 오늘날 완전히 평범한 2026-07-28 와이어 트래픽입니다. 그 기능들이 합법적으로 사라질 수 있는 시점까지 아직 몇 달 혹은 몇 년이나 남았는데도요. 반면 여전히 `logging/setLevel`을 시도하는 요청은 벌렁 "method not found"를 받습니다. 그 특정 메시지가 상태 없는 코어가 이제 갖고 있지 않은 커넥션 전체 세션에 의존했기 때문입니다. 어떤 이름이 어느 양동이에 떨어지는지, 그리고 왜 그런지를 아는 것이야말로 이 레슨이 기르는 실제 능력입니다.

## 핵심 개념

MCP 명세의 모든 기능은 세 수명 주기 상태 중 정확히 하나에 자리합니다. Active, Deprecated, Removed입니다. Active는 현재 개정판의 다른 모든 것과 마찬가지로 규범 텍스트대로 구현하라는 뜻입니다. Deprecated는 기능이 명세에 여전히 온전히 있고 여전히 완전히 작동하지만, Core Maintainer 결정이 언젠가의 제거를 예약했고 마이그레이션 경로도 이미 공개되어 있다는 뜻입니다. Removed는 기능이 초안 명세에서 사라지고 다음 Current 개정판에는 없다는 뜻이지만, 마지막으로 그것을 실었던 Final 개정판에는 문서로 남습니다. Deprecated 기능은 제거 자격이 생기기도 전에 최소 열두 달의 윈도우를 안고 갑니다. 그것을 처음 Deprecated로 표시한 개정판의 출시일부터 잰 시간입니다. 실제 제거 날짜는 나중에 릴리스 준비 중에 내려지는 별개의 Core Maintainer 결정이라서, 윈도우가 닫힌 지 한참 뒤에 올 수도 있고 아예 오지 않을 수도 있습니다. Roots, Sampling, Logging은 2026-07-28 개정판이 나온 순간 SEP-2577에 따라 Deprecated가 되었으므로, 가장 이른 제거 시점은 2027-07-28 당일 또는 그 이후에 출시되는 첫 명세 개정판입니다. 그 달력 날짜 그 자체도, 우연히 나오는 다음 개정판도 아닙니다.

SEP-2577이 이 셋을 묶은 이유는 각자 같은 패턴을 보였기 때문입니다. 실제 구현 비용에 비해 현실 세계의 채택이 낮다는 것입니다. Roots는 서버가 지킬 의무가 전혀 없는 참고용 디렉터리 힌트를 주는데, 선택기 UI를 구현한 클라이언트는 거의 없었습니다. Sampling은 서버가 클라이언트의 모델 접근을 빌려 쓰게 해주지만, 올바르게 하려면 휴먼 인 더 루프(HITL) 검토, 모델 선택 로직, 그리고 2025-11-25 이후로는 온전한 도구 루프까지 필요해서 그럼에도 채택은 여전히 저조했습니다. Logging은 모든 런타임이 이미 갖춘 인프라를 복제합니다. stdio 트랜스포트에서는 `stderr`, 그 밖에서는 OpenTelemetry가 있죠. 셋 중 그 어느 것도 실제로 MCP를 정의하는 리소스, 도구, 프롬프트 모델에는 손대지 않으므로, 이들을 deprecated로 밀어내는 것은 프로토콜의 존재 이유를 줄이지 않고 구현 표면만 좁힙니다.

루츠와 샘플링은 와이어 모양을 그대로 유지했습니다. 달라진 것은 전달 메커니즘뿐입니다. 2026-07-28 이전에는 서버가 열려 있는 커넥션 위에서 `roots/list`나 `sampling/createMessage`를 서버 주도 요청으로 클라이언트에 곧장 보냈습니다. 상태 없는 코어가 그 커넥션을 완전히 제거했으므로, 이제 두 요청은 다른 모든 서버→클라이언트 요청과 똑같이 이동합니다. `InputRequiredResult`의 `inputRequests` 맵 안의 항목으로 실려 가고, 새 JSON-RPC id를 실은 재시도에서 답이 오는, 모든 서버 푸시를 대체한 바로 그 멀티 라운드 트립 패턴으로요.

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "resultType": "input_required",
    "inputRequests": {
      "workspace_roots": {"method": "roots/list"},
      "workspace_summary": {
        "method": "sampling/createMessage",
        "params": {
          "messages": [
            {"role": "user", "content": {"type": "text", "text": "Summarize this workspace in one sentence."}}
          ],
          "maxTokens": 100
        }
      }
    },
    "requestState": "summarize-workspace:v1"
  }
}
```

클라이언트가 그 같은 요청에서 짝이 되는 캐퍼빌리티, 즉 `roots: {}`나 `sampling: {}`를 `io.modelcontextprotocol/clientCapabilities`에 선언하지 않았다면 어느 항목도 합법적이지 않습니다. 어쨌든 하나가 필요한 서버는 `-32021`로 거부하고 `data.requiredCapabilities`에 필요했던 것을 나열해야 합니다. 서버가 가정할 수 없는 다른 모든 기능을 지배하는 것과 동일한 캐퍼빌리티 관문입니다. 클라이언트는 완전히 새로운 id로 원래 요청을 재시도하며, `params.inputResponses`는 `inputRequests`와 같은 방식으로 키가 매겨지고, `params.requestState`는 바이트 단위로 그대로 에코되며 결코 지어내지 않습니다.

샘플링 요청은 여전히 `includeContext`를 실을 수 있지만, 그 `"thisServer"`와 `"allServers"` 값도 별도로 deprecated입니다. 다른 SEP 아래 같은 수명 주기 레지스트리에 편입된 더 오래된 고지죠. 어차피 이 필드의 기본값은 `"none"`이므로, 가장 단순하면서 올바른 행동은 deprecated 값을 일부러 찾아 쓰는 대신 생략하는 것입니다.

로깅은 다르게 deprecated되었습니다. 그 기능 이름이 두 가지 뚜렷이 다른 와이어 동작을 커버하는데, 그중 하나만 살아남았기 때문입니다. 살아남은 부분은 요청별입니다. 클라이언트가 단일 요청의 `_meta`에 `io.modelcontextprotocol/logLevel`을 더하면, 서버는 그 심각도 이상의 `notifications/message`로 답할 수 있습니다. 단, 그 요청 자신의 응답 스트림 위에서만, 최종 결과 이전에만, 그리고 그 요청에 이 키가 없다면 전혀 보내지 않습니다.

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "level": "warning",
    "logger": "diagnostics",
    "data": {"message": "cache subsystem degraded"}
  }
}
```

살아남지 못한 부분은 주변 환경(ambient) 쪽입니다. 예전에는 클라이언트가 `logging/setLevel`을 한 번 보내면 그 커넥션의 이후 모든 메시지가 다시 바뀌기 전까지 그 레벨을 물려받았습니다. 그것은 커넥션이 요청 사이의 상태를 쥐고 있을 때만 성립하는 이야기입니다. 상태 없는 코어에는 커넥션 전체 레벨을 걸어둘 곳이 없으므로, `logging/setLevel`은 단순한 Deprecated가 아니라 사라졌습니다. 현대 서버에는 이를 위한 핸들러가 전혀 없어서 다른 모르는 메서드 이름과 완전히 똑같이 `-32601`, Method not found로 답합니다. 도구 실행 오류도, `-32602`도 아닙니다.

루츠, 샘플링, 로깅과 deprecated 레지스트리를 공유하는 항목이 둘 더 있습니다. 동적 클라이언트 등록(Dynamic Client Registration)은 클라이언트 ID 메타데이터 문서(Client ID Metadata Documents)에 자리를 내어줍니다(뒤 레슨이 등록 결정 전체를 깊게 다룹니다). 첫 공개 개정판의 HTTP+SSE 트랜스포트는 Streamable HTTP에 자리를 내어줍니다. 둘 다 여기 있는 다른 모든 것과 같은 규칙을 따릅니다. 여전히 명세에 있고, 만나는 것도 여전히 합법적이며, 같은 종류의 시계 위에서 돌아갑니다. 시험이 가장 좋아하는 함정은 이 목록 전체를 "removed"로 뭉뚱그리는 겁니다. 아닙니다. 2026-07-28이 실제로 제거한 것은 짧고 다른 목록입니다. `initialize` 핸드셰이크와 `notifications/initialized`, `Mcp-Session-Id`와 세션 범위 HTTP 엔드포인트들, `ping`, `resources/subscribe`, `logging/setLevel`, `notifications/roots/list_changed`, `Last-Event-ID`와 SSE 재개 가능성, MRTR 밖의 모든 서버 주도 요청, `tasks/result`와 `tasks/list`, 그리고 `notifications/elicitation/complete`에 묶인 URL 모드 엘리시테이션 필드들입니다. 이 어느 것도 deprecated 레지스트리에 자리하지 않습니다. 레지스트리 항목은 정의상 아직 그 자리에 있어서 그것으로부터 벗어나 마이그레이션할 무언가를 기술하는 것이니까요.

한 가지 비대칭을 더 짚을 가치가 있는데, 그래야 `notifications/roots/list_changed`만 사라지고 루츠 자체는 사라지지 않은 이유가 설명됩니다. 그 알림은 클라이언트의 노출된 루츠가 바뀌었다고 서버에게 말해주는, 클라이언트에서 서버로 가는 푸시였습니다. MRTR은 모든 서버 주도 푸시를 요청-재시도 패턴으로 대체했고, 2026-07-28이 남겨둔 유일한 청취 채널은 `subscriptions/listen`인데 이것은 클라이언트가 서버를 향해 여는 것이지 그 반대가 아닙니다. 클라이언트가 요청받지 않은 것을 서버에 밀어넣을 채널이 남아 있지 않게 되자, 그 변화 알림은 deprecated든 아니든 갈 곳이 없어서, 자신을 실어 날랐던 커넥션 모델과 함께 떠났습니다.

```figure
mcpa-15-deprecation-timeline
```

## 인터랙티브 랩

그림은 2026-07-28 출시일과 1년 뒤 가장 이른 제거일 사이에 타임라인을 깔고, 루츠, 샘플링, 로깅 각각의 레인을 놓습니다. deprecated에서 오늘까지 이어지는 실선 막대가 가장 이른 제거 표식을 지나며 점선 막대로 부드럽게 바뀝니다. 제거 자격이 생기는 것과 제거가 예정되는 것은 다르기 때문입니다. 그 아래 짧은 두 열이 와이어에서 여전히 응답하는 것들, 즉 `roots/list`, `sampling/createMessage`, 그리고 `notifications/message`와 짝을 이루는 요청별 `logLevel`을, 그냥 사라진 두 이름인 `logging/setLevel`과 `notifications/roots/list_changed`와 대비시킵니다. 레인을 제거 표식 너머로 추적해도 막대는 계속 이어집니다. 실제 제거 날짜를 정하는 것은 달력이 아니라 Core Maintainer들이기 때문입니다.

## 실습 랩

`code/main.py`를 열어 보세요. `advise_migrations`는 랩 브리프의 마이그레이션 조언자입니다. 서버의 캐퍼빌리티와 클라이언트의 캐퍼빌리티를 건네주면, 어느 쪽이 쓰고 있는 모든 Deprecated 기능을 각각의 SEP, 마이그레이션 경로, 그리고 열두 달 윈도우에서 `add_months`로 계산한 가장 이른 제거일과 함께 보고합니다. 그 뒤의 `Server`는 도구 두 개를 노출합니다. `summarize_workspace`는 루츠와 샘플링을 둘 다 필요로 합니다. 어느 쪽도 선언하지 않는 클라이언트는 빠진 캐퍼빌리티 이름과 함께 `-32021`을 곧장 받고, 둘 다 선언하는 클라이언트는 `workspace_roots`와 `workspace_summary` 항목을 실은 `input_required` 결과를 받아 답한 뒤, 새 id와 정확히 에코한 `requestState`로 재시도해서 완료 결과를 받습니다. 잘못된 `requestState`를 에코하는 재시도는 거부됩니다. `run_diagnostic`은 아무 캐퍼빌리티도 필요로 하지 않습니다. 로그 레벨 없이 호출하면 침묵하고, `logLevel: "info"`로 호출하면 info와 warning 이벤트에는 `notifications/message`를 내보되 debug는 건너뛰며, 알 수 없는 레벨로 호출하면 `-32602`를 돌려줍니다.

```bash
python3 code/main.py
```

출력의 마지막 블록을 읽어 보세요. 감싸서 분명히 라벨이 붙은 레거시 교환이 `logging/setLevel`을 바로 그 같은 서버에 보내고 `-32601`, 즉 method not found를 받습니다. 아직 그 자리에 있는 기능과 그렇지 않은 기능의 구체적인 차이입니다.

## 제공되는 산출물

`outputs/deprecation-migration-guide.md`는 한 페이지 참고 자료입니다. 수명 주기 정책 아래에서 Deprecated가 무슨 뜻인지, SEP-2577의 세 기능을 동적 클라이언트 등록과 HTTP+SSE 옆에 놓은 표, 2026-07-28이 실제로 제거한 짧은 이름 목록, 그리고 오늘날 감싸지 않은 채로도 와이어 검사기를 통과하는 더 짧은 deprecated 이름 목록이 담겨 있습니다.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요:

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 검사합니다. 루츠, 샘플링, 로깅이 각각 마이그레이션 경로와 올바르게 계산된 가장 이른 제거일과 함께 표시되는지, deprecated된 것이 아무것도 없는 캐퍼빌리티 집합이 아무 지적도 보고하지 않는지, `summarize_workspace`가 선언되지 않은 캐퍼빌리티를 `-32021`로 거부하고 그 외에는 재시도가 새 id와 에코된 `requestState`로 완료하는 정상적인 MRTR 왕복을 여는지, 어긋난 `requestState`가 거부되는지, `run_diagnostic`이 로그 레벨 없이 침묵하고 레벨이 있으면 요청된 심각도 이상만 내보내며 알 수 없는 레벨은 거부하는지, 그리고 감싼 레거시 예제가 진짜로 제거된 메서드를 현대 서버가 `-32601`로 답하는 모습을 보여주는지입니다. 저장소의 와이어 검사기도 이 레슨의 트랜스크립트를 2026-07-28 규칙에 대해 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/15-deprecated-client-features
```

## 캡스톤 연계

캡스톤의 엔드투엔드 교환은 수험생이 Deprecated 기능과 Removed 기능을 보자마자 구분할 수 있다고 가정합니다. 동의 절차에 MRTR을 기대는 방식이 이 레슨이 루츠와 샘플링에 MRTR을 기대는 방식과 같고, 트랜스크립트를 조립하는 동안 `initialize`나 `logging/setLevel`을 찾아 손을 뻗는 일은 결코 없습니다. 여기서 만든 마이그레이션 조언자는 뒤에 오는 정책 엔진과 감사 파이프라인이 모두 재사용하는 모양이기도 합니다. 캐퍼빌리티 집합이나 와이어 기록을 들여다보고, 고정된 날짜가 아니라 윈도우인 마감 전에 무엇을 바꿔야 하는지 보고하는 것이죠.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| Active | 현재 개정판이 완전히 명세하고 요구하는 기능 |
| Deprecated | 여전히 명세되어 작동하는 기능. 마이그레이션 경로와, 제거가 가능해지기까지 최소 열두 달의 윈도우가 있다 |
| Removed | 초안 명세에서 삭제되어 다음 Current 개정판에는 없는 기능 |
| 가장 이른 제거(Earliest removal) | 기능의 deprecation 윈도우가 지나간 뒤 출시되는 첫 명세 개정판 |
| Roots | 서버에 디렉터리 힌트를 제공하는 deprecated 클라이언트 기능. 이제 MRTR 입력 요청으로 요청된다 |
| Sampling | 서버가 클라이언트의 모델 접근을 빌려 쓰게 하는 deprecated 클라이언트 기능. 이제 MRTR 입력 요청으로 요청된다 |
| `io.modelcontextprotocol/logLevel` | 단일 요청이 `notifications/message`를 받도록 선택하게 하는 요청별 `_meta` 키 |
| `notifications/message` | 서버가 `logLevel`을 설정한 요청의 응답 스트림 위에서만 보낼 수 있는 로그 알림 |
| `logging/setLevel` | 제거된 커넥션 전체 로그 레벨 설정자. 상태 없는 코어에는 자리가 없다 |
| SEP-2577 | 2026-07-28 개정판에서 루츠, 샘플링, 로깅을 함께 deprecated로 만든 제안 |

## 더 읽을거리

- [Roots (deprecated)](https://modelcontextprotocol.io/specification/2026-07-28/client/roots)
- [Sampling (deprecated)](https://modelcontextprotocol.io/specification/2026-07-28/client/sampling)
- [Logging (deprecated)](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/logging)
- [Deprecated 기능 레지스트리](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)
- [기능 수명 주기와 deprecation 정책](https://modelcontextprotocol.io/community/feature-lifecycle)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 11, 15절
- `phases/13-tools-and-protocols/11-mcp-sampling`, 샘플링 마이그레이션 경로를 깊게 만들어 보는 단계
