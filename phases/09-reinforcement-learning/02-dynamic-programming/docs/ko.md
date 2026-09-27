> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 동적 계획법 — 정책 반복과 가치 반복

> 동적 계획법(DP)은 컨닝하는 강화 학습입니다. 전이 함수와 보상 함수를 이미 알고 있으니, `V`나 `π`가 멈출 때까지 벨만 방정식을 반복만 하면 됩니다. 샘플링 기반 방법들이 모두 다가가려 하는 벤치마크이기도 합니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 9 · 01(MDP)
**시간:** 약 75분

## 문제 상황

모델을 아는 MDP가 주어졌습니다: 어떤 상태-행동 쌍에 대해서든 `P(s' | s, a)`와 `R(s, a, s')`를 물어볼 수 있습니다. 재고 관리자는 수요 분포를 알고요. 보드 게임은 전이가 결정론적입니다. GridWorld는 파이썬 네 줄이면 됩니다. 즉 *모델*이 있는 것입니다.

모델 프리(model-free) RL(Q-learning, PPO, REINFORCE)은 모델이 없을 때 — 환경에서 샘플만 뽑을 수 있을 때 — 를 위해 발명되었습니다. 하지만 모델이 있을 때는 더 빠르고 더 좋은 방법이 있습니다: 동적 계획법입니다. Bellman이 1957년에 설계했습니다. 지금까지도 "정답"의 기준을 정의합니다. 사람들이 "이 MDP의 최적 정책"이라고 말할 때, 그 의미는 DP가 돌려줄 정책입니다.

2026년에도 이 방법들이 필요한 이유는 세 가지입니다. 첫째, RL 연구의 모든 표(tabular) 환경(GridWorld, FrozenLake, CliffWalking)은 DP로 풀어 골드 스탠다드 정책을 만듭니다. 둘째, 정확한 가치를 알면 샘플링 기반 방법을 *디버그*할 수 있습니다: Q-learning의 `V*(s_0)` 추정치가 DP 답과 30% 어긋난다면 Q-learning에 버그가 있는 것입니다. 셋째, 현대의 오프라인 RL과 계획(planning) 방법(MCTS, AlphaZero의 탐색, 페이즈 9 · 10의 모델 기반 RL)은 모두 학습하거나 주어진 모델 위에서 벨만 백업을 반복합니다.

## 핵심 개념

![정책 반복과 가치 반복, 나란히](../assets/dp.svg)

**두 알고리즘, 둘 다 벨만 위의 고정점 반복입니다.**

**정책 반복(policy iteration).** 정책이 바뀌지 않을 때까지 두 단계를 번갈아 수행합니다.

1. *평가:* 정책 `π`가 주어지면, `V(s) ← Σ_a π(a|s) Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`를 수렴할 때까지 반복 적용해 `V^π`를 계산합니다.
2. *개선:* `V^π`가 주어지면, `π`를 `V^π`에 대해 탐욕적으로 만듭니다: `π(s) ← argmax_a Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`.

수렴이 보장됩니다. (a) 각 개선 단계는 `π`를 그대로 두거나 어떤 상태에 대해 `V^π`를 엄격히 증가시키고, (b) 결정론적 정책의 공간은 유한하기 때문입니다. 보통 큰 상태 공간에서도 외부 반복 약 5~20번 만에 수렴합니다.

**가치 반복(value iteration).** 평가와 개선을 한 번의 스윕으로 합칩니다. 벨만 *최적성* 방정식을 적용합니다:

`V(s) ← max_a Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`

`max_s |V_{new}(s) - V(s)| < ε`가 될 때까지 반복합니다. 마지막에 탐욕 행동을 골라 정책을 뽑아 냅니다. 반복당은 확실히 더 빠릅니다 — 안쪽 평가 루프가 없으니까요 — 하지만 보통 수렴에는 더 많은 반복이 필요합니다.

**일반화된 정책 반복(GPI, Generalized Policy Iteration).** 이 모든 것을 묶는 틀입니다. 가치 함수와 정책은 서로를 끌어올리는 루프에 묶여 있고, 둘을 상호 일관성으로 이끄는 모든 방법(비동기 가치 반복, 수정 정책 반복, Q-learning, 액터-크리틱, PPO)은 GPI의 한 사례입니다.

**`γ < 1`이 중요한 이유.** 벨만 연산자는 상한 노름(sup-norm)에서 `γ`-수축 사상입니다: `||T V - T V'||_∞ ≤ γ ||V - V'||_∞`. 수축 사상은 유일한 고정점과 기하급수적 수렴을 보장합니다. `γ < 1`을 버리면 이 보장도 사라집니다 — 유한 시야나 흡수 종료 상태가 필요합니다.

```figure
value-iteration-gamma
```

## 직접 만들기

