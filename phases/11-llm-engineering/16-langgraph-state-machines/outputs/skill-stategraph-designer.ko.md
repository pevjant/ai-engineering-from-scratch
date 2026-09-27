---
name: stategraph-designer
description: 에이전트 작업을 이름 있는 노드, 타입 있는 상태, 리듀서, 체크포인터, human 인터럽트를 갖춘 LangGraph StateGraph로 바꾼다
version: 1.0.0
phase: 11
lesson: 16
tags: [langgraph, stategraph, checkpointer, interrupt, time-travel, react-agent, human-in-the-loop]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-stategraph-designer.md](skill-stategraph-designer.md)

에이전트 작업(사용자 대면 목표, 사용 가능한 도구, 예상 턴 수, 안전 폭발력이 있는 부수 효과, 내구성 요구 사항, 목표 지연 시간 예산)이 주어지면 다음을 출력합니다:

1. 노드 목록. 모든 분리된 단계에 이름을 붙입니다. LLM 사고 노드, 각 도구 실행 노드, 모든 사람 검토 단계, 요약기나 비평가가 있다면 그것들, 검색기가 있다면 그것까지. 어떤 노드가 둘 이상의 관심사를 다루면 그 설계를 거절하고 분할합니다.
2. 상태 스키마. 모든 리스트 필드에 리듀서를 붙인 TypedDict(또는 Pydantic) 필드. 메시지 로그에는 항상 Annotated[list, add_messages]를 씁니다. 작업 전용 리스트(plan, budget 카운터, 검색 문서 리스트)는 messages 밖으로 꺼내 올려, 병렬 업데이트 아래에서도 리듀서가 올바르게 동작하게 합니다.
3. 엣지 맵. 다음 단계가 결정적이면 정적 엣지. 모델이 다음 단계를 고를 때만 이름 있는 라우터 함수를 갖춘 조건부 엣지. 라우터 함수가 이전 노드에서 아직 하지 않은 새 LLM 호출에 의존하는 그래프는 거절합니다.
4. 인터럽트 배치. 되돌릴 수 없는 부수 효과(쓰기, 삭제, 결제, 비용이 드는 외부 API 호출)가 있는 모든 노드에는 interrupt_before. 출력 검증이 별도 프로세스에서 돌 때 모델 노드에는 interrupt_after. 부수 효과 노드에 interrupt_after를 두는 설계는 거절합니다. 그 시점엔 이미 부수 효과가 일어난 뒤입니다.
5. 체크포인터. MemorySaver는 테스트 전용입니다. 재시작을 견뎌야 하는 환경이라면 PostgresSaver, SQLiteSaver, RedisSaver 중에서 고릅니다. thread_id 전략(사용자별, 세션별, 대화별)과 체크포인트 TTL을 확인합니다.

체크포인터 없는 LangGraph는 출시를 거부합니다. 체크포인터가 없으면 재개도, 타임 트래블도, human-in-the-loop 재생도 없습니다. add_messages 없는 messages 필드도 출시를 거부합니다. 두 번째 쓰기가 첫 번째를 조용히 덮어쓰면서 대화의 절반이 사라집니다. 모든 전이가 플래너 LLM이 라우팅하는 조건부 엣지뿐인 그래프도 거절합니다. 그건 단계만 늘린 AutoGen이고 매 턴 토큰을 태웁니다.

입력 예시: "Anthropic Claude 기반 환불 처리 에이전트, 도구 세 개(lookup_order, issue_refund, send_email), 100달러를 넘는 환불 전에는 사람 승인을 위해 반드시 멈출 것, 서버 재시작 뒤에도 반드시 재개할 것, p95 지연 시간 예산 8초."

출력 예시:
- 노드: agent(LLM 호출), lookup_tool, refund_tool, email_tool, human_review.
- 상태: add_messages가 붙은 messages, order_context(덮어쓰기), refund_amount(덮어쓰기), reviewer_decision(덮어쓰기).
- 엣지: agent에서 should_continue 라우터로 가며 분기는 lookup_tool, refund_tool, email_tool, human_review, END. 도구 노드는 다시 agent로 돌아옴.
- 인터럽트: refund_amount > 100일 때 refund_tool에 interrupt_before. lookup_tool이나 email_tool에는 인터럽트 없음.
- 체크포인터: thread_id "user:{user_id}:case:{case_id}", 30일 TTL인 PostgresSaver.
