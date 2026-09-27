# 선형 대수 직관 (Linear Algebra Intuition)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 모든 AI 모델은 결국 멋진 모자를 쓴 행렬 계산일 뿐입니다.

**유형:** Learn
**언어:** Python, Julia
**선수 지식:** 페이즈 0
**소요 시간:** 약 60분

## 학습 목표

- Python으로 벡터와 행렬 연산(덧셈, 내적, 행렬 곱셈)을 처음부터 직접 구현하기
- 내적(dot product), 사영(projection), 그람-슈미트 과정이 기하학적으로 무엇을 하는지 설명하기
- 행 축약(row reduction)으로 벡터 집합의 선형 독립, 랭크, 기저를 판단하기
- 선형 대수 개념을 AI 응용 분야와 연결하기: 임베딩, 어텐션 점수, LoRA

## 문제 상황

ML 논문을 아무거나 펼쳐 보세요. 첫 페이지 안에서 벡터, 행렬, 내적, 변환을 만나게 됩니다. 선형 대수 직관이 없으면 이것들은 그냥 기호일 뿐입니다. 직관이 있으면 신경망이 실제로 하고 있는 일 — 공간 속의 점들을 옮기는 일 — 이 보이기 시작합니다.

수학자가 될 필요는 없습니다. 이 연산들이 기하학적으로 무슨 의미인지 보고, 직접 코드로 작성해 보면 됩니다.

## 핵심 개념

### 벡터는 점입니다 (그리고 방향입니다)

벡터는 그냥 숫자 목록입니다. 하지만 그 숫자들은 의미가 있습니다 — 공간에서의 좌표죠.

**2D 벡터 [3, 2]:**

| x | y | 점 |
|---|---|-------|
| 3 | 2 | 이 벡터는 평면 위에서 원점 (0,0)부터 (3, 2)를 향합니다 |

이 벡터의 크기는 sqrt(3^2 + 2^2) = sqrt(13)이고, 오른쪽 위를 향합니다.

AI에서는 벡터가 모든 것을 표현합니다:
- 단어 → 768개의 숫자로 이루어진 벡터 (임베딩 공간에서의 "의미")
- 이미지 → 수백만 개의 픽셀 값으로 이루어진 벡터
- 사용자 → 선호도로 이루어진 벡터

### 행렬은 변환입니다

행렬은 한 벡터를 다른 벡터로 바꿉니다. 회전시키거나, 크기를 바꾸거나, 늘리거나, 사영할 수 있죠.

```mermaid
graph LR
    subgraph Before["이전"]
        A["점 A"]
        B["점 B"]
    end
    subgraph Matrix["행렬 곱셈"]
        M["M (변환)"]
    end
    subgraph After["이후"]
        A2["점 A'"]
        B2["점 B'"]
    end
    A --> M
    B --> M
    M --> A2
    M --> B2
```

AI에서 행렬은 곧 모델 그 자체입니다:
- 신경망 가중치 → 입력을 출력으로 바꾸는 행렬
- 어텐션 점수 → 어디에 집중할지 결정하는 행렬
- 임베딩 → 단어를 벡터로 대응시키는 행렬

### 내적은 유사도를 잽니다

두 벡터의 내적(dot product)은 두 벡터가 얼마나 비슷한지 알려 줍니다.

```
a · b = a₁×b₁ + a₂×b₂ + ... + aₙ×bₙ

같은 방향:      a · b > 0  (비슷함)
수직:           a · b = 0  (관련 없음)
반대 방향:      a · b < 0  (다름)
```

검색 엔진, 추천 시스템, RAG(검색 증강 생성)가 실제로 동작하는 방식이 바로 이것입니다 — 내적이 큰 벡터를 찾는 거죠.

### 선형 독립

어떤 벡터 집합에서 그 집합의 어떤 벡터도 다른 벡터들의 조합으로 표현될 수 없다면, 이 벡터들은 선형 독립입니다. v1, v2, v3가 독립이면 3차원 공간 전체를 채웁니다(span). 하나가 다른 것들의 조합이라면 평면밖에 채우지 못합니다.

