# 게임을 위한 RL — AlphaZero, MuZero, 그리고 LLM 추론의 시대

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 1992년 TD-Gammon은 순수 TD(시간차 학습)만으로 백개먼 인간 챔피언을 꺾었습니다. 2016년 AlphaGo는 이세돌을 이겼습니다. 2017년 AlphaZero는 체스, 쇼기, 바둑을 제로부터 지배했습니다. 2024년 DeepSeek-R1은 같은 레시피에서 PPO를 GRPO로 바꾸면 추론에도 통한다는 것을 증명했습니다. 게임은 이 페이즈의 모든 돌파구를 이끌어 온 벤치마크입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 9 · 05 (DQN), 페이즈 9 · 08 (PPO), 페이즈 9 · 09 (RLHF), 페이즈 9 · 10 (MARL)
**소요 시간:** 약 120분

## 문제 상황

게임에는 RL이 원하는 모든 것이 있습니다. 깔끔한 보상(승/패). 무한한 에피소드(셀프 플레이 리셋). 완벽한 시뮬레이션(게임 자체가 곧 시뮬레이터). 이산적이거나 작은 연속 행동 공간. 적대적 강건성을 강제하는 멀티 에이전트 구조.

그리고 모든 주요 RL 돌파구는 게임으로 검증됐습니다. TD-Gammon(백개먼, 1992). Atari-DQN(2013). AlphaGo(2016). AlphaZero(2017). OpenAI Five(Dota 2, 2019). AlphaStar(StarCraft II, 2019). MuZero(학습된 모델, 2019). AlphaTensor(행렬 곱셈, 2022). AlphaDev(정렬 알고리즘, 2023). DeepSeek-R1(수학 추론, 2025) — 게임 RL 기법이 텍스트에도 통한다는 가장 최근의 증명입니다.

이 캡스톤 레슨은 세 개의 이정표 아키텍처 — AlphaZero, MuZero, GRPO — 를 하나의 통합 렌즈로 조맵니다: **셀프 플레이 + 탐색 + 정책 개선**. 각각은 이전 것을 일반화하며, 특히 GRPO는 AlphaZero의 레시피를 LLM 추론에 적용한 것입니다. 토큰이 행동이 되고, 수학적 검증이 승리 신호가 됩니다.

## 핵심 개념

![AlphaZero ↔ MuZero ↔ GRPO: 같은 루프, 다른 환경](../assets/rl-games.svg)

**통합 루프.**

```
while True:
    trajectory = self_play(current_policy, search)     # 자기 자신과 대국
    policy_target = search.improved_policy(trajectory) # 탐색이 날것의 정책을 개선
    policy_net.update(policy_target, value_target)     # 탐색 결과로 지도 학습
```

**AlphaZero (2017).** Silver 등. 규칙이 알려진 게임(체스, 쇼기, 바둑)이 주어지면:

- 정책-가치 네트워크: 타워 하나 `f_θ(s) → (p, v)`. `p`는 합법적인 수에 대한 사전확률, `v`는 예상 대국 결과입니다.
- 몬테카를로 트리 탐색(MCTS): 매 수마다 가능한 진행을 나무로 펼칩니다. `(p, v)`를 사전확률 + 부트스트랩으로 쓰고, UCB(PUCT)로 노드를 고릅니다: `a* = argmax Q(s, a) + c · p(a|s) · √N(s) / (1 + N(s, a))`.
- 셀프 플레이: 에이전트 대 에이전트로 대국합니다. `t`번째 수에서 MCTS 방문 분포 `π_t`가 정책 학습 목표가 됩니다.
- 손실: `L = (v - z)² - π · log p + c · ||θ||²`. `z`는 대국 결과(+1 / 0 / -1)입니다.

인간 지식 제로. 손으로 만든 휴리스틱 제로. 레시피 하나로 체스, 쇼기, 바둑을 각각 수천만 번의 셀프 플레이 대국 끝에 정복했습니다.

**MuZero (2019).** Schrittwieser 등. "규칙을 알아야 한다"는 요구 조건을 제거합니다.

- 고정된 환경 대신 *잠재 동역학 모델* `(h, g, f)`를 학습합니다:
  - `h(s)`: 관측을 잠재 상태로 인코딩.
  - `g(s_latent, a)`: 다음 잠재 상태 + 보상을 예측.
  - `f(s_latent)`: 정책 사전확률 + 가치를 예측.
