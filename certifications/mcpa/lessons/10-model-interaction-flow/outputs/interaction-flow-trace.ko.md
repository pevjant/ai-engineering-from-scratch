> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [interaction-flow-trace.md](interaction-flow-trace.md)

# 모델 상호작용 흐름 추적

MCPA '아키텍처와 구성 요소' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.
각 단계에서 도구 호출이 무엇을 해야 할지 판단할 때 호스트 구현 곁에 두고 보세요.

## 순서대로 다섯 단계

| 단계 | 누가 움직이나 | 무슨 일이 일어나나 | 와이어에 실리나 |
|-------|----------|---------------|-------------------|
| 1. 컨텍스트 만들기 | 호스트 | 캐시된 tools/list 항목이 모델의 눈에 보이는 뷰가 됩니다: name, description, inputSchema, annotations | 아니요, 호스트 측에서 캐시 결과를 읽는 것일 뿐 |
| 2. 선택하고 초안 작성 | 모델 | 모델이 도구를 고르고 진행 중인 대화에서 인자 초안을 만듭니다 | 아니요, 호스트 안의 판단 |
| 3. 확인 | 호스트 | 사람이 초안 입력을 봅니다. 파괴적인 도구는 무엇이든 보내기 전에 '예'가 필요합니다 | 아니요, 승인되지 않으면 |
| 4. 호출 | 클라이언트 | 승인된 판단이 tools/call이 되어 params._meta에 프로토콜 버전과 기능(capabilities)을 실어 나갑니다 | 예 |
| 5. 답변 | 호스트, 그다음 모델 | 결과의 콘텐츠가 컨텍스트로 되돌아가고, 모델은 도구가 실제로 말한 것에서 답을 만듭니다 | 결과는 와이어에 실리고, 답변은 아님 |

## 모델이 보는 것, 호출 전과 후

호출 전에 모델은 서버가 보냈을 경우에 한해 `name`, `description`, `inputSchema`, `annotations`만 봅니다.
서버 코드, 자격 증명, 레지스트리 메타데이터는 보지 못합니다. 호출 후에는 `content`, 도구가 `outputSchema`를
정의했다면 `structuredContent`, 그리고 `isError` 플래그를 봅니다. HTTP 상태 코드나 헤더 같은 원시 전송 세부
정보는 절대 보지 못합니다.

## tools/call 결과가 루프를 돌리는 세 가지 방식

| 결과 | resultType | isError | 루프가 다음에 하는 일 |
|--------|------------|---------|---------------------------|
| 성공 | complete | false | 콘텐츠(와 structuredContent)를 모델에 넘김; 답변 |
| 도구 실행 오류 | complete | true | 콘텐츠를 모델에 넘김; 모델이 고쳐진 인자와 새 id로 재시도, inputResponses 없음 |
| 입력 더 필요 | input_required | 없음 | 호스트가 답을 모음(elicitation/create, sampling/createMessage, roots/list) 후 새 id, inputResponses, 서버가 보낸 requestState를 그대로 되돌려 실어 재시도 |

JSON-RPC 오류(예: 모르는 도구에 대한 `-32602`)는 네 번째 결과이며, 애초에 `tools/call` 결과가 아닙니다.
모델이 취할 수 있는 정보가 하나도 없으므로, 잘 만들어진 루프는 동일한 요청을 다시 보내지 않습니다.

## 확인 게이트

```text
read annotations from the cached tool definition
read_only  = annotations.readOnlyHint     (default false)
destructive = annotations.destructiveHint (default true, meaningful only when not read only)
gate fires when: (not read_only) and destructive
```

`annotations` 블록이 아예 없이 출시된 도구는 이 기본값 아래에서 파괴적인 것입니다. 클라이언트가 무언가를
보내기 전에 사람에게 초안 입력을 보여 주세요. 거부되면 클라이언트는 요청을 아예 만들지 않으므로, 거부가
와이어에 남기는 것은 아무것도 없고 호스트 자체 상태의 기록뿐입니다.

## 실전 예제 (code/main.py에서)

- `get_forecast({})`는 빠진 `city`를 지목하는 도구 실행 오류를 돌려줍니다. 재시도인
  `get_forecast({"city": "Pune"})`은 새 id를 쓰고 성공합니다.
- `open_ticket({"title": "..."})`은 사람에게 우선순위 확인을 요청하는 `input_required`를 돌려줍니다.
  재시도는 `inputResponses`와 서버가 발급한 정확한 `requestState` 문자열(클라이언트는 읽지 않음)을 실어
  보내고, 그제서야 티켓이 실제로 생깁니다.
- `close_ticket`은 `annotations` 없이 출시됐으므로 기본값상 파괴적입니다. 제안된 호출 하나는 승인되어
  와이어에 오르고, 다른 하나는 거부되어 요청조차 되지 않습니다.
- `archive_ticket`은 서버에 존재하지 않습니다. 호출이 한 번 보내졌다가 `-32602`로 돌아오고, 같은 이름과
  인자로 재시도되지 않습니다.

## 호스트 루프를 위한 체크리스트

- 모델 컨텍스트는 캐시된, 결정적 순서로 정렬된 tools/list 결과에서 만드세요. 턴 사이에 배열을 다시 정렬하지
  마세요. 대부분의 모델 제공자는 프롬프트 접두사를 캐시하며, 그 배열은 접두사 안에 들어 있습니다.
- 호출에 사람의 '예'가 필요한지 판단하기 전에, 서버가 보낸 어노테이션뿐 아니라 어노테이션 기본값을 적용하세요.
- 민감한 호출을 확인하기 전에 도구 이름만이 아니라 초안 입력을 보여 주세요.
- isError true는 고친 뒤 재시도하라는 신호로 취급하지, 루프를 멈추는 이유로 취급하지 마세요.
- input_required는 isError와 다른 메커니즘으로 취급하세요. 언제나 새 id와 requestState의 정확한 에코로
  재시도하며, inputResponses 키는 서버가 지은 이름 그대로 씁니다.
- JSON-RPC 오류는 그 정확한 요청의 재시도를 멈추라는 신호로 취급하되, 실패를 모델에게 완전히 숨기는 이유로
  취급하지는 마세요.
- 도구가 실제로 돌려준 콘텐츠에서 답하세요. 그것과 무관하게 멋대로 만든 요약에서 답하지 마세요.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 5, 7, 10절.
