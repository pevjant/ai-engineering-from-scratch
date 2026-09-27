> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 정책 경사(Policy Gradient) — 스크래치로 만드는 REINFORCE

> 가치를 추정하는 것을 멈추세요. 정책을 직접 파라미터화하고, 기대 반환값의 기울기를 계산하고, 언덕 위로 한 걸음 오르면 됩니다. Williams(1992)가 정리 하나로 써 놓았습니다. PPO, GRPO, 그리고 모든 LLM RL 루프가 존재하는 이유이기도 하고요.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 3 · 03(역전파), 페이즈 9 · 03(몬테카를로), 페이즈 9 · 04(TD 학습)
**시간:** 약 75분

## 문제 상황

Q-learning과 DQN은 *가치* 함수를 파라미터화합니다. 행동은 `argmax Q`로 고르죠. 이산 행동과 이산 상태에서는 문제없습니다. 하지만 행동이 연속이면(10차원 토크에 대해 `argmax`를 어떻게 하죠?) 또는 확률적 정책을 원하면(`argmax`는 구조상 결정론적입니다) 무너집니다.

정책 경사는 대신 *정책*을 파라미터화합니다. `π_θ(a | s)`는 행동 분포를 출력하는 신경망입니다. 여기서 샘플링해서 행동합니다. 기대 반환값의 `θ`에 대한 기울기를 계산합니다. 언덕 위로 오릅니다. `argmax`도 없고, 벨만 재귀도 없습니다. 그냥 `J(θ) = E_{π_θ}[G]` 위의 경사 상승입니다.

REINFORCE 정리(Williams 1992)는 이 기울기가 계산 가능하다는 것을 알려 줍니다: `∇J(θ) = E_π[ G · ∇_θ log π_θ(a | s) ]`. 에피소드를 하나 돌립니다. 반환값을 계산합니다. 매 스텝 `∇ log π_θ(a | s)`를 곱합니다. 평균을 냅니다. 경사 상승. 끝.

2026년의 모든 LLM-RL 알고리즘 — PPO, DPO, GRPO — 은 REINFORCE의 개량판입니다. 이것을 손에 익히는 것이 이 페이즈의 나머지와, 페이즈 10 · 07(RLHF 구현), 페이즈 10 · 08(DPO)의 선수 지식입니다.

## 핵심 개념

![정책 경사: 소프트맥스 정책, log-π 기울기, 반환값 가중 갱신](../assets/policy-gradient.svg)

**정책 경사 정리.** `θ`로 파라미터화된 임의의 정책 `π_θ`에 대해:

`∇J(θ) = E_{τ ~ π_θ}[ Σ_{t=0}^{T} G_t · ∇_θ log π_θ(a_t | s_t) ]`

여기서 `G_t = Σ_{k=t}^{T} γ^{k-t} r_{k+1}`은 스텝 `t`부터의 할인 반환값입니다. 기댓값은 `π_θ`에서 샘플링한 전체 궤적 `τ`에 대해 취합니다.

**증명은 짧습니다.** 기댓값 아래에서 `J(θ) = Σ_τ P(τ; θ) G(τ)`를 미분합니다. `∇P(τ; θ) = P(τ; θ) ∇ log P(τ; θ)`(로그 미분 트릭)를 씁니다. `log P(τ; θ) = Σ log π_θ(a_t | s_t) + θ에 의존하지 않는 환경 항들`로 분해합니다. 환경 항은 사라집니다. 대수 두 줄로 정리가 나옵니다.

**분산 감소 트릭.** 바닐라 REINFORCE는 분산이 살인적입니다 — 반환값도 시끄럽고, `∇ log π`도 시끄럽고, 그 곱은 훨씬 더 시끄럽습니다. 표준 해법 두 가지:

