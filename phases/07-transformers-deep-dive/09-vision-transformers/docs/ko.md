# 비전 트랜스포머 (ViT)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 이미지는 패치의 격자입니다. 문장은 토큰의 격자입니다. 같은 트랜스포머가 둘 다 씹어 삼킵니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 7 · 05 (완전한 트랜스포머), 페이즈 4 · 03 (CNN), 페이즈 4 · 14 (비전 트랜스포머 입문)
**시간:** 약 45분

## 문제 상황

2020년 이전의 컴퓨터 비전은 합성곱이 곧 전부였습니다. ImageNet, COCO, 탐지 벤치마크의 모든 SOTA가 CNN 백본을 썼습니다. 트랜스포머는 언어 전용이라는 인식이었습니다.

Dosovitskiy et al. (2020) — "An Image is Worth 16x16 Words" — 은 합성곱을 아예 없애도 된다는 것을 보여 줬습니다. 이미지를 고정 크기 패치로 쪼개고, 각 패치를 임베딩으로 선형 프로젝션한 뒤, 그 시퀀스를 평범한 트랜스포머 인코더에 먹이면 됩니다. 충분한 규모(ImageNet-21k 사전 학습 이상)라면 ViT가 ResNet 기반 모델과 맞먹거나 앞섭니다.

ViT는 2026년의 더 넓은 흐름의 출발점이었습니다: 하나의 아키텍처, 많은 모달리티. Whisper는 오디오를 토큰화합니다. ViT는 이미지를 토큰화합니다. 로봇공학에는 행동 토큰, 비디오에는 픽셀 토큰. 트랜스포머는 상관없습니다 — 시퀀스를 먹이면 배웁니다.

2026년이면 ViT와 그 후손들(DeiT, Swin, DINOv2, ViT-22B, SAM 3)이 비전의 대부분을 차지합니다. CNN은 엣지 기기와 지연 시간에 민감한 과제에서 아직 이깁니다. 그 외 모든 곳의 스택 어딘가에는 ViT가 있습니다.

## 핵심 개념

![이미지 → 패치 → 토큰 → 트랜스포머](../assets/vit.svg)

### 단계 1 — 패치로 나누기(patchify)

`H × W × C` 이미지를 `N × (P·P·C)` 모양의 평평한 패치 시퀀스로 쪼갭니다. 전형적인 설정: `224 × 224` 이미지, `16 × 16` 패치 → 각각 768개 값으로 이뤄진 패치 196개.

```
image (224, 224, 3) → 14 × 14 grid of 16x16x3 patches → 196 vectors of length 768
```

패치 크기가 조절 손잡이입니다. 작은 패치 = 토큰이 많아지고 해상도는 좋아지지만 어텐션 비용은 이차원. 큰 패치 = 거칠지만 쌉니다.

### 단계 2 — 선형 임베딩

학습된 행렬 하나가 각 평평한 패치를 `d_model`로 프로젝션합니다. 커널 크기 `P`, 스트라이드 `P`짜리 합성곱과 동등합니다. PyTorch에서는 문자 그대로 `nn.Conv2d(C, d_model, kernel_size=P, stride=P)` — 두 줄짜리 구현입니다.

### 단계 3 — `[CLS]` 토큰 붙이기, 위치 임베딩 더하기

- 학습 가능한 `[CLS]` 토큰을 앞에 붙입니다. 분류에는 그 마지막 은닉 상태가 이미지 표현으로 쓰입니다.
- 학습 가능한 위치 임베딩(ViT 원조) 또는 사인 기반 2D(이후 변형들)를 더합니다.
- 2024년 이후로는 RoPE가 2D 위치로 확장됐고, 때로는 명시적 임베딩 없이 쓰입니다.

### 단계 4 — 표준 트랜스포머 인코더

`LayerNorm → Self-Attention → + → LayerNorm → MLP → +` 블록 L개를 쌓습니다. BERT와 완전히 동일합니다. 비전 전용 층은 없습니다. 이것이 논문의 교과서적 결론입니다.

