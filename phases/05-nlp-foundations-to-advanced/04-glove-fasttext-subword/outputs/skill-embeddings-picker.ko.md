---
name: skill-embeddings-picker
description: 새 언어 모델이나 텍스트 파이프라인을 위한 토큰화 방식을 고른다.
version: 1.0.0
phase: 5
lesson: 04
tags: [nlp, tokenization, embeddings]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-embeddings-picker.md](skill-embeddings-picker.md)

작업과 데이터셋 설명이 주어지면 다음을 출력합니다:

1. 토큰화 전략(단어 수준, BPE, WordPiece, SentencePiece, 바이트 수준 BPE). 한 문장 근거.
2. 목표 어휘 크기. 영어 전용 LM: 32k. 다국어: 64k-100k. 코드: 50k-100k.
3. 정확한 학습 명령이 들어간 라이브러리 호출. 라이브러리 이름을 적는다(Hugging Face `tokenizers`, `sentencepiece`). 인자를 인용한다.
4. 재현성 함정 하나. 토크나이저-모델 불일치는 가장 흔한 조용한 프로덕션 버그다. 어떤 토크나이저가 어떤 사전학습 체크포인트와 짝을 이루는지 이름으로 밝히고, 교체하지 말라고 경고한다.

사용자가 사전학습 LLM을 파인튜닝하는 중이라면 커스텀 토크나이저 학습을 권하지 않는다(파인튜닝은 반드시 사전학습 토크나이저를 써야 한다). 프로덕션 추론 경로에는 단어 수준 토큰화를 권하지 않는다. 영어가 아니거나 다중 문자 체계인 말뭉치는 바이트 폴백이 있는 SentencePiece가 필요하다고 표시한다.
