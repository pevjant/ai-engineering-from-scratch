# 비전 트랜스포머 (ViT)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 이미지를 패치로 잘라서, 각 패치를 단어처럼 다루고, 평범한 트랜스포머를 돌리면 끝입니다. 더 이상 뒤돌아볼 필요 없습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 7 레슨 02(셀프 어텐션), 페이즈 4 레슨 04(이미지 분류)
**시간:** 약 45분

## 학습 목표

- 패치 임베딩, 학습된 위치 임베딩, 클래스 토큰, 트랜스포머 인코더 블록을 처음부터 직접 구현해서 최소한의 ViT를 만들어 봅니다
- DeiT와 MAE가 아니었다면 대규모 사전 학습 데이터가 꼭 필요하다고 여겨졌을 ViT의 역사를 설명할 수 있습니다
- ViT, Swin, ConvNeXt를 아키텍처가 담고 있는 사전 편향(prior) 관점에서 비교합니다(없음, 지역 윈도우 어텐션, 합성곱 백본)
- `timm`과 표준적인 선형 프로브/파인튜닝 레시피를 사용해 사전 학습된 ViT를 작은 데이터셋에 파인튜닝합니다

## 문제 상황

십 년 동안 합성곱은 컴퓨터 비전과 거의 동의어였습니다. CNN에는 지역성(locality), 이동 등변성(translation equivariance) 같은 강력한 귀납 편향(inductive bias)이 있었고, 아무도 이걸 대체할 수 없다고 생각했습니다. 그러다 Dosovitskiy 등(2020)이 합성곱 장치를 전혀 쓰지 않고, 펼쳐 놓은 이미지 패치에 그냥 트랜스포머를 적용했을 뿐인데 충분한 규모만 있으면 최고의 CNN과 맞먹거나 능가할 수 있음을 보여줬습니다.

문제는 "충분한 규모"였습니다. ImageNet-1k로만 학습한 ViT는 ResNet에 졌습니다. ImageNet-21k나 JFT-300M으로 사전 학습한 뒤 ImageNet-1k로 파인튜닝한 ViT는 ResNet을 이겼습니다. 결론은 이랬습니다. 트랜스포머에는 유용한 사전 편향이 없지만, 데이터가 충분하면 그 편향을 스스로 학습할 수 있다. 이후 연구들(DeiT, MAE, DINO)은 강한 증강, 자기지도 사전 학습, 증류 같은 올바른 학습 레시피만 있으면 ViT도 작은 데이터로 잘 학습할 수 있다는 걸 보여줬습니다.

2026년 현재도 순수 CNN은 엣지 디바이스에서 경쟁력이 있습니다(가장 강한 건 ConvNeXt입니다). 하지만 그 외 모든 분야는 트랜스포머가 지배합니다: 세그멘테이션(Mask2Former, SegFormer), 객체 검출(DETR, RT-DETR), 멀티모달(CLIP, SigLIP), 비디오(VideoMAE, VJEPA). 따라서 알아야 할 구조는 바로 ViT 블록입니다.

## 개념

### 파이프라인

```mermaid
flowchart LR
    IMG["이미지<br/>(3, 224, 224)"] --> PATCH["패치 임베딩<br/>conv 16x16 s=16<br/>-> (768, 14, 14)"]
    PATCH --> FLAT["펼쳐서<br/>(196, 768) 토큰으로"]
    FLAT --> CAT["[CLS] 토큰을<br/>맨 앞에 붙이기"]
    CAT --> POS["학습된 위치 임베딩<br/>더하기"]
    POS --> ENC["트랜스포머 인코더<br/>블록 N개"]
    ENC --> CLS["[CLS] 토큰의<br/>출력을 꺼내기"]
    CLS --> HEAD["MLP 분류기"]

    style PATCH fill:#dbeafe,stroke:#2563eb
    style ENC fill:#fef3c7,stroke:#d97706
    style HEAD fill:#dcfce7,stroke:#16a34a
```

일곱 단계입니다. 패치 -> 토큰 -> 어텐션 -> 분류기. 모든 변형(ViT, DeiT, Swin, ConvNeXt, MAE 사전 학습)은 이 일곱 단계 중 한두 가지만 바꾸고 나머지는 그대로 둡니다.

### 패치 임베딩

첫 번째 합성곱이 핵심입니다. 커널 크기 16, 스트라이드 16으로 설정하면 224x224 이미지가 16x16 패치 14x14 격자로 나뉘고, 각 패치가 768차원 임베딩으로 투영됩니다. 합성곱 하나가 패치 분할과 선형 투영을 동시에 해결하는 셈입니다.

