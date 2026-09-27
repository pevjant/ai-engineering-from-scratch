# 직접 선호 최적화(DPO) 계열

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> Rafailov et al. (2023)은 RLHF의 최적해가 선호 데이터 관점에서 닫힌 형태(closed form)로 존재함을 보였습니다. 그래서 명시적인 보상 모델을 건너뛰고 정책을 직접 최적화할 수 있습니다. 이 통찰이 하나의 계열을 낳았습니다 — IPO, KTO, SimPO, ORPO, BPO — 각각은 DPO의 한 실패 모드를 고치는 방법들입니다. 2026년에는 직접 정렬 알고리즘(DAA)이 PPO보다 많은 프론티어 포스트 트레이닝 런에 쓰입니다. 하지만 레슨 2의 과최적화 곡선은 여전히 적용됩니다. DAA도 굿하트에서 벗어나지 못하고, 굿하트가 물어뜯는 자리를 옮길 뿐입니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 6가지 변형 선호 손실 비교기)
**선수 지식:** 페이즈 18 · 01 (InstructGPT), 페이즈 18 · 02 (보상 해킹), 페이즈 10 · 08 (DPO 기초)
**시간:** 약 75분

## 학습 목표

- KL이 붙은 RLHF 최적해로부터 DPO의 닫힌 형태를 유도할 수 있습니다.
- IPO, KTO, SimPO, ORPO, BPO 각각이 DPO의 어떤 실패 모드를 고치는지 말할 수 있습니다.
- "암시적 보상 격차"와 "선호 강도"를 구분하고, IPO의 항등 함수 매핑이 왜 중요한지 설명할 수 있습니다.
- 명시적 RM이 없는데도 Rafailov et al. (NeurIPS 2024)가 DAA도 과최적화한다고 증명한 이유를 설명할 수 있습니다.

## 문제 상황

RLHF 목적 함수(레슨 1):

```
max_pi E_{x,y~pi} [ r(x, y) ] - beta * KL(pi || pi_ref)
```

에는 알려진 최적해가 있습니다:

```
pi*(y|x) = (1/Z(x)) * pi_ref(y|x) * exp(r(x, y) / beta)
```

그러므로 보상은 최적 정책과 참조 정책의 비율로 암시적으로 정의됩니다:

```
r(x, y) = beta * log(pi*(y|x) / pi_ref(y|x)) + beta * log Z(x)
```

이걸 Bradley-Terry 선호 가능도에 대입하면, 분배 함수 `Z(x)`는 `x`에만 의존하기 때문에 소거됩니다. 남는 것은 정책 파라미터만의 손실 함수 — 보상 모델이 필요 없습니다. 이것이 DPO입니다.

문제는: 이 유도는 최적해에 도달 가능하고, 선호 데이터가 분포 내에 있고, 참조 정책이 참 모드 앵커라는 가정을 깔고 있습니다. 셋 중 하나도 정확히 성립하지 않습니다. 그리고 이 계열의 모든 구성원이 서로 다른 깨진 가정을 고칩니다.

## 개념

### DPO (Rafailov et al., 2023)

```
L_DPO = -log sigmoid(
  beta * log(pi(y_w | x) / pi_ref(y_w | x))
  - beta * log(pi(y_l | x) / pi_ref(y_l | x))
)
```

무엇이 잘못될 수 있는가:

- 암시적 보상 격차 `beta * (log(pi/pi_ref)_w - log(pi/pi_ref)_l)`는 상한이 없습니다. 작은 선호 차이도 무한히 큰 격차를 만들어 낼 수 있습니다.
- 이 손실은 선택(chosen)과 기각(rejected) 로그확률을 반대 방향으로 밉니다. 기각이 더 빨리 떨어지기만 하면 선택의 절대 로그확률을 떨어뜨릴 수도 있습니다. 이것이 Degraded Chosen Response(열화된 선택 응답) 현상입니다.
- 분포 밖 선호(희귀 쌍 vs 희귀 쌍)는 아무런 의미 없는 암시적 보상을 만들어 냅니다.

### IPO (Azar et al., 2024)

항등 선호 최적화(Identity Preference Optimization)는 log-sigmoid를 선호 확률 위의 항등 함수 매핑으로 바꿉니다. 손실은 유계 목표에 대한 제곱 오차가 됩니다:

```
L_IPO = (log(pi(y_w | x) / pi_ref(y_w | x)) - log(pi(y_l | x) / pi_ref(y_l | x)) - 1/(2 beta))^2
```

