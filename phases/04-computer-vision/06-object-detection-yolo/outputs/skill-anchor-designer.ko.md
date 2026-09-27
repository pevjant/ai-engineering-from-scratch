---
name: skill-anchor-designer
description: 정답 박스 데이터셋이 주어지면 (w, h)에 k-평균을 돌리고 FPN 레벨별 앵커 집합과 커버리지 통계 반환
version: 1.0.0
phase: 4
lesson: 6
tags: [computer-vision, detection, anchors, kmeans]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-anchor-designer.md](skill-anchor-designer.md)

# 앵커 디자이너 (Anchor Designer)

앵커는 앵커 기반 탐지기에서 가장 데이터 고유적인 하이퍼파라미터입니다. 기본 COCO 앵커는 세포 배양 이미지, 위성 타일, 소형 물체 감시 영상에서 성능이 떨어집니다. 이 스킬은 대상 데이터에 실제로 맞는 앵커를 도출합니다.

## 언제 사용하나

- 새 데이터셋 첫 학습 전.
- 그 외로 건강한 모델에서 아주 작거나 아주 큰 물체의 recall이 약할 때.
- 박스 크기 분포가 바뀌었을 수 있는 대규모 데이터 확장 후.

## 입력

- `boxes`: `(cx, cy, w, h)` 또는 `(x1, y1, x2, y2)` 형식 중 하나인 (N, 4) 모양의 numpy 배열; 양성 박스 1,000개 이상 권장.
- `num_anchors_per_level`: 보통 3.
- `num_fpn_levels`: 보통 3(P3, P4, P5) 또는 4.
- `input_size`: 학습 해상도 HxW.
- 선택 사항 `strides`: 레벨별 stride; 생략하면 `[8, 16, 32, 64]`의 첫 `num_fpn_levels`개를 사용. 탐지기의 FPN이 다른 stride를 쓴다면 더 길거나 짧은 배열을 명시적으로 전달할 것.

## 단계

1. **박스 정규화** — `input_size` 기준 픽셀 단위 `(w, h)` 쌍으로. w나 h가 2픽셀 미만인 것은 버립니다.

2. **k-평균 실행** — `(w, h)` 쌍에, `k = num_anchors_per_level * num_fpn_levels`. 거리 함수는 유클리드 거리가 아니라 `1 - IoU(box, cluster)` — `(w, h)` 위의 유클리드는 가늘고 긴 박스와 정사각 박스를 뭉개서 한 덩어리로 만듭니다. 모든 박스는 동등하게(가중치 없이) 기여합니다; 클래스 불균형 데이터셋에서 큰 박스의 recall을 챙기고 싶다면 가중치 벡터를 넘기는 대신 희귀 클래스 박스를 입력 배열에 반복 넣으세요.

3. **클러스터를 면적 오름차순으로 정렬.** `num_fpn_levels`개 그룹으로, 그룹당 `num_anchors_per_level`개씩 나눕니다. 면적이 가장 작은 것들이 최고 해상도 레벨(가장 작은 stride)로 갑니다.

4. **레벨별 커버리지 통계 계산:**
   - 그 레벨에서 각 정답 박스의 최선 앵커에 대한 `median IoU`.
   - `recall@IoU=0.5` — 최선 앵커의 IoU가 0.5 이상인 박스 비율.
   - `area coverage` — 면적이 그 레벨의 `[anchor_min_area / 4, anchor_max_area * 4]` 안에 드는 박스 비율.

5. **레벨별 앵커 보고**와 `recall@IoU=0.5 < 0.9`인 레벨 표시; 그 레벨의 앵커는 데이터와 잘 맞지 않으므로 재조정하거나 레벨당 앵커 수를 늘려야 합니다.

## 리포트 형식

```
[anchor-designer]
  total boxes:         <N>
  clusters:            <k>
  distance metric:     1 - IoU

[level P3  stride=8]
  anchors (w, h):      [(A, B), (C, D), (E, F)]
  median IoU:          <X>
  recall@IoU=0.5:      <X>
  coverage:            <X>
  flag:                ok | retune

[level P4  stride=16]
  ...

[summary]
  overall recall@IoU=0.5: <X>
  smallest anchor:        <w x h>
  largest anchor:         <w x h>
  recommendation:         <표시된 레벨이 있다면 한 문장>
```

## 규칙

- 항상 IoU 기반 거리를 사용합니다; 유클리드 k-평균은 눈으로는 그럴듯하지만 경험적으로 더 나쁜 앵커를 만듭니다.
- 클러스터를 면적으로 정렬한 뒤 오름차순으로 레벨에 배정합니다.
- `num_anchors_per_level = 1`이면 k-평균을 건너뜁니다: 박스를 면적 분위수로 `num_fpn_levels`개 구간(3 레벨이면 삼분위수 등)으로 나누고, 각 레벨의 앵커를 구간별 (w, h) 중앙값으로 설정. 작은 데이터셋에서 `k = num_fpn_levels`로 k-평균을 돌리는 것보다 견고합니다.
- 음수 앵커 크기를 출력하지 않습니다; 1에서 클램프합니다.
- 데이터셋의 박스가 200개 미만이면 앵커 탐색이 신뢰 불가하다고 사용자에게 경고하고, 기본 COCO 앵커에 더 많은 학습 데이터를 권합니다.
