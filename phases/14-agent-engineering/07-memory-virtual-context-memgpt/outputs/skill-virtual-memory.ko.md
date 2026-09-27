---
name: virtual-memory
description: 어떤 대상 런타임에든 올바른 축출, 출처 인용, 신뢰할 수 없는 입력 처리를 갖춘 MemGPT 형태의 2계층 메모리 시스템(메인 컨텍스트 + 아카이벌 저장소 + 메모리 도구)을 만들어 줍니다.
version: 1.0.0
phase: 14
lesson: 07
tags: [memory, memgpt, virtual-context, archival, citations]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-virtual-memory.md](skill-virtual-memory.md)

대상 런타임(Python, Node, Rust), 모델 프로바이더(Anthropic, OpenAI, 로컬), 저장소 백엔드(인메모리, SQLite, 벡터 DB, KV, 그래프)가 주어지면 올바른 MemGPT 형태의 메모리 시스템을 만들어 냅니다.

산출물:

1. `core` 딕셔너리(이름 있는 영속 섹션)와 `messages` 리스트(FIFO)를 가진 `MainContext` 타입. 크기 상한에 도달하면 자동 축출합니다. 축출된 턴은 `conversation_search`로 여전히 찾을 수 있어야 합니다.
2. 삽입과 검색을 갖춘 `ArchivalStore`. 레코드는 반드시 `id`, `text`, `tags`, `session_id`, `turn_id`, `created_at`을 실어야 합니다. 모든 쓰기는 인용에 쓰도록 저장된 id를 반환합니다.
3. MemGPT 표면에 대응하는 다섯 가지 메모리 도구: `core_memory_append`, `core_memory_replace`, `archival_memory_insert`, `archival_memory_search`, `conversation_search`. 각각을 언제 쓰는지 알려 주는 `description` 텍스트와 함께 모델에게 제시합니다.
4. 출처 인용 계약: 모든 아카이벌 검색은 반드시 텍스트와 함께 레코드 id를 반환하고, 에이전트는 최종 답변에 반드시 이를 인용해야 합니다. 인용 없는 답변은 소프트 실패입니다.
5. 통합 훅(v1에서는 no-op이어도 됨). 레슨 08의 sleep-time 에이전트가 배관을 다시 하지 않고 끼워 들어갈 수 있게 합니다. `list_records_since(timestamp)`와 `delete(id)`를 노출합니다.

절대 거부 항목:

- 아카이벌 검색을 전체 프롬프트 LLM 채점으로 하는 것. 제대로 된 검색 백엔드(BM25, 벡터 유사도)를 쓰세요. LLM 재순위는 상위 k 후보 목록에서만 허용되고, 전체 코퍼스에서는 안 됩니다.
- 축출 정책이 없는 메인 컨텍스트. 상한 없는 메인 컨텍스트는 조용히 자라서 윈도우를 넘습니다.
- 검색해 온 콘텐츠를 사용자 지시인 것처럼 저장하는 것. 모든 아카이벌 콘텐츠는 신뢰할 수 없는 텍스트입니다(레슨 27). 시스템 프롬프트가 아니라 관찰로 모델에게 전달하세요.
- 모든 섹션을 지워 버리는 `core_memory_clear` 도구를 만드는 것. 코어는 빠지면 안 되는 기둥입니다. 전체 삭제는 발등을 찍는 행동입니다. `clear`가 아니라 `replace`를 지원하세요.

거부 규칙:

- "인용 없이 답만" 달라고 요청하면, 출처 표기가 중요한 도메인(의료, 법률, 정책, 금융)에서는 거부합니다. 타협안을 제시하세요. 인용을 인라인이 아니라 각주로 렌더링하는 방식.
- "검색한 콘텐츠를 걸러 주지 말고 전부 아카이벌에 되써 달라"고 요청하면 거부하고 레슨 27을 가리킵니다. 검색된 콘텐츠는 공격자가 닿을 수 있는 것이고, 일괄 되쓰기는 메모리 오염입니다.
- 런타임에 지속성 계층이 없다면 "장기 메모리를 갖췄다"고 묘사된 에이전트를 출시하는 것을 거부합니다. 구현이 아니라 제품 설명을 낮추세요.

출력: 컴포넌트별 파일 하나씩(`main_context.*`, `archival_store.*`, `memory_tools.*`, `agent.*`)과 축출 정책, 출처 인용 계약, 레슨 08(sleep-time 통합)과 레슨 09(Mem0 융합)를 어디에 끼워 넣을지 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다. 에이전트가 세 계층이나 비동기 통합이 필요하면 레슨 08, 벡터+KV+그래프 융합이 필요하면 레슨 09를 가리킵니다.
