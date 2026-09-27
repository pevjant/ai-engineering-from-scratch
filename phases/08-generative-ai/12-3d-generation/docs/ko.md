> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 3D 생성

> 3D는 2D에서 3D로 가는 레버리지가 가장 강한 모달리티입니다. 2023년의 돌파구는 3D Gaussian Splatting이었습니다. 2024~2026년의 생성 모델 물결은 그 위에 멀티뷰 확산 + 3D 재구성을 얹어 프롬프트 하나 또는 사진 한 장에서 물체와 장면을 만들어 냅니다.

**유형:** Learn
**언어:** Python
**선수 지식:** 페이즈 4(비전), 페이즈 8 · 07(잠재 확산)
**시간:** 약 45분

## 문제 상황

3D 콘텐츠는 고통스럽습니다:

- **표현.** 메시, 포인트 클라우드, 복셀 그리드, 부호 거리 필드(SDF), 신경 방사 필드(NeRF), 3D 가우시안. 각각 트레이드오프가 있습니다.
- **데이터 부족.** ImageNet은 1,400만 장의 이미지가 있습니다. 가장 큰 깨끗한 3D 데이터셋(Objaverse-XL, 2023)은 약 1,000만 개 물체인데 대부분 저품질입니다.
- **메모리.** 512³ 복셀 그리드는 1억 2,800만 복셀입니다. 쓸 만한 장면 NeRF는 광선당 100만 샘플이 필요합니다. 생성은 재구성보다 더 어렵습니다.
- **감독 신호.** 2D 이미지에는 픽셀이 있습니다. 3D에는 보통 소수의 2D 뷰만 있고 이를 3D로 끌어올려야(lift) 합니다.

2026년 스택은 이 두 문제를 갈라 놓습니다. 먼저 확산 모델로 *2D 멀티뷰 이미지*를 생성합니다. 그다음 그 이미지들에 *3D 표현*(보통 가우시안 스플래팅)을 피팅합니다.

## 개념

![3D 생성: 멀티뷰 확산 + 3D 재구성](../assets/3d-generation.svg)

### 표현: 3D Gaussian Splatting (Kerbl 외, 2023)

장면을 약 100만 개 3D 가우시안의 구름으로 표현합니다. 각 가우시안은 59개 파라미터를 갖습니다: 위치(3), 공분산(6, 또는 쿼터니언 4 + 스케일 3), 불투명도(1), 구면 조화 색(3차에서 48, 0차에서 3).

렌더링 = 사영 + 알파 합성. 빠릅니다(4090에서 1080p 기준 약 100 fps). 미분 가능합니다. 정답 사진과의 비교로 경사 하강법으로 피팅합니다. 소비자용 GPU에서 장면 하나가 5-30분 안에 피팅됩니다.

그 위에 얹힌 2023~2024년의 혁신 둘:
- **생성형 가우시안 스플랫.** LGM, LRM, InstantMesh 같은 모델은 이미지 한 장 또는 몇 장에서 가우시안 구름을 직접 예측합니다.
- **4D Gaussian Splatting.** 동적 장면을 위해 프레임별 오프셋을 가진 가우시안.

### 멀티뷰 확산

사전학습된 이미지 확산 모델을 파인튜닝해 같은 물체의 일관된 여러 뷰를 텍스트 프롬프트나 단일 이미지에서 생성합니다. Zero123(Liu 외, 2023), MVDream(Shi 외, 2023), SV3D(Stability, 2024), CAT3D(Google, 2024). 보통 물체 주변의 4-16개 뷰를 출력하고, 가우시안 스플래팅이나 NeRF로 3D로 끌어올립니다.

### 텍스트-3D 파이프라인

| 모델 | 입력 | 출력 | 시간 |
|-------|-------|--------|------|
| DreamFusion (2022) | 텍스트 | SDS를 통한 NeRF | 자산당 약 1시간 |
| Magic3D | 텍스트 | 메시 + 텍스처 | 약 40분 |
| Shap-E (OpenAI, 2023) | 텍스트 | 암시적 3D | 약 1분 |
| SJC / ProlificDreamer | 텍스트 | NeRF / 메시 | 약 30분 |
| LRM (Meta, 2023) | 이미지 | 트라이플레인 | 약 5초 |
| InstantMesh (2024) | 이미지 | 메시 | 약 10초 |
| SV3D (Stability, 2024) | 이미지 | 신규 뷰 | 약 2분 |
| CAT3D (Google, 2024) | 이미지 1-64장 | 3D NeRF | 약 1분 |
| TripoSR (2024) | 이미지 | 메시 | 약 1초 |
| Meshy 4 (2025) | 텍스트 + 이미지 | PBR 메시 | 약 30초 |
| Rodin Gen-1.5 (2025) | 텍스트 + 이미지 | PBR 메시 | 약 60초 |
| Tencent Hunyuan3D 2.0 (2025) | 이미지 | 메시 | 약 30초 |

