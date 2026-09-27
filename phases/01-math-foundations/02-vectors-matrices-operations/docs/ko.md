# 벡터, 행렬, 그리고 연산들 (Vectors, Matrices & Operations)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 모든 신경망은 결국 행렬 곱셈에 절차를 조금 얹은 것에 불과합니다.

**유형:** Build
**언어:** Python, Julia
**선수 지식:** 페이즈 1, 레슨 01 (선형 대수 직관)
**소요 시간:** 약 60분

## 학습 목표

- 요소별 연산, 행렬 곱셈, 전치, 행렬식, 역행렬을 갖춘 Matrix 클래스 만들기
- 요소별 곱셈(element-wise multiplication)과 행렬 곱셈을 구분하고, 각각이 언제 쓰이는지 설명하기
- 처음부터 만든 Matrix 클래스만으로 단일 완전연결(dense) 신경망 레이어(`relu(W @ x + b)`) 구현하기
- 브로드캐스팅 규칙과 신경망 프레임워크에서 편향(bias) 덧셈이 동작하는 방식 설명하기

## 문제 상황

신경망을 직접 만들고 싶다. 코드를 읽다 보면 이런 줄을 만납니다:

```
output = activation(weights @ input + bias)
```

그 `@`가 행렬 곱셈입니다. `weights`는 행렬이고, `input`은 벡터죠. 이 연산들이 무엇을 하는지 모르면 이 한 줄은 마법입니다. 알고 있다면, 이것이 레이어의 순전파(forward pass) 전체를 세 번의 연산으로 표현한 것임을 알게 됩니다.

모델이 처리하는 모든 이미지는 픽셀 값의 행렬입니다. 모든 단어 임베딩은 벡터입니다. 모든 신경망의 모든 레이어는 행렬 변환입니다. 변수를 이해하지 못하고 코드를 쓸 수 없듯이, 행렬 연산에 능숙하지 않으면 AI 시스템을 만들 수 없습니다.

이 레슨은 그 능숙함을 처음부터 길러 줍니다.

## 핵심 개념

### 벡터: 순서가 있는 숫자 목록

벡터는 방향과 크기를 가진 숫자 목록입니다. AI에서 벡터는 데이터 포인트, 특성(feature), 파라미터를 표현합니다.

```
v = [3, 4]        -- 2D 벡터
w = [1, 0, -2]    -- 3D 벡터
```

2D 벡터 `[3, 4]`는 평면 위의 좌표 (3, 4)를 가리킵니다. 길이(크기)는 5입니다 (3-4-5 직각삼각형이죠).

### 행렬: 숫자의 격자

행렬은 2차원 격자입니다. 행과 열로 이루어지죠. m x n 행렬은 행이 m개, 열이 n개라는 뜻입니다.

```
A = | 1  2  3 |     -- 2x3 행렬 (행 2개, 열 3개)
    | 4  5  6 |
```

신경망에서 가중치 행렬은 입력 벡터를 출력 벡터로 변환합니다. 입력 784개, 출력 128개짜리 레이어는 128x784 가중치 행렬을 사용합니다.

### 왜 모양(shape)이 중요한가

행렬 곱셈에는 엄격한 규칙이 있습니다: `(m x n) @ (n x p) = (m x p)`. 안쪽 차원이 서로 같아야 합니다.

```
(128 x 784) @ (784 x 1) = (128 x 1)
  weights       input       output

안쪽 차원: 784 = 784  -- 성립
```

PyTorch에서 shape mismatch 오류를 만나면 원인이 바로 이것입니다.

### 연산 지도

| 연산 | 하는 일 | 신경망에서의 용도 |
|-----------|-------------|-------------------|
| 덧셈 | 요소별 결합 | 출력에 편향 더하기 |
| 스칼라 곱 | 모든 요소에 배율 적용 | 학습률 * 그래디언트 |
| 행렬 곱 | 벡터 변환 | 레이어 순전파 |
| 전치 | 행과 열 뒤집기 | 역전파 |
| 행렬식 | 하나의 숫자로 요약 | 역행렬 존재 여부 확인 |
| 역행렬 | 변환 되돌리기 | 연립 선형 방정식 풀기 |
| 항등행렬 | 아무것도 안 하는 행렬 | 초기화, 잔차 연결(residual connection) |

### 요소별 곱셈 vs 행렬 곱셈

이 구분이 초보자를 항상 헷갈리게 만듭니다.

요소별 곱셈: 같은 위치끼리 곱합니다. 두 행렬의 모양이 같아야 합니다.

```
| 1  2 |   | 5  6 |   | 5  12 |
| 3  4 | * | 7  8 | = | 21 32 |
```

행렬 곱셈: 행과 열 사이의 내적입니다. 안쪽 차원이 같아야 합니다.

