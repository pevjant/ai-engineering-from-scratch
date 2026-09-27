---
name: td-agent
description: 표(tabular) 또는 소규모 특성(feature) RL 태스크에서 Q-learning, SARSA, 기대 SARSA 중 하나를 고릅니다.
version: 1.0.0
phase: 9
lesson: 4
tags: [rl, td-learning, q-learning, sarsa]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-td-agent.md](skill-td-agent.md)

표 또는 소규모 특성 환경이 주어지면 다음을 출력합니다:

1. 알고리즘. Q-learning / SARSA / 기대 SARSA / n-스텝 변형. on-policy vs off-policy와 분산에 근거한 한 문장 이유.
2. 하이퍼파라미터. α, γ, ε, 감쇠 스케줄.
3. 초기화. Q_0 값(낙관적 vs 0)과 근거.
4. 수렴 진단. 목표 학습 곡선, DP가 가능하면 `|Q - Q*|` 검사.
5. 배포 시 주의점. 추론 시 탐색은 어떻게 동작하는가? SARSA의 보수성이 필요한가?

상태 공간이 10⁶를 넘는 표 TD 적용은 거부하세요. 최대값 편향(max-bias) 주의점 없이 Q-learning 에이전트를 출시하는 것은 거부하세요. ε를 처음부터 끝까지 1.0으로 고정한 채 학습한 에이전트(활용 단계가 없음)는 표시하세요.
