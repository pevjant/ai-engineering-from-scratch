> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 오토인코더 & 변분 오토인코더(VAE)

> 평범한 오토인코더는 압축한 뒤 재구성합니다. 기억할 뿐, 생성하지는 않죠. 여기에 한 가지 트릭 — 코드가 가우시안처럼 보이게 강제하기 — 을 더하면 샘플러가 생깁니다. 그 단 하나의 트릭, 즉 `z = μ + σ·ε`의 재파라미터화(reparameterization) 때문에 2026년 여러분이 쓰는 모든 잠재 확산 및 플로우 매칭 이미지 모델의 입력에 VAE가 자리 잡은 것입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 3 · 02(역전파), 페이즈 3 · 07(CNN), 페이즈 8 · 01(분류)
**시간:** 약 75분

## 문제 상황

784픽셀 MNIST 숫자를 16개 숫자짜리 코드로 압축한 뒤 재구성해 봅시다. 평범한 오토인코더는 재구성 MSE를 훌륭히 달성하지만 코드 공간은 울퉁불퉁한 엉망입니다. 코드 공간에서 무작위 점을 골라 디코딩하면 잡음이 나옵니다. 샘플러가 없는 거죠. 그저 포장한 압축 모델일 뿐입니다.

여러분이 진짜 원하는 것은: (a) 코드 공간이 샘플링할 수 있는 깨끗하고 매끄러운 분포 — 이를테면 등방성 가우시안 `N(0, I)` — 이고, (b) 어떤 샘플을 디코딩해도 그럴듯한 숫자가 나오며, (c) 인코더와 디코더가 여전히 잘 압축하는 것입니다. 목표 셋, 아키텍처 하나, 손실 하나.

Kingma의 2013년 VAE는 이렇게 풉니다: 인코더가 *분포* `q(z|x) = N(μ(x), σ(x)²)`를 출력하도록 학습시키고, KL 벌점으로 그 분포를 사전 분포 `N(0, I)` 쪽으로 끌어당긴 뒤, 디코딩 전에 `q(z|x)`에서 `z`를 샘플링합니다. 추론 때는 인코더를 버리고, `z ~ N(0, I)`를 샘플링해 디코딩합니다. KL 벌점이 코드 공간을 구조화하는 주체입니다.

2026년 VAE는 단독으로 출시되는 일이 드뭅니다 — 순수 이미지 품질에서는 확산에 밀렸습니다 — 하지만 모든 잠재 확산 모델(SD 1/2/XL/3, Flux, AudioCraft)의 인코더로 선택받고 있습니다. VAE를 배우면 여러분이 쓰는 모든 이미지 파이프라인의 보이지 않는 첫 레이어를 배우는 셈입니다.

## 개념

![오토인코더 vs VAE: 재파라미터화 트릭](../assets/vae.svg)

**오토인코더.** `z = encoder(x)`, `x̂ = decoder(z)`, 손실 = `||x - x̂||²`. 코드 공간은 비구조적입니다.

**VAE 인코더.** 벡터 두 개를 출력합니다: `μ(x)`와 `log σ²(x)`. 이들이 `q(z|x) = N(μ, diag(σ²))`를 정의합니다.

**재파라미터화 트릭.** `q(z|x)`에서의 샘플링은 미분 가능하지 않습니다. 샘플을 `z = μ + σ·ε`(`ε ~ N(0, I)`)로 다시 씁니다. 이제 `z`는 `(μ, σ)`의 결정론적 함수에 파라미터가 아닌 순수 잡음을 더한 것이므로, 그래디언트가 `μ`와 `σ`를 통해 흐릅니다.

**손실.** 증거 하한(ELBO), 두 항:

```
loss = reconstruction + β · KL[q(z|x) || N(0, I)]
     = ||x - x̂||²  + β · Σ_i ( σ_i² + μ_i² - log σ_i² - 1 ) / 2
```

재구성 항은 `x̂`를 `x` 쪽으로 밀고, KL 항은 `q(z|x)`를 사전 분포 쪽으로 밉니다. 둘은 상충합니다. 작은 β(1 미만) = 샘플이 더 선명, 코드 공간은 덜 가우시안. 큰 β(1 초과) = 코드 공간은 더 깨끗, 샘플은 더 흐릿. β-VAE(Higgins, 2017)가 이 다이얼을 유명하게 만들고 분리 표현(disentanglement) 연구를 불러일으켰습니다.

**샘플링.** 추론 때: `z ~ N(0, I)`를 뽑아 디코더에 통과시킵니다. 순전파 한 번 — 확산 같은 반복 샘플링이 없습니다.

```figure
vae-latent-grid
```

## 만들어 보기