```
Input:  (3, 224, 224)
Conv (3 -> 768, k=16, s=16, no padding):
Output: (768, 14, 14)
Flatten spatial: (196, 768)
```

패치 196개 = 토큰 196개. 각 토큰의 특성(feature) 차원은 768(ViT-B), 1024(ViT-L), 1280(ViT-H)입니다.

### 클래스 토큰

시퀀스 맨 앞에 붙이는 학습된 벡터 하나입니다.

```
tokens = [CLS; patch_1; patch_2; ...; patch_196]   shape (197, 768)
```

트랜스포머 블록 N개를 통과한 뒤의 `[CLS]` 출력이 이미지 전체의 표현(representation)입니다. 분류 헤드는 이 벡터 하나만 읽습니다.

### 위치 임베딩

트랜스포머에는 공간적 위치를 알려주는 장치가 내장돼 있지 않습니다. 그래서 모든 토큰에 학습된 벡터를 더해 줍니다.

```
tokens = tokens + learned_pos_embedding   (also shape (197, 768))
```

이 임베딩은 모델의 파라미터라서, 경사 하강법 기반 학습이 이를 2D 이미지 구조에 맞게 조정해 줍니다. 2D 사인파(sinusoidal) 방식도 있지만 실무에서는 거의 쓰이지 않습니다.

### 트랜스포머 인코더 블록

표준 구성입니다. 멀티헤드 셀프 어텐션, MLP, 잔차 연결(residual connection), pre-LayerNorm.

```
x = x + MSA(LN(x))
x = x + MLP(LN(x))

MLP is two-layer with GELU: Linear(d -> 4d) -> GELU -> Linear(4d -> d)
```

ViT-B/16은 이 블록을 12개 쌓고, 각 블록에 어텐션 헤드 12개를 둬서 총 8,600만 개의 파라미터를 가집니다.

### 왜 pre-LN인가

초기 트랜스포머는 post-LN(`x = LN(x + sublayer(x))`) 방식을 썼는데, 워밍업 없이는 6~8층 이상 깊게 학습하기가 어려웠습니다. pre-LN(`x = x + sublayer(LN(x))`)은 워밍업 없이도 훨씬 깊은 네트워크를 안정적으로 학습시킵니다. 모든 ViT와 모든 현대 LLM이 pre-LN을 사용합니다.

### 패치 크기의 트레이드오프

- 16x16 패치 -> 토큰 196개, 표준입니다.
- 32x32 패치 -> 토큰 49개, 빠르지만 해상도가 낮습니다.
- 8x8 패치 -> 토큰 784개, 더 정밀하지만 O(n^2) 어텐션 비용이 감당하기 어렵게 커집니다.

패치가 클수록 = 토큰이 적을수록 = 빠르지만 공간 디테일이 떨어집니다. SwinV2는 계층적 윈도우 안에서 4x4 패치를 사용합니다.

### ImageNet-1k만으로 ViT를 학습시키는 DeiT 레시피

원조 ViT가 CNN을 이기려면 JFT-300M이 필요했습니다. DeiT(Touvron 등, 2020)는 네 가지 변경으로 ViT-B를 ImageNet-1k만으로 학습시켜 top-1 정확도 81.8%를 달성했습니다.

1. 강한 증강: RandAugment, Mixup, CutMix, Random Erasing.
2. 확률적 깊이(stochastic depth, 학습 중 블록 전체를 무작위로 건너뜀).
3. 반복 증강(repeated augmentation, 같은 이미지를 배치당 3번 샘플링).
4. CNN 교사로부터의 증류(선택 사항, 정확도를 더 끌어올림).

오늘날 모든 ViT 학습 레시피는 DeiT에서 파생됐습니다.

### Swin vs ConvNeXt

- **Swin**(Liu 등, 2021) — 윈도우 기반 어텐션입니다. 각 블록은 지역 윈도우 안에서만 어텐션을 수행하고, 번갈아 등장하는 블록이 윈도우를 이동(shift)시켜 윈도우 사이의 정보를 섞습니다. 어텐션 연산자는 유지하면서 CNN 같은 지역성 편향을 되살린 접근입니다.
- **ConvNeXt**(Liu 등, 2022) — Swin의 아키텍처 선택(depthwise 합성곱, LayerNorm, GELU, inverted bottleneck)을 그대로 따라 하도록 재설계된 CNN입니다. 이를 통해 격차의 본질이 "어텐션 대 합성곱"이 아니라 "현대적인 학습 레시피 + 아키텍처"임이 밝혀졌습니다.

