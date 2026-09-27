---
name: skill-content-classifier-integration
description: 하나의 심각도 라우터 뒤에 놓인 세 가지 출력 쪽 분류기(독성, PII, 지시 유출). block, redact, warn, log 행동 제공
version: 1.0.0
phase: 19
lesson: 85
tags: [safety, classifier, output-filter]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-content-classifier-integration.md](skill-content-classifier-integration.md)

# Content Classifier Integration(콘텐츠 분류기 통합)

분류기 셋, 라우터 하나, 행동 넷입니다.

## 판정 구조

```text
ClassifierVerdict
  name: str
  severity: none | low | medium | high
  score: float in [0, 1]
  findings: list[str]
```

## 행동 표

| 심각도 | 행동 | 효과 |
|---|---|---|
| high | block | 출력이 정책 거절로 대체됨 |
| medium | redact | 분류기별 레닥터(redactor)가 순서대로 적용됨 |
| low | warn | 출력에 부드러운 안내문을 덧붙여 출하 |
| none | log | 출력은 그대로 출하, 판정만 기록 |

## 분류기별 동작

- toxicity - 공백 경계 매칭과 작은 좌측 윈도우 부정 검사를 곁들인 괴롭힘 용어 목록. 걸린 부분은 `[redacted-language]`로 가림
- pii - 이메일, 전화번호, SSN, Luhn 검증을 통과한 카드, IPv4. SSN과 카드에서는 심각도가 상승. 각 형태를 태그로 가림
- instruction-leakage - 알려진 시스템 프롬프트와의 트라이그램 코사인. 겹침에 비례해 심각도 상승. 시스템 프롬프트 첫 줄을 가림

## 산출물

`outputs/classifier_report.json`에 사례별 행동 동사, 심각도, 가려진 출력, 전체 판정 목록이 담깁니다.
