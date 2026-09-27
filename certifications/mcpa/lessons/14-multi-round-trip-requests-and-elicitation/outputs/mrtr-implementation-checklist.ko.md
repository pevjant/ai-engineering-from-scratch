> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mrtr-implementation-checklist.md](mrtr-implementation-checklist.md)

# MRTR 구현 체크리스트

서버나 클라이언트에 다중 왕복 요청(MRTR)과 일러시테이션(elicitation)을 넣기 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## 서버 쪽: input_required로 호출 마치기

- resultType input_required로 요청을 끝낼 수 있는 건 tools/call, prompts/get, resources/read뿐입니다. 그 외의 클라이언트 요청은 이것을 받아서는 안 됩니다.
- 모든 InputRequiredResult에 inputRequests 또는 requestState 중 최소 하나는 포함합니다.
- 각 inputRequests 항목은 서버가 고른 키와 요청 객체 한 개를 짝지으며, 그 요청 객체는 elicitation/create, sampling/createMessage, roots/list 셋 중 정확히 하나여야 합니다.
- 요청한 클라이언트가 그 요청의 clientCapabilities에 선언하지 않은 inputRequests 타입은 절대 포함하지 마세요. 도구가 어차피 일러시테이션을 필요로 하는데 요청에 그 기능이 없다면 추측하지 말고 -32021(data.requiredCapabilities)로 거부하세요.
- 클라이언트가 재시도할 거라고 가정하지 마세요. 답을 기다리며 메모리든 그 밖의 무엇이든 자원을 붙잡아 두지 마세요.

## requestState 지키기

- requestState는 자기 서버가 만든 바이트라 해도, 클라이언트를 거치는 순간 공격자가 조작한 입력으로 취급합니다.
- requestState가 인가, 리소스 접근, 비즈니스 로직에 영향을 준다면 HMAC이나 AEAD 암호로 무결성을 지키세요. 검증에 실패한 상태는 거부합니다.
- 페이로드를 세 가지에 묶고 재시도 때마다 세 가지를 모두 확인하세요: 인증된 주체(clientInfo는 스스로 보고한 값이므로 안 됨), 짧은 만료 시간, 그리고 원래 요청의 핵심 매개변수(메서드, 도구 이름, 인자) 다이제스트.
- 토큰이 최대 한 번만 쓰여야 한다면 서버 측에서 일회용 사용을 강제하세요. 서명과 만료 검사만으로는 아직 유효한 토큰의 리플레이를 막지 못합니다.
- 암호화됐더라도 비밀, 자격 증명, 개인 데이터를 requestState에 직접 넣지 마세요. 중개자에게 기록되고, 캐시되고, 복사된다고 취급하세요.

## 클라이언트 쪽: 재시도 처리

- requestState는 완전히 불투명한 것으로 취급하세요. 파싱도, 들여다보기도, 디코딩도 하지 말고 내용에 기반해 판단하지 마세요.
- InputRequiredResult에 inputRequests가 실려 왔다면 재시도 전에 요청된 모든 입력을 만들어야 합니다. 없었다면 클라이언트는 바로 재시도해도 됩니다.
- InputRequiredResult에 requestState가 실려 왔다면 재시도에 완전히 똑같은 문자열을 되돌려 보내야 합니다. 없었다면 새로 만들어 넣지도 마세요.
- 재시도에는 언제나 새 JSON-RPC id를 쓰세요. 독립된 요청이지 원래 id의 연속이 아닙니다.
- inputRequests와 requestState는 그 원래 요청의 다음 재시도에만 적용됩니다. 병렬로 도는 무관한 호출에 재사용하지 마세요.

## 폼 모드 vs URL 모드 일러시테이션 고르기

| 상황 | 모드 | 이유 |
|---|---|---|
| 파괴적 동작 확인, 짧은 목록에서 고르기, 짧은 폼 작성 | form | requestedSchema로 검증하고 사용자에게 보여 줄 수 있는 구조화 데이터 |
| 비밀번호, API 키, 접근 토큰, 결제 정보 수집 | url | 폼 모드는 절대 이런 걸 실어선 안 됨. URL 모드는 이것들을 MCP 클라이언트 밖에 둠 |
| 사용자를 대신해 제3자 OAuth 흐름 실행 | url | 서버가 제3자에 대해 자기 자신이 OAuth 클라이언트가 되어 동작함. MCP 서버에 대한 클라이언트의 bearer 토큰은 무관하며 그대로임 |

- 폼 모드의 requestedSchema는 원시 타입 속성만 가진 평평한 객체입니다: string, number, integer, boolean, 단일/다중 선택 열거. 중첩 객체도 객체 배열도 없습니다.
- ElicitResult.action은 accept, decline, cancel 중 하나입니다. accept는 폼 모드에서 content를 실어 오고 URL 모드에서는 아무것도 없습니다. 셋을 모두 처리하세요. decline이나 cancel을 오류로 취급하지 마세요.
- 2026-07-28의 URL 모드는 mode, message, url만 실어 옵니다. elicitationId도 notifications/elicitation/complete도 없습니다. 둘 다 구버전 -32042 오류 코드와 함께 제거됐습니다. 서버는 클라이언트가 받아 둔 requestState로 원래 요청을 재시도하는 시점에만 결과를 알게 됩니다.

## 함정 빠른 점검

- 원래 id를 재사용하는 재시도는 틀렸습니다. 반드시 새 id여야 합니다.
- 서버가 보낸 requestState를 바꾸거나 빠뜨리는 재시도는 틀렸습니다. 반드시 그대로 에코해야 합니다.
- 명세는 검증에 실패한 requestState를 서버가 거부하라고 요구하지만 채널은 정해 두지 않습니다. 이 랩은 변조되거나 만료된 requestState를 만료된 핸들처럼 다룹니다. 즉 모델이 읽고 도구를 다시 호출해 대응할 수 있는 도구 실행 오류(isError true)로 답합니다. 새로운 input_required 결과로 다시 묻는 것도 유효한 선택입니다.
- 원래 호출을 끝내지 않은 채 열린 스트림으로 elicitation/create를 밀어 넣는 서버는 SEP-2322가 대체한 2026-07-28 이전 패턴을 구현하고 있는 것입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 7절과 11절.
