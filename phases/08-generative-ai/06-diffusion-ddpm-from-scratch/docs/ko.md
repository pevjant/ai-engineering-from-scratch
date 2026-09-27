> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 확산 모델 — DDPM 밑바닥부터

> Ho, Jain, Abbeel(2020)은 이 분야가 벗어날 수 없는 레시피를 주었습니다. 데이터를 천 번의 작은 단계에 걸쳐 잡음으로 망가뜨립니다. 그 잡음을 예측하는 신경망 하나를 학습시킵니다. 추론 때는 과정을 거꾸로 돌립니다. 오늘날 모든 주류 이미지, 비디오, 3D, 음악 모델이 이 루프 위에서 돌아갑니다. 위에 플로우 매칭이나 일관성(consistency) 트릭이 얹혀 있기도 하고요.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 3 · 02(역전파), 페이즈 8 · 02(VAE)
**시간:** 약 75분

## 문제 상황

여러분이 원하는 것은 `p_data(x)`의 샘플러입니다. GAN은 자주 발산하는 미니맥스 게임을 하고, VAE는 가우시안 디코더에서 흐릿한 샘플을 냅니다. 진짜로 원하는 것은 (a) 하나의 안정적인 손실(안장점도, 미니맥스도 없음), (b) `log p(x)`의 하한(가능도를 얻을 수 있음), (c) SOTA 품질에 맞먹는 샘플인 학습 목표입니다.

Sohl-Dickstein 외(2015)가 이론적 답을 내놓았습니다: 가우시안 잡음을 서서히 더하는 마르코프 연쇄 `q(x_t | x_{t-1})`를 정의하고, 잡음을 제거하는 역 연쇄 `p_θ(x_{t-1} | x_t)`를 학습시키자는 것이죠. Ho, Jain, Abbeel(2020)은 이 손실이 한 줄 — 잡음 예측 — 로 단순화될 수 있음을 보이고 수학을 다듬었습니다. 2020년엔 흥미로운 발견이었고, 2021년엔 최고 수준의 샘플을 만들었고, 2022년엔 Stable Diffusion이 되었고, 2026년엔 모든 것의 기반이 되었습니다.

## 개념

![DDPM: 순방향 잡음 추가, 역방향 잡음 제거](../assets/ddpm.svg)

**순방향 과정 `q`.** `T`번의 작은 단계에 걸쳐 가우시안 잡음을 더합니다. 닫힌 형태 — 수학이 다루기 쉬운 이유 — 는 누적 단계 역시 가우시안이라는 점입니다:

```
q(x_t | x_0) = N( sqrt(α̅_t) · x_0,  (1 - α̅_t) · I )
```

여기서 `α̅_t = ∏_{s=1..t} (1 - β_s)`이고 `β_t`는 스케줄입니다. T=1000스텝에 걸쳐 `β_t`를 1e-4부터 0.02까지 선형으로 고르면 `x_T`는 대략 `N(0, I)`가 됩니다.

**역방향 과정 `p_θ`.** 더해진 잡음을 예측하는 신경망 `ε_θ(x_t, t)`를 학습합니다. `x_t`가 주어지면 다음으로 잡음을 제거합니다:

```
x_{t-1} = (1 / sqrt(α_t)) · ( x_t - (β_t / sqrt(1 - α̅_t)) · ε_θ(x_t, t) )  +  σ_t · z
```

여기서 `σ_t`는 `sqrt(β_t)`이거나 학습된 분산입니다. 식은 지저분하지만 그저 대수일 뿐입니다 — 사후 분포 `q(x_{t-1} | x_t, x_0)`에서 `x_{t-1}`을 풀고, `x_0`을 잡음 예측으로부터의 추정값으로 대입한 것입니다.

**학습 손실.**

```
L_simple = E_{x_0, t, ε} [ || ε - ε_θ( sqrt(α̅_t) · x_0 + sqrt(1 - α̅_t) · ε,  t ) ||² ]
```

