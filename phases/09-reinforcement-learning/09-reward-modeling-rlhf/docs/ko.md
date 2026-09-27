> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 보상 모델링 & RLHF

> 인간은 "좋은 어시스턴트 응답"에 대한 보상 함수를 직접 쓸 수는 없지만, 두 응답을 비교해서 더 나은 쪽을 고를 수는 있습니다. 그 비교들에 보상 모델을 피팅하고, 그 보상을 향해 언어 모델을 RL로 학습시킵니다. Christiano 2017. InstructGPT 2022. GPT-3를 ChatGPT로 바꾼 레시피입니다. 2026년에는 대부분 DPO로 대체되고 있지만 — 멘탈 모델은 그대로 남습니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 5 · 05(감성 분석), 페이즈 9 · 08(PPO)
**시간:** 약 45분

## 문제 상황

다음 토큰 예측 목적 함수로 언어 모델을 학습시켰습니다. 문법에 맞는 영어를 씁니다. 하지만 거짓말도 하고, 두서없이 늘어지고, 거절해야 할 때 거절도 하지 않습니다. 이것은 사전학습을 더 한다고 고쳐지지 않습니다 — 웹 텍스트가 문제지 치료약이 아니니까요.

"명령 X에 대해 응답 A가 응답 B보다 낫다"고 말해 주는 *스칼라 보상*이 필요합니다. 그 보상 함수를 손으로 쓰는 것은 불가능합니다. "유용성"은 토큰 위의 닫힌 형태 표현식이 아니니까요. 하지만 인간은 두 출력을 비교해서 선호를 표시할 수 있습니다. 대규모로 모으기도 저렴합니다.

RLHF(Christiano et al. 2017; Ouyang et al. 2022)는 선호를 보상 모델로 바꾸고, 그 보상을 향해 PPO로 LM을 최적화합니다. 세 단계입니다: SFT → RM → PPO. 2023~2025년 ChatGPT, Claude, Gemini 등 모든 정렬된(aligned) LLM을 출시시킨 레시피입니다.

2026년에는 PPO 단계가 대부분 DPO(페이즈 10 · 08)로 대체됩니다. 정렬 튜닝에는 더 저렴하고 거의 만큼 좋기 때문입니다. 하지만 *보상 모델* 조각은 여전히 모든 Best-of-N 샘플러, 검증 가능 보상 기반 RL 파이프라인, 프로세스 보상 모델을 쓰는 모든 추론 모델의 토대입니다. RLHF를 이해하면 정렬(alignment) 스택 전체를 이해하는 것입니다.

## 핵심 개념

![3단계 RLHF: SFT, 쌍별 선호에 대한 RM 학습, KL 벌점을 붙인 PPO](../assets/rlhf.svg)

**1단계: 지도 파인튜닝(SFT).** 사전학습된 베이스 모델에서 시작합니다. 목표 행동(명령 따르기 응답, 유용한 답변 등)에 대한 사람이 쓴 시범 데이터로 파인튜닝합니다. 결과: *좋은 행동 쪽으로 기울어졌지만* 여전히 무한한 행동 공간을 가진 모델 `π_SFT`.

**2단계: 보상 모델(RM) 학습.**

- 프롬프트 `x`에 대한 응답 쌍 `(y_+, y_-)`을 수집하고, 사람이 "y_+가 y_-보다 선호됨"이라고 표시합니다.
- `y_+`에 더 높은 점수를 주도록 보상 모델 `R_φ(x, y)`를 학습합니다.
- 손실: **Bradley-Terry 쌍별 로지스틱**:

  `L(φ) = -E[ log σ(R_φ(x, y_+) - R_φ(x, y_-)) ]`

  σ는 시그모이드입니다. 보상의 차이가 선호의 로그 오즈가 됩니다. BT는 1952년(Bradley-Terry)부터 표준이었고 현대 RLHF에서 지배적인 선택입니다.

- `R_φ`는 보통 SFT 모델 위에 스칼라 헤드를 붙여 초기화합니다. 같은 트랜스포머 백본; 선형 층 하나가 보상을 출력합니다.