### 단계 1: GridWorld MDP 모델 만들기

레슨 01의 4×4 GridWorld를 그대로 씁니다. 확률적 변형을 하나 추가합니다: 확률 `0.1`로 에이전트가 무작위 직교 방향으로 미끄러집니다.

```python
SLIP = 0.1

def transitions(state, action):
    if state == TERMINAL:
        return [(state, 0.0, 1.0)]
    outcomes = []
    for direction, prob in action_probs(action):
        outcomes.append((apply_move(state, direction), -1.0, prob))
    return outcomes
```

`transitions(s, a)`는 `(s', r, p)` 목록을 돌려줍니다. 이것이 모델의 전부입니다.

### 단계 2: 정책 평가

정책 `π(s) = {action: prob}`가 주어지면, `V`가 멈출 때까지 벨만 방정식을 반복합니다:

```python
def policy_evaluation(policy, gamma=0.99, tol=1e-6):
    V = {s: 0.0 for s in states()}
    while True:
        delta = 0.0
        for s in states():
            v = sum(pi_a * sum(p * (r + gamma * V[s_prime])
                              for s_prime, r, p in transitions(s, a))
                   for a, pi_a in policy(s).items())
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            return V
```

### 단계 3: 정책 개선

`π`를 `V`에 대해 탐욕적인 정책으로 바꿉니다. `π`가 바뀌지 않았다면 끝 — 최적점에 도달한 것입니다.

```python
def policy_improvement(V, gamma=0.99):
    new_policy = {}
    for s in states():
        best_a = max(
            ACTIONS,
            key=lambda a: sum(p * (r + gamma * V[s_prime])
                              for s_prime, r, p in transitions(s, a)),
        )
        new_policy[s] = best_a
    return new_policy
```

### 단계 4: 둘을 합치기

```python
def policy_iteration(gamma=0.99):
    policy = {s: "up" for s in states()}   # arbitrary start
    for _ in range(100):
        V = policy_evaluation(lambda s: {policy[s]: 1.0}, gamma)
        new_policy = policy_improvement(V, gamma)
        if new_policy == policy:
            return V, policy
        policy = new_policy
```

4×4에서의 전형적인 수렴: 외부 반복 4~6번. `V*(0,0) ≈ -6`과 스텝 수를 확실히 줄이는 정책이 출력됩니다.

### 단계 5: 가치 반복(루프 하나 버전)

```python
def value_iteration(gamma=0.99, tol=1e-6):
    V = {s: 0.0 for s in states()}
    while True:
        delta = 0.0
        for s in states():
            v = max(sum(p * (r + gamma * V[s_prime])
                       for s_prime, r, p in transitions(s, a))
                   for a in ACTIONS)
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            break
    policy = policy_improvement(V, gamma)
    return V, policy
```

같은 고정점, 더 적은 코드 줄 수.

## 흔한 함정

- **종료 상태 처리를 잊음.** 흡수 상태에 벨만을 적용하면, 아무것도 바꾸지 않는 "최선의 행동"을 여전히 고릅니다. `if s == terminal: V[s] = 0` 가드를 두세요.
- **상한 노름 vs L2 수렴.** 평균이 아니라 `max |V_new - V|`를 쓰세요. 이론적 보장은 상한 노름 기준입니다.
- **제자리 갱신 vs 동기 갱신.** `V[s]`를 제자리에서 갱신하면(Gauss-Seidel) 별도의 `V_new` 딕셔너리를 쓰는 것(Jacobi)보다 빨리 수렴합니다. 프로덕션(운영 환경) 코드는 제자리 갱신을 씁니다.
- **정책 동점.** 두 행동의 Q-값이 같으면 `argmax`가 반복마다 동점 처리를 다르게 해서 "정책 안정" 검사가 진동할 수 있습니다. 안정적인 동점 처리(고정 순서에서 첫 번째 행동)를 쓰세요.
- **상태 공간 폭발.** DP는 스윕당 `O(|S| · |A|)`입니다. 대략 10⁷ 상태까지는 동작합니다. 그 이상은 함수 근사가 필요합니다(페이즈 9 · 05부터).

## 실전 활용

2026년에 DP는 정답의 베이스라인이자 계획기(planner)의 안쪽 루프입니다:

| 사용 사례 | 방법 |
|----------|--------|
| 작은 표 MDP를 정확히 풀기 | 가치 반복(더 단순) 또는 정책 반복(외부 스텝이 더 적음) |
| Q-learning / PPO 구현 검증 | 토이 환경에서 DP-최적 V*와 비교 |
| 모델 기반 RL(페이즈 9 · 10) | 학습된 전이 모델 위의 벨만 백업 |
| AlphaZero / MuZero의 계획 | 몬테카를로 트리 탐색 = 비동기 벨만 백업 |
| 오프라인 RL(CQL, IQL) | 보수적 Q 반복 — OOD 행동에 벌점을 붙인 DP |

