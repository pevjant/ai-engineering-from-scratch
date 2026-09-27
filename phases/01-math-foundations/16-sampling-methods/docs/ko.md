> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 샘플링 방법

> 샘플링은 AI가 가능성의 공간을 탐색하는 방법입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 1, 레슨 06-07(확률, 베이즈 정리)
**시간:** ~120분

## 학습 목표

- 균등 난수만 사용해서 역 CDF 샘플링, 기각 샘플링, 중요도 샘플링을 직접 구현합니다
- 언어 모델 토큰 생성을 위한 temperature, top-k, top-p(니클레우스) 샘플링을 만듭니다
- 재파라미터화 트릭(reparameterization trick)이 무엇인지, 그리고 VAE에서 샘플링을 통과하는 역전파를 가능하게 하는 이유를 설명합니다
- 메트로폴리스-해스팅스 MCMC를 실행해 정규화되지 않은 목표 분포에서 샘플을 뽑습니다

## 문제 상황

언어 모델이 여러분의 프롬프트 처리를 마치고 50,000개짜리 로짓(logit) 벡터를 내놓습니다. 어휘 집합의 토큰 하나하나마다 로짓이 하나씩 있는 것이죠. 이제 이 중 하나를 골라야 합니다. 어떻게 고를까요?

항상 확률이 가장 높은 토큰만 고르면 모든 응답이 똑같아집니다. 결정적(deterministic)이고 지루하죠. 반대로 완전히 무작위로 고르면 결과는 엉터리가 됩니다. 답은 이 두 극단 사이 어딘가에 있고, 그 '어딘가'를 조절하는 것이 바로 샘플링입니다.

샘플링은 텍스트 생성에만 쓰이는 게 아닙니다. 강화 학습은 궤적(trajectory)을 샘플링해서 정책 그래디언트를 추정합니다. VAE는 학습한 분포에서 샘플을 뽑고 그 무작위성을 통과해 역전파를 흘려보내면서 잠재 표현(latent representation)을 배웁니다. 확산(diffusion) 모델은 노이즈를 샘플링한 뒤 반복적으로 노이즈를 제거하면서 이미지를 만듭니다. 몬테카를로 방법은 닫힌 형태(closed-form)의 해가 없는 적분을 추정합니다. MCMC 알고리즘은 하나하나 세어 볼 수조차 없는 고차원 사후 분포를 탐색합니다.

모든 생성형 AI 시스템은 곧 샘플링 시스템입니다. 샘플링 전략이 산출물의 품질, 다양성, 제어 가능성을 결정합니다. 이 레슨에서는 균등 난수에서 출발해 현대 LLM과 생성 모델을 움직이는 기술들로 끝나는, 주요 샘플링 방법을 모두 직접 만들어 봅니다.

## 핵심 개념

### 샘플링이 왜 중요한가

샘플링은 AI와 머신러닝 전반에서 네 가지 기본적인 역할로 등장합니다:

**생성(Generation).** 언어 모델, 확산 모델, GAN은 모두 샘플링으로 결과물을 만듭니다. 샘플링 알고리즘이 창의성, 일관성, 다양성을 직접 조절합니다. Temperature, top-k, 니클레우스 샘플링은 엔지니어가 매일 만지는 다이얼입니다.

**학습(Training).** 확률적 경사 하강법은 미니배치를 샘플링합니다. 드롭아웃은 비활성화할 뉴런을 샘플링합니다. 데이터 증강은 무작위 변환을 샘플링합니다. 중요도 샘플링은 강화 학습(PPO, TRPO)에서 샘플에 가중치를 다시 매겨 그래디언트 분산을 줄입니다.

**추정(Estimation).** 머신러닝의 많은 양들은 닫힌 형태의 해가 없습니다. 데이터 분포에 대한 기대 손실, 에너지 기반 모델의 분배 함수, 베이즈 추론의 증거(evidence) 같은 것들이죠. 몬테카를로 추정은 샘플을 평균 내어 이 모든 것을 근사합니다.

**탐색(Exploration).** MCMC 알고리즘은 베이즈 추론에서 사후 분포를 탐색합니다. 진화 전략은 파라미터 섭동을 샘플링합니다. 톰슨 샘플링(Thompson sampling)은 밴딧(bandit) 문제에서 탐색과 활용의 균형을 잡습니다.

핵심 난제는 이것입니다. 단순한 분포(균등 분포, 정규 분포)에서만 직접 샘플을 뽑을 수 있다는 점입니다. 나머지 모든 분포에 대해서는, 단순한 샘플을 목표 분포의 샘플로 바꿔주는 방법이 필요합니다.

### 균등 난수 샘플링

모든 샘플링 방법은 여기서 출발합니다. 균등 난수 생성기는 [0, 1) 범위의 값을 만들어내며, 같은 길이의 부분 구간은 모두 같은 확률을 가집니다.

```
U ~ Uniform(0, 1)

P(a <= U <= b) = b - a    (0 <= a <= b <= 1일 때)

성질:
  E[U] = 0.5
  Var(U) = 1/12
```

