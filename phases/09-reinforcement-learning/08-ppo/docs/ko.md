> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 근접 정책 최적화(PPO)

> A2C는 각 롤아웃을 갱신 한 번에 버립니다. PPO는 정책 경사를 클리핑된 중요도 비율로 감싸서, 같은 데이터로 10회 이상의 에포크를 돌려도 정책이 폭주하지 않게 합니다. Schulman et al. (2017). 2026년에도 여전히 기본 정책 경사 알고리즘입니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 9 · 06(REINFORCE), 페이즈 9 · 07(액터-크리틱)
**시간:** 약 75분

## 문제 상황

A2C(레슨 07)는 온폴리시입니다: 기울기 `E_{π_θ}[A · ∇ log π_θ]`는 *현재* `π_θ`에서 샘플링한 데이터를 요구합니다. 갱신을 한 번 하면 `π_θ`가 바뀌고, 쓰던 데이터는 이제 오프폴리시가 됩니다. 재사용하면 기울기가 편향됩니다.

롤아웃은 비쌉니다. Atari에서 롤아웃 하나는 8개 환경 × 128스텝 = 전이 1024개이고, 환경 시간으로는 십수 초입니다. 기울기 스텝 한 번에 버리는 건 낭비입니다.

신뢰 영역 정책 최적화(TRPO, Schulman 2015)가 첫 해법이었습니다: 옛 정책과 새 정책 사이의 KL 발산이 `δ` 아래로 유지되도록 각 갱신을 제한합니다. 이론상 깔끔하지만 갱신마다 켤레 기울기(conjugate-gradient) 풀이가 필요합니다. 2026년에 TRPO를 돌리는 사람은 없습니다.

PPO(Schulman et al. 2017)는 하드 신뢰 영역 제약을 간단한 클리핑 목적 함수로 바꿨습니다. 코드 한 줄 추가. 롤아웃당 에포크 열 번. 켤레 기울기 없음. 충분한 이론적 보장. 9년이 지나도 MuJoCo부터 RLHF까지 모든 분야의 기본 정책 경사 알고리즘입니다.

## 핵심 개념

![PPO 클리핑 서러게이트 목적 함수: 1 ± ε에서 비율 클리핑](../assets/ppo.svg)

**중요도 비율.**

`r_t(θ) = π_θ(a_t | s_t) / π_{θ_old}(a_t | s_t)`

새 정책과 데이터를 수집한 정책의 가능도 비율입니다. `r_t = 1`은 변화 없음. `r_t = 2`는 새 정책이 옛 정책보다 `a_t`를 취할 확률이 두 배라는 뜻입니다.

**클리핑 서러게이트.**

`L^{CLIP}(θ) = E_t [ min( r_t(θ) A_t, clip(r_t(θ), 1-ε, 1+ε) A_t ) ]`

두 항으로 동작합니다:

- 어드밴티지 `A_t > 0`인데 비율이 `1 + ε`을 넘으려 하면, 클리핑이 기울기를 평평하게 만듭니다 — 좋은 행동을 옛 확률보다 `+ε` 이상 밀지 마세요.
- 어드밴티지 `A_t < 0`인데 비율이 `1 - ε`을 넘으려 하면(즉, 클리핑된 감소분 대비 나쁜 행동을 더 자주 취하게 만들려 하면), 클리핑이 기울기에 한계를 둡니다 — 나쁜 행동을 `-ε` 아래로 누르지 마세요.

`min`은 반대 방향을 처리합니다: 비율이 *이득이 되는* 방향으로 움직였다면 여전히 기울기를 받습니다(당신을 해치는 쪽에서는 클리핑하지 않습니다).

전형적인 값은 `ε = 0.2`입니다. 목적 함수를 `r_t`의 함수로 그려 보세요: "좋은 쪽"에는 평평한 지붕이, "나쁜 쪽"에는 평평한 바닥이 있는 조각별 선형 함수입니다.

**PPO 전체 손실.**

