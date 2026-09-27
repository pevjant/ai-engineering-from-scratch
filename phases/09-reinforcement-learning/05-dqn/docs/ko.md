> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 딥 Q-네트워크(DQN)

> 2013년, Mnih는 원시 픽셀 하나로 Q-learning 네트워크 하나를 학습시켜 일곱 개 Atari 게임에서 모든 고전 RL 에이전트를 이겼습니다. 2015년에는 49개 게임으로 확장되어 Nature에 실렸고, 딥 RL 시대가 열렸습니다. DQN은 Q-learning에 함수 근사를 안정시키는 트릭 세 개를 얹은 것입니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 3 · 03(역전파), 페이즈 9 · 04(Q-learning, SARSA)
**시간:** 약 75분

## 문제 상황

표(tabular) Q-learning은 (상태, 행동) 쌍마다 별도의 Q-값이 필요합니다. 체스 보드는 상태가 약 10⁴³개입니다. Atari 프레임 하나는 210×160×3 = 100,800개 특성입니다. 표 RL은 수천 개 상태에서도 버티지 못합니다. 하물며 수억 개에서는요.

해결책은 뒤돌아보면 뻔합니다: Q-테이블을 신경망 `Q(s, a; θ)`로 바꾸는 것. 하지만 그 뻔한 해결에도 수십 년이 걸렸습니다. Q-learning에 무작정 함수 근사를 얹으면 "죽음의 삼중조(deadly triad)" — 함수 근사 + 부트스트래핑 + 오프폴리시 학습 — 때문에 발산합니다. Mnih et al. (2013, 2015)가 학습을 안정시키는 세 가지 엔지니어링 트릭을 찾아 냈습니다:

1. **경험 리플레이(experience replay)**가 전이들 사이의 상관관계를 끊습니다.
2. **타깃 네트워크**가 부트스트랩 타깃을 얼립니다.
3. **보상 클리핑**이 기울기 크기를 정규화합니다.

Atari 위의 DQN은 단일 아키텍처 + 단일 하이퍼파라미터 세트로 수십 개의 제어 문제를 원시 픽셀에서 푼 첫 사례였습니다. 그 이후 만들어진 모든 "딥 RL" — DDQN, Rainbow, Dueling, Distributional, R2D2, Agent57 — 은 이 세 트릭 기반 위에 쌓인 것입니다.

## 핵심 개념

![DQN 학습 루프: 환경, 리플레이 버퍼, 온라인 네트워크, 타깃 네트워크, 벨만 TD 손실](../assets/dqn.svg)

**목적 함수.** DQN은 신경망 Q 함수 위에서 한 스텝 TD 손실을 최소화합니다:

`L(θ) = E_{(s,a,r,s')~D} [ (r + γ max_{a'} Q(s', a'; θ^-) - Q(s, a; θ))² ]`

`θ` = 온라인 네트워크, 매 스텝 경사 하강법으로 갱신됩니다. `θ^-` = 타깃 네트워크, `θ`에서 주기적으로 복사됩니다(약 10,000스텝마다). `D` = 과거 전이의 리플레이 버퍼.

**세 가지 트릭, 중요도 순:**

**경험 리플레이.** `~10⁶`개 전이를 담는 링 버퍼입니다. 각 학습 스텝은 미니배치를 균등 무작위로 샘플링합니다. 이것이 시간적 상관관계를 끊어 주고(연속된 프레임은 거의 동일합니다), 희귀한 보상 전이를 여러 번 배울 수 있게 하며, 연속된 기울기 갱신들의 상관관계를 없앱니다. 이것이 없으면 신경망을 얹은 온폴리시 TD는 Atari에서 발산합니다.

**타깃 네트워크.** 벨만 방정식 양변에 같은 네트워크 `Q(·; θ)`를 쓰면 타깃이 갱신 때마다 움직입니다 — "자기 꼬리를 쫓는" 꼴이죠. 해결책: 가중치를 얼린 두 번째 네트워크 `Q(·; θ^-)`를 유지하는 것. `C`스텝마다 `θ → θ^-`를 복사합니다. 이것이 회귀 타깃을 한 번에 수천 번의 기울기 스텝 동안 안정시켜 줍니다. 소프트 갱신 `θ^- ← τ θ + (1-τ) θ^-`(DDPG, SAC에서 사용)는 더 부드러운 변형입니다.