### 단계 5 — 헤드

분류라면: `[CLS]` 은닉 상태 → linear → softmax. DINOv2나 SAM이라면: `[CLS]`를 버리고 패치 임베딩을 그대로 씁니다.

### 영향력 있었던 변형들

| 모델 | 연도 | 변화 |
|-------|------|--------|
| ViT | 2020 | 원조. 고정 패치 크기, 풀 전역 어텐션. |
| DeiT | 2021 | 증류(distillation); ImageNet-1k만으로 학습 가능. |
| Swin | 2021 | 이동 윈도우(shifted windows)를 쓰는 계층 구조. 고정된 준이차원 비용. |
| DINOv2 | 2023 | 자기지도 학습(레이블 없음). 가장 좋은 범용 비전 특성. |
| ViT-22B | 2023 | 22B 파라미터; 스케일링 법칙이 그대로 적용. |
| SigLIP | 2023 | ViT + 언어 쌍, 시그모이드 대조 손실. |
| SAM 3 | 2025 | Segment anything; ViT-Large + 프롬프트 가능한 마스크 디코더. |

### 왜 시간이 걸렸나

ViT가 CNN에 맞서려면 *많은* 데이터가 필요합니다. CNN의 귀납 편향(평행 이동 불변성, 지역성)을 하나도 갖고 있지 않기 때문입니다. 레이블된 이미지 1억 장을 넘거나 강한 자기지도 사전 학습이 없으면, 같은 연산량에서 CNN이 여전히 이깁니다. DeiT가 2021년 증류 트릭으로 이 문제를 줄였고, DINOv2가 2023년 자기지도 학습으로 영구히 해결했습니다.

```figure
n5-patch-stream
```

## 만들어 보기

`code/main.py`를 보세요. 순수 표준 라이브러리 패치 분할 + 선형 임베딩 + 온전성 검사입니다. 학습은 없습니다 — 현실적인 규모의 ViT에는 PyTorch와 수 시간의 GPU 시간이 필요하니까요.

### 단계 1: 가짜 이미지

`(R, G, B)` 튜플 행들의 목록으로 된 24 × 24 RGB 이미지. 6×6 패치를 씁니다 → 패치 16개, 각각 108차원 임베딩 벡터.

### 단계 2: 패치로 나누기

```python
def patchify(image, P):
    H = len(image)
    W = len(image[0])
    patches = []
    for i in range(0, H, P):
        for j in range(0, W, P):
            patch = []
            for di in range(P):
                for dj in range(P):
                    patch.extend(image[i + di][j + dj])
            patches.append(patch)
    return patches
```

래스터 순서: 격자를 행 우선으로 훑습니다. 모든 ViT가 이 순서를 씁니다.

### 단계 3: 선형 임베딩

각 평평한 패치에 무작위 `(patch_flat_size, d_model)` 행렬을 곱합니다. `[CLS]`를 앞에 붙인 뒤 출력 모양이 `(N_patches + 1, d_model)`인지 검증합니다.

### 단계 4: 현실적인 ViT의 파라미터 수 세기

ViT-Base의 파라미터 수를 출력합니다: 12층, 12헤드, d=768, patch=16. ResNet-50(약 25M)과 비교합니다. ViT-Base는 약 86M에 도달합니다. ViT-Large 약 307M. ViT-Huge 약 632M.

## 활용하기

```python
from transformers import ViTImageProcessor, ViTModel
import torch
from PIL import Image

processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
model = ViTModel.from_pretrained("google/vit-base-patch16-224-in21k")

img = Image.open("cat.jpg")
inputs = processor(img, return_tensors="pt")
out = model(**inputs).last_hidden_state   # (1, 197, 768): [CLS] + 196 patches
cls_emb = out[:, 0]                       # image representation
```

