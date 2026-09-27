---
name: mcp-transport-migrator
description: 레거시 MCP HTTP 전송을 무상태, POST 전용 2026-07-28 계약으로 마이그레이션합니다.
version: 2.0.0
phase: 13
lesson: 09
tags: [mcp, streamable-http, stateless, migration, headers]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mcp-transport-migrator.md](skill-mcp-transport-migrator.md)

세션 기반 Streamable HTTP 또는 HTTP+SSE 서버가 주어지면, MCP `2026-07-28`용 마이그레이션 런북을 만들어 냅니다.

산출물:

1. 엔드포인트 맵. POST를 받아들이는 하나의 현대 MCP 엔드포인트를 정의합니다. 각 JSON-RPC 요청 또는 알림은 새 POST를 받습니다.
2. 응답 맵. 응답 하나에는 `application/json`을, 관련 알림에 이어 최종 응답이 오는 경우에는 요청 범위 `text/event-stream`을 씁니다.
3. 제거된 동작. 현대 GET과 DELETE에는 `405`를 돌려줍니다. `Mcp-Session-Id`와 `Last-Event-ID`는 무시합니다. 발행, 되돌려 말하기, 폐기, 재개는 절대 없습니다.
4. 요청 메타데이터. 모든 본문 `_meta`에서 프로토콜 버전과 클라이언트 기능을 요구하고, 권장 클라이언트 신원을 둡니다.
5. 헤더 검증. `MCP-Protocol-Version`, `Mcp-Method`, 조건부 `Mcp-Name`을 요구합니다. Base64 센티널을 디코드하고 헤더를 본문과 비교합니다. 불일치 시 `-32020`. 짝은 맞지만 미지원 버전에는 정확한 데이터 키 `supported`와 `requested`와 함께 `-32022`.
6. 구독 마이그레이션. 독립형 GET, `resources/subscribe`, `resources/unsubscribe`을 POST `subscriptions/listen`으로 바꿉니다. 승인, 모든 알림, 최종 결과에 listen 요청 id와 같은 `io.modelcontextprotocol/subscriptionId`를 태그합니다.
7. 상태 마이그레이션. 연결 친화성을, 인증된 주체에 묶인 명시적이고 불투명한 애플리케이션 핸들로 바꿉니다.
8. 호환성 기간. 낡은 엔드포인트는 분리하고 명확히 표시해 둡니다. 어떤 레거시 폴백보다도 현대 POST 에러를 먼저 들여다봐야 합니다. 메서드와 본문 보존이 안전하지 않으므로 POST를 `301`이나 `302`로 리디렉트하지 마세요.
9. 검증. 오리진 거부, POST 미디어 협상, 본문 메타데이터, 미러 헤더, JSON 응답, 본문 없는 승인 알림 `202`, 범위가 지정된 SSE 구독 메타데이터, GET과 DELETE `405`, 제거된 헤더 무시, 새 id로 끊어진 스트림 재시도를 테스트합니다.

즉시 반려 사항:

- 세션 id, 독립형 GET, DELETE, 재생을 현대 동작으로 제시하는 것.
- 요청별 기능을 프로세스나 연결 메모리로 공유하는 것.
- 서버가 시작한 JSON-RPC 요청 보내기.
- `Last-Event-ID`로 현대 SSE 스트림 재개하기.
- 인식된 현대 에러 뒤에 레거시로 폴백하기.
- 마이그레이션 중 JSON-RPC POST를 옮기는 데 리디렉트 쓰기.

거절 규칙:

- 인증, 인가, 정확한 오리진 정책 없이 공개 노출은 거부합니다.
- 명시적 워크플로 상태의 대체품으로 숨겨진 스티키 라우팅은 거부합니다.
- 애플리케이션 멱등성 통제 없이 비멱등 작업의 자동 재시도는 거부합니다.

출력: 전과 후 엔드포인트 표, 단계적 배포, 롤백 경계, 실행 가능한 적합성 체크리스트. 레거시 경로가 제거될 정확한 날짜로 마무리하세요.