- MCTS는 *학습된 잠재 공간*에서 돕니다. 같은 탐색, 같은 학습 루프.
- 바둑, 체스, 쇼기 *그리고* Atari에서 통합니다. 알고리즘 하나, 규칙 지식 없음.

**Stochastic MuZero (2022).** 확률적 동역학과 우연(chance) 노드를 추가해 백개먼류 게임으로 확장합니다.

**Muesli, Gumbel MuZero (2022-2024).** 샘플 효율과 결정론적 탐색을 개선한 후속 연구들입니다.

**GRPO (2024-2025).** DeepSeek-R1 레시피. AlphaZero와 같은 모양의 루프를 언어 모델 추론에 적용한 것입니다:

- "게임": 수학 / 코딩 / 추론 문제를 푸는 것. "승리" = 검증기(테스트 케이스 통과, 수치 답 일치)가 1을 반환하는 것.
- 정책: LLM. 행동: 토큰. 상태: 프롬프트 + 지금까지의 응답.
- 크리틱(PPO 스타일의 V_φ)이 없습니다. 대신 각 프롬프트마다 정책에서 완성문 `G`개를 샘플링하고, 각각의 보상을 계산한 뒤, **그룹 상대 어드밴티지** `A_i = (r_i - mean_r) / std_r`를 REINFORCE 스타일 갱신의 신호로 씁니다.
- 레퍼런스 정책에 대한 KL 페널티로 표류를 막습니다(RLHF와 같음).
- 전체 손실:

  `L_GRPO(θ) = -E_{q, {o_i}} [ (1/G) Σ_i A_i · log π_θ(o_i | q) ] + β · KL(π_θ || π_ref)`

보상 모델 없음, 크리틱 없음, MCTS 없음. 그룹 상대 베이스라인이 세 가지를 모두 대체합니다. 추론 벤치마크에서 PPO-RLHF급 이상의 품질을 컴퓨트의 일부로 달성합니다.

**R1 레시피 전체.** DeepSeek-R1(DeepSeek 2025)은 한 논문에 두 모델을 담고 있습니다:

- **R1-Zero.** DeepSeek-V3 베이스 모델에서 출발. SFT 없이 GRPO를 바로 적용하되 보상 구성 요소는 두 개입니다: *정확도 보상*(규칙 기반 — 최종 답이 올바른 숫자로 파싱되는지 / 코드가 단위 테스트를 통과하는지)과 *형식 보상*(완성문이 사고 과정을 `<think>…</think>` 태그로 감쌌는지). 수천 스텝에 걸쳐 평균 응답 길이가 약 100에서 약 10,000 토큰으로 늘어나고 수학 벤치마크 점수는 o1-preview 수준까지 올라갑니다. 모델이 추론을 제로부터 배우는 것입니다. 단점은: 사고 과정이 종종 읽기 어렵고, 언어가 뒤섞이고, 문체적 세련미가 없다는 것.
- **R1.** R1-Zero의 가독성 문제를 4단계 파이프라인으로 수정합니다:
  1. **콜드 스타트 SFT.** 깔끔한 형식의 긴 CoT(사고 과정) 시범 데이터 수천 건을 모아 베이스 모델을 지도 파인튜닝합니다. 읽을 수 있는 출발점을 만들어 줍니다.
  2. **추론 지향 GRPO.** 정확도+형식 보상에 *언어 일관성* 보상을 더해 코드 스위칭을 막으며 GRPO를 적용합니다.
  3. **기각 샘플링 + SFT 2차.** RL 체크포인트에서 추론 궤적 약 60만 개를 샘플링하고, 최종 답이 맞고 CoT가 읽을 수 있는 것만 남긴 뒤, 비추론 SFT 예시(글쓰기, QA, 자기 인지) 약 20만 개와 합쳐 베이스 모델을 다시 파인튜닝합니다.
  4. **전 영역 GRPO.** 추론(규칙 기반 보상)과 일반 정렬(유용성/무해성 선호 기반 보상)을 모두 아우르는 RL을 한 번 더 돌립니다.

결과는 오픈 웨이트로 AIME와 MATH-500에서 o1에 필적하고, 증류할 수 있을 만큼 작습니다. 같은 논문은 R1의 추론 흔적으로 SFT한 여섯 개의 증류 밀집 모델(Qwen-1.5B부터 Llama-70B까지)도 공개합니다 — 학생 쪽에서는 RL이 전혀 없습니다. 강한 RL 교사의 증류는 학생 규모에서 제로부터의 RL을 꾸준히 이깁니다.

