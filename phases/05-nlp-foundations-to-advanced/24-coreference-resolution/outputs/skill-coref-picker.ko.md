---
name: coref-picker
description: 상호 참조 해소(coreference resolution) 접근 방식, 평가 계획, 통합 전략을 선택합니다.
version: 1.0.0
phase: 5
lesson: 24
tags: [nlp, coref, information-extraction]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-coref-picker.md](skill-coref-picker.md)

사용 사례(단일 문서 / 다중 문서, 도메인, 언어)가 주어지면 다음을 출력합니다:

1. 접근 방식. 규칙 기반 / 신경망 span 기반 / LLM 프롬프트 / 하이브리드. 한 문장 근거.
2. 모델. 신경망 방식이라면 체크포인트 이름을 명시.
3. 통합. 처리 순서: 토큰화(tokenize) → NER → 상호 참조 해소(coref) → 하위 작업.
4. 평가. 홀드아웃 셋에서 CoNLL F1 (MUC + B³ + CEAF-φ4 평균) + 문서 20개 수동 클러스터 검토.

슬라이딩 윈도우 병합 없이 2,000토큰을 넘는 문서에 LLM 전용 coref를 쓰는 것은 거부합니다. 멘션(mention) 수준 정밀도-재현율 보고서 없이 coref를 돌리는 파이프라인은 거부합니다. 인구 통계적으로 다양한 텍스트에 배포되는 성별 휴리스틱 시스템은 경고를 표시합니다.
