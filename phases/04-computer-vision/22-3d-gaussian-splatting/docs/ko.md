> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 3D 가우시안 스플래팅 바닥부터 만들기 (3D Gaussian Splatting from Scratch)

> 장면은 수백만 개의 3D 가우시안 구름입니다. 각각은 위치, 방향, 크기, 불투명도, 그리고 시선 방향에 따라 달라지는 색을 가집니다. 이들을 래스터라이즈하고, 래스터라이제이션을 통과해 역전파하면 끝입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 4 레슨 13(3D 비전 & NeRF), 페이즈 1 레슨 12(텐서 연산), 페이즈 4 레슨 10(확산 기초, 선택)
**시간:** 약 90분

## 학습 목표

- 2026년에 3D 가우시안 스플래팅이 사실적 3D 재구성의 프로덕션(운영 환경) 기본값으로 NeRF를 대체한 이유를 설명합니다.
- 가우시안별 여섯 파라미터(위치, 회전 쿼터니언, 스케일, 불투명도, 구면 조화 색, 선택적 특징)가 무엇이고 각각 몇 개의 float를 쓰는지 말합니다.
- `alpha` 합성으로 2D 가우시안 스플래팅 래스터라이저를 바닥부터 구현하고, 3D 케이스가 같은 루프로 환원되는 과정을 보여줍니다.
- `nerfstudio`, `gsplat`, `SuperSplat`으로 20-50장의 사진에서 장면을 재구성하고, `KHR_gaussian_splatting` glTF 확장이나 OpenUSD 26.03 `UsdVolParticleField3DGaussianSplat` 스키마로 내보냅니다.

## 문제 상황

NeRF는 장면을 MLP의 가중치로 저장합니다. 픽셀 하나를 렌더링하려면 광선을 따라 수백 번 MLP를 질의합니다. 학습은 몇 시간, 렌더링은 몇 초, 그리고 가중치는 편집할 수 없습니다 — 장면 안의 의자를 옮기려면 재학습해야 합니다.

3D 가우시안 스플래팅(Kerbl, Kopanas, Leimkühler, Drettakis, SIGGRAPH 2023)이 그 모든 것을 바꿨습니다. 장면은 명시적인 3D 가우시안 집합입니다. 렌더링은 100+ fps의 GPU 래스터라이제이션입니다. 학습은 몇 분 걸립니다. 편집은 직접적입니다: 가우시안 일부를 평행이동하면 의자가 옮겨집니다. 2026년까지 Khronos Group은 가우시안 스플랫용 glTF 확장을 승인했고, OpenUSD 26.03은 가우시안 스플랫 스키마를 실으며, Zillow와 Apartments.com은 부동산을 이것으로 렌더링하고, 3D 재구성 관련 신규 논문 대부분은 핵심 3DGS 아이디어의 변형입니다.

멘탈 모델은 단순하지만, 수학에는 움직이는 부품이 충분히 많아서 대부분의 입문 자료는 래스터라이제이션에서 시작해 투영과 구면 조화는 건너뜁니다. 이 레슨은 그 전부를 만듭니다 — 먼저 2D 버전, 그다음 3D 확장.

## 개념

### 가우시안이 지니는 것

3D 가우시안 하나는 다음 속성을 가진 파라메트릭 블롭입니다:

```
position         mu         (3,)    세계 좌표계의 중심
rotation         q          (4,)    방향을 인코딩하는 단위 쿼터니언
scale            s          (3,)    축별 로그 스케일 (렌더 시 지수 적용)
opacity          alpha      (1,)    시그모이드 후 불투명도 [0, 1]
SH 계수          c_lm       (3 * (L+1)^2,)   시선 의존 색
```

회전 + 스케일이 3x3 공분산을 만듭니다: `Sigma = R S S^T R^T`. 이것이 3D에서 가우시안의 모양입니다. 구면 조화(spherical harmonics)는 색이 시선 방향에 따라 바뀌게 해줍니다 — 정반사 하이라이트, 은은한 광택, 시선 의존 발광 — 뷰별 텍스처를 저장하지 않고도. SH 차수 3이면 채널당 계수 16개, 색만으로 가우시안당 float 48개입니다.

