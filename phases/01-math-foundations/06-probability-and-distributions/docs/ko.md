# 확률과 분포 (Probability and Distributions)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 확률은 AI가 불확실성을 표현할 때 쓰는 언어입니다.

**유형:** Learn
**언어:** Python
**선수 지식:** 페이즈 1, 레슨 01-04
**소요 시간:** 약 75분

## 학습 목표

- 베르누이, 범주형, 포아송, 균등, 정규 분포의 PMF와 PDF를 처음부터 구현하기
- 기댓값과 분산을 계산하고, 중심극한정리로 가우시안이 어디에나 있는 이유 설명하기
- 수치 안정화 트릭(최대 로짓 빼기)을 적용한 softmax와 log-softmax 함수 만들기
- 로짓으로부터 교차 엔트로피 손실을 계산하고 음의 로그 가능도와 연결하기

## 문제 상황

분류기가 `[0.03, 0.91, 0.06]`을 출력합니다. 언어 모델은 50,000개 후보 중 다음 단어를 고릅니다. 확산 모델은 학습한 분포에서 샘플링해 이미지를 만들어 냅니다. 이 모두가 확률이 실전에서 쓰이는 모습입니다.

모델이 내놓는 모든 예측은 확률 분포입니다. 모든 손실 함수는 예측 분포가 진짜 분포와 얼마나 먼지 잽니다. 모든 학습 단계는 한 분포가 다른 분포를 더 닮도록 파라미터를 조정합니다. 확률 없이는 ML 논문 한 편을 읽을 수도, 모델 하나를 디버깅할 수도, 학습 손실이 NaN이 되는 이유를 이해할 수도 없습니다.

## 핵심 개념

### 사건, 표본 공간, 확률

표본 공간 S는 가능한 모든 결과의 집합입니다. 사건은 표본 공간의 부분집합이죠. 확률은 사건을 0과 1 사이의 숫자로 대응시킵니다.

```
동전 던지기:
  S = {H, T}
  P(H) = 0.5,  P(T) = 0.5

주사위 한 번 굴리기:
  S = {1, 2, 3, 4, 5, 6}
  P(짝수) = P({2, 4, 6}) = 3/6 = 0.5
```

세 공리가 확률 전체를 정의합니다:
1. 어떤 사건 A에 대해서도 P(A) >= 0
2. P(S) = 1 (무언가는 반드시 일어난다)
3. A와 B가 동시에 일어날 수 없다면 P(A 또는 B) = P(A) + P(B)

나머지 전부(베이즈 정리, 기댓값, 분포)는 이 세 규칙에서 따라 나옵니다.

### 조건부 확률과 독립

P(A|B)는 B가 일어났다는 조건에서의 A의 확률입니다.

```
P(A|B) = P(A and B) / P(B)

예: 카드 한 벌
  P(킹 | 그림 카드) = P(킹이면서 그림 카드) / P(그림 카드)
                      = (4/52) / (12/52)
                      = 4/12 = 1/3
```

한 사건을 알아도 다른 사건에 대해 아무것도 알려 주지 않으면, 두 사건은 독립입니다:

```
독립:           P(A|B) = P(A)
동치:           P(A and B) = P(A) * P(B)
```

동전 던지기는 독립입니다. 카드를 뽑고 다시 넣지 않는 방식은 독립이 아닙니다.

### 확률질량함수 vs 확률밀도함수

이산 확률 변수는 확률질량함수(PMF)를 가집니다. 각 결과마다 직접 읽을 수 있는 확률이 매겨져 있죠.

```
PMF: P(X = k)

공정한 주사위:
  P(X = 1) = 1/6
  P(X = 2) = 1/6
  ...
  P(X = 6) = 1/6

  모든 확률의 합 = 1
```

연속 확률 변수는 확률밀도함수(PDF)를 가집니다. 단일 지점에서의 밀도는 확률이 아닙니다. 확률은 밀도를 구간에 걸쳐 적분해야 나옵니다.