**보상 클리핑.** Atari 보상 크기는 1부터 1000 이상까지 들쭉날쭉합니다. `{-1, 0, +1}`로 클리핑하면 특정 게임이 기울기를 독점하는 일이 없습니다. 보상 크기 자체가 중요할 때는 틀린 방법이지만, 부호만 중요한 Atari에서는 괜찮습니다.

**Double DQN.** Hasselt (2016)가 최대화 편향을 고쳤습니다: 행동 *선택*은 온라인 네트워크가, 그 행동 *평가*는 타깃 네트워크가 합니다.

`target = r + γ Q(s', argmax_{a'} Q(s', a'; θ); θ^-)`

갈아 끼우기만 하면 되는(drop-in) 교체품이고, 꾸준히 더 좋습니다. 기본값으로 쓰세요.

**기타 개선(Rainbow, 2017):** 우선순위 리플레이(TD 오차가 큰 전이를 더 자주 샘플링), 듀얼링 아키텍처(`V(s)`와 어드밴티지 헤드를 분리), 노이즈 네트워크(학습되는 탐색), n-스텝 반환값, 분산형 Q(C51/QR-DQN), 멀티스텝 부트스트래핑. 각각 몇 퍼센트씩 더하며, 이득은 대체로 가산적입니다.

```figure
f3-dqn-stability
```

## 직접 만들기

여기 코드는 stdlib 전용, numpy 없이 동작합니다 — 작은 연속 GridWorld 위에 손으로 만든 은닉층 하나짜리 MLP를 써서 모든 학습 스텝이 마이크로초 안에 돕니다. 알고리즘은 규모를 키운 Atari DQN과 동일합니다.

### 단계 1: 리플레이 버퍼

```python
class ReplayBuffer:
    def __init__(self, capacity):
        self.buf = []
        self.capacity = capacity
    def push(self, s, a, r, s_next, done):
        if len(self.buf) == self.capacity:
            self.buf.pop(0)
        self.buf.append((s, a, r, s_next, done))
    def sample(self, batch, rng):
        return rng.sample(self.buf, batch)
```

Atari라면 용량 ~50,000; 우리 토이 환경에는 5,000이면 충분합니다.

### 단계 2: 작은 Q-네트워크(수작업 MLP)

```python
class QNet:
    def __init__(self, n_in, n_hidden, n_actions, rng):
        self.W1 = [[rng.gauss(0, 0.3) for _ in range(n_in)] for _ in range(n_hidden)]
        self.b1 = [0.0] * n_hidden
        self.W2 = [[rng.gauss(0, 0.3) for _ in range(n_hidden)] for _ in range(n_actions)]
        self.b2 = [0.0] * n_actions
    def forward(self, x):
        h = [max(0.0, sum(w * xi for w, xi in zip(row, x)) + b) for row, b in zip(self.W1, self.b1)]
        q = [sum(w * hi for w, hi in zip(row, h)) + b for row, b in zip(self.W2, self.b2)]
        return q, h
```

포워드 패스: 선형 → ReLU → 선형. 네트워크의 전부입니다.

### 단계 3: DQN 갱신

```python
def train_step(online, target, batch, gamma, lr):
    grads = zeros_like(online)
    for s, a, r, s_next, done in batch:
        q, h = online.forward(s)
        if done:
            y = r
        else:
            q_next, _ = target.forward(s_next)
            y = r + gamma * max(q_next)
        td_error = q[a] - y
        accumulate_grads(grads, online, s, h, a, td_error)
    apply_sgd(online, grads, lr / len(batch))
```

형태는 레슨 04의 Q-learning인데 차이가 두 가지입니다: (a) 테이블을 인덱싱하는 대신 미분 가능한 `Q(·; θ)`로 역전파하고, (b) 타깃에 `Q(·; θ^-)`를 씁니다.

### 단계 4: 바깥 루프

에피소드마다 `Q(·; θ)` 위에서 ε-greedy로 행동하고, 전이를 버퍼에 밀어 넣고, 미니배치를 뽑고, 기울기 스텝을 밟고, 주기적으로 `θ^- ← θ`를 동기화합니다. 패턴은 이렇습니다:

```python
for episode in range(N):
    s = env.reset()
    while not done:
        a = epsilon_greedy(online, s, epsilon)
        s_next, r, done = env.step(s, a)
        buffer.push(s, a, r, s_next, done)
        if len(buffer) >= batch:
            train_step(online, target, buffer.sample(batch), gamma, lr)
        if steps % sync_every == 0:
            target = copy(online)
        s = s_next
```

16차원 원핫(one-hot) 상태를 쓰는 이 작은 GridWorld에서 에이전트는 약 500 에피소드 만에 거의 최적인 정책을 배웁니다. Atari에서는 이것을 2억 프레임으로 늘리고 CNN 특성 추출기를 앞단에 붙이면 됩니다.

## 흔한 함정

- **죽음의 삼중조.** 함수 근사 + 오프폴리시 + 부트스트래핑은 발산할 수 있습니다. DQN은 타깃 네트워크 + 리플레이로 완화합니다. 둘 중 하나도 빼면 안 됩니다.
- **탐색.** ε는 반드시 감쇠해야 합니다. 보통 학습 초반 ~10% 동안 1.0에서 0.01로. 초기 탐색이 부족하면 Q-넷이 지역 분지에 갇힙니다.
- **과대추정.** 시끄러운 Q에 `max`를 씌우면 위로 편향됩니다. 프로덕션(운영 환경)에서는 항상 Double DQN을 쓰세요.
- **보상 스케일.** 보상을 클리핑하거나 정규화하세요. 기울기 크기는 보상 크기에 비례합니다.
- **리플레이 버퍼 콜드스타트.** 버퍼에 전이가 수천 개 쌓이기 전에는 학습하지 마세요. ~20개 샘플 위의 초기 기울기는 과적합됩니다.
- **타깃 동기화 주기.** 너무 잦으면 ≈ 타깃 네트워크가 없는 것; 너무 드물면 ≈ 타깃이 낡습니다. Atari DQN은 환경 스텝 10,000번을 씁니다. 경험칙: 학습 전체 구간의 약 1/100마다 동기화.
- **관측 전처리.** Atari DQN은 상태를 마르코프하게 만들려고 프레임 4개를 쌓습니다. 속도 정보가 있는 환경은 전부 프레임 스태킹이나 순환 상태가 필요합니다.

## 실전 활용

2026년에 DQN은 최신 기술(state-of-the-art)인 경우는 드물지만 여전히 오프폴리시의 기준 알고리즘입니다:

| 태스크 | 선호 방법 | 왜 DQN이 아닌가? |
|------|------------------|--------------|
| 이산 행동 Atari류 | Rainbow DQN 또는 Muesli | 같은 프레임워크, 트릭이 더 많음. |
| 연속 제어 | SAC / TD3 (페이즈 9 · 07) | DQN에는 정책 네트워크가 없음. |
| 온폴리시 / 고처리량 | PPO (페이즈 9 · 08) | 리플레이 버퍼가 없어 확장이 쉬움. |
| 오프라인 RL | CQL / IQL / Decision Transformer | 보수적 Q 타깃, 부트스트랩 폭주 없음. |
| 큰 이산 행동 공간(추천) | 행동 임베딩을 얹은 DQN 또는 IMPALA | 괜찮음; 장식이 중요할 뿐. |
| LLM RL | PPO / GRPO | 스텝 단위가 아니라 시퀀스 단위; 손실이 다름. |

그래도 교훈은 여기저기 통합니다. 리플레이와 타깃 네트워크는 SAC, TD3, DDPG, SAC-X, AlphaZero의 자가 대국 버퍼, 모든 오프라인 RL 방법에 등장합니다. 보상 클리핑은 PPO의 어드밴티지 정규화로 이어졌습니다. 이 아키텍처가 설계도입니다.

## 출시하기

`outputs/skill-dqn-trainer.md`로 저장하세요:

```markdown
---
name: dqn-trainer
description: 이산 행동 RL 태스크를 위한 DQN 학습 설정(버퍼, 타깃 동기화, ε 스케줄, 보상 클리핑)을 만듭니다.
version: 1.0.0
phase: 9
lesson: 5
tags: [rl, dqn, deep-rl]
---

이산 행동 환경(관측 형태, 행동 수, 시야, 보상 스케일)이 주어지면 다음을 출력합니다:

1. 네트워크. 아키텍처(MLP / CNN / Transformer), 특성 차원, 깊이.
2. 리플레이 버퍼. 용량, 미니배치 크기, 워밍업 크기.
3. 타깃 네트워크. 동기화 전략(C스텝마다 하드 복사 또는 소프트 τ).
4. 탐색. ε 시작 / 끝 / 스케줄 길이.
5. 손실. Huber vs MSE, 기울기 클리핑 값, 보상 클리핑 규칙.
6. Double DQN. 명시적인 끌 이유가 없는 한 기본 켜짐.

타깃 네트워크가 없거나, 리플레이 버퍼가 없거나, ε가 1로 고정된 DQN은 출시를 거부하세요. 연속 행동 태스크는 거부하세요(SAC / TD3로 안내). 스텝당 평균 보상의 10배를 넘는 보상 범위는 클리핑 또는 스케일 정규화가 필요하다고 표시하세요.
```

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 에피소드당 반환값 곡선을 그래프로 그리세요. 이동 평균이 -10을 넘으려면 몇 에피소드가 필요한가요?
2. **보통.** 타깃 네트워크를 끄세요(벨만 타깃 양변에 온라인 네트워크 사용). 학습 불안정성을 측정하세요 — 반환값이 진동하나요 발산하나요?
3. **어려움.** Double DQN을 추가하세요: `argmax a'` 선택은 온라인 네트워크, 평가는 타깃 네트워크. 시끄러운 보상의 GridWorld에서 1,000 에피소드 후 `Q(s_0, best_a)`와 참값 `V*(s_0)`의 편향을 Double DQN 유무로 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| DQN | "딥 Q-learning" | 신경망 Q 함수 + 리플레이 버퍼 + 타깃 네트워크를 얹은 Q-learning. |
| 경험 리플레이 | "섞은 전이들" | 기울기 스텝마다 균등 샘플링하는 링 버퍼; 데이터의 상관관계를 끊음. |
| 타깃 네트워크 | "얼린 부트스트랩" | 벨만 타깃에 쓰는 주기적 복사본 Q; 학습을 안정화. |
| 죽음의 삼중조 | "RL이 발산하는 이유" | 함수 근사 + 부트스트래핑 + 오프폴리시 = 수렴 보장 없음. |
| Double DQN | "최대화 편향의 해법" | 온라인 네트가 행동을 선택하고, 타깃 네트가 평가. |
| Dueling DQN | "V와 A 헤드" | Q = V + A - mean(A)로 분해; 같은 출력, 더 나은 기울기 흐름. |
| Rainbow | "모든 트릭" | DDQN + PER + 듀얼링 + n-스텝 + 노이즈 + 분산형을 하나로. |
| PER | "우선순위 리플레이" | TD 오차 크기에 비례해 전이를 샘플링. |

## 더 읽기

- [Mnih et al. (2013). Playing Atari with Deep Reinforcement Learning](https://arxiv.org/abs/1312.5602) — 딥 RL의 도화선이 된 2013 NeurIPS 워크숍 논문.
- [Mnih et al. (2015). Human-level control through deep reinforcement learning](https://www.nature.com/articles/nature14236) — Nature 논문, 49게임 DQN.
- [Hasselt, Guez, Silver (2016). Deep Reinforcement Learning with Double Q-learning](https://arxiv.org/abs/1509.06461) — DDQN.
- [Wang et al. (2016). Dueling Network Architectures](https://arxiv.org/abs/1511.06581) — 듀얼링 DQN.
- [Hessel et al. (2018). Rainbow: Combining Improvements in Deep RL](https://arxiv.org/abs/1710.02298) — 트릭을 쌓은 논문.
- [OpenAI Spinning Up — DQN](https://spinningup.openai.com/en/latest/algorithms/dqn.html) — 명쾌한 현대적 해설.
- [Sutton & Barto (2018). Ch. 9 — On-policy Prediction with Approximation](http://incompleteideas.net/book/RLbook2020.pdf) — DQN의 타깃 네트워크와 리플레이 버퍼가 길들이려는 "죽음의 삼중조"(함수 근사 + 부트스트래핑 + 오프폴리시)의 교과서적 다룸.
- [CleanRL DQN implementation](https://docs.cleanrl.dev/rl-algorithms/dqn/) — 소거 실험에서 쓰는 단일 파일 레퍼런스 DQN; 이 레슨의 스크래치 버전과 나란히 읽으면 좋습니다.
