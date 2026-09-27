> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 몬테카를로 방법 — 완결된 에피소드로 배우기

> 동적 계획법에는 모델이 필요합니다. 몬테카를로에는 에피소드만 있으면 됩니다. 정책을 돌리고, 반환값을 보고, 평균을 냅니다. RL에서 가장 단순한 아이디어 — 그리고 이후의 모든 것을 열어 주는 아이디어입니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 9 · 01(MDP), 페이즈 9 · 02(동적 계획법)
**시간:** 약 75분

## 문제 상황

동적 계획법은 우아하지만, 모든 상태와 행동에 대해 `P(s' | s, a)`를 물어볼 수 있다고 가정합니다. 실제 세계에서 그렇게 동작하는 것은 거의 없습니다. 로봇은 관절 토크 이후 카메라 픽셀의 분포를 해석적으로 계산할 수 없습니다. 가격 책정 알고리즘은 고객의 가능한 모든 반응에 대해 적분할 수 없습니다. LLM은 토큰 이후의 가능한 모든 이어짐을 열거할 수 없습니다.

여러분에게는 환경에서 *샘플링*할 수 있는 능력만 있으면 되는 방법이 필요합니다. 정책을 돌립니다. 궤적 `s_0, a_0, r_1, s_1, a_1, r_2, …, s_T`를 얻습니다. 이것으로 가치를 추정합니다. 그것이 몬테카를로입니다.

DP에서 MC로의 전환은 철학적으로도 중요합니다: *알려진 모델 + 정확한 백업*에서 *샘플링한 롤아웃 + 평균낸 반환값*으로 옮겨 가는 것입니다. 분산은 커지지만, 적용 범위는 폭발적으로 넓어집니다. 이 레슨 이후의 모든 RL 알고리즘 — TD, Q-learning, REINFORCE, PPO, GRPO — 은 본질적으로 몬테카를로 추정량이며, 때로 부트스트래핑이 그 위에 얹혀 있습니다.

## 핵심 개념

![몬테카를로: 롤아웃, 반환값 계산, 평균; first-visit vs every-visit](../assets/monte-carlo.svg)

**한 줄로 정리한 핵심 아이디어:** `V^π(s) = E_π[G_t | s_t = s] ≈ (1/N) Σ_i G^{(i)}(s)` — 여기서 `G^{(i)}(s)`는 정책 `π` 하에서 `s`를 방문한 뒤 관측된 반환값들입니다.

**First-visit vs every-visit MC.** 한 에피소드가 상태 `s`를 여러 번 방문할 때, first-visit MC는 첫 방문의 반환값만 세고, every-visit MC는 모든 방문을 셉니다. 둘 다 극한에서는 편향이 없습니다(unbiased). First-visit이 분석이 더 단순합니다(iid 샘플). Every-visit은 에피소드당 더 많은 데이터를 쓰고 실제로는 보통 더 빨리 수렴합니다.

**증분 평균.** 모든 반환값을 저장하는 대신, 누적 평균을 갱신합니다:

`V_n(s) = V_{n-1}(s) + (1/n) [G_n - V_{n-1}(s)]`

재배열하면 `V_new = V_old + α · (target - V_old)`, 여기에 `α = 1/n`입니다. `1/n`을 고정 스텝 크기 `α ∈ (0, 1)`로 바꾸면 `π`의 변화를 따라가는 비정상(non-stationary) MC 추정량이 됩니다. 바로 이 한 수가 MC에서 TD로, 그리고 모든 현대 RL 알고리즘으로 가는 도약입니다.

**이제 탐색이 문제가 됩니다.** DP는 열거로 모든 상태를 만졌습니다. MC는 정책이 방문하는 상태만 봅니다. `π`가 결정론적이면 상태 공간의 영역 통째가 샘플링되지 않고, 그 영역의 가치 추정치는 영원히 0에 머뭅니다. 역사적 순서대로 세 가지 해법:

1. **탐색적 시작(exploring starts).** 각 에피소드를 무작위 (s, a) 쌍에서 시작합니다. 커버리지를 보장하지만, 현실에서는 비현실적입니다(로봇을 임의 상태로 "리셋"할 수는 없죠).
2. **ε-greedy.** 현재 Q에 대해 탐욕적으로 행동하되, 확률 `ε`로 무작위 행동을 고릅니다. 모든 상태-행동 쌍이 점근적으로 샘플링됩니다.
3. **오프폴리시(off-policy) MC.** 행동 정책(behavior policy) `μ` 아래에서 데이터를 모으고, 중요도 샘플링(importance sampling)으로 목표 정책 `π`에 대해 학습합니다. 분산이 크지만, DQN 같은 리플레이 버퍼 방법으로 가는 다리입니다.

**몬테카를로 제어(Control).** 평가 → 개선 → 평가, 정책 반복과 같지만 평가가 샘플링 기반입니다:

1. `π`를 돌려 에피소드를 얻습니다.
2. 관측된 반환값으로 `Q(s, a)`를 갱신합니다.
3. `Q`에 대해 `π`를 ε-greedy로 만듭니다.
4. 반복합니다.

완만한 조건(모든 쌍을 무한 번 방문, `α`가 Robbins-Monro 조건 충족)에서 확률 1로 `Q*`와 `π*`로 수렴합니다.

```figure
epsilon-greedy
```

## 직접 만들기

### 단계 1: 롤아웃 → (s, a, r) 목록

```python
def rollout(env, policy, max_steps=200):
    trajectory = []
    s = env.reset()
    for _ in range(max_steps):
        a = policy(s)
        s_next, r, done = env.step(s, a)
        trajectory.append((s, a, r))
        s = s_next
        if done:
            break
    return trajectory
```

모델 없음, 오직 `env.reset()`과 `env.step(s, a)`만. gym 환경과 같은 인터페이스지만 벗긴 내기 버전입니다.

### 단계 2: 반환값 계산(역방향 스윕)

```python
def returns_from(trajectory, gamma):
    returns = []
    G = 0.0
    for _, _, r in reversed(trajectory):
        G = r + gamma * G
        returns.append(G)
    return list(reversed(returns))
```

한 번의 패스, `O(T)`. 역방향 점화식 `G_t = r_{t+1} + γ G_{t+1}`이 다시 합산하는 것을 피해 줍니다.

### 단계 3: first-visit MC 평가

```python
def mc_policy_evaluation(env, policy, episodes, gamma=0.99):
    V = defaultdict(float)
    counts = defaultdict(int)
    for _ in range(episodes):
        trajectory = rollout(env, policy)
        returns = returns_from(trajectory, gamma)
        seen = set()
        for t, ((s, _, _), G) in enumerate(zip(trajectory, returns)):
            if s in seen:
                continue
            seen.add(s)
            counts[s] += 1
            V[s] += (G - V[s]) / counts[s]
    return V
```

핵심은 세 줄입니다: 첫 방문에서 상태를 "본 것"으로 표시하고, 카운트를 늘리고, 누적 평균을 갱신합니다.

### 단계 4: ε-greedy MC 제어(on-policy)

```python
def mc_control(env, episodes, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})
    counts = defaultdict(lambda: {a: 0 for a in ACTIONS})

    def policy(s):
        if random() < epsilon:
            return choice(ACTIONS)
        return max(Q[s], key=Q[s].get)

    for _ in range(episodes):
        trajectory = rollout(env, policy)
        returns = returns_from(trajectory, gamma)
        seen = set()
        for (s, a, _), G in zip(trajectory, returns):
            if (s, a) in seen:
                continue
            seen.add((s, a))
            counts[s][a] += 1
            Q[s][a] += (G - Q[s][a]) / counts[s][a]
    return Q, policy
```