```
PDF: f(x)

P(a <= X <= b) = f(x)를 a부터 b까지 적분

f(x)는 1보다 클 수 있음 (확률이 아니라 밀도)
f(x)를 -inf부터 +inf까지 적분하면 = 1
```

이 구분이 ML에서 중요합니다. 분류 출력은 PMF(이산 선택)입니다. VAE 잠재 공간은 PDF(연속)를 사용합니다.

### 자주 쓰이는 분포들

**베르누이:** 시행 한 번, 결과 둘. 이진 분류를 모델링합니다.

```
P(X = 1) = p
P(X = 0) = 1 - p
평균 = p,  분산 = p(1-p)
```

**범주형(Categorical):** 시행 한 번, 결과 k개. 다중 클래스 분류(소프트맥스 출력)를 모델링합니다.

```
P(X = i) = p_i,  단 p_i의 합 = 1
예: P(고양이) = 0.7,  P(개) = 0.2,  P(새) = 0.1
```

**균등(Uniform):** 모든 결과가 똑같이 나올 확률. 무작위 초기화에 사용됩니다.

```
이산: P(X = k) = 1/n (k in {1, ..., n})
연속: f(x) = 1/(b-a) (x in [a, b])
```

**정규(가우시안):** 종 모양 곡선. 평균(mu)과 분산(sigma^2)으로 매개변수화됩니다.

```
f(x) = (1 / sqrt(2*pi*sigma^2)) * exp(-(x - mu)^2 / (2*sigma^2))

표준 정규: mu = 0, sigma = 1
  데이터의 68%가 1 sigma 안에
  95%가 2 sigma 안에
  99.7%가 3 sigma 안에
```

**포아송:** 고정된 구간 안의 희귀 사건 횟수. 사건 발생률을 모델링합니다.

```
P(X = k) = (lambda^k * e^(-lambda)) / k!
평균 = lambda,  분산 = lambda
```

### 기댓값과 분산

기댓값은 가중 평균 결과입니다.

```
이산:   E[X] = x_i * P(X = x_i)의 합
연속:   E[X] = x * f(x)의 적분
```

분산은 평균 주변으로 흩어진 정도를 잽니다.

```
Var(X) = E[(X - E[X])^2] = E[X^2] - (E[X])^2
표준편차 = sqrt(Var(X))
```

ML에서 기댓값은 손실 함수(데이터 분포에 걸친 평균 손실)로 등장합니다. 분산은 모델의 안정성을 알려 줍니다. 그래디언트 분산이 크면 학습이 시끄럽다(noisy)는 뜻이죠.

### 결합 분포와 주변 분포

결합 분포 P(X, Y)는 두 확률 변수를 함께 기술합니다.

결합 PMF 예시 (X = 날씨, Y = 우산):

| | Y=0 (우산 없음) | Y=1 (우산 있음) | 주변 P(X) |
|---|---|---|---|
| X=0 (맑음) | 0.40 | 0.10 | P(X=0) = 0.50 |
| X=1 (비) | 0.05 | 0.45 | P(X=1) = 0.50 |
| **주변 P(Y)** | P(Y=0) = 0.45 | P(Y=1) = 0.55 | 1.00 |

주변 분포는 다른 변수를 모두 합쳐 없앱니다(sum out):

```
P(X = x) = 모든 y에 대해 P(X = x, Y = y)의 합
```

위 표의 행 합계와 열 합계가 바로 주변 분포입니다.

### 정규 분포가 어디에나 나타나는 이유

중심극한정리(CLT): 독립인 확률 변수 여러 개의 합(또는 평균)은, 원래 분포가 무엇이든 정규 분포로 수렴합니다.

```
주사위 1개:  균등 분포 (평평함)
주사위 2개의 평균:  삼각형 모양 (뾰족)
주사위 30개의 평균:  거의 완벽한 종 모양

어떤 시작 분포에서도 동작합니다.
```

