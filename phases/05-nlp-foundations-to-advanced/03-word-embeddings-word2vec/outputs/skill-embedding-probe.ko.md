---
name: embedding-probe
description: 학습된 word2vec 모델을 검사한다. 유추를 돌리고, 이웃을 찾고, 품질을 진단한다.
version: 1.0.0
phase: 5
lesson: 03
tags: [nlp, embeddings, debugging]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-embedding-probe.md](skill-embedding-probe.md)

당신은 학습된 단어 임베딩을 검사(probe)해 제대로 동작하는지 확인합니다. `gensim.models.KeyedVectors` 객체와 어휘가 주어지면 다음을 실행합니다:

1. 정통 유추 테스트 세 개. `king : man :: queen : woman`. `paris : france :: tokyo : japan`. `walking : walked :: swimming : ?`. 최상위(top-1) 결과와 코사인 값을 보고한다.
2. 사용자가 제공한 도메인 특화 단어로 최근접 이웃 테스트 다섯 개. 코사인과 함께 상위 5개 이웃을 출력한다.
3. 대칭성 검사 하나. `similarity(a, b) == similarity(b, a)`가 부동소수점 정밀도 수준에서 성립하는지 확인한다.
4. 퇴화(degenerate) 검사 하나. 임베딩의 노름(norm)이 0.01 미만이거나 100 초과인 것이 있으면 학습 버그다. 표시한다.

유추 정확도만으로 모델이 좋다고 선언하지 않는다. 유추 벤치마크는 속이기 쉽고 하위 과제로 전이되지 않는다. 고유(intrinsic) 평가와 하위 과제 평가를 함께 권한다.
