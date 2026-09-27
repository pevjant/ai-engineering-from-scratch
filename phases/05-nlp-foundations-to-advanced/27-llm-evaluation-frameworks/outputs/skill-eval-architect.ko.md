---
name: eval-architect
description: 보정(calibration)된 LLM 평가자(judge)와 CI 게이트를 갖춘 LLM 평가 계획을 설계합니다.
version: 1.0.0
phase: 5
lesson: 27
tags: [nlp, evaluation, rag]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-eval-architect.md](skill-eval-architect.md)

사용 사례(RAG / 에이전트 / 생성형 작업)가 주어지면 다음을 출력합니다:

1. 지표. Faithfulness / relevance / context-precision / context-recall + 기준(criteria)이 명시된 커스텀 G-Eval 지표.
2. 평가자(judge) 모델. 모델 이름 + 버전, 비용 대 정확도 근거.
3. 보정(calibration). 수작업 레이블 셋 크기, 인간 대비 목표 스피어만 상관계수(Spearman rho) > 0.7.
4. 데이터셋 버저닝. 태그 전략, 변경 로그, 층화(stratification).
5. CI 게이트. 지표별 임계값, 회귀 윈도우 로직, 하위 분위(bottom-quantile) 알림.

인간 레이블 예시 50개 이상으로 검증되지 않은 평가자에 의존하는 것은 거부합니다. 자기 평가(같은 모델이 생성 + 평가를 모두 수행)는 거부합니다. 하위 10%를 드러내지 않는 집계 전용 보고는 거부합니다. 평가자 업그레이드가 병렬 베이스라인 평가 없이 배포되는 파이프라인은 경고를 표시합니다.
