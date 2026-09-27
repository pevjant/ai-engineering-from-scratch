> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 조건부 GAN과 Pix2Pix

> 2014~2017년의 첫 번째 큰 돌파구는 GAN이 만들어낼 것을 통제하는 것이었습니다. 레이블을 붙이거나, 이미지를 붙이거나, 문장을 붙이면 됩니다. Pix2Pix는 이미지 버전을 해냈고, 좁은 이미지-이미지 과제에서는 지금도 모든 범용 텍스트-이미지 모델을 이깁니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 8 · 03(GAN), 페이즈 4 · 06(U-Net), 페이즈 3 · 07(CNN)
**시간:** 약 75분

## 문제 상황

비조건부(unconditional) GAN은 임의의 얼굴을 샘플링합니다. 데모로는 유용하지만 프로덕션(운영 환경)에서는 쓸모가 없죠. 여러분이 원하는 것은 이런 것들입니다: *스케치를 사진으로 바꾸기*, *지도를 항공 사진으로 바꾸기*, *낮 풍경을 밤 풍경으로 바꾸기*, *흑백 이미지에 색 입히기*. 이 모든 경우 입력 이미지 `x`가 주어지고, 의미상 대응 관계가 있는 `y`를 출력해야 합니다. `x` 하나에 그럴듯한 `y`는 여러 개 있습니다. 평균 제곱 오차(MSE)는 이것들을 뭉개서 흐릿한 덩어리로 만듭니다. 적대적 손실은 그렇지 않습니다. "진짜처럼 보임"은 날카로운 신호이기 때문입니다.

조건부 GAN(Conditional GAN, Mirza & Osindero, 2014)은 조건 `c`를 `G`와 `D` 양쪽의 입력으로 추가합니다. Pix2Pix(Isola 외, 2017)는 이를 특수화했습니다: 조건은 입력 이미지 전체, 생성자는 U-Net, 판별자는 *패치 기반* 분류기(PatchGAN), 손실은 적대적 손실 + L1. 이 레시피는 2026년에도 좁은 이미지-이미지 도메인에서는 백지에서 시작하는 텍스트-이미지 모델을 능가합니다. *페어 데이터*로 학습하기 때문입니다 — 정확히 필요한 신호를 손에 쥐고 있는 셈이죠.

## 개념

![Pix2Pix: U-Net 생성자, PatchGAN 판별자](../assets/pix2pix.svg)

**조건부 G.** `G(x, z) → y`. Pix2Pix에서 `z`는 G 내부의 드롭아웃입니다(입력 잡음 없음 — Isola는 명시적 잡음이 무시된다는 사실을 발견했습니다).

**조건부 D.** `D(x, y) → [0, 1]`. 입력은 (조건, 출력) *페어*입니다. 여기가 핵심 차이입니다: D는 `y`가 진짜처럼 보이는지뿐 아니라 `y`가 `x`와 일관된지를 판단해야 합니다.

**U-Net 생성자.** 병목(bottleneck)을 가로지르는 스킵 연결을 갖춘 인코더-디코더. 입력과 출력이 저수준 구조(에지, 실루엣)를 공유하는 과제에 결정적입니다. 스킵이 없으면 고주파 디테일이 사라집니다.

**PatchGAN 판별자.** 진짜/가짜 점수 하나를 출력하는 대신, D는 `N×N` 그리드를 출력하고 각 칸은 약 70×70 픽셀 수용 영역(receptive field)을 판정합니다. 그리드 값은 평균 냅니다. 이것은 마르코프 랜덤 필드 가정입니다: 사실성은 국소적이라는 것이죠. 훨씬 빠르게 학습되고, 파라미터도 적으며, 출력도 더 선명합니다.

**손실.**

```
loss_G = -log D(x, G(x)) + λ · ||y - G(x)||_1
loss_D = -log D(x, y) - log (1 - D(x, G(x)))
```

L1 항은 학습을 안정화하고 G를 알려진 타깃 쪽으로 밀어갑니다. L1은 L2보다 선명한 에지를 줍니다(평균이 아니라 중앙값의 효과). `λ = 100`이 Pix2Pix의 기본값이었습니다.

## CycleGAN — 페어가 없을 때

