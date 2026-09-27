---
name: entity-linker
description: 개체 연결(entity linking) 파이프라인 설계 — 지식 베이스, 후보 생성기, 개체 판별기, 평가.
version: 1.0.0
phase: 5
lesson: 25
tags: [nlp, entity-linking, knowledge-graph]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-entity-linker.md](skill-entity-linker.md)

사용 사례(도메인 KB, 언어, 처리량, 지연 시간 예산)가 주어지면 다음을 출력합니다:

1. 지식 베이스. Wikidata / Wikipedia / 자체 KB. 버전 날짜. 갱신 주기.
2. 후보 생성기. 별칭 인덱스(alias-index), 임베딩, 또는 하이브리드. 목표 mention recall @ K.
3. 개체 판별기(disambiguator). 사전 확률 + 문맥, 임베딩 기반, 생성형, 또는 LLM 프롬프트.
4. NIL 전략. 최고 점수에 임계값 적용, 분류기, 또는 명시적 NIL 후보.
5. 평가. 홀드아웃 셋에서 mention recall @ 30, top-1 정확도, NIL 탐지 F1.

mention-recall 베이스라인 없는 EL 파이프라인은 거부합니다(후보 생성이 올바른 개체를 찾아냈는지 모르면 개체 판별기를 평가할 수 없습니다). 유효한 KB id로 출력을 제약하지 않는 LLM 프롬프트 방식 EL 파이프라인은 거부합니다. 도메인 파인튜닝 없이 인기 편향이 소수 개체(예: 이름 충돌)에 영향을 주는 시스템은 경고를 표시합니다.
