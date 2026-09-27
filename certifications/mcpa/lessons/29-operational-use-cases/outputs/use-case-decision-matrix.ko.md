> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [use-case-decision-matrix.md](use-case-decision-matrix.md)

# 사용 사례 판단 매트릭스

MCPA '사용 사례와 생태계' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다. 네 가지 질문으로 시작하고, 그다음에 맞는 행을 확인하세요.

## 네 가지 질문

1. 누가 동작을 시작하나: 모델, 애플리케이션, 사용자, 아니면 무인 시스템?
2. 그 뒤의 데이터는 얼마나 민감한가: 공개인가, 아니면 특정 사용자나 조직만의 것인가?
3. 작업은 얼마나 걸리나: 요청-응답 한 쌍인가, 아니면 몇 분 이상인가?
4. 결과에 대화형 화면이 필요한가, 그리고 승인이나 동의를 내 줄 사람이 자리에 있는가?

## 매트릭스

| 사용 사례 | 프리미티브 | 전송 방식 | 인가 경로 | 확장 | 캐시 스코프 |
|---|---|---|---|---|---|
| 개발자 도구(로컬 코드 검색, 로컬 파일 접근) | Tool | stdio | 환경 자격 증명, OAuth 흐름 없음 | 없음 | private |
| 데이터 접근(읽기 전용 컨텍스트: 티켓, 문서, 기록) | Resource | Streamable HTTP | PKCE와 함께하는 대화형 OAuth 2.1 | 없음 | 사용자별 내용이면 private, 아니면 public |
| 기업의 시스템 기록(Systems of record) | Tool 또는 Resource | Streamable HTTP | Enterprise-Managed Authorization | `io.modelcontextprotocol/enterprise-managed-authorization` | private |
| 워크플로 자동화와 긴 작업 | Tool | Streamable HTTP | 대화형 OAuth 2.1, 무인이면 클라이언트 자격 증명 | `io.modelcontextprotocol/tasks` | private |
| 대화형 UI(대시보드, 폼, 뷰어) | Tool | Streamable HTTP | 대화형 OAuth 2.1 | `io.modelcontextprotocol/ui`, 텍스트 폴백 포함 | private |
| 재사용 가능한 워크플로(스킬) | Prompt, MCP 위의 Skills가 뒷받침 | Streamable HTTP | 대화형 OAuth 2.1 | `io.modelcontextprotocol/skills` | 내용에 따라 public 또는 private |
| 머신 간 통합 | Tool | Streamable HTTP | OAuth 클라이언트 자격 증명, 사람 없음 | `io.modelcontextprotocol/oauth-client-credentials` | private |

## MCP가 잘못된 도구일 때

외부 시스템도 두 번째 소비자도 없는 기능, 문자열 포매팅, 산술, 로컬 변수로 프롬프트 조립하기 같은 것에는 프로토콜 경계가 필요 없습니다. JSON-RPC 봉투, 탐색 왕복, 인가 판단은 클라이언트와 서버가 실제로 프로세스나 조직의 경계를 넘어 상호 운용되어야 할 때만 본전이 됩니다. 그 경계를 넘는 것이 아무것도 없다면 평범한 함수 호출을 쓰세요.

## 네 가지 운영 관심사, 모든 사용 사례에

| 관심사 | 결정할 것 |
|---|---|
| 인가 경로 | 환경 자격 증명(stdio), 대화형 OAuth 2.1(사람이 있음), 클라이언트 자격 증명(무인, 머신 간), 또는 엔터프라이즈 관리(중앙 IdP 정책) |
| 캐시 스코프 | 데이터에 사용자별 민감성이 없으면 `public`, 있으면 `private`. 캐시 가능한 여섯 연산에만 적용되며, 그 자체로 접근 통제가 되지는 않음 |
| 동의 | 사람이 있는 곳에서의 민감하거나 느린 동작에는 MRTR 일러시테이션. 물어볼 사람이 없으면 일러시테이션 없는 사전 승인된 스코프 |
| 관측 가능성 | `_meta`로 전파되는 추적 컨텍스트(`traceparent`, `tracestate`). 인증된 주체에 키를 둔 감사 기록. 스스로 보고한 `clientInfo`는 절대 아님 |

## 시험을 위해 기억하기

- 도구는 모델이 통제하고, 리소스는 애플리케이션이 이끌고, 프롬프트는 사용자가 통제합니다. 프리미티브를 결정하는 것은 전송 방식이나 데이터 형식이 아니라 이 구분입니다.
- 확장은 옵트인이며 기본적으로 비활성입니다. 확장을 제공하는 서버는 그것을 선언하지 않은 호출자에게도 우아하게 기본 동작으로 내려갑니다.
- cacheScope는 인가 컨텍스트를 넘는 공유를 제한합니다. 접근 통제가 아닙니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 10절과 14절.