Pix2Pix는 페어가 맞는 `(x, y)` 데이터가 필요합니다. CycleGAN(Zhu 외, 2017)은 추가 손실 하나 — *순환 일관성(cycle consistency)* 손실 — 을 대가로 이 요구사항을 없앱니다. 생성자 두 개, `G: X → Y`와 `F: Y → X`. `F(G(x)) ≈ x`이고 `G(F(y)) ≈ y`가 되도록 학습시킵니다. 이렇게 하면 페어 예시 없이도 말을 얼룩말로, 여름을 겨울로 바꿀 수 있습니다.

2026년에는 페어 없는 이미지-이미지 변환을 CycleGAN보다 확산(ControlNet, IP-Adapter)으로 처리하는 경우가 대부분입니다. 하지만 순환 일관성 아이디어는 페어 없는 도메인 적응 논문 거의 모두에서 살아 있습니다.

```figure
gx-patchgan
```

## 만들어 보기

`code/main.py`는 1차원 데이터로 아주 작은 조건부 GAN을 구현합니다. 조건 `c`는 클래스 레이블(0 또는 1)입니다. 과제: 주어진 클래스의 조건부 분포에서 샘플을 만들어 냅니다.

### 단계 1: G와 D 양쪽 입력에 조건 붙이기

```python
def G(z, c, params):
    return mlp(concat([z, one_hot(c)]), params)

def D(x, c, params):
    return mlp(concat([x, one_hot(c)]), params)
```

원-핫 인코딩이 가장 단순한 방법입니다. 더 큰 모델은 학습된 임베딩, FiLM 변조, 크로스 어텐션을 씁니다.

### 단계 2: 조건부 학습

```python
for step in range(steps):
    x, c = sample_real_conditional()
    noise = sample_noise()
    update_D(x_real=x, x_fake=G(noise, c), c=c)
    update_G(noise, c)
```

생성자는 주변 분포(marginal)가 아니라 *주어진 조건에 대한* 실제 분포를 맞춰야 합니다.

### 단계 3: 클래스별 출력 검증

```python
for c in [0, 1]:
    samples = [G(noise, c) for noise in batch]
    mean_c = mean(samples)
    assert_near(mean_c, real_mean_for_class_c)
```

## 함정들

- **조건이 무시됨.** G는 주변화해 버리는 법을 배우고, 조건 신호가 약해서 D는 결코 벌주지 않습니다. 해결: D를 더 공격적으로 조건화하세요(마지막 층뿐 아니라 초기 층에서), projection 판별자를 쓰세요(Miyato & Koyama 2018).
- **L1 가중치가 너무 낮음.** G가 충실한 출력이 아니라 그럴듯해 보이기만 하는 임의의 출력으로 흘러갑니다. Pix2Pix 스타일 과제는 λ≈100에서 시작하세요.
- **L1 가중치가 너무 높음.** L1도 결국 L_p 노름이므로 G가 흐릿한 출력을 냅니다. 학습이 안정되면 서서히 낮추세요.
- **D에 정답이 새는 문제.** D 입력에는 `y`만이 아니라 `(x, y)`를 연결해 넣으세요. 이게 없으면 D는 일관성을 검사할 수 없습니다.
- **클래스별 모드 붕괴.** 각 클래스가 독립적으로 붕괴할 수 있습니다. 클래스 조건부 다양성 검사를 돌리세요.

## 사용해 보기

2026년 현재 이미지-이미지 과제의 상황:

| 과제 | 최선의 접근 |
|------|---------------|
| 스케치 → 사진, 같은 도메인, 페어 데이터 | Pix2Pix / Pix2PixHD (여전히 빠르고, 여전히 선명) |
| 스케치 → 사진, 페어 없음 | Scribble 조건 모델을 얹은 ControlNet |
| 시맨틱 세그멘테이션 → 사진 | SPADE / GauGAN2 또는 SD + ControlNet-Seg |
| 스타일 변환 | IP-Adapter나 LoRA를 곁들인 확산; GAN 방식은 레거시 |
| 깊이 → 사진 | Stable Diffusion 위의 ControlNet-Depth |
| 초해상도 | Real-ESRGAN(GAN), ESRGAN-Plus, 또는 SD-Upscale(확산) |
| 채색 | ColTran, 확산 기반 채색기, 또는 Pix2Pix-color |
| 낮 → 밤, 계절, 날씨 | CycleGAN 또는 ControlNet 기반 |

Pix2Pix는 (a) 페어 예시가 수천 개 있고, (b) 과제가 좁고 반복 가능하며, (c) 빠른 추론이 필요할 때 여전히 맞는 도구입니다. 범용 오픈 도메인 과제에서는 확산이 이깁니다.

