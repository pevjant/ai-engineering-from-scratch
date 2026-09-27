> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 에이전트 상태 머신 — 그래프, 노드, 체크포인트

> 손으로 짠 ReAct 루프는 그냥 `while True`입니다. 같은 루프를 명시적인 그래프로 작성하면 체크포인트를 찍고, 멈추고, 분기하고, 시간을 거슬러 돌아갈 수 있는 무언가가 됩니다. 에이전트는 그대로인데, 에이전트를 감싼 하네스가 달라진 것입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 11 · 09(함수 호출), 페이즈 11 · 14(Model Context Protocol)
**소요 시간:** 약 75분

## 문제 상황

함수 호출 에이전트를 출시했습니다. 세 턴은 잘 돌다가 어디선가 문제가 생깁니다. 모델이 500을 반환하는 도구를 건드리거나, 사용자가 작업 도중 마음을 바꾸거나, 에이전트가 사람의 서명 없이 주문 환불을 결정하는 상황입니다. `while True:` 루프에는 갈고리(hook)가 없습니다. 멈출 수도, 되감을 수도 없고, "모델이 다른 도구를 골랐더라면 어땠을까"를 시험해 볼 수도 없습니다. 데모를 넘어 출시하는 순간, 에이전트는 '됐거나 안 됐거나' 둘 중 하나인 블랙박스가 됩니다.

일단 보면 다음 단계는 자명합니다. 에이전트는 이미 상태 머신입니다. 시스템 프롬프트 + 메시지 기록 + 대기 중인 도구 호출 + 다음 행동이 곧 상태죠. 이 상태 머신을 명시적으로 만들면 됩니다. "모델이 생각한다", "도구가 실행된다", "사람이 승인한다"를 노드로, 그 사이의 조건 전이를 엣지로 옮기세요. 그래프가 명시되면 하네스는 네 가지를 공짜로 얻습니다. 체크포인팅(단계 사이 상태 저장), 인터럽트(사람을 위해 일시정지), 스트리밍(토큰과 중간 이벤트 스트리밍), 타임 트래블(이전 상태로 되감고 다른 분기 시도)입니다.

이 추상화의 레퍼런스 구현이 LangGraph입니다. LangChain식 에이전트 프레임워크("AgentExecutor 드릴 테니 알아서 잘 쓰세요")와는 다릅니다. 상태, 영속성, 인터럽트가 모두 일급 시민인 그래프 런타임입니다. 에이전트 루프는 손으로 쓰는 것이 아니라 그리는 것입니다.

## 개념

![LangGraph StateGraph: 노드, 엣지, 체크포인터](../assets/langgraph-stategraph.svg)

`StateGraph`는 세 가지로 이루어집니다.

1. **상태(State).** 그래프를 흐르는 타입이 있는 dict(TypedDict 또는 Pydantic 모델)입니다. 모든 노드는 전체 상태를 받고 부분 업데이트를 반환하며, LangGraph는 필드마다 *리듀서(reducer)*로 이를 병합합니다. 누적되어야 할 리스트는 `operator.add`, 기본값은 덮어쓰기입니다.
2. **노드(Nodes).** `state -> partial_state` 형태의 Python 함수입니다. 각각이 하나의 분리된 단계입니다. "모델 호출", "도구 실행", "요약" 같은 것이죠.
3. **엣지(Edges).** 노드 사이의 전이입니다. 정적 엣지는 한 곳으로만 향합니다. 조건부 엣지는 `state -> next_node_name` 라우터 함수를 받아 모델 출력에 따라 그래프가 분기할 수 있게 합니다.

그래프를 컴파일합니다. 컴파일은 토폴로지를 묶고, 체크포인터를 붙이고(선택 사항이지만 프로덕션(운영 환경)에는 필수), 실행 가능한(runnable) 객체를 돌려줍니다. 초기 상태와 `thread_id`를 넣어 실행하면, 실행의 매 단계가 `(thread_id, checkpoint_id)`를 키로 하는 체크포인트를 저장합니다.

### 네 가지 초능력

**체크포인팅.** 노드가 전환될 때마다 새 상태를 저장소에 기록합니다(테스트는 인메모리, 프로덕션은 Postgres/Redis/SQLite). 같은 `thread_id`로 그래프를 다시 호출하면 멈췄던 곳에서 이어서 실행됩니다.