장면은 보통 가우시안 100-500만 개를 가집니다. 각각은 대략 float 60개(3 + 4 + 3 + 1 + 48 + 기타)를 저장합니다. 500만 가우시안 장면에서 240MB입니다 — 점별 텍스처가 있는 동일한 포인트 클라우드보다 훨씬 작고, 고해상도로 다시 렌더링하는 NeRF의 MLP 가중치보다는 한 자릿수 작습니다.

### 광선 행진이 아니라 래스터라이제이션

```mermaid
flowchart LR
    SCENE["수백만 개의 3D 가우시안<br/>(위치, 회전, 스케일,<br/>불투명도, SH 색)"] --> PROJ["2D로 투영<br/>(카메라 외부/내부 파라미터)"]
    PROJ --> TILES["타일에 할당<br/>(16x16 화면 공간)"]
    TILES --> SORT["타일별<br/>깊이 정렬"]
    SORT --> ALPHA["앞에서 뒤로<br/>알파 합성"]
    ALPHA --> PIX["픽셀 색"]

    style SCENE fill:#dbeafe,stroke:#2563eb
    style ALPHA fill:#fef3c7,stroke:#d97706
    style PIX fill:#dcfce7,stroke:#16a34a
```

5단계, 모두 GPU 친화적입니다. 픽셀마다 MLP 질의가 없습니다. RTX 3080 Ti 한 장이 600만 스플랫을 147fps로 렌더링합니다.

### 투영 단계

세계 위치 `mu`, 3D 공분산 `Sigma`인 3D 가우시안은 화면 위치 `mu'`, 2D 공분산 `Sigma'`인 2D 가우시안으로 투영됩니다:

```
mu' = project(mu)
Sigma' = J W Sigma W^T J^T          (2 x 2)

W = 뷰잉 변환 (카메라 회전 + 평행이동)
J = mu'에서의 원근 투영 야코비안
```

2D 가우시안의 발자국은 `Sigma'`의 고유벡터를 축으로 하는 타원입니다. 그 타원 안의 모든 픽셀은 `exp(-0.5 * (p - mu')^T Sigma'^-1 (p - mu'))`로 가중된 가우시안의 기여를 받습니다.

### 알파 합성 규칙

한 픽셀에 대해, 그 픽셀을 덮는 가우시안들을 뒤에서 앞으로 정렬합니다(공식을 뒤집어 앞에서 뒤로 할 수도 있습니다). 색은 1980년대 이후 모든 반투명 래스터라이저가 써온 것과 같은 식으로 합성됩니다:

```
C_pixel = sum_i alpha_i * T_i * c_i

T_i = prod_{j < i} (1 - alpha_j)       i까지의 투과율
alpha_i = opacity_i * exp(-0.5 * d^T Sigma'^-1 d)   국소 기여
c_i = eval_SH(SH_i, view_direction)    시선 의존 색
```

이것은 **NeRF의 볼륨 렌더와 같은 식**입니다. 광선을 따라 촘촘히 샘플링하는 대신 명시적인 희소 가우시안 집합 위에서 적분할 뿐입니다. 렌더 품질이 NeRF와 어깨를 나란히 하는 이유가 바로 이 동일성입니다 — 둘 다 같은 복사 필드 방정식을 적분합니다.

### 미분 가능한 이유

모든 단계 — 투영, 타일 할당, 알파 합성, SH 평가 — 는 가우시안 파라미터에 대해 미분 가능합니다. 정답 이미지가 주어지면 렌더 픽셀 손실을 계산하고, 래스터라이저를 통과해 역전파하고, 모든 `(mu, q, s, alpha, c_lm)`을 경사 하강법으로 갱신합니다. 약 30,000 반복이면 가우시안들이 제 위치, 크기, 색을 찾아갑니다.

### 밀도화와 가지치기

