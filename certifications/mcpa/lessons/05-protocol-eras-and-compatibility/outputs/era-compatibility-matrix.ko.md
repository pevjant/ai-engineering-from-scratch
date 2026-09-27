> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [era-compatibility-matrix.md](era-compatibility-matrix.md)

# 프로토콜 시대 호환성 매트릭스

MCPA 'MCP 기초' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다.

## 리비전 타임라인

| 리비전 | 시대 | 핵심 변화 |
|---|---|---|
| 2024-11-05 | Legacy | 최초 공개 리비전: stdio와 HTTP+SSE 전송 방식, 그리고 모든 연결을 여던 구버전 핸드셰이크. |
| 2025-03-26 | Legacy | Streamable HTTP가 HTTP+SSE를 대체; OAuth 2.1 인가; 도구 어노테이션; 오디오 콘텐츠. |
| 2025-06-18 | Legacy | 구조화된 도구 출력; 리소스 링크; 일러시테이션(elicitation); OAuth 리소스 서버 분류; MCP-Protocol-Version 헤더; JSON-RPC 배칭 제거. |
| 2025-11-25 | Legacy | 아이콘; 점진적 범위(scope) 동의; 도구 이름 가이드; URL 모드 일러시테이션; 실험 단계 tasks; 검증 오류가 도구 실행 오류로 변경. |
| 2026-07-28 | Modern | 스테이트리스 코어, 핸드셰이크와 세션 폐지; server/discover, 다중 왕복 요청(MRTR), resultType, subscriptions/listen 추가; tasks를 확장(extension)으로 이동; roots, sampling, logging, Dynamic Client Registration 폐기. |

## 용어

- **Modern**: 2026-07-28 이상. 버전, 식별 정보, 기능(capabilities)이 요청별 메타데이터로 이동합니다.
- **Legacy**: 2025-11-25 이하. 연결이 세션을 만드는 핸드셰이크로 열립니다.
- **Dual-era**: 양쪽을 모두 지원하는 구현체로, 파싱 전에 명시적으로 시대를 결정합니다.

## stdio 탐지(probe)

다른 어떤 요청보다 먼저 `server/discover`를 보내되, 클라이언트가 선호하는 버전을 `_meta`에 실어 보냅니다:

1. `DiscoverResult`가 돌아오면: 서버는 modern입니다. 이후 요청에는 `supportedVersions`에서 하나를 골라 쓰세요.
2. 알아들을 수 있는 modern 오류가 돌아오면(예: `UnsupportedProtocolVersionError`, 코드 -32022): 서버는 modern이지만 다른 버전을 원하는 겁니다. `data.supported` 중 하나로 재시도하세요. 폴백(fallback)하지 마세요.
3. 다른 종류의 오류가 돌아오거나 합리적인 시간 안에 답이 없으면: 서버는 legacy입니다. 구버전 핸드셰이크로 폴백하세요.

폴백 판단을 특정 오류 코드 하나에 묶지 마세요. 알아들을 수 없는 오류와 타임아웃은 같은 의미입니다.

## HTTP 탐지(probe)

먼저 modern 요청을 시도합니다. `400 Bad Request`가 돌아오면 판단 전에 바디를 읽어 보세요:

- 바디에 알아들을 수 있는 modern JSON-RPC 오류가 있다면: 서버는 modern입니다. 요청을 고쳐 재시도하세요. 폴백하지 마세요.
- 바디가 비어 있거나, 알아들을 수 있는 modern 오류가 아니라면: 서버는 legacy입니다. 구버전 핸드셰이크로 폴백하고, 필요하면 더 나아가 폐기된 HTTP+SSE 전송 방식까지 내려갑니다.

## 호환성 매트릭스

| 클라이언트 | 서버 | 결과 |
|---|---|---|
| Modern | Modern | 동작합니다. server/discover는 선택 사항이고, 버전이 맞지 않으면 UnsupportedProtocolVersionError로 드러나며 클라이언트가 서로 지원하는 버전으로 재시도합니다. |
| Modern | Legacy | 실패합니다. 구버전 서버는 읽을 요청별 메타데이터가 없습니다. dual-era 탐지를 했다면 중요한 요청을 보내기 전에 이 상황을 잡았을 겁니다. |
| Dual-era | Modern | 동작합니다. 탐지가 DiscoverResult나 알아들을 수 있는 modern 오류를 돌려주므로 클라이언트는 modern으로 유지됩니다. |
| Dual-era | Legacy | 동작합니다. 탐지가 알아들을 수 없는 오류를 돌려주거나 타임아웃되므로 클라이언트는 구버전 핸드셰이크로 폴백합니다. |
| Legacy | Modern | 실패합니다. 구버전 클라이언트의 첫 요청은 modern 서버가 구현하지 않은 메서드이고, modern 서버가 요구하는 메타데이터도 없습니다. |
| Legacy | Dual-era | 동작합니다. 서버가 구버전 핸드셰이크에 응답하고 협상된 구버전 리비전으로 그 클라이언트를 서비스합니다. |
| Legacy | Legacy | 동작합니다. 전적으로 구버전 리비전 자체의 규칙 안에서요. |

## 시험을 위해 기억하기

- 2026-07-28에는 핸드셰이크도 세션도 없습니다. 모든 요청이 스스로를 설명합니다.
- 시대 판단은 서버의 속성이며, 프로세스(stdio)나 오리진(HTTP)별로 캐시하고, 나중에 실패하면 다시 탐지할 수 있습니다.
- modern 전용 서버라도 legacy 연결 시도를 거부할 때는 자신이 지원하는 버전들을 오류에 알려 줘야 합니다. legacy 전용 클라이언트에게는 뭘 해야 하는지 알아낼 다른 방법이 없기 때문입니다.
- 알아들을 수 있는 modern 오류는 절대 legacy 폴백을 촉발하지 않습니다. 폴백을 일으키는 건 알아들을 수 없는 오류나 타임아웃뿐입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 1절과 6절.