AI에서 중요한 이유: 특성(feature) 행렬의 열들은 선형 독립이어야 합니다. 두 특성이 완벽하게 상관되어 있으면(선형 종속이면) 모델은 두 효과를 구분할 수 없습니다. 이것이 회귀에서 다중공선성을 일으킵니다 — 가중치 행렬이 불안정해지고, 입력이 조금만 바뀌어도 출력이 크게 요동칩니다.

**구체적인 예:**

```
v1 = [1, 0, 0]
v2 = [0, 1, 0]
v3 = [2, 1, 0]   # v3 = 2*v1 + v2
```

v1과 v2는 독립입니다 — 어느 쪽도 다른 쪽의 스칼라 배도 조합도 아니거든요. 하지만 v3 = 2*v1 + v2이므로 {v1, v2, v3}는 종속 집합입니다. 이 세 벡터는 모두 xy 평면 위에 놓여 있습니다. 아무리 조합해도 [0, 0, 1]에는 도달할 수 없습니다. 벡터는 세 개인데 자유도는 두 차원뿐인 셈이죠.

데이터셋에 빗대면: feature_3 = 2*feature_1 + feature_2라면, feature_3을 추가해도 모델에게 새로운 정보는 전혀 없습니다. 더 나쁜 것은 정규 방정식(normal equations)을 특이(singular)하게 만든다는 점입니다 — 가중치에 대한 유일한 해가 존재하지 않게 됩니다.

### 기저와 랭크

기저(basis)는 공간 전체를 채우는 최소한의 선형 독립 벡터 집합입니다. 기저 벡터의 개수가 그 공간의 차원입니다.

3차원 공간의 표준 기저는 {[1,0,0], [0,1,0], [0,0,1]}입니다. 하지만 3차원의 독립인 벡터 세 개라면 무엇이든 유효한 기저가 됩니다. 기저를 고른다는 것은 좌표계를 고른다는 뜻입니다.

행렬의 랭크(rank) = 선형 독립인 열의 개수 = 선형 독립인 행의 개수입니다. rank < min(rows, cols)이면 그 행렬은 랭크 부족(rank-deficient)입니다. 이는 다음을 의미합니다:
- 연립 방정식의 해가 무수히 많거나 (아예 없거나)
- 변환 과정에서 정보가 손실되고
- 행렬의 역행렬을 구할 수 없습니다

| 상황 | 랭크 | ML에서의 의미 |
|-----------|------|---------------------|
| 풀 랭크 (rank = min(m, n)) | 최댓값 | 유일한 최소제곱 해가 존재. 모델이 잘 조건화됨(well-conditioned). |
| 랭크 부족 (rank < min(m, n)) | 최댓값 미만 | 특성이 중복됨. 가중치 해가 무수히 많음. 정규화가 필요함. |
| 랭크 1 | 1 | 모든 열이 하나의 벡터의 배율 사본. 모든 데이터가 한 선 위에 있음. |
| 랭크 부족에 근접 (작은 특이값) | 수치적으로 낮음 | 행렬이 ill-conditioned. 작은 입력 노이즈에도 출력이 크게 변함. SVD 절단이나 릿지 회귀 사용. |

### 사영

벡터 **a**를 벡터 **b**에 사영(projection)하면 **b** 방향으로의 **a**의 성분을 얻습니다:

```
proj_b(a) = (a dot b / b dot b) * b
```

잔차 (a - proj_b(a))는 b에 수직입니다. 이 직교 분해가 최소제곱 피팅의 기초입니다.

사영은 ML 곳곳에 있습니다:
- 선형 회귀는 관측값에서 열 공간까지의 거리를 최소화합니다 — 그 해 자체가 사영입니다
- PCA는 데이터를 최대 분산 방향으로 사영합니다
- 트랜스포머의 어텐션은 쿼리를 키에 사영한 값을 계산합니다

```mermaid
graph LR
    subgraph Projection["b 방향으로의 a의 사영"]
        direction TB
        O["원점"] --> |"b (방향)"| B["b"]
        O --> |"a (원래 벡터)"| A["a"]
        O --> |"proj_b(a)"| P["사영"]
        A -.-> |"잔차 (수직)"| P
    end
```

**예:** a = [3, 4], b = [1, 0]

proj_b(a) = (3*1 + 4*0) / (1*1 + 0*0) * [1, 0] = 3 * [1, 0] = [3, 0]

사영이 y 성분을 그냥 버려 버렸죠. 이것이 가장 단순한 형태의 차원 축소입니다 — 관심 없는 방향은 과감히 버리는 겁니다.

