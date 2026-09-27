> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-heatmap-to-coords.md](skill-heatmap-to-coords.md)

---
name: skill-heatmap-to-coords
description: 모든 프로덕션 포즈 모델이 쓰는 서브픽셀 히트맵→좌표 변환 루틴을 작성합니다
version: 1.0.0
phase: 4
lesson: 21
tags: [keypoint, pose, subpixel, inference]
---

# Heatmap to Coords

원시 키포인트 히트맵을 서브픽셀 정밀 좌표로 바꿔줍니다. 모든 포즈 파이프라인에서 가장 싼 정확도 업그레이드입니다.

## 언제 사용하나

- 히트맵 기반 키포인트 모델을 배포할 때.
- 포즈 지표 벤치마킹 — OKS는 서브픽셀 정확도에 극도로 민감합니다.
- 포즈 코드를 한 프레임워크에서 다른 프레임워크로 옮길 때.

## 입력

- `heatmaps`: 모델이 내는 키포인트별 히트맵 `(N, K, H, W)` 텐서.
- `confidence_threshold`: 봉우리가 이 값보다 낮은 키포인트는 버립니다.

## 단계

1. 각 히트맵을 **argmax**해서 정수 봉우리 위치를 찾습니다.
2. **1차 차분 오프셋** — 이웃 픽셀로 서브픽셀 오프셋을 추정합니다. `0.25` 계수는 `sigma >= 1`인 가우시안 히트맵에 맞춰 보정된 휴리스틱입니다. 원리적으로 깔끔한 서브픽셀 복원이 필요하면 완전한 2차 포물선 피팅(DARK)이나 가우시안 피팅을 쓰세요.

```
dx = 0.25 * sign(heatmap[y, x+1] - heatmap[y, x-1])
dy = 0.25 * sign(heatmap[y+1, x] - heatmap[y-1, x])
```

DARK / 2차 변형은 국소 2차 함수로 근사합니다:

```
dx = -0.5 * (heatmap[y, x+1] - heatmap[y, x-1])
        / (heatmap[y, x+1] - 2 * heatmap[y, x] + heatmap[y, x-1] + eps)
```

봉우리가 뾰족한 히트맵에서는 2차 피팅이 더 정확하고, 히트맵이 시끄러울 때는 부호 기반 오프셋이 더 안전한 기본값입니다.

3. 정수 봉우리에 **오프셋을 더합니다**.
4. **신뢰도(confidence)** — 키포인트별 봉우리 값을 반환합니다. 클라이언트가 낮은 신뢰도 예측을 마스킹하는 데 씁니다.
5. **경계 케이스** — 봉우리가 축의 첫/마지막 픽셀에 걸리면 이웃 하나가 클램프됩니다. 오프셋이 0으로 수렴하는데, 이게 가장 안전한 폴백입니다.

## 출력 템플릿

```python
import torch

def heatmap_to_coords_subpixel(heatmaps, threshold=0.2):
    N, K, H, W = heatmaps.shape
    flat = heatmaps.reshape(N, K, -1)
    conf, idx = flat.max(dim=-1)
    ys = (idx // W).float()
    xs = (idx % W).float()

    ys_int = ys.long()
    xs_int = xs.long()

    x_minus = (xs_int - 1).clamp(min=0)
    x_plus = (xs_int + 1).clamp(max=W - 1)
    y_minus = (ys_int - 1).clamp(min=0)
    y_plus = (ys_int + 1).clamp(max=H - 1)

    batch_idx = torch.arange(N).view(-1, 1).expand(-1, K)
    kp_idx = torch.arange(K).view(1, -1).expand(N, -1)

    dx_raw = (heatmaps[batch_idx, kp_idx, ys_int, x_plus]
              - heatmaps[batch_idx, kp_idx, ys_int, x_minus])
    dy_raw = (heatmaps[batch_idx, kp_idx, y_plus, xs_int]
              - heatmaps[batch_idx, kp_idx, y_minus, xs_int])
    dx = 0.25 * torch.sign(dx_raw)
    dy = 0.25 * torch.sign(dy_raw)

    at_left = xs_int == 0
    at_right = xs_int == (W - 1)
    at_top = ys_int == 0
    at_bottom = ys_int == (H - 1)
    dx = torch.where(at_left | at_right, torch.zeros_like(dx), dx)
    dy = torch.where(at_top | at_bottom, torch.zeros_like(dy), dy)

    refined_x = xs + dx
    refined_y = ys + dy
    coords = torch.stack([refined_x, refined_y], dim=-1)
    mask = conf >= threshold
    return coords, conf, mask
```

## 보고서

```
[subpixel decode]
  keypoints:   K
  threshold:   <float>
  valid_rate:  임계값을 넘은 키포인트 비율
```

## 규칙

- 이웃 인덱스는 항상 유효 범위로 클램프하세요. 경계 밖 키포인트는 오프셋이 0이 될 뿐 크래시가 나지 않습니다.
- 좌표와 함께 신뢰도를 반환해서 클라이언트가 낮은 신뢰도 점을 마스킹할 수 있게 하세요.
- 서브픽셀 정밀화는 봉우리 주변 히트맵이 매끄러울 때만 도움이 됩니다. 학습에 sigma >= 1인 가우시안 타깃을 썼는지 확인하세요.
- 히트맵 해상도가 아주 작으면(< 48x48), 좌표를 뽑기 전에 히트맵을 전체 이미지 크기로 업샘플하는 걸 고려하세요. 서브픽셀 오프셋은 스트라이드에 비례합니다.
