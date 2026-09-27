> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 수치 안정성(Numerical Stability)

> 부동소수점은 새는 추상화입니다. 학습 도중에 반드시 여러분을 물어 뜯을 텐데, 정작 여러분은 그것이 오는 줄도 모릅니다.

**유형:** Build(직접 만들기)
**언어:** Python
**선수 지식:** 페이즈 1, 레슨 01-04
**시간:** 약 120분

## 학습 목표

- 최댓값 빼기 트릭(max-subtraction trick)으로 수치적으로 안정한 softmax와 log-sum-exp를 구현하기
- 부동소수점 계산에서 오버플로, 언더플로, 심각한 자릿수 상쇄(catastrophic cancellation)를 식별하기
- 중앙 차분(centered finite difference)으로 해석적 그래디언트를 수치 그래디언트와 비교해 검증하기
- 학습에는 float16보다 bfloat16이 선호되는 이유와, loss scaling이 그래디언트 언더플로를 막는 원리를 설명하기

## 문제 상황

모델이 세 시간째 학습하다가 손실이 NaN이 됩니다. print 문을 넣어 봅니다. 스텝 9,000에서 logits는 멀쩡합니다. 스텝 9,001에서는 `inf`가 됩니다. 스텝 9,002에는 모든 그래디언트가 `nan`이고 학습은 끝장입니다.

혹은 이렇습니다. 모델은 끝까지 학습했는데 정확도가 논문 주장보다 2% 낮습니다. 모든 걸 확인해 봅니다. 아키텍처도 같고, 하이퍼파라미터도 같고, 데이터도 같습니다. 문제는 논문은 float32를 썼는데 여러분은 float16을 적절한 스케일링 없이 썼다는 점입니다. 쌓인 반올림 오차가 조용히 정확도를 갉아먹은 겁니다.

또는 이렇습니다. 크로스엔트로피 손실을 직접 구현했습니다. logits가 작을 때는 잘 동작합니다. logits가 100을 넘으면 `inf`를 돌려줍니다. `exp(100)`이 float32가 표현할 수 있는 크기를 넘어서 softmax가 오버플로한 겁니다. 모든 ML 프레임워크는 두 줄짜리 트릭으로 이를 처리합니다. 그런데 여러분은 그 트릭이 존재하는지 몰랐던 거죠.

수치 안정성은 이론적인 문제가 아닙니다. 성공하는 학습과 조용히 실패하는 학습을 가르는 차이입니다. 결국 여러분이 디버깅하게 될 심각한 ML 버그는 모두 부동소수점으로 귀결됩니다.

## 핵심 개념

### IEEE 754: 컴퓨터가 실수를 저장하는 방식

컴퓨터는 IEEE 754 표준에 따라 실수를 부동소수점 값으로 저장합니다. float는 부호 비트, 지수(exponent), 가수(mantissa, significand)의 세 부분으로 이루어집니다.

```
Float32 레이아웃(총 32비트):
[부호 1비트] [지수 8비트] [가수 23비트]

값 = (-1)^sign * 2^(exponent - 127) * 1.mantissa
```

가수는 정밀도(유효 숫자가 몇 자리인지)를 결정합니다. 지수는 범위(얼마나 크고 작은 수를 담을 수 있는지)를 결정합니다.

```
포맷      비트   지수      가수      십진 자릿수       범위(근사)
float64    64     11        52        ~15-16          +/- 1.8e308
float32    32     8         23        ~7-8            +/- 3.4e38
float16    16     5         10        ~3-4            +/- 65,504
bfloat16   16     8         7         ~2-3            +/- 3.4e38
```

float32는 십진수 약 7자리의 정밀도를 줍니다. 즉 1.0000001과 1.0000002는 구별하지만, 1.00000001과 1.00000002는 구별하지 못합니다. 7자리를 넘어가면 전부 반올림 잡음입니다.

float16은 약 3자리를 줍니다. 표현할 수 있는 가장 큰 수는 65,504입니다. logits, 그래디언트, 활성값이 일상적으로 이 값을 넘는 ML 세계에서는 불안할 정도로 작은 숫자죠.

bfloat16은 float16의 범위 문제에 대한 Google의 해답입니다. float32와 같은 8비트 지수(최대 3.4e38까지 같은 범위)를 갖지만 가수는 겨우 7비트(float16보다 정밀도가 낮음)입니다. 신경망 학습에서는 정밀도보다 범위가 더 중요하기 때문에 보통은 bfloat16이 이깁니다.