고정된 가우시안 집합으로는 복잡한 장면을 덮을 수 없습니다. 학습에는 두 가지 적응 메커니즘이 있습니다:

- 그래디언트 크기가 큰데 스케일이 작은 가우시안을 현재 위치에서 **복제(clone)** 합니다 — 재구성이 이곳에서 더 많은 디테일을 필요로 합니다.
- 그래디언트가 큰 대형 가우시안을 더 작은 둘로 **분할(split)** 합니다 — 하나의 큰 가우시안은 그 영역을 담기에 너무 매끄럽습니다.
- 불투명도가 임계값 아래로 떨어진 가우시안은 **가지치기(prune)** 합니다 — 기여하지 않는 것들입니다.

밀도화는 N 반복마다 실행됩니다. 장면은 보통 초기 약 10만 개(SfM 점에서 시딩)에서 학습이 끝나면 100-500만 개로 자랍니다.

### 구면 조화 한 단락 요약

시선 의존 색은 단위 구 위의 함수 `c(direction)`입니다. 구면 조화는 구의 푸리에 기저입니다. 차수 `L`에서 자르면 채널당 `(L+1)^2`개의 기저 함수를 얻습니다. 새 뷰의 색 평가는 학습된 SH 계수와 시선 방향에서 평가한 기저 사이의 내적입니다. 차수 0 = 계수 하나 = 일정한 색. 차수 3 = 계수 16개 = 램버트 셰이딩, 정반사, 완만한 반사를 담기에 충분. SD Gaussian Splatting 계열 논문은 기본으로 차수 3을 씁니다.

### 2026 프로덕션 스택

```
1. 촬영            스마트폰 / DJI 드론 / 핸드헬드 스캐너
2. SfM / MVS       COLMAP 또는 GLOMAP이 카메라 포즈 + 희소 점 도출
3. 3DGS 학습       nerfstudio / gsplat / inria 공식 / PostShot (RTX 4090 기준 약 10-30분)
4. 편집            SuperSplat / SplatForge (플로터 정리, 세그먼트)
5. 내보내기        .ply -> glTF KHR_gaussian_splatting 또는 .usd (OpenUSD 26.03)
6. 보기            Cesium / Unreal / Babylon.js / Three.js / Vision Pro
```

### 4D와 생성형 변형

- **4D 가우시안 스플래팅** — 가우시안이 시간의 함수입니다; 볼륨 비디오에 사용(Superman 2026, A$AP Rocky의 "Helicopter").
- **생성형 스플랫** — 장면 전체를 상상해내는 텍스트→스플랫 모델(World Labs의 Marble).
- **3D 가우시안 언센티드 변환** — 자율주행 시뮬레이션용 NVIDIA NuRec 변형.

```figure
cv3-gaussian-splat
```

## 만들어 보기

### 단계 1: 2D 가우시안

먼저 2D 래스터라이저를 만듭니다. 3D 케이스는 투영 후 이것으로 환원됩니다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


def eval_2d_gaussian(means, covs, points):
    """
    means:  (G, 2)      중심
    covs:   (G, 2, 2)   공분산 행렬
    points: (H, W, 2)   픽셀 좌표
    반환:    (G, H, W)  모든 가우시안의 모든 픽셀 밀도
    """
    G = means.size(0)
    H, W, _ = points.shape
    flat = points.view(-1, 2)
    inv = torch.linalg.inv(covs)
    diff = flat[None, :, :] - means[:, None, :]
    d = torch.einsum("gpi,gij,gpj->gp", diff, inv, diff)
    density = torch.exp(-0.5 * d)
    return density.view(G, H, W)