### 그람-슈미트 과정

독립인 벡터 집합을 정규 직교 기저(orthonormal basis)로 바꾸는 과정입니다. 정규 직교라는 말은 모든 벡터의 길이가 1이고 모든 벡터 쌍이 서로 수직이라는 뜻입니다.

알고리즘:
1. 첫 번째 벡터를 가져와 정규화합니다
2. 두 번째 벡터에서 첫 번째 벡터 방향으로의 사영을 빼고, 정규화합니다
3. 세 번째 벡터에서 앞선 모든 벡터 방향으로의 사영을 빼고, 정규화합니다
4. 남은 벡터에 대해 반복합니다

```
입력:  v1, v2, v3, ... (선형 독립)

u1 = v1 / |v1|

w2 = v2 - (v2 dot u1) * u1
u2 = w2 / |w2|

w3 = v3 - (v3 dot u1) * u1 - (v3 dot u2) * u2
u3 = w3 / |w3|

출력: u1, u2, u3, ... (정규 직교 기저)
```

QR 분해가 내부적으로 동작하는 원리가 바로 이것입니다. Q는 정규 직교 기저이고, R은 사영 계수를 담습니다. QR 분해는 다음 용도로 사용됩니다:
- 연립 선형 방정식 풀기 (가우스 소거법보다 안정적)
- 고윳값 계산 (QR 알고리즘)
- 최소제곱 회귀 (표준 수치 해법)

```figure
eigen-directions
```

## 직접 만들기

### 단계 1: 벡터를 처음부터 (Python)

```python
class Vector:
    def __init__(self, components):
        self.components = list(components)
        self.dim = len(self.components)

    def __add__(self, other):
        return Vector([a + b for a, b in zip(self.components, other.components)])

    def __sub__(self, other):
        return Vector([a - b for a, b in zip(self.components, other.components)])

    def dot(self, other):
        return sum(a * b for a, b in zip(self.components, other.components))

    def magnitude(self):
        return sum(x**2 for x in self.components) ** 0.5

    def normalize(self):
        mag = self.magnitude()
        return Vector([x / mag for x in self.components])

    def cosine_similarity(self, other):
        return self.dot(other) / (self.magnitude() * other.magnitude())

    def __repr__(self):
        return f"Vector({self.components})"


a = Vector([1, 2, 3])
b = Vector([4, 5, 6])

print(f"a + b = {a + b}")
print(f"a · b = {a.dot(b)}")
print(f"|a| = {a.magnitude():.4f}")
print(f"cosine similarity = {a.cosine_similarity(b):.4f}")
```

### 단계 2: 행렬을 처음부터 (Python)

```python
class Matrix:
    def __init__(self, rows):
        self.rows = [list(row) for row in rows]
        self.shape = (len(self.rows), len(self.rows[0]))

    def __matmul__(self, other):
        if isinstance(other, Vector):
            return Vector([
                sum(self.rows[i][j] * other.components[j] for j in range(self.shape[1]))
                for i in range(self.shape[0])
            ])
        rows = []
        for i in range(self.shape[0]):
            row = []
            for j in range(other.shape[1]):
                row.append(sum(
                    self.rows[i][k] * other.rows[k][j]
                    for k in range(self.shape[1])
                ))
            rows.append(row)
        return Matrix(rows)

    def transpose(self):
        return Matrix([
            [self.rows[j][i] for j in range(self.shape[0])]
            for i in range(self.shape[1])
        ])

    def __repr__(self):
        return f"Matrix({self.rows})"


rotation_90 = Matrix([[0, -1], [1, 0]])
point = Vector([3, 1])

rotated = rotation_90 @ point
print(f"Original: {point}")
print(f"Rotated 90°: {rotated}")
```

### 단계 3: AI에 왜 중요한가

```python
import random

random.seed(42)
weights = Matrix([[random.gauss(0, 0.1) for _ in range(3)] for _ in range(2)])
input_vector = Vector([1.0, 0.5, -0.3])

output = weights @ input_vector
print(f"Input (3D): {input_vector}")
print(f"Output (2D): {output}")
print("This is what a neural network layer does -- matrix multiplication.")
```

### 단계 4: Julia 버전