### 0.1 + 0.2 != 0.3인 이유

0.1이라는 수는 2진 부동소수점으로 정확히 표현할 수 없습니다. 2진법에서는 무한반복 소수입니다:

```
2진법에서 0.1 = 0.0001100110011001100110011... (영원히 반복)
```

float32는 이를 가수 23비트로 잘라 냅니다. 저장된 값은 약 0.100000001490116입니다. 마찬가지로 0.2는 약 0.200000002980232로 저장됩니다. 둘의 합은 0.300000004470348이지 0.3이 아닙니다.

```
Python에서:
>>> 0.1 + 0.2
0.30000000000000004

>>> 0.1 + 0.2 == 0.3
False
```

ML에서 문제가 되는 이유는 다음과 같습니다:

1. `if loss < threshold` 같은 손실 비교가 잘못된 답을 줄 수 있습니다
2. 작은 값들을 계속 누적하면(수천 스텝에 걸친 그래디언트 업데이트) 진짜 합에서 점점 어긋납니다
3. float를 `==`로 비교하면 체크섬이나 재현성 테스트가 실패합니다

해결책: float를 `==`로 절대 비교하지 마세요. `abs(a - b) < epsilon`이나 `math.isclose()`를 사용하세요.

### 심각한 자릿수 상쇄(Catastrophic Cancellation)

거의 같은 부동소수점 수 두 개를 빼면 유효 숫자들이 서로 상쇄되고, 반올림 잡음이 앞자리로 올라온 채 남습니다.

```
a = 1.0000001    (float32에서는 1.00000011920929로 저장됨)
b = 1.0000000    (float32에서는 1.00000000000000로 저장됨)

실제 차이:  0.0000001
계산 결과:         0.00000011920929

상대 오차: 19.2%
```

뺄셈 한 번으로 19%의 상대 오차가 나옵니다. ML에서는 다음 경우에 이런 일이 벌어집니다:

- 평균이 큰 데이터의 분산을 계산할 때: E[x]가 큰 상태에서 `E[x^2] - E[x]^2`
- 거의 같은 로그 확률을 뺄 때
- 너무 작은 epsilon으로 유한 차분 그래디언트를 계산할 때

해결책: 식을 다시 배열해서 크고 거의 같은 수의 뺄셈을 피합니다. 분산은 Welford 알고리즘을 쓰거나 데이터를 먼저 중심화하세요. 로그 확률은 처음부터 끝까지 로그 공간에서 계산하세요.

### 오버플로와 언더플로

오버플로는 결과가 너무 커서 표현할 수 없을 때 생깁니다. 언더플로는 결과가 너무 작아서(표현 가능한 가장 작은 양수보다 0에 가까울 때) 생깁니다.

```
float32 경계:
  최댓값:                   3.4028235e+38
  최소 양수(정규수):      1.175e-38
  최소 양수(비정규수):    1.401e-45
  오버플로:  3.4e38보다 큰 값은 inf가 됨
  언더플로: 1.4e-45보다 작은 값은 0.0이 됨
```

`exp()` 함수는 ML에서 오버플로의 주범입니다:

```
exp(88.7)  = 3.40e+38   (float32에 간신히 들어감)
exp(89.0)  = inf         (오버플로)
exp(-87.3) = 1.18e-38   (언더플로 바로 위)
exp(-104)  = 0.0         (0으로 언더플로)
```

`log()` 함수는 반대 방향으로 문제를 일으킵니다:

```
log(0.0)   = -inf
log(-1.0)  = nan
log(1e-45) = -103.3      (괜찮음)
log(1e-46) = -inf        (입력이 0으로 언더플로한 뒤 log(0) = -inf)
```

ML에서 `exp()`는 softmax, sigmoid, 확률 계산에 등장합니다. `log()`는 크로스엔트로피, 로그 가능도, KL 발산에 등장합니다. `log(exp(x))` 조합은 올바른 트릭 없이는 지뢰밭입니다.

### log-sum-exp 트릭

`log(sum(exp(x_i)))`를 직접 계산하는 것은 수치적으로 위험합니다. `x_i` 중 하나라도 크면 `exp(x_i)`가 오버플로합니다. `x_i`가 모두 아주 큰 음수이면 모든 `exp(x_i)`가 0으로 언더플로하고 `log(0)`은 `-inf`가 됩니다.

