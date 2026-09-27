---
name: skill-noise-schedule-designer
description: T와 목표 훼손 수준이 주어지면 선형/코사인/시그모이드 베타 스케줄을 만들고 SNR 그래프까지 제공
version: 1.0.0
phase: 4
lesson: 10
tags: [computer-vision, diffusion, noise-schedule, training]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-noise-schedule-designer.md](skill-noise-schedule-designer.md)

# 노이즈 스케줄 설계기

베타 스케줄은 각 디퓨전 단계에서 신호를 얼마나 남길지 결정합니다. 나쁜 스케줄은 학습 효율과 샘플 품질을 그 이후의 모든 결정에서 제한해 버립니다.

## 언제 사용하나

- 새 디퓨전 학습을 시작하며 T와 베타를 고를 때
- 흐릿한 샘플을 내는 디퓨전 모델(스케줄이 너무 공격적)이나 구조를 학습하지 못하는 모델(스케줄이 너무 온건한)을 디버깅할 때
- 서로 다른 스케줄을 보고하는 논문들의 설계를 비교할 때

## 입력

- `T`: 타임스텝 수, 보통 100-1000.
- `type`: linear | cosine | sigmoid.
- `target_alpha_bar_final`: t=T에서 남길 신호의 비율, 기본값 0.001(99.9% 훼손).
- 선택 `image_resolution` — 큰 이미지일수록 천천히 훼손되는 스케줄(코사인 또는 시프트 스케줄)이 유리합니다.

## 스케줄 공식

### Linear
```
beta_t = beta_start + (beta_end - beta_start) * (t - 1) / (T - 1)
```
기본값: beta_start=1e-4, beta_end=0.02 (DDPM 논문).

### Cosine (Nichol & Dhariwal, 2021)
```
alpha_bar_t = cos^2((t/T + s) / (1 + s) * pi/2)
beta_t = 1 - alpha_bar_t / alpha_bar_{t-1}
```
s = 0.008. 신호를 더 오래 유지하며, 단계 수가 적을 때 유리합니다.

### Sigmoid
```
alpha_bar_t = 1 / (1 + exp(k * (t/T - 0.5)))
```
k = 6에서 12. 좋은 중간 지점이며 일부 SDXL 변형이 사용합니다.

## 단계

1. 공식대로 베타를 계산합니다.
2. `alphas`, `alphas_cumprod`, `sqrt_alphas_cumprod`, `sqrt_one_minus_alphas_cumprod`를 미리 계산합니다.
3. SNR_t = alpha_bar_t / (1 - alpha_bar_t)를 계산하고, 시간에 따른 SNR 요약을 만듭니다.
4. `alphas_cumprod[T-1]`이 `target_alpha_bar_final`의 10% 오차 안인지 확인합니다. 아니면 beta_end(선형), s(코사인), k(시그모이드)를 조정하고 다시 시도합니다.
5. 세 개의 체크포인트를 보고합니다:
   - `t=T*0.25` — 초기 훼손
   - `t=T*0.5` — 중간
   - `t=T*0.75` — 거의 마지막

## 보고

```
[schedule]
  type:   <name>
  T:      <int>
  beta_start: <float>   beta_end: <float>

[signal retention]
  t=0.25T:  alpha_bar=<X>  SNR=<X>
  t=0.5T:   alpha_bar=<X>  SNR=<X>
  t=0.75T:  alpha_bar=<X>  SNR=<X>
  t=T:      alpha_bar=<X>  SNR=<X>

[warnings]
  - <if alpha_bar collapses before 0.75T>
  - <if beta_end produces NaN in log-SNR>
```

## 규칙

- `alpha_bar_t <= 0`인 스케줄은 절대 만들지 않습니다. 1e-5 미만 값은 잘라내고(clamp) 경고합니다.
- 단계 수가 적은 샘플링(30단계 미만)에는 코사인이 기본 권장입니다.
- `quality_target == research`에는 선형이 기본입니다. DDPM 베이스라인은 선형 스케줄로 보고됩니다.
- `image_resolution > 256`이면 고해상도에서 신호를 더 남기도록 스케줄을 시프트하는 방법(Chen, 2023)을 권하세요.