n개 항목으로 이루어진 이산 집합에서 균등하게 뽑으려면 U를 생성한 뒤 floor(n * U)를 반환하면 됩니다. 연속 구간 [a, b]에서 뽑으려면 a + (b - a) * U를 계산합니다.

핵심 통찰: 균등 난수 하나에는 어떤 분포에서든 샘플 하나를 만들기에 딱 맞는 양의 무작위성이 들어 있습니다. 요령은 올바른 변환을 찾는 것입니다.

### 역 CDF 방법(역변환 샘플링)

누적 분포 함수(CDF, Cumulative Distribution Function)는 값을 확률로 대응시킵니다:

```
F(x) = P(X <= x)

성질:
  F는 감소하지 않음(단조 증가)
  F(-inf) = 0
  F(+inf) = 1
  F는 실수 전체를 [0, 1]로 대응
```

역 CDF는 확률을 다시 값으로 되돌려줍니다. U ~ Uniform(0, 1)이면 X = F_inverse(U)는 목표 분포를 따릅니다.

```
알고리즘:
  1. u ~ Uniform(0, 1) 생성
  2. F_inverse(u) 반환

왜 작동하나:
  P(X <= x) = P(F_inverse(U) <= x) = P(U <= F(x)) = F(x)
```

**지수 분포 예시:**

```
PDF: f(x) = lambda * exp(-lambda * x),   x >= 0
CDF: F(x) = 1 - exp(-lambda * x)

F(x) = u를 x에 대해 풀면:
  u = 1 - exp(-lambda * x)
  exp(-lambda * x) = 1 - u
  x = -ln(1 - u) / lambda

(1 - U)와 U는 같은 분포이므로:
  x = -ln(u) / lambda
```

F_inverse를 닫힌 형태로 적어둘 수만 있다면 이 방법은 완벽하게 작동합니다. 정규 분포는 역 CDF가 닫힌 형태로 존재하지 않기 때문에 다른 방법(Box-Muller 변환, 수치 근사)을 사용합니다.

**이산 버전:** 이산 분포라면 CDF를 누적 합으로 만들어 두고, U를 생성한 뒤 누적 합이 처음 U를 넘어서는 인덱스를 찾으면 됩니다. 레슨 06의 `sample_categorical`이 바로 이렇게 동작합니다.

### 기각 샘플링

CDF를 뒤집을 수는 없지만 목표 PDF를 상수 배까지는 계산할 수 있을 때, 기각 샘플링(rejection sampling)이 유용합니다.

```
목표 분포: p(x)  (상수 배까지 계산 가능, 정규화 안 되어 있어도 됨)
제안 분포: q(x)  (샘플링 가능)
상계: 모든 x에 대해 p(x) <= M * q(x)를 만족하는 M

알고리즘:
  1. x ~ q(x) 샘플
  2. u ~ Uniform(0, 1) 샘플
  3. u < p(x) / (M * q(x))이면 x를 받아들임
  4. 아니면 기각하고 1번으로

수용률 = 1/M
```

상계 M이 타이트할수록 수용률이 높아집니다. 저차원(1~3차원)에서는 기각 샘플링이 잘 작동합니다. 고차원에서는 제안 공간의 대부분이 기각되기 때문에 수용률이 지수적으로 떨어집니다. 기각 샘플링에게 차원의 저주(curse of dimensionality)가 닥치는 순간이죠.

**예시: 절단 정규 분포(truncated normal) 샘플링.** 절단된 구간 위에서 균등 제안 분포를 사용합니다. 포락(envelope) M은 그 구간에서 정규 PDF의 최댓값입니다.

**예시: 반원(semicircle) 샘플링.** 감싸는 사각형 안에서 균등하게 점을 찍고, 그 점이 반원 안에 떨어지면 받아들입니다. 몬테카를로가 원주율 pi를 계산하는 방식이 바로 이것입니다. 수용률이 넓이 비율 pi/4와 같거든요.

### 중요도 샘플링

때로는 목표 분포 p(x)의 샘플 자체가 필요한 게 아닙니다. p(x) 아래에서 기댓값을 추정해야 하는데, 손에 있는 샘플은 다른 분포 q(x)에서 온 것일 수 있죠.

```
목표: E_p[f(x)] = f(x) * p(x)의 적분 추정

재배열:
  E_p[f(x)] = f(x) * (p(x)/q(x)) * q(x)의 적분
            = E_q[f(x) * w(x)]

여기서 w(x) = p(x) / q(x)가 바로 중요도 가중치(importance weight)입니다.

추정량:
  E_p[f(x)] ~ (1/N) * sum(f(x_i) * w(x_i))    (x_i ~ q(x))
```

이 방식은 강화 학습에서 결정적으로 중요합니다. PPO(Proximal Policy Optimization)에서는 오래된 정책 pi_old 아래에서 궤적을 수집하면서, 동시에 새 정책 pi_new를 최적화하고 싶어 합니다. 이때 중요도 가중치는 pi_new(a|s) / pi_old(a|s)입니다. PPO는 이 가중치를 클리핑해서 새 정책이 옛 정책에서 너무 멀리 벗어나지 않도록 합니다.