트릭: 지수화하기 전에 최댓값을 빼는 것입니다.

```
log(sum(exp(x_i))) = max(x) + log(sum(exp(x_i - max(x))))
```

왜 이게 통하나: `max(x)`를 빼고 나면 가장 큰 지수는 `exp(0) = 1`입니다. 오버플로는 불가능합니다. 또 합계에 최소한 하나의 항은 1이므로 합계는 최소 1이고, `log(1) = 0`입니다. `-inf`로 언더플로하는 일도 불가능합니다.

증명:

```
log(sum(exp(x_i)))
= log(sum(exp(x_i - c + c)))                    (c를 더하고 뺌)
= log(sum(exp(x_i - c) * exp(c)))               (exp(a+b) = exp(a)*exp(b))
= log(exp(c) * sum(exp(x_i - c)))               (exp(c)로 묶어냄)
= c + log(sum(exp(x_i - c)))                    (log(a*b) = log(a) + log(b))
```

`c = max(x)`로 두면 오버플로가 사라집니다.

이 트릭은 ML 곳곳에 등장합니다:
- softmax 정규화
- 크로스엔트로피 손실 계산
- 시퀀스 모델의 로그 확률 합산
- 가우시안 혼합 모델
- 변분 추론(variational inference)

### softmax에 최댓값 빼기 트릭이 필요한 이유

softmax는 logits를 확률로 바꿉니다:

```
softmax(x_i) = exp(x_i) / sum(exp(x_j))
```

트릭 없이는 [100, 101, 102] 같은 logits가 오버플로를 일으킵니다:

```
exp(100) = 2.69e43
exp(101) = 7.31e43
exp(102) = 1.99e44
합계      = 2.99e44

이 값들이 float32(최대 약 3.4e38)를 넘을까? 잠깐, 2.69e43 < 3.4e38? 실제로는:
exp(88.7)만 돼도 이미 float32 한계선이다.
float32에서 exp(100) = inf다.
```

트릭을 쓰면 max(x) = 102를 뺍니다:

```
exp(100 - 102) = exp(-2) = 0.135
exp(101 - 102) = exp(-1) = 0.368
exp(102 - 102) = exp(0)  = 1.000
합계 = 1.503

softmax = [0.090, 0.245, 0.665]
```

확률 값은 완전히 동일합니다. 계산은 안전해집니다. 이건 최적화가 아니라 정확성을 위한 필수 사항입니다.

### NaN과 Inf: 감지와 예방

`nan`(Not a Number)과 `inf`(무한대)는 계산을 통해 바이러스처럼 퍼집니다. 그래디언트 업데이트에 `nan` 하나가 섞이면 가중치가 `nan`이 되고, 이어지는 모든 출력이 `nan`이 됩니다. 학습은 한 스텝 만에 죽습니다.

`inf`가 생기는 경우:
- 큰 양수에 대한 `exp()`
- 0으로 나누기: `1.0 / 0.0`
- 누적 과정에서의 `float32` 오버플로

`nan`이 생기는 경우:
- `0.0 / 0.0`
- `inf - inf`
- `inf * 0`
- 음수의 `sqrt()`
- 음수의 `log()`
- 이미 있는 `nan`이 관여하는 모든 산술 연산

감지:

```python
import math

math.isnan(x)       # x가 nan이면 True
math.isinf(x)       # x가 +inf 또는 -inf면 True
math.isfinite(x)    # x가 nan도 inf도 아니면 True
```

예방 전략:

1. `exp()` 입력을 잘라내기(clamp): `exp(clamp(x, -80, 80))`
2. 분모에 epsilon 더하기: `x / (y + 1e-8)`
3. `log()` 안에 epsilon 더하기: `log(x + 1e-8)`
4. 안정한 구현 사용하기(log-sum-exp, 안정 softmax)
5. 가중치 폭발을 막는 그래디언트 클리핑(gradient clipping)
6. 디버깅 중에는 포워드 패스마다 `nan`/`inf` 확인하기

### 수치 그래디언트 검증(gradient checking)

해석적 그래디언트(역전파로 계산한 것)에는 버그가 있을 수 있습니다. 수치 그래디언트 검증은 유한 차분으로 그래디언트를 계산해서 이를 확인해 줍니다.

