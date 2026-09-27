> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# JAX 입문

> PyTorch는 텐서를 그 자리에서 바꿔 붙입니다(mutate). TensorFlow는 그래프를 만듭니다. JAX는 순수 함수를 컴파일합니다. 마지막 문장이 딥러닝을 바라보는 관점 자체를 바꿉니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 03 레슨 01-10, 기초 NumPy
**시간:** 약 90분

## 학습 목표

- JAX의 함수형 API(jax.numpy, jax.grad, jax.jit, jax.vmap)를 사용해 순수 함수 기반 신경망 코드를 작성합니다
- PyTorch의 즉시 실행 방식(eager mutation)과 JAX의 함수형 컴파일 모델 사이의 핵심 설계 차이를 설명합니다
- 순진한 파이썬 구현과 비교해 jit 컴파일과 vmap 벡터화를 학습 루프에 적용해 속도를 높입니다
- JAX로 간단한 신경망을 학습시키고, 명시적인 상태 관리 방식을 PyTorch의 객체지향 방식과 대조합니다

## 문제 상황

여러분은 PyTorch로 신경망을 만드는 방법을 이미 알고 있습니다. `nn.Module`을 정의하고, `.backward()`를 호출하고, 옵티마이저를 한 단계(step) 전진시키죠. 잘 동작합니다. 수백만 명이 쓰고 있습니다.

하지만 PyTorch에는 유전자에 새겨 든 제약이 하나 있습니다. 모든 연산을 파이썬에서 한 번에 하나씩 즉시 실행(eager)한다는 점입니다. `tensor + tensor` 하나하나가 별개의 커널 실행이고, 학습 단계마다 똑같은 파이썬 코드를 매번 다시 해석합니다. 2,048개 TPU에 걸쳐 5,400억 개 파라미터짜리 모델을 학습시켜야 하는 순간까지는 잘 견딥니다. 그 순간부터는 이 오버헤드가 발목을 잡습니다.

Google DeepMind는 Gemini를 JAX로 학습시킵니다. Anthropic도 Claude를 JAX로 학습시켰습니다. 이건 규모가 작은 사업이 아닙니다 — 지구에서 가장 큰 신경망 학습 작업들입니다. 이들이 JAX를 택한 이유는, JAX가 학습 루프를 파이썬 호출의 나열이 아니라 컴파일 가능한 프로그램으로 다루기 때문입니다.

JAX는 세 가지 초능력이 얹힌 NumPy입니다: 자동 미분, XLA로의 JIT 컴파일, 자동 벡터화. 여러분은 예제 하나를 처리하는 함수를 작성합니다. 그러면 JAX가 배치를 처리하고, 그래디언트를 계산하고, 기계어로 컴파일하고, 여러 장치에 걸쳐 실행되는 함수를 만들어 줍니다. 원래 함수는 한 글자도 바꾸지 않고요.

## 핵심 개념

### JAX의 철학

JAX는 함수형 프레임워크입니다. 클래스도, 바꿀 수 있는 상태도, `.backward()` 메서드도 없습니다. 대신 이런 방식을 씁니다:

| PyTorch | JAX |
|---------|-----|
| 상태를 가진 `nn.Module` 클래스 | 순수 함수: `f(params, x) -> y` |
| `loss.backward()` | `jax.grad(loss_fn)(params, x, y)` |
| 즉시 실행 | XLA를 통한 JIT 컴파일 |
| `for x in batch:` 손 루프 | `jax.vmap(f)` 자동 벡터화 |
| `DataParallel` / `FSDP` | `jax.pmap(f)` 자동 병렬화 |
| 바뀔 수 있는 `model.parameters()` | 불변 배열의 파이트리(pytrees) |

이건 취향의 문제가 아닙니다. 컴파일러의 제약 조건입니다. JIT 컴파일은 순수 함수를 요구합니다 — 같은 입력은 언제나 같은 출력을 내고, 부수 효과(side effect)가 없어야 하죠. 바로 이 제약이 100배 속도 향상을 가능하게 만듭니다.

### jax.numpy: 익숙한 겉모습

JAX는 NumPy API를 가속기 위에 다시 구현했습니다:

```python
import jax.numpy as jnp

a = jnp.array([1.0, 2.0, 3.0])
b = jnp.array([4.0, 5.0, 6.0])
c = jnp.dot(a, b)
```

함수 이름도 같고, 브로드캐스팅 규칙도 같고, 슬라이싱 의미도 같습니다. 다만 배열이 GPU/TPU 위에 살고 있고, 모든 연산을 컴파일러가 추적(trace)할 수 있습니다.

결정적인 차이가 하나 있습니다. JAX 배열은 불변(immutable)입니다. `a[0] = 5` 같은 코드는 안 됩니다. 대신 `a = a.at[0].set(5)`를 씁니다. 한동안은 어색하게 느껴지다가 어느 순간 이해하게 됩니다 — 바로 이 불변성 덕분에 `grad`, `jit`, `vmap` 같은 변환들을 자유롭게 조립할 수 있는 것입니다.

### jax.grad: 함수형 자동 미분

PyTorch는 텐서에 그래디언트를 붙입니다(`.grad`). JAX는 함수에 그래디언트를 붙입니다.

```python
import jax

def f(x):
    return x ** 2

df = jax.grad(f)
df(3.0)
```

`jax.grad`는 함수를 받아서 그래디언트를 계산하는 새 함수를 돌려줍니다. `.backward()` 호출도 없고, 텐서에 계산 그래프를 저장해 두지도 않습니다. 그래디언트는 그냥 호출하고, 조립하고, JIT 컴파일할 수 있는 또 하나의 함수일 뿐입니다.

조립은 무한히 가능합니다:

```python
d2f = jax.grad(jax.grad(f))
d2f(3.0)
```

2계 도함수, 3계 도함수, 야코비안(Jacobian), 헤시안(Hessian). 전부 `grad`를 조립해서 얻습니다. PyTorch로도 할 수 있습니다(`torch.autograd.functional.hessian`). 하지만 PyTorch에서는 나중에 붙인 덧붙임이고, JAX에서는 이것이 기반입니다.

제약 조건: `grad`는 순수 함수에만 동작합니다. 함수 안에 print 문을 넣으면 안 됩니다(print는 실행이 아니라 트레이싱 중에 돌아버립니다). 외부 상태를 바꾸면 안 되고, 명시적인 키 관리 없이 난수를 만들어서도 안 됩니다.

### jit: XLA로 컴파일하기

```python
@jax.jit
def train_step(params, x, y):
    loss = loss_fn(params, x, y)
    return loss

fast_step = jax.jit(train_step)
```

첫 호출에서 JAX는 함수를 트레이싱합니다 — 연산을 실제로 실행하지는 않고 어떤 연산이 일어나는지 기록합니다. 그리고 그 기록을 XLA(Accelerated Linear Algebra), 즉 구글이 TPU와 GPU용으로 만든 컴파일러에 넘깁니다. XLA는 연산들을 융합(fuse)하고, 불필요한 메모리 복사를 없애고, 최적화된 기계어를 만들어 냅니다.

이후 호출부터는 파이썬을 완전히 건너뜁니다. 컴파일된 코드가 가속기 위에서 C++ 수준의 속도로 돌아갑니다.

JIT이 도움이 되는 경우:
- 학습 단계(똑같은 계산을 수천 번 반복할 때)
- 추론(같은 모델, 다른 입력)
- 비슷한 모양의 입력으로 두 번 이상 호출되는 모든 함수

JIT이 독이 되는 경우:
- 값에 의존하는 파이썬 제어 흐름이 있는 함수(x가 트레이싱된 배열일 때의 `if x > 0`)
- 한 번만 실행하는 계산(컴파일 오버헤드가 실행 시간을 초과)
- 디버깅(트레이싱이 실제 실행을 가려 버림)

제어 흐름 제약은 진짜입니다. `jax.lax.cond`가 `if/else`를 대신하고, `jax.lax.scan`이 `for` 루프를 대신합니다. 선택 사항이 아닙니다 — 컴파일의 대가입니다.

### vmap: 자동 벡터화

예제 하나를 처리하는 함수를 작성합니다:

