---
name: skill-mask-rcnn-head-swapper
description: 커스텀 num_classes에 맞춰 torchvision Mask R-CNN의 박스/마스크 헤드를 교체하는 정확한 코드를 생성
version: 1.0.0
phase: 4
lesson: 8
tags: [computer-vision, mask-rcnn, fine-tuning, torchvision]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mask-rcnn-head-swapper.md](skill-mask-rcnn-head-swapper.md)

# Mask R-CNN 헤드 교체기(Head Swapper)

Mask R-CNN 전용 헤드 교체 보일러플레이트 코드를 만들어 줍니다. 아래 템플릿은 `model.roi_heads.box_predictor`와 `model.roi_heads.mask_predictor`를 전제하는데, 이 속성들은 `maskrcnn_resnet50_fpn`과 `maskrcnn_resnet50_fpn_v2`에만 있습니다. Faster R-CNN에는 박스 예측기는 있지만 마스크 예측기가 없고, RetinaNet은 `RetinaNetHead`를 써서 `roi_heads` 자체가 없습니다. 이 둘은 각각 다른 스킬이 필요합니다.

## 언제 사용하나

- 커스텀 클래스 집합으로 `maskrcnn_resnet50_fpn` 또는 `maskrcnn_resnet50_fpn_v2`를 파인튜닝할 때
- COCO로 학습한 Mask R-CNN 체크포인트를 COCO가 아닌 클래스 수로 옮길 때
- `cls_score.out_features` 또는 `mask_predictor` 불일치로 학습이 죽는 Mask R-CNN을 디버깅할 때

## 범위 밖

- `fasterrcnn_*` — mask_predictor가 없습니다. `box_predictor`만 교체하며, 별도의 Faster R-CNN 헤드 교체 레시피를 사용하세요.
- `retinanet_*` — `roi_heads`가 없습니다. 분류 + 회귀 헤드는 `model.head.classification_head`와 `model.head.regression_head` 아래에 있습니다. RetinaNet 전용 스킬을 사용하세요.
- `keypointrcnn_*` — `mask_predictor` 대신 `keypoint_predictor`를 사용합니다.

## 입력

- `model_name`: torchvision 검출 모델 생성자. 예: `maskrcnn_resnet50_fpn_v2`
- `num_classes`: 배경 포함 개수. 객체 클래스가 4개인 데이터셋이면 `num_classes=5`입니다.
- `freeze`: `backbone`, `backbone_fpn`, `none` 중 하나

## 단계

1. 모델 생성자와 두 예측기 클래스(`FastRCNNPredictor`, `MaskRCNNPredictor`)를 임포트합니다.
2. 기본 가중치(DEFAULT)로 사전 학습된 모델을 불러옵니다.
3. `model.roi_heads.box_predictor`를 새 `FastRCNNPredictor(in_features, num_classes)`로 교체합니다.
4. `model.roi_heads.mask_predictor`를 새 `MaskRCNNPredictor(in_features_mask, hidden_layer=256, num_classes)`로 교체합니다.
5. 요청받은 freeze 정책을 적용합니다.
6. 모듈별 학습 가능 파라미터 수를 나열한 확인 블록을 출력합니다.

## 출력 코드 템플릿

```python
from torchvision.models.detection import {MODEL_NAME}, {MODEL_WEIGHTS}
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

def build_model(num_classes={NUM_CLASSES}):
    model = {MODEL_NAME}(weights={MODEL_WEIGHTS}.DEFAULT)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask, 256, num_classes)

    {FREEZE_BLOCK}

    return model
```

`{FREEZE_BLOCK}`는 다음과 같습니다:

- `none` -> 비워 둠
- `backbone` ->
  ```python
  for p in model.backbone.parameters():
      p.requires_grad = False
  ```
- `backbone_fpn` ->
  ```python
  for p in model.backbone.parameters():
      p.requires_grad = False
  # FPN 파라미터는 backbone.fpn 안에 있습니다
  ```

## 보고

```
[head-swap]
  model:         <MODEL_NAME>
  num_classes:   <N>  (includes background)
  freeze policy: <choice>
  trainable:     <N>
  total:         <N>
```

## 규칙

- 배경을 포함하지 않은 `num_classes`는 절대 권하지 마세요. 항상 사용자에게 다시 상기시킵니다.
- 가능하면 torchvision 검출 모델은 항상 `_v2` 변형을 사용하세요. 구형보다 사전 학습 가중치가 더 좋습니다.
- 이 스킬 안에서 모델을 직접 인스턴스화하지 마세요. 코드 블록을 만들어 사용자가 실행하도록 맡깁니다.
- 이미지가 1만 장을 넘는 데이터셋에서 `freeze backbone`을 요청하면, 백본도 함께 파인튜닝할지 고려해 보라고 제안하세요.
