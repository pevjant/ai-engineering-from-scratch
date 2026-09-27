---
name: embedding-picker
description: 주어진 코퍼스와 배포 환경에 맞는 임베딩 모델, 차원, 검색 모드 고르기.
version: 1.0.0
phase: 5
lesson: 22
tags: [nlp, embeddings, retrieval]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-embedding-picker.md](skill-embedding-picker.md)

코퍼스(크기, 언어, 도메인, 평균 길이), 배포 대상(클라우드 / 엣지 / 온프레미스), 지연 시간 예산, 저장 예산이 주어지면 다음을 출력하세요:

1. 모델. 이름이 명시된 체크포인트 또는 API. 한 문장 근거.
2. 차원. 전체 / Matryoshka 절단 / int8 양자화. 저장 예산에 근거를 댈 것.
3. 모드. Dense / 스파스 / 멀티 벡터 / 하이브리드. 근거.
4. 모델 카드가 요구한다면 쿼리 접두어 / 템플릿.
5. 평가 계획. 도메인과 관련된 MTEB 과제 + nDCG@10을 쓰는 보류(held-out) 도메인 평가.

도메인 검증 없이 Matryoshka를 64차원 미만으로 자르는 추천은 받아들이지 마세요. 1만 구절 미만 코퍼스에 ColBERTv2를 추천하지 마세요(오버헤드가 정당화되지 않음). 512토큰 윈도우 모델에 긴 문서 코퍼스(8천 토큰 초과)를 보내는 구성은 표시하세요.
