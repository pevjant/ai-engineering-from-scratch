---
name: state-graph
description: 타입 지정 상태, 조건부 엣지, 노드별 체크포인팅, 내구 재개를 갖춘 LangGraph 스타일 상태 기계를 만듭니다.
version: 1.0.0
phase: 14
lesson: 13
tags: [langgraph, state-machine, durable, checkpointing, human-in-the-loop]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-state-graph.md](skill-state-graph.md)

대상 런타임, 상태 모양, 노드 함수 집합, 체크포인터 백엔드가 주어지면, 상태 기반 에이전트 그래프를 만들어 냅니다.

만들 것:

1. 타입이 지정된 `State`(dict 또는 Pydantic). 모든 필드를 문서화합니다. 노드는 상태를 읽고, 업데이트를 반환합니다.
2. `add_node`, `add_edge`, `add_conditional_edges`, `set_entry`와 `START`/`END` 센티널을 갖춘 `StateGraph`.
3. `save(session_id, node, state)`와 `load_latest(session_id)`를 가진 `Checkpointer` 인터페이스. 기본은 SQLite이고 Postgres/Redis/커스텀도 허용합니다.
4. 그래프를 한 단계씩 걷고, 매 노드 뒤 상태를 직렬화하고, 휴먼인더루프용 `PausedAtNode`를 잡아 내고, 선택적 `state_override`가 있는 `resume_from`을 지원하는 `Runner`.
5. 세 가지 토폴로지 헬퍼: 슈퍼바이저(중앙 라우터), 스웜(공유 도구 인계), 계층형(서브그래프).

절대 반려 사항:

- 난수 시드나 실제 시계를 명시적으로 기록하지 않는 비결정론적 노드. 재개는 입력 상태가 주어지면 노드 출력이 재현된다고 가정합니다.
- "요약" 상태만 저장하는 체크포인터. 전체 상태를 직렬화하지 않으면 재개가 깨집니다.
- 모든 엣지가 조건부인 그래프. 가끔 갈라지는 선형 체인을 우선하세요.

거절 규칙:

- 영속화 없는 상태 그래프를 요구하면 거절하세요. 핵심은 내구 재개입니다. 재개가 필요 없다면 레슨 12의 워크플로 패턴을 쓰세요.
- "성공할 때만 체크포인트를 찍자"는 요구는 거절하세요. 실패도 상태가 필요합니다 — 디버깅은 거기서 시작됩니다.
- 그래프가 약 30개 노드를 넘으면 평면 배치를 거절하고 중첩 서브그래프를 요구하세요. 평면적인 30노드 그래프는 리뷰가 불가능합니다.

출력: `state.py`, `graph.py`, `checkpointer.py`, `runner.py`, 상태 스키마·체크포인터 선택·재개 의미론을 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 액터 모델 대안은 레슨 14, 핸드오프/가드레일 레이어는 레슨 16, 그래프 단계의 OTel 스팬은 레슨 23을 가리킵니다.
