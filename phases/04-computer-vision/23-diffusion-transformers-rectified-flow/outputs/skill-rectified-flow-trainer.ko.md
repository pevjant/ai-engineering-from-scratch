> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-rectified-flow-trainer.md](skill-rectified-flow-trainer.md)

---
name: skill-rectified-flow-trainer
description: AdaLN DiT와 Euler 샘플링으로 정류 흐름 학습 루프 전체를 작성합니다
version: 1.0.0
phase: 4
lesson: 23
tags: [diffusion, rectified-flow, DiT, training]
---

# Rectified Flow Trainer

어떤 이미지 텐서 데이터셋이든 정류 흐름으로 작은 DiT를 성공적으로 학습시킬 수 있는 깔끔하고 최소한의 학습 루프를 만들어냅니다.

## 언제 사용하나

- SD3 / FLUX 학습 목적함수를 작은 규모로 재현할 때.
- 같은 데이터에서 정류 흐름 vs DDPM 벤치마킹.
- 비표준 도메인(의료, 위성)용 커스텀 정류 흐름 모델 구축.

## 입력

- `model`: `(x, t)`를 받아 예측 속도를 반환하는 `nn.Module`.
- `dataset`: 모델 도메인의 깨끗한 이미지 이터러블.
- `optimizer`: `lr=1e-4`, `weight_decay=0.01`, `betas=(0.9, 0.99)`인 AdamW.
- `scheduler`: 워밍업이 있는 코사인, 기본 1000 워밍업 스텝.

## 학습 스텝

```python
def rectified_flow_train_step(model, x0, optimizer, device):
    model.train()
    x0 = x0.to(device)
    n = x0.size(0)
    t = torch.rand(n, device=device)                     # [0, 1] 균등
    epsilon = torch.randn_like(x0)
    x_t = (1 - t[:, None, None, None]) * x0 + t[:, None, None, None] * epsilon
    target_v = epsilon - x0                              # 속도 타깃
    pred_v = model(x_t, t)
    loss = F.mse_loss(pred_v, target_v)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()
```

## 샘플링 (Euler)

```python
@torch.no_grad()
def sample(model, shape, steps=20, device="cpu"):
    model.eval()
    x = torch.randn(shape, device=device)
    dt = 1.0 / steps
    t = torch.ones(shape[0], device=device)
    for _ in range(steps):
        v = model(x, t)
        x = x - dt * v
        t = t - dt
    return x
```

## 팁

- `torch.rand` 균등 `t`를 쓰세요. logit-normal이나 SD3 스타일 가중 `t` 샘플링이 약간 도움이 되지만, 시작하는 데 필수는 아닙니다.
- 모델 가중치의 EMA는 표준 관행입니다. decay 0.9999로 `ema_model`을 유지하세요.
- 조건부 모델의 classifier-free guidance: 학습 중 10% 확률로 조건을 빈/널 임베딩으로 바꾸고, 추론 때 `v_uncond + w * (v_cond - v_uncond)`를 `w` 약 3-5로 섞습니다.
- LDM 스타일 학습(FLUX, SD3)에서는 루프 전체가 VAE 잠재 공간에서 돕니다. 위의 깨끗한 `x0`는 실제로는 `VAE.encode(image)`입니다.
- 32x32 장난감 데이터셋의 전형적 수렴: 2000-5000 스텝. 실제 잠재 SD3 학습: 수십만 스텝.

## 보고서

```
[rectified flow training]
  steps:        <int>
  final loss:   <float>
  ema decay:    <float>
  vae?:         yes | no
  cfg dropout:  <비율>

[sampling]
  default steps: 20
  schnell / turbo target: 4
  full quality reference: 50+ (비교용)
```

## 규칙

- RGB `uint8` 데이터에 이미지 공간 속도 타깃으로 정류 흐름을 학습하지 마세요. 먼저 평균 0, 단위 분산으로 정규화하세요.
- 항상 시간 스텝 구간별 학습 손실을 로그하세요. 초기 시간 스텝(0 근처)의 손실이 후기(1 근처)보다 높으면 속도 파라미터화가 잘못 연결되었을 가능성이 높습니다.
- 같은 학습 루프에서 정류 흐름 속도 타깃과 DDPM 노이즈 타깃을 섞지 마세요. 하나를 고르세요.
- Ampere+ GPU에서는 bfloat16 학습을 쓰세요. float16은 속도 크기 때문에 정류 흐름에서 가끔 NaN 그래디언트를 냅니다.
