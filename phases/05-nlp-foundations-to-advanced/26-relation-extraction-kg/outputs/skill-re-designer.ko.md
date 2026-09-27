---
name: re-designer
description: 출처 추적(provenance)과 정규화(canonicalization)를 갖춘 관계 추출 파이프라인을 설계합니다.
version: 1.0.0
phase: 5
lesson: 26
tags: [nlp, relation-extraction, knowledge-graph]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-re-designer.md](skill-re-designer.md)

코퍼스(도메인, 언어, 처리량)와 하위 용도(KG-RAG, 분석, 컴플라이언스)가 주어지면 다음을 출력합니다:

1. 추출기. 패턴 기반 / 지도 학습 / LLM / AEVS 하이브리드. 정밀도 대 재현율 목표에 근거를 둡니다.
2. 온톨로지. 닫힌 속성 목록(Wikidata / 도메인) 또는 정규화 단계를 거치는 오픈 IE.
3. 출처 추적(provenance). 모든 트리플에 원본 문자 범위(char-span) + 문서 id를 첨부. 감사(audit)를 위해 타협 불가.
4. 병합 전략. 정규 개체 id + 관계 id + 시간 한정자(qualifier); 중복 제거 정책.
5. 평가. 수작업 레이블 트리플 200개에서 정밀도 / 재현율 + LLM 추출 샘플의 환각 비율.

span 검증(원본 출처) 없는 LLM 기반 RE 파이프라인은 거부합니다. 정규화 없이 오픈 IE 결과가 프로덕션(운영 환경) 그래프로 흘러 들어가는 것은 거부합니다. 시간 한정 관계(고용주, 배우자, 직위)에 시간 한정자가 없는 파이프라인은 경고를 표시합니다.
