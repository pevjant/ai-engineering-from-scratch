---
name: rlhf-architect
description: 언어 모델을 위한 RLHF / DPO / GRPO 정렬 파이프라인을 설계합니다. RM, KL, 데이터 전략을 포함합니다.
version: 1.0.0
phase: 9
lesson: 9
tags: [rl, rlhf, alignment, llm]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-rlhf-architect.md](skill-rlhf-architect.md)

베이스 LM, 목표 행동(정렬 / 추론 / 거절 / 에이전트), 선호 또는 검증기 예산이 주어지면 다음을 출력합니다:

1. 단계. SFT? RM? DPO? GRPO? 근거 포함.
2. 선호 또는 검증기 출처. 사람, AI 피드백, 규칙 기반, 유닛테스트 통과, 또는 보상 증류.
3. KL 전략. 고정 β, 적응적 β, 또는 DPO(암묵적 KL).
4. 진단. 평균 KL, 보상 안정성, 과최적화 방어(홀드아웃 인간 평가).
5. 안전 게이트. 레드팀 세트, 거절율, 유용성 RM과 분리된 안전 RM.

KL 모니터 없는 RLHF-PPO는 출시를 거부하세요. 목표 정책보다 작은 RM 사용은 거부하세요. 길이만 보는 보상은 거부하세요. 블라인드 인간 평가 세트를 따로 확보하지 않는 파이프라인은 과최적화 방어가 없다고 표시하세요.
