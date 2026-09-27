> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 시간차 학습 — Q-Learning & SARSA

> 몬테카를로는 에피소드가 끝나기를 기다립니다. 시간차(TD) 학습은 매 스텝마다 다음 가치 추정치를 부트스트랩해서 갱신합니다. Q-learning은 오프폴리시이고 낙관적입니다. SARSA는 온폴리시이고 신중합니다. 둘 다 코드 한 줄입니다. 둘 다 이 페이즈의 모든 딥 RL 방법을 떠받치는 기둥입니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 9 · 01(MDP), 페이즈 9 · 02(동적 계획법), 페이즈 9 · 03(몬테카를로)
**시간:** 약 75분

## 문제 상황

몬테카를로는 동작하지만 비싼 요구 조건이 두 개 있습니다. 끝나는 에피소드가 필요하고, 최종 반환값이 들어온 후에야 갱신합니다. 에피소드가 1,000스텝이면 MC는 뭘 하나 갱신하려고 1,000스텝을 기다립니다. 분산이 크고, 편향은 적지만, 실전에서는 느립니다.

동적 계획법은 정반대 성질입니다 — 분산 0의 부트스트랩 백업 — 하지만 알려진 모델이 필요합니다.

시간차(TD, temporal difference) 학습은 그 사이를 쪼갭니다. 단 하나의 전이 `(s, a, r, s')`에서 한 스텝 타깃 `r + γ V(s')`를 만들고 `V(s)`를 그쪽으로 살짝 끌어당깁니다. 모델도 없고, 완결된 에피소드도 필요 없습니다. 우변의 근사 `V`를 쓰기 때문에 편향은 생기지만, MC보다 분산은 극적으로 낮고 첫 스텝부터 온라인 갱신이 됩니다.

이것이 현대 RL 전체 — DQN, A2C, PPO, SAC — 가 도는 축입니다. 페이즈 9의 나머지는 이 레슨에서 쓸 한 스텝 TD 갱신 위에 함수 근사와 트릭을 여러 겹 쌓은 것입니다.

## 핵심 개념

![Q-learning vs SARSA: 오프폴리시 max vs 온폴리시 Q(s', a')](../assets/td.svg)

**V를 위한 TD(0) 갱신:**

`V(s) ← V(s) + α [r + γ V(s') - V(s)]`

괄호 안의 양이 TD 오차 `δ = r + γ V(s') - V(s)`입니다. MC의 `G_t - V(s_t)`에 해당하는 온라인 버전입니다. 수렴하려면 `α`가 Robbins-Monro 조건(`Σ α = ∞`, `Σ α² < ∞`)을 만족하고 모든 상태가 무한 번 방문되어야 합니다.

**Q-learning.** 제어를 위한 오프폴리시 TD 방법:

`Q(s, a) ← Q(s, a) + α [r + γ max_{a'} Q(s', a') - Q(s, a)]`

이 `max`는 에이전트가 실제로 무슨 행동을 하든, `s'` 이후로는 *탐욕* 정책이 따라질 것이라고 가정합니다. 이 분리 덕분에 Q-learning은 에이전트가 ε-greedy로 탐색하는 동안에도 `Q*`를 학습합니다. Mnih et al. (2015)가 이것을 Atari 위의 딥 Q-learning으로 바꿨습니다(레슨 05).

**SARSA.** 온폴리시 TD 방법:

`Q(s, a) ← Q(s, a) + α [r + γ Q(s', a') - Q(s, a)]`

이름이 바로 튜플 `(s, a, r, s', a')`입니다. SARSA는 탐욕 `argmax`가 아니라 에이전트가 *실제로* 다음에 취하는 행동 `a'`를 씁니다. 돌아가고 있는 ε-greedy `π`가 무엇이든 그에 대한 `Q^π`로 수렴하고, 극한 `ε → 0`에서 `Q*`가 됩니다.

**절벽 걷기의 차이.** 고전적인 절벽 걷기(cliff-walking) 태스크(절벽에서 떨어짐 = 보상 -100)에서, Q-learning은 절벽 가장자리를 따르는 최적 경로를 학습하지만 탐색 중에 종종 벌점을 받습니다. SARSA는 절벽에서 한 칸 떨어진 더 안전한 경로를 학습합니다. 탐색 노이즈를 Q-값에 반영하기 때문입니다. 학습이 충분하면 `ε → 0`에서 둘 다 최적에 도달합니다. 하지만 실전에서는 의미가 있습니다: 배포 시점에 실제로 탐색이 일어나고 있다면 SARSA의 행동이 더 보수적입니다.

**기대(expected) SARSA.** `Q(s', a')`를 `π` 아래에서의 기댓값으로 바꿉니다:

`Q(s, a) ← Q(s, a) + α [r + γ Σ_{a'} π(a'|s') Q(s', a') - Q(s, a)]`

SARSA보다 분산이 낮고(`a'` 샘플이 필요 없음), 같은 온폴리시 타깃입니다. 현대 교과서에서는 흔히 이것이 기본값입니다.