마진이 `1/(2 beta)`로 유계입니다. 선호 강도와 암시적 보상 격차가 비례합니다. 폭발이 없습니다.

### KTO (Ethayarajh et al., 2024)

칸먼-트버스키 최적화(Kahneman-Tversky Optimization)는 쌍(pairwise) 구조를 완전히 버립니다. 단일 레이블 출력과 이진 "바람직함/바람직하지 않음" 신호가 주어지면, 전망 이론(prospect theory)의 효용에 매핑합니다:

```
v(x, y) = sigma(beta * log(pi(y|x) / pi_ref(y|x)) - z_ref)
```

이득과 손실에 다른 가중치를 둡니다(손실 회피). 장점: 훨씬 풍부한 비쌍(unpaired) 데이터를 쓸 수 있습니다.

### SimPO (Meng et al., 2024)

심플 선호 최적화(Simple Preference Optimization)는 학습 신호를 생성과 맞춥니다. 참조 정책을 완전히 빼고, 로그우도를 길이로 정규화합니다:

```
L_SimPO = -log sigmoid(
  (beta / |y_w|) * log pi(y_w | x)
  - (beta / |y_l|) * log pi(y_l | x)
  - gamma
)
```

안정화를 위한 마진 `gamma`가 붙습니다. 길이 정규화가 DPO의 길이 편향 실패 모드를 이용할 유인을 제거합니다(구조상 더 긴 `y_w`가 더 큰 로그확률 격차를 만드는 문제).

### ORPO (Hong et al., 2024)

오즈비 선호 최적화(Odds-Ratio Preference Optimization)는 표준 SFT 음의 로그우도에 선호 항을 더합니다:

```
L_ORPO = L_NLL(y_w) + lambda * L_OR
L_OR = -log sigmoid(log(odds(y_w) / odds(y_l)))
```

참조 정책이 없습니다 — SFT 항이 정규화 역할을 합니다. 베이스 모델에서 정렬된 모델까지 단일 스테이지로 학습합니다. 별도의 SFT 체크포인트가 필요 없습니다.

### BPO (ICLR 2026 투고, OpenReview id=b97EwMUWu7)

Degraded Chosen Responses 문제를 지적합니다. DPO는 순위 `y_w > y_l`을 지키지만 `y_w`의 절대 로그확률은 떨어질 수 있다는 것이죠. BPO는 선택 응답의 하락에 벌점을 주는 한 줄짜리 교정을 추가합니다. Llama-3.1-8B-Instruct의 수학 추론에서 DPO 대비 +10.1% 정확도를 보고했습니다.

### 보편적 결과: DAA도 여전히 과최적화합니다

Rafailov et al. "Scaling Laws for Reward Model Overoptimization in Direct Alignment Algorithms" (NeurIPS 2024)는 DPO, IPO, SLiC로 여러 데이터셋의 정책을 여러 KL 예산에서 학습했습니다. 골드 보상 대 KL 곡선은 Gao et al.과 같은 정점-붕괴 형태였습니다. 암시적 보상은 학습 중 분포 밖 샘플을 쿼리하고, KL 정규화는 이를 안정화하지 못합니다.

DAA도 굿하트에서 벗어나지 못합니다. 물어뜯는 표면을 "보상 모델 과최적화"에서 "참조 정책 비율 과최적화"로 바꿀 뿐입니다. 보편적 해법 — 더 나은 데이터, 앙상블, 조기 중단 — 은 양쪽에 모두 적용됩니다.

### 그중 고르기 (2026)

- 큰 쌍(pair) 선호 데이터가 있다면: 보수적인 beta로 DPO. 길이 편향이 뚜렷하면 SimPO.
- 비쌍 이진 피드백만 있다면: KTO.
- 베이스 모델에서 단일 스테이지 파이프라인을 원한다면: ORPO.
- DPO 로그에서 선택 로그확률의 열화가 보인다면: BPO.
- 선호 강도가 크게 들쭉날쭉하고 DPO가 포화 중이라면: IPO.

모든 연구소는 다섯 가지를 배터리로 돌려 보고 과제별로 승자를 고릅니다. 수학 추론과 안전의 최적해가 같을 이유가 없으니까요.

```figure
dpo-margin
```

## 사용해 보기

