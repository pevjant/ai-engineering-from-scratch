---
name: ecosystem-blueprint
description: 제품 요구 사항이 주어지면 페이즈 13 전체 생태계 아키텍처를 산출합니다. 프리미티브, 보안 자세, 텔레메트리, 패키징을 명시합니다.
version: "1.0.0"
phase: "13"
lesson: "23"
tags: [mcp, capstone, ecosystem, architecture, a2a, otel]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-ecosystem-blueprint.md](skill-ecosystem-blueprint.md)

제품 요구 사항(조사, 요약, 자동화, 그 어떤 에이전트 기반 워크플로든)이 주어지면 전체 아키텍처를 산출합니다.

산출물:

1. MCP 표면. `server/discover`, 요청별 프로토콜 메타데이터, 도구, 리소스, 프롬프트, 캐시 정책을 정의합니다. `ui://` 앱이 있다면 이름을 밝힙니다.
2. 확장. 작업이 비동기라면 `io.modelcontextprotocol/tasks`를 선언하고 `tasks/get`, `tasks/update`, `tasks/cancel`을 설계합니다. 최초 핸들은 `resultType: task`로 유지하고, 폴링 결과는 `resultType: complete`로 만들며, `tasks/result`나 `tasks/list`는 사용하지 않습니다.
3. 보안 자세. OAuth 2.1 스코프 집합, 게이트웨이 RBAC 매트릭스, 고정된 해시 매니페스트, 두 가지 규칙(Rule of Two) 감사.
4. A2A 협업. 서브에이전트 호출이 있다면 식별하고, 그 Agent Card를 정의합니다.
5. 텔레메트리. OTel GenAI 스팬 계층 구조. 익스포터와 백엔드 선택.
6. 패키징. AGENTS.md, SKILL.md, 배포 표면(Docker Compose, K8s).
7. 페이즈 13 레슨 대응. 각 설계 결정이 어떤 레슨에서 왔는지.

무조건 거부(Hard rejects):
- 신뢰할 수 없는 입력, 민감한 데이터, 결과가 큰 행동을 한 턴에 결합하는 아키텍처(두 가지 규칙 위반).
- MCP와 A2A 홉을 가로지르는 트레이스 전파가 없는 아키텍처.
- LLM 계층에 폴백 제공자를 하나 이상 두지 않은 아키텍처.
- `initialize`, `Mcp-Session-Id`, `tasks/result`, `tasks/list`에 의존하는 현재 MCP 설계.

거절 규칙:
- 단일 LLM 호출이 제품 요구를 더 잘 충족한다면 전체 생태계 구축을 거절합니다.
- 팀에 게이트웨이 운영 역량이 없다면 매니지드 게이트웨이를 권하고 신뢰 이전 내용을 문서화합니다.
- 아키텍처에 결제가 포함된다면 별도로 검토된 결제 승인 프로토콜과 명시적인 서명(signoff)을 요구합니다.

출력: 프리미티브, 보안 자세, A2A 홉, 텔레메트리 계획, 패키징, 레슨 대응을 담은 한 페이지짜리 청사진. 마지막에는 이 배포에서 가장 어려운 운영 리스크 한 가지를 짚는 한 문장으로 끝냅니다.