**추론에는 왜 PPO 대신 GRPO인가.** DeepSeekMath 논문(2024년 2월)이 든 세 가지 이유: (1) 학습시킬 가치 네트워크가 없어 메모리가 절반; (2) 그룹 베이스라인이 추론 과제가 만들어 내는 궤적 끝의 희소 보상을 자연스럽게 처리; (3) 프롬프트별 정규화가 난이도가 크게 다른 문제들 사이에서도 어드밴티지를 비교 가능하게 만드는데, PPO의 단일 크리틱으로는 불가능합니다.

**탐색 없음 vs 탐색 기반.** 게임 RL은 갈라졌습니다:

- *긴 수평선의 완전 정보 게임*(바둑, 체스): 여전히 탐색 기반. AlphaZero / MuZero가 지배적.
- *LLM 추론*: 프로덕션에는 아직 MCTS 없음; 전체 롤아웃에 GRPO, 추론 컴퓨트로 best-of-N. 프로세스 보상 모델(PRM)이 단계 수준 탐색을 다시 붙이는 움직임을 암시합니다.

```figure
f3-selfplay-ladder
```

## 직접 만들기

`code/main.py`의 코드는 **미니어처 GRPO** — 샘플 그룹이 여러 개인 밴딧 — 를 구현합니다. 알고리즘은 LLM에서와 같고, 정책과 환경만 더 단순합니다. 이 코드는 *손실*과 *그룹 상대 어드밴티지*, 즉 2025년의 혁신을 가르칩니다.

### 단계 1: 아주 작은 검증기 환경

```python
QUESTIONS = [
    {"prompt": "q1", "correct": 3},
    {"prompt": "q2", "correct": 1},
]

def verify(prompt_idx, answer_token):
    return 1.0 if answer_token == QUESTIONS[prompt_idx]["correct"] else 0.0
```

진짜 GRPO에서 검증기는 단위 테스트를 돌리거나 수학적 등식을 확인합니다.

### 단계 2: 정책 — 프롬프트별 K개 답 토큰에 대한 소프트맥스

```python
def policy_probs(theta, p_idx):
    return softmax(theta[p_idx])
```

프롬프트가 주어졌을 때 LLM 마지막 층의 출력과 같습니다.

### 단계 3: 그룹 샘플링과 그룹 상대 어드밴티지

```python
def grpo_step(theta, p_idx, G=8, beta=0.01, lr=0.1, rng=None):
    probs = policy_probs(theta, p_idx)
    samples = [sample(probs, rng) for _ in range(G)]
    rewards = [verify(p_idx, s) for s in samples]
    mean_r = sum(rewards) / G
    std_r = stddev(rewards) + 1e-8
    advs = [(r - mean_r) / std_r for r in rewards]

    for a, A in zip(samples, advs):
        grad = onehot(a) - probs
        for i in range(len(probs)):
            theta[p_idx][i] += lr * A * grad[i]
    # KL 페널티: theta를 레퍼런스 쪽으로 당긴다
    for i in range(len(probs)):
        theta[p_idx][i] -= beta * (theta[p_idx][i] - reference[p_idx][i])
```

그룹 상대 어드밴티지가 2024년 DeepSeek의 트릭입니다. 크리틱이 필요 없습니다. "베이스라인"은 그룹 평균이고, 정규화는 그룹 표준편차를 씁니다.

### 단계 4: REINFORCE 베이스라인(가치 없음)과 비교

같은 설정, 같은 컴퓨트로 평범한 REINFORCE를 돌립니다. GRPO가 더 빠르고 안정적으로 수렴합니다.

### 단계 5: 엔트로피와 KL 관찰

RLHF와 같은 진단 지표입니다: 레퍼런스에 대한 평균 KL, 정책 엔트로피, 시간에 따른 보상. 이 값들이 안정되면 학습은 끝난 것입니다.

## 흔한 실수