데이터에서 `x_0`을 샘플링하고, 무작위 `t`를 고르고, `ε ~ N(0, I)`를 샘플링하고, 닫힌 형태로 한 번에 잡음 섞인 `x_t`를 계산한 뒤, 잡음에 대해 회귀합니다. 손실 하나, 미니맥스 없음, KL 없음, 재파라미터화 트릭 없음.

**샘플링.** `x_T ~ N(0, I)`에서 시작합니다. `t = T`부터 `1`까지 역방향 단계를 반복합니다. 끝.

## 작동하는 이유

세 가지 직관:

1. **잡음 제거는 쉽고, 생성은 어렵다.** `t=T`에서는 데이터가 순수한 잡음 — 네트워크는 사소한 문제를 풀어야 합니다. `t=0`에서는 네트워크가 몇 픽셀만 닦으면 됩니다. 중간 `t`에서는 문제가 어렵지만, 같은 가중치로 모든 잡음 수준에서 그래디언트가 흘러 들어옵니다.

2. **옷을 갈아입은 스코어 매칭.** Vincent(2011)가 증명했듯, 잡음을 예측하는 것은 *스코어*인 `∇_x log q(x_t | x_0)`를 추정하는 것과 같습니다. 역방향 SDE는 이 스코어로 밀도의 그래디언트를 따라 올라갑니다 — 높은 확률 영역을 향한 안내된 무작위 보행이죠.

3. **ELBO는 단순 MSE로 줄어든다.** 완전한 변분 하한에는 타임스텝마다 KL 항이 있습니다. DDPM의 파라미터화에서는 이 KL 항들이 특정 계수를 곱한 잡음 예측 MSE로 단순화되는데, Ho는 계수를 버렸고("simple" 손실이라 불렀죠) 품질은 오히려 *좋아졌습니다*.

```figure
diffusion-denoise
```

## 만들어 보기

`code/main.py`는 1차원 DDPM을 구현합니다. 데이터는 두 모드 혼합입니다. "네트워크"는 `(x_t, t)`를 받아 예측 잡음을 출력하는 작은 MLP입니다. 학습은 한 줄짜리 손실이고, 샘플링은 역 연쇄를 반복합니다.

### 단계 1: 순방향 스케줄(닫힌 형태)

```python
betas = [1e-4 + (0.02 - 1e-4) * t / (T - 1) for t in range(T)]
alphas = [1 - b for b in betas]
alpha_bars = []
cum = 1.0
for a in alphas:
    cum *= a
    alpha_bars.append(cum)
```

### 단계 2: `x_t`를 한 번에 샘플링

```python
def forward_sample(x0, t, alpha_bars, rng):
    a_bar = alpha_bars[t]
    eps = rng.gauss(0, 1)
    x_t = math.sqrt(a_bar) * x0 + math.sqrt(1 - a_bar) * eps
    return x_t, eps
```

### 단계 3: 학습 스텝 한 번

```python
def train_step(x0, model, alpha_bars, rng):
    t = rng.randrange(T)
    x_t, eps = forward_sample(x0, t, alpha_bars, rng)
    eps_hat = model_forward(model, x_t, t)
    loss = (eps - eps_hat) ** 2
    return loss, gradient_step(model, ...)
```

### 단계 4: 역방향 샘플링

```python
def sample(model, alpha_bars, T, rng):
    x = rng.gauss(0, 1)
    for t in range(T - 1, -1, -1):
        eps_hat = model_forward(model, x, t)
        beta_t = 1 - alphas[t]
        x = (x - beta_t / math.sqrt(1 - alpha_bars[t]) * eps_hat) / math.sqrt(alphas[t])
        if t > 0:
            x += math.sqrt(beta_t) * rng.gauss(0, 1)
    return x
```

40타임스텝과 24유닛 MLP짜리 1차원 문제에서, 이 코드는 약 200 에포크 만에 두 모드 혼합을 배웁니다.

## 시간 조건화

네트워크는 지금 몇 번째 타임스텝의 잡음을 제거하는지 알아야 합니다. 표준 옵션 두 가지:

