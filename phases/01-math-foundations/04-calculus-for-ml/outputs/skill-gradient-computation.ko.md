---
name: skill-gradient-computation
description: 흔한 ML 손실 함수의 그래디언트를 계산하고 올바른 미분 접근법을 고릅니다
version: 1.0.0
phase: 1
lesson: 4
tags: [calculus, gradients, backpropagation]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-gradient-computation.md](skill-gradient-computation.md)

# ML을 위한 그래디언트 계산

신경망에 쓰이는 손실 함수, 활성화 함수, 레이어 연산의 그래디언트를 계산하는 실전 레퍼런스입니다.

## 결정 체크리스트

1. 함수가 간단한 기본 요소(거듭제곱, exp, log, 삼각 함수)의 합성인가? 해석적 도함수와 연쇄 법칙을 사용한다.
2. 함수가 커스텀이거나 블랙박스 연산인가? 수치 미분을 사용한다: `(f(x+h) - f(x-h)) / (2h)`, h = 1e-7.
3. 함수가 PyTorch/JAX의 텐서 연산으로 구성돼 있는가? autograd에 맡긴다. 수치 검산으로 확인한다.
4. 스칼라 손실을 가중치 행렬에 대해 미분해야 하는가? 계산 그래프를 따라 노드 하나씩 연쇄 법칙을 적용한다.
5. 미분 불가능한 연산(argmax, 반올림, 샘플링)이 있는가? straight-through 추정량이나 재매개변화 트릭(reparameterization trick)을 사용한다.

## 접근법별 사용 시점

| 접근법 | 사용 시점 | 비용 |
|---|---|---|
| 해석적 (손으로 유도) | 간단한 함수, autograd 결과 검증 | 실행 시점에 공짜 |
| 수치적 (유한 차분) | 디버깅, 그래디언트 검산, 블랙박스 함수 | 파라미터 n개에 순전파 2n회 |
| 자동 미분 | 미분 가능한 모든 계산 그래프 (기본 선택) | 역방향 패스 한 번 |
| 심볼릭 (SymPy, Mathematica) | 논문용 폐형(closed-form) 그래디언트 유도 | 컴파일 시간만 소요 |

## 빠른 참조: 자주 쓰는 도함수

| 함수 | f(x) | f'(x) | ML 맥락 |
|---|---|---|---|
| MSE 손실 | (1/n) sum(y_hat - y)^2 | (2/n)(y_hat - y) | 회귀 |
| 교차 엔트로피 (이진) | -(y log(p) + (1-y) log(1-p)) | p - y (시그모이드 이후) | 이진 분류 |
| 교차 엔트로피 (다중) | -log(p_true_class) | p - one_hot(y) (소프트맥스 이후) | 다중 클래스 분류 |
| Sigmoid | 1 / (1 + e^(-x)) | sigma(x) * (1 - sigma(x)) | 출력 게이트, 이진 출력 |
| Tanh | (e^x - e^(-x)) / (e^x + e^(-x)) | 1 - tanh(x)^2 | 은닉 활성화 (구식) |
| ReLU | max(0, x) | x > 0이면 1, x < 0이면 0 | 기본 은닉 활성화 |
| Leaky ReLU | max(0.01x, x) | x > 0이면 1, x < 0이면 0.01 | 죽은 뉴런 방지 |
| GELU | x * Phi(x) | Phi(x) + x * phi(x) | 트랜스포머 |
| Softmax_i | e^(x_i) / sum(e^(x_j)) | i=j면 s_i(1 - s_i), i!=j면 -s_i*s_j | 출력 레이어 (야코비안) |
| Log-softmax | x_i - log(sum(e^(x_j))) | i번째 항목은 1 - softmax(x_i) | 수치적으로 안정한 CE |
| 선형 레이어 | y = Wx + b | dL/dW = dL/dy * x^T, dL/db = dL/dy | 모든 레이어 |
| L2 정규화 | lambda * sum(w^2) | 2 * lambda * w | 가중치 감쇠(weight decay) |
| L1 정규화 | lambda * sum(\|w\|) | lambda * sign(w) | 희소성 |

## 흔한 실수

- 배치 평균 손실(MSE, 교차 엔트로피)에서 1/n 인수를 빼먹기. 그래디언트는 배치 크기에 비례해 스케일됩니다.
- 소프트맥스 그래디언트를 벡터로 계산하기. 실제로는 야코비안 행렬입니다. 교차 엔트로피 + 소프트맥스를 합치면 그래디언트가 (p - y)로 단순화되어 전체 야코비안을 피할 수 있습니다.
- 연쇄 법칙을 잘못된 순서로 적용하기. 손실에서 거꾸로 작업합니다: dL/dW = dL/dy * dy/dW.
- 수치 미분에서 h가 너무 크거나(h = 0.1) 너무 작은 경우(h = 1e-15). float64에서는 h = 1e-7을 고수하세요.
- ReLU는 정확히 x = 0에서 그래디언트가 정의되지 않는다는 점을 잊기. 실전에서는 0 또는 0.5로 둡니다.

## 그래디언트 검산 레시피

```
각 파라미터 w에 대해:
  numeric_grad = (loss(w + h) - loss(w - h)) / (2h)
  auto_grad = 역방향 패스 값
  relative_error = |numeric - auto| / max(|numeric|, |auto|, 1e-8)
  assert relative_error < 1e-5
```

상대 오차가 1e-3을 넘으면 뭔가 잘못된 것입니다. 1e-5와 1e-3 사이면 조사해 보세요.