- **검증기 농단을 통한 보상 해킹.** GRPO는 RLHF의 위험을 물려받습니다: 검증기가 틀렸거나 뚫릴 수 있으면 LLM은 그 구멍을 찾아냅니다. 강한 검증기(여러 테스트 케이스, 형식 증명)가 중요합니다.
- **그룹 크기가 너무 작음.** 그룹 베이스라인의 분산은 `1/√G`로 줄어듭니다. `G = 4` 미만에서는 어드밴티지 신호가 시끄럽습니다; 표준 선택은 `G = 8`~`64`입니다.
- **길이 편향.** 길이가 다른 LLM 완성문은 로그 확률도 다릅니다. 토큰 수로 정규화하거나, 시퀀스 수준 로그 확률을 쓰거나, 최대 길이로 자르세요.
- **순수 셀프 플레이 순환.** AlphaZero 스타일 학습은 일반합 게임에서 지배 루프에 갇힐 수 있습니다. 다양한 상대 풀(레슨 10의 리그 플레이)로 완화합니다.
- **탐색-정책 불일치.** AlphaZero는 탐색 결과를 흉내 내도록 정책을 학습시킵니다. 정책 네트워크가 탐색의 분포를 표현하기엔 너무 작으면 학습이 멈춥니다.
- **컴퓨트 최저선.** MuZero / AlphaZero는 엄청난 컴퓨트가 필요합니다. 단일 ablation에도 수백 GPU시간이 드는 일이 흔합니다. 학습용 미니어처 데모(예: Connect Four의 AlphaZero)가 존재합니다.
- **검증기 커버리지.** 버그 있는 해법도 통과시키는 단위 테스트는 그 버그를 강화합니다. 엣지 케이스를 잡는 검증기를 설계하세요.

## 실전에서 활용하기

도메인별 2026년 게임 RL 지형:

| 도메인 | 지배적 방법 |
|--------|-----------------|
| 2인 제로섬 보드게임(바둑, 체스, 쇼기) | AlphaZero / MuZero / KataGo |
| 불완전 정보 카드게임(포커) | CFR + 딥러닝 (DeepStack, Libratus, Pluribus) |
| Atari / 픽셀 게임 | Muesli / MuZero / IMPALA-PPO |
| 대규모 멀티플레이 전략(Dota, StarCraft) | PPO + 셀프 플레이 + 리그 (OpenAI Five, AlphaStar) |
| LLM 수학/코드 추론 | GRPO (DeepSeek-R1, Qwen-RL, 오픈 재현) |
| LLM 정렬 | DPO / RLHF-PPO (GRPO 아님; 검증기가 선호이지 검증 가능한 게 아님) |
| 로봇공학 | PPO + DR (게임 RL은 아니지만 같은 정책 경사 도구 사용) |
| 조합 최적화 문제 | AlphaZero 변형 (AlphaTensor, AlphaDev) |

이 *레시피* — 셀프 플레이, 탐색으로 보강한 개선, 정책 증류 — 는 텍스트, 픽셀, 물리 제어를 모두 관통합니다. GRPO는 가장 어린 사례일 뿐, 더 많은 것이 올 겁니다.

## 출시하기

`outputs/skill-game-rl-designer.md`로 저장하세요:

```markdown
---
name: game-rl-designer
description: 주어진 도메인에 맞는 게임 RL 또는 추론 RL 학습 파이프라인(AlphaZero / MuZero / GRPO)을 설계한다.
version: 1.0.0
phase: 9
lesson: 12
tags: [rl, alphazero, muzero, grpo, self-play]
---

대상(완전 정보 게임 / 불완전 정보 / Atari / LLM 추론 / 조합 문제)이 주어지면 다음을 출력합니다:

1. 환경 적합성. 규칙이 알려져 있는가? 마르코프인가? 확률적인가? 멀티 에이전트인가? AlphaZero vs MuZero vs GRPO 선택의 근거가 된다.
2. 탐색 전략. MCTS(학습된 사전확률의 PUCT), Gumbel 샘플링, best-of-N, 또는 없음.
3. 셀프 플레이 계획. 대칭 셀프 플레이 / 리그 / 오프라인 데이터 / 검증기 생성.
4. 목표 신호. 대국 결과 / 검증기 보상 / 선호 / 학습된 모델. 강건성 계획을 포함한다.
5. 진단. 베이스라인 대비 승률, ELO 곡선, 검증기 통과율, 레퍼런스에 대한 KL.

불완전 정보 게임에 AlphaZero를 쓰지 않는다(CFR로 안내). 신뢰할 수 있는 검증기 없이 GRPO를 쓰지 않는다. 고정 베이스라인 상대 세트가 없는 게임 RL 파이프라인은 받지 않는다(그렇지 않으면 셀프 플레이 ELO는 보정되지 않는다).
```