`code/main.py`는 numpy나 torch 없이 아주 작은 VAE를 구현합니다. 입력은 8차원 공간의 2성분 가우시안 혼합에서 뽑은 8차원 합성 데이터입니다. 인코더와 디코더는 은닉층 하나짜리 MLP입니다. tanh 활성화, 순전파, 손실, 그리고 손으로 쓴 역전파를 구현합니다. 프로덕션이 아니라 교육용입니다.

### 단계 1: 인코더 순전파

```python
def encode(x, enc):
    h = tanh(add(matmul(enc["W1"], x), enc["b1"]))
    mu = add(matmul(enc["W_mu"], h), enc["b_mu"])
    log_sigma2 = add(matmul(enc["W_sig"], h), enc["b_sig"])
    return mu, log_sigma2
```

`σ` 대신 `log σ²`을 써서 네트워크 출력이 제약 없이 나오게 합니다(σ의 softplus는 함정입니다 — σ ≈ 0에서 그래디언트가 죽습니다).

### 단계 2: 재파라미터화하고 디코딩하기

```python
def reparameterize(mu, log_sigma2, rng):
    eps = [rng.gauss(0, 1) for _ in mu]
    sigma = [math.exp(0.5 * lv) for lv in log_sigma2]
    return [m + s * e for m, s, e in zip(mu, sigma, eps)]

def decode(z, dec):
    h = tanh(add(matmul(dec["W1"], z), dec["b1"]))
    return add(matmul(dec["W_out"], h), dec["b_out"])
```

### 단계 3: ELBO

```python
def elbo(x, x_hat, mu, log_sigma2, beta=1.0):
    recon = sum((a - b) ** 2 for a, b in zip(x, x_hat))
    kl = 0.5 * sum(math.exp(lv) + m * m - lv - 1 for m, lv in zip(mu, log_sigma2))
    return recon + beta * kl, recon, kl
```

두 분포가 모두 가우시안이므로 KL은 닫힌 형태 그대로입니다. 수치 적분을 하지 마세요. 2026년에도 몬테카를로 KL 추정을 담아 출시하는 코드가 있는데 — 이유 없이 3배 느릴 뿐입니다.

### 단계 4: 생성

```python
def sample(dec, z_dim, rng):
    z = [rng.gauss(0, 1) for _ in range(z_dim)]
    return decode(z, dec)
```

이것이 생성 모델입니다. 다섯 줄.

## 함정들

- **사후 분포 붕괴(posterior collapse).** KL 항이 `q(z|x) → N(0, I)`를 너무 밀어붙여 `z`가 `x`에 대한 정보를 전혀 담지 못합니다. 해법: β 어닐링(β=0에서 시작해 1까지 올림), free bits, 또는 비활성 차원에는 KL 생략.
- **흐릿한 샘플.** 가우시안 디코더 우도는 MSE 재구성을 의미하는데, 이는 L2에 대한 베이즈 최적 해(평균)입니다 — 그럴듯한 숫자들의 평균은 흐릿한 숫자죠. 해법: 이산 디코더(VQ-VAE, NVAE), 또는 VAE는 인코더로만 쓰고 잠재 공간 위에 확산을 얹기(Stable Diffusion이 하는 것).
- **β가 너무 크고 너무 이르게.** 사후 분포 붕괴 참고. β≈0.01에서 시작해 서서히 올리세요.
- **잠재 차원이 너무 작음.** MNIST에는 16차원, ImageNet 256²에는 256차원, ImageNet 1024²에는 2048차원이 맞습니다. Stable Diffusion의 VAE는 512×512×3 → 64×64×4로 압축합니다(공간적으로 32배, 채널에서 32배의 다운샘플링).

## 사용해 보기

2026년 VAE 스택:

| 상황 | 선택 |
|-----------|------|
| 확산용 이미지 잠재 인코더 | Stable Diffusion VAE(`sd-vae-ft-ema`) 또는 Flux VAE |
| 오디오 잠재 인코더 | Encodec(Meta), SoundStream, 또는 DAC(Descript) |
| 비디오 잠재 공간 | Sora의 시공간 패치, Latte VAE, WAN VAE |
| 분리 표현 학습 | β-VAE, FactorVAE, TCVAE |
| 이산 잠재 공간(트랜스포머 모델링용) | VQ-VAE, RVQ (ResidualVQ) |
| 생성용 연속 잠재 공간 | 평범한 VAE, 그런 다음 그 잠재 공간에서 플로우/확산 모델을 조건화 |

잠재 확산 모델은 인코더와 디코더 사이에 확산 모델이 사는 VAE입니다. VAE가 거친 압축을 하고, 확산 모델이 무거운 일을 합니다. 비디오(VAE + 비디오 확산 DiT)와 오디오(Encodec + MusicGen 트랜스포머)도 같은 패턴입니다.

## 출시하기

`outputs/skill-vae-trainer.md`로 저장하세요.

