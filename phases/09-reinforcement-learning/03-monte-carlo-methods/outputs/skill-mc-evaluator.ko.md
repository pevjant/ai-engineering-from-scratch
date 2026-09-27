---
name: mc-evaluator
description: 몬테카를로 롤아웃으로 정책을 평가하고, 가능하면 DP 비교가 포함된 수렴 보고서를 만듭니다.
version: 1.0.0
phase: 9
lesson: 3
tags: [rl, monte-carlo, evaluation]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mc-evaluator.md](skill-mc-evaluator.md)

환경(에피소딕, reset+step API)과 정책이 주어지면 다음을 출력합니다:

1. 방법. First-visit vs every-visit MC. 이유.
2. 에피소드 예산. 목표 횟수, 분산 진단, 예상 표준오차.
3. 탐색 계획. ε 스케줄(필요하면) 또는 탐색적 시작.
4. 골드 스탠다드 비교. 표(tabular) 환경이면 DP-최적 V*; 아니면 Q-learning / PPO 베이스라인의 상한.
5. 종료 검사. 최대 스텝 제한, 타임아웃, 끝나지 않는 궤적 처리.

유한 시야 제한 없이 비에피소딕 태스크에서 MC를 실행하는 것은 거부하세요. 표 환경에서 상태당 100 에피소드 미만으로 V^π 추정치를 보고하는 것은 거부하세요. 분산이 0인 행동만 있는 정책은 탐색 리스크로 표시하세요.