**인터럽트.** 노드에 `interrupt_before=["human_review"]`를 표시하면 그 노드가 실행되기 직전에 실행이 멈춥니다. 상태는 저장되어 있고, API는 사용자에게 "승인 대기 중"이라고 응답합니다. 나중에 같은 `thread_id`로 `Command(resume=...)`를 넣어 요청하면 실행이 재개됩니다.

**스트리밍.** `graph.stream(state, mode="updates")`는 상태 변화분(delta)이 생길 때마다 내보냅니다. `mode="messages"`는 모델 노드 안에서 LLM 토큰을 스트리밍하고, `mode="values"`는 전체 스냅샷을 내보냅니다. UI에 무엇을 보여줄지는 여러분이 고릅니다.

**타임 트래블.** `graph.get_state_history(thread_id)`는 전체 체크포인트 로그를 돌려줍니다. 과거의 `checkpoint_id`를 `graph.invoke`에 넘기면 그 지점에서 분기합니다. 디버깅("모델이 도구 B를 골랐더라면?")과, 프로덕션 기록을 재생하는 회귀 테스트에 아주 유용합니다.

### 핵심은 리듀서입니다

모든 상태 필드에는 리듀서가 있습니다. 대부분 기본값으로 충분합니다. 새 값이 이전 값을 덮어쓰죠. 하지만 메시지 리스트는 `operator.add`가 필요합니다. 그래야 새 메시지가 기존 것을 대체하지 않고 뒤에 붙습니다. 병렬 엣지의 업데이트도 리듀서를 통해 병합됩니다. 두 노드가 모두 `messages`를 갱신하는데 `Annotated[list, add_messages]`를 빠뜨리면, 두 번째 노드가 조용히 이기고 턴의 절반이 사라집니다. 리듀서가 이 라이브러리에서 유일하게 미묘한 부분입니다. 이것만 제대로 잡으면 나머지는 조립하면 됩니다.

### 네 노드로 만드는 ReAct 그래프

프로덕션급 ReAct 에이전트는 노드 넷과 엣지 둘입니다:

1. `agent` — 현재 메시지 기록으로 LLM을 호출합니다. 어시스턴트 메시지를 반환합니다(tool_calls를 포함할 수 있음).
2. `tools` — 마지막 어시스턴트 메시지의 tool_calls를 실행하고, 도구 결과를 도구 메시지로 추가합니다.
3. `agent`에서 나오는 조건부 엣지. 마지막 메시지에 tool_calls가 있으면 `tools`로, 없으면 `END`로 보냅니다.
4. `tools`에서 다시 `agent`로 돌아오는 정적 엣지.

이게 전부입니다. 체크포인팅, 인터럽트, 스트리밍이 모두 붙은 완전한 ReAct 루프(생각 → 행동 → 관찰 → 생각 → …)를 약 40줄의 코드로 얻습니다.

### StateGraph와 Send(팬아웃)

`Send(node_name, state)`를 쓰면 노드가 병렬 서브그래프를 발송할 수 있습니다. 예를 들어 에이전트가 검색기 세 개를 한 번에 조회하기로 했다고 합시다. `Send` 하나당 대상 노드의 병렬 실행이 하나 생기고, 그 출력들은 상태 리듀서를 통해 병합됩니다. LangGraph가 스레딩 기본 요소 없이 오케스트레이터-워커 패턴을 표현하는 방법이 바로 이것입니다.

### 서브그래프

컴파일된 그래프는 다른 그래프의 노드가 될 수 있습니다. 바깥 그래프에는 노드 하나로 보이고, 안쪽 그래프는 자신만의 상태와 체크포인트를 가집니다. 팀들이 슈퍼바이저-워커 에이전트를 만드는 방식이 이것입니다. 슈퍼바이저 그래프가 사용자 의도를 도메인별 워커 서브그래프로 라우팅하죠.

```figure
l5-state-graph-ledger
```

## 직접 만들어 보기

### 단계 1: 상태와 노드

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def agent_node(state: State) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: State) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

tool_node = ToolNode(tools=[search_web, read_file])

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=MemorySaver())
```

`add_messages`는 메시지 리스트가 덮어쓰지 않고 누적되게 만드는 리듀서입니다. 이것을 빠뜨리는 것이 가장 흔한 LangGraph 버그입니다.

### 단계 2: 스레드로 실행하기

```python
config = {"configurable": {"thread_id": "user-42"}}
for event in app.stream(
    {"messages": [HumanMessage("find the Anthropic headquarters address")]},
    config,
    stream_mode="updates",
):
    print(event)