2026년 현재 ConvNeXt-V2와 Swin-V2 둘 다 프로덕션(운영 환경) 등급입니다. 올바른 선택은 추론 스택(ConvNeXt는 엣지용으로 컴파일이 더 잘 됩니다)과 사전 학습 코퍼스에 따라 달라집니다.

### MAE 사전 학습

마스크드 오토인코더(He 등, 2022): 패치의 75%를 무작위로 가리고(mask), 인코더는 보이는 25%만 처리하도록 학습시키고, 작은 디코더를 학습시켜 인코더 출력으로부터 가려진 패치를 복원합니다. 사전 학습이 끝나면 디코더는 버리고 인코더만 파인튜닝합니다.

MAE 덕분에 ViT를 ImageNet-1k만으로 학습할 수 있게 됐고, SOTA를 달성했으며, 지금은 ViT 자기지도 사전 학습의 기본 레시피입니다.

```figure
batchnorm-inference
```

## 만들어 보기

### 단계 1: 패치 임베딩

```python
import torch
import torch.nn as nn

class PatchEmbedding(nn.Module):
    def __init__(self, in_channels=3, patch_size=16, dim=192, image_size=64):
        super().__init__()
        assert image_size % patch_size == 0
        self.proj = nn.Conv2d(in_channels, dim, kernel_size=patch_size, stride=patch_size)
        num_patches = (image_size // patch_size) ** 2
        self.num_patches = num_patches

    def forward(self, x):
        x = self.proj(x)
        return x.flatten(2).transpose(1, 2)
```

합성곱 한 번, flatten 한 번, transpose 한 번. 이미지를 토큰으로 바꾸는 단계는 이게 전부입니다.

### 단계 2: 트랜스포머 블록

pre-LN, 멀티헤드 셀프 어텐션, GELU를 쓰는 MLP, 잔차 연결입니다.

```python
class Block(nn.Module):
    def __init__(self, dim, num_heads, mlp_ratio=4, dropout=0.0):
        super().__init__()
        self.ln1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * mlp_ratio),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * mlp_ratio, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        a, _ = self.attn(self.ln1(x), self.ln1(x), self.ln1(x), need_weights=False)
        x = x + a
        x = x + self.mlp(self.ln2(x))
        return x
```

`nn.MultiheadAttention`이 헤드 분할, 스케일된 점곱(scaled dot-product), 출력 투영을 모두 처리해 줍니다. `batch_first=True`로 지정해서 텐서 모양이 `(N, seq, dim)`이 되도록 합니다.

### 단계 3: ViT 완성

```python
class ViT(nn.Module):
    def __init__(self, image_size=64, patch_size=16, in_channels=3,
                 num_classes=10, dim=192, depth=6, num_heads=3, mlp_ratio=4):
        super().__init__()
        self.patch = PatchEmbedding(in_channels, patch_size, dim, image_size)
        num_patches = self.patch.num_patches
        self.cls_token = nn.Parameter(torch.zeros(1, 1, dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, dim))
        self.blocks = nn.ModuleList([
            Block(dim, num_heads, mlp_ratio) for _ in range(depth)
        ])
        self.ln = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, num_classes)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)

    def forward(self, x):
        x = self.patch(x)
        cls = self.cls_token.expand(x.size(0), -1, -1)
        x = torch.cat([cls, x], dim=1)
        x = x + self.pos_embed
        for blk in self.blocks:
            x = blk(x)
        x = self.ln(x[:, 0])
        return self.head(x)

vit = ViT(image_size=64, patch_size=16, num_classes=10, dim=192, depth=6, num_heads=3)
x = torch.randn(2, 3, 64, 64)
print(f"output: {vit(x).shape}")
print(f"params: {sum(p.numel() for p in vit.parameters()):,}")
```

약 280만 개의 파라미터로, CPU에서도 다룰 수 있는 아주 작은 ViT입니다. 진짜 ViT-B는 8,600만 개인데, 같은 클래스 정의에서 `dim=768, depth=12, num_heads=12`로 바꾸면 됩니다.

### 단계 4: 동작 확인 — 이미지 한 장 추론

```python
logits = vit(torch.randn(1, 3, 64, 64))
print(f"logits: {logits}")
print(f"probs:  {logits.softmax(-1)}")
```

오류 없이 실행되어야 합니다. 확률의 합은 1이 되어야 합니다.

## 사용해 보기

`timm`에는 ImageNet 사전 학습 가중치가 적용된 모든 ViT 변형이 들어 있습니다. 한 줄이면 됩니다.