중앙 차분 공식:

```
df/dx ~= (f(x + h) - f(x - h)) / (2h)
```

이 방식은 정확도가 O(h^2)로, O(h)에 불과한 전진 차분 `(f(x+h) - f(x)) / h`보다 훨씬 좋습니다.

h 고르기: 너무 크면 근사가 틀립니다. 너무 작으면 자릿수 상쇄 때문에 답이 망가집니다. `h = 1e-5`에서 `1e-7` 정도가 일반적입니다.

검증 방법: 해석적 그래디언트와 수치 그래디언트의 상대 차이를 계산합니다.

```
relative_error = |grad_analytical - grad_numerical| / max(|grad_analytical|, |grad_numerical|, 1e-8)
```

경험 법칙:
- relative_error < 1e-7: 완벽합니다. 그래디언트가 올바름
- relative_error < 1e-5: 허용 가능. 아마 올바름
- relative_error > 1e-3: 뭔가 잘못됨
- relative_error > 1: 그래디언트가 완전히 틀림

새 레이어나 손실 함수를 구현할 때는 항상 그래디언트를 검증하세요. PyTorch는 이를 위해 `torch.autograd.gradcheck()`를 제공합니다.

### 혼합 정밀도(mixed precision) 학습

현대 GPU에는 float16 행렬 곱셈을 float32보다 2-8배 빠르게 계산하는 전용 하드웨어(Tensor Core)가 있습니다. 혼합 정밀도 학습은 이를 활용합니다:

```
1. float32 마스터 가중치 사본을 유지한다
2. float16으로 포워드 패스를 돌린다 (빠름)
3. float32로 손실을 계산한다 (오버플로 방지)
4. float16으로 백워드 패스를 돌린다 (빠름)
5. 그래디언트를 float32로 스케일링한다
6. float32 마스터 가중치를 업데이트한다
```

순수 float16 학습의 문제: 그래디언트는 종종 아주 작습니다(1e-8 이하). float16은 약 6e-8보다 작은 값은 모두 0으로 언더플로시킵니다. 그래디언트 업데이트가 전부 0이라서 모델은 더 이상 학습하지 못합니다.

해결책은 loss scaling입니다:

```
1. 손실에 큰 스케일 인수를 곱한다 (예: 1024)
2. 백워드 패스는 (loss * 1024)의 그래디언트를 계산한다
3. 모든 그래디언트가 1024배 커진다 (float16 언더플로 선 위로 밀어 올림)
4. 가중치를 업데이트하기 전에 그래디언트를 1024로 나눈다
5. 순 효과: 업데이트는 동일한데 언더플로는 없다
```

동적 loss scaling은 스케일 인수를 자동으로 조정합니다. 큰 값(65536)으로 시작하고, 그래디언트가 `inf`로 오버플로하면 절반으로 줄입니다. 오버플로 없이 N스텝이 지나면 두 배로 늘립니다.

### bfloat16 vs float16: 학습에서 bfloat16이 이기는 이유

```
float16:   [부호 1] [지수 5]  [가수 10]
bfloat16:  [부호 1] [지수 8]  [가수 7]
```

float16은 정밀도가 더 높지만(가수 10비트 vs 7비트) 범위가 제한적입니다(최대 약 65,504). bfloat16은 정밀도는 낮지만 float32와 같은 범위(최대 약 3.4e38)를 갖습니다.

신경망 학습에서는:

- 학습 스파이크가 오면 활성값과 logits가 65,504를 넘기 일쑤입니다. float16은 오버플로하고, bfloat16은 견딥니다.
- float16에서는 loss scaling이 필수지만, bfloat16은 범위가 그래디언트 크기 스펙트럼 전체를 커버하므로 보통 필요 없습니다.
- bfloat16은 float32를 단순히 잘라낸 것입니다. 가수의 아래 16비트를 버리면 됩니다. 변환은 아주 쉽고 지수 부분은 손실이 없습니다.

값이 범위 안에 있고 정밀도가 더 중요한 추론에는 float16이 적합합니다. 범위가 더 중요한 학습에는 bfloat16이 적합합니다. 그래서 TPU와 최신 NVIDIA GPU(A100, H100)가 bfloat16을 기본으로 지원하는 것입니다.

### 그래디언트 클리핑