```

`einsum`이 모든 (가우시안, 픽셀) 쌍에 대해 2차 형식 `diff^T Sigma^-1 diff`를 계산합니다.

### 단계 2: 2D 스플래팅 래스터라이저

앞에서 뒤로 알파 합성입니다. 2D에서 깊이는 무의미하므로, 순서를 정하기 위해 학습된 가우시안별 스칼라를 씁니다.

```python
def rasterise_2d(means, covs, colours, opacities, depths, image_size):
    """
    means:     (G, 2)
    covs:      (G, 2, 2)
    colours:   (G, 3)
    opacities: (G,)     [0, 1] 범위
    depths:    (G,)     순서 정렬에 쓰는 가우시안별 스칼라
    image_size: (H, W)
    반환:      (H, W, 3) 렌더된 이미지
    """
    H, W = image_size
    yy, xx = torch.meshgrid(
        torch.arange(H, dtype=torch.float32, device=means.device),
        torch.arange(W, dtype=torch.float32, device=means.device),
        indexing="ij",
    )
    points = torch.stack([xx, yy], dim=-1)

    densities = eval_2d_gaussian(means, covs, points)
    alphas = opacities[:, None, None] * densities
    alphas = alphas.clamp(0.0, 0.99)

    order = torch.argsort(depths)
    alphas = alphas[order]
    colours_sorted = colours[order]

    T = torch.ones(H, W, device=means.device)
    out = torch.zeros(H, W, 3, device=means.device)
    for i in range(means.size(0)):
        a = alphas[i]
        out += (T * a)[..., None] * colours_sorted[i][None, None, :]
        T = T * (1.0 - a)
    return out
```

빠르지는 않습니다 — 실제 구현은 타일 기반 CUDA 커널을 씁니다 — 하지만 수학은 정확히 맞고 완전히 미분 가능합니다.

### 단계 3: 학습 가능한 2D 스플랫 장면

```python
class Splats2D(nn.Module):
    def __init__(self, num_splats=128, image_size=64, seed=0):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        H, W = image_size, image_size
        self.means = nn.Parameter(torch.rand(num_splats, 2, generator=g) * torch.tensor([W, H]))
        self.log_scale = nn.Parameter(torch.ones(num_splats, 2) * math.log(2.0))
        self.rot = nn.Parameter(torch.zeros(num_splats))  # 2D에서는 각도 하나
        self.colour_logits = nn.Parameter(torch.randn(num_splats, 3, generator=g) * 0.5)
        self.opacity_logit = nn.Parameter(torch.zeros(num_splats))
        self.depth = nn.Parameter(torch.rand(num_splats, generator=g))

    def covs(self):
        s = torch.exp(self.log_scale)
        c, si = torch.cos(self.rot), torch.sin(self.rot)
        R = torch.stack([
            torch.stack([c, -si], dim=-1),
            torch.stack([si, c], dim=-1),
        ], dim=-2)
        S = torch.diag_embed(s ** 2)
        return R @ S @ R.transpose(-1, -2)

    def forward(self, image_size):
        covs = self.covs()
        colours = torch.sigmoid(self.colour_logits)
        opacities = torch.sigmoid(self.opacity_logit)
        return rasterise_2d(self.means, covs, colours, opacities, self.depth, image_size)
```

`log_scale`, `opacity_logit`, `colour_logits`은 모두 제약 없는 파라미터이고, 렌더 시 올바른 활성화를 통과합니다. 모든 3DGS 구현이 쓰는 표준 패턴입니다.

### 단계 4: 대상 이미지에 2D 가우시안 피팅

```python
import math
import numpy as np

def make_target(size=64):
    yy, xx = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    img = np.zeros((size, size, 3), dtype=np.float32)
    # 빨간 원
    mask = (xx - 20) ** 2 + (yy - 20) ** 2 < 10 ** 2
    img[mask] = [1.0, 0.2, 0.2]
    # 파란 사각형
    mask = (np.abs(xx - 45) < 8) & (np.abs(yy - 40) < 8)
    img[mask] = [0.2, 0.3, 1.0]
    return torch.from_numpy(img)


target = make_target(64)
model = Splats2D(num_splats=64, image_size=64)
opt = torch.optim.Adam(model.parameters(), lr=0.05)

for step in range(200):
    pred = model((64, 64))
    loss = F.mse_loss(pred, target)
    opt.zero_grad(); loss.backward(); opt.step()
    if step % 40 == 0:
        print(f"step {step:3d}  mse {loss.item():.4f}")