2025~2026년 방향: 게임 엔진에 맞는 PBR 소재를 갖춘 직접 텍스트-메시 모델. 범용 물체에는 멀티뷰 확산 중간 단계가 여전히 가장 잘 작동하는 레시피입니다.

### NeRF (참고용)

Neural Radiance Field(Mildenhall 외, 2020). 작은 MLP가 `(x, y, z, 뷰 방향)`을 받아 `(색, 밀도)`를 출력합니다. 광선을 따라 적분해 렌더링합니다. 품질은 메시 기반 신규 뷰 합성을 이기지만 렌더링이 100~1000배 느립니다. 대부분의 실시간 용도는 가우시안 스플래팅으로 대체되었지만 연구에서는 여전히 지배적입니다.

```figure
v4-3d-multiview
```

## 만들어 보기

`code/main.py`는 장난감 2D "가우시안 스플래팅" 피팅을 구현합니다: 합성 목표 이미지(매끄러운 그라데이션)를 2D 가우시안 스플랫들의 합으로 표현합니다. 경사 하강법으로 위치, 색, 공분산을 최적화해 목표와 일치시킵니다. 두 핵심 연산 — 순방향 렌더(스플랫 + 알파 합성)와 경사 하강법 피팅 — 를 직접 보게 됩니다.

### 단계 1: 2D 가우시안 스플랫

```python
def gaussian_at(x, y, gaussian):
    px, py = gaussian["pos"]
    sigma = gaussian["sigma"]
    d2 = (x - px) ** 2 + (y - py) ** 2
    return math.exp(-d2 / (2 * sigma * sigma))
```

### 단계 2: 스플랫을 합쳐 렌더

```python
def render(image_size, gaussians):
    img = [[0.0] * image_size for _ in range(image_size)]
    for g in gaussians:
        for y in range(image_size):
            for x in range(image_size):
                img[y][x] += g["color"] * gaussian_at(x, y, g)
    return img
```

진짜 3D 가우시안 스플래팅은 깊이순으로 가우시안을 정렬해 순서대로 알파 합성합니다. 우리 2D 장난감은 그냥 더하기만 합니다.

### 단계 3: 경사 하강법으로 피팅

```python
for step in range(steps):
    pred = render(size, gaussians)
    loss = mse(pred, target)
    gradients = compute_grads(pred, target, gaussians)
    update(gaussians, gradients, lr)
```

## 함정들

- **뷰 불일치.** 뷰 4개를 독립적으로 생성했는데 물체 구조에 대해 서로 다르게 그리면 3D 피팅이 흐릿해집니다. 해결: 공유 어텐션을 쓰는 멀티뷰 확산.
- **뒷면 환각.** 단일 이미지 → 3D는 보이지 않는 면을 지어내야 합니다. 품질은 들쑥날쑥합니다.
- **가우시안 스플랫 폭발.** 제약 없는 학습은 1,000만 스플랫까지 자라며 과적합됩니다. 밀도화 + 가지치기 휴리스틱(3D-GS 원본 논문에서)이 필수입니다.
- **위상 문제.** 암시적 필드(SDF)에서 온 메시는 구멍이나 자기 교차가 있는 경우가 많습니다. 출시 전에 리메셔(예: blender의 복셀 리메시)를 돌리세요.
- **학습 데이터 라이선스.** Objaverse는 라이선스가 섞여 있습니다; 상업적 사용은 모델마다 다릅니다.

## 사용해 보기

| 과제 | 2026년 선택 |
|------|-----------|
| 사진으로 장면 재구성 | 가우시안 스플래팅 (3DGS, Gsplat, Scaniverse) |
| 게임용 텍스트-3D 물체 | Meshy 4 또는 Rodin Gen-1.5 (PBR 출력) |
| 이미지-3D | Hunyuan3D 2.0, TripoSR, InstantMesh |
| 소수 이미지로 신규 뷰 합성 | CAT3D, SV3D |
| 동적 장면 재구성 | 4D Gaussian Splatting |
| 아바타 / 옷 입은 인간 | Gaussian Avatar, HUGS |
| 연구 / SOTA | 지난주에 나온 그것 |

게임이나 전자상거래 파이프라인에 프로덕션 3D를 출시하려면: Meshy 4 또는 Rodin Gen-1.5의 PBR 메시 출력이 Unity / Unreal에 바로 들어갑니다.

## 출시하기