### 단계 5: DP 골드 스탠다드와 비교

에피소드 수 → ∞이면 `V^π`의 MC 추정치는 레슨 02의 DP 결과와 일치해야 합니다. 실제로는: 4×4 GridWorld에서 50,000 에피소드면 DP 답과 `~0.1` 이내로 들어옵니다.

## 흔한 함정

- **끝나지 않는 에피소드.** MC는 에피소드가 *끝나기를* 요구합니다. 정책이 영원히 맴돌 수 있다면 `max_steps`로 제한하고, 제한에 걸리는 것을 암묵적 실패로 셉니다. 무작위 정책의 GridWorld는 흔히 타임아웃됩니다 — 정상입니다. 다만 제대로 세는 것만 확인하세요.
- **분산.** MC는 전체 반환값을 씁니다. 긴 에피소드에서는 분산이 어마어마합니다 — 맨 끝의 한 번의 불운한 보상이 `V(s_0)`을 그만큼 통째로 흔듭니다. TD 방법(레슨 04)은 부트스트래핑으로 이것을 줄입니다.
- **상태 커버리지.** 초기 Q에서 동점인 탐욕적 MC는 단 한 가지 행동만 시도합니다. 탐색이 *반드시* 필요합니다(ε-greedy, 탐색적 시작, UCB).
- **비정상 정책.** `π`가 바뀌면(MC 제어에서처럼) 오래된 반환값은 다른 정책에서 나온 것입니다. 고정 α MC는 이걸 처리하지만, 샘플 평균 MC는 못 합니다.
- **오프폴리시 중요도 샘플링.** 가중치 `π(a|s)/μ(a|s)`가 궤적을 따라 계속 곱해집니다. 시야가 길어지면 분산이 폭발합니다. per-decision weighted IS로 제한하거나 TD로 전환하세요.

## 실전 활용

2026년의 몬테카를로 방법의 역할:

| 사용 사례 | 왜 MC인가 |
|----------|--------|
| 짧은 시야 게임(블랙잭, 포커) | 에피소드가 자연히 끝난다; 반환값이 깨끗하다. |
| 기록된(logged) 정책의 오프라인 평가 | 저장된 궤적들에 대해 할인 반환값을 평균낸다. |
| 몬테카를로 트리 탐색(AlphaZero) | 트리 잎에서의 MC 롤아웃이 선택을 이끈다. |
| LLM RL 평가 | 주어진 정책에 대해 샘플링한 완성문들의 평균 보상을 계산한다. |
| PPO의 베이스라인 추정 | 어드밴티지 타깃 `A_t = G_t - V(s_t)`는 MC의 `G_t`를 쓴다. |
| RL 교육 | 실제로 동작하는 가장 단순한 알고리즘 — 부트스트래핑을 벗겨 내면 핵심이 보인다. |

현대 딥 RL 알고리즘(PPO, SAC)은 `n`-스텝 반환값이나 GAE를 통해 순수 MC(전체 반환값)와 순수 TD(한 스텝 부트스트랩) 사이를 보간합니다. 양쪽 끝 모두 같은 추정량의 사례입니다.

## 출시하기

`outputs/skill-mc-evaluator.md`로 저장하세요:

```markdown
---
name: mc-evaluator
description: 몬테카를로 롤아웃으로 정책을 평가하고, 가능하면 DP 비교가 포함된 수렴 보고서를 만듭니다.
version: 1.0.0
phase: 9
lesson: 3
tags: [rl, monte-carlo, evaluation]
---

환경(에피소딕, reset+step API)과 정책이 주어지면 다음을 출력합니다:

1. 방법. First-visit vs every-visit MC. 이유.
2. 에피소드 예산. 목표 횟수, 분산 진단, 예상 표준오차.
3. 탐색 계획. ε 스케줄(필요하면) 또는 탐색적 시작.
4. 골드 스탠다드 비교. 표(tabular) 환경이면 DP-최적 V*; 아니면 Q-learning / PPO 베이스라인의 상한.
5. 종료 검사. 최대 스텝 제한, 타임아웃, 끝나지 않는 궤적 처리.

유한 시야 제한 없이 비에피소딕 태스크에서 MC를 실행하는 것은 거부하세요. 표 환경에서 상태당 100 에피소드 미만으로 V^π 추정치를 보고하는 것은 거부하세요. 분산이 0인 행동만 있는 정책은 탐색 리스크로 표시하세요.
```