**3단계: KL 벌점을 붙인 RM 대상 PPO.**

- 학습 가능한 정책 `π_θ`를 `π_SFT`에서 초기화합니다. 얼린 *참조* `π_ref = π_SFT`를 유지합니다.
- 응답 `y`의 끝에서 주어지는 보상:

  `r_total(x, y) = R_φ(x, y) - β · KL(π_θ(·|x) || π_ref(·|x))`

  KL 벌점은 `π_θ`가 `π_SFT`에서 멋대로 흘러가는 것을 막습니다 — 하드 신뢰 영역이 아니라 *정규화*입니다. `β`는 보통 `0.01`~`0.05`입니다.
- 이 보상으로 PPO(레슨 08)를 돌립니다. 어드밴티지는 토큰 단위 궤적에서 계산하지만, RM은 전체 응답에만 점수를 매깁니다.

**왜 KL인가?** 이것이 없으면 PPO는 기꺼이 보상 해킹 전략을 찾아냅니다 — RM은 분포 내(in-distribution) 완성문으로만 학습되었으니까요. 분포 밖 응답이 사람이 쓴 어떤 것보다 높은 점수를 받을 수도 있습니다. KL은 `π_θ`가 RM이 학습된 매니폴드 근처에 머물게 합니다. RLHF에서 가장 중요한 단 하나의 노브입니다.

**2026년 현황:**

- **DPO**(Rafailov 2023): 닫힌 형태의 대수가 2단계+3단계를 선호 데이터 위의 단일 지도 학습 손실로 압축합니다. RM도 없고 PPO도 없습니다. 일부분의 연산으로 정렬 벤치마크에서 같은 품질. 페이즈 10 · 08에서 다룹니다.
- **GRPO**(DeepSeek 2024~2025): 크리틱 대신 그룹 상대 베이스라인을 쓰는 PPO, 사람이 학습한 RM 대신 *검증기*(코드가 돌아가는지 / 수학 답이 맞는지)의 보상. 추론 모델에서 지배적. 페이즈 9 · 12에서 다룹니다.
- **프로세스 보상 모델(PRM):** 부분 해답(각 추론 스텝)에 점수를 매기며, 추론을 위한 RLHF와 GRPO 변형 양쪽에서 사용됩니다.
- **Constitutional AI / RLAIF:** 사람 대신 정렬된 LLM으로 선호를 생성합니다. 선호 예산을 확장합니다.

```figure
reward-model
```

## 직접 만들기

이 레슨은 문자열로 표현되는 작은 합성 "프롬프트"와 "응답"을 사용합니다. RM은 토큰 가방(bag-of-tokens) 표현 위의 선형 스코어러입니다. 실제 LLM은 없습니다 — 중요한 것은 파이프라인의 *형태*이지 규모가 아닙니다. `code/main.py`를 보세요.

### 단계 1: 합성 선호 데이터

```python
PROMPTS = ["help me", "answer me", "explain this"]
GOOD_WORDS = {"clear", "specific", "kind", "thorough"}
BAD_WORDS = {"vague", "rude", "wrong", "short"}

def make_pair(rng):
    x = rng.choice(PROMPTS)
    y_good = rng.choice(list(GOOD_WORDS)) + " " + rng.choice(list(GOOD_WORDS))
    y_bad = rng.choice(list(BAD_WORDS)) + " " + rng.choice(list(BAD_WORDS))
    return (x, y_good, y_bad)
```

실제 RLHF에서는 이것이 사람 라벨러로 대체됩니다. 형태 — `(prompt, preferred_response, rejected_response)` — 는 동일합니다.

### 단계 2: Bradley-Terry 보상 모델

선형 점수: `R(x, y) = w · bag(y)`. BT 쌍별 로그 손실을 최소화하도록 학습합니다:

```python
def rm_train_step(w, x, y_pos, y_neg, lr):
    r_pos = dot(w, bag(y_pos))
    r_neg = dot(w, bag(y_neg))
    p = sigmoid(r_pos - r_neg)
    for tok, cnt in bag(y_pos).items():
        w[tok] += lr * (1 - p) * cnt
    for tok, cnt in bag(y_neg).items():
        w[tok] -= lr * (1 - p) * cnt
```

