---
name: skill-constitutional-rules-engine
description: 출력 제약을 위한 선언적 YAML 규칙 엔진. 심각도, 설명, 수정기 연산, 구조화된 diff 제공
version: 1.0.0
phase: 19
lesson: 86
tags: [safety, rules, constitutional]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-constitutional-rules-engine.md](skill-constitutional-rules-engine.md)

# Constitutional Rules Engine(헌법적 규칙 엔진)

헌법(constitution)은 YAML 파일입니다. 각 규칙은 `name`, `severity`(low | medium | high), `applies_when`(술어), `must`(술어), `explanation`, 선택적 `fix`를 갖습니다.

## 술어

원자적 술어:

- `contains_regex` / `not_contains_regex`
- `starts_with_regex` / `ends_with_regex`
- `max_words` / `min_words`

조합형 술어:

- `all_of: [...predicates]`
- `any_of: [...predicates]`
- `not_: predicate`

## 수정 연산

- `append_if_missing: <suffix>`
- `prepend_if_missing: <prefix>`
- `replace_regex: { pattern: <regex>, replacement: <text> }`

## 엔진 출력

`Engine.evaluate(text) -> EngineReport`는 규칙마다 `pass`, `violation`, `not_applicable` 중 하나의 `status`를 가진 `RuleResult`를 돌려줍니다. `report.violations()`는 위반만 걸러 주고, `report.max_severity()`는 존재하는 가장 나쁜 심각도를 돌려줍니다.

## 산출물

`outputs/rules_report.json`에 사례별 초안, 개정안, 구조화된 diff가 담깁니다.