```python
def predict(params, x):
    return jnp.dot(params['w'], x) + params['b']
```

`vmap`이 이 함수를 배치를 처리하도록 끌어올립니다:

```python
batch_predict = jax.vmap(predict, in_axes=(None, 0))
```

`in_axes=(None, 0)`의 뜻은 이렇습니다: `params`는 배치로 나누지 않는다(공유), `x`의 0번 축을 따라 배치로 나눈다. `for` 루프를 손으로 짤 필요도, reshape할 필요도, 배치 차원을 여기저기 끼워 넣을 필요도 없습니다. JAX가 배치 차원을 알아서 찾아 계산 전체를 벡터화합니다.

이건 단순한 문법 설탕(syntactic sugar)이 아닙니다. `vmap`은 파이썬 루프보다 10~100배 빠르게 돌아가는 융합된 벡터화 코드를 생성합니다. 게다가 `jit`, `grad`와 조립도 됩니다:

```python
per_example_grads = jax.vmap(jax.grad(loss_fn), in_axes=(None, 0, 0))
```

예제별 그래디언트(per-example gradients). 단 한 줄입니다. PyTorch에서는 편법을 쓰지 않으면 거의 불가능한 일입니다.

### pmap: 여러 장치에 걸친 데이터 병렬화

```python
parallel_step = jax.pmap(train_step, axis_name='devices')
```

`pmap`은 함수를 사용 가능한 모든 장치(GPU/TPU)에 복제하고 배치를 나눠 담습니다. 함수 안에서 `jax.lax.pmean`과 `jax.lax.psum`이 장치들 사이에서 그래디언트를 동기화합니다.

구글은 `pmap`(과 그 후속격인 `shard_map`)을 써서 수천 개의 TPU v5e 칩에 걸쳐 Gemini를 학습시킵니다. 프로그래밍 모델은 이렇습니다: 장치 한 개용 버전을 작성하고, `pmap`으로 감싸면 끝.

### 파이트리(pytrees): 만능 데이터 구조

JAX는 "파이트리(pytrees)" — 리스트, 튜플, 딕셔너리, 배열이 중첩된 조합 — 위에서 동작합니다. 여러분의 모델 파라미터도 하나의 파이트리입니다:

```python
params = {
    'layer1': {'w': jnp.zeros((784, 256)), 'b': jnp.zeros(256)},
    'layer2': {'w': jnp.zeros((256, 128)), 'b': jnp.zeros(128)},
    'layer3': {'w': jnp.zeros((128, 10)),  'b': jnp.zeros(10)},
}
```

JAX의 모든 변환 — `grad`, `jit`, `vmap` — 은 파이트리를 훑는 방법을 알고 있습니다. `jax.tree.map(f, tree)`는 모든 잎(leaf)에 `f`를 적용합니다. 옵티마이저가 모든 파라미터를 한 번에 갱신하는 방식이 바로 이것입니다:

```python
params = jax.tree.map(lambda p, g: p - lr * g, params, grads)
```

`.parameters()` 메서드도, 파라미터 등록도 없습니다. 트리 구조 자체가 곧 모델입니다.

### 함수형 vs 객체지향

PyTorch는 상태를 객체 안에 저장합니다:

```python
class Model(nn.Module):
    def __init__(self):
        self.linear = nn.Linear(784, 10)

    def forward(self, x):
        return self.linear(x)
```

JAX는 명시적인 상태를 가진 순수 함수를 사용합니다:

```python
def predict(params, x):
    return jnp.dot(x, params['w']) + params['b']
```

파라미터는 인자로 전달됩니다. 저장되는 것도, 바뀌는 것도 없습니다. 덕분에 모든 함수가 테스트하기 쉽고, 조립하기 쉽고, 컴파일하기 쉽습니다. 대신 파라미터를 직접 관리해야 한다는 뜻이기도 합니다 — 아니면 Flax나 Equinox 같은 라이브러리를 쓰면 됩니다.

### JAX 생태계

JAX는 기본 부품(primitive)을 줍니다. 쓰기 편한 인체공학은 라이브러리가 채워 줍니다:

