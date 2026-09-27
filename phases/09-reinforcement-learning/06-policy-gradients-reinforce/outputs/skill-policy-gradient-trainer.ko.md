---
name: policy-gradient-trainer
description: 주어진 태스크에 대한 REINFORCE / 액터-크리틱 / PPO 학습 설정을 만들고 분산 문제를 진단합니다.
version: 1.0.0
phase: 9
lesson: 6
tags: [rl, policy-gradient, reinforce]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-policy-gradient-trainer.md](skill-policy-gradient-trainer.md)

환경(이산 / 연속 행동, 시야, 보상 통계)이 주어지면 다음을 출력합니다:

1. 정책 헤드. 소프트맥스(이산) 또는 가우시안(연속), 파라미터 수 포함.
2. 베이스라인. 없음(바닐라), 이동 평균, 학습된 `V̂(s)`, 또는 A2C 크리틱.
3. 분산 제어. 기본 켜진 reward-to-go, 반환값 정규화, 기울기 클리핑 값.
4. 엔트로피 보너스. 계수 β와 감쇠 스케줄.
5. 배치 크기. 갱신당 에피소드 수; 온폴리시 데이터 신선도 계약.

시야가 500스텝을 넘는 태스크에서 베이스라인 없는 REINFORCE는 거부하세요. 소프트맥스 헤드로 연속 행동 제어를 하는 것은 거부하세요. `β = 0`이고 관측된 정책 엔트로피가 0.1 미만인 실행은 엔트로피 붕괴로 표시하세요.
