---
name: skill-probability-reasoning
description: 주어진 ML 문제에 맞는 확률 분포를 고릅니다
version: 1.0.0
phase: 1
lesson: 6
tags: [probability, distributions, modeling]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-probability-reasoning.md](skill-probability-reasoning.md)

# 확률 분포 선택

데이터를 모델링하거나, 손실 함수를 설계하거나, 사전 분포(prior)를 설정할 때 올바른 분포를 고르는 방법입니다.

## 결정 체크리스트

1. 결과가 이산형인가(범주, 개수) 아니면 연속형인가(측정값, 점수)?
2. 결과가 한정돼 있는가(예: [0, 1]) 아니면 무한한가?
3. 가능한 결과가 몇 개인가? 둘? k개? 무한?
4. 데이터가 대칭인가, 아니면 한쪽으로 치우쳤는가?
5. 사건들이 독립인가, 상관돼 있는가?
6. 발생률(rate), 개수(count), 비율(proportion), 측정값 중 무엇을 모델링하는가?

## 분포 결정 트리

```
변수가 이산형인가?
  예 --> 결과가 2개뿐인가? --> Bernoulli (p)
     |    k개의 결과, 시행 1회? --> Categorical (p1...pk)
     |    k개의 결과, 시행 n회? --> Multinomial (n, p1...pk)
     |    n번 시행 중 성공 횟수? --> Binomial (n, p)
     |    구간당 사건 횟수? --> Poisson (lambda)
     |    첫 성공까지의 시행 횟수? --> Geometric (p)
     |    r번 성공까지의 시행 횟수? --> Negative Binomial (r, p)
  아니오 --> 대칭, 종 모양? --> Normal (mu, sigma)
     |   양수이며 오른쪽으로 치우침? --> Log-normal 또는 Exponential
     |   [0, 1] 안에 한정됨? --> Beta (alpha, beta)
     |   양수이며 유연한 모양? --> Gamma (alpha, beta)
     |   사건 사이의 시간? --> Exponential (lambda)
     |   두꺼운 꼬리가 필요? --> Student's t (nu) 또는 Cauchy
     |   다변량, 종 모양? --> Multivariate Normal
     |   심플렉스 위(합이 1)? --> Dirichlet (alpha)
```

## 실제 ML 시나리오를 분포에 대응시키기

| 시나리오 | 분포 | 파라미터 |
|---|---|---|
| 이진 분류 출력 | Bernoulli | p = sigmoid(logit) |
| 다중 클래스 분류 출력 | Categorical | p = softmax(logits) |
| 언어 모델의 토큰 예측 | 어휘 전체에 걸친 Categorical | p = softmax 결과 |
| 픽셀 강도 (정규화됨) | Beta 또는 Uniform [0, 1] | 이미지 통계에 따라 다름 |
| 문서의 단어 수 | Poisson | lambda = 평균 단어 수 |
| 사용자 요청 사이의 시간 | Exponential | lambda = 요청 발생률 |
| 측정 오차 | Normal | mu = 0, sigma는 데이터에서 추정 |
| 가중치 초기화 | Normal 또는 Uniform | Kaiming/Xavier 규칙 |
| VAE 잠재 공간 사전 분포 | 표준 정규 | mu = 0, sigma = 1 |
| 비율에 대한 베이지안 사전 분포 | Beta | 믿음에 따라 alpha, beta |
| 범주 가중치에 대한 베이지안 사전 분포 | Dirichlet | alpha 벡터 |
| 회귀 타깃의 노이즈 | Normal | mu = 0, 추정된 sigma |
| 이상치에 강건한 회귀 | Student's t | 낮은 자유도 |
| 지속 시간/수명 모델링 | Weibull 또는 Gamma | 모양(shape)과 척도(scale) |
| 문서별 토픽 분포 (LDA) | Dirichlet | 희소하게는 alpha < 1 |

## 분포가 잘못 쓰이는 경우

- 데이터에 단단한 하한이 있는데(예: 가격, 거리) Normal을 쓰는 경우. 정규 분포는 음수에도 0이 아닌 확률을 부여합니다. 대신 log-normal이나 gamma를 사용하세요.
- 분산이 평균과 다른데 Poisson을 쓰는 경우. Poisson은 평균 = 분산을 가정합니다. 분산 > 평균이면 negative binomial을 사용하세요.
- 다중 클래스 문제에 Bernoulli를 쓰는 경우. Bernoulli는 엄격하게 이진입니다. k > 2면 categorical을 사용하세요.
- 관측치가 상관돼 있는데 독립을 가정하는 경우. 시계열, 공간 데이터, 그룹화된 데이터는 독립을 위반합니다. 자기회귀(autoregressive)나 계층적 모델을 사용하세요.

## 흔한 실수

- PDF 값을 확률과 혼동하기. PDF는 1을 넘을 수 있습니다. 확률은 PDF를 구간에 걸쳐 적분해야 나옵니다.
- 소프트맥스 출력을 독립적인 Bernoulli 확률이 아니라 범주형 확률로 다뤄야 한다는 점을 잊기. 소프트맥스 출력은 구조상 합이 1입니다.
- 도메인 지식이 있는데도 균등 사전 분포를 쓰는 경우. 잘 고른 유익한 사전 분포는 결과를 편향시키지 않으면서 분산을 줄여 줍니다.
- 로그 확률을 확률처럼 다루기. 로그 확률은 항상 음수(또는 0)이며, 합이 1이 되지 않습니다.

## 빠른 참조: 분포 성질

| 분포 | 지지집합 | 평균 | 분산 | 핵심 성질 |
|---|---|---|---|---|
| Bernoulli(p) | {0, 1} | p | p(1-p) | 가장 단순한 이산 분포 |
| Binomial(n, p) | {0..n} | np | np(1-p) | Bernoulli n개의 합 |
| Poisson(lam) | {0, 1, 2, ...} | lam | lam | 평균 = 분산 |
| Normal(mu, s^2) | (-inf, inf) | mu | s^2 | 주어진 평균/분산에서 최대 엔트로피 |
| Exponential(lam) | [0, inf) | 1/lam | 1/lam^2 | 무기억성(memoryless) |
| Beta(a, b) | [0, 1] | a/(a+b) | ab/((a+b)^2(a+b+1)) | Binomial의 켤레(conjugate) |
| Gamma(a, b) | (0, inf) | a/b | a/b^2 | Poisson의 켤레(conjugate) |
| Dirichlet(alpha) | 심플렉스 | alpha_i/sum | (공식 참조) | Categorical의 켤레(conjugate) |