```
| 1  2 |   | 5  6 |   | 1*5+2*7  1*6+2*8 |   | 19  22 |
| 3  4 | @ | 7  8 | = | 3*5+4*7  3*6+4*8 | = | 43  50 |
```

다른 연산, 다른 결과, 다른 규칙입니다.

### 브로드캐스팅

출력 행렬에 편향 벡터를 더하려 하면 모양이 맞지 않습니다. 브로드캐스팅(broadcasting)은 작은 배열을 늘려서 큰 배열에 맞춰 줍니다.

```
| 1  2  3 |   +   [10, 20, 30]
| 4  5  6 |

브로드캐스팅이 벡터를 행 방향으로 늘립니다:

| 1  2  3 |   | 10  20  30 |   | 11  22  33 |
| 4  5  6 | + | 10  20  30 | = | 14  25  36 |
```

모든 현대 프레임워크가 이걸 자동으로 해 줍니다. 원리를 알아 두면, 모양이 이상해 보여도 코드가 돌아가는 상황에서 헤매지 않을 수 있습니다.

```figure
vector-projection
```

## 직접 만들기

### 단계 1: Vector 클래스

```python
class Vector:
    def __init__(self, data):
        self.data = list(data)
        self.size = len(self.data)

    def __repr__(self):
        return f"Vector({self.data})"

    def __add__(self, other):
        return Vector([a + b for a, b in zip(self.data, other.data)])

    def __sub__(self, other):
        return Vector([a - b for a, b in zip(self.data, other.data)])

    def __mul__(self, scalar):
        return Vector([x * scalar for x in self.data])

    def dot(self, other):
        return sum(a * b for a, b in zip(self.data, other.data))

    def magnitude(self):
        return sum(x ** 2 for x in self.data) ** 0.5
```

### 단계 2: 핵심 연산을 갖춘 Matrix 클래스

```python
class Matrix:
    def __init__(self, data):
        self.data = [list(row) for row in data]
        self.rows = len(self.data)
        self.cols = len(self.data[0])
        self.shape = (self.rows, self.cols)

    def __repr__(self):
        rows_str = "\n  ".join(str(row) for row in self.data)
        return f"Matrix({self.shape}):\n  {rows_str}"

    def __add__(self, other):
        return Matrix([
            [self.data[i][j] + other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def __sub__(self, other):
        return Matrix([
            [self.data[i][j] - other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def scalar_multiply(self, scalar):
        return Matrix([
            [self.data[i][j] * scalar for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def element_wise_multiply(self, other):
        return Matrix([
            [self.data[i][j] * other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def matmul(self, other):
        return Matrix([
            [
                sum(self.data[i][k] * other.data[k][j] for k in range(self.cols))
                for j in range(other.cols)
            ]
            for i in range(self.rows)
        ])

    def transpose(self):
        return Matrix([
            [self.data[j][i] for j in range(self.rows)]
            for i in range(self.cols)
        ])

    def determinant(self):
        if self.shape == (1, 1):
            return self.data[0][0]
        if self.shape == (2, 2):
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]
        det = 0
        for j in range(self.cols):
            minor = Matrix([
                [self.data[i][k] for k in range(self.cols) if k != j]
                for i in range(1, self.rows)
            ])
            det += ((-1) ** j) * self.data[0][j] * minor.determinant()
        return det

    def inverse_2x2(self):
        det = self.determinant()
        if det == 0:
            raise ValueError("Matrix is singular, no inverse exists")
        return Matrix([
            [self.data[1][1] / det, -self.data[0][1] / det],
            [-self.data[1][0] / det, self.data[0][0] / det]
        ])

    @staticmethod
    def identity(n):
        return Matrix([
            [1 if i == j else 0 for j in range(n)]
            for i in range(n)
        ])
```

### 단계 3: 동작 확인

```python
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])

print("A + B =", (A + B).data)
print("A @ B =", A.matmul(B).data)
print("A^T =", A.transpose().data)
print("det(A) =", A.determinant())
print("A^-1 =", A.inverse_2x2().data)

I = Matrix.identity(2)
print("A @ A^-1 =", A.matmul(A.inverse_2x2()).data)
```

### 단계 4: 신경망과 연결하기

```python
import random

inputs = Matrix([[0.5], [0.8], [0.2]])
weights = Matrix([
    [random.uniform(-1, 1) for _ in range(3)]
    for _ in range(2)
])
bias = Matrix([[0.1], [0.1]])

def relu_matrix(m):
    return Matrix([[max(0, val) for val in row] for row in m.data])

pre_activation = weights.matmul(inputs) + bias
output = relu_matrix(pre_activation)

print(f"Input shape: {inputs.shape}")
print(f"Weight shape: {weights.shape}")
print(f"Output shape: {output.shape}")
print(f"Output: {output.data}")
```

이것이 단일 완전연결 레이어입니다: `output = relu(W @ x + b)`. 모든 신경망의 모든 완전연결 레이어가 정확히 이 일을 합니다.

