> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 잠재 확산과 Stable Diffusion

> 512×512 이미지에 픽셀 공간 확산을 돌리는 것은 계산 자원의 전쟁 범죄입니다. Rombach 외(2022)는 이미지를 생성하는 데 786k 차원 전부가 필요 없다는 것을 알아챘습니다 — 의미 구조를 담을 만큼만 필요하고, 나머지는 별도의 디코더가 맡으면 됩니다. 확산을 VAE의 잠재 공간 안에서 돌리세요. 바로 이 아이디어가 Stable Diffusion입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 8 · 02(VAE), 페이즈 8 · 06(DDPM), 페이즈 7 · 09(ViT)
**시간:** 약 75분

## 문제 상황

512² 픽셀 공간 확산은 U-Net이 `[B, 3, 512, 512]` 모양 텐서를 다룬다는 뜻입니다. 5억 파라미터 U-Net 기준 샘플링 스텝 하나가 약 100 GFLOPS입니다. 50스텝이면 이미지 하나당 5 TFLOPS입니다. 10억 장의 이미지로 학습하면 계산 비용이 터무니없어집니다.

그 FLOPs 대부분은 지각적으로 중요하지 않은 디테일 — 손실 VAE가 압축해 버릴 고주파 텍스처 — 을 네트워크에 흘려 보내는 데 쓰입니다. Rombach의 아이디어: VAE(*1단계*)를 한 번 학습시켜 고정하고, 확산은 전부 4채널 64×64 잠재 공간(*2단계*)에서 돌립니다. 같은 U-Net으로 픽셀 수는 1/16. 비슷한 품질에 FLOPs는 약 64분의 1.

이것이 Stable Diffusion 레시피입니다. SD 1.x / 2.x는 `64×64×4` 잠재 위의 860M U-Net을, SDXL은 `128×128×4` 위의 2.6B U-Net을, SD3는 U-Net을 플로우 매칭을 쓰는 Diffusion Transformer(DiT)로 바꿨습니다. Flux.1-dev(Black Forest Labs, 2024)는 12B 파라미터 DiT-MMDiT를 실어 왔습니다. 모두 같은 2단계 기반 위에서 돌아갑니다.

## 개념

![잠재 확산: VAE 압축 + 잠재 공간에서의 확산](../assets/latent-diffusion.svg)

**따로 학습되는 두 단계.**

1. **1단계 — VAE.** 인코더 `E(x) → z`, 디코더 `D(z) → x`. 목표 압축률: 공간축마다 8배 다운샘플 + 채널을 조정해 전체 잠재 크기를 픽셀 수의 약 1/16으로. 손실 = 재구성(L1 + LPIPS 지각 손실) + KL(`z`를 지나치게 가우시안으로 강요하지 않도록 작은 가중치 — `z`에서 정확히 샘플링할 필요가 없기 때문입니다). 디코딩된 이미지가 선명해지도록 적대적 손실을 곁들여 학습하는 경우가 많습니다.

2. **2단계 — `z` 위의 확산.** `z = E(x_real)`를 데이터로 취급합니다. `z_t`의 잡음을 제거하도록 U-Net(또는 DiT)을 학습시킵니다. 추론 때는: 확산으로 `z_0`을 샘플링한 뒤 `x = D(z_0)`.

**텍스트 조건화.** 두 부품이 추가됩니다. 고정된 텍스트 인코더(SD 1.x는 CLIP-L, SD 2/XL은 CLIP-L+OpenCLIP-G, SD3와 Flux는 T5-XXL). 그리고 크로스 어텐션 주입: 모든 U-Net 블록이 `[Q = 이미지 특성, K = V = 텍스트 토큰]`을 받아 섞어 넣습니다. 텍스트가 이미지에 영향을 주는 유일한 통로가 이 토큰들입니다.

**손실 함수는 레슨 06과 동일합니다.** 잡음에 대한 같은 DDPM / 플로우 매칭 MSE입니다. 데이터 도메인만 바꾸면 됩니다.

## 아키텍처 변형

| 모델 | 연도 | 백본 | 잠재 모양 | 텍스트 인코더 | 파라미터 |
|-------|------|----------|--------------|--------------|--------|
| SD 1.5 | 2022 | U-Net | 64×64×4 | CLIP-L (77 토큰) | 860M |
| SD 2.1 | 2022 | U-Net | 64×64×4 | OpenCLIP-H | 865M |
| SDXL | 2023 | U-Net + refiner | 128×128×4 | CLIP-L + OpenCLIP-G | 2.6B + 6.6B |
| SDXL-Turbo | 2023 | 증류 | 128×128×4 | 동일 | 1-4스텝 샘플링 |
| SD3 | 2024 | MMDiT (multimodal DiT) | 128×128×16 | T5-XXL + CLIP-L + CLIP-G | 2B / 8B |
| Flux.1-dev | 2024 | MMDiT | 128×128×16 | T5-XXL + CLIP-L | 12B |
| Flux.1-schnell | 2024 | MMDiT 증류 | 128×128×16 | T5-XXL + CLIP-L | 12B, 1-4스텝 |