몇백 번의 갱신 후에는 `w`가 좋은 단어 토큰에는 양의 가중치를, 나쁜 단어에는 음의 가중치를 부여합니다.

### 단계 3: RM 위의 PPO 스타일 정책

우리 토이 정책은 어휘에서 토큰 하나를 만들어 냅니다. RM 아래에서 토큰 점수를 매기고, `log π_θ(token | prompt)`를 계산하고, 참조 대비 KL 벌점을 더하고, 클리핑된 PPO 서러게이트를 적용합니다.

```python
def rlhf_step(theta, ref, w, prompt, rng, eps=0.2, beta=0.1, lr=0.05):
    logits_theta = policy_logits(theta, prompt)
    probs = softmax(logits_theta)
    token = sample(probs, rng)
    logits_ref = policy_logits(ref, prompt)
    probs_ref = softmax(logits_ref)
    reward = dot(w, bag([token])) - beta * kl(probs, probs_ref)
    # 보상을 반환값으로 삼아 theta 위에서 PPO 스타일 갱신
    ...
```

### 단계 4: KL 감시

매 갱신마다 평균 `KL(π_θ || π_ref)`를 추적하세요. `~5-10`을 넘어 기어 올라가면 정책이 `π_SFT`에서 멀리 흘러간 것입니다 — `β`를 낮추는 중이거나 보상 해킹이 시작된 것입니다. 실제 RLHF의 최상위 진단 항목입니다.

### 단계 5: TRL로 짜는 프로덕션(운영 환경) 레시피

