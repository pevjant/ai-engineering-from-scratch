---
name: bert-finetuner
description: 새로운 분류, 추출, 검색 과제를 위한 BERT 파인튜닝의 범위를 잡는다.
version: 1.0.0
phase: 7
lesson: 6
tags: [bert, fine-tuning, nlp]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-bert-finetuner.md](skill-bert-finetuner.md)

다운스트림 과제(분류 / NER / 검색 / 리랭킹 / NLI), 레이블 데이터 크기, 배포 제약(지연 시간, 기기)이 주어지면 다음을 출력합니다:

1. 백본 선택. 모델 이름(ModernBERT-base / large, DeBERTa-v3, multilingual-e5 등)과 한 문장 짜리 이유. 8K 이하 컨텍스트가 필요한 영어 과제는 ModernBERT 선호.
2. 헤드 명세. 분류: `[CLS]` → dropout → linear(num_classes). NER: 토큰별 linear + CRF 선택적. 검색: 평균 풀링 + 대조 손실.
3. 학습 레시피. 옵티마이저(AdamW, lr은 보통 2e-5), 워밍업 비율(6-10%), 에포크(3-5), 배치 크기, fp16/bf16.
4. 평가 계획. 과제에 맞는 지표(분류는 accuracy + F1, NER은 개체 수준 F1, 검색은 MRR/NDCG). 홀드아웃(held-out) 분할 크기.
5. 실패 양상 점검. 구체적인 위험 하나: 레이블 누수, 클래스 불균형, 컨텍스트 절단, 사전 학습 코퍼스와 파인튜닝 코퍼스 간 토크나이저 불일치.

생성형 출력(텍스트 생성)을 위한 BERT 파인튜닝은 거부합니다 — 디코더 전용을 대신 추천합니다. 소수 클래스가 10% 미만인데 클래스 계층화 평가 없이 파인튜닝을 출시하는 것도 거부합니다. 레이블 예제가 1,000개 미만인데 백본 전체를 풀어 헤치는 파인튜닝은 과적합 가능성이 높다고 표시합니다.