`L(θ, φ) = L^{CLIP}(θ) - c_v · (V_φ(s_t) - V_t^{target})² + c_e · H(π_θ(·|s_t))`

A2C와 같은 액터-크리틱 구조입니다. 계수 셋, 보통 `c_v = 0.5`, `c_e = 0.01`, `ε = 0.2`입니다.

**학습 루프.**

1. `N`개 병렬 환경에서 각각 `T`스텝, 전이 `N × T`개를 수집합니다.
2. 어드밴티지(GAE)를 계산하고 상수로 얼립니다.
3. 현재 `π_θ`의 스냅숏으로 `π_{θ_old}`를 얼립니다.
4. `K` 에포크 동안, 미니배치 `(s, a, A, V_target, log π_old(a|s))`마다:
   - `r_t(θ) = exp(log π_θ(a|s) - log π_old(a|s))`를 계산합니다.
   - `L^{CLIP}` + 가치 손실 + 엔트로피를 적용합니다.
   - 기울기 스텝을 밟습니다.
5. 롤아웃을 버립니다. 1단계로 돌아갑니다.

`K = 10`과 64짜리 미니배치가 표준 하이퍼파라미터 세트입니다. PPO는 튼튼합니다: 정확한 수치는 ±50% 안에서는 거의 중요하지 않습니다.

**KL 벌점 변형.** 원조 논문은 적응적 KL 벌점을 쓰는 대안을 제안했습니다: `L = L^{PG} - β · KL(π_θ || π_old)`, 관측된 KL에 따라 `β`를 조정합니다. 클리핑 버전이 지배적이 되었고, KL 변형은 RLHF에서 살아남았습니다(참조 정책에 대한 KL은 어차피 항상 원하는 별도의 제약이니까요).

```figure
ppo-clip
```

## 직접 만들기

### 단계 1: 롤아웃 시점에 `log π_old(a | s)` 기록하기

```python
for step in range(T):
    probs = softmax(logits(theta, state_features(s)))
    a = sample(probs, rng)
    s_next, r, done = env.step(s, a)
    buffer.append({
        "s": s, "a": a, "r": r, "done": done,
        "v_old": value(w, state_features(s)),
        "log_pi_old": log(probs[a] + 1e-12),
    })
    s = s_next
```

스냅숏은 롤아웃 시점에 딱 한 번 찍습니다. 갱신 에포크 동안 바뀌지 않습니다.

### 단계 2: GAE 어드밴티지 계산(레슨 07)

A2C와 같습니다. 배치 전체에서 정규화하세요.

### 단계 3: 클리핑 서러게이트 갱신

```python
for _ in range(K_EPOCHS):
    for mb in minibatches(buffer, size=64):
        for rec in mb:
            x = state_features(rec["s"])
            probs = softmax(logits(theta, x))
            logp = log(probs[rec["a"]] + 1e-12)
            ratio = exp(logp - rec["log_pi_old"])
            adv = rec["advantage"]
            surrogate = min(
                ratio * adv,
                clamp(ratio, 1 - EPS, 1 + EPS) * adv,
            )
            # -surrogate를 역전파하고, 가치 손실을 더하고, 엔트로피를 뺀다
            grad_logpi = onehot(rec["a"]) - probs
            if (adv > 0 and ratio >= 1 + EPS) or (adv < 0 and ratio <= 1 - EPS):
                pg_grad = 0.0  # 클리핑됨
            else:
                pg_grad = ratio * adv
            for i in range(N_ACTIONS):
                for j in range(N_FEAT):
                    theta[i][j] += LR * pg_grad * grad_logpi[i] * x[j]
```

"클리핑되면 → 기울기 0" 패턴이 PPO의 심장입니다. 새 정책이 이미 이득 방향으로 너무 멀리 흘렀다면 갱신이 멈춥니다.

### 단계 4: 가치와 엔트로피

A2C와 마찬가지로 크리틱 타깃에 표준 MSE를, 액터에 엔트로피 보너스를 더하세요.

### 단계 5: 진단

매 갱신마다 볼 세 가지:

- **평균 KL** `E[log π_old - log π_θ]`. `[0, 0.02]` 안에 있어야 합니다. `0.1`을 넘어 폭주하면 `K_EPOCHS`나 `LR`을 줄이세요.
- **클리핑 비율** — 비율이 `[1-ε, 1+ε]` 밖에 있는 샘플의 비율. `~0.1-0.3`이어야 합니다. `~0`이면 클리핑이 한 번도 안 걸리는 것이니 → `LR`이나 `K_EPOCHS`를 올리세요. `~0.5+`이면 롤아웃을 과적합하는 것이니 → 내리세요.
- **설명 분산** `1 - Var(V_target - V_pred) / Var(V_target)`. 크리틱 품질 지표입니다. 크리틱이 배울수록 1로 올라가야 합니다.

## 흔한 함정

- **클리핑 계수 잘못 조정.** `ε = 0.2`가 사실상 표준입니다. `0.1`로 내리면 갱신이 너무 소심해지고, `0.3+`는 불안정을 부릅니다.
- **에포크 과다.** `K > 20`은 정책이 `π_old`에서 멀리 흘러 흔히 불안정해집니다. 에포크에 상한을 두세요, 특히 큰 네트워크에서.
- **보상 정규화 부재.** 큰 보상 스케일은 클리핑 범위를 잠식합니다. 어드밴티지를 계산하기 전에 보상을 정규화하세요(이동 표준편차).
- **어드밴티지 정규화를 잊음.** 배치별 평균 0/표준편차 1 정규화가 표준입니다. 빼먹으면 대부분의 벤치마크에서 PPO가 망가집니다.
- **학습률 감쇠 부재.** PPO는 학습률을 0까지 선형 감쇠하면 이득을 봅니다. 고정 학습률은 보통 더 나쁩니다.
- **중요도 비율 수식 오류.** 수치 안정성을 위해 항상 `exp(log_new - log_old)`로 쓰세요. `new / old`가 아니라.
- **기울기 부호 반대.** 서러게이트를 *최대화* = `-L^{CLIP}`을 *최소화*. 부호가 뒤집힌 것이 가장 흔한 PPO 버그입니다.

## 실전 활용

PPO는 2026년에 놀라울 만큼 많은 도메인의 기본 RL 알고리즘입니다:

| 사용 사례 | PPO 변형 |
|----------|-------------|
| MuJoCo / 로봇 제어 | 가우시안 정책, GAE(0.95)를 쓰는 PPO |
| Atari / 이산 게임 | 범주형 정책, 128스텝 구르는 롤아웃을 쓰는 PPO |
| LLM RLHF | 참조 모델에 KL 벌점, 응답 끝에서 RM 보상을 받는 PPO |
| 대규모 게임 에이전트 | IMPALA + PPO (AlphaStar, OpenAI Five) |
| 추론 LLM | GRPO(레슨 12) — 크리틱 없는 PPO 변형 |
| 선호 데이터만 있을 때 | DPO — PPO+KL의 닫힌 형태 압축, 온라인 샘플링 없음 |

PPO의 *손실 형태* — 클리핑 서러게이트 + 가치 + 엔트로피 — 가 DPO, GRPO, 그리고 거의 모든 RLHF 파이프라인의 비계입니다.

## 출시하기

`outputs/skill-ppo-trainer.md`로 저장하세요:

```markdown
---
name: ppo-trainer
description: 주어진 환경에 대한 PPO 학습 설정과 진단 계획을 만듭니다.
version: 1.0.0
phase: 9
lesson: 8
tags: [rl, ppo, policy-gradient]
---

환경과 학습 예산이 주어지면 다음을 출력합니다:

1. 롤아웃 크기. `N` 환경 × `T` 스텝.
2. 갱신 일정. `K` 에포크, 미니배치 크기, 학습률 스케줄.
3. 서러게이트 파라미터. `ε`(클리핑), `c_v`, `c_e`, 어드밴티지 정규화 켜짐.
4. 어드밴티지. 명시적인 `γ`와 `λ`를 갖춘 GAE(`λ`).
5. 진단 계획. KL, 클리핑 비율, 설명 분산 임계값과 알림.

`K > 30` 또는 `ε > 0.3`(위험한 신뢰 영역)은 거부하세요. 어드밴티지 정규화나 KL/클리핑 모니터링 없는 PPO 실행은 거부하세요. 클리핑 비율이 0.4 위에서 지속되면 드리프트로 표시하세요.
```

