---
name: long-context-eval
description: 주어진 모델과 사용 사례를 위한 롱 컨텍스트(long-context) 평가 배터리를 설계합니다.
version: 1.0.0
phase: 5
lesson: 28
tags: [nlp, long-context, evaluation]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-long-context-eval.md](skill-long-context-eval.md)

대상 모델, 목표 컨텍스트 길이, 사용 사례가 주어지면 다음을 출력합니다:

1. 테스트. NIAH 깊이 × 길이 그리드; RULER 멀티홉; 커스텀 도메인 작업.
2. 샘플링. 각 길이에서 깊이 0, 0.25, 0.5, 0.75, 1.0.
3. 지표. 검색 통과율; 추론 통과율; time-to-first-token; 질의당 비용.
4. 컷오프. 유효 검색 길이(통과율 90%)와 유효 추론 길이(통과율 70%). 둘 다 보고합니다.
5. 회귀. 고정된 테스트 하네스, 모델 업그레이드 때마다 재실행, 변화량(delta) 보고.

모델 카드만 믿고 컨텍스트 윈도우를 신뢰하는 것은 거부합니다. 멀티홉 작업에 NIAH 전용 평가를 쓰는 것은 거부합니다. 벤더가 자체 보고한 롱 컨텍스트 점수를 독립적 근거로 받아들이는 것은 거부합니다.
