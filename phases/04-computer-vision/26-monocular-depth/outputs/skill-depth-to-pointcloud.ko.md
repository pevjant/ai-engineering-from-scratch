---
name: skill-depth-to-pointcloud
description: 뎁스 맵에서 내부 파라미터(intrinsics)를 올바르게 처리해 포인트 클라우드를 만들고 .ply로 내보낸다
version: 1.0.0
phase: 4
lesson: 26
tags: [depth, point-cloud, 3d, intrinsics]
---

# 뎁스를 포인트 클라우드로 (Depth to Point Cloud)

뎁스 맵과 컬러 이미지를 텍스처가 입혀진 포인트 클라우드로 바꿔, 시각화나 추가 3D 작업에 쓸 수 있게 내보냅니다.

## 사용 시점

- 뎁스 예측 결과를 실제 3D 장면으로 시각화할 때.
- 이미지 한 장으로 희소(sparse) 3D 복원을 시작할 때.
- SfM(Structure from Motion)이 실패했을 때 3DGS 학습 입력을 만들 때.
- 예측 뎁스를 라이다(LiDAR) 정답과 비교할 때.

## 입력

- `depth`: `(H, W)` 모양의 numpy 배열. 출력에 쓰고 싶은 단위와 같은 단위로 담긴 뎁스(미터 권장).
- `rgb`: `(H, W, 3)` 모양의 numpy 배열. 색상 값(uint8 또는 float32 [0, 1]).
- `intrinsics`: 픽셀 단위의 `(fx, fy, cx, cy)`.
- 선택값 `depth_scale`: 예측 뎁스 단위를 미터로 바꾸기 위한 곱셈 계수.

## 파이프라인

1. **검증(Validate)** — 포함시키려는 픽셀의 뎁스는 양수이고 유한(finite)해야 한다. 유효하지 않은 픽셀은 마스크로 제외한다.
2. **들어올리기(Lift)** — 픽셀마다 `X = (u - cx) * d / fx`, `Y = (v - cy) * d / fy`, `Z = d`를 계산한다.
3. **RGB와 짝짓기(Pair)** — 각 3D 점에 대응 픽셀에서 가져온 `(r, g, b)` 값을 붙인다.
4. **내보내기(Export)** — PLY(범용), `.xyz`(가벼움), `.pcd`(Open3D 기본 형식), `.las`/`.laz`(지리공간).

## 구현 템플릿

```python
import numpy as np

def depth_to_point_cloud(depth, intrinsics, depth_scale=1.0, min_depth=0.1, max_depth=100.0):
    H, W = depth.shape
    fx, fy, cx, cy = intrinsics
    v, u = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    z = depth.astype(np.float32) * depth_scale
    valid = (z > min_depth) & (z < max_depth) & np.isfinite(z)
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    points = np.stack([x, y, z], axis=-1)
    return points, valid


def write_ply(path, points, colors=None, valid_mask=None):
    p = points.reshape(-1, 3)
    if valid_mask is not None:
        p = p[valid_mask.flatten()]
    lines = [
        "ply",
        "format ascii 1.0",
        f"element vertex {p.shape[0]}",
        "property float x", "property float y", "property float z",
    ]
    if colors is not None:
        c = colors.reshape(-1, 3).astype(np.uint8)
        if valid_mask is not None:
            c = c[valid_mask.flatten()]
        lines += ["property uchar red", "property uchar green", "property uchar blue"]
    lines.append("end_header")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
        if colors is not None:
            for pt, col in zip(p, c):
                f.write(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f} {col[0]} {col[1]} {col[2]}\n")
        else:
            for pt in p:
                f.write(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f}\n")
```

## 보고서

```
[export]
  input depth shape:  (H, W)
  valid points:       <N> of <H*W>
  output format:      ply | xyz | pcd | las
  coordinate system:  camera (+X right, +Y down, +Z forward)
  scale:              metres | millimetres | normalised
```

## 규칙

- 유효하지 않은 뎁스(0, NaN, inf, 포화된 값)는 반드시 마스킹한다. 그대로 두면 원점에 쓰레기 점 더미가 생긴다.
- 상대 뎁스 모델의 예측 결과는 메트릭으로 내보내지 **않는다**. 관례를 알리기 위해 출력 파일 이름 앞에 `relative_`를 붙인다.
- 카메라 좌표계 관례를 일관되게 유지한다(OpenCV: +X 오른쪽, +Y 아래, +Z 앞). 후속 도구가 OpenGL(+Y 위)을 기대한다면 부호를 뒤집는다.
- 조밀한 장면(> 100만 점)에서는 서브샘플(subsample) 파라미터를 제공한다. 500MB가 넘는 PLY 파일은 어디서 열든 부담스럽다.
- "그럴듯한" 결과를 만들려고 뎁스를 조용히 잘라내지 않는다. 잘라낸다면 경고와 함께 임계값을 명시해서 사용자가 무엇이 버려졌는지 알게 한다.