그래디언트 폭발은 그래디언트가 여러 레이어를 거치며 지수적으로 커질 때 생깁니다(RNN, 깊은 네트워크, 트랜스포머에서 흔함). 그래디언트 하나가 크게 튀면 스텝 한 번에 모든 가중치가 망가질 수 있습니다.

클리핑 방식은 두 가지입니다:

**값 기반 클리핑:** 각 그래디언트 원소를 독립적으로 clamp합니다.

```
grad = clamp(grad, -max_val, max_val)
```

간단하지만 그래디언트 벡터의 방향을 바꿔 버릴 수 있습니다.

**노름(norm) 기반 클리핑:** 그래디언트 벡터 전체의 노름이 임계값을 넘지 않도록 스케일을 조정합니다.

```
if ||grad|| > max_norm:
    grad = grad * (max_norm / ||grad||)
```

그래디언트의 방향을 보존합니다. `torch.nn.utils.clip_grad_norm_()`이 하는 일이 바로 이것이며, 표준적인 선택입니다.

일반적인 값: 트랜스포머는 `max_norm=1.0`, RL은 `max_norm=0.5`, 더 단순한 네트워크는 `max_norm=5.0`.

그래디언트 클리핑은 임시방편이 아닙니다. 안전 장치입니다. 이것이 없으면 이상치 배치 하나가 몇 주 치 학습을 망가뜨릴 만큼 큰 그래디언트를 만들어 낼 수 있습니다.

### 수치 안정 장치로서의 정규화 레이어

배치 정규화, 레이어 정규화, RMS 정규화는 보통 학습 수렴을 돕는 정규화 기법으로 소개됩니다. 하지만 이들은 수치 안정 장치이기도 합니다.

정규화가 없으면 활성값이 레이어를 거치며 지수적으로 커지거나 작아질 수 있습니다:

```
레이어 1: 값이 [0, 1]
레이어 5: 값이 [0, 100]
레이어 10: 값이 [0, 10,000]
레이어 50: 값이 [0, inf]
```

정규화는 모든 레이어에서 활성값을 다시 중심화하고 다시 스케일링합니다:

```
LayerNorm(x) = (x - mean(x)) / (std(x) + epsilon) * gamma + beta
```

`epsilon`(보통 1e-5)은 모든 활성값이 동일할 때 0으로 나누는 것을 막아 줍니다. 학습되는 파라미터 `gamma`와 `beta`는 네트워크가 필요한 스케일을 스스로 되찾게 해 줍니다.

덕분에 값이 네트워크 전체에서 수치적으로 안전한 범위 안에 머물러, 포워드 패스의 오버플로와 백워드 패스의 그래디언트 폭발을 모두 막아 줍니다.

### ML에서 흔한 수치 버그

**버그: 몇 에포크 후 손실이 NaN이 된다.**
원인: logits가 너무 커져 softmax가 오버플로했다. 또는 학습률이 너무 높아 가중치가 발산했다.
해결: 안정한 softmax(최댓값 빼기)를 쓰고, 학습률을 낮추고, 그래디언트 클리핑을 추가한다.

**버그: 손실이 log(num_classes)에 머물러 있다.**
원인: 모델 출력이 거의 균등한 확률이다. 그래디언트가 사라지고 있거나 모델이 전혀 학습하지 않고 있을 때가 많다.
해결: 데이터 레이블이 올바른지 확인하고, 손실 함수를 검증하고, 죽은 ReLU가 있는지 확인한다.

**버그: 검증 정확도가 기대보다 1-3% 낮다.**
원인: 적절한 loss scaling 없이 혼합 정밀도를 사용했다. 그래디언트 언더플로가 작은 업데이트를 조용히 0으로 만든다.
해결: 동적 loss scaling을 켜거나 bfloat16으로 전환한다.

**버그: 일부 레이어의 그래디언트 노름이 0.0이다.**
원인: 죽은 ReLU 뉴런(입력이 모두 음수) 또는 float16 언더플로.
해결: LeakyReLU나 GELU를 쓰고, 그래디언트 스케일링을 적용하고, 가중치 초기화를 점검한다.

**버그: 한 GPU에서는 되는데 다른 GPU에서는 결과가 다르다.**
원인: 비결정적인 부동소수점 누적 순서. GPU 병렬 reduction은 하드웨어마다 다른 순서로 합산하고, 부동소수점 덧셈은 결합법칙이 성립하지 않는다.
해결: 작은 차이(1e-6)는 받아들이거나, `torch.use_deterministic_algorithms(True)`를 설정하고 속도 저하를 감수한다.

