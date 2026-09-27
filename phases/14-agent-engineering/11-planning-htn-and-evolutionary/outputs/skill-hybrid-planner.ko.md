---
name: hybrid-planner
description: 하이브리드 플래너를 만듭니다 — 타당성 증명이 가능한 계획은 ChatHTN, 기계 검증 가능한 평가기를 쓰는 코드 탐색은 AlphaEvolve — 그리고 문제에 맞는 것을 고릅니다.
version: 1.0.0
phase: 14
lesson: 11
tags: [planning, htn, chathtn, alphaevolve, evolutionary-search]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-hybrid-planner.md](skill-hybrid-planner.md)

문제 유형(정책에 묶인 워크플로 vs 코드 최적화 vs 열린 태스크)이 주어지면, 플래너를 고르고 올바른 스캐폴드를 만들어 냅니다.

판단 기준:

1. 문제에 강한 사전조건/정책/스케줄링 제약이 있나? -> HTN(ChatHTN).
2. 문제에 결정론적이고 기계 검증 가능한 적합도 함수가 있나? -> 진화(AlphaEvolve).
3. 둘 다 아닌가? -> 대신 ReAct(레슨 01)나 ReWOO(레슨 02)를 쓰세요.

HTN이라면 만들 것:

1. `preconditions`, `effects_add`, `effects_remove`를 가진 `Operator` 타입.
2. `task`, `preconditions`, `subtasks`를 가진 `Method` 타입.
3. 먼저 메서드를 시도하고, LLM 분해로 폴백하며, 성공한 LLM 분해를 캐시하는 플래너.
4. 알 수 없는 연산자나 메서드를 참조하는 LLM 분해를 거부하는 검증 단계.

진화라면 만들 것:

1. 후보 프로그램들의 시드 개체군.
2. 스칼라 적합도를 돌려주는 결정론적 평가기.
3. 변이 연산자(LLM 기반이거나 규칙 기반).
4. 조기 종료가 붙은 선택 루프(상위 k 유지, 변이, 반복).

절대 반려 사항:

- 연산자 스키마 검증 없이 LLM 출력을 그대로 적용하는 ChatHTN. 타당성 주장이 무너집니다.
- 평가기가 LLM 심판을 부르는 AlphaEvolve. 적합도는 결정론적이어야 합니다. LLM 심판은 루프가 복구할 수 없는 확률적 노이즈를 끌어들입니다.
- 열린 태스크("블로그 글 써줘")에 두 패턴 중 하나를 쓰는 것. 평가기도, 사전조건도 없다면 -> ReAct를 쓰세요.

거절 규칙:

- 도메인에 명확한 연산자 스키마가 없으면 ChatHTN을 거절하세요. ReWOO나 순수 ReAct를 제안합니다.
- 도메인에 기계 검증 가능한 적합도가 없으면 AlphaEvolve를 거절하세요. Self-Refine(레슨 05)을 제안합니다.
- 사용자가 "플래너가 계획하고 LLM이 최종 결정"을 원하면 거절하세요. 기호적 옳음과 LLM 탐색 사이의 분업은 구조를 떠받치는 기둥입니다.

출력: `operators.py`, `methods.py`, `planner.py`(HTN) 또는 `evaluator.py`, `mutator.py`, `loop.py`(진화), 그리고 판단 근거를 담은 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 문제에 토론식 검증이 어울리면 레슨 25, 알고 보니 태스크가 ReWOO 모양이라면 레슨 02를 가리킵니다.
