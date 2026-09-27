---
name: skill-image-tensor-inspector
description: 이미지 모양 텐서나 배열을 검사해 dtype, 레이아웃, 범위, 그리고 원본/정규화/표준화 상태를 보고하기
version: 1.0.0
phase: 4
lesson: 1
tags: [computer-vision, debugging, preprocessing, tensors]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-image-tensor-inspector.md](skill-image-tensor-inspector.md)

# 이미지 텐서 검사기

비전 파이프라인의 어느 지점에서든, 이미지 모양 배열을 손에 들고 정확히 어떤 상태인지 알아야 할 때 쓰는 진단 스킬입니다.

## 언제 쓰나

- 사전 학습된 모델이 엉터리 예측을 내놓고 전처리가 의심될 때.
- 파이프라인을 OpenCV와 torchvision 사이에서 옮기는데 채널 순서가 불확실할 때.
- 여러 프레임워크의 레이어를 쌓는데 배치 축이 자꾸 엉뚱한 자리에 나타날 때.
- 손실이 `log(num_classes)`에 고착된 학습 루프를 디버깅할 때.

## 입력

- `x`: 2차원, 3차원, 4차원 배열 형태라면 무엇이든(NumPy, PyTorch, JAX).
- 선택적 `expected`: 검사 기준이 될 불변 조건 딕셔너리. 예: `{"layout": "CHW", "range": "standardized"}`.

## 단계

1. **백엔드 판별** — `x`가 NumPy인지, Torch인지, JAX인지 감지합니다. 원본을 바꾸지 않고 검사용으로 NumPy로 변환합니다.

2. **차원 수(rank) 분류**:
   - rank 2 -> 단일 채널 이미지 (H, W).
   - rank 3 -> 마지막 축이 1, 3, 4이고 나머지 두 축보다 확실히 작으면 `HWC`, 아니면 `CHW`.
   - rank 4 -> 1번 축이 {1, 3, 4}에 있고 **그리고** 2번 축이나 3번 축 중 하나가 16보다 크면 `NCHW`로 판단하고, 아니면 `NHWC`로 판단합니다. 1번 축만 보면 `(3, 4, 224, 3)` 같은 작은 이미지 NHWC 배치를 잘못 분류합니다.
   - 모호한 경우(예: `(1, 3, 3, 3)`)는 추측하지 말고 반드시 `ambiguous`로 표시하세요. 호출자에게 `expected` 제공을 요구합니다.

3. **dtype과 범위 분류**:
   - [0, 255] 범위의 `uint8` -> `raw`.
   - min >= 0이고 max <= 1.01인 `float*` -> `normalized`.
   - min < 0이고 |mean| < 0.5이고 0.5 <= std <= 1.5인 `float*` -> `standardized`.
   - 그 외 -> `unusual`, 히스토그램을 출력합니다.

4. **채널별 통계** — 채널별 평균과 표준편차를 보고합니다. 배열이 표준화된 것으로 보이면 ImageNet 평균/표준편차와 비교해 일치 신뢰도를 함께 알려 줍니다.

5. **보고** — 다음 블록 그대로:

```
[inspector]
  backend:   numpy | torch | jax
  rank:      2 | 3 | 4
  layout:    HW | HWC | CHW | NHWC | NCHW
  dtype:     <dtype>
  shape:     <shape>
  range:     raw | normalized | standardized | unusual
  min/max:   <min> / <max>
  per-channel mean: [ ... ]
  per-channel std:  [ ... ]
  likely source:    camera | PIL | OpenCV | torchvision | random init
  likely target:    display | training | inference
```

6. **다음 행동 추천** — `likely target`을 기준으로:
   - `display`라면: HWC로 전치하고, 클리핑하고, uint8로 변환하세요.
   - `training`이라면: 데이터셋 통계로 표준화하고, CHW로 전치하고, 배치 축을 추가하세요.
   - `inference`라면: 모델 카드의 불변 조건을 정확히 맞추세요.

## 규칙

- 입력을 절대 바꾸지 마세요. 진단 출력만 합니다.
- `expected`가 주어지면 모든 불일치를 `[expected X got Y]`로 표시하세요.
- 레이아웃이나 채널 순서가 모호할 때는 조용한 실패 위험을 짚어 주세요.
- 선택지 목록이 아니라 한 번에 행동 하나만 추천하세요.