| 라이브러리 | 역할 | 스타일 |
|---------|------|-------|
| **Flax** (Google) | 신경망 레이어 | 명시적 상태를 가진 `nn.Module` |
| **Equinox** (Patrick Kidger) | 신경망 레이어 | 파이트리 기반, 파이썬스러움 |
| **Optax** (DeepMind) | 옵티마이저 + 학습률 스케줄 | 조립 가능한 그래디언트 변환 |
| **Orbax** (Google) | 체크포인팅 | 파이트리 저장/복원 |
| **CLU** (Google) | 지표 + 로깅 | 학습 루프 유틸리티 |

Optax는 표준 옵티마이저 라이브러리입니다. 그래디언트 변환(Adam, SGD, 클리핑)을 파라미터 갱신과 분리해 놓아서 조립이 아주 쉽습니다:

```python
optimizer = optax.chain(
    optax.clip_by_global_norm(1.0),
    optax.adam(learning_rate=1e-3),
)
```

### JAX vs PyTorch, 언제 무엇을 쓸까

| 요소 | JAX | PyTorch |
|--------|-----|---------|
| TPU 지원 | 일급 시민(구글이 둘 다 만듦) | 커뮤니티가 유지(torch_xla) |
| GPU 지원 | 좋음(XLA를 통한 CUDA) | 최고 수준(네이티브 CUDA) |
| 디버깅 | 어려움(트레이싱 + 컴파일) | 쉬움(즉시 실행, 한 줄씩) |
| 생태계 | 연구 중심(Flax, Equinox) | 방대함(HuggingFace, torchvision 등) |
| 채용 | 틈새(구글/DeepMind/Anthropic) | 주류(어디서나) |
| 대규모 학습 | 우수(XLA, pmap, mesh) | 좋음(FSDP, DeepSpeed) |
| 프로토타이핑 속도 | 느림(함수형 오버헤드) | 빠름(고치고 바로 실행) |
| 프로덕션(운영 환경) 추론 | TensorFlow Serving, Vertex AI | TorchServe, Triton, ONNX |
| 사용 주체 | DeepMind(Gemini), Anthropic(Claude) | Meta(Llama), OpenAI(GPT), Stability AI |

솔직한 답: JAX를 쓸 특별한 이유가 없다면 PyTorch를 쓰세요. 그 이유에 해당하는 경우는 — TPU를 쓸 수 있을 때, 예제별 그래디언트가 필요할 때, 초대규모 다중 장치 학습을 할 때, 구글/DeepMind/Anthropic에서 일할 때입니다.

### JAX에서의 난수

JAX에는 전역 난수 상태가 없습니다. 모든 난수 연산에는 명시적인 PRNG 키가 필요합니다:

```python
key = jax.random.PRNGKey(42)
key1, key2 = jax.random.split(key)
w = jax.random.normal(key1, shape=(784, 256))
```

처음에는 귀찮습니다. 하지만 장치가 달라져도, 컴파일이 달라져도 결과가 똑같이 재현된다는 보장을 받습니다 — PyTorch의 `torch.manual_seed`는 멀티 GPU 환경에서 이걸 보장해 주지 못합니다.

```figure
batchnorm-effect
```

## 만들어 보기

### 단계 1: 준비와 데이터

JAX와 Optax로 MNIST에서 3층 MLP를 학습시켜 보겠습니다. 입력 784개, 은닉층 두 개(256, 128 뉴런), 출력 클래스 10개입니다.

```python
import jax
import jax.numpy as jnp
from jax import random
import optax

def get_mnist_data():
    from sklearn.datasets import fetch_openml
    mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
    X = mnist.data.astype('float32') / 255.0
    y = mnist.target.astype('int')
    X_train, X_test = X[:60000], X[60000:]
    y_train, y_test = y[:60000], y[60000:]
    return X_train, y_train, X_test, y_test
```

### 단계 2: 파라미터 초기화

클래스 없이, 파이트리를 돌려주는 함수 하나면 됩니다:

