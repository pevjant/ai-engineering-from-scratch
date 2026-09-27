---
name: summary-picker
description: 추출형/생성형을 고르고, 라이브러리를 정하고, 사실성 점검을 붙입니다.
version: 1.0.0
phase: 5
lesson: 12
tags: [nlp, summarization]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-summary-picker.md](skill-summary-picker.md)

과제(문서 유형, 컴플라이언스 요건, 길이, 연산 예산)가 주어지면 다음을 출력합니다:

1. 접근 방식. 추출형 또는 생성형(abstractive). 이유를 한 문장으로 설명합니다.
2. 시작 모델/라이브러리. 이름을 밝힙니다. `sumy.TextRankSummarizer`, `facebook/bart-large-cnn`, `google/pegasus-pubmed`, 또는 LLM 프롬프트.
3. 평가 계획. ROUGE-1, ROUGE-2, ROUGE-L(어형 분석(stemming)을 켠 `rouge-score` 사용). 생성형이라면 사실성 점검도 추가.
4. 파고들 실패 모드 하나. 개체 바꿔치기(entity swap)가 생성형 뉴스 요약에서 가장 흔합니다. 원문 개체가 요약에 나타나지 않는 샘플을 표시합니다.

의료, 법률, 금융, 규제 대상 콘텐츠에 사실성 게이트 없이 생성형 요약을 추천하는 일은 거부합니다. 모델의 컨텍스트 윈도우를 넘는 입력은 단순 잘림이 아니라 청크 단위 맵-리듀스(map-reduce) 요약이 필요하다고 표시합니다.