## 실전에서 활용하기

NumPy는 위의 모든 일을 더 적은 줄로, 수십 배 빠르게 처리합니다.

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

print("A + B =\n", A + B)
print("A * B (element-wise) =\n", A * B)
print("A @ B (matrix multiply) =\n", A @ B)
print("A^T =\n", A.T)
print("det(A) =", np.linalg.det(A))
print("A^-1 =\n", np.linalg.inv(A))
print("I =\n", np.eye(2))

inputs = np.random.randn(3, 1)
weights = np.random.randn(2, 3)
bias = np.array([[0.1], [0.1]])
output = np.maximum(0, weights @ inputs + bias)

print(f"\nNeural network layer: {weights.shape} @ {inputs.shape} = {output.shape}")
print(f"Output:\n{output}")
```

Python의 `@` 연산자는 `__matmul__`을 호출합니다. NumPy는 C와 Fortran으로 작성된 최적화된 BLAS 루틴으로 이를 구현합니다. 같은 수학인데 100배 빠른 거죠.

NumPy의 브로드캐스팅:

```python
matrix = np.array([[1, 2, 3], [4, 5, 6]])
bias = np.array([10, 20, 30])
print(matrix + bias)
```

NumPy가 1차원 편향을 두 행에 자동으로 브로드캐스팅합니다. 모든 신경망 프레임워크에서 편향 덧셈이 동작하는 방식이 바로 이것입니다.

## 출시하기

이 레슨은 행렬 연산을 기하학적 직관으로 가르치는 프롬프트를 산출물로 만듭니다. `outputs/prompt-matrix-operations.md`를 참고하세요.

여기서 만든 Matrix 클래스는 페이즈 3, 레슨 10에서 만들 미니 신경망 프레임워크의 토대입니다.

## 연습 문제

1. **역행렬 검증하기.** `A @ A.inverse_2x2()`를 곱해 항등행렬이 나오는지 확인하세요. 서로 다른 2x2 행렬 세 개로 시도해 보고, 행렬식이 0일 때는 어떻게 되는지 관찰하세요.

2. **3x3 역행렬 구현하기.** Matrix 클래스를 확장해 수반 행렬(adjugate) 방식으로 3x3 행렬의 역행렬을 계산하세요. NumPy의 `np.linalg.inv`와 비교해 검증합니다.

3. **두 레이어 신경망 만들기.** Matrix 클래스만 사용해서(NumPy 금지) 입력(3) -> 은닉(4) -> 출력(2) 구조의 신경망을 만드세요. 무작위 가중치로 초기화하고, 순전파를 돌린 다음, 모든 모양이 올바른지 확인합니다.

## 핵심 용어

| 용어 | 사람들의 말 | 실제 의미 |
|------|----------------|----------------------|
| 벡터 | "화살표" | 순서가 있는 숫자 목록. AI에서는 고차원 공간의 한 점. |
| 행렬 | "숫자 표" | 선형 변환. 벡터를 한 공간에서 다른 공간으로 대응시킴. |
| 행렬 곱 | "그냥 숫자끼리 곱하기" | 첫 행렬의 모든 행과 두 번째 행렬의 모든 열 사이의 내적. 순서가 중요함. |
| 전치 | "뒤집기" | 행과 열을 맞바꿈. m x n 행렬이 n x m이 된다. 역전파에서 결정적 역할. |
| 행렬식 | "행렬에서 나온 어떤 숫자" | 행렬이 면적(2D)이나 부피(3D)를 얼마나 늘리는지 측정. 0이면 변환이 한 차원을 납작하게 눌러 버린다는 뜻. |
| 역행렬 | "행렬 되돌리기" | 변환을 되돌리는 행렬. 행렬식이 0이 아닐 때만 존재. |
| 항등행렬 | "지루한 행렬" | 1을 곱하는 것과 같은 행렬. 잔차 연결(ResNet)에 사용됨. |
| 브로드캐스팅 | "모양을 알아서 맞추는 마법" | 부족한 차원 방향으로 반복해 작은 배열을 큰 배열에 맞게 늘리는 것. |
| 요소별(element-wise) | "평범한 곱셈" | 같은 위치끼리 곱함. 두 배열의 모양이 같아야 함(또는 브로드캐스팅 가능해야 함). |

## 더 읽을거리

- [3Blue1Brown: Essence of Linear Algebra](https://www.3blue1brown.com/topics/linear-algebra) - 이 레슨의 모든 연산을 시각적 직관으로 설명
- [NumPy 브로드캐스팅 문서](https://numpy.org/doc/stable/user/basics.broadcasting.html) - NumPy가 따르는 정확한 규칙
- [Stanford CS229 Linear Algebra Review](http://cs229.stanford.edu/section/cs229-linalg.pdf) - ML용 선형 대수 요약 레퍼런스