```python
def init_params(key):
    k1, k2, k3 = random.split(key, 3)
    scale1 = jnp.sqrt(2.0 / 784)
    scale2 = jnp.sqrt(2.0 / 256)
    scale3 = jnp.sqrt(2.0 / 128)
    params = {
        'layer1': {
            'w': scale1 * random.normal(k1, (784, 256)),
            'b': jnp.zeros(256),
        },
        'layer2': {
            'w': scale2 * random.normal(k2, (256, 128)),
            'b': jnp.zeros(128),
        },
        'layer3': {
            'w': scale3 * random.normal(k3, (128, 10)),
            'b': jnp.zeros(10),
        },
    }
    return params
```

He 초기화를 손으로 직접 구현한 것입니다. 시드 하나에서 PRNG 키 세 개를 나눠 쓰고, 모든 가중치는 중첩 딕셔너리 안의 불변 배열입니다.

### 단계 3: 순전파

```python
def forward(params, x):
    x = jnp.dot(x, params['layer1']['w']) + params['layer1']['b']
    x = jax.nn.relu(x)
    x = jnp.dot(x, params['layer2']['w']) + params['layer2']['b']
    x = jax.nn.relu(x)
    x = jnp.dot(x, params['layer3']['w']) + params['layer3']['b']
    return x

def loss_fn(params, x, y):
    logits = forward(params, x)
    one_hot = jax.nn.one_hot(y, 10)
    return -jnp.mean(jnp.sum(jax.nn.log_softmax(logits) * one_hot, axis=-1))
```

순수 함수들입니다. 파라미터를 넣으면 예측이 나옵니다. `self`도 없고, 저장해 둔 상태도 없습니다. `loss_fn`은 교차 엔트로피를 밑바닥부터 계산합니다 — 소프트맥스, log, 음의 평균.

### 단계 4: JIT 컴파일된 학습 단계

```python
@jax.jit
def train_step(params, opt_state, x, y):
    loss, grads = jax.value_and_grad(loss_fn)(params, x, y)
    updates, opt_state = optimizer.update(grads, opt_state, params)
    params = optax.apply_updates(params, updates)
    return params, opt_state, loss

@jax.jit
def accuracy(params, x, y):
    logits = forward(params, x)
    preds = jnp.argmax(logits, axis=-1)
    return jnp.mean(preds == y)
```

`jax.value_and_grad`는 손실 값과 그래디언트를 한 번의 패스로 모두 돌려줍니다. `@jax.jit` 데코레이터가 두 함수를 XLA로 컴파일합니다. 첫 호출 이후에는 학습 단계마다 파이썬을 거치지 않고 실행됩니다.

### 단계 5: 학습 루프

```python
optimizer = optax.adam(learning_rate=1e-3)

X_train, y_train, X_test, y_test = get_mnist_data()
X_train, X_test = jnp.array(X_train), jnp.array(X_test)
y_train, y_test = jnp.array(y_train), jnp.array(y_test)

key = random.PRNGKey(0)
params = init_params(key)
opt_state = optimizer.init(params)

batch_size = 128
n_epochs = 10

for epoch in range(n_epochs):
    key, subkey = random.split(key)
    perm = random.permutation(subkey, len(X_train))
    X_shuffled = X_train[perm]
    y_shuffled = y_train[perm]

    epoch_loss = 0.0
    n_batches = len(X_train) // batch_size
    for i in range(n_batches):
        start = i * batch_size
        xb = X_shuffled[start:start + batch_size]
        yb = y_shuffled[start:start + batch_size]
        params, opt_state, loss = train_step(params, opt_state, xb, yb)
        epoch_loss += loss

    train_acc = accuracy(params, X_train[:5000], y_train[:5000])
    test_acc = accuracy(params, X_test, y_test)
    print(f"Epoch {epoch + 1:2d} | Loss: {epoch_loss / n_batches:.4f} | "
          f"Train Acc: {train_acc:.4f} | Test Acc: {test_acc:.4f}")
```

10 에포크, 테스트 정확도 약 97%. 첫 에포크는 느립니다(JIT 컴파일 때문). 2~10 에포크는 빠릅니다.

무엇이 빠져 있는지 보세요. `.zero_grad()`도, `.backward()`도, `.step()`도 없습니다. 갱신 전체가 조립된 함수 호출 하나로 끝납니다. 그래디언트를 계산하고, Adam으로 변환하고, 파라미터에 적용하는 모든 일이 `train_step` 안에서 일어납니다.

