---
name: skill-point-cloud-loader
description: .ply / .pcd / .xyz 파일용 PyTorch Dataset을 올바른 정규화, 중심 정렬, 점 샘플링과 함께 작성
version: 1.0.0
phase: 4
lesson: 13
tags: [3d-vision, point-cloud, data-loading, pytorch]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-point-cloud-loader.md](skill-point-cloud-loader.md)

# 포인트 클라우드 로더

3D 스캔 파일 폴더를 바로 학습에 쓸 수 있는 PyTorch `Dataset`으로 바꿔 줍니다.

## 언제 사용하나

- 새 포인트 클라우드 분류/분할 프로젝트를 시작할 때
- `.ply`, `.pcd`, `.xyz` 형식 사이를 오갈 때
- 오류 없이 학습되는데 수렴이 나쁜 모델을 디버깅할 때. 대개 데이터 로더의 정규화가 잘못된 경우입니다.

## 입력

- `data_root`: 포인트 클라우드 파일들과 선택적인 레이블 CSV가 있는 폴더.
- `file_format`: ply | pcd | xyz | npy.
- `num_points`: 고정 샘플링 크기, 보통 1024 또는 2048.
- `augmentation`: none | rotate | jitter | mixup.

## 정규화 정책

모든 프로덕션 포인트 클라우드 파이프라인은 다음을 순서대로 적용합니다:

1. 클라우드를 **중심 정렬**합니다: 무게중심(centroid)을 뺍니다.
2. **단위 구로 스케일**합니다: 중심에서 가장 먼 거리로 나눕니다.
3. `num_points`개 점을 **샘플링**합니다. 클라우드가 더 크면 충실한 형태 표현을 위해 **최원점 샘플링(farthest point sampling, FPS)**을, 속도가 중요하면 무작위 샘플링을 씁니다. 더 적으면 점을 반복해 채웁니다.
4. 점 순서를 **섞습니다**(어차피 모델에는 순서가 중요하지 않지만, 섞어야 우연한 순서 의존을 끊습니다).

## 출력 템플릿

```python
import numpy as np
import torch
from torch.utils.data import Dataset

try:
    import open3d as o3d
    HAS_O3D = True
except ImportError:
    HAS_O3D = False

def _read_ply(path):
    if HAS_O3D:
        pc = o3d.io.read_point_cloud(path)
        return np.asarray(pc.points, dtype=np.float32)
    # 폴백: 최소한의 ascii-ply 판독기
    ...

def _fps(points, k):
    idx = np.zeros(k, dtype=np.int64)
    dist = np.full(len(points), np.inf)
    seed = np.random.randint(len(points))
    idx[0] = seed
    for i in range(1, k):
        dist = np.minimum(dist, ((points - points[idx[i-1]]) ** 2).sum(axis=1))
        idx[i] = int(np.argmax(dist))
    return idx

def normalise(points):
    centre = points.mean(axis=0)
    points = points - centre
    scale = np.max(np.linalg.norm(points, axis=1))
    return points / max(scale, 1e-8)

class PointCloudDataset(Dataset):
    def __init__(self, files, labels, num_points=1024, augment=False):
        self.files = files
        self.labels = labels
        self.num_points = num_points
        self.augment = augment

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        pts = _read_ply(self.files[i])
        pts = normalise(pts)
        if len(pts) >= self.num_points:
            idx = _fps(pts, self.num_points)
            pts = pts[idx]
        else:
            reps = int(np.ceil(self.num_points / len(pts)))
            pts = np.tile(pts, (reps, 1))[:self.num_points]
        # 우연한 의존을 끊으려고 점 순서를 섞는다(특히 타일링이 점을 정해진
        # 순서로 반복할 때 중요).
        np.random.shuffle(pts)
        if self.augment:
            theta = np.random.uniform(0, 2 * np.pi)
            R = np.array([[np.cos(theta), 0, np.sin(theta)],
                          [0, 1, 0],
                          [-np.sin(theta), 0, np.cos(theta)]], dtype=np.float32)
            pts = pts @ R
            pts = pts + np.random.normal(0, 0.02, pts.shape).astype(np.float32)
        pts = np.ascontiguousarray(pts, dtype=np.float32)
        return torch.from_numpy(pts).transpose(0, 1), int(self.labels[i])
```

## 보고

```
[dataset]
  files:          <N>
  format:         <ply|pcd|xyz|npy>
  points_per_sample: <int>
  normalise:      centre + unit sphere
  sampling:       FPS | random
  augmentation:   <list>
```

## 규칙

- 항상 스케일링 전에 중심 정렬을 하세요. 순서를 바꾸면 '단위 구'의 의미가 달라집니다.
- 형태(shape) 작업에서는 무작위 샘플링보다 FPS를 선호하세요. 모든 점이 어차피 중요한 분할에는 무작위도 괜찮습니다.
- 평가 중에는 절대 증강하지 마세요. 학습 중에만 적용합니다.
- 포인트 클라우드 파일에 색상이나 법선이 추가 채널로 들어 있다면, Dataset이 xyz만이 아니라 `(3 + C, num_points)` 텐서를 반환하도록 확장하세요.