중요도 샘플링 추정량의 분산은 q가 p와 얼마나 비슷한지에 달려 있습니다. q가 p와 크게 다르면 소수의 샘플이 어마어마한 가중치를 받아 추정 전체를 좌우하고 말죠. 자기 정규화 중요도 샘플링(self-normalized importance sampling)은 가중치의 합으로 나누어 이 문제를 줄입니다:

```
E_p[f(x)] ~ sum(w_i * f(x_i)) / sum(w_i)
```

### 몬테카를로 추정

몬테카를로 추정은 무작위 샘플을 평균 내어 적분을 근사합니다. 큰수의 법칙이 수렴을 보장합니다.

```
목표: 정의역 D에서의 I = g(x)의 적분 추정

방법:
  1. D에서 x_1, ..., x_N을 균등하게 샘플
  2. I ~ (D의 부피 / N) * sum(g(x_i))

오차: O(1 / sqrt(N))   차원과 무관
```

오차율은 차원과 무관합니다. 격자 기반 적분이 불가능한 고차원에서 몬테카를로 방법이 왕좌를 차지하는 이유가 바로 이것입니다.

**pi 추정하기:**

```
[-1, 1] x [-1, 1]에서 (x, y)를 균등하게 샘플
단위원 안에 떨어지는 점(x^2 + y^2 <= 1)을 셈
pi ~ 4 * (안쪽 점 개수) / (전체 개수)
```

**기댓값 추정하기:**

```
E[f(X)] ~ (1/N) * sum(f(x_i))    (x_i ~ p(x))

표본 평균은 참 기댓값으로 수렴합니다.
추정량의 분산 = Var(f(X)) / N
```

### 마르코프 연쇄 몬테카를로(MCMC): 메트로폴리스-해스팅스

MCMC는 정상 분포(stationary distribution)가 목표 분포 p(x)인 마르코프 연쇄(Markov chain)를 만듭니다. 충분한 단계를 거치고 나면, 이 연쇄가 내놓는 샘플은 (근사적으로) p(x)의 샘플이 됩니다.

```
목표: p(x)  (정규화 상수 빼고 알고 있음)
제안: q(x'|x)  (현재 상태가 주어졌을 때 다음 상태를 제안하는 방법)

메트로폴리스-해스팅스 알고리즘:
  1. 적당한 x_0에서 시작
  2. t = 1, 2, ..., T에 대해:
     a. x' ~ q(x'|x_t) 제안
     b. 수용 비율 계산:
        alpha = [p(x') * q(x_t|x')] / [p(x_t) * q(x'|x_t)]
     c. 확률 min(1, alpha)로 수용:
        - u < alpha이면 (u ~ Uniform(0,1)): x_{t+1} = x'
        - 아니면: x_{t+1} = x_t
  3. 처음 B개 샘플은 버림(번인, burn-in)
  4. 남은 샘플 반환
```