## 활용하기

### Flax: 구글 표준

Flax는 가장 널리 쓰이는 JAX 신경망 라이브러리입니다. `nn.Module`을 다시 돌려주되, 상태 관리는 명시적으로 합니다:

```python
import flax.linen as nn

class MLP(nn.Module):
    @nn.compact
    def __call__(self, x):
        x = nn.Dense(256)(x)
        x = nn.relu(x)
        x = nn.Dense(128)(x)
        x = nn.relu(x)
        x = nn.Dense(10)(x)
        return x

model = MLP()
params = model.init(jax.random.PRNGKey(0), jnp.ones((1, 784)))
logits = model.apply(params, x_batch)
```

구조는 PyTorch와 같지만, `params`가 모델과 분리되어 있습니다. `model.init()`이 파라미터를 만들고, `model.apply(params, x)`가 순전파를 실행합니다. 모델 객체는 상태가 없습니다.

### Equinox: 파이썬다운 대안

Equinox(Patrick Kidger 작)는 모델을 파이트리로 표현합니다:

```python
import equinox as eqx

model = eqx.nn.MLP(
    in_size=784, out_size=10, width_size=256, depth=2,
    activation=jax.nn.relu, key=jax.random.PRNGKey(0)
)
logits = model(x)
```

모델 자체가 파이트리입니다. `.apply()`가 필요 없습니다. 파라미터는 그냥 모델의 잎사귀들입니다. JAX의 사고방식에는 이쪽이 더 가깝습니다.

### Optax: 조립식 옵티마이저

Optax는 그래디언트 변환을 갱신으로부터 분리합니다:

```python
schedule = optax.warmup_cosine_decay_schedule(
    init_value=0.0, peak_value=1e-3,
    warmup_steps=1000, decay_steps=50000
)

optimizer = optax.chain(
    optax.clip_by_global_norm(1.0),
    optax.adamw(learning_rate=schedule, weight_decay=0.01),
)
```

그래디언트 클리핑, 학습률 워밍업, 가중치 감쇠(weight decay) — 전부 변환 체인으로 조립됩니다. 각 변환은 그래디언트를 받아 고친 뒤 다음 변환에 넘깁니다. 거대한 단일체 옵티마이저 클래스는 없습니다.

## 출시하기

**설치:**

```bash
pip install jax jaxlib optax flax
```

GPU 지원:

```bash
pip install jax[cuda12]
```

TPU(Google Cloud):

```bash
pip install jax[tpu] -f https://storage.googleapis.com/jax-releases/libtpu_releases.html
```

**성능 함정들:**

- 첫 JIT 호출은 느립니다(컴파일 때문). 벤치마크 전에 미리 워밍업하세요.
- JIT 안에서 JAX 배열을 도는 파이썬 루프는 피하세요. `jax.lax.scan`이나 `jax.lax.fori_loop`를 쓰세요.
- `jax.debug.print()`는 JIT 안에서 동작합니다. 평범한 `print()`는 안 됩니다.
- `jax.profiler`나 TensorBoard로 프로파일링하세요. XLA 컴파일이 병목을 숨길 수 있습니다.
- JAX는 기본적으로 GPU 메모리의 75%를 미리 잡아 둡니다. `XLA_PYTHON_CLIENT_PREALLOCATE=false`로 끌 수 있습니다.

**체크포인팅:**

```python
import orbax.checkpoint as ocp
checkpointer = ocp.PyTreeCheckpointer()
checkpointer.save('/tmp/model', params)
restored = checkpointer.restore('/tmp/model')
```

**이 레슨이 만드는 산출물:**
- `outputs/prompt-jax-optimizer.md` — 올바른 JAX 옵티마이저 설정을 고르기 위한 프롬프트
- `outputs/skill-jax-patterns.md` — JAX의 함수형 패턴을 다루는 스킬

## 연습 문제