그래서 이런 일들이 벌어집니다:
- 측정 오차는 대략 정규 분포를 따릅니다 (작은 독립 원인이 많이 겹치니까)
- 신경망의 가중치 초기화는 정규 분포를 사용합니다
- SGD의 그래디언트 노이즈는 대략 정규 분포입니다 (많은 샘플 그래디언트의 합)
- 정규 분포는 주어진 평균과 분산에서 최대 엔트로피 분포입니다

### 로그 확률

원래 확률 값은 수치 문제를 일으킵니다. 작은 확률을 여러 번 곱하면 금방 언더플로로 0이 되어 버리죠.

```
P(문장) = P(word1) * P(word2) * ... * P(word_n)
            = 0.01 * 0.003 * 0.02 * ...
            -> 0.0 (약 30항 이후 언더플로)
```

로그 확률이 이걸 고칩니다. 곱셈이 덧셈이 됩니다.

```
log P(문장) = log P(word1) + log P(word2) + ... + log P(word_n)
                = -4.6 + -5.8 + -3.9 + ...
                -> 유한한 숫자 (언더플로 없음)
```

규칙:
- log(a * b) = log(a) + log(b)
- 로그 확률은 항상 <= 0 (0 < P <= 1이니까)
- 더 음수일수록 = 덜 가능함
- 교차 엔트로피 손실은 정답 클래스의 음의 로그 확률입니다

### 확률 분포로서의 소프트맥스

신경망은 날것의 점수(로짓)를 출력합니다. 소프트맥스는 이걸 유효한 확률 분포로 바꿉니다.

```
softmax(z_i) = exp(z_i) / sum(exp(z_j) for all j)

성질:
  - 모든 출력이 (0, 1) 안에 있음
  - 모든 출력의 합이 1
  - 입력의 상대적 순서를 보존
  - exp()가 로짓 사이의 차이를 증폭
```

소프트맥스 트릭: 오버플로를 막으려면 지수를 계산하기 전에 최대 로짓을 빼 줍니다.

```
z = [100, 101, 102]
exp(102) = 오버플로

z_shifted = z - max(z) = [-2, -1, 0]
exp(0) = 1  (안전)

결과는 같은데 오버플로는 없습니다.
```

Log-softmax는 소프트맥스와 로그를 합쳐 수치 안정성을 확보합니다. PyTorch가 교차 엔트로피 손실을 내부적으로 이 방식으로 계산합니다.

### 샘플링

샘플링은 분포에서 무작위 값을 뽑는 일입니다. ML에서:
- 드롭아웃은 0으로 만들 뉴런을 무작위로 샘플링합니다
- 데이터 증강은 무작위 변환을 샘플링합니다
- 언어 모델은 예측 분포에서 다음 토큰을 샘플링합니다
- 확산 모델은 노이즈를 샘플링하고 점진적으로 노이즈를 제거합니다

임의의 분포에서 샘플링하려면 역변환 샘플링, 기각 샘플링, 재매개변화 트릭(VAE에서 사용) 같은 기법이 필요합니다.

```figure
gaussian-pdf
```

## 직접 만들기

### 단계 1: 확률 기초

```python
import math
import random

def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def combinations(n, k):
    return factorial(n) // (factorial(k) * factorial(n - k))

def conditional_probability(p_a_and_b, p_b):
    return p_a_and_b / p_b

p_king_given_face = conditional_probability(4/52, 12/52)
print(f"P(King | Face card) = {p_king_given_face:.4f}")
```

### 단계 2: PMF와 PDF를 처음부터

```python
def bernoulli_pmf(k, p):
    return p if k == 1 else (1 - p)

def categorical_pmf(k, probs):
    return probs[k]

def poisson_pmf(k, lam):
    return (lam ** k) * math.exp(-lam) / factorial(k)

def uniform_pdf(x, a, b):
    if a <= x <= b:
        return 1.0 / (b - a)
    return 0.0

def normal_pdf(x, mu, sigma):
    coeff = 1.0 / (sigma * math.sqrt(2 * math.pi))
    exponent = -0.5 * ((x - mu) / sigma) ** 2
    return coeff * math.exp(exponent)
```