흐름: U-Net을 DiT(잠재 패치 위의 트랜스포머)로 교체, 텍스트 인코더 확대(프롬프트 충실도는 T5가 CLIP을 이김), 잠재 채널 증가(4 → 16이면 디테일 여유가 커짐).

```figure
noise-schedule
```

## 만들어 보기

`code/main.py`는 레슨 06의 DDPM 위에 장난감 1차원 "VAE"(시연용 항등 인코더 + 디코더; 진짜 VAE는 conv 네트워크)를 쌓고, classifier-free guidance로 클래스 조건화를 추가합니다. 원시 1차원 값 위에서든 인코딩된 값 위에서든 같은 확산 손실이 통한다는 것 — 핵심 통찰 — 을 보여 줍니다.

### 단계 1: 인코더/디코더

```python
def encode(x):    return x * 0.5          # 더 작은 스케일로의 장난감 "압축"
def decode(z):    return z * 2.0
```

진짜 VAE는 학습된 가중치를 갖습니다. 교육 목적에는 이 선형 사상만으로도 확산이 원래 데이터 공간을 신경 쓰지 않고 `z` 위에서 동작한다는 것을 보여 주기에 충분합니다.

### 단계 2: `z` 공간에서의 확산

레슨 06과 같은 DDPM입니다. 네트워크가 보는 데이터는 `z = E(x)`입니다. `z_0`을 샘플링한 뒤 `D(z_0)`로 디코드합니다.

### 단계 3: classifier-free guidance

학습 중에는 10% 확률로 클래스 레이블을 버립니다(null 토큰으로 대체). 추론 때는 `ε_cond`와 `ε_uncond`를 둘 다 계산한 뒤:

```python
eps_cfg = (1 + w) * eps_cond - w * eps_uncond
```

`w = 0`은 가이던스 없음(최대 다양성), `w = 3`이 기본값, `w = 7+`는 포화 / 과도하게 날카로움입니다.

### 단계 4: 텍스트 조건화(개념이지 코드가 아님)

클래스 레이블을 고정된 텍스트 인코더 출력으로 바꿉니다. 텍스트 임베딩을 크로스 어텐션으로 U-Net에 먹입니다:

```python
h = h + CrossAttention(Q=h, K=text_embed, V=text_embed)
```

클래스 조건부 확산 모델과 Stable Diffusion 사이의 실질적 차이는 이것 하나뿐입니다.

## 함정들

- **VAE 스케일 불일치.** SD 1.x VAE는 인코딩 뒤 곱해지는 스케일링 상수(`scaling_factor ≈ 0.18215`)가 있습니다. 이걸 잊으면 U-Net이 분산이 크게 틀린 잠재 벡터 위에서 학습됩니다. 모든 체크포인트가 하나씩 실어 나릅니다.
- **텍스트 인코더가 조용히 틀리는 문제.** SD3는 128토큰 이상의 T5-XXL이 필요하고, CLIP 전용으로 폴백하면 손실이 있습니다. 항상 `use_t5=True`를 확인하세요. 아니면 프롬프트 충실도가 폭락합니다.
- **잠재 공간 뒤섞기.** SDXL, SD3, Flux는 모두 다른 VAE를 씁니다. SDXL 잠재 위에서 학습된 LoRA는 SD3에서 작동하지 않습니다. Hugging Face diffusers 0.30+는 맞지 않는 체크포인트 로딩을 거부합니다.
- **CFG 과다.** `w > 10`은 포화되고 기름진 이미지를 만들며 다양성을 희생하고 프롬프트에 과적합됩니다. 적정선은 `w = 3-7`입니다.
- **네거티브 프롬프트 누수.** 빈 네거티브 프롬프트는 null 토큰이 되고, 내용이 채워진 네거티브 프롬프트는 `ε_uncond`가 됩니다. 이 둘은 같지 않은데, 어떤 파이프라인은 조용히 null을 기본값으로 씁니다.

## 사용해 보기

2026년 프로덕션 스택:

| 목표 | 추천 백본 |
|--------|----------------------|
| 좁은 도메인, 페어 데이터, 백지에서 모델 학습 | SDXL 파인튜닝(LoRA / 전체) — 출시가 가장 빠름 |
| 오픈 도메인 텍스트-이미지, 공개 가중치 | Flux.1-dev (12B, Apache / 비상업) 또는 SD3.5-Large |
| 가장 빠른 추론, 공개 가중치 | Flux.1-schnell (1-4스텝, Apache) 또는 SDXL-Lightning |
| 최고 프롬프트 충실도, 호스팅 | GPT-Image / DALL-E 3(여전히), Midjourney v7, Imagen 4 |
| 편집 워크플로 | Flux.1-Kontext (2024년 12월) — 이미지 + 텍스트를 네이티브로 받음 |
| 연구, 베이스라인 | SD 1.5 — 낡았지만 가장 많이 연구됨 |

## 출시하기