## 연습 문제

1. **쉬움.** `ε=0.2, K=4`로 4×4 GridWorld에서 PPO를 돌리세요. 같은 환경 스텝 수에서 롤아웃당 에포크 한 번인 A2C와 샘플 효율을 비교하세요.
2. **보통.** `K ∈ {1, 4, 10, 30}`을 훑어 보세요. 환경 스텝 대비 반환값을 그래프로 그리고 갱신당 평균 KL을 추적하세요. 이 태스크에서 KL이 폭발하는 `K`는 얼마인가요?
3. **어려움.** 클리핑 서러게이트를 적응적 KL 벌점으로 바꾸세요(`KL > 2·target`이면 `β` 두 배, `KL < target/2`면 절반). 최종 반환값, 안정성, 클리핑 없음의 정도를 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 중요도 비율 | "r_t(θ)" | `π_θ(a\|s) / π_old(a\|s)`; 데이터를 수집한 정책에서 벗어난 정도. |
| 클리핑 서러게이트 | "PPO의 핵심 트릭" | `min(r·A, clip(r, 1-ε, 1+ε)·A)`; 이득 쪽에서는 클리핑 너머로 기울기가 평평함. |
| 신뢰 영역 | "TRPO / PPO의 의도" | 각 갱신의 KL을 제한해 단조 개선을 보장. |
| KL 벌점 | "소프트 신뢰 영역" | PPO의 대안: `L - β · KL(π_θ \|\| π_old)`. 적응적 `β`. |
| 클리핑 비율 | "클리핑이 걸리는 빈도" | 진단 지표 — 0.1-0.3이 정상; 벗어나면 조정이 잘못된 것. |
| 다에포크 학습 | "데이터 재사용" | 각 롤아웃에서 K 에포크; 샘플 효율을 얻는 대가로 분산 비용을 치름. |
| 준온폴리시 | "거의 온폴리시" | PPO는 명목상 온폴리시지만 K>1 에포크는 약간 오프폴리시인 데이터를 안전하게 씀. |
| PPO-KL | "다른 PPO" | KL 벌점 변형; 참조 정책에 대한 KL이 이미 제약인 RLHF에서 사용. |

## 더 읽기

- [Schulman et al. (2017). Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347) — 그 논문.
- [Schulman et al. (2015). Trust Region Policy Optimization](https://arxiv.org/abs/1502.05477) — TRPO, PPO의 전신.
- [Andrychowicz et al. (2021). What Matters In On-Policy RL? A Large-Scale Empirical Study](https://arxiv.org/abs/2006.05990) — PPO 하이퍼파라미터 전부를 소거 실험.
- [Ouyang et al. (2022). Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — InstructGPT; RLHF 속의 PPO 레시피.
- [OpenAI Spinning Up — PPO](https://spinningup.openai.com/en/latest/algorithms/ppo.html) — PyTorch와 함께하는 깔끔한 현대적 해설.
- [CleanRL PPO implementation](https://github.com/vwxyzjn/cleanrl) — 많은 논문이 쓰는 단일 파일 레퍼런스 PPO.
- [Hugging Face TRL — PPOTrainer](https://huggingface.co/docs/trl/main/en/ppo_trainer) — 언어 모델 위의 PPO 프로덕션(운영 환경) 레시피; 레슨 09(RLHF)와 나란히 읽으세요.
- [Engstrom et al. (2020). Implementation Matters in Deep Policy Gradients](https://arxiv.org/abs/2005.12729) — "37가지 코드 수준 최적화" 논문; 어떤 PPO 트릭이 진짜 하중을 받고 어떤 것이 속설인지.