1. **베이스라인 차감.** `G_t`를 `G_t - b(s_t)`로 바꿉니다. 단, `b(s_t)`는 `a_t`에 의존하지 않는 임의의 베이스라인. 편향이 없습니다. `E[b(s_t) · ∇ log π(a_t | s_t)] = 0`이기 때문입니다. 전형적인 선택: 크리틱(critic)이 학습한 `b(s_t) = V̂(s_t)` → 액터-크리틱(레슨 07).
2. **보상-to-go(reward-to-go).** `Σ_t G_t · ∇ log π_θ(a_t | s_t)`를 `Σ_t G_t^{from t} · ∇ log π_θ(a_t | s_t)`로 바꿉니다. 주어진 행동에 중요한 것은 미래의 반환값뿐입니다 — 과거 보상은 평균이 0인 노이즈일 뿐입니다.

둘을 합치면:

`∇J ≈ (1/N) Σ_{i=1}^{N} Σ_{t=0}^{T_i} [ G_t^{(i)} - V̂(s_t^{(i)}) ] · ∇_θ log π_θ(a_t^{(i)} | s_t^{(i)})`

이것이 베이스라인을 얹은 REINFORCE — A2C(레슨 07)와 PPO(레슨 08)의 직계 조상입니다.

**소프트맥스 정책 파라미터화.** 이산 행동에서의 표준 선택:

`π_θ(a | s) = exp(f_θ(s, a)) / Σ_{a'} exp(f_θ(s, a'))`

여기서 `f_θ`는 행동별 점수를 출력하는 임의의 신경망입니다. 기울기는 깔끔한 형태를 가집니다:

`∇_θ log π_θ(a | s) = ∇_θ f_θ(s, a) - Σ_{a'} π_θ(a' | s) ∇_θ f_θ(s, a')`

즉, 취한 행동의 점수에서 그것의 정책 아래 기댓값을 뺀 것입니다.

**연속 행동을 위한 가우시안 정책.** `π_θ(a | s) = N(μ_θ(s), σ_θ(s))`. `∇ log N(a; μ, σ)`는 닫힌 형태를 가집니다. 페이즈 9 · 07의 SAC에 필요한 것이 전부입니다.

```figure
policy-gradient-landscape
```

## 직접 만들기

### 단계 1: 소프트맥스 정책 네트워크

```python
def policy_logits(theta, state_features):
    return [dot(theta[a], state_features) for a in range(N_ACTIONS)]

def softmax(logits):
    m = max(logits)
    exps = [exp(l - m) for l in logits]
    Z = sum(exps)
    return [e / Z for e in exps]
```

표(tabular) 환경에서는 선형 정책(행동마다 가중치 벡터 하나)을 쓰세요. Atari라면 CNN으로 갈아끼우고 소프트맥스 헤드는 그대로 두면 됩니다.

### 단계 2: 샘플링과 로그 확률

```python
def sample_action(probs, rng):
    x = rng.random()
    cum = 0
    for a, p in enumerate(probs):
        cum += p
        if x <= cum:
            return a
    return len(probs) - 1

def log_prob(probs, a):
    return log(probs[a] + 1e-12)
```

### 단계 3: 로그 확률을 기록하는 롤아웃

```python
def rollout(theta, env, rng, gamma):
    trajectory = []
    s = env.reset()
    while not done:
        logits = policy_logits(theta, s)
        probs = softmax(logits)
        a = sample_action(probs, rng)
        s_next, r, done = env.step(s, a)
        trajectory.append((s, a, r, probs))
        s = s_next
    return trajectory
```

### 단계 4: REINFORCE 갱신

```python
def reinforce_step(theta, trajectory, gamma, lr, baseline=0.0):
    returns = compute_returns(trajectory, gamma)
    for (s, a, _, probs), G in zip(trajectory, returns):
        advantage = G - baseline
        grad_log_pi_a = [-p for p in probs]
        grad_log_pi_a[a] += 1.0
        for i in range(N_ACTIONS):
            for j in range(len(s)):
                theta[i][j] += lr * advantage * grad_log_pi_a[i] * s[j]
```