**n-스텝 TD와 TD(λ).** 부트스트랩 전에 `n`스텝을 기다리면 TD(0)와 MC 사이를 보간할 수 있습니다. `n=1`은 TD, `n=∞`는 MC입니다. TD(λ)는 모든 `n`을 기하 가중치 `(1-λ)λ^{n-1}`로 평균 냅니다. 딥 RL은 대개 `n`을 3~20 사이로 씁니다.

```figure
qlearning-gridworld
```

## 직접 만들기

### 단계 1: ε-greedy 정책 위의 SARSA

```python
def sarsa(env, episodes, alpha=0.1, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})

    def choose(s):
        if random() < epsilon:
            return choice(ACTIONS)
        return max(Q[s], key=Q[s].get)

    for _ in range(episodes):
        s = env.reset()
        a = choose(s)
        while True:
            s_next, r, done = env.step(s, a)
            a_next = choose(s_next) if not done else None
            target = r + (gamma * Q[s_next][a_next] if not done else 0.0)
            Q[s][a] += alpha * (target - Q[s][a])
            if done:
                break
            s, a = s_next, a_next
    return Q
```

여덟 줄. Q-learning과의 *유일한* 차이는 타깃 줄입니다.

### 단계 2: Q-learning

```python
def q_learning(env, episodes, alpha=0.1, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})
    for _ in range(episodes):
        s = env.reset()
        while True:
            a = choose(s, Q, epsilon)
            s_next, r, done = env.step(s, a)
            target = r + (gamma * max(Q[s_next].values()) if not done else 0.0)
            Q[s][a] += alpha * (target - Q[s][a])
            if done:
                break
            s = s_next
    return Q
```

이 `max`가 타깃을 행동으로부터 분리합니다. 이 기호 하나가 on-policy와 off-policy의 차이입니다.

### 단계 3: 학습 곡선

100 에피소드당 평균 반환값을 추적하세요. 단순한 결정론적 GridWorld에서는 Q-learning이 더 빨리 수렴하고, 절벽 걷기에서는 SARSA가 더 보수적입니다. `code/main.py`의 4×4 GridWorld에서는 `α=0.1, ε=0.1`로 둘 다 약 2,000 에피소드 후에 거의 최적이 됩니다.

### 단계 4: DP 진리와 비교

가치 반복(레슨 02)을 돌려 `Q*`를 얻습니다. `max_{s,a} |Q_learned(s,a) - Q*(s,a)|`를 확인하세요. 건강한 표(tabular) TD 에이전트는 10,000 에피소드 후 4×4 GridWorld에서 `~0.5` 이내에 들어옵니다.

## 흔한 함정

- **초기 Q 값이 중요합니다.** 낙관적 초기화(보상이 음수인 태스크에서 `Q = 0`)는 탐색을 부추깁니다. 비관적 초기화는 탐욕 정책을 영원히 갇힌 상태로 만들 수 있습니다.
- **α 스케줄.** 고정 `α`는 비정상(non-stationary) 문제에서 괜찮습니다. 감쇠 `α_n = 1/n`은 이론상 수렴이지만 실전에서는 너무 느립니다 — `α`를 `[0.05, 0.3]`에 고정하고 학습 곡선을 감시하세요.
- **ε 스케줄.** 높게 시작해서(`ε=1.0`) `ε=0.05`로 감쇠하세요. "GLIE"(무한 탐색 하의 극한 탐욕)가 수렴 조건입니다.
- **Q-learning의 최대값 편향.** `Q`가 시끄러울 때 `max` 연산자는 위로 편향됩니다. 과대추정으로 이어집니다 — Hasselt의 Double Q-learning(레슨 05의 DDQN이 사용)이 Q 테이블 두 개로 이것을 고칩니다.
- **끝나지 않는 에피소드.** TD는 종료 상태 없이도 배울 수 있지만, 스텝을 제한하거나 제한 지점에서 부트스트랩을 올바르게 처리해야 합니다. 표준 방식: 제한을 비종료로 취급하고 부트스트랩을 계속합니다.
- **상태 해싱.** 상태가 튜플/텐서라면 해시 가능한 키를 쓰세요(리스트가 아니라 튜플; 원시 float가 아니라 반올림한 float 튜플).

## 실전 활용

2026년의 TD 지형:

| 태스크 | 방법 | 이유 |
|------|--------|--------|
| 작은 표(tabular) 환경 | Q-learning | 최적 정책을 직접 학습. |
| 온폴리시 안전 필수 | SARSA / 기대 SARSA | 탐색 중에 보수적. |
| 고차원 상태 | DQN (페이즈 9 · 05) | 리플레이와 타깃 네트워크를 갖춘 신경망 Q 함수. |
| 연속 행동 | SAC / TD3 (페이즈 9 · 07) | Q-네트워크 위의 TD 갱신; 정책 네트워크가 행동을 출력. |
| LLM RL(보상 모델 기반) | PPO / GRPO (페이즈 9 · 08, 12) | GAE를 통한 TD 스타일 어드밴티지의 액터-크리틱. |
| 오프라인 RL | CQL / IQL (페이즈 9 · 08) | 보수적 정규화를 얹은 Q-learning. |

