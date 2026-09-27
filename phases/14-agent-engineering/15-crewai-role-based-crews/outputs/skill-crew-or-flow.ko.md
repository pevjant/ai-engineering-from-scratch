---
name: crew-or-flow
description: 주어진 태스크에 CrewAI 크루와 플로 중 하나를 고르고, 최소 구현의 뼈대를 세웁니다.
version: 1.0.0
phase: 14
lesson: 15
tags: [crewai, crews, flows, multi-agent, role-based]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-crew-or-flow.md](skill-crew-or-flow.md)

태스크 설명이 주어지면 크루(자율) 또는 플로(결정론)를 고르고 뼈대를 세웁니다.

판단 기준:

1. 태스크에 SLA, 컴플라이언스, 결정론적 재현 요구가 있나? -> Flow.
2. 태스크가 탐색적인가(리서치, 초고, 브레인스토밍)? -> Crew.
3. 태스크에 LLM이 순서를 정하는 전문가 4명 이상이 있나? -> Hierarchical Crew.
4. 태스크에 고정 순서의 전문가 3명 이하가 있나? -> Sequential Crew 또는 Flow — Flow를 선호하세요.

크루라면 만들 것:

1. 에이전트 정의: role, goal, backstory(짧게, 200단어 이하), tools.
2. 태스크 정의: description, expected_output, agent.
3. 맞는 Process를 가진 Crew(Sequential | Hierarchical).
4. 샘플 입력으로 크루를 돌리고 expected_output이 나오는지 확인하는 테스트 하네스스.

플로라면 만들 것:

1. `@start` 진입 함수.
2. DAG를 이루는 `@listen(topic)` 단계들.
3. 명시적 이벤트 토픽. 마법 같은 브로드캐스트는 없음.
4. 재현 하네스스: 킥오프 페이로드가 주어지면 결정론적으로 다시 돌립니다.

절대 반려 사항:

- 백스토리 없는 크루. 백스토리는 구조를 떠받치는 기둥입니다.
- 명시적 토픽 이름 없는 플로. "암묵적 체이닝"은 감사의 목적을 무너뜨립니다.
- 전문가 2명인 Hierarchical 크루. 매니저 오버헤드가 값을 하지 못합니다.

거절 규칙:

- 프로덕션 전용 컴플라이언스 태스크에 크루를 요구하면 거절하고 Flow로 옮기세요.
- 열린 리서치 태스크에 Flow를 요구하면 거절하고 Crew로 옮기세요.
- 백스토리가 200단어를 넘으면 거절하고 줄일 것을 요구하세요. 컨텍스트 예산은 유한합니다.

출력: `agents.py`, `tasks.py`, `crew.py` 또는 `flow.py`, 판단 근거를 담은 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 관측 가능성은 레슨 24(Langfuse/AgentOps), Flow에 내구 재개 의미론이 필요하면 레슨 13을 가리킵니다.