```

200 스텝이면 64개 가우시안이 두 모양에 자리 잡습니다. 그게 전체 아이디어입니다 — 명시적인 기하 프리미티브 위의 경사 하강법.

### 단계 5: 2D에서 3D로

3D 확장도 같은 루프를 유지합니다. 추가되는 것:

1. 가우시안별 회전이 단일 각도 대신 쿼터니언이 됩니다.
2. 공분산은 쿼터니언으로 만든 `R`과 `S = diag(exp(log_scale))`를 쓰는 `R S S^T R^T`입니다.
3. 투영 `(mu, Sigma) -> (mu', Sigma')`는 카메라 외부 파라미터와 `mu`에서의 원근 투영 야코비안을 씁니다.
4. 색은 구면 조화 전개가 됩니다. 시선 방향에서 평가합니다.
5. 깊이 정렬은 학습된 스칼라 대신 실제 카메라 공간 z를 씁니다.

모든 프로덕션 구현(`gsplat`, `inria/gaussian-splatting`, `nerfstudio`)이 타일 기반 CUDA 커널로 GPU에서 정확히 이것을 합니다.

### 단계 6: 구면 조화 평가

차수 3까지의 SH 기저는 채널당 16개 항입니다. 평가:

```python
def eval_sh_degree_3(sh_coeffs, dirs):
    """
    sh_coeffs: (..., 16, 3)   마지막 차원은 RGB 채널
    dirs:      (..., 3)       단위 벡터
    반환:      (..., 3)
    """
    C0 = 0.282094791773878
    C1 = 0.488602511902920
    C2 = [1.092548430592079, 1.092548430592079,
          0.315391565252520, 1.092548430592079,
          0.546274215296039]
    x, y, z = dirs[..., 0], dirs[..., 1], dirs[..., 2]
    x2, y2, z2 = x * x, y * y, z * z
    xy, yz, xz = x * y, y * z, x * z

    result = C0 * sh_coeffs[..., 0, :]
    result = result - C1 * y[..., None] * sh_coeffs[..., 1, :]
    result = result + C1 * z[..., None] * sh_coeffs[..., 2, :]
    result = result - C1 * x[..., None] * sh_coeffs[..., 3, :]

    result = result + C2[0] * xy[..., None] * sh_coeffs[..., 4, :]
    result = result + C2[1] * yz[..., None] * sh_coeffs[..., 5, :]
    result = result + C2[2] * (2.0 * z2 - x2 - y2)[..., None] * sh_coeffs[..., 6, :]
    result = result + C2[3] * xz[..., None] * sh_coeffs[..., 7, :]
    result = result + C2[4] * (x2 - y2)[..., None] * sh_coeffs[..., 8, :]

    # 간결함을 위해 차수 3 항은 생략; 16계수 전체 버전은 코드 파일에 있음
    return result
