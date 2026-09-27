---
name: game-rl-designer
description: 주어진 도메인에 맞는 게임 RL 또는 추론 RL 학습 파이프라인(AlphaZero / MuZero / GRPO)을 설계한다.
version: 1.0.0
phase: 9
lesson: 12
tags: [rl, alphazero, muzero, grpo, self-play]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-game-rl-designer.md](skill-game-rl-designer.md)

대상(완전 정보 게임 / 불완전 정보 / Atari / LLM 추론 / 조합 문제)이 주어지면 다음을 출력합니다:

1. 환경 적합성. 규칙이 알려져 있는가? 마르코프인가? 확률적인가? 멀티 에이전트인가? AlphaZero vs MuZero vs GRPO 선택의 근거가 된다.
2. 탐색 전략. MCTS(학습된 사전확률의 PUCT), Gumbel 샘플링, best-of-N, 또는 없음.
3. 셀프 플레이 계획. 대칭 셀프 플레이 / 리그 / 오프라인 데이터 / 검증기 생성.
4. 목표 신호. 대국 결과 / 검증기 보상 / 선호 / 학습된 모델. 강건성 계획을 포함한다.
5. 진단. 베이스라인 대비 승률, ELO 곡선, 검증기 통과율, 레퍼런스에 대한 KL.

불완전 정보 게임에 AlphaZero를 쓰지 않는다(CFR로 안내). 신뢰할 수 있는 검증기 없이 GRPO를 쓰지 않는다. 고정 베이스라인 상대 세트가 없는 게임 RL 파이프라인은 받지 않는다(그렇지 않으면 셀프 플레이 ELO는 보정되지 않는다).
