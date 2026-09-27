---
name: topic-picker
description: 코퍼스에 LDA 또는 BERTopic을 고르기. 라이브러리, 설정값, 평가 방법까지 명시.
version: 1.0.0
phase: 5
lesson: 15
tags: [nlp, topic-modeling]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-topic-picker.md](skill-topic-picker.md)

코퍼스 설명(문서 수, 평균 길이, 도메인, 언어, 컴퓨팅 예산)이 주어지면 다음을 출력하세요:

1. 알고리즘. LDA / NMF / BERTopic / Top2Vec / FASTopic. 한 문장 근거.
2. 설정. 토픽 수(~sqrt(n_docs)부터 시작), `min_df` / `max_df` 필터, 신경망 기반 접근의 임베딩 모델.
3. 평가. `gensim.models.CoherenceModel`을 통한 토픽 일관성(c_v), 토픽 다양성, 그리고 20개 표본의 사람이 읽는 검토.
4. 점검할 실패 양상. LDA는 불용어와 빈번한 단어를 빨아들이는 "정크 토픽". BERTopic은 모호한 문서들을 삼키는 -1 이상치 클러스터.

임베딩 모델의 컨텍스트 윈도우보다 긴 문서에 청킹 전략 없이 BERTopic을 쓰는 안은 받아들이지 마세요. 아주 짧은 텍스트(10토큰 미만의 트윗, 리뷰)에 LDA를 쓰면 일관성이 무너지므로 받아들이지 마세요. n_topics을 5 미만이나 200 초과로 정하는 안은 실제 데이터에서 틀렸을 가능성이 높다고 표시하세요.