- **사인파 임베딩.** 트랜스포머 위치 인코딩과 같습니다. `embed(t) = [sin(t/ω_0), cos(t/ω_0), sin(t/ω_1), ...]`. MLP에 통과시킨 뒤 네트워크에 브로드캐스트합니다.
- **FiLM / 그룹 정규화 조건화.** 임베딩을 각 블록에서 채널별 스케일/바이어스(FiLM)로 사영합니다.

우리 장난감 코드는 사인파 → concat을 씁니다. 프로덕션 U-Net은 FiLM을 씁니다.

## 함정들

- **스케줄이 정말 중요합니다.** 선형 `β`가 DDPM 기본값이지만 코사인 스케줄(Nichol & Dhariwal, 2021)은 같은 계산량으로 더 좋은 FID를 줍니다. 품질이 정체되면 스케줄을 바꿔 보세요.
- **타임스텝 임베딩은 깨지기 쉽습니다.** 원시 `t`를 float로 넘기는 방식은 1차원 장난감에서는 통하지만 이미지에서는 실패합니다. 항상 제대로 된 임베딩을 쓰세요.
- **V-예측 vs ε-예측.** 좁은 구간(아주 작거나 아주 큰 t)에서는 `ε`의 신호 대 잡음비가 나쁩니다. V-예측(`v = α·ε - σ·x`)이 더 안정적입니다. SDXL, SD3, Flux가 이를 씁니다.
- **Classifier-free guidance.** 추론 때 조건부와 무조건부 `ε`를 둘 다 계산한 뒤, `w ≈ 3-7`로 `ε_cfg = (1 + w) · ε_cond - w · ε_uncond`를 계산합니다. 레슨 08에서 다룹니다.
- **1000스텝은 너무 많습니다.** 프로덕션은 DDIM(20-50스텝), DPM-Solver(10-20스텝), 또는 증류(1-4스텝)를 씁니다. 레슨 12를 보세요.

## 사용해 보기

| 역할 | 2026년 전형적 스택 |
|------|-----------------------|
| 이미지 픽셀 공간 확산(작은 규모, 장난감) | DDPM + U-Net |
| 이미지 잠재 확산 | VAE 인코더 + U-Net 또는 DiT (레슨 07) |
| 비디오 잠재 확산 | 시공간 DiT (Sora, Veo, WAN) |
| 오디오 잠재 확산 | Encodec + 확산 트랜스포머 |
| 과학(분자, 단백질, 물리) | 등변 확산(EDM, RFdiffusion, AlphaFold3) |

확산은 만능 생성 백본입니다. 플로우 매칭(레슨 13)은 같은 품질에서 추론 속도로 보통 이기는 2024~2026년의 경쟁자입니다.

## 출시하기

`outputs/skill-diffusion-trainer.md`로 저장하세요. 이 스킬은 데이터셋 + 계산 예산을 받아 스케줄(선형/코사인/시그모이드), 예측 타깃(ε/v/x), 스텝 수, 가이던스 스케일, 샘플러 계열, 평가 프로토콜을 출력합니다.

## 연습 문제

1. **쉬움.** `code/main.py`에서 T를 40에서 10으로 바꿔 보세요. 샘플 품질(출력 히스토그램을 눈으로 확인)이 어떻게 나빠지나요? 몇 T에서 두 모드 구조가 무너지나요?
2. **보통.** ε-예측을 v-예측으로 바꿔 보세요. 역방향 단계를 다시 유도하고, 최종 샘플 품질을 비교합니다.
3. **어려움.** classifier-free guidance를 추가해 보세요. 클래스 레이블 `c ∈ {0, 1}`로 조건화하고, 학습 중 10%는 레이블을 버리고, 샘플링 때는 `ε = (1+w)·ε_cond - w·ε_uncond`를 씁니다. `w = 0, 1, 3, 7`에서 조건 모드 적중률을 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 순방향 과정 | "잡음 섞기" | 데이터를 망가뜨리는 고정된 마르코프 연쇄 `q(x_t \| x_{t-1})`. |
| 역방향 과정 | "잡음 제거" | 데이터를 재구성하는 학습된 연쇄 `p_θ(x_{t-1} \| x_t)`. |
| β 스케줄 | "잡음 사다리" | 단계별 분산; 선형, 코사인, 또는 시그모이드. |
| α̅ | "알파 바" | 누적 곱 `∏(1 - β)`; `x_0`에서 닫힌 형태의 `x_t`를 줍니다. |
| 단순 손실 | "잡음에 대한 MSE" | `\|\|ε - ε_θ(x_t, t)\|\|²`; 모든 변분 유도가 여기로 수렴합니다. |
| ε-예측 | "잡음 예측" | 출력은 더해진 잡음; 표준 DDPM. |
| V-예측 | "속도 예측" | 출력은 `α·ε - σ·x`; 모든 t에서 더 나은 조건화. |
| DDPM | "그 논문" | Ho 외 2020; 선형 β, 1000스텝, U-Net. |
| DDIM | "결정론적 샘플러" | 비마르코프 샘플러, 20-50스텝, 학습 목표는 동일. |
| Classifier-free guidance | "CFG" | 조건부와 무조건부 잡음 예측을 섞어 조건화를 증폭합니다. |

