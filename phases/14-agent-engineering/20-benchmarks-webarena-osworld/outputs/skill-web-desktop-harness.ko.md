---
name: web-desktop-harness
description: 실행 기반 평가와 궤적 효율 지표를 갖춘 WebArena/OSWorld 스타일 하네스스를 만듭니다.
version: 1.0.0
phase: 14
lesson: 20
tags: [webarena, osworld, harness, trajectory-efficiency]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-web-desktop-harness.md](skill-web-desktop-harness.md)

대상 앱(웹 또는 데스크톱)과 정답 궤적이 딸린 태스크 목록이 주어지면 평가 하네스스를 만듭니다.

만들 것:

1. 태스크 정의: `(tid, description, gold_steps, success_predicate, state_reset)`.
2. 러너: 에이전트를 돌리고 모든 행동을 포착해 단계 수 + 경과 시간 + 성공 상태를 기록합니다.
3. 궤적 효율 지표: `agent_steps / gold_steps`. 태스크별과 집계로 보고합니다.
4. 태스크 사이 상태 초기화 — 다른 태스크가 더럽힌 상태 위에서 태스크를 돌리는 일은 없어야 합니다.
5. 실패 양상 분류기: 실패마다 그라운딩 미스(잘못된 요소)인지 계획 미스(잘못된 행동)인지 꼬리표를 답니다.

절대 반려 사항:

- 태스크 사이 상태 초기화 없음. 태스크 간 오염은 모든 점수를 무효로 만듭니다.
- 성공률만 보고. 궤적 효율이 2026년의 표준입니다.
- DOM 동등성 없이 스크린샷만 있는 하네스스. 어떤 에이전트는 DOM+비전을 씁니다. 표면을 일부러 제한하는 게 아니라면 둘 다 주세요.

거절 규칙:

- 태스크에 정답 궤적이 없으면 거절하세요. 이게 없으면 효율을 측정할 수 없습니다.
- 앱이 특정 버전에 고정돼 있지 않으면 거절하세요. 흐트러지면 실행 간 비교가 무효가 됩니다.
- 에이전트가 파괴적 도구(삭제, 게시)를 가지고 있으면 앱의 샌드박스 사본을 요구하세요.

출력: `tasks.py`, `runner.py`, `failure_classifier.py`, `report.py`, 초기화 정책·정답 궤적 조달·그라운딩 vs 계획 분리를 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 레슨 21(컴퓨터 사용 모델) 또는 레슨 30(평가 주도 개발)을 가리킵니다.