1. MLP에 드롭아웃을 추가해 보세요. JAX에서 드롭아웃은 PRNG 키가 필요합니다 — 순전파에 키를 끝까지 전달하고, 드롭아웃 레이어마다 키를 나눠 주세요. 드롭아웃의 유무에 따라 테스트 정확도가 어떻게 달라지는지 비교해 보세요.

2. `jax.vmap`으로 MNIST 이미지 32장짜리 배치의 예제별 그래디언트를 계산해 보세요. 예제마다 그래디언트 노름(norm)을 구하고, 어떤 예제가 가장 큰 그래디언트를 갖는지, 왜 그런지 생각해 보세요.

3. 손으로 짠 순전파 함수를, 레이어 수가 몇 개든 동작하는 범용 `mlp_forward(params, x)`로 바꿔 보세요. `jax.tree.leaves`로 깊이를 자동으로 판단하게 만들어 보세요.

4. `@jax.jit`를 붙였을 때와 안 붙였을 때의 학습 단계를 벤치마크해 보세요. 각각 100단계씩 시간을 재고, 여러분 하드웨어에서 속도 향상이 얼마나 되는지, 첫 호출에서 컴파일 오버헤드가 얼마나 되는지 확인해 보세요.

5. `optax.chain(optax.clip_by_global_norm(1.0), optax.adam(1e-3))`을 조립해 그래디언트 클리핑을 구현해 보세요. 클리핑의 유무로 각각 학습시키고, 학습 내내 그래디언트 노름을 그려서 그 효과를 확인해 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| XLA | "JAX를 빠르게 만드는 그것" | Accelerated Linear Algebra — 계산 그래프에서 연산을 융합하고 최적화된 GPU/TPU 커널을 생성하는 컴파일러 |
| JIT | "적시(just-in-time) 컴파일" | JAX가 첫 호출 때 함수를 트레이싱해 XLA로 컴파일하고, 이후 호출부터는 컴파일된 버전을 실행하는 것 |
| 순수 함수 | "부수 효과가 없는 함수" | 출력이 입력에만 의존하는 함수 — 전역 상태 없음, 변경 없음, 명시적 키 없이는 난수 없음 |
| vmap | "자동 배치 처리" | 예제 하나를 처리하는 함수를 재작성 없이 배치를 처리하는 함수로 바꾸는 변환 |
| pmap | "자동 병렬화" | 함수를 여러 장치에 복제하고 입력 배치를 나눠 주는 변환 |
| 파이트리 | "배열의 중첩 딕셔너리" | JAX가 훑고 변환할 수 있는, 리스트·튜플·딕셔너리·배열의 임의 중첩 구조 |
| 트레이싱 | "계산을 기록하는 것" | JAX가 실제 결과를 계산하지 않고 추상 값으로 함수를 실행해 계산 그래프를 만드는 과정 |
| 함수형 자동 미분 | "함수의 grad" | 텐서에 그래디언트 저장소를 붙이는 대신, 함수를 변환해서 도함수를 구하는 방식 |
| Optax | "JAX의 옵티마이저 라이브러리" | Adam, SGD, 클리핑, 스케줄링 같은 그래디언트 변환을 체인으로 연결해 쓰는 조립식 라이브러리 |
| Flax | "JAX의 nn.Module" | 레이어 추상화를 더하면서도 상태를 명시적으로 유지하는, 구글의 JAX용 신경망 라이브러리 |

## 더 읽을거리

- JAX 문서: https://jax.readthedocs.io/ — 공식 문서. grad, jit, vmap 튜토리얼이 아주 훌륭합니다
- "JAX: composable transformations of Python+NumPy programs" (Bradbury 등, 2018) — 설계 철학을 설명하는 원 논문
- Flax 문서: https://flax.readthedocs.io/ — 구글의 JAX용 신경망 라이브러리
- Patrick Kidger, "Equinox: neural networks in JAX via callable PyTrees and filtered transformations" (2021) — Flax의 파이썬다운 대안
- DeepMind, "Optax: composable gradient transformation and optimisation" — 표준 옵티마이저 라이브러리
- "You Don't Know JAX" (Colin Raffel, 2020) — T5 저자 중 한 명이 쓴, JAX의 함정과 패턴에 대한 실용 가이드