```julia
a = [1.0, 2.0, 3.0]
b = [4.0, 5.0, 6.0]

println("a + b = ", a + b)
println("a · b = ", a ⋅ b)       # Julia는 유니코드 연산자를 지원합니다
println("|a| = ", √(a ⋅ a))
println("cosine = ", (a ⋅ b) / (√(a ⋅ a) * √(b ⋅ b)))

# 행렬-벡터 곱셈
W = [0.1 -0.2 0.3; 0.4 0.5 -0.1]
x = [1.0, 0.5, -0.3]
println("Wx = ", W * x)
println("This is a neural network layer.")
```

### 단계 5: 선형 독립과 사영을 처음부터 (Python)

```python
def is_linearly_independent(vectors):
    n = len(vectors)
    dim = len(vectors[0].components)
    mat = Matrix([v.components[:] for v in vectors])
    rows = [row[:] for row in mat.rows]
    rank = 0
    for col in range(dim):
        pivot = None
        for row in range(rank, len(rows)):
            if abs(rows[row][col]) > 1e-10:
                pivot = row
                break
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        scale = rows[rank][col]
        rows[rank] = [x / scale for x in rows[rank]]
        for row in range(len(rows)):
            if row != rank and abs(rows[row][col]) > 1e-10:
                factor = rows[row][col]
                rows[row] = [rows[row][j] - factor * rows[rank][j] for j in range(dim)]
        rank += 1
    return rank == n


def project(a, b):
    scalar = a.dot(b) / b.dot(b)
    return Vector([scalar * x for x in b.components])


def gram_schmidt(vectors):
    orthonormal = []
    for v in vectors:
        w = v
        for u in orthonormal:
            proj = project(w, u)
            w = w - proj
        if w.magnitude() < 1e-10:
            continue
        orthonormal.append(w.normalize())
    return orthonormal


v1 = Vector([1, 0, 0])
v2 = Vector([1, 1, 0])
v3 = Vector([1, 1, 1])
basis = gram_schmidt([v1, v2, v3])
for i, u in enumerate(basis):
    print(f"u{i+1} = {u}")
    print(f"  |u{i+1}| = {u.magnitude():.6f}")

print(f"u1 · u2 = {basis[0].dot(basis[1]):.6f}")
print(f"u1 · u3 = {basis[0].dot(basis[2]):.6f}")
print(f"u2 · u3 = {basis[1].dot(basis[2]):.6f}")
```

## 실전에서 활용하기

이제 같은 작업을 NumPy로 해 봅니다 — 실전에서 실제로 쓰게 될 도구죠:

```python
import numpy as np

a = np.array([1, 2, 3], dtype=float)
b = np.array([4, 5, 6], dtype=float)

print(f"a + b = {a + b}")
print(f"a · b = {np.dot(a, b)}")
print(f"|a| = {np.linalg.norm(a):.4f}")
print(f"cosine = {np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)):.4f}")

W = np.random.randn(2, 3) * 0.1
x = np.array([1.0, 0.5, -0.3])
print(f"Wx = {W @ x}")
```

### NumPy로 랭크, 사영, QR 다루기

```python
import numpy as np

A = np.array([[1, 2], [2, 4]])
print(f"Rank: {np.linalg.matrix_rank(A)}")

a = np.array([3, 4])
b = np.array([1, 0])
proj = (np.dot(a, b) / np.dot(b, b)) * b
print(f"Projection of {a} onto {b}: {proj}")

Q, R = np.linalg.qr(np.random.randn(3, 3))
print(f"Q is orthogonal: {np.allclose(Q @ Q.T, np.eye(3))}")
print(f"R is upper triangular: {np.allclose(R, np.triu(R))}")
```

### PyTorch -- 자동 미분이 붙은 벡터, 바로 텐서

```python
import torch

x = torch.randn(3, requires_grad=True)
y = torch.tensor([1.0, 0.0, 0.0])

similarity = torch.dot(x, y)
similarity.backward()

print(f"x = {x.data}")
print(f"y = {y.data}")
print(f"dot product = {similarity.item():.4f}")
print(f"d(dot)/dx = {x.grad}")
```

내적을 x에 대해 미분한 그래디언트는 그냥 y입니다. PyTorch가 이걸 자동으로 계산해 준 거죠. 신경망의 모든 연산은 이런 연산들 — 행렬 곱, 내적, 사영 — 을 조합해 만들어지고, 자동 미분(autodiff)이 그 모든 과정의 그래디언트를 추적합니다.

