---
name: framework-picker
description: 추상화를 문제 모양에 맞춰 에이전트 작업에 LangGraph, CrewAI, AutoGen, Agno, 평범한 Python 중 하나를 고른다
version: 1.0.0
phase: 11
lesson: 17
tags: [langgraph, crewai, autogen, agno, agent-framework, orchestration, decision-matrix]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-framework-picker.md](skill-framework-picker.md)

작업 설명(문제 모양, 실행당 총 LLM 호출 수, 분기 패턴, 내구성과 재개 요구, human-in-the-loop 체크포인트, 병렬 팬아웃, 세션 메모리, 예상 일일 실행량)이 주어지면 다음을 출력합니다:

1. 모양 일치. 맞는 추상화를 한 문장으로 짚습니다. 그래프(타입 있는 상태, 이름 있는 전이), 조직도(전문가 역할, 매니저가 라우팅하는 작업 인계), 채팅(에이전트들이 끝날 때까지 대화), 도구를 달은 단일 에이전트. 하나를 고를 수 없다면 그 작업은 아직 에이전트 모양이 아닌 것이므로 멈추고 분해합니다.
2. 분기 권한. 다음 단계를 누가 고르는지: 개발자(명시적 엣지), 매니저 LLM(CrewAI 계층), 대화에서 자연 발생(AutoGen GroupChat), 도구 호출 자체 라우팅(Agno). 해당되면 LLM 선택 라우팅의 턴당 토큰 비용을 인용합니다.
3. 상태 예산. 재시작 뒤 재개, 타임 트래블, human 인터럽트가 필요한지 확인합니다. 필요하다면 상태 우선 추상화의 LangGraph가 이기고, Agno는 세션 범위의 메모리만 커버합니다.
4. 프레임워크 선택. langgraph, crewai, autogen, agno, plain_python 중 하나를 출력합니다. 모양과 상태 답변을 프레임워크의 핵심 추상화에 대응시키는 한 문장 근거를 함께 넣습니다.
5. 탈출구. 일일 실행량이 10_000을 넘거나, 작업이 상태 없는 LLM 호출 두 번 이하라면 대신 제공사 SDK를 쓰는 평범한 Python을 추천합니다. 작은 작업에는 프레임워크 없음이 가장 빠른 프레임워크입니다.

DAG가 알려진 결정론적 워크플로에 AutoGen을 추천하는 것은 거부합니다. GroupChatManager는 개발자가 정적으로 연결했을 토큰을 발화자 고르기에 낭비합니다. CrewAI는 `output_pydantic` / `output_json`으로 구조화된 작업 출력을 지원하긴 합니다([docs.crewai.com/en/concepts/tasks](https://docs.crewai.com/en/concepts/tasks) 참고)만, 그 `context` 채널은 여전히 다음 작업의 프롬프트 문자열을 타고 흐릅니다. 그런 출력 스키마를 연결하지 않은 채 구조화된 상태를 작업 사이로 나르는 데 raw `context`에 의존하는 워크플로라면 CrewAI에 반대 의견을 냅니다. 호출 두 번짜리 요약기에 LangGraph는 반대 의견을 냅니다. StateGraph 오버헤드는 순수한 세금입니다. 리듀서 의미론을 갖춘 병렬 서브워커가 4개를 넘게 확산되는 작업에 Agno는 반대 의견을 냅니다. Agno는 출력이 단계 이름을 키로 하는 dict로 합쳐지는 `Parallel` 블록을 제공하긴 합니다([docs-v1.agno.com/workflows_2/overview](https://docs-v1.agno.com/workflows_2/overview), [docs.agno.com/workflows/access-previous-steps](https://docs.agno.com/workflows/access-previous-steps) 참고)만, LangGraph의 Send 방식 팬아웃-리듀스 API에 필적하는 것을 노출하지는 않습니다.

입력 예시: "장기 실행 리서치 워크플로: 계획, 검색기 셋으로 팬아웃, 종합, 사람이 브리프 승인, 보고서 작성, 출처 인용. 크래시 뒤 반드시 재개할 것. 프로덕션 대상이며 하루 50회 실행."

출력 예시:
- 모양: 그래프. 타입 있는 plan, 병렬 검색기 셋, synthesize와 write 사이의 이름 있는 전이.
- 분기: 조건부 엣지로 개발자가 결정. 턴당 매니저 LLM 없음.
- 상태: 재개와 human 인터럽트 필요. LangGraph 필수.
- 프레임워크: langgraph. 상태, Send 팬아웃, interrupt_before, PostgresSaver가 모두 일급.
- 탈출구: 해당 없음. 하루 50회 실행은 평범한 Python 기준선보다 훨씬 낮고, 워크플로가 너무 상태가 많아 프레임워크 없이 두기 어려움.