**버그: 손실 계산에서 `exp()`가 `inf`를 반환한다.**
원인: 최댓값 빼기 트릭 없이 원본 logits가 `exp()`로 전달됐다.
해결: log-sum-exp를 내부적으로 구현한 `torch.nn.functional.log_softmax()`를 사용한다.

**버그: float32에서 float16으로 바꾼 뒤 학습이 발산한다.**
원인: float16은 6e-8보다 작은 그래디언트 크기나 65,504보다 큰 활성값을 표현할 수 없다.
해결: loss scaling이 있는 혼합 정밀도(AMP)를 쓰거나 bfloat16으로 대체한다.

```figure
logsumexp-stability
```

## 직접 만들기

### 단계 1: 부동소수점 정밀도 한계 확인하기

```python
print("=== Floating Point Precision ===")
print(f"0.1 + 0.2 = {0.1 + 0.2}")
print(f"0.1 + 0.2 == 0.3? {0.1 + 0.2 == 0.3}")
print(f"Difference: {(0.1 + 0.2) - 0.3:.2e}")
```

### 단계 2: 순진한 softmax vs 안정한 softmax 구현하기

```python
import math

def softmax_naive(logits):
    exps = [math.exp(z) for z in logits]
    total = sum(exps)
    return [e / total for e in exps]

def softmax_stable(logits):
    max_logit = max(logits)
    exps = [math.exp(z - max_logit) for z in logits]
    total = sum(exps)
    return [e / total for e in exps]

safe_logits = [2.0, 1.0, 0.1]
print(f"Naive:  {softmax_naive(safe_logits)}")
print(f"Stable: {softmax_stable(safe_logits)}")

dangerous_logits = [100.0, 101.0, 102.0]
print(f"Stable: {softmax_stable(dangerous_logits)}")
# softmax_naive(dangerous_logits)는 [nan, nan, nan]을 반환함
```

### 단계 3: 안정한 log-sum-exp 구현하기

```python
def logsumexp_naive(values):
    return math.log(sum(math.exp(v) for v in values))

def logsumexp_stable(values):
    c = max(values)
    return c + math.log(sum(math.exp(v - c) for v in values))

safe = [1.0, 2.0, 3.0]
print(f"Naive:  {logsumexp_naive(safe):.6f}")
print(f"Stable: {logsumexp_stable(safe):.6f}")

large = [500.0, 501.0, 502.0]
print(f"Stable: {logsumexp_stable(large):.6f}")
# logsumexp_naive(large)는 inf를 반환함
```

### 단계 4: 안정한 크로스엔트로피 구현하기

```python
def cross_entropy_naive(true_class, logits):
    probs = softmax_naive(logits)
    return -math.log(probs[true_class])

def cross_entropy_stable(true_class, logits):
    max_logit = max(logits)
    shifted = [z - max_logit for z in logits]
    log_sum_exp = math.log(sum(math.exp(s) for s in shifted))
    log_prob = shifted[true_class] - log_sum_exp
    return -log_prob

logits = [2.0, 5.0, 1.0]
true_class = 1
print(f"Naive:  {cross_entropy_naive(true_class, logits):.6f}")
print(f"Stable: {cross_entropy_stable(true_class, logits):.6f}")
```

### 단계 5: 그래디언트 검증

```python
def numerical_gradient(f, x, h=1e-5):
    grad = []
    for i in range(len(x)):
        x_plus = x[:]
        x_minus = x[:]
        x_plus[i] += h
        x_minus[i] -= h
        grad.append((f(x_plus) - f(x_minus)) / (2 * h))
    return grad

def check_gradient(analytical, numerical, tolerance=1e-5):
    for i, (a, n) in enumerate(zip(analytical, numerical)):
        denom = max(abs(a), abs(n), 1e-8)
        rel_error = abs(a - n) / denom
        status = "OK" if rel_error < tolerance else "FAIL"
        print(f"  param {i}: analytical={a:.8f} numerical={n:.8f} "
              f"rel_error={rel_error:.2e} [{status}]")

def f(params):
    x, y = params
    return x**2 + 3*x*y + y**3

def f_grad(params):
    x, y = params
    return [2*x + 3*y, 3*x + 3*y**2]

point = [2.0, 1.0]
analytical = f_grad(point)
numerical = numerical_gradient(f, point)
check_gradient(analytical, numerical)
```