## 프로덕션 노트: 확산 추론은 스텝 수의 문제

DDPM 논문은 역방향 스텝 T=1000을 돌립니다. 프로덕션에서 저렇게 출시하는 곳은 없습니다. 모든 실전 추론 스택은 세 전략 중 하나를 고릅니다 — 그리고 각각은 "지연 시간이 어디서 오는가"라는 프로덕션 관점에 깔끔하게 대응합니다:

1. **더 빠른 샘플러, 같은 모델.** DDIM(20-50스텝), DPM-Solver++(10-20), UniPC(8-16). 역방향 루프를 통째로 갈아끼우는 것; 학습된 `ε_θ` 가중치는 그대로입니다. 지연 시간을 20~50배 줄입니다.
2. **증류.** 적은 스텝으로 교사를 따라 하도록 학생을 학습시킵니다: Progressive Distillation(2 → 1), Consistency Models(임의 → 1-4), LCM, SDXL-Turbo, SD3-Turbo. 지연 시간을 추가로 5~10배 줄이지만 재학습이 필요합니다.
3. **캐싱과 컴파일.** `torch.compile(unet, mode="reduce-overhead")`, TensorRT-LLM의 확산 백엔드, `xformers`/SDPA 어텐션, bf16 가중치. 스텝당 지연 시간을 약 2배 줄입니다. (1)과 (2)와 함께 쌓을 수 있습니다.

프로덕션 확산 서버의 예산 논의는 LLM에 대해 프로덕션 문헌이 말하는 것과 같습니다: 지연 시간은 `num_steps × step_cost + VAE_decode`, 처리량은 `batch_size × (num_steps × step_cost)^-1`입니다. TTFT는 작고(스텝 한 번) TPOT에 해당하는 것은 전체 응답 시간입니다. 사용자 눈에는 이미지 생성이 "한꺼번에 끝나는" 일이기 때문입니다.

## 더 읽을거리

- [Sohl-Dickstein 외 (2015). Deep Unsupervised Learning using Nonequilibrium Thermodynamics](https://arxiv.org/abs/1503.03585) — 확산의 원조 논문, 시대를 앞서갔습니다.
- [Ho, Jain, Abbeel (2020). Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) — DDPM.
- [Song, Meng, Ermon (2021). Denoising Diffusion Implicit Models](https://arxiv.org/abs/2010.02502) — DDIM, 더 적은 스텝.
- [Nichol & Dhariwal (2021). Improved DDPM](https://arxiv.org/abs/2102.09672) — 코사인 스케줄, 학습된 분산.
- [Dhariwal & Nichol (2021). Diffusion Models Beat GANs on Image Synthesis](https://arxiv.org/abs/2105.05233) — classifier guidance.
- [Ho & Salimans (2022). Classifier-Free Diffusion Guidance](https://arxiv.org/abs/2207.12598) — CFG.
- [Karras 외 (2022). Elucidating the Design Space of Diffusion-Based Generative Models (EDM)](https://arxiv.org/abs/2206.00364) — 통일된 표기법, 가장 깔끔한 레시피.