### 단계 3: 기댓값과 분산

```python
def expected_value(values, probabilities):
    return sum(v * p for v, p in zip(values, probabilities))

def variance(values, probabilities):
    mu = expected_value(values, probabilities)
    return sum(p * (v - mu) ** 2 for v, p in zip(values, probabilities))

die_values = [1, 2, 3, 4, 5, 6]
die_probs = [1/6] * 6
mu = expected_value(die_values, die_probs)
var = variance(die_values, die_probs)
print(f"Die: E[X] = {mu:.4f}, Var(X) = {var:.4f}, SD = {var**0.5:.4f}")
```

### 단계 4: 분포에서 샘플링하기

```python
def sample_bernoulli(p, n=1):
    return [1 if random.random() < p else 0 for _ in range(n)]

def sample_categorical(probs, n=1):
    cumulative = []
    total = 0
    for p in probs:
        total += p
        cumulative.append(total)
    samples = []
    for _ in range(n):
        r = random.random()
        for i, c in enumerate(cumulative):
            if r <= c:
                samples.append(i)
                break
    return samples

def sample_normal_box_muller(mu, sigma, n=1):
    samples = []
    for _ in range(n):
        u1 = random.random()
        u2 = random.random()
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        samples.append(mu + sigma * z)
    return samples
```

### 단계 5: 소프트맥스와 로그 확률

```python
def softmax(logits):
    max_logit = max(logits)
    shifted = [z - max_logit for z in logits]
    exps = [math.exp(z) for z in shifted]
    total = sum(exps)
    return [e / total for e in exps]

def log_softmax(logits):
    max_logit = max(logits)
    shifted = [z - max_logit for z in logits]
    log_sum_exp = max_logit + math.log(sum(math.exp(z) for z in shifted))
    return [z - log_sum_exp for z in logits]

def cross_entropy_loss(logits, target_index):
    log_probs = log_softmax(logits)
    return -log_probs[target_index]
```

### 단계 6: 중심극한정리 시연

```python
def demonstrate_clt(dist_fn, n_samples, n_averages):
    averages = []
    for _ in range(n_averages):
        samples = [dist_fn() for _ in range(n_samples)]
        averages.append(sum(samples) / len(samples))
    return averages
```

### 단계 7: 시각화

```python
import matplotlib.pyplot as plt

xs = [mu + sigma * (i - 500) / 100 for i in range(1001)]
ys = [normal_pdf(x, mu, sigma) for x, mu, sigma in ...]
plt.plot(xs, ys)
```

모든 시각화를 포함한 전체 구현은 `code/probability.py`에 있습니다.

## 실전에서 활용하기

NumPy와 SciPy를 쓰면 위의 모든 것이 한 줄짜리가 됩니다:

```python
import numpy as np
from scipy import stats

normal = stats.norm(loc=0, scale=1)
samples = normal.rvs(size=10000)
print(f"Mean: {np.mean(samples):.4f}, Std: {np.std(samples):.4f}")
print(f"P(X < 1.96) = {normal.cdf(1.96):.4f}")

logits = np.array([2.0, 1.0, 0.1])
from scipy.special import softmax, log_softmax
probs = softmax(logits)
log_probs = log_softmax(logits)
print(f"Softmax: {probs}")
print(f"Log-softmax: {log_probs}")
```

이걸 전부 직접 만들었습니다. 이제 라이브러리 호출이 무슨 일을 하는지 아는 셈이죠.

## 연습 문제

1. 지수 분포에 대한 역변환 샘플링을 구현하세요. 10,000개 값을 샘플링해 히스토그램을 진짜 PDF와 비교해 검증합니다.