**DINOv2 임베딩이 2026년 이미지 특성의 기본값입니다.** 백본을 얼리고 작은 헤드 하나를 학습하면 됩니다. 분류, 검색, 탐지, 캡셔닝에 모두 동작합니다. Meta의 DINOv2 체크포인트는 텍스트가 아닌 모든 비전 과제에서 CLIP을 앞섭니다.

**패치 크기 고르기.** 작은 모델은 16×16(ViT-B/16)을 씁니다. 밀집 예측(세그멘테이션)은 8×8 또는 14×14(SAM, DINOv2)를 씁니다. 아주 큰 모델은 14×14를 씁니다.

## 출시하기

`outputs/skill-vit-configurator.md`를 보세요. 이 스킬은 데이터셋 크기, 해상도, 연산 예산이 주어진 새 비전 과제에 ViT 변형과 패치 크기를 골라 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행합니다. 패치 수가 `(H/P) * (W/P)`와 같고 평평한 패치 차원이 `P*P*C`와 같은지 검증합니다.
2. **보통.** 2D 사인 기반 위치 임베딩을 구현합니다 — 각 패치의 `row`와 `col`에 대해 서로 독립인 사인 코드 두 개를 이어 붙입니다. 작은 PyTorch ViT에 넣어 CIFAR-10에서 학습형 위치 임베딩과 정확도를 비교합니다.
3. **어려움.** 3층 ViT(PyTorch)를 만들어 MNIST 이미지 1,000장을 4×4 패치로 학습합니다. 테스트 정확도를 측정합니다. 이제 같은 1,000장으로 DINOv2 사전 학습을 추가합니다(단순화: 마스크된 패치로부터 패치 임베딩을 예측하도록 인코더만 학습). 정확도가 좋아지나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 패치 (Patch) | "비전 트랜스포머의 토큰" | 이미지의 `P × P × C` 영역 픽셀 값들을 편 평한 벡터. |
| 패치 분할 (Patchify) | "자르고 + 펼친다" | 이미지를 겹치지 않는 패치로 쪼개 각각을 벡터로 펼친다. |
| `[CLS]` 토큰 | "이미지 요약" | 앞에 붙는 학습형 토큰; 마지막 임베딩이 이미지 표현으로 쓰인다. |
| 귀납 편향 (Inductive bias) | "모델이 갖는 가정" | ViT는 CNN보다 사전 믿음이 적다; 그 차이를 메우려 더 많은 데이터가 필요하다. |
| DINOv2 | "자기지도 ViT" | 이미지 증강 + 모멘텀 교사로 레이블 없이 학습. 2026년 최고의 범용 이미지 특성. |
| SigLIP | "CLIP의 후계자" | ViT + 텍스트 인코더를 시그모이드 대조 손실로 학습; 같은 연산량에서 CLIP보다 낫다. |
| Swin | "윈도우 방식 ViT" | 국소 어텐션 + 이동 윈도우를 쓰는 계층형 ViT; 준이차원 비용. |
| 레지스터 토큰 (Register tokens) | "2023년의 트릭" | 어텐션 싱크(attention sink)를 흡수하는 여분의 학습형 토큰 몇 개; DINOv2 특성을 개선한다. |

## 더 읽을거리

- [Dosovitskiy et al. (2020). An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale](https://arxiv.org/abs/2010.11929) — ViT 논문.
- [Touvron et al. (2021). Training data-efficient image transformers & distillation through attention](https://arxiv.org/abs/2012.12877) — DeiT.
- [Liu et al. (2021). Swin Transformer: Hierarchical Vision Transformer using Shifted Windows](https://arxiv.org/abs/2103.14030) — Swin.
- [Oquab et al. (2023). DINOv2: Learning Robust Visual Features without Supervision](https://arxiv.org/abs/2304.07193) — DINOv2.
- [Darcet et al. (2023). Vision Transformers Need Registers](https://arxiv.org/abs/2309.16588) — DINOv2를 위한 레지스터 토큰 해법.