기울기 `∇ log π(a|s) = e_a - π(·|s)`(`a`의 원핫에서 확률을 뺀 것)가 소프트맥스 정책 경사의 심장입니다. 몸에 새겨 두세요.

### 단계 5: 베이스라인

최근 에피소드들에 걸친 `G`의 이동 평균만으로도 4×4 GridWorld를 돌리기에 충분한 분산 감소가 됩니다. 수렴까지 약 500 에피소드죠. 베이스라인을 학습된 `V̂(s)`로 업그레이드하면 액터-크리틱이 됩니다.

## 흔한 함정

- **기울기 폭발.** 반환값은 아주 클 수 있습니다. `∇ log π`를 곱하기 전에 배치 전체에서 `G`를 `~N(0, 1)`로 반드시 정규화하세요.
- **엔트로피 붕괴.** 정책이 너무 일찍 거의 결정론적인 행동으로 수렴하고, 탐색을 멈추고, 갇힙니다. 해법: 목적 함수에 엔트로피 보너스 `β · H(π(·|s))`를 더하세요.
- **높은 분산.** 바닐라 REINFORCE는 수천 에피소드가 필요합니다. 크리틱 베이스라인(레슨 07)이나 TRPO/PPO의 신뢰 영역(레슨 08)이 표준 해법입니다.
- **샘플 비효율.** 온폴리시라는 것은 갱신 한 번마다 모든 전이를 버린다는 뜻입니다. 중요도 샘플링을 통한 오프폴리시 보정은 데이터를 되살려 주지만, 분산이 그 대가입니다(PPO의 비율은 클리핑된 IS 가중치입니다).
- **비정상 기울기.** 100 에피소드 전의 같은 기울기는 옛 `π`에서 나온 것입니다. 그래서 온폴리시 방법은 몇 번의 롤아웃마다 갱신합니다.
- **신용 할당(credit assignment).** reward-to-go가 없으면 과거 보상이 노이즈로 기여합니다. 항상 reward-to-go를 쓰세요.

## 실전 활용

2026년에 REINFORCE를 직접 돌리는 일은 드물지만, 그 기울기 공식은 어디에나 있습니다:

| 사용 사례 | 파생 방법 |
|----------|---------------|
| 연속 제어 | 가우시안 정책을 쓰는 PPO / SAC |
| LLM RLHF | KL 벌점을 붙인 PPO, 토큰 단위 정책 위에서 동작 |
| LLM 추론(DeepSeek) | GRPO — 그룹 상대 베이스라인을 쓴 REINFORCE, 크리틱 없음 |
| 멀티 에이전트 | 중앙화 크리틱 REINFORCE (MADDPG, COMA) |
| 이산 행동 로봇공학 | A2C, A3C, PPO |
| 선호 데이터만 있을 때 | DPO — REINFORCE를 선호 가능도 손실로 재작성, 샘플링 없음 |

2026년 학습 스크립트에서 `loss = -advantage * log_prob`를 본다면, 그것은 베이스라인을 얹은 REINFORCE입니다. 논문 전체(DPO, GRPO, RLOO)가 이 한 줄 위에 얹은 분산 감소 트릭입니다.

## 출시하기

`outputs/skill-policy-gradient-trainer.md`로 저장하세요:

```markdown
---
name: policy-gradient-trainer
description: 주어진 태스크에 대한 REINFORCE / 액터-크리틱 / PPO 학습 설정을 만들고 분산 문제를 진단합니다.
version: 1.0.0
phase: 9
lesson: 6
tags: [rl, policy-gradient, reinforce]
---

환경(이산 / 연속 행동, 시야, 보상 통계)이 주어지면 다음을 출력합니다:

1. 정책 헤드. 소프트맥스(이산) 또는 가우시안(연속), 파라미터 수 포함.
2. 베이스라인. 없음(바닐라), 이동 평균, 학습된 `V̂(s)`, 또는 A2C 크리틱.
3. 분산 제어. 기본 켜진 reward-to-go, 반환값 정규화, 기울기 클리핑 값.
4. 엔트로피 보너스. 계수 β와 감쇠 스케줄.
5. 배치 크기. 갱신당 에피소드 수; 온폴리시 데이터 신선도 계약.

시야가 500스텝을 넘는 태스크에서 베이스라인 없는 REINFORCE는 거부하세요. 소프트맥스 헤드로 연속 행동 제어를 하는 것은 거부하세요. `β = 0`이고 관측된 정책 엔트로피가 0.1 미만인 실행은 엔트로피 붕괴로 표시하세요.
```