## 연습 문제

1. **쉬움.** 4×4 GridWorld에서 균등 무작위 정책의 first-visit MC 평가를 구현하세요. 10,000 에피소드를 실행하고, 에피소드 수에 따른 `V(0,0)` 변화를 DP 답과 함께 그래프로 그리세요.
2. **보통.** `ε ∈ {0.01, 0.1, 0.3}`로 ε-greedy MC 제어를 구현하세요. 20,000 에피소드 후의 평균 반환값을 비교하세요. 곡선은 어떤 모양인가요? 편향-분산 트레이드오프는 어디에 있나요?
3. **어려움.** 중요도 샘플링으로 *오프폴리시* MC를 구현하세요: 균등 무작위 정책 `μ` 아래에서 데이터를 모아 결정론적 최적 정책 `π`의 `V^π`를 추정합니다. 일반 IS vs per-decision IS vs weighted IS를 비교하세요. 어느 것이 분산이 가장 낮은가요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 몬테카를로 | "무작위 샘플링" | 분포에서 뽑은 iid 샘플을 평균 내어 기댓값을 추정. |
| 반환값 `G_t` | "미래 보상" | 스텝 `t`부터 에피소드 끝까지의 할인 보상 합: `Σ_{k≥0} γ^k r_{t+k+1}`. |
| First-visit MC | "상태마다 한 번만 센다" | 에피소드에서 첫 방문만 가치 추정에 기여. |
| Every-visit MC | "모든 방문을 쓴다" | 모든 방문이 기여; 약간의 편향이 있지만 샘플 효율이 더 좋음. |
| ε-greedy | "탐색 노이즈" | 확률 `1-ε`로 탐욕 행동, 확률 `ε`로 무작위 행동. |
| 중요도 샘플링 | "잘못된 분포에서 샘플링한 것을 바로잡기" | `μ` 데이터로 `V^π`를 추정하기 위해 반환값을 `π(a\|s)/μ(a\|s)` 곱으로 재가중. |
| On-policy | "내 데이터로 내가 배운다" | 목표 정책 = 행동 정책. 바닐라 MC, PPO, SARSA. |
| Off-policy | "남의 데이터로 배운다" | 목표 정책 ≠ 행동 정책. 중요도 샘플링 MC, Q-learning, DQN. |

## 더 읽기

- [Sutton & Barto (2018). Ch. 5 — Monte Carlo Methods](http://incompleteideas.net/book/RLbook2020.pdf) — 표준적 다룸.
- [Singh & Sutton (1996). Reinforcement Learning with Replacing Eligibility Traces](https://link.springer.com/article/10.1007/BF00114726) — first-visit vs every-visit 분석.
- [Precup, Sutton, Singh (2000). Eligibility Traces for Off-Policy Policy Evaluation](http://incompleteideas.net/papers/PSS-00.pdf) — 오프폴리시 MC와 분산 제어.
- [Mahmood et al. (2014). Weighted Importance Sampling for Off-Policy Learning](https://arxiv.org/abs/1404.6362) — 현대의 저분산 IS 추정량.
- [Tesauro (1995). TD-Gammon, A Self-Teaching Backgammon Program](https://dl.acm.org/doi/10.1145/203330.203343) — MC/TD 자가 대국이 초인적 수준에 도달함을 보인 첫 대규모 실증; 이 페이즈 후반부 모든 레슨의 개념적 선구자.