## 연습 문제

1. **쉬움.** `code/main.py`의 GRPO 밴딧을 구현하세요. 프롬프트 2개 × 답 토큰 4개로 학습해 `G=8`로 1,000회 갱신 안에 수렴시키세요.
2. **보통.** PPO(클리핑)와 바닐라 REINFORCE를 붙여 보세요. 같은 밴딧에서 GRPO와 샘플 효율과 보상 분산을 비교하세요.
3. **어려움.** 길이 2짜리 "추론 체인"으로 확장하세요: 에이전트가 토큰 두 개를 내놓고 검증기가 그 쌍에 보상을 줍니다. GRPO가 두 단계 시퀀스에 걸친 크레딧 할당을 어떻게 처리하는지 측정하세요. (힌트: *전체 시퀀스* 기준으로 그룹 어드밴티지를 계산해 두 토큰 위치에 모두 전파합니다.)

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| MCTS | "학습된 네트워크를 곁들인 트리 탐색" | 몬테카를로 트리 탐색; 학습된 `(p, v)` 사전확률로 UCB1/PUCT 선택. |
| AlphaZero | "셀프 플레이 + MCTS" | MCTS 방문과 대국 결과에 맞춰 학습된 정책-가치 네트워크. |
| MuZero | "학습 모델 AlphaZero" | 같은 루프지만 학습된 동역학의 잠재 공간에서 돈다. |
| GRPO | "크리틱 없는 PPO" | Group Relative Policy Optimization; 그룹 평균 베이스라인 + KL을 얹은 REINFORCE. |
| PUCT | "AlphaZero의 UCB" | `Q + c · p · √N / (1 + N_a)` — 가치 추정과 사전확률의 균형. |
| 셀프 플레이 | "에이전트 vs 과거의 나" | 제로섬의 표준; 대칭적인 학습 신호. |
| 리그 플레이 | "개체군 기반 셀프 플레이" | 과거 + 현재 + 익스플로이터를 상대로 샘플링. |
| 검증기 보상 | "검증 가능한 RL" | 보상이 결정론적 검사기(테스트 통과, 답 일치)에서 나온다. |
| 프로세스 보상 | "PRM" | 최종 답뿐 아니라 추론의 각 단계를 점수 매긴다. |

## 더 읽을거리

- [Silver et al. (2017). Mastering the game of Go without human knowledge (AlphaGo Zero)](https://www.nature.com/articles/nature24270).
- [Silver et al. (2018). A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play (AlphaZero)](https://www.science.org/doi/10.1126/science.aar6404).
- [Schrittwieser et al. (2020). Mastering Atari, Go, chess and shogi by planning with a learned model (MuZero)](https://www.nature.com/articles/s41586-020-03051-4).
- [Vinyals et al. (2019). Grandmaster level in StarCraft II (AlphaStar)](https://www.nature.com/articles/s41586-019-1724-z).
- [DeepSeek-AI (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models (GRPO)](https://arxiv.org/abs/2402.03300) — GRPO와 그룹 상대 베이스라인을 소개한 논문.
- [DeepSeek-AI (2025). DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) — 4단계 전체 R1 레시피와 R1-Zero ablation.
- [Brown et al. (2019). Superhuman AI for multiplayer poker (Pluribus)](https://www.science.org/doi/10.1126/science.aay2400) — 대규모 CFR + 딥러닝.
- [Tesauro (1995). Temporal Difference Learning and TD-Gammon](https://dl.acm.org/doi/10.1145/203330.203343) — 모든 것을 시작한 논문.
- [Hugging Face TRL — GRPOTrainer](https://huggingface.co/docs/trl/main/en/grpo_trainer) — 커스텀 보상 함수로 GRPO를 적용하는 프로덕션 레퍼런스.
- [Qwen Team (2024). Qwen2.5-Math — GRPO replication](https://github.com/QwenLM/Qwen2.5-Math) — 여러 규모에서 R1 레시피를 재현한 오픈 프로젝트.
- [Sutton & Barto (2018). Ch. 17 — Frontiers of Reinforcement Learning](http://incompleteideas.net/book/RLbook2020.pdf) — 셀프 플레이, 탐색, "설계된 보상"에 대한 교과서적 관점. R1이 LLM 규모에서 구현한 것이 바로 이것입니다.
