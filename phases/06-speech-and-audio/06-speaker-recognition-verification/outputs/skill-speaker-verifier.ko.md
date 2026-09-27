> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-speaker-verifier.md](skill-speaker-verifier.md)

---
name: speaker-verifier
description: 모델 선택, 등록 프로토콜, 임계값 튜닝까지 포함한 화자 검증 또는 화자 분리 파이프라인을 설계한다.
version: 1.0.0
phase: 6
lesson: 06
tags: [audio, speaker, verification, diarization]
---

목표(검증 vs 식별 vs 화자 분리, 도메인, 채널, 위협 모델)와 데이터(임계값 튜닝용 시간, 화자 수, 등록 클립 예산)가 주어지면 다음을 출력한다:

1. 임베더(Embedder). ECAPA-TDNN / WavLM-SV / ReDimNet / x-vector. 이유.
2. 등록 프로토콜. 클립 수, 최소 길이, 노이즈 게이트, 채널 일치.
3. 스코어링. 코사인 / PLDA. AS-norm 사용 여부, 코호트(cohort) 크기.
4. 임계값. 목표 FAR(사기 위험) 또는 EER. 튜닝 세트 크기.
5. 스푸핑 방어. 안티 스푸핑 모델(AASIST, RawNet2), 라이브니스 챌린지, 재생 공격 탐지 중 선택.

사기 방지 등급의 배포에 안티 스푸핑 프런트엔드 없이 진행하는 것은 거부한다. 평가 세트와 그 채널, 클립 길이 분포를 밝히지 않고 EER을 발표하는 것은 거부한다. 도메인이 다르게 바뀌는데도 재튜닝 없이 코사인 임계값을 고정하는 경우는 표시(플래그)한다.
