---
name: skill-classification-diagnostics
description: 혼동 행렬과 클래스 이름이 주어지면 클래스별 실패를 끌어내고 가장 영향 큰 수정 하나를 제안
version: 1.0.0
phase: 4
lesson: 4
tags: [computer-vision, classification, evaluation, debugging]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-classification-diagnostics.md](skill-classification-diagnostics.md)

# 분류 진단 (Classification Diagnostics)

혼동 행렬을 위한 읽기 렌즈입니다. 집계 정확도는 "분류기가 동작한다"만 알려 줍니다. 혼동 행렬은 *아직 무엇을 모르는지*를 알려 줍니다.

## 언제 사용하나

- 학습된 분류기의 검증 성능을 처음 들여다볼 때.
- 다음 학습 실행 전에 무엇을 바꿀지 결정할 때.
- 모델 출시 전: 중요한 클래스가 조용히 실패하지 않는지 확인할 때.
- 전체 정확도가 1포인트 떨어진 프로덕션 회귀를 디버깅하며 그 이유를 알아야 할 때.

## 입력

- `cm`: CxC 혼동 행렬(행 = 진짜, 열 = 예측).
- `labels`: 같은 순서의 C개 클래스 이름 목록.
- 선택 사항 `class_priors`: 클래스별 학습 빈도(기본값은 `cm`의 행 합).

## 단계

1. **클래스별 지표 계산.** 0으로 나누는 경우는 그 클래스에서 해당 지표가 정의되지 않은 것으로 취급해 `n/a`로 보고합니다; 조용히 0으로 대체하지 않습니다.
   - precision_i = cm[i,i] / sum(cm[:, i])   (그 클래스가 한 번도 예측되지 않았으면 정의되지 않음)
   - recall_i    = cm[i,i] / sum(cm[i, :])   (그 클래스에 정답 샘플이 없으면 정의되지 않음)
   - f1_i        = 2 * p * r / (p + r)        (둘 중 하나라도 정의되지 않으면 정의되지 않음)

2. **최악의 클래스 최대 셋을 F1 기준으로 순위 매기기.** 혼동 행렬의 클래스가 셋보다 적으면 존재하는 만큼만 순위를 매깁니다. 모든 지표가 정의되지 않는 클래스는 제외합니다.

3. **행별 최대 대각선 밖 셀 찾기** — 이 클래스에서 가장 자주 가져가는 클래스 하나. `진짜 -> 예측` 형태로 보고합니다.

4. **최악 클래스 각각의 실패 양상 분류.** 레이블이 재현 가능하도록 다음 정량 기준을 사용합니다:
   - `ambiguity` — 다른 클래스와 쌍방향 혼동: `cm[i,j] / sum(cm[i, :]) >= 0.15`와 `cm[j,i] / sum(cm[j, :]) >= 0.15`가 둘 다 참.
   - `imbalance` — 그 클래스의 학습 개수가 최다 혼동 상대의 `< 0.5x`.
   - `label_noise` — `|precision_i - recall_i| >= 0.2`이고 불균형/모호 경로에 해당하지 않음.
   - `systematic` — 이 클래스 오차의 0.2 이상 몫을 차지하는 혼동 상대가 하나도 없음; 오차가 셋 이상의 다른 클래스에 흩어져 있음.

5. **가장 영향 큰 다음 행동 하나를 추천**:
   - `ambiguity` -> 구분적(discriminative) 예시를 수집·합성하고, 구별 특징을 보존하는 목표 증강을 추가.
   - `imbalance` -> 소수 클래스를 오버샘플링하거나 클래스 가중 손실 적용.
   - `label_noise` -> 그 클래스의 층화 표본(stratified sample)을 감사; 다른 어떤 변경보다 먼저 잘못된 레이블부터 수정.
   - `systematic` -> 해당 클래스의 데이터를 늘리거나 이 클래스 손실에 더 높은 가중을 둔 파인튜닝.

## 리포트

```
[diagnostics]
  aggregate accuracy: X.XX
  macro F1:           X.XX

[top-3 worst classes]
  1. class <이름>  F1 = X.XX  prec = X.XX  rec = X.XX
     top confusion: <이름> -> <다른 클래스>  (N건)
     failure mode:  ambiguity | imbalance | label_noise | systematic
     action:        <한 문장>

  2. ...
  3. ...

[recommendation]
  single biggest lever: <클래스와 수정책을 이름 짓는 한 문장>
```

## 규칙

- 최대 세 클래스까지만 반환합니다. 더 많으면 신호가 묻힙니다.
- 최악 클래스마다 지배적인 혼동 상대를 이름으로 말합니다; "여러 클래스와 혼동" 식으로 요약하지 않습니다.
- 모든 추천을 혼동 행렬 증거에 근거시킵니다. 클래스를 지정하지 않은 뭉뚱그린 "데이터를 더 모으세요"는 금지.
- 정밀도와 재현율이 0.2 이상 어긋나면 항상 레이블 노이즈를 후보로 표시합니다 — 학습 후에는 진짜 클래스의 P와 R이 보통 정렬되어 있습니다.
