---
name: skill-segmentation-mask-inspector
description: 클래스 분포, 예측 마스크 통계, 과소 예측되거나 경계가 번지기 쉬운 클래스를 보고
version: 1.0.0
phase: 4
lesson: 7
tags: [computer-vision, segmentation, debugging, evaluation]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-segmentation-mask-inspector.md](skill-segmentation-mask-inspector.md)

# 세그멘테이션 마스크 검사관 (Segmentation Mask Inspector)

"손실이 내려갔다"와 "마스크가 실제로 그럴듯하다" 사이의 간격을 위한 진단 도구입니다.

## 언제 사용하나

- 학습이 끝난 직후, mIoU는 괜찮아 보이는데 눈으로 보면 그렇지 않을 때.
- 배포 전: 예측의 클래스 균형을 정답과 대조할 때.
- 큰 물체의 클래스별 IoU는 높은데 작은 물체는 낮을 때.
- 픽셀 수가 작아서 IoU에는 드러나지 않는 경계 아티팩트를 디버깅할 때.

## 입력

- `preds`: 예측 클래스 ID의 (N, H, W) 텐서.
- `targets`: 정답 클래스 ID의 (N, H, W) 텐서.
- `num_classes`: 정수.
- 선택 사항 `class_names`: C개 문자열 목록.

## 단계

1. **클래스별 픽셀 히스토그램.** `preds`와 `targets`의 클래스별 픽셀 비율을 계산합니다. `|pred% - gt%| / max(gt%, 1e-6) > 0.30`(상대 편차 30% 초과)인 클래스는 표시합니다. 정답에 없는 클래스(`gt% == 0`)는 예측 비율이 `0.3`을 넘으면 바로 표시합니다.

2. **클래스별 IoU**와 **클래스별 경계 F1**. 경계 F1은 각 마스크를 3픽셀 팽창(dilate)하고 교집합을 내어 점수를 매깁니다. IoU는 0.7을 넘지만 경계 F1이 0.5 미만인 클래스는 경계를 번지고 있는 것입니다.

3. **소형 물체 recall.** 모든 정답 연결 컴포넌트(connected component)를 크기 버킷으로 나눕니다(tiny < 100 px, small < 1,000 px, medium < 10,000 px, large >= 10,000 px). 버킷별·클래스별 recall을 보고합니다. 소형 물체 recall이 0.3 미만인데 대형 물체 recall은 0.9를 넘으면 해상도 / 수용 영역 문제입니다.

4. **혼동 쌍.** 각 클래스가 가장 자주 헷갈리는 클래스(그 클래스의 정답 마스크 안에서 가장 흔한 잘못된 예측 클래스)를 찾습니다. 상위 3쌍을 보고합니다.

5. **포화 검사(`preds`만이 아니라 `probs` 또는 `logits` 필요).** 호출자가 픽셀별 확률 분포 `probs: (N, C, H, W)`를 넘겨주면, 클래스별로 `probs.max(dim=1) > 0.99`인 픽셀 비율을 계산합니다. 높은 포화(어떤 클래스 픽셀의 0.9 초과)는 과신의 신호입니다 — 레이블 스무딩이나 보정(calibration) 후보입니다. argmax만 거친 `preds`만 있다면 이 단계를 건너뛰고 리포트에 그 사실을 적습니다.

## 리포트 형식

```
[mask-inspector]
  classes: C

[class distribution]
  name       gt %    pred %   delta
  ...

[metrics]
  class       IoU     bF1    recall_tiny  recall_small  recall_medium  recall_large
  ...

[confusion pairs]
  class A confused with class B: <N> pixels (most common)
  class B confused with class A: <N> pixels
  ...

[verdict]
  most impactful issue: <한 문장>
```

## 규칙

- 클래스 행을 gt 픽셀 비율 내림차순으로 정렬해 가장 빈번한 클래스가 먼저 오게 합니다.
- IoU < 0.4 또는 경계 F1 < 0.3인 클래스는 `critical`로 표시합니다.
- 소형 물체 recall이 지배적 실패라면 다음을 권합니다: 더 높은 해상도 학습, 마지막 인코더 스테이지에서 더 작은 stride, 또는 특성 피라미드 디코더.
- 경계 F1이 지배적 실패라면 다음을 권합니다: 경계 인지 손실(Lovasz 또는 BoundaryLoss), 수평 뒤집기 TTA, stride 없는 디코더.
- 클래스 인덱스만 식별자로 출력하지 않습니다; `class_names`가 주어졌다면 모든 행에 사용합니다.