2. 두 개의 조작된 주사위에 대한 결합 분포 표를 만드세요. 주변 분포를 계산하고 두 주사위가 독립인지 확인합니다.

3. 5클래스 분류기가 로짓 `[2.0, 0.5, -1.0, 3.0, 0.1]`을 출력하고 정답 클래스가 인덱스 3일 때의 교차 엔트로피 손실을 계산하세요. 그다음 PyTorch의 `nn.CrossEntropyLoss`로 답을 검증합니다.

4. 로그 확률 목록을 받아 가장 가능성 높은 시퀀스, 총 로그 확률, 그에 상응하는 원래 확률을 반환하는 함수를 작성하세요. 각 단어의 확률이 0.01인 50단어 문장으로 시험해 보세요.

## 핵심 용어

| 용어 | 사람들의 말 | 실제 의미 |
|------|----------------|----------------------|
| 표본 공간 | "가능성 전부" | 실험에서 가능한 모든 결과의 집합 S |
| PMF | "확률 함수" | 각 이산 결과의 정확한 확률을 알려 주고 합이 1이 되는 함수 |
| PDF | "확률 곡선" | 연속 변수용 밀도 함수. 구간에 걸쳐 적분해야 확률이 나옴 |
| 조건부 확률 | "~가 주어졌을 때의 확률" | P(A\|B) = P(A and B) / P(B). 베이지안 사고와 베이즈 정리의 토대 |
| 독립 | "서로 영향을 안 줌" | P(A and B) = P(A) * P(B). 한 사건을 알아도 다른 사건에 대해 아무것도 모름 |
| 기댓값 | "평균" | 모든 결과를 확률로 가중 합산한 값. 손실 함수도 기댓값임 |
| 분산 | "흩어진 정도" | 평균에서 벗어난 정도의 제곱 기댓값. 분산이 크다 = 시끄럽고 불안정한 추정 |
| 정규 분포 | "종 모양 곡선" | f(x) = (1/sqrt(2*pi*sigma^2)) * exp(-(x-mu)^2/(2*sigma^2)). CLT 덕분에 어디에나 등장 |
| 중심극한정리 | "평균은 정규가 된다" | 많은 독립 표본의 평균은 원래 분포와 무관하게 정규 분포로 수렴 |
| 결합 분포 | "두 변수를 함께" | P(X, Y)는 X와 Y 결과 조합 각각의 확률을 기술 |
| 주변 분포 | "다른 변수를 합쳐 없애기" | P(X) = sum_y P(X, Y). 결합에서 한 변수의 분포를 복원 |
| 로그 확률 | "확률의 로그" | log P(x). 곱셈을 덧셈으로 바꿔 긴 시퀀스에서의 수치 언더플로를 막음 |
| 소프트맥스 | "점수를 확률로" | softmax(z_i) = exp(z_i) / sum(exp(z_j)). 실수 로짓을 유효한 확률 분포로 매핑 |
| 교차 엔트로피 | "그 손실 함수" | -sum(p_true * log(p_predicted)). 두 분포의 차이를 측정. 낮을수록 좋음 |
| 로짓 | "모델의 날것 출력" | 소프트맥스 이전의 정규화되지 않은 점수. 로지스틱 함수에서 이름이 유래 |
| 샘플링 | "무작위 값 뽑기" | 확률 분포에 따라 값을 생성. 모델이 출력을 만들어 내는 방식 |

## 더 읽을거리

- [3Blue1Brown: But what is the Central Limit Theorem?](https://www.youtube.com/watch?v=zeJD6dqJ5lo) - 평균이 왜 정규가 되는지에 대한 시각적 증명
- [Stanford CS229 Probability Review](https://cs229.stanford.edu/section/cs229-prob.pdf) - 여기 내용 전부와 그 이상을 담은 간결한 레퍼런스
- [The Log-Sum-Exp Trick](https://gregorygundersen.com/blog/2020/02/09/log-sum-exp/) - 수치 안정성이 왜 중요하고 어떻게 달성하는지
