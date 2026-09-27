---
name: skill-bpe-vs-wordpiece
description: 주어진 코퍼스와 배포 대상에 맞는 토크나이저 알고리즘, 어휘 크기, 라이브러리 고르기.
version: 1.0.0
phase: 5
lesson: 19
tags: [nlp, tokenization]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-bpe-vs-wordpiece.md](skill-bpe-vs-wordpiece.md)

코퍼스(크기, 언어, 도메인)와 배포 대상(밑바닥부터 학습 / 파인튜닝 / API 호환 추론)이 주어지면 다음을 출력하세요:

1. 알고리즘. BPE, Unigram, 또는 WordPiece. 한 문장 근거.
2. 라이브러리. SentencePiece, HF Tokenizers, 또는 tiktoken. 근거.
3. 어휘 크기. 가장 가까운 1k 단위로 반올림. 모델 크기와 언어 커버리지에 근거를 댈 것.
4. 커버리지 설정. `character_coverage`, `byte_fallback`, 특수 토큰 목록.
5. 검증 계획. 보류(held-out) 셋의 단어당 평균 토큰 수, OOV 비율, 압축 비율, 왕복 디코딩 일치 여부.

희귀 문자 체계 콘텐츠가 섞인 코퍼스에는 character-coverage 0.995 미만 토크나이저를 학습하지 마세요. CI에 고정된 `tokenizer.json` 해시 검사 없이 어휘를 출시하지 마세요. 16k 미만 어휘의 단일 언어 토크나이저는 스펙 미달일 가능성이 높다고 표시하세요.