```

모든 업데이트는 `{node_name: state_delta}` 형태의 dict입니다. 프런트엔드가 이를 UI로 스트리밍하면 사용자는 "에이전트가 생각하는 중… search_web 호출… 결과 수신… 답변 작성"을 실시간으로 볼 수 있습니다.

### 단계 3: human-in-the-loop 인터럽트 추가하기

노드를 표시해서 실행되기 직전에 멈추게 만듭니다.

```python
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["tools"],  # 모든 도구 호출 전에 일시정지
)

state = app.invoke({"messages": [HumanMessage("delete the production database")]}, config)
# state["__interrupt__"]가 설정됨. 제안된 도구 호출을 검사합니다.
# 승인되었다면:
from langgraph.types import Command
app.invoke(Command(resume=True), config)
# 거절되었다면: 거절 메시지를 쓰고 재개합니다
app.update_state(config, {"messages": [AIMessage("Blocked by human reviewer.")]})
```

상태, 체크포인트, 스레드는 모두 인터럽트를 넘어 유지됩니다. 실행 중이 아닐 때는 메모리에 아무것도 남지 않습니다.

### 단계 4: 디버깅용 타임 트래블

```python
history = list(app.get_state_history(config))
for snapshot in history:
    print(snapshot.values["messages"][-1].content[:80], snapshot.config)

# 이전 체크포인트에서 분기하기
target = history[3].config  # 세 단계 뒤
for event in app.stream(None, target, stream_mode="values"):
    pass  # 그 지점부터 앞으로 재생
```

입력으로 `None`을 넘기면 주어진 체크포인트부터 재생합니다. 값을 넘기면 재개하기 전에 그 체크포인트의 상태에 업데이트로 덧붙습니다. 대화 전체를 다 돌리지 않고도 문제 있던 에이전트 실행을 재현하는 방법이 이것입니다.

### 단계 5: 프로덕션용 체크포인터로 교체하기

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string("postgresql://...") as checkpointer:
    checkpointer.setup()
    app = graph.compile(checkpointer=checkpointer)
```

SQLite, Redis, Postgres용 체크포인터가 기본 제공됩니다. `MemorySaver`는 테스트용입니다. 재시작 사이에 살아남아야 하는 것이라면 진짜 저장소가 필요합니다.

## 스킬

> 에이전트를 `while True` 루프가 아니라 그래프로 만듭니다.

LangGraph에 손을 뻗기 전에 60초 설계를 해 봅니다:

1. **노드에 이름 붙이기.** 분리된 판단이나 부수 효과를 일으키는 동작은 모두 노드입니다. "에이전트가 생각함", "도구 실행", "리뷰어 승인", "응답 스트리밍" 같은 것이죠. 목록을 만들 수 없다면 그 작업은 아직 에이전트 모양이 아닙니다.
2. **상태 선언하기.** 리스트 필드마다 리듀서를 붙인 최소한의 TypedDict를 만듭니다. 모든 것을 `messages`에 우겨 넣지 마세요. 작업 전용 필드(작업 중인 `plan`, `budget` 카운터, `retrieved_docs` 리스트)는 최상위로 올리세요.
3. **엣지 그리기.** 다음 단계가 모델 출력에 의존하지 않는 한 정적 엣지로 충분합니다. 조건부 엣지마다 이름 있는 분기를 가진 라우터 함수가 필요합니다.
4. **체크포인터를 미리 고르기.** 테스트는 `MemorySaver`, 그 외는 Postgres/Redis/SQLite입니다. 체크포인터 없이 출시하지 마세요. 체크포인터가 없으면 재개도, 인터럽트도, 타임 트래블도 없습니다.
5. **인터럽트는 도구 실행 전에 정하기, 실행 후가 아니라.** 승인은 부수 효과 노드로 들어가는 엣지에 배치해 피해가 생기기 전에 취소할 수 있게 하고, 검증은 모델에서 나오는 엣지에 배치해 나쁜 호출을 값싸게 거절할 수 있게 하세요.
6. **기본으로 스트리밍하기.** UI에는 `mode="updates"`, 모델 노드 안의 토큰 수준 스트리밍에는 `mode="messages"`, 평가(eval) 때의 전체 스냅샷에는 `mode="values"`를 씁니다.

체크포인터 없는 LangGraph 에이전트는 출시를 거부합니다. 부수 효과 *뒤에* 인터럽트가 오는 에이전트도, `add_messages` 리듀서 없는 `messages` 필드도 출시를 거부합니다.

