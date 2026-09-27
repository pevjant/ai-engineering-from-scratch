---
name: ner-picker
description: 주어진 추출 과제에 맞는 NER 접근 방식을 고릅니다.
version: 1.0.0
phase: 5
lesson: 06
tags: [nlp, ner, extraction]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-ner-picker.md](skill-ner-picker.md)

과제 설명(도메인, 레이블 집합, 언어, 지연 시간, 데이터 양)이 주어지면 다음을 출력합니다:

1. 접근 방식. 규칙 기반 + 개체명 사전(gazetteer), CRF, BiLSTM-CRF, 또는 트랜스포머 파인튜닝.
2. 시작 모델. 이름을 밝힙니다(spaCy 모델 ID 예: `en_core_web_sm` / `en_core_web_trf`, Hugging Face 체크포인트 ID 예: `dslim/bert-base-NER`, 또는 "custom, trained from scratch").
3. 레이블링 전략. BIO, BILOU, 또는 span 기반. 한 문장으로 근거를 댑니다.
4. 평가. `seqeval`을 씁니다. 항상 개체 수준(entity-level) F1을 보고하고, 토큰 수준은 절대 쓰지 않습니다.

레이블 예시가 500개 미만인데 트랜스포머 파인튜닝을 추천하는 일은 거부합니다. 단, 사용자가 이미 사전학습된 도메인 모델(예: 의료라면 BioBERT)을 갖고 있는 경우는 예외입니다. 중첩 개체가 있으면 span 기반 또는 멀티패스 모델이 필요하다고 표시합니다. 사용자가 "프로덕션 규모"를 언급하면서 CoNLL-2003 기본 레이블을 그대로 쓰고 있다면 개체명 사전 감사(audit)를 요구합니다.
