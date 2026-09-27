---
name: positional-encoding-picker
description: 컨텍스트 길이와 학습 예산이 주어지면 위치 인코딩(RoPE, ALiBi, 사인 기반)과 스케일링 전략을 고른다.
version: 1.0.0
phase: 7
lesson: 4
tags: [transformers, positional-encoding, rope, alibi]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-positional-encoding-picker.md](skill-positional-encoding-picker.md)

트랜스포머 명세(추론 시 목표 컨텍스트 길이, 학습된 컨텍스트 길이, 외삽 요구 사항, 토큰 단위 파인튜닝 예산)가 주어지면 다음을 출력합니다:

1. 기본 인코딩. 다음 중 하나: RoPE, ALiBi, 사인 기반, 학습형 절대. 한 문장 짜리 이유.
2. 하이퍼파라미터. RoPE라면: `base` 값, 짝수 분할을 위한 `d_head` 요구 조건. ALiBi라면: 기울기 공식. 사인 기반이라면: `max_len`.
3. 확장 전략. 목표가 학습 길이보다 크다면: NTK-aware 스케일링 팩터, YaRN 설정, LongRoPE 명세, 또는 위치 보간 비율. 파인튜닝 토큰 예산도 명시합니다.
4. 테스트 계획. 최대 컨텍스트에서의 NIAH(바늘 찾기, needle-in-a-haystack) 통과율 목표, 학습 길이 베이스라인 대비 퍼플렉시티 X 이내.
5. 폴백(fallback). 장기 컨텍스트 평가가 실패하면: 더 큰 `base`로 재학습, ALiBi로 전환, 또는 배포 컨텍스트 길이 제한.

2026년 새 모델에 사인 기반이나 학습형 절대 인코딩을 추천하는 일은 거부합니다 — 외삽이 안 될뿐더러 모든 현대 스택이 RoPE나 ALiBi를 가정합니다. 파인튜닝 단계 없이 RoPE를 학습 길이의 8배를 넘게 스케일하는 것도 거부합니다. 배포 길이 전체에서 NIAH 테스트를 돌려 보지 않은 채 장기 컨텍스트 설정을 출시하는 일 역시 거부합니다.