토이 파이프라인을 이해했다면, 같은 루프를 실제 라이브러리 사용자가 쓰는 모습이 아래에 있습니다. Hugging Face의 [TRL](https://huggingface.co/docs/trl)이 레퍼런스 구현입니다 — 2단계는 `RewardTrainer`, 3단계는 참조 대비 KL이 내장된 `PPOTrainer`입니다.

```python
# 2단계: 쌍별 선호로부터 보상 모델
from trl import RewardTrainer, RewardConfig
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
rm = AutoModelForSequenceClassification.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct", num_labels=1
)

# 데이터셋 행: {"prompt", "chosen", "rejected"} — Bradley-Terry 형식
trainer = RewardTrainer(
    model=rm,
    tokenizer=tok,
    train_dataset=preference_data,
    args=RewardConfig(output_dir="./rm", num_train_epochs=1, learning_rate=1e-5),
)
trainer.train()
```

```python
# 3단계: SFT 참조에 KL 벌점을 붙여 RM 대상 PPO
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

policy = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-checkpoint")
ref    = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-checkpoint")  # frozen

ppo = PPOTrainer(
    config=PPOConfig(learning_rate=1.41e-5, batch_size=64, init_kl_coef=0.05,
                     target_kl=6.0, adap_kl_ctrl=True),
    model=policy, ref_model=ref, tokenizer=tok,
)

for batch in dataloader:
    responses = ppo.generate(batch["query_ids"], max_new_tokens=128)
    rewards   = rm(torch.cat([batch["query_ids"], responses], dim=-1)).logits[:, 0]
    stats     = ppo.step(batch["query_ids"], responses, rewards)
    # stats에는 mean_kl, clip_frac, value_loss가 들어 있다 — PPO의 세 가지 진단
```

라이브러리가 대신 해 주는 세 가지입니다. `adap_kl_ctrl=True`는 적응적 β 스케줄을 구현합니다: 관측된 KL이 `target_kl`을 넘으면 β를 두 배로, 절반 아래로 내려가면 β를 절반으로. 참조 모델은 관례상 얼려 둡니다 — 실수로 `policy`와 파라미터를 공유하면 안 됩니다. 그리고 가치 헤드는 정책과 같은 백본 위에 살아 있는데(`AutoModelForCausalLMWithValueHead`가 스칼라 MLP 헤드를 붙임), 그래서 TRL은 `policy/kl`과 `value/loss`를 따로 보고합니다.

## 흔한 함정

- **과최적화 / 보상 해킹.** RM은 불완전합니다. `π_θ`는 점수는 높지만 나쁜 적대적 완성문을 찾아냅니다. 증상: 인간 평가 점수는 정체되거나 떨어지는데 보상만 계속 오름. 해법: 일찍 멈추기, `β` 올리기, RM 학습 데이터 넓히기.
- **길이 해킹.** 유용한 응답으로 학습한 RM은 암묵적으로 길이에 보상을 주는 경우가 많습니다. 정책은 응답을 늘이는 법을 배우죠. 처방: 길이 정규화된 보상, 또는 길이를 인식하는 RM을 쓰는 RLAIF.
- **너무 작은 RM.** RM은 정책과 최소한 같은 크기여야 합니다. 작은 RM은 정책의 출력을 충실히 채점할 수 없습니다.
- **KL 튜닝.** β가 너무 낮으면 → 드리프트와 보상 해킹. 너무 높으면 → 정책이 거의 안 바뀜. 표준 트릭은 스텝당 고정 KL을 목표로 하는 *적응적* β입니다.
- **선호 데이터 노이즈.** 사람 라벨의 약 30%는 시끄럽거나 모호합니다. 합의 필터링된 데이터로 RM을 학습하거나 BT에 온도를 써서 보정하세요.
- **오프폴리시 문제.** PPO 데이터는 첫 에포크 이후 약간 오프폴리시입니다. 레슨 08처럼 클리핑 비율을 감시하세요.

## 실전 활용

2026년의 RLHF는 층으로 나뉩니다:

| 층 | 목표 | 방법 |
|-------|--------|--------|
| 명령 따르기, 유용성, 무해성 | 정렬 | RLHF-PPO보다 DPO(페이즈 10 · 08) 선호. |
| 추론 정확성(수학, 코드) | 능력 | 검증기 보상을 쓰는 GRPO(페이즈 9 · 12). |
| 긴 시야의 다중 스텝 태스크 | 에이전틱 | 스텝 위의 프로세스 보상 모델을 쓰는 PPO / GRPO. |
| 안전 / 거절 행동 | 안전 | 별도의 안전 RM을 쓰는 RLHF-PPO, 또는 Constitutional AI. |
| 추론 시 Best-of-N | 빠른 정렬 | 디코딩 시 RM 사용; 정책 학습 불필요. |
| 보상 증류 | 추론 연산 | 얼린 LM 위에 작은 "보상 헤드" 학습. |

RLHF는 2022~2024년의 *그* 방법이었습니다. 2026년에는 프로덕션(운영 환경) 정렬 파이프라인이 DPO 우선이고, RM 집약적이거나 안전이 중요한 단계에서만 PPO를 씁니다.

## 출시하기

`outputs/skill-rlhf-architect.md`로 저장하세요:

```markdown
---
name: rlhf-architect
description: 언어 모델을 위한 RLHF / DPO / GRPO 정렬 파이프라인을 설계합니다. RM, KL, 데이터 전략을 포함합니다.
version: 1.0.0
phase: 9
lesson: 9
tags: [rl, rlhf, alignment, llm]
---

베이스 LM, 목표 행동(정렬 / 추론 / 거절 / 에이전트), 선호 또는 검증기 예산이 주어지면 다음을 출력합니다:

1. 단계. SFT? RM? DPO? GRPO? 근거 포함.
2. 선호 또는 검증기 출처. 사람, AI 피드백, 규칙 기반, 유닛테스트 통과, 또는 보상 증류.
3. KL 전략. 고정 β, 적응적 β, 또는 DPO(암묵적 KL).
4. 진단. 평균 KL, 보상 안정성, 과최적화 방어(홀드아웃 인간 평가).
5. 안전 게이트. 레드팀 세트, 거절율, 유용성 RM과 분리된 안전 RM.

KL 모니터 없는 RLHF-PPO는 출시를 거부하세요. 목표 정책보다 작은 RM 사용은 거부하세요. 길이만 보는 보상은 거부하세요. 블라인드 인간 평가 세트를 따로 확보하지 않는 파이프라인은 과최적화 방어가 없다고 표시하세요.
```

## 연습 문제

1. **쉬움.** `code/main.py`의 Bradley-Terry 보상 모델을 500개 합성 선호 쌍으로 학습하세요. 따로 둔 100개 쌍에서 쌍별 정확도를 측정하세요. 90%를 넘어야 합니다.
2. **보통.** `β ∈ {0.0, 0.1, 1.0}`으로 토이 PPO-RLHF 루프를 돌리세요. 각각에 대해 갱신에 따른 RM 점수 대비 참조 대비 KL을 그래프로 그리세요. 어느 실행이 보상 해킹을 하나요?
3. **어려움.** 같은 선호 데이터로 DPO(닫힌 형태 선호 가능도 손실)를 구현하고, 쓴 연산량과 달성한 최종 RM 점수에서 RLHF-PPO 파이프라인과 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| RLHF | "정렬 RL" | 3단계 SFT + RM + PPO 파이프라인 (Christiano 2017, Ouyang 2022). |
| 보상 모델(RM) | "채점 네트" | Bradley-Terry로 쌍별 선호에 피팅한 학습된 스칼라 함수. |
| Bradley-Terry | "쌍별 로지스틱 손실" | `P(y_+ ≻ y_-) = σ(R(y_+) - R(y_-))`; 표준 RM 목적 함수. |
| KL 벌점 | "참조 근처에 머물기" | 보상에 들어가는 `β · KL(π_θ \|\| π_ref)`; 보상 해킹 방지 정규화. |
| 보상 해킹 | "굿하트의 법칙" | 정책이 RM의 허점을 악용함; 증상: 보상 상승, 인간 평가 정체. |
| RLAIF | "AI가 라벨 붙인 선호" | 라벨이 사람이 아니라 다른 LM에서 오는 RLHF. |
| PRM | "프로세스 보상 모델" | 부분 추론 스텝에 점수를 매김; 추론 파이프라인에서 사용. |
| Constitutional AI | "Anthropic의 방법" | 명시적 규칙이 이끄는 AI 생성 선호. |

## 더 읽기

- [Christiano et al. (2017). Deep Reinforcement Learning from Human Preferences](https://arxiv.org/abs/1706.03741) — RLHF를 시작시킨 논문.
- [Ouyang et al. (2022). InstructGPT — Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — ChatGPT의 뒤에 있던 레시피.
- [Stiennon et al. (2020). Learning to summarize with human feedback](https://arxiv.org/abs/2009.01325) — 요약을 위한 초기 RLHF.
- [Rafailov et al. (2023). Direct Preference Optimization](https://arxiv.org/abs/2305.18290) — DPO; 2026년 RLHF 이후의 기본값.
- [Bai et al. (2022). Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073) — RLAIF와 자기 비판 루프.
- [Anthropic RLHF 논문 (Bai et al. 2022). Training a Helpful and Harmless Assistant](https://arxiv.org/abs/2204.05862) — HH 논문.
- [Hugging Face TRL 라이브러리](https://huggingface.co/docs/trl) — 프로덕션(운영 환경) `RewardTrainer`와 `PPOTrainer`. 적응적 KL과 가치 헤드 디테일은 트레이너 소스를 읽으세요.
- [Hugging Face — Illustrating Reinforcement Learning from Human Feedback](https://huggingface.co/blog/rlhf), Lambert, Castricato, von Werra, Havrilla — 다이어그램과 함께 보는 3단계 파이프라인의 정석 워크스루.
- [von Werra et al. (2020). TRL: Transformer Reinforcement Learning](https://github.com/huggingface/trl) — 그 라이브러리; `examples/`에 Llama, Mistral, Qwen용 엔드투엔드 RLHF 스크립트가 있습니다.
- [Sutton & Barto (2018). Ch. 17.4 — Designing Reward Signals](http://incompleteideas.net/book/RLbook2020.pdf) — 보상 가설 관점; 보상 해킹을 생각하기 위한 필수 선수 지식.
