---
name: retrieval-picker
description: 주어진 코퍼스와 쿼리 패턴에 맞는 검색 스택을 고르기.
version: 1.0.0
phase: 5
lesson: 14
tags: [nlp, retrieval, rag, search]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-retrieval-picker.md](skill-retrieval-picker.md)

요구 사항(코퍼스 크기, 쿼리 패턴, 지연 시간 예산, 품질 기준, 인프라 제약)이 주어지면 다음을 출력하세요:

1. 스택. BM25만, dense만, 하이브리드(BM25 + dense + RRF), 하이브리드 + 크로스 인코더 리랭크, 또는 3-웨이(BM25 + dense + learned-sparse).
2. Dense 인코더. 구체적인 모델 이름을 말하세요(`all-MiniLM-L6-v2`, `bge-large-en-v1.5`, `e5-large-v2`, `paraphrase-multilingual-MiniLM-L12-v2`). 언어, 도메인, 컨텍스트 길이에 맞춥니다.
3. 리랭커. 사용한다면 크로스 인코더 모델 이름을 말하세요(`cross-encoder/ms-marco-MiniLM-L-6-v2`, `BAAI/bge-reranker-large`). 상위 30개 기준으로 지연 시간이 약 30-100ms 추가된다는 점을 표시하세요.
4. 평가 계획. Recall@10이 리트리버의 1차 지표입니다. 다중 정답에는 MRR. 먼저 베이스라인을 세우고, 증분 개선은 그 기준으로 측정합니다.

고유명사, 에러 코드, 제품 SKU가 섞인 코퍼스에는, dense가 정확한 일치를 잘 처리한다는 근거를 사용자가 제시하지 않는 한 dense-only를 추천하지 마세요. 최종 상위 5개가 사용자의 답변을 결정하는 고위험 검색(법률, 의료)에서는 리랭킹을 건너뛰는 방안을 받아들이지 마세요.