`outputs/skill-3d-pipeline.md`로 저장하세요. 이 스킬은 3D 브리프(입력: 텍스트 / 이미지 한 장 / 이미지 몇 장; 출력: 메시 / 스플랫 / NeRF; 용도: 렌더 / 게임 / VR)를 받아 파이프라인(멀티뷰 확산 + 피팅, 또는 직접 메시 모델), 베이스 모델, 반복 예산, 위상 후처리, 필요한 소재 채널을 출력합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 가우시안 4개, 16개, 64개로 실행하세요. 목표 대비 최종 MSE를 보고합니다.
2. **보통.** 컬러 가우시안(RGB)으로 확장해 보세요. 재구성이 목표 색 패턴과 일치하는지 확인합니다.
3. **어려움.** gsplat이나 Nerfstudio로 사진 50장 촬영물에서 실제 물체를 재구성합니다. 피팅 시간과 홀드아웃 뷰에서의 최종 SSIM을 보고합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 3D Gaussian Splatting | "3DGS" | 3D 가우시안 구름으로 표현한 장면; 미분 가능한 알파 합성 렌더. |
| NeRF | "신경 방사 필드" | 3D 점에서 색 + 밀도를 출력하는 MLP; 광선 적분으로 렌더링. |
| 트라이플레인 | "2-D 평면 세 장" | 3D를 축에 정렬된 2D 특성 그리드 세 개로 분해; 체적보다 쌉니다. |
| SDS | "스코어 증류 샘플링" | 2D 확산 스코어를 의사 그래디언트로 써서 3D 모델을 학습시킵니다. |
| 멀티뷰 확산 | "한 번에 여러 뷰" | 일관된 카메라 뷰 배치를 출력하는 확산 모델. |
| PBR | "물리 기반 렌더링" | 알베도, 거칠기, 금속성, 노멀 채널을 가진 소재. |
| 밀도화 | "스플랫 키우기" | 3DGS 학습 휴리스틱: 그래디언트가 큰 영역에서 스플랫을 나누거나 복제. |

## 프로덕션 노트: 3D에는 아직 공유 기반이 없습니다

이미지(잠재 확산 + DiT)와 비디오(시공간 DiT)와 달리, 3D는 2026년 기준 지배적인 단일 런타임이 없습니다. 프로덕션 의사결정 트리는 표현에 따라 갈라집니다:

- **NeRF / 트라이플레인.** 추론은 광선 행진(ray-marching) + 샘플당 MLP 순전파입니다. 512² 렌더 하나에 수백만 번의 MLP 순전파가 필요합니다. 광선 샘플을 공격적으로 배칭하세요; SDPA/xformers가 적용됩니다.
- **멀티뷰 확산 + LRM 재구성.** 2단계 파이프라인입니다. 1단계(멀티뷰 DiT)는 레슨 07과 똑같은 확산 서버입니다. 2단계(LRM 트랜스포머)는 뷰들 위의 한 번에 끝나는 순전파입니다. 전체 지연 시간 프로필은 "확산 + 원샷" — 단계별 서빙 원시물을 그에 맞게 고르세요.
- **SDS / DreamFusion.** 추론이 아니라 자산별 최적화입니다. 요청 핸들러가 아니라 잡(job)을 만드세요.

대다수 2026년 제품의 정답은 "요청 시 멀티뷰 확산 모델을 돌리고, 비동기로 3DGS를 재구성하고, 실시간 뷰잉용으로는 3DGS를 서빙한다"입니다. GPU 추론 서버(빠름)와 오프라인 옵티마이저(느림) 사이에서 작업이 깔끔하게 갈라집니다.

## 더 읽을거리

- [Mildenhall 외 (2020). NeRF: Representing Scenes as Neural Radiance Fields](https://arxiv.org/abs/2003.08934) — NeRF.
- [Kerbl 외 (2023). 3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://arxiv.org/abs/2308.04079) — 3DGS.
- [Poole 외 (2022). DreamFusion: Text-to-3D using 2D Diffusion](https://arxiv.org/abs/2209.14988) — SDS.
- [Liu 외 (2023). Zero-1-to-3: Zero-shot One Image to 3D Object](https://arxiv.org/abs/2303.11328) — Zero123.
- [Shi 외 (2023). MVDream](https://arxiv.org/abs/2308.16512) — 멀티뷰 확산.
- [Hong 외 (2023). LRM: Large Reconstruction Model for Single Image to 3D](https://arxiv.org/abs/2311.04400) — LRM.
- [Gao 외 (2024). CAT3D: Create Anything in 3D with Multi-View Diffusion Models](https://arxiv.org/abs/2405.10314) — CAT3D.
- [Stability AI (2024). Stable Video 3D (SV3D)](https://stability.ai/research/sv3d) — SV3D.