## 연습 문제

1. **쉬움.** 위의 네 노드 ReAct 그래프를 계산기 도구와 웹 검색 도구로 구현합니다. 두 턴 대화에서 `list(app.get_state_history(config))`가 최소 네 개의 체크포인트를 반환하는지 확인합니다.
2. **보통.** `agent`보다 먼저 실행되어 구조화된 `plan: list[str]`을 상태에 기록하는 `planner` 노드를 추가합니다. `agent`가 계획 단계를 완료로 표시하게 만듭니다. 체크포인트 재개 사이에 `plan`이 사라지면(잘못된 리듀서) 테스트가 실패하게 만드세요.
3. **어려움.** `Send`를 사용해 세 서브그래프(`researcher`, `writer`, `reviewer`) 사이를 라우팅하는 슈퍼바이저 그래프를 만듭니다. 각 서브그래프는 자신만의 상태와 체크포인터를 가집니다. 바깥 그래프에 `interrupt_before=["writer"]`를 추가해 사람이 리서치 브리프를 승인할 수 있게 하고, 이전 체크포인트에서의 타임 트래블이 분기한 브랜치만 다시 실행하는지 확인합니다.

## 핵심 용어

| 용어 | 흔히 하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| StateGraph | "LangGraph 그래프" | compile 전에 노드와 엣지를 추가하는 빌더 객체. |
| 리듀서 | "필드가 어떻게 병합되나" | 노드가 해당 필드의 업데이트를 반환할 때 적용되는 `(old, new) -> merged` 함수. 기본은 덮어쓰기, `add_messages`는 덧붙이기. |
| 스레드(Thread) | "대화 ID" | 한 세션의 모든 체크포인트를 묶는 `thread_id` 문자열. |
| 체크포인트 | "멈춰 둔 상태" | 노드 전환 뒤 그래프 전체 상태의 저장된 스냅샷. `(thread_id, checkpoint_id)`를 키로 함. |
| 인터럽트 | "사람을 위해 멈춤" | `interrupt_before` / `interrupt_after`가 노드 경계에서 실행을 멈춤. `Command(resume=...)`으로 재개. |
| 타임 트래블 | "이전 단계에서 분기" | `graph.invoke(None, 오래된_checkpoint_id가_담긴_config)`이 그 체크포인트부터 앞으로 재생함. |
| Send | "병렬 서브그래프 발송" | 노드가 반환해 대상 노드의 N개 병렬 실행을 일으키는 생성자. |
| 서브그래프 | "노드로 쓰인 컴파일된 그래프" | 다른 그래프에서 노드로 쓰이는 컴파일된 StateGraph. 자신만의 상태 범위를 유지함. |

## 더 읽을거리

- [LangGraph 문서](https://langchain-ai.github.io/langgraph/) — StateGraph, 리듀서, 체크포인터, 인터럽트의 공식 레퍼런스.
- [LangGraph 개념: 상태, 리듀서, 체크포인터](https://langchain-ai.github.io/langgraph/concepts/low_level/) — 이 레슨이 쓰는 멘탈 모델의 1차 자료.
- [LangGraph 영속성과 체크포인트](https://langchain-ai.github.io/langgraph/concepts/persistence/) — Postgres/SQLite/Redis 저장소, 체크포인트 네임스페이스, 스레드 ID 상세.
- [LangGraph Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) — `interrupt_before`, `interrupt_after`, `Command(resume=...)`, 상태 편집 패턴.
- [Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models" (ICLR 2023)](https://arxiv.org/abs/2210.03629) — 모든 LangGraph 에이전트가 구현하는 패턴. 추론 과정(reasoning trace)을 남기는 근거를 이해하려 읽어 보세요.
- [Anthropic — 효과적인 에이전트 만들기 (2024년 12월)](https://www.anthropic.com/research/building-effective-agents) — 어떤 그래프 형태(체인, 라우터, 오케스트레이터-워커, 평가자-최적화자)를 언제 선호해야 하는지.
- 페이즈 11 · 09(함수 호출) — 모든 LangGraph 에이전트 노드가 재사용하는 도구 호출 기본 요소.
- 페이즈 11 · 14(Model Context Protocol) — MCP 어댑터를 통해 LangGraph `ToolNode`에 연결되는 외부 도구 탐색.
- 페이즈 11 · 17(에이전트 프레임워크 트레이드오프) — LangGraph를 CrewAI, AutoGen, Agno 대신 언제 고를지.