## 연습 문제

1. **쉬움.** 4×4 GridWorld에 선형 소프트맥스 정책으로 REINFORCE를 구현하세요. 베이스라인 없이 1,000 에피소드를 학습하세요. 학습 곡선을 그래프로 그리고, 분산(반환값의 표준편차)을 측정하세요.
2. **보통.** 이동 평균 베이스라인을 추가하고 다시 학습하세요. 바닐라 실행과 샘플 효율과 분산을 비교하세요. 베이스라인이 수렴까지 걸리는 스텝을 얼마나 줄여 주나요?
3. **어려움.** 엔트로피 보너스 `β · H(π)`를 추가하세요. `β ∈ {0, 0.01, 0.1, 1.0}`을 훑어 보세요. 최종 반환값과 정책 엔트로피를 그래프로 그리세요. 이 태스크에서 스윗스팟은 어디인가요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 정책 경사 | "정책을 직접 학습" | `∇J(θ) = E[G · ∇ log π_θ(a\|s)]`; 로그 미분 트릭에서 유도. |
| REINFORCE | "원조 PG 알고리즘" | Williams (1992); 몬테카를로 반환값에 로그 정책 기울기를 곱함. |
| 로그 미분 트릭 | "점수 함수 추정량" | `∇P(τ;θ) = P(τ;θ) · ∇ log P(τ;θ)`; 기댓값의 기울기를 다룰 수 있게 만듦. |
| 베이스라인 | "분산 감소" | `G`에서 빼는 임의의 `b(s)`; `E[b · ∇ log π] = 0`이라 편향 없음. |
| Reward-to-go | "미래 반환값만 센다" | 전체 `G_0` 대신 `G_t^{from t}`; 올바르고 분산도 낮음. |
| 엔트로피 보너스 | "탐색 장려" | `+β · H(π(·\|s))` 항이 정책이 붕괴하는 것을 막음. |
| On-policy | "방금 본 것으로 학습" | 기울기 기댓값이 현재 정책 기준 — 옛 데이터를 직접 재사용할 수 없음. |
| 어드밴티지 | "평균보다 얼마나 나은가" | `A(s, a) = G(s, a) - V(s)`; 베이스라인 REINFORCE가 곱하는 부호 있는 양. |

## 더 읽기

- [Williams (1992). Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning](https://link.springer.com/article/10.1007/BF00992696) — 원조 REINFORCE 논문.
- [Sutton et al. (2000). Policy Gradient Methods for Reinforcement Learning with Function Approximation](https://papers.nips.cc/paper_files/paper/1999/hash/464d828b85b0bed98e80ade0a5c43b0f-Abstract.html) — 함수 근사를 포함한 현대적 정책 경사 정리.
- [Sutton & Barto (2018). Ch. 13 — Policy Gradient Methods](http://incompleteideas.net/book/RLbook2020.pdf) — 교과서 전개.
- [OpenAI Spinning Up — VPG / REINFORCE](https://spinningup.openai.com/en/latest/algorithms/vpg.html) — PyTorch 코드와 함께하는 명쾌한 해설.
- [Peters & Schaal (2008). Reinforcement Learning of Motor Skills with Policy Gradients](https://homes.cs.washington.edu/~todorov/courses/amath579/reading/PolicyGradient.pdf) — 분산 감소와, REINFORCE를 신뢰 영역 계열(TRPO, PPO)과 잇는 자연 기울기 관점.