## 활용하기

### 혼합 정밀도 시뮬레이션

```python
import struct

def float32_to_float16_round(x):
    packed = struct.pack('f', x)
    f32 = struct.unpack('f', packed)[0]
    packed16 = struct.pack('e', f32)
    return struct.unpack('e', packed16)[0]

def simulate_bfloat16(x):
    packed = struct.pack('f', x)
    as_int = int.from_bytes(packed, 'little')
    truncated = as_int & 0xFFFF0000
    repacked = truncated.to_bytes(4, 'little')
    return struct.unpack('f', repacked)[0]
```

### 그래디언트 클리핑

```python
def clip_by_norm(gradients, max_norm):
    total_norm = math.sqrt(sum(g**2 for g in gradients))
    if total_norm > max_norm:
        scale = max_norm / total_norm
        return [g * scale for g in gradients]
    return gradients

grads = [10.0, 20.0, 30.0]
clipped = clip_by_norm(grads, max_norm=5.0)
print(f"Original norm: {math.sqrt(sum(g**2 for g in grads)):.2f}")
print(f"Clipped norm:  {math.sqrt(sum(g**2 for g in clipped)):.2f}")
print(f"Direction preserved: {[c/clipped[0] for c in clipped]} == {[g/grads[0] for g in grads]}")
```

### NaN/Inf 감지

```python
def check_tensor(name, values):
    has_nan = any(math.isnan(v) for v in values)
    has_inf = any(math.isinf(v) for v in values)
    if has_nan or has_inf:
        print(f"WARNING {name}: nan={has_nan} inf={has_inf}")
        return False
    return True

check_tensor("good", [1.0, 2.0, 3.0])
check_tensor("bad",  [1.0, float('nan'), 3.0])
check_tensor("ugly", [1.0, float('inf'), 3.0])
```

모든 엣지 케이스를 보여 주는 전체 구현은 `code/numerical.py`에 있습니다.

## 출시하기

이 레슨의 산출물:
- 안정한 softmax, log-sum-exp, 크로스엔트로피, 그래디언트 검증, 혼합 정밀도 시뮬레이션이 들어 있는 `code/numerical.py`
- 학습 중 NaN/Inf와 수치 문제를 진단하는 `outputs/prompt-numerical-debugger.md`

이 안정한 구현들은 페이즈 3에서 학습 루프를 만들 때, 페이즈 4에서 어텐션 메커니즘을 구현할 때 다시 등장합니다.

## 연습 문제

1. **자릿수 상쇄.** [1000000.0, 1000001.0, 1000002.0]의 분산을 float32로 순진한 공식 `E[x^2] - E[x]^2`을 써서 계산해 보세요. 그다음 Welford 온라인 알고리즘으로 계산해 보세요. 진짜 분산(0.6667)과 비교해 오차를 비교합니다.

2. **정밀도 사냥.** Python에서 `1.0 + x == 1.0`이 되는 가장 작은 양의 float32 값 `x`를 찾아 보세요. 이것이 기계 epsilon(machine epsilon)입니다. `numpy.finfo(numpy.float32).eps`와 일치하는지 확인합니다.

3. **log-sum-exp 엣지 케이스.** `logsumexp_stable` 함수를 다음 경우에 테스트해 보세요. (a) 모든 값이 같을 때, (b) 한 값이 나머지보다 훨씬 클 때, (c) 모든 값이 아주 큰 음수(-1000)일 때. 순진한 버전이 실패하는 지점에서 올바른 결과를 내는지 확인합니다.

4. **신경망 레이어 그래디언트 검증.** 단일 선형 레이어 `y = Wx + b`와 그 해석적 백워드 패스를 구현합니다. `numerical_gradient`로 3x2 가중치 행렬의 정확성을 검증합니다.