이 스킬은 데이터셋 프로필 + 잠재 차원 목표 + 다운스트림 용도(재구성, 샘플링, 또는 잠재 확산 입력)를 받아 다음을 출력합니다: 아키텍처 선택(평범/β/VQ/RVQ), β 스케줄, 잠재 차원, 디코더 우도(가우시안 vs 범주형), 평가 계획(재구성 MSE, 차원별 KL, `q(z|x)`와 `N(0, I)` 사이 Fréchet 거리).

## 연습 문제

1. **쉬움.** `code/main.py`의 `β`를 `0.01`, `0.1`, `1.0`, `5.0`으로 바꿔 보세요. 최종 재구성 MSE와 KL을 기록합니다. 여러분의 합성 데이터에 파레토 최적인 β는 어느 것인가요?
2. **보통.** 가우시안 디코더 우도를 베르누이 우도(교차 엔트로피 손실)로 교체해 보세요. 같은 합성 데이터를 이진화한 버전에서 샘플 품질을 비교합니다.
3. **어려움.** `code/main.py`를 미니 VQ-VAE로 확장해 보세요: 연속적인 `z`를 K=32개 항목의 코드북에서의 최근접 이웃 탐색으로 교체합니다. 재구성 MSE를 비교하고, 코드북 항목이 몇 개나 쓰이는지 보고합니다(코드북 붕괴는 실제로 일어납니다).

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 오토인코더 | 인코딩-디코딩 네트워크 | `x → z → x̂`, MSE로 학습. 생성 모델이 아닙니다. |
| VAE | 샘플러를 단 오토인코더 | 인코더가 분포를 출력, KL 벌점이 코드 공간을 다듬습니다. |
| ELBO | 증거 하한 | `log p(x) ≥ recon - KL[q(z\|x) \|\| p(z)]`; `q = p(z\|x)`일 때 팽팽합니다. |
| 재파라미터화 | `z = μ + σ·ε` | 확률적 노드를 결정론적 부분 + 순수 잡음으로 다시 씀. 샘플링을 통한 역전파를 가능하게 합니다. |
| 사전 분포(Prior) | `p(z)` | 잠재 변수의 목표 분포, 보통 `N(0, I)`. |
| 사후 분포 붕괴 | "KL 항이 이김" | 인코더가 `x`를 무시하고 사전 분포를 출력; 디코더가 환각을 해야 합니다. |
| β-VAE | 조절 가능한 KL 가중치 | `loss = recon + β·KL`. β가 클수록 더 분리되지만 더 흐릿합니다. |
| VQ-VAE | 이산 잠재 공간 | 연속적인 `z`를 최근접 코드북 벡터로 교체; 트랜스포머 모델링을 가능하게 합니다. |

## 프로덕션 노트: 확산 서버에서 가장 뜨거운 경로는 VAE

Stable Diffusion / Flux / SD3 파이프라인에서 VAE는 요청마다 두 번 호출됩니다 — 인코딩 한 번(img2img / 인페인팅이라면), 디코딩 한 번. 1024²에서는 디코더 패스가 `128×128×16` 잠재 공간을 다시 `1024×1024×3`으로 업샘플링하기 때문에 파이프라인 전체에서 활성화 메모리 피크가 가장 큰 단일 지점이 되곤 합니다. 실전적 결과 두 가지:

- **디코드를 슬라이스하거나 타일하라.** `diffusers`는 `pipe.vae.enable_slicing()`과 `pipe.vae.enable_tiling()`을 제공합니다. 타일링은 작은 이음선 아티팩트를 치르고 `O(H·W)` 대신 `O(tile²)` 메모리를 씁니다. 소비자 GPU에서 1024² 이상에는 필수입니다.
- **bf16 디코더, 최종 리사이즈는 fp32 수치로.** SD 1.x VAE는 fp32로 출시되었고 1024² 이상에서 fp16으로 캐스팅하면 *조용히 NaN을 냅니다*. SDXL은 `madebyollin/sdxl-vae-fp16-fix`를 탑재합니다 — 항상 fp16-fix 변형을 선호하거나 bf16을 쓰세요.

## 더 읽을거리

- [Kingma & Welling (2013). Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) — VAE 논문.
- [Higgins 외 (2017). β-VAE: Learning Basic Visual Concepts with a Constrained Variational Framework](https://openreview.net/forum?id=Sy2fzU9gl) — 분리형 β-VAE.
- [van den Oord 외 (2017). Neural Discrete Representation Learning](https://arxiv.org/abs/1711.00937) — VQ-VAE.
- [Vahdat & Kautz (2021). NVAE: A Deep Hierarchical Variational Autoencoder](https://arxiv.org/abs/2007.03898) — 최고 수준의 이미지 VAE.
- [Rombach 외 (2022). High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) — Stable Diffusion; 인코더로서의 VAE.
- [Défossez 외 (2022). High Fidelity Neural Audio Compression](https://arxiv.org/abs/2210.13438) — Encodec, 오디오 VAE의 표준.
