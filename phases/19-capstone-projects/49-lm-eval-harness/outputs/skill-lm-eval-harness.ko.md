---
name: lm-eval-harness
description: JSONL 과제 명세, 다섯 가지 지표, 교체 가능한 어댑터, 리더보드 JSON 출력을 갖춘 최소 언어 모델 평가 하네스.
version: 1.0.0
phase: 19
lesson: 49
tags: [evaluation, metrics, leaderboard, harness]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-lm-eval-harness.md](skill-lm-eval-harness.md)

## 언제 사용하나

두 모델, 두 체크포인트, 두 프롬프트 템플릿을 고정된 과제 세트에 대해 비교할 때 사용합니다. 출시하는 것 중 시간이 지나도 계속 모니터링해야 하는 모든 것에 해당합니다.

## 과제 명세

예제마다 JSONL 한 줄:

```json
{"id": "ex-001", "prompt": "...", "targets": ["..."], "metric": "exact_match", "extras": {}}
```

한 파일 안의 모든 예제는 같은 지표를 공유합니다. 파일 이름이 곧 과제 이름입니다.

## 지표

| 지표 | 서명 | 용도 |
|--------|-----------|---------|
| exact_match | 소문자 + 공백 정규화 후 동등 비교 | 산술, 팩토이드형 답변 |
| substring_contains | 정규화한 예측 안에 대상이 나타나야 함 | 앵커 단어가 있는 자유 형식 생성 |
| multiple_choice | 첫 글자 일치 | A/B/C/D 스타일 질문 |
| rouge_l | 토큰화한 텍스트에 대한 LCS F1 | 요약, 바꿔 쓰기 |
| code_exec | 예측의 `f`를 io_pairs에 대해 실행, 일치 개수 집계 | 코드 생성 |

모든 지표는 [0.0, 1.0] 범위의 float를 반환합니다. 과제 점수는 그 평균입니다.

## 어댑터

```python
class Adapter(Protocol):
    name: str
    def generate(self, prompts: list[str]) -> list[str]: ...
```

어댑터가 유일한 모델 고유 코드입니다.

## 리더보드 JSON

스키마 문자열, 타임스탬프, 과제별 점수와 지연 시간, 전체 평균을 담습니다. 실행 간 비교 시에는 예제별 레코드를 포함하세요. 그래야 예측 수준의 성능 하락(regression)이 보입니다.

## 실패 모드

- 지표가 [0, 1] 밖의 값을 반환하는 경우: 전체 점수가 해석 불가능해집니다.
- 한 과제 파일에 여러 지표를 섞는 경우: 단언문이 발동합니다. 파일당 지표 하나를 유지하세요.
- 제한된 네임스페이스 없이 code_exec를 쓰는 경우: 임의 코드 실행 위험이 있습니다.
- 스키마 문자열이 없는 경우: 형식이 진화할 때 다운스트림 대시보드가 깨집니다.