## 출시하기

`outputs/skill-img2img-chooser.md`로 저장하세요. 이 스킬은 과제 설명, 데이터 가용성(페어 여부, 샘플 수 N), 지연 시간/품질 예산을 받아서 접근 방식(Pix2Pix, CycleGAN, ControlNet 변형, SDXL + IP-Adapter), 학습 데이터 요구사항, 추론 비용, 평가 프로토콜(LPIPS, FID, 과제별 지표)을 출력합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 고쳐 세 번째 클래스를 추가하세요. G가 여전히 각 클래스의 잡음을 올바른 모드로 사상하는지 확인합니다.
2. **보통.** 1차원 설정에서 L1을 지각 스타일 손실로 교체해 보세요(예: 특성(feature) 추출기 역할을 하는 작은 고정 D). 조건부 분포의 선명도가 달라지나요?
3. **어려움.** 1차원 설정에서 CycleGAN을 스케치해 보세요: 분포 두 개, 생성자 두 개, 순환 손실. 페어 데이터 없이 두 분포 사이를 사상하는 법을 배우는지 보여주세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 조건부 GAN | "레이블 달린 GAN" | G(z, c), D(x, c). 두 네트워크 모두 조건을 봅니다. |
| Pix2Pix | "이미지-이미지 GAN" | U-Net G와 PatchGAN D + L1 손실을 쓰는 페어 cGAN. |
| U-Net | "스킵 있는 인코더-디코더" | 대칭 합성곱 네트워크; 스킵이 고주파를 지켜 줍니다. |
| PatchGAN | "국소 사실성 분류기" | D가 전역 점수 대신 패치별 점수를 출력합니다. |
| CycleGAN | "페어 없는 이미지 변환" | 생성자 두 개 + 순환 일관성 손실; 페어 데이터 불필요. |
| SPADE | "GauGAN" | 시맨틱 맵으로 중간 활성값을 정규화; 세그멘테이션-이미지 변환. |
| FiLM | "특성별 선형 변조" | 조건으로부터 특성별 아핀 변환; 값싼 조건화 방식. |

## 프로덕션 노트: 지연 시간 한정 베이스라인으로서의 Pix2Pix

페어 데이터와 좁은 과제(스케치 → 렌더링, 시맨틱 맵 → 사진, 낮 → 밤)가 있을 때, Pix2Pix의 한 번에 끝나는 추론은 지연 시간에서 확산을 한 자릿수 앞섭니다. 프로덕션 비교는 보통 이렇습니다:

| 방식 | 스텝 수 | L4 한 장에서 512² 기준 전형적 지연 시간 |
|------|-------|----------------------------------------|
| Pix2Pix (U-Net 순전파) | 1 | ~30 ms |
| SD-Inpaint 또는 SD-Img2Img | 20 | ~1.2 s |
| SDXL-Turbo Img2Img | 1-4 | ~0.15-0.35 s |
| ControlNet + SDXL base | 20-30 | ~3-5 s |

정적 배치(모든 요청이 같은 FLOPs)에서는 처리량이 Pix2Pix의 승리입니다. 품질과 일반화에서는 확산이 이깁니다. 요즘 흔한 전략은 좁은 과제용으로 Pix2Pix 스타일 증류 모델을 출시하고, 꼬리(tail) 입력용으로 확산 폴백을 두는 것입니다.

## 더 읽을거리

- [Mirza & Osindero (2014). Conditional Generative Adversarial Nets](https://arxiv.org/abs/1411.1784) — cGAN 원조 논문.
- [Isola 외 (2017). Image-to-Image Translation with Conditional Adversarial Networks](https://arxiv.org/abs/1611.07004) — Pix2Pix.
- [Zhu 외 (2017). Unpaired Image-to-Image Translation using Cycle-Consistent Adversarial Networks](https://arxiv.org/abs/1703.10593) — CycleGAN.
- [Wang 외 (2018). High-Resolution Image Synthesis with Conditional GANs](https://arxiv.org/abs/1711.11585) — Pix2PixHD.
- [Park 외 (2019). Semantic Image Synthesis with Spatially-Adaptive Normalization](https://arxiv.org/abs/1903.07291) — SPADE / GauGAN.
- [Miyato & Koyama (2018). cGANs with Projection Discriminator](https://arxiv.org/abs/1802.05637) — projection D.