제안이 대칭이면(q(x'|x) = q(x|x')) 비율이 p(x')/p(x)로 단순해집니다. 이것이 원조 격인 메트로폴리스 알고리즘입니다.

**왜 작동하나.** 수용 규칙은 상세 균형(detailed balance)을 보장합니다. x에 있다가 x'로 움직일 확률이, x'에 있다가 x로 움직일 확률과 정확히 같다는 뜻이죠. 상세 균형이 성립하면 p(x)가 연쇄의 정상 분포가 됩니다.

**실전 고려 사항:**
- 번인(burn-in): 연쇄가 평형 상태에 도달하기 전의 초기 샘플은 버립니다
- 씨닝(thinning): 자기상관을 줄이기 위해 k번째마다 하나씩만 남깁니다
- 제안 분포 크기: 너무 작으면 연쇄가 느리게 움직이고(수용률은 높지만 탐색이 느림), 너무 크면 대부분의 제안이 기각됩니다(수용률이 낮아 제자리에 머묾)
- 고차원에서 가우시안 제안에 대한 최적 수용률은 약 0.234입니다

### 깁스 샘플링

깁스 샘플링(Gibbs sampling)은 다변량 분포를 위한 MCMC의 특별한 경우입니다. 모든 차원에서 한 번에 움직이는 대신, 한 번에 변수 하나를 그 변수의 조건부 분포에서 갱신합니다.

```
목표: p(x_1, x_2, ..., x_d)

알고리즘:
  각 반복 t마다:
    x_1^{t+1} ~ p(x_1 | x_2^t, x_3^t, ..., x_d^t) 샘플
    x_2^{t+1} ~ p(x_2 | x_1^{t+1}, x_3^t, ..., x_d^t) 샘플
    ...
    x_d^{t+1} ~ p(x_d | x_1^{t+1}, x_2^{t+1}, ..., x_{d-1}^{t+1}) 샘플
```

깁스 샘플링이 성립하려면 각 조건부 분포 p(x_i | x_{-i})에서 샘플을 뽑을 수 있어야 합니다. 많은 모델에서 이건 어렵지 않습니다:
- 베이지언 네트워크: 조건부 분포가 그래프 구조에서 바로 나옵니다
- 가우시안 혼합: 조건부 분포가 가우시안입니다
- 이징(Ising) 모델: 각 스핀의 조건부 분포는 이웃에만 의존합니다

수용률은 항상 1입니다(모든 제안이 받아들여짐). 정확한 조건부 분포에서 샘플링하면 상세 균형이 자동으로 만족되기 때문입니다.

**한계.** 변수들이 서로 강하게 상관되어 있으면 깁스 샘플링의 혼합(mixing)이 느려집니다. 한 번에 변수 하나씩 갱신하는 방식으로는 분포를 가로지르는 큰 대각선 이동을 할 수 없기 때문입니다.

### Temperature 샘플링(LLM에서 사용)

언어 모델은 어휘의 각 토큰에 대해 로짓 z_1, ..., z_V를 출력합니다. 소프트맥스(softmax)가 이 값들을 확률로 바꾸죠. Temperature는 소프트맥스에 넣기 전에 로짓의 스케일을 조정합니다:

```
p_i = exp(z_i / T) / sum(exp(z_j / T))

T = 1.0: 표준 소프트맥스(원래 분포)
T -> 0:  argmax(결정적, 항상 가장 높은 로짓 선택)
T -> inf: 균등(모든 토큰이 똑같이 가능)
T < 1.0: 분포를 뾰족하게(더 확신에 차고, 덜 다양)
T > 1.0: 분포를 평평하게(덜 확신에 차고, 더 다양)
```

**왜 작동하나.** 로짓을 T < 1로 나누면 로짓 간 차이가 증폭됩니다. z_1 = 2, z_2 = 1일 때 T = 0.5로 나누면 z_1/T = 4, z_2/T = 2가 되어 격차가 벌어지죠. 소프트맥스를 통과하면 가장 높은 로짓을 가진 토큰이 훨씬 큰 몫을 가져갑니다.

**실전에서:**
- T = 0.0: 그리디 디코딩, 사실 기반 질의응답에 최적
- T = 0.3-0.7: 살짝 창의적, 코드 생성에 적합
- T = 0.7-1.0: 균형 잡힘, 일반 대화에 적합
- T = 1.0-1.5: 창작, 브레인스토밍
- T > 1.5: 점점 무작위적, 유용한 경우가 드묾

Temperature는 어떤 토큰이 가능한지를 바꾸지 않습니다. 각 토큰에 배분되는 확률 질량을 바꿀 뿐입니다.

### Top-k 샘플링

Top-k 샘플링은 후보 집합을 확률이 가장 높은 k개 토큰으로 제한한 뒤, 다시 정규화해서 그 좁혀진 집합에서 샘플을 뽑습니다.

```
알고리즘:
  1. V개 토큰 전부의 소프트맥스 확률 계산
  2. 확률 기준으로 토큰 정렬(내림차순)
  3. 상위 k개 토큰만 남김
  4. 재정규화: p_i' = p_i / sum(top-k에 속한 j의 p_j)
  5. 재정규화된 분포에서 샘플

k = 1:  그리디 디코딩
k = V:  필터링 없음(표준 샘플링)
k = 40: 전형적인 설정, 가능성 낮은 토큰의 긴 꼬리를 제거
```

Top-k는 어휘 분포의 긴 꼬리에 숨어 있는, 극도로 가능성 낮은 토큰(오타, 무의미한 말)을 모델이 고르는 사고를 막아줍니다. 문제는 k가 문맥과 상관없이 고정된다는 점입니다. 모델이 확신에 찬 경우(어떤 토큰이 95% 확률)에도 k = 40이면 39개의 대안이 여전히 허용됩니다. 반대로 모델이 불확실한 경우(확률이 1000개 토큰에 흩어짐)에는 k = 40이 그럴듯한 선택지를 잘라버리죠.

### Top-p(니클레우스) 샘플링

Top-p 샘플링은 후보 집합 크기를 동적으로 조절합니다. 토큰 수를 고정하는 대신, 누적 확률이 p를 넘는 최소한의 토큰 집합만 남깁니다.

```
알고리즘:
  1. V개 토큰 전부의 소프트맥스 확률 계산
  2. 확률 기준으로 토큰 정렬(내림차순)
  3. 상위 k개 확률의 합이 p 이상이 되는 가장 작은 k를 찾음
  4. 그 k개 토큰만 남김
  5. 재정규화하고 샘플

p = 0.9:  확률 질량의 90%를 커버하는 토큰만 유지
p = 1.0:  필터링 없음
p = 0.1:  매우 제한적, 거의 그리디
```

모델이 확신에 차 있으면 니클레우스 샘플링은 토큰을 몇 개(2~3개 정도)만 남깁니다. 모델이 불확실하면 많이 남기고요(200개 정도). 이 적응적 동작 때문에 니클레우스 샘플링이 일반적으로 top-k보다 더 나은 텍스트를 만들어냅니다.

**자주 쓰는 조합:**
- Temperature 0.7 + top-p 0.9: 범용으로 좋은 설정
- Temperature 0.0(그리디): 결정적 작업에 최적
- Temperature 1.0 + top-k 50: Fan et al. (2018) 원논문의 설정

Top-k와 top-p는 조합할 수 있습니다. 먼저 top-k를 적용하고, 남은 집합에 top-p를 적용합니다.

### 재파라미터화 트릭(VAE에서 사용)

변이형 오토인코더(VAE, Variational Autoencoder)는 입력을 잠재 공간(latent space)의 분포로 인코딩하고, 그 분포에서 샘플을 뽑고, 다시 그 샘플을 디코딩하는 방식으로 학습합니다. 문제는 샘플링 연산을 통과해서는 역전파를 할 수 없다는 점입니다.

```
표준 샘플링(미분 불가):
  z ~ N(mu, sigma^2)

  무작위성이 그래디언트 흐름을 막습니다.
  d/d_mu [N(mu, sigma^2)에서의 샘플] = ???
```

재파라미터화 트릭(reparameterization trick)은 무작위성을 파라미터로부터 분리합니다:

```
재파라미터화된 샘플링:
  epsilon ~ N(0, 1)          (고정된 무작위 노이즈, 파라미터 없음)
  z = mu + sigma * epsilon   (파라미터의 결정적 함수)

  이제 z는 mu와 sigma의 결정적이고 미분 가능한 함수입니다.
  d(z)/d(mu) = 1
  d(z)/d(sigma) = epsilon

  그래디언트가 mu와 sigma를 통과해 흐릅니다.
```

이게 작동하는 이유는 N(mu, sigma^2)가 mu + sigma * N(0, 1)과 같은 분포이기 때문입니다. 핵심 통찰: 무작위성을 파라미터 없는 원천(epsilon)으로 옮기고, 샘플을 파라미터의 미분 가능한 변환으로 표현한다.

**VAE 학습 루프에서는:**
1. 인코더가 각 입력에 대해 mu와 log(sigma^2)를 출력합니다
2. epsilon ~ N(0, 1)을 샘플합니다
3. z = mu + sigma * epsilon을 계산합니다
4. z를 디코딩해 입력을 재구성합니다
5. 4, 3, 2, 1 단계를 거슬러 역전파합니다(3단계가 미분 가능하기 때문에 가능)

재파라미터화 트릭이 없다면 VAE는 표준 역전파로 학습할 수 없습니다. 이 단 하나의 통찰이 VAE를 실용적으로 만들었습니다.

### Gumbel-Softmax(미분 가능한 범주형 샘플링)

재파라미터화 트릭은 연속 분포(가우시안)에서 작동합니다. 이산 범주형(categorical) 분포에는 다른 접근이 필요합니다. Gumbel-Softmax는 범주형 샘플링의 미분 가능한 근사를 제공합니다.

**Gumbel-Max 트릭(미분 불가):**

```
로그 확률 log(p_1), ..., log(p_k)를 가진 범주형 분포에서 샘플하려면:
  1. 각 범주마다 g_i ~ Gumbel(0, 1)을 샘플
     (g = -log(-log(u)), 여기서 u ~ Uniform(0, 1))
  2. argmax(log(p_i) + g_i) 반환

이렇게 하면 정확한 범주형 샘플이 나옵니다.
```

**Gumbel-Softmax(미분 가능한 근사):**

```
하드 argmax를 부드러운 소프트맥스로 교체:
  y_i = exp((log(p_i) + g_i) / tau) / sum(exp((log(p_j) + g_j) / tau))

tau(온도)가 근사를 조절합니다:
  tau -> 0:  원-핫 벡터에 가까워짐(하드 범주형)
  tau -> inf: 균등에 가까워짐 (1/k, 1/k, ..., 1/k)
  tau = 1.0: 소프트 근사
```

Gumbel-Softmax는 이산 샘플의 연속 완화(continuous relaxation)를 만들어냅니다. 출력은 하드 원-핫이 아니라 확률 벡터(소프트 원-핫)이고, 그래디언트는 소프트맥스를 통과해 흐릅니다. 학습 중 순전파에서는 "straight-through" 추정기를 쓸 수 있습니다. 순전파에는 하드 argmax를 쓰되, 역전파에는 소프트 Gumbel-Softmax 그래디언트를 쓰는 방식이죠.

**활용 분야:**
- VAE의 이산 잠재 변수
- 신경망 구조 탐색(neural architecture search, 이산 연산 선택)
- 하드 어텐션 메커니즘
- 이산 행동을 가진 강화 학습

### 층화 샘플링

표준 몬테카를로 샘플링은 우연 때문에 샘플 공간에 빈 구멍을 남길 수 있습니다. 층화 샘플링(stratified sampling)은 공간을 층(strata)으로 나누고 각 층에서 샘플을 뽑아 골고루 뒤덮이도록 강제합니다.

```
표준 몬테카를로:
  [0, 1]에서 N개 점을 균등하게 샘플
  어떤 지역엔 샘플이 몰리고, 어떤 지역은 빌 수 있음

층화 샘플링:
  [0, 1]을 N개의 동일한 층으로 나눔: [0, 1/N), [1/N, 2/N), ..., [(N-1)/N, 1)
  각 층 안에서 점 하나를 균등하게 샘플
  x_i = (i + u_i) / N   (u_i ~ Uniform(0, 1),  i = 0, ..., N-1)
```

층화 샘플링은 표준 몬테카를로와 비교해 항상 분산이 같거나 더 낮습니다:

```
Var(층화) <= Var(표준 몬테카를로)

f(x)가 매끄럽게 변할 때 개선 폭이 가장 큽니다.
구간별 상수 함수(piecewise-constant)라면 층화 샘플링은 정확합니다.
```

**활용 분야:**
- 수치 적분(준 몬테카를로, quasi-Monte Carlo)
- 학습 데이터 분할(각 폴드에서 클래스 균형 보장)
- 층화를 결합한 중요도 샘플링(두 기법의 조합)
- NeRF(Neural Radiance Fields)는 카메라 광선을 따라 층화 샘플링을 사용합니다

### 확산 모델과의 연결

확산(diffusion) 모델은 샘플링 과정을 통해 이미지를 생성합니다. 순방향 과정은 T 단계에 걸쳐 이미지에 가우시안 노이즈를 더해 순수한 노이즈로 만듭니다. 역방향 과정은 노이즈 제거를 학습해서 원래 이미지를 한 단계씩 되살려 냅니다.

```
순방향 과정(알려져 있음):
  x_t = sqrt(alpha_t) * x_{t-1} + sqrt(1 - alpha_t) * epsilon
  (epsilon ~ N(0, I))

  T단계 후: x_T ~ N(0, I)  (순수 노이즈)

역방향 과정(학습됨):
  x_{t-1} = (1/sqrt(alpha_t)) * (x_t - (1 - alpha_t)/sqrt(1 - alpha_bar_t) * epsilon_theta(x_t, t)) + sigma_t * z
  (z ~ N(0, I))

  각 노이즈 제거 단계가 곧 샘플링 단계입니다.
```

이 레슨의 방법들과의 연결고리:
- 각 노이즈 제거 단계는 재파라미터화 트릭을 사용합니다(노이즈를 샘플링하고 결정적 변환을 적용)
- 노이즈 스케줄 {alpha_t}는 일종의 temperature 어닐링(annealing)을 조절합니다
- 학습은 몬테카를로 추정으로 ELBO(증거 하한, evidence lower bound)를 근사합니다
- 확산 모델의 조상 샘플링(ancestral sampling)은 마르코프 연쇄입니다(각 단계는 현재 상태에만 의존)

이미지 생성 과정 전체가 반복 샘플링입니다. 노이즈에서 출발해, 각 단계마다 학습된 노이즈 제거 모델을 조건으로 삼아 조금 덜 노이즈 낀 버전을 샘플링하는 것이죠.

```figure
monte-carlo-pi
```

## 직접 만들기

### 단계 1: 균등 샘플링과 역 CDF 샘플링

```python
import math
import random

def sample_uniform(a, b):
    return a + (b - a) * random.random()

def sample_exponential_inverse_cdf(lam):
    u = random.random()
    return -math.log(u) / lam
```

지수 분포 샘플 10,000개를 생성하고 평균이 1/lambda인지 확인해 보세요.

### 단계 2: 기각 샘플링

```python
def rejection_sample(target_pdf, proposal_sample, proposal_pdf, M):
    while True:
        x = proposal_sample()
        u = random.random()
        if u < target_pdf(x) / (M * proposal_pdf(x)):
            return x
```

기각 샘플링으로 절단 정규 분포에서 샘플을 뽑아 보세요. 샘플로 히스토그램을 그려 모양을 확인합니다.

### 단계 3: 중요도 샘플링

```python
def importance_sampling_estimate(f, target_pdf, proposal_pdf, proposal_sample, n):
    total = 0
    for _ in range(n):
        x = proposal_sample()
        w = target_pdf(x) / proposal_pdf(x)
        total += f(x) * w
    return total / n
```

균등 제안 분포를 사용해 정규 분포 아래에서 E[X^2]를 추정해 보세요. 알려진 답(mu^2 + sigma^2)과 비교합니다.

### 단계 4: 몬테카를로로 pi 추정하기

```python
def monte_carlo_pi(n):
    inside = 0
    for _ in range(n):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        if x*x + y*y <= 1:
            inside += 1
    return 4 * inside / n
```

### 단계 5: 메트로폴리스-해스팅스 MCMC

```python
def metropolis_hastings(target_log_pdf, proposal_sample, proposal_log_pdf, x0, n_samples, burn_in):
    samples = []
    x = x0
    for i in range(n_samples + burn_in):
        x_new = proposal_sample(x)
        log_alpha = (target_log_pdf(x_new) + proposal_log_pdf(x, x_new)
                     - target_log_pdf(x) - proposal_log_pdf(x_new, x))
        if math.log(random.random()) < log_alpha:
            x = x_new
        if i >= burn_in:
            samples.append(x)
    return samples
```

쌍봉 분포(두 가우시안의 혼합)에서 샘플을 뽑아 보세요. 연쇄의 궤적을 시각화합니다.

### 단계 6: 깁스 샘플링

```python
def gibbs_sampling_2d(conditional_x_given_y, conditional_y_given_x, x0, y0, n_samples, burn_in):
    x, y = x0, y0
    samples = []
    for i in range(n_samples + burn_in):
        x = conditional_x_given_y(y)
        y = conditional_y_given_x(x)
        if i >= burn_in:
            samples.append((x, y))
    return samples
```

### 단계 7: Temperature 샘플링

```python
def softmax(logits):
    max_l = max(logits)
    exps = [math.exp(z - max_l) for z in logits]
    total = sum(exps)
    return [e / total for e in exps]

def temperature_sample(logits, temperature):
    scaled = [z / temperature for z in logits]
    probs = softmax(scaled)
    return sample_from_probs(probs)
```

토큰 로짓 집합에 대해 temperature가 출력 분포를 어떻게 바꾸는지 확인해 보세요.

### 단계 8: Top-k와 top-p 샘플링

```python
def top_k_sample(logits, k):
    indexed = sorted(enumerate(logits), key=lambda x: -x[1])
    top = indexed[:k]
    top_logits = [l for _, l in top]
    probs = softmax(top_logits)
    idx = sample_from_probs(probs)
    return top[idx][0]

def top_p_sample(logits, p):
    probs = softmax(logits)
    indexed = sorted(enumerate(probs), key=lambda x: -x[1])
    cumsum = 0
    selected = []
    for token_idx, prob in indexed:
        cumsum += prob
        selected.append((token_idx, prob))
        if cumsum >= p:
            break
    sel_probs = [pr for _, pr in selected]
    total = sum(sel_probs)
    sel_probs = [pr / total for pr in sel_probs]
    idx = sample_from_probs(sel_probs)
    return selected[idx][0]
```

### 단계 9: 재파라미터화 트릭

```python
def reparam_sample(mu, sigma):
    epsilon = random.gauss(0, 1)
    return mu + sigma * epsilon

def reparam_gradient(mu, sigma, epsilon):
    dz_dmu = 1.0
    dz_dsigma = epsilon
    return dz_dmu, dz_dsigma
```

재파라미터화된 샘플에는 그래디언트가 흐르지만 직접 샘플링에는 흐르지 않음을 보여주세요.

### 단계 10: Gumbel-Softmax

```python
def gumbel_sample():
    u = random.random()
    return -math.log(-math.log(u))

def gumbel_softmax(logits, temperature):
    gumbels = [math.log(p) + gumbel_sample() for p in logits]
    return softmax([g / temperature for g in gumbels])
```

temperature를 낮추면 출력이 원-핫 벡터에 가까워진다는 것을 보여주세요.

모든 시각화가 포함된 전체 구현은 `code/sampling.py`에 있습니다.

## 실전에서 쓰기

NumPy와 SciPy가 있다면, 실무에서 쓰는 버전은 이렇습니다:

```python
import numpy as np

rng = np.random.default_rng(42)

exponential_samples = rng.exponential(scale=2.0, size=10000)
print(f"Exponential mean: {exponential_samples.mean():.4f} (expected 2.0)")

from scipy import stats
normal = stats.norm(loc=0, scale=1)
print(f"CDF at 1.96: {normal.cdf(1.96):.4f}")
print(f"Inverse CDF at 0.975: {normal.ppf(0.975):.4f}")

logits = np.array([2.0, 1.0, 0.5, 0.1, -1.0])
temperature = 0.7
scaled = logits / temperature
probs = np.exp(scaled - scaled.max()) / np.exp(scaled - scaled.max()).sum()
token = rng.choice(len(logits), p=probs)
print(f"Sampled token index: {token}")
```

규모 있는 MCMC에는 전용 라이브러리를 사용하세요:
- PyMC: NUTS(적응형 HMC)를 갖춘 풀 베이지언 모델링
- emcee: 앙상블 MCMC 샘플러
- NumPyro/JAX: GPU 가속 MCMC

여러분은 이것들을 직접 만들었습니다. 이제 라이브러리 호출이 무엇을 하는지 알고 있는 것이죠.

## 연습 문제

1. 코시(Cauchy) 분포에 대한 역 CDF 샘플링을 구현하세요. CDF는 F(x) = 0.5 + arctan(x)/pi입니다. 샘플 10,000개를 생성해 히스토그램을 참 PDF와 겹쳐 그려 보세요. 두꺼운 꼬리(중심에서 아주 먼 극단값)에 주목합니다.

2. 기각 샘플링으로 Uniform(0, 1) 제안을 사용해 Beta(2, 5) 분포의 샘플을 생성하세요. 수용된 샘플을 참 Beta PDF와 겹쳐 그려 보세요. 이론적 수용률은 얼마일까요?

3. 몬테카를로로 sin(x)을 0부터 pi까지 적분해 보세요. 샘플 수는 1,000, 10,000, 100,000개를 사용합니다. 각 수준에서 오차를 비교하고, 오차가 O(1/sqrt(N))로 줄어드는지 확인합니다.

4. 2차원 분포 p(x, y) ∝ exp(-(x^2 * y^2 + x^2 + y^2 - 8*x - 8*y) / 2)에서 샘플을 뽑는 메트로폴리스-해스팅스를 구현하세요. 샘플과 연쇄 궤적을 그려 보고, 서로 다른 제안 분포 표준편차로 실험해 봅니다.

5. 완전한 텍스트 생성 데모를 만들어 보세요. 로짓이 주어진 10개 단어 어휘로, (a) 그리디, (b) temperature=0.7, (c) top-k=3, (d) top-p=0.9를 사용해 20토큰 시퀀스를 생성합니다. 5회 실행 결과의 다양성을 비교해 보세요.

## 핵심 용어

| 용어 | 흔히 하는 말 | 실제 의미 |
|------|----------------|----------------------|
| 샘플링 | "무작위 값을 뽑는 것" | 확률 분포에 따라 값을 생성하는 것. 모든 생성형 AI 뒤에 있는 메커니즘 |
| 균등 분포 | "모두 똑같이 가능" | [a, b]의 모든 값이 같은 확률 밀도 1/(b-a)를 가짐. 모든 샘플링 방법의 출발점 |
| 역 CDF | "확률 변환" | F_inverse(U)는 균등 샘플을, CDF를 아는 임의의 분포의 샘플로 바꿈. 정확하고 효율적 |
| 기각 샘플링 | "제안하고 수용/기각" | 단순한 제안 분포에서 생성하고, 목표/제안 비율에 비례하는 확률로 수용. 정확하지만 샘플이 낭비됨 |
| 중요도 샘플링 | "샘플에 가중치 다시 매기기" | q(x)의 샘플에 p(x)/q(x) 가중치를 매겨 p(x) 아래의 기댓값을 추정. 강화 학습 PPO의 핵심 |
| 몬테카를로 | "무작위 샘플의 평균" | 적분을 샘플 평균으로 근사. 차원과 무관하게 오차 O(1/sqrt(N)) |
| MCMC | "수렴하는 무작위 걸음" | 정상 분포가 목표인 마르코프 연쇄를 구성. 메트로폴리스-해스팅스가 기초 알고리즘 |
| 메트로폴리스-해스팅스 | "오르막은 수용, 내리막은 때때로 수용" | 이동을 제안하고 밀도 비율로 수용 여부 결정. 상세 균형이 목표 분포로의 수렴을 보장 |
| 깁스 샘플링 | "한 번에 변수 하나씩" | 나머지는 고정한 채 각 변수를 조건부 분포에서 갱신. 수용률 100% |
| Temperature | "확신 다이얼" | 소프트맥스 전에 로짓을 T로 나눔. T<1이면 뾰족해지고(더 확신), T>1이면 평평해짐(더 다양) |
| Top-k 샘플링 | "k개 베스트만 유지" | 확률 상위 k개를 제외한 토큰은 0으로 만들고 재정규화해 샘플. 후보 집합 크기 고정 |
| 니클레우스 샘플링(top-p) | "가능성 높은 것만 유지" | 누적 확률이 p를 넘는 최소 토큰 집합만 유지. 후보 집합 크기가 적응적으로 변함 |
| 재파라미터화 트릭 | "무작위성을 밖으로 꺼내기" | z = mu + sigma * epsilon (epsilon ~ N(0,1))로 표현. 샘플링을 미분 가능하게 만듦. VAE 학습에 필수 |
| Gumbel-Softmax | "부드러운 범주형 샘플링" | Gumbel 노이즈 + temperature를 곁들인 소프트맥스로 범주형 샘플링을 미분 가능하게 근사 |
| 층화 샘플링 | "강제로 골고루" | 샘플 공간을 층으로 나누고 각 층에서 샘플. 순진한 몬테카를로보다 항상 분산이 낮음 |
| 번인(burn-in) | "워밍업 기간" | 연쇄가 정상 분포에 도달하기 전의 초기 MCMC 샘플은 버림 |
| 상세 균형 | "가역성 조건" | p(x) * T(x->y) = p(y) * T(y->x). p가 마르코프 연쇄의 정상 분포이기 위한 충분조건 |
| 확산 샘플링 | "반복 노이즈 제거" | 노이즈에서 출발해 학습된 노이즈 제거 단계를 적용해 데이터를 생성. 각 단계는 조건부 샘플링 연산 |

## 더 읽을거리

- [Holbrook (2023): The Metropolis-Hastings Algorithm](https://arxiv.org/abs/2304.07010) - MCMC 기초에 대한 상세 튜토리얼
- [Jang, Gu, Poole (2017): Categorical Reparameterization with Gumbel-Softmax](https://arxiv.org/abs/1611.01144) - Gumbel-Softmax 원논문
- [Holtzman et al. (2020): The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) - 니클레우스(top-p) 샘플링 논문
- [Kingma & Welling (2014): Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) - 재파라미터화 트릭을 소개한 VAE 논문
- [Ho, Jain, Abbeel (2020): Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) - 샘플링과 이미지 생성을 연결한 DDPM 논문