방금 여러분은 NumPy가 한 줄로 처리하는 일을 처음부터 직접 만들었습니다. 이제 후드 아래에서 무슨 일이 벌어지는지 아는 셈이죠.

## 출시하기

이 레슨이 만드는 산출물:
- `outputs/prompt-linear-algebra-tutor.md` -- AI 어시스턴트가 기하학적 직관으로 선형 대수를 가르치도록 돕는 프롬프트

## 연결고리

이 레슨의 모든 내용은 현대 AI의 구체적인 부분과 연결됩니다:

| 개념 | 등장하는 곳 |
|---------|------------------|
| 내적 | 트랜스포머의 어텐션 점수, RAG의 코사인 유사도 |
| 행렬 곱 | 모든 신경망 레이어, 모든 선형 변환 |
| 선형 독립 | 특성 선택, 다중공선성 회피 |
| 랭크 | 연립 방정식이 풀리는지 판단, LoRA(저랭크 적응) |
| 사영 | 선형 회귀(열 공간으로의 사영), PCA |
| 그람-슈미트 / QR | 수치 솔버, 고윳값 계산 |
| 정규 직교 기저 | 안정적인 수치 계산, 화이트닝 변환 |

LoRA는 특별히 짚고 넘어갈 가치가 있습니다. LoRA는 가중치 업데이트를 저랭크 행렬로 분해하는 방식으로 대규모 언어 모델(LLM)을 파인튜닝합니다. 4096x4096 가중치 행렬(1,600만 개 파라미터) 전체를 업데이트하는 대신, LoRA는 4096x16과 16x4096 크기의 두 행렬(13.1만 개 파라미터)만 업데이트합니다. 랭크 16이라는 제약은, LoRA가 가중치 업데이트가 4096차원 전체 공간 안의 16차원 부분 공간에 있다고 가정한다는 뜻입니다. 바로 선형 대수가 진짜 일을 해 내는 순간이죠.

## 연습 문제

1. 두 벡터 사이의 각도를 도 단위로 반환하는 `Vector.angle_between(other)`를 구현하세요
2. x좌표는 2배, y좌표는 3배로 만드는 2D 스케일링 행렬을 만들고, 벡터 [1, 1]에 적용해 보세요
3. 단어처럼 생긴 무작위 벡터 5개(차원 50)가 주어졌을 때, 코사인 유사도로 가장 비슷한 두 벡터를 찾아 보세요
4. 그람-슈미트 결과가 진짜 정규 직교인지 확인해 보세요: 모든 쌍의 내적이 0이고 모든 벡터의 크기가 1인지 검사합니다
5. 랭크가 2인 3x3 행렬을 만드세요. `rank()` 메서드로 검증한 뒤, 열들이 어떤 기하학적 대상을 채우는지 설명해 보세요
6. 벡터 [1, 2, 3]을 [1, 1, 1]에 사영해 보세요. 결과는 기하학적으로 무엇을 나타낼까요?

## 핵심 용어

| 용어 | 사람들의 말 | 실제 의미 |
|------|----------------|----------------------|
| 벡터 | "화살표" | n차원 공간의 점이나 방향을 나타내는 숫자 목록 |
| 행렬 | "숫자 표" | 벡터를 한 공간에서 다른 공간으로 대응시키는 변환 |
| 내적 | "곱하고 더하기" | 두 벡터가 얼마나 정렬돼 있는지의 척도 — 유사도 검색의 핵심 |
| 임베딩 | "AI 마법" | 무언가(단어, 이미지, 사용자)의 의미를 담은 벡터 |
| 선형 독립 | "서로 겹치지 않음" | 집합의 어떤 벡터도 다른 벡터들의 조합으로 표현될 수 없음 |
| 랭크 | "차원이 몇 개" | 행렬에서 선형 독립인 열(또는 행)의 개수 |
| 사영 | "그림자" | 한 벡터의, 다른 벡터 방향 성분 |
| 기저 | "좌표축" | 공간을 채우는 최소한의 독립 벡터 집합 |
| 정규 직교 | "수직인 단위 벡터들" | 서로 수직이고 각각 길이가 1인 벡터들 |