누군가 "최적 가치 함수"라고 말할 때마다, 그 의미는 "DP의 고정점"입니다. 논문에서 `V*`나 `Q*`를 보면 이 루프를 떠올리세요.

## 출시하기

`outputs/skill-dp-solver.md`로 저장하세요:

```markdown
---
name: dp-solver
description: 작은 표(tabular) MDP를 정책 반복 또는 가치 반복으로 정확히 풉니다. 수렴 동작을 보고합니다.
version: 1.0.0
phase: 9
lesson: 2
tags: [rl, dynamic-programming, bellman]
---

모델을 아는 MDP가 주어지면 다음을 출력합니다:

1. 선택. 정책 반복 vs 가치 반복. |S|, |A|, γ에 근거한 이유.
2. 초기화. V_0, 시작 정책. 수렴 민감도.
3. 정지 조건. 상한 노름 허용 오차 ε. 예상 스윕 수.
4. 검증. 정확히 계산한 V*(s_0). 추출된 탐욕 정책.
5. 활용. 이 베이스라인이 샘플링 기반 방법의 디버그/평가에 어떻게 쓰일지.

상태 공간이 10⁷를 넘는 DP 실행은 거부하세요. 상한 노름 검사 없이 수렴을 주장하는 것은 거부하세요. 무한 시야 태스크에서 γ ≥ 1이면 보장 위반으로 표시하세요.
```

## 연습 문제

1. **쉬움.** 4×4 GridWorld에서 `γ ∈ {0.9, 0.99}`로 가치 반복을 실행하세요. `max |ΔV| < 1e-6`까지 스윕이 몇 번 필요한가요? `V*`를 4×4 그리드로 출력하세요.
2. **보통.** *확률적* GridWorld(미끄러짐 확률 `0.1`)에서 정책 반복과 가치 반복을 비교하세요. 스윕 수, 실제 걸린 시간, 최종 `V*(0,0)`을 세어 보세요. 반복 횟수로는 어느 쪽이 빠른가요? 실제 시간으로는요?
3. **어려움.** 수정 정책 반복을 만들어 보세요: 평가 단계에서 수렴까지가 아니라 `k`번의 스윕만 실행합니다. `k ∈ {1, 2, 5, 10, 50}`에 대해 `V*(0,0)` 오차를 `k`에 대해 그래프로 그리세요. 이 곡선이 평가/개선 트레이드오프에 대해 말해 주는 것은 무엇인가요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 정책 반복 | "DP 알고리즘" | 평가(`V^π`)와 개선(`V^π`에 대한 탐욕 `π`)을 정책이 멈출 때까지 번갈아 수행. |
| 가치 반복 | "더 빠른 DP" | 벨만 최적성 백업을 한 스윕에 적용; `V*`로 기하급수적으로 수렴. |
| 벨만 연산자 | "그 재귀식" | `(T V)(s) = max_a Σ P (r + γ V(s'))`; 상한 노름에서 `γ`-수축 사상. |
| 수축 사상 | "DP가 수렴하는 이유" | `\|\|T x - T y\|\| ≤ γ \|\|x - y\|\|`를 만족하는 연산자 `T`는 유일한 고정점을 가짐. |
| GPI | "전부 DP다" | 일반화된 정책 반복: `V`와 `π`를 상호 일관성으로 이끄는 모든 방법. |
| 동기 갱신 | "Jacobi 방식" | 스윕 내내 옛 `V`를 사용; 깔끔하게 분석 가능하지만 느림. |
| 제자리 갱신 | "Gauss-Seidel 방식" | 갱신되는 `V`를 즉시 사용; 실제로 더 빨리 수렴. |

## 더 읽기

- [Sutton & Barto (2018). Ch. 4 — Dynamic Programming](http://incompleteideas.net/book/RLbook2020.pdf) — 정책 반복과 가치 반복의 표준적 전개.
- [Bertsekas (2019). Reinforcement Learning and Optimal Control](http://www.athenasc.com/rlbook.html) — 수축 사상 논증의 엄밀한 다룸.
- [Puterman (2005). Markov Decision Processes](https://onlinelibrary.wiley.com/doi/book/10.1002/9780470316887) — 수정 정책 반복과 그 수렴 분석.
- [Howard (1960). Dynamic Programming and Markov Processes](https://mitpress.mit.edu/9780262582300/dynamic-programming-and-markov-processes/) — 정책 반복의 원조 논문.
- [Bertsekas & Tsitsiklis (1996). Neuro-Dynamic Programming](http://www.athenasc.com/ndpbook.html) — DP에서 근사 DP/딥 RL로 이어지는 다리. 이후 모든 레슨이 이용합니다.
