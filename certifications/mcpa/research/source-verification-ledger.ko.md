# MCPA 출처 검증 대장(Ledger)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [source-verification-ledger.md](source-verification-ledger.md)

이 커리큘럼의 모든 시험 사실은 가져온 날짜까지 공식 출처에 대응합니다. 프로토콜 사실은 MCP 명세에 대응합니다. 레슨과 문제는 자체 제작입니다. 출처가 바뀌면 여기서 사실과 날짜를 갱신하세요.

## 출처

- **PAGE**: MCPA 인증 페이지, https://training.linuxfoundation.org/certification/model-context-protocol-associate-mcpa/ (2026-09-24에 가져옴; 페이지 최종 수정 2026-09-16).
- **PRESS**: MCPA 출시 발표, https://www.linuxfoundation.org/press/agentic-ai-foundation-launches-mcpa-certification-to-validate-mcp-expertise (Linux Foundation, 2026년 9월 14일).
- **SPEC**: Model Context Protocol 명세 2026-07-28, https://modelcontextprotocol.io/specification/2026-07-28.

## 검증된 시험 사실

| 사실 | 값 | 출처 | 비고 |
|------|-------|--------|-------|
| 자격증 이름 | Model Context Protocol Associate (MCPA) | PAGE, PRESS | 최초의 공식 MCP 자격증이자 Agentic AI Foundation의 첫 자격증. |
| 발급 기관 | Agentic AI Foundation(Linux Foundation Training and Certification을 통해) | PAGE, PRESS | 벤더 중립적. |
| 난이도 | 초급 / 기초(Beginner / Foundational) | PAGE | "Experience Level: Beginner". |
| 형식 | 온라인, 감독관 감시(proctored), 객관식 | PAGE, PRESS | |
| 제한 시간 | 90분 | PAGE | PAGE는 "Duration of Exam 90 minutes"라고 밝힘. PRESS는 120분이라고 밝힘. 이 커리큘럼은 인증 페이지 값인 90분을 따르며 불일치를 표시해 둠. 어느 쪽에 의존하기 전에 다시 검증할 것. |
| 응시료 | 250달러(시험만) | PAGE | THRIVE-ONE 연간 구독과의 번들은 495달러. |
| 유효 기간 | 2년 | PAGE | |
| 응시 자격 | 12개월 | PAGE | |
| 재응시 | 재응시 1회 포함 | PAGE | |
| 정합 기준 명세 | MCP 2026-07-28 | PAGE, PRESS, SPEC | 시험은 최신 MCP 릴리스에 맞춰져 있음. |
| 문항 수 | 미공개 | PAGE | 공식 페이지는 문항 수를 밝히지 않음. 이 커리큘럼의 풀 모의고사는 공식 수치가 아니라 연습용 규모로 60문항을 사용함. |
| 합격 점수 | 미공개 | PAGE | 환산 점수나 커트라인은 공개되지 않음. |
| 선수 요건 | 필수는 없음. 권장 경험이 명시됨 | PAGE | JSON-RPC, LLM API, 에이전틱 패턴, 보안 기초, MCP 매니페스트 읽기. |

## 검증된 도메인과 비중

출처: PAGE(Domains and Competencies), PRESS로 교차 확인.

| 도메인 | 비중 | 하위 역량(공개된 그대로) |
|--------|--------|---------------------------------|
| MCP 기초(MCP Fundamentals) | 16% | MCP의 목적과 범위(Purpose and Scope); 핵심 MCP 개념(Core MCP Concepts); 상호운용성과 가치(Interoperability and Value) |
| 아키텍처와 구성 요소(Architecture and Components) | 14% | 스키마와 구조화 데이터(Schemas and Structured Data); MCP 호스트, 클라이언트, 서버(MCP Hosts, Clients and Servers); 모델 상호작용 흐름(Model Interaction Flow) |
| 상호작용과 실행(Interactions and Execution) | 26% | 상호작용 패턴과 응답 처리(Interaction Patterns and Response Handling); 오류 처리(Error Handling); 도구 호출 수명 주기(Tool Invocation Lifecycle); 프로토콜 프리미티브(Protocol Primitives) |
| 보안과 거버넌스(Security and Governance) | 24% | 신뢰 경계(Trust Boundaries); 권한과 동의(Permissions and Consent); 위험과 안전 통제(Risk and Safety Controls); 감사 가능성과 관측 가능성(Auditability and Observability) |
| 사용 사례와 생태계(Use Cases and Ecosystem) | 20% | 역할, 책임, 도입(Roles, Responsibilities and Adoption); 운영 사용 사례(Operational Use Cases); 생태계와 이식성(Ecosystem and Portability) |

비중의 합계는 100퍼센트입니다. `tracks/mcpa-f.json`의 도메인 학습 목표는 공개된 이 하위 역량 이름들과 MCP 2026-07-28 명세에서 파생한 자체 제작 학습 목표이며, 시험 목표를 복사한 것이 아닙니다.