2026년 논문에서 읽게 되는 "RL"의 90퍼센트는 Q-learning이나 SARSA의 어떤 변형입니다. 더 깊이 읽기 전에 이 표 갱신을 손에 익히세요.

## 출시하기

`outputs/skill-td-agent.md`로 저장하세요:

```markdown
---
name: td-agent
description: 표(tabular) 또는 소규모 특성(feature) RL 태스크에서 Q-learning, SARSA, 기대 SARSA 중 하나를 고릅니다.
version: 1.0.0
phase: 9
lesson: 4
tags: [rl, td-learning, q-learning, sarsa]
---

표 또는 소규모 특성 환경이 주어지면 다음을 출력합니다:

1. 알고리즘. Q-learning / SARSA / 기대 SARSA / n-스텝 변형. on-policy vs off-policy와 분산에 근거한 한 문장 이유.
2. 하이퍼파라미터. α, γ, ε, 감쇠 스케줄.
3. 초기화. Q_0 값(낙관적 vs 0)과 근거.
4. 수렴 진단. 목표 학습 곡선, DP가 가능하면 `|Q - Q*|` 검사.
5. 배포 시 주의점. 추론 시 탐색은 어떻게 동작하는가? SARSA의 보수성이 필요한가?

상태 공간이 10⁶를 넘는 표 TD 적용은 거부하세요. 최대값 편향(max-bias) 주의점 없이 Q-learning 에이전트를 출시하는 것은 거부하세요. ε를 처음부터 끝까지 1.0으로 고정한 채 학습한 에이전트(활용 단계가 없음)는 표시하세요.
```

## 연습 문제

1. **쉬움.** 4×4 GridWorld에서 Q-learning과 SARSA를 구현하세요. 2,000 에피소드의 학습 곡선(100 에피소드당 평균 반환값)을 그래프로 그리세요. 누가 더 빨리 수렴하나요?
2. **보통.** 절벽 걷기 환경을 만드세요(4×12, 마지막 행이 절벽, 보상 -100과 시작 지점 리셋). Q-learning과 SARSA의 최종 정책을 비교하세요. 각각이 지나가는 경로를 그려 보세요. 어느 쪽이 절벽에 더 가까운가요?
3. **어려움.** Double Q-learning을 구현하세요. 시끄러운 보상의 GridWorld(스텝당 보상에 가우시안 노이즈 σ=5 추가)에서, Q-learning은 `V*(0,0)`을 유의미하게 과대추정하는 반면 Double Q-learning은 그렇지 않음을 보이세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| TD 오차 | "갱신 신호" | `δ = r + γ V(s') - V(s)`, 부트스트랩된 잔차. |
| TD(0) | "한 스텝 TD" | 다음 상태의 추정치만 써서 전이마다 갱신. |
| Q-learning | "오프폴리시 RL 101" | 다음 상태 행동에 `max`를 붙인 TD 갱신; 행동 정책과 무관하게 `Q*`를 학습. |
| SARSA | "온폴리시 Q-learning" | 실제 다음 행동을 쓰는 TD 갱신; 현재 ε-greedy π의 `Q^π`를 학습. |
| 기대 SARSA | "저분산 SARSA" | 샘플링한 `a'`을 π 아래 기댓값으로 교체. |
| GLIE | "올바른 탐색 스케줄" | 무한 탐색 하의 극한 탐욕; Q-learning 수렴에 필요. |
| 부트스트래핑 | "타깃에 현재 추정치를 쓰는 것" | TD를 MC와 구분하는 것. 편향의 원인이지만 분산을 대폭 줄여 줌. |
| 최대화 편향 | "Q-learning은 과대추정한다" | 시끄러운 추정치에 `max`를 씌우면 위로 편향됨; Double Q-learning으로 해결. |

## 더 읽기

- [Watkins & Dayan (1992). Q-learning](https://link.springer.com/article/10.1007/BF00992698) — 원조 논문과 수렴 증명.
- [Sutton & Barto (2018). Ch. 6 — Temporal-Difference Learning](http://incompleteideas.net/book/RLbook2020.pdf) — TD(0), SARSA, Q-learning, 기대 SARSA.
- [Hasselt (2010). Double Q-learning](https://papers.nips.cc/paper_files/paper/2010/hash/091d584fced301b442654dd8c23b3fc9-Abstract.html) — 최대화 편향의 해법.
- [Seijen, Hasselt, Whiteson, Wiering (2009). A Theoretical and Empirical Analysis of Expected SARSA](https://ieeexplore.ieee.org/document/4927542) — 기대 SARSA의 동기.
- [Rummery & Niranjan (1994). On-line Q-learning using connectionist systems](https://www.researchgate.net/publication/2500611_On-Line_Q-Learning_Using_Connectionist_Systems) — SARSA라는 이름을 처음 만든 논문(당시에는 "modified connectionist Q-learning").
- [Sutton & Barto (2018). Ch. 7 — n-step Bootstrapping](http://incompleteideas.net/book/RLbook2020.pdf) — TD(0)를 TD(n)로 일반화; Q-learning에서 적격성 추적(eligibility traces)으로, 나중에는 PPO의 GAE로 이어지는 길.