`outputs/skill-sd-prompter.md`로 저장하세요. 이 스킬은 텍스트 프롬프트 + 목표 스타일을 받아 모델 + 체크포인트, CFG 스케일, 샘플러, 네거티브 프롬프트, 해상도, 선택적 ControlNet/IP-Adapter 조합, 단계별 QA 체크리스트를 출력합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 가이던스 `w ∈ {0, 1, 3, 7, 15}`로 실행하세요. 클래스별 평균 샘플을 기록합니다. 몇 `w`에서 클래스 평균이 실제 데이터 평균을 넘어 벌어지나요?
2. **보통.** 장난감 선형 인코더를 재구성 손실을 곁들인 tanh-MLP 인코더/디코더 쌍으로 바꿔 보세요. 새 잠재 위에서 확산을 다시 학습시킵니다. 샘플 품질이 달라지나요?
3. **어려움.** diffusers로 진짜 Stable Diffusion 추론을 세팅하세요: `sdxl-base`를 로드하고 CFG=7로 Euler 30스텝을 돌려 시간을 잽니다. 이제 4스텝, CFG=0인 `sdxl-turbo`로 바꿉니다. 같은 소재, 다른 품질 — 무엇이 어떻게 바뀌었는지 설명해 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 1단계 | "그 VAE" | 학습된 인코더/디코더 쌍; 512²를 64²로 압축합니다. |
| 2단계 | "그 U-Net" | 잠재 공간 위의 확산 모델. |
| CFG | "가이던스 스케일" | `(1+w)·ε_cond - w·ε_uncond`; 조건화 강도를 조절합니다. |
| Null 토큰 | "빈 프롬프트 임베딩" | `ε_uncond`에 쓰이는 무조건부 임베딩. |
| 크로스 어텐션 | "텍스트가 들어오는 통로" | 각 U-Net 블록이 텍스트 토큰을 K와 V로 어텐션합니다. |
| DiT | "Diffusion Transformer" | U-Net을 잠재 패치 위의 트랜스포머로 교체; 더 잘 확장됩니다. |
| MMDiT | "멀티모달 DiT" | SD3의 아키텍처: 조인트 어텐션을 쓰는 텍스트·이미지 스트림. |
| VAE 스케일링 팩터 | "매직 넘버" | 잠재를 약 5.4로 나눠 확산이 단위 분산 공간에서 동작하게 합니다. |

## 프로덕션 노트: 8GB 소비자용 GPU에서 Flux-12B 돌리기

레퍼런스 Flux 통합은 "소비자용 GPU 하나 있는데 이걸 출시할 수 있나요?"의 정석 레시피입니다. 트릭은 프로덕션 추론 문헌이 열거하는 세 노브 레시피를 확산 DiT에 적용한 것입니다:

1. **교차 적재.** Flux는 VRAM에 동시에 존재할 필요가 없는 세 개의 네트워크를 갖습니다: T5-XXL 텍스트 인코더(fp32 기준 약 10 GB), CLIP-L(작음), 12B MMDiT, 그리고 VAE. 프롬프트를 먼저 인코딩하고, 인코더를 *삭제*, DiT를 로드해 잡음을 제거하고, DiT를 *삭제*, VAE를 로드해 디코드합니다. 소비자 8GB GPU에는 한 번에 한 단계만 들어갑니다.
2. **bitsandbytes 4비트 양자화.** T5 인코더와 DiT 양쪽에 `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)`. 메모리를 8배 줄이며, Aritra의 벤치마크(노트북에 링크됨)에 따르면 텍스트-이미지에서 품질 저하는 느낄 수 없는 수준입니다.
3. **CPU 오프로드.** `pipe.enable_model_cpu_offload()`는 순전파가 진행됨에 따라 모듈을 CPU와 GPU 사이에서 자동으로 교체합니다. 지연 시간이 10~20% 늘지만 파이프라인이 아예 돌아가게 만듭니다.

메모리 계산은 이렇습니다: 양자화된 T5는 `10 GB / 8 = 1.25 GB`, 양자화된 DiT는 `12 B 파라미터 × 0.5 바이트 = 약 6 GB`, 활성값까지. stas00의 말로 하자면 이것은 TP=1 추론의 극단 끝단입니다 — 모델 병렬화 없음, 최대 양자화. 프로덕션이라면 H100에서 TP=2나 TP=4로 돌리겠지만, 개발자 노트북 한 대라면 이것이 그 레시피입니다.

## 더 읽을거리

- [Rombach 외 (2022). High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) — Stable Diffusion.
- [Podell 외 (2023). SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis](https://arxiv.org/abs/2307.01952) — SDXL.
- [Peebles & Xie (2023). Scalable Diffusion Models with Transformers (DiT)](https://arxiv.org/abs/2212.09748) — DiT.
- [Esser 외 (2024). Scaling Rectified Flow Transformers for High-Resolution Image Synthesis](https://arxiv.org/abs/2403.03206) — SD3, MMDiT.
- [Ho & Salimans (2022). Classifier-Free Diffusion Guidance](https://arxiv.org/abs/2207.12598) — CFG.
- [Labs (2024). Flux.1 — Black Forest Labs announcement](https://blackforestlabs.ai/announcing-black-forest-labs/) — Flux.1 계열.
- [Hugging Face Diffusers docs](https://huggingface.co/docs/diffusers/index) — 위 모든 체크포인트의 레퍼런스 구현.
