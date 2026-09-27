---
name: grammar-pipeline
description: 다운스트림 NLP 과제를 위한 고전 품사 + 의존 분석 파이프라인을 설계합니다.
version: 1.0.0
phase: 5
lesson: 07
tags: [nlp, pos, parsing]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-grammar-pipeline.md](skill-grammar-pipeline.md)

다운스트림 과제(정보 추출, 재작성 검증, 쿼리 분해, 표제어 추출)가 주어지면 다음을 출력합니다:

1. 태그 집합. 영어 전용 레거시 파이프라인에는 Penn Treebank, 다국어나 교차 언어에는 Universal Dependencies.
2. 라이브러리. 대부분의 프로덕션(운영 환경)에는 spaCy(`en_core_web_sm` / `_lg` / `_trf`), 학술급 다국어에는 stanza, 최고 UD 정확도에는 trankit.
3. 통합 코드 조각. 라이브러리를 호출하고 `.pos_`, `.dep_`, `.head`를 소비하는 3~5줄.
4. 테스트할 실패 모드. 명사-동사 중의성(`saw`, `book`, `can`)과 전치사구(PP) 부착 중의성이 고전적인 함정입니다. 출력 20개를 표본으로 뽑아 직접 눈으로 확인합니다.

자체 파서를 만들라는 추천은 거부합니다. 파서를 처음부터 만드는 일은 연구 프로젝트지 응용 과제가 아닙니다. 대소문자 변형을 처리하지 않고 품사 태그를 소비하는 파이프라인은 취약하다고 표시합니다.