```

학습된 `sh_coeffs`는 그 가우시안의 "모든 방향에서의 색"을 저장합니다. 렌더 시 현재 시선 방향으로 평가하면 RGB 3-벡터를 얻습니다.

## 활용하기

실제 3DGS 작업에는 `gsplat`(Meta)이나 `nerfstudio`를 쓰세요:

```bash
pip install nerfstudio gsplat
ns-download-data example
ns-train splatfacto --data path/to/data
```

`splatfacto`는 nerfstudio의 3DGS 트레이너입니다. 일반적인 장면 기준 RTX 4090에서 10-30분 걸립니다.

2026년에 중요한 내보내기 옵션:

- `.ply` — 원시 가우시안 클라우드(이식성 좋음, 가장 큰 파일).
- `.splat` — PlayCanvas / SuperSplat 양자화 포맷.
- glTF `KHR_gaussian_splatting` — Khronos 표준, 뷰어 전반에서 이식 가능(2026년 2월 RC).
- OpenUSD `UsdVolParticleField3DGaussianSplat` — USD 네이티브, NVIDIA Omniverse와 Vision Pro 파이프라인용.

4D / 동적 장면에는 `4DGS`와 `Deformable-3DGS`가 같은 기계 장치에 시간에 따라 변하는 평균과 불투명도를 얹어 확장합니다.

## 출시하기

이 레슨이 만드는 산출물:

- `outputs/prompt-3dgs-capture-planner.md` — 장면 유형이 주어지면 촬영 세션(사진 장수, 카메라 경로, 조명)을 계획하는 프롬프트.
- `outputs/skill-3dgs-export-router.md` — 하위 뷰어나 엔진에 맞는 내보내기 포맷(`.ply` / `.splat` / glTF / USD)을 고르는 스킬.

## 연습 문제

1. **(쉬움)** 위의 2D 스플랫 트레이너를 다른 합성 이미지로 실행하세요. `num_splats`를 `[16, 64, 256]`으로 바꿔가며 각각의 MSE vs 스텝을 그래프로 그리세요. 수확이 체감되는 지점을 찾으세요.
2. **(보통)** 2D 래스터라이저가 차수-2 조화를 통과하는 스칼라 "시각 각도"에 따라 달라지는 가우시안별 RGB 색을 지원하도록 확장하세요. 대상 이미지 한 쌍으로 학습하고 두 장 모두 재구성하는지 확인하세요.
3. **(어려움)** `nerfstudio`를 클론하고 가지고 계신 장면(책상, 식물, 얼굴, 방 아무거나)의 20장 촬영으로 `splatfacto`를 학습하세요. glTF `KHR_gaussian_splatting`으로 내보내 뷰어(Three.js `GaussianSplats3D`, SuperSplat, Babylon.js V9)에서 열어보세요. 학습 시간, 가우시안 수, 렌더 fps를 보고하세요.

## 핵심 용어

| 용어 | 흔한 표현 | 실제 의미 |
|------|----------------|----------------------|
| 3DGS | "가우시안 스플랫" | 수백만 개의 3D 가우시안(위치, 회전, 스케일, 불투명도, SH 색)으로 장면을 표현하는 명시적 표현 |
| 공분산 | "가우시안의 모양" | `Sigma = R S S^T R^T`; 가우시안 하나의 방향과 비등방성 스케일 |
| 알파 합성 | "뒤에서 앞으로 블렌딩" | NeRF 볼륨 렌더와 같은 식, 명시적 희소 집합 위에 적용 |
| 밀도화 | "복제와 분할" | 재구성이 덜 된 곳에 새 가우시안을 적응적으로 추가 |
| 가지치기 | "낮은 불투명도 삭제" | 학습 중 불투명도가 거의 0으로 무너진 가우시안 제거 |
| 구면 조화 | "시선 의존 색" | 구 위의 푸리에 기저; 색을 시선 방향의 함수로 저장 |
| Splatfacto | "nerfstudio의 3DGS" | 2026년에 3DGS를 학습하는 가장 쉬운 길 |
| `KHR_gaussian_splatting` | "glTF 표준" | 3DGS를 뷰어와 엔진 전반에서 이식 가능하게 만드는 Khronos 2026 확장 |

## 더 읽을거리

- [3D Gaussian Splatting for Real-Time Radiance Field Rendering (Kerbl et al., SIGGRAPH 2023)](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) — 원 논문
- [gsplat (Meta/nerfstudio)](https://github.com/nerfstudio-project/gsplat) — 프로덕션 수준 CUDA 래스터라이저
- [nerfstudio Splatfacto](https://docs.nerf.studio/nerfology/methods/splat.html) — 레퍼런스 학습 레시피
- [Khronos KHR_gaussian_splatting 확장](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_gaussian_splatting/README.md) — 2026년 이식 포맷
- [OpenUSD 26.03 릴리스 노트](https://openusd.org/release/) — `UsdVolParticleField3DGaussianSplat` 스키마
- [THE FUTURE 3D State of Gaussian Splatting 2026](https://www.thefuture3d.com/blog-0/2026/4/4/state-of-gaussian-splatting-2026) — 업계 개관