5. **loss scaling 실험.** float16 학습을 시뮬레이션해 보세요. [1e-9, 1e-3] 범위의 무작위 그래디언트를 만들어 float16으로 변환하고, 몇 퍼센트가 0이 되는지 측정합니다. 그다음 loss scaling(1024 곱하기)을 적용해 float16으로 변환한 뒤 다시 나누고, 0이 되는 비율을 다시 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 방식 | 실제 의미 |
|------|----------------|----------------------|
| IEEE 754 | "부동소수점 표준" | 이진 부동소수점 형식, 반올림 규칙, 특수 값(inf, nan)을 정의하는 국제 표준. 현대의 모든 CPU와 GPU가 이를 구현함. |
| 기계 epsilon | "정밀도 한계" | 주어진 float 형식에서 1.0 + e != 1.0이 되는 가장 작은 값 e. float32에서는 약 1.19e-7. |
| 자릿수 상쇄(catastrophic cancellation) | "뺄셈으로 인한 정밀도 손실" | 거의 같은 부동소수점 수를 빼면 유효 숫자가 상쇄되어 반올림 잡음이 결과를 지배하게 되는 현상. |
| 오버플로 | "숫자가 너무 큼" | 결과가 표현 가능한 최댓값을 넘어 inf가 됨. exp(89)는 float32에서 오버플로함. |
| 언더플로 | "숫자가 너무 작음" | 결과가 표현 가능한 가장 작은 양수보다 0에 가까워 0.0이 됨. exp(-104)는 float32에서 언더플로함. |
| log-sum-exp 트릭 | "먼저 최댓값을 뺀다" | exp(max(x))를 묶어내는 방식으로 log(sum(exp(x)))를 계산해 오버플로와 언더플로를 방지. softmax, 크로스엔트로피, 로그 확률 계산에 쓰임. |
| 안정한 softmax | "폭발하지 않는 softmax" | exp를 취하기 전에 max(logits)를 빼는 것. 결과는 수치적으로 동일하며 오버플로가 불가능함. |
| 그래디언트 검증 | "역전파 검증하기" | 역전파로 얻은 해석적 그래디언트를 유한 차분의 수치 그래디언트와 비교해 구현 버그를 잡는 방법. |
| 혼합 정밀도 | "float16 포워드, float32 백워드" | 속도가 중요한 연산은 낮은 정밀도 float로, 수치적으로 민감한 연산은 높은 정밀도 float로 처리. 보통 2-3배 속도 향상. |
| loss scaling | "그래디언트 언더플로 방지" | 역전파 전에 손실에 큰 상수를 곱해 그래디언트가 float16 표현 범위 안에 있게 하고, 가중치 업데이트 전에 같은 상수로 나누는 기법. |
| bfloat16 | "Brain floating point" | Google의 16비트 형식. 지수 8비트(float32와 같은 범위), 가수 7비트(float16보다 낮은 정밀도). 학습에 선호됨. |
| 그래디언트 클리핑 | "그래디언트 노름에 상한 두기" | 그래디언트 벡터의 노름이 임계값을 넘지 않게 스케일링. 폭발하는 그래디언트가 가중치를 망치는 것을 방지. |
| NaN | "Not a Number(숫자가 아님)" | 정의되지 않은 연산(0/0, inf-inf, sqrt(-1))에서 나오는 특수 float 값. 이후 모든 산술로 퍼져 나감. |
| Inf | "무한대" | 오버플로나 0으로 나누기에서 나오는 특수 float 값. 결합하면 NaN을 만들 수 있음(inf - inf, inf * 0). |
| 수치 그래디언트 | "무식하게 계산한 미분" | f(x+h)와 f(x-h)를 계산해서 2h로 나누어 미분을 근사. 느리지만 검증용으로는 믿을 만함. |

## 더 읽을거리

- [What Every Computer Scientist Should Know About Floating-Point Arithmetic (Goldberg 1991)](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) -- 방대하지만 완벽한 표준 참고 문헌
- [Mixed Precision Training (Micikevicius et al., 2018)](https://arxiv.org/abs/1710.03740) -- float16 학습을 위한 loss scaling을 도입한 NVIDIA 논문
- [AMP: Automatic Mixed Precision (PyTorch 문서)](https://pytorch.org/docs/stable/amp.html) -- PyTorch에서 혼합 정밀도를 쓰는 실전 안내
- [bfloat16 포맷 (Google Cloud TPU 문서)](https://cloud.google.com/tpu/docs/bfloat16) -- Google이 TPU에 이 포맷을 선택한 이유
- [Kahan 합산 (Wikipedia)](https://en.wikipedia.org/wiki/Kahan_summation_algorithm) -- 부동소수점 합계의 반올림 오차를 줄이는 알고리즘
