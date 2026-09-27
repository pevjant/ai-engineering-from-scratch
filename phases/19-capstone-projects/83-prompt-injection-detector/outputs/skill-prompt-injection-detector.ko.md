---
name: skill-prompt-injection-detector
description: 모든 프롬프트에 대해 범주와 신뢰도를 돌려주는 계층형 탐지기 파이프라인. 측정 가능한 정밀도와 재현율 제공
version: 1.0.0
phase: 19
lesson: 83
tags: [safety, detector, prompt-injection]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-prompt-injection-detector.md](skill-prompt-injection-detector.md)

# Prompt Injection Detector(프롬프트 인젝션 탐지기)

여기서 탐지기란 프롬프트를 판정(verdict)으로 바꾸는 함수입니다. 판정은 레슨 82 분류 체계에서 온 범주 하나와 [0, 1] 범위의 신뢰도를 담습니다.

## 파이프라인

1. 정규화(Normalize) - 너비 0 문자 제거, 호모글리프 되돌리기, base64/hex 디코딩, 리트 스피치 숫자 접기, 흔한 단어 정합성 검사를 곁들인 rot13 시도.
2. 부분 문자열 규칙 - `ignore previous`, `from now on you are`, `decode this base64` 같은 손으로 쓴 바늘(needle) 패턴들.
3. 정규식 규칙 - `\bignor\w*\s+(all|prior|previous|earlier)\b` 같은 토큰 수준 패턴들.

집계는 범주별 최대 점수를 유지하고, 가장 큰 점수의 범주를 돌려줍니다. 아무것도 발동하지 않으면 `benign`을 돌려줍니다.

## 규칙 추가하기

`code/rules.py`를 수정하세요. 규칙은 `name`, `category`(여섯 분류 범주 중 하나), `score`(0부터 1까지의 실수), 그리고 `substring`이나 `regex` 중 하나를 가진 딕셔너리입니다. `main.py`를 다시 실행해서 범주별 정밀도와 재현율에 어떤 영향을 주는지 확인하세요.

## 산출물

`outputs/detector_report.json`이 범주별 지표 파일입니다. 레슨 87의 종단 간 게이트가 이것을 읽어 신뢰도 임곗값을 정합니다.
