---
name: skill-jax-patterns
description: JAX의 함수형 프로그래밍 패턴 — grad, jit, vmap, pmap을 언제 어떻게 쓰는지
version: 1.0.0
phase: 3
lesson: 12
tags: [jax, functional-programming, autodiff, compilation, vectorization]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-jax-patterns.md](skill-jax-patterns.md)

# JAX 함수형 패턴

JAX는 순수 함수를 변환합니다. 아래의 모든 패턴은 한 가지 규칙을 따릅니다: 입력을 받아 출력을 돌려주는, 부수 효과 없는 함수를 작성한다. 그다음 그 함수를 변환한다.

## 네 가지 변환

### grad — 함수를 미분하다

```python
grads = jax.grad(loss_fn)(params, x, y)
loss, grads = jax.value_and_grad(loss_fn)(params, x, y)
```

언제 쓰나: 최적화에 그래디언트가 필요할 때.
제약: 함수는 스칼라를 반환해야 합니다. 스칼라가 아닌 출력에는 `jax.jacobian`을 쓰세요.

### jit — 함수를 컴파일하다

```python
fast_fn = jax.jit(f)
```

언제 쓰나: 같은 모양의 입력으로 두 번 이상 호출될 함수일 때.
제약: 트레이싱된 값에 의존하는 파이썬 제어 흐름은 안 됩니다. 조건문은 `jax.lax.cond`, 루프는 `jax.lax.scan`을 쓰세요.

### vmap — 함수를 벡터화하다

```python
batch_fn = jax.vmap(f, in_axes=(None, 0))
```

언제 쓰나: 예제 하나 기준으로 작성한 함수를 배치에서도 동작하게 해야 할 때.
`in_axes`는 어떤 인자 축을 따라 배치로 나눌지 지정합니다. `None`은 배치로 나누지 않음(브로드캐스트)을 뜻합니다.

### pmap — 여러 장치에 걸쳐 병렬화하다

```python
parallel_fn = jax.pmap(f, axis_name='devices')
```

언제 쓰나: GPU/TPU가 여러 개 있고 데이터 병렬화를 원할 때.
함수 안에서 `jax.lax.pmean(x, 'devices')`가 장치들 사이의 평균을 구합니다.

## 조립 규칙

변환들은 조립됩니다. 순서가 중요합니다:

```python
per_example_grads = jax.jit(jax.vmap(jax.grad(loss_fn), in_axes=(None, 0, 0)))
```

오른쪽에서 왼쪽으로 읽습니다: loss_fn의 그래디언트를 구하고, 예제 축으로 벡터화하고, 결과를 컴파일합니다.

유효한 조립들:
- `jit(grad(f))` — 컴파일된 그래디언트 계산
- `jit(vmap(f))` — 컴파일된 배치 계산
- `vmap(grad(f))` — 예제별 그래디언트
- `pmap(jit(f))` — 병렬 컴파일 계산
- `grad(jit(f))` — 컴파일된 함수의 그래디언트(jit(grad(f))와 동일)

## 파라미터 관리 패턴

JAX 파라미터는 파이트리(배열의 중첩 딕셔너리)입니다:

```python
params = {
    'layer1': {'w': jnp.zeros((784, 256)), 'b': jnp.zeros(256)},
    'layer2': {'w': jnp.zeros((256, 10)),  'b': jnp.zeros(10)},
}
```

모든 파라미터를 한 번에 갱신:
```python
params = jax.tree.map(lambda p, g: p - lr * g, params, grads)
```

파라미터 수 세기:
```python
n_params = sum(p.size for p in jax.tree.leaves(params))
```

## PRNG 키 관리

JAX는 명시적인 난수 키를 요구합니다:

```python
key = jax.random.PRNGKey(0)
key, subkey = jax.random.split(key)
noise = jax.random.normal(subkey, shape)
```

난수 연산이 여러 번 필요하면 한 번에 나눠서:
```python
keys = jax.random.split(key, n)
```

키를 재사용하지 마세요. 사용하기 전에 반드시 나눠야 합니다.

## 자주 하는 실수

1. **jit 안에서 배열 변경**: JAX 배열은 불변입니다. `x[i] = v` 대신 `x.at[i].set(v)`를 쓰세요.

2. **jit 안에서 파이썬 print 사용**: `print`는 실행이 아니라 트레이싱 중에 돕니다. `jax.debug.print("{}", x)`를 쓰세요.

3. **트레이싱된 값에 파이썬 if/for 사용**: `jax.lax.cond`, `jax.lax.switch`, `jax.lax.scan`, `jax.lax.fori_loop`를 쓰세요.

4. **`.block_until_ready()` 잊기**: JAX는 비동기 디스패치를 씁니다. 벤치마크 시에는 `.block_until_ready()`를 호출해 실제 완료를 기다리세요.

5. **PRNG 키 재사용**: 같은 키를 쓰는 두 연산은 똑같은 "난수"를 냅니다. 반드시 나눠 쓰세요.

6. **jitted 함수 안의 전역 상태**: 전역 변수는 트레이싱 시점에 붙잡힙니다. 트레이싱 이후의 변경은 보이지 않습니다. 모든 값을 인자로 전달하세요.

## 의사 결정 체크리스트

1. 이 함수는 두 번 이상 호출되나요? `@jax.jit`를 붙이세요.
2. 그래디언트가 필요한가요? `jax.grad`나 `jax.value_and_grad`로 감싸세요.
3. 예제 하나를 처리하는데 배치가 있나요? `jax.vmap`으로 감싸세요.
4. 장치가 여러 개인가요? `jax.pmap`으로 감싸세요.
5. 난수를 쓰나요? PRNG 키를 명시적으로 끝까지 전달하세요.
6. 배열 값에 대한 파이썬 제어 흐름이 있나요? `jax.lax` 프리미티브로 바꾸세요.

## JAX를 쓸 때

JAX를 쓰면 좋은 경우:
- 예제별 그래디언트가 필요할 때(차등 프라이버시, 피셔 정보)
- TPU에서 학습할 때(JAX가 기본 프레임워크입니다)
- 고계 도함수(헤시안, 야코비안)가 필요할 때
- 학습 단계 전체를 하나의 커널로 컴파일하고 싶을 때
- 팀이 Google DeepMind나 Anthropic에 있을 때

PyTorch를 쓰면 좋은 경우:
- 가장 큰 생태계가 필요할 때(HuggingFace, torchvision, Lightning)
- 날것의 속도보다 디버깅 편의를 우선할 때
- TorchServe/Triton으로 NVIDIA GPU에 배포할 때
- 채용할 때(PyTorch 개발자가 더 많습니다)
- 새 아키텍처를 빠르게 반복 실험하고 싶을 때