`code/main.py`는 실제 선호 강도가 쌍마다 다른 장난감 선호 데이터셋에서 여섯 손실(DPO, IPO, KTO, SimPO, ORPO, BPO)을 비교합니다. 각 손실은 같은 500쌍 샘플과 작은 소프트맥스 정책으로 최적화됩니다. 방법별 최종 승률, 선택 로그확률 표류, 암시적 보상 분포를 그래프로 그립니다.

## 출시하기

이 레슨은 `outputs/skill-preference-loss-selector.md`를 산출물로 만듭니다. 데이터셋 통계(쌍 여부, 균등 여부, 선호 강도 분포, 길이 분포)와 목표(단일 스테이지 또는 SFT 후 선호 학습)를 주면 선호 손실을 추천하고 그것이 막아 주는 실패 모드를 보고합니다.

## 연습 문제

1. `code/main.py`를 실행하세요. DPO와 BPO의 최종 선택 로그확률 하락 폭을 보고하세요. BPO가 더 높은 선택 절대 확률을 유지해야 합니다 — 이걸 검증하세요.

2. 선호 데이터를 모든 쌍의 강도가 같도록 바꿔 보세요. 여섯 방법 중 어느 것이 가장 견고한가요? 어느 것이 열화되나요? 여기서 IPO의 강점을 설명하세요.

3. 기각 응답이 평균적으로 선택 응답보다 2배 길게 만들어 보세요. 다른 것은 건드리지 말고, DPO의 길이 이용을 수치로 보이고 SimPO의 해법을 보여 주세요.

4. Rafailov et al. (NeurIPS 2024)는 DAA가 과최적화된다고 주장합니다. 단일 지점 버전을 재현해 보세요. 선택-기각 KL 발산을 그래프로 그리고, 큰 beta에서 DPO의 과최적화를 관찰하세요.

5. BPO 논문 초록(OpenReview b97EwMUWu7)을 읽으세요. BPO가 DPO에 더하는 한 줄 교정을 적어 보세요. `code/main.py`의 구현과 대조해 확인하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| DPO | "보상 모델 없는 RLHF" | 닫힌 형태 RLHF 최적해에서 유도된 손실. 정책 파라미터만 사용 |
| 암시적 보상 | "그 로그비" | `beta * log(pi(y\|x) / pi_ref(y\|x))` — DPO가 함축하는 보상 |
| IPO | "유계 DPO" | log-sigmoid를 항등 함수로 교체. 암시적 보상 격차가 `1/(2 beta)`로 상한 |
| KTO | "비쌍 DPO" | 단일 레이블 위의 전망 이론 효용, 손실 회피 적용 |
| SimPO | "참조 없는 DPO" | 길이 정규화 로그우도 + 마진. 참조 정책 없음 |
| ORPO | "원스테이지 DPO" | NLL + 오즈비 선호 항. 베이스 모델에서 한 번에 학습 |
| BPO | "선택 보존 DPO" | DPO에 선택 응답의 절대 로그확률 하락 벌점을 더함 |
| Degraded Chosen | "선택이 떨어짐" | 기각이 더 빨리 떨어지기만 하면 DPO가 선택 로그확률을 떨어뜨림 |
| DAA | "직접 정렬 알고리즘" | 명시적 RM을 건너뛰는 모든 선호 손실 방법 |

## 더 읽을거리

- [Rafailov et al. — Direct Preference Optimization (NeurIPS 2023, arXiv:2305.18290)](https://arxiv.org/abs/2305.18290)
- [Azar et al. — A General Theoretical Paradigm to Understand Learning from Human Preferences (AISTATS 2024, arXiv:2310.12036)](https://arxiv.org/abs/2310.12036) — IPO
- [Ethayarajh et al. — KTO: Model Alignment as Prospect Theoretic Optimization (arXiv:2402.01306)](https://arxiv.org/abs/2402.01306)
- [Meng, Xia, Chen — SimPO (NeurIPS 2024, arXiv:2405.14734)](https://arxiv.org/abs/2405.14734)
- [Hong, Lee, Thorne — ORPO (EMNLP 2024, arXiv:2403.07691)](https://arxiv.org/abs/2403.07691)
- [BPO — Behavior Preservation Optimization (ICLR 2026 OpenReview b97EwMUWu7)](https://openreview.net/forum?id=b97EwMUWu7)
- [Rafailov et al. — Scaling Laws for RM Overoptimization in DAAs (NeurIPS 2024, arXiv:2406.02900)](https://arxiv.org/abs/2406.02900)
