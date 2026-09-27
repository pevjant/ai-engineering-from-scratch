---
name: qa-architect
description: QA 아키텍처, 검색 전략, 평가 계획을 고릅니다.
version: 1.0.0
phase: 5
lesson: 13
tags: [nlp, qa, rag]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-qa-architect.md](skill-qa-architect.md)

요구 사항(코퍼스 크기, 질문 유형, 사실성 제약, 지연 시간 예산)이 주어지면 다음을 출력합니다:

1. 아키텍처. 추출형, 추출형 판독기를 곁들인 RAG, 생성형 판독기를 곁들인 RAG, 또는 클로즈드북(closed-book) LLM. 한 문장으로 이유를 댑니다.
2. 검색기. 없음, BM25, 밀집(인코더 이름을 밝힘, 예: `all-MiniLM-L6-v2`), 또는 하이브리드.
3. 판독기. SQuAD 튜닝 모델(`deepset/roberta-base-squad2`), 이름을 밝힌 LLM, 또는 도메인 파인튜닝 DistilBERT.
4. 평가. 추출형 벤치마크에는 EM + F1. 프로덕션에는 답변 정확도 + 인용 정확도 + 거절 보정. 무엇을 어떻게 측정하는지 밝힙니다.

규제나 컴플라이언스에 민감한 질문에 클로즈드북 LLM 답변을 권하는 일은 거부합니다. 검색 재현율 베이스라인이 없는 QA 시스템도 거부합니다(검색기가 올바른 지문을 가져왔는지 모르면 판독기를 평가할 수 없습니다). 멀티홉(multi-hop) 추론이 필요한 질문은 HotpotQA로 학습된 시스템 같은 전용 멀티홉 검색기가 필요하다고 표시합니다.
