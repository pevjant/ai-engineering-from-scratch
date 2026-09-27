---
name: actor-critic-trainer
description: 주어진 환경에 대한 A2C / A3C / GAE 설정을 만들고, 어드밴티지 추정기와 손실 가중치를 명시합니다.
version: 1.0.0
phase: 9
lesson: 7
tags: [rl, actor-critic, gae]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-actor-critic-trainer.md](skill-actor-critic-trainer.md)

환경과 연산 예산이 주어지면 다음을 출력합니다:

1. 병렬화. A2C(GPU 배치) vs A3C(CPU 비동기)와 워커 수.
2. 롤아웃 길이 T. 갱신당 환경별 스텝 수.
3. 어드밴티지 추정기. n-스텝 또는 GAE(λ); λ를 명시.
4. 손실 가중치. `c_v`(가치), `c_e`(엔트로피), 기울기 클리핑.
5. 학습률. 액터와 크리틱(분리 사용 시 각각).

시야가 1000을 넘는 환경에서 워커 하나짜리 A2C는 거부하세요(온폴리시 성이 너무 강하고 너무 느림). 어드밴티지 정규화 없이는 출시를 거부하세요. `c_e = 0`이고 관측된 엔트로피가 0.1 미만인 실행은 엔트로피 붕괴로 표시하세요.
