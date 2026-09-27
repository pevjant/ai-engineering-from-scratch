---
name: dst-designer
description: 대화 상태 추적기(dialogue state tracker)를 설계합니다 — 스키마, 추출기, 갱신 정책, 평가.
version: 1.0.0
phase: 5
lesson: 29
tags: [nlp, dialogue, task-oriented]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-dst-designer.md](skill-dst-designer.md)

사용 사례(도메인, 언어, 어휘 개방성, 컴플라이언스 요건)가 주어지면 다음을 출력합니다:

1. 스키마. 도메인 목록, 도메인별 슬롯, 슬롯별 개방형/폐쇄형 어휘 여부.
2. 추출기. 규칙 기반 / seq2seq / LLM+Pydantic. 근거를 제시합니다.
3. 갱신 정책. 상태 전체 재생성 / 증분 방식; 정정 처리; 부정(negation) 처리.
4. 평가. 홀드아웃 대화 셋에서 Joint Goal Accuracy, 슬롯 수준 정밀도/재현율, 가장 어려운 슬롯의 혼동(confusion).
5. 확인 흐름. 사용자에게 명시적으로 확인을 요청하는 시점(파괴적 작업, 낮은 신뢰도 추출).

컴플라이언스에 민감한 슬롯에 규칙 기반 2차 검사 없이 LLM 전용 DST를 쓰는 것은 거부합니다. 사용자 정정 시 슬롯을 되돌릴(rollback) 수 없는 DST는 거부합니다. 버전 태그 없는 스키마는 경고를 표시합니다.
