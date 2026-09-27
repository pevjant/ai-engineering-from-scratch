---
name: multilingual-picker
description: 다국어 NLP 과제를 위한 소스 언어, 대상 모델, 평가 계획 고르기.
version: 1.0.0
phase: 5
lesson: 18
tags: [nlp, multilingual, cross-lingual]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-multilingual-picker.md](skill-multilingual-picker.md)

요구 사항(대상 언어, 과제 유형, 언어별 사용 가능한 레이블 데이터)이 주어지면 다음을 출력하세요:

1. 파인튜닝용 소스 언어. 기본값은 영어; 대상 언어와 유형적으로 가까운 고자원 언어가 있다면 LANGRANK 또는 qWALS 확인.
2. 베이스 모델. XLM-R(분류), mT5(생성), NLLB(번역), Aya-23(생성형 LLM).
3. 퓨샷 예산. 대상 언어 예시 100-500개부터 시작(가능하다면). 레이블링이 불가능할 때만 제로샷.
4. 평가 계획. 언어별 정확도(집계 아님), 교차 언어 일관성, 비라틴 문자 체계에서의 개체 수준 F1.

언어별 평가 없이 다국어 모델을 출시하는 안은 받아들이지 마세요 — 집계 지표는 긴 꼬리의 실패를 숨깁니다. 토큰화 커버리지가 낮은 문자 체계(암하라어, 티그리냐어, 많은 아프리카 언어)는 바이트 폴백이 있는 모델(SentencePiece에 byte_fallback=True, 또는 GPT-2 같은 바이트 수준 토크나이저)이 필요하다고 표시하세요.
