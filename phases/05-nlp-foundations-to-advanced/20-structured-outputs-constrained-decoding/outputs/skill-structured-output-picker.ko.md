---
name: structured-output-picker
description: 구조화 출력 접근법, 스키마 설계, 검증 계획 고르기.
version: 1.0.0
phase: 5
lesson: 20
tags: [nlp, llm, structured-output]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-structured-output-picker.md](skill-structured-output-picker.md)

사용 사례(벤더, 지연 시간 예산, 스키마 복잡도, 실패 허용도)가 주어지면 다음을 출력하세요:

1. 메커니즘. 네이티브 벤더 구조화 출력, Instructor 재시도, Outlines FSM, 또는 XGrammar CFG. 한 문장 근거.
2. 스키마 설계. 필드 순서(추론 먼저, 답 마지막), "unknown"을 위한 nullable 필드, enum vs 정규식, 필수 필드.
3. 실패 전략. 최대 재시도 횟수, 폴백 모델, 우아한 `null` 처리, 분포 외 입력 거부.
4. 검증 계획. 스키마 준수율(목표 100%), 의미적 유효성(LLM 심판), 필드 커버리지율, 지연 시간 p50/p99.

`answer`나 `decision`을 추론 필드보다 앞에 두는 설계는 받아들이지 마세요. 스키마 없이 맨바닥 JSON 모드를 쓰는 방안은 받아들이지 마세요. FSM 전용 라이브러리 뒤에 재귀 스키마를 두는 안은 표시하세요.
