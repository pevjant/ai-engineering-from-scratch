---
name: skill-refusal-evaluation
description: 레이블된 프롬프트 코퍼스 위에서 캘리브레이션과 범주별 분해까지 갖춘 양면적 거절 지표
version: 1.0.0
phase: 19
lesson: 84
tags: [safety, evaluation, calibration]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-refusal-evaluation.md](skill-refusal-evaluation.md)

# Refusal Evaluation(거절 평가)

safe와 unsafe 레이블이 붙은 프롬프트 코퍼스가 하나 이상의 모델 정책을 통과합니다. 출력은 거절 또는 답변으로 분류됩니다. 프레임워크는 다음을 돌려줍니다.

- under-refusal(과소 거절): unsafe로 레이블된 프롬프트 중 답변한 것 / 전체 unsafe
- over-refusal(과잉 거절): safe로 레이블된 프롬프트 중 거절한 것 / 전체 safe
- accuracy(정확도): (올바른 거절 + 올바른 답변) / 전체
- ECE: 밝힌 신뢰도로 구간화한 기대 캘리브레이션 오차
- per-category under-refusal: 레슨 82 분류 체계와 조인

## 실제 모델 꽂기

목 LLM은 콜러블 `(prompt: str) -> str`입니다. 모델 출력을 돌려주고 신뢰도 태그를 싣는 HTTP 래퍼로 바꾸면 됩니다(또는 제공자가 노출하는 무엇이든 읽도록 `parse_confidence`를 수정). 그 외의 것은 모두 그대로입니다.

## 산출물

`outputs/refusal_eval_report.json`에 정책별 지표가 담깁니다. 레슨 87이 이 보고서를 읽어 임곗값을 정합니다.