```python
import timm

model = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=10)
```

2026년 현재 비전 트랜스포머의 프로덕션 기본 선택지는 `timm`입니다. ViT, DeiT, Swin, Swin-V2, ConvNeXt, ConvNeXt-V2, MaxViT, MViT, EfficientFormer 등 수십 가지 모델을 같은 API로 지원합니다.

멀티모달 작업(이미지 + 텍스트)에는 `transformers`로 CLIP, SigLIP, BLIP-2, LLaVA를 쓸 수 있습니다. 이들 모두의 이미지 인코더는 ViT 변형입니다.

## 출시하기

이 레슨에서 만드는 산출물:

- `outputs/prompt-vit-vs-cnn-picker.md` — 데이터셋 크기, 컴퓨팅 자원, 추론 스택을 근거로 ViT, ConvNeXt, Swin 중 하나를 골라 주는 프롬프트
- `outputs/skill-vit-patch-and-pos-embed-inspector.md` — ViT의 패치 임베딩과 위치 임베딩 모양이 모델이 기대하는 시퀀스 길이와 일치하는지 검증해서, 가장 흔한 포팅 버그를 잡아 주는 스킬

## 연습 문제

1. **(쉬움)** 위의 작은 ViT를 순전파(forward pass)하면서 모든 중간 텐서의 모양을 출력해 보세요. 확인할 것: 입력 `(N, 3, 64, 64)` -> 패치 `(N, 16, 192)` -> CLS 포함 `(N, 17, 192)` -> 분류기 입력 `(N, 192)` -> 출력 `(N, num_classes)`.
2. **(보통)** 사전 학습된 `timm` ViT-S/16을 레슨 4의 합성 CIFAR 데이터셋으로 파인튜닝해 보세요. 같은 데이터로 파인튜닝한 ResNet-18과 비교하고, 학습 시간과 최종 정확도를 보고하세요.
3. **(어려움)** 작은 ViT에 MAE 사전 학습을 구현해 보세요. 패치 75%를 가리고, 인코더 + 작은 디코더를 학습시켜 가려진 패치를 복원합니다. 사전 학습 전후로 합성 데이터에 대한 선형 프로브(linear-probe) 정확도를 평가하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 방식 | 실제 의미 |
|------|----------------|----------------------|
| 패치 임베딩 | "첫 번째 conv" | 커널 크기 = 스트라이드 = 패치 크기인 합성곱. 이미지를 토큰 임베딩 격자로 바꿈 |
| 클래스 토큰 | "[CLS]" | 토큰 시퀀스 맨 앞에 붙는 학습된 벡터. 최종 출력이 이미지 전체 표현이 됨 |
| 위치 임베딩 | "학습된 pos" | 모든 토큰에 더해지는 학습된 벡터. 트랜스포머가 각 패치의 위치를 알 수 있게 해 줌 |
| Pre-LN | "서브레이어 앞의 LayerNorm" | 안정적인 트랜스포머 변형: `LN(x + sublayer(x))` 대신 `x + sublayer(LN(x))` |
| 멀티헤드 어텐션 | "병렬 어텐션" | 표준 트랜스포머 어텐션을 num_heads개의 독립된 부분 공간으로 나눠 처리한 뒤 다시 이어 붙인 것 |
| ViT-B/16 | "Base, patch 16" | 표준 크기: dim=768, depth=12, heads=12, patch_size=16, image=224, 약 8,600만 파라미터 |
| DeiT | "데이터 효율적 ViT" | 강한 증강만으로 ImageNet-1k만을 사용해 학습한 ViT. 대규모 사전 학습 데이터셋이 반드시 필요한 건 아님을 증명함 |
| MAE | "마스크드 오토인코더" | 자기지도 사전 학습: 패치 75%를 가리고 복원. 현재 ViT 사전 학습의 지배적 레시피 |

## 더 읽을거리

- [An Image is Worth 16x16 Words (Dosovitskiy et al., 2020)](https://arxiv.org/abs/2010.11929) — ViT 원 논문
- [DeiT: Data-efficient Image Transformers (Touvron et al., 2020)](https://arxiv.org/abs/2012.12877) — ImageNet-1k만으로 ViT 학습하기
- [Masked Autoencoders are Scalable Vision Learners (He et al., 2022)](https://arxiv.org/abs/2111.06377) — MAE 사전 학습
- [timm 문서](https://huggingface.co/docs/timm) — 프로덕션에서 쓰게 될 모든 비전 트랜스포머의 레퍼런스
