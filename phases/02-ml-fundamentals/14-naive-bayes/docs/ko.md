# 나이브 베이즈

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> "순진한(naive)" 가정은 틀렸는데도 어쨌든 잘 동작합니다. 여기에 이 모델의 매력이 있습니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 2, 레슨 01~07(분류, 베이즈 정리)
**시간:** 약 75분

## 학습 목표

- 라플라스 스무딩을 적용해 텍스트 분류용 멀티노미얼 나이브 베이즈를 직접 구현할 수 있습니다
- 순진한 독립 가정이 수학적으로 틀렸음에도 실전에서는 올바른 클래스 순위를 만들어 내는 이유를 설명할 수 있습니다
- 멀티노미얼, 베르누이, 가우시안 나이브 베이즈 변형을 비교하고 특성(feature) 유형에 맞는 것을 고를 수 있습니다
- 고차원 희소 데이터에서 나이브 베이즈와 로지스틱 회귀를 비교하고, 그 안에서 작동하는 편향-분산 트레이드오프를 설명할 수 있습니다

## 문제 상황

텍스트를 분류해야 합니다. 이메일을 스팸/정상으로, 고객 리뷰를 긍정/부정으로, 고객 지원 티켓을 카테고리별로요. 특성은 수천 개(단어마다 하나씩)인데 학습 데이터는 부족합니다.

대부분의 분류기는 여기서 막힙니다. 로지스틱 회귀는 수천 개의 가중치를 안정적으로 추정하려면 충분한 샘플이 필요합니다. 결정 트리는 한 번에 단어 하나씩 분할하다가 심하게 과적합됩니다. 10,000차원에서의 KNN은 무의미합니다. 모든 점이 서로에게 똑같이 멀기 때문입니다.

나이브 베이즈는 이걸 처리합니다. 수학적으로 틀린 가정(클래스가 주어지면 모든 특성이 서로 독립이라는)을 하면서도, 텍스트 분류에서는 "더 똑똑한" 모델들을 이깁니다. 특히 학습 세트가 작을 때 그렇습니다. 데이터를 한 번만 훑고 학습이 끝납니다. 수백만 개의 특성으로 확장됩니다. 확률 추정치도 냅니다(다만 독립 가정 때문에 캘리브레이션이 자주 나쁩니다).

틀린 가정이 좋은 예측으로 이어지는 이유를 이해하면 머신러닝의 근본적인 한 가지를 배우게 됩니다. 최고의 모델은 가장 올바른 모델이 아니라, 여러분의 데이터에 가장 좋은 편향-분산 트레이드오프를 가진 모델이라는 것이죠.

## 개념

### 베이즈 정리(빠른 복습)

베이즈 정리는 조건부 확률을 뒤집습니다:

```
P(class | features) = P(features | class) * P(class) / P(features)
```

우리가 원하는 것은 `P(class | features)`입니다. 문서에 들어 있는 단어들이 주어졌을 때 그 문서가 어떤 클래스에 속할 확률이죠. 다음으로 계산할 수 있습니다:
- `P(features | class)` -- 이 클래스의 문서에서 이런 단어들이 보일 가능도(likelihood)
- `P(class)` -- 클래스의 사전 확률(전반적으로 스팸이 얼마나 흔한가?)
- `P(features)` -- 증거(evidence). 모든 클래스에 대해 같으므로 비교할 때는 무시할 수 있습니다

`P(class | features)`가 가장 높은 클래스가 이깁니다.

### 순진한 독립 가정

`P(features | class)`를 정확히 계산하려면 모든 특성의 결합 확률을 추정해야 합니다. 어휘가 10,000 단어라면 2^10,000가지 조합에 대한 분포를 추정해야 합니다. 불가능하죠.

순진한 가정: 클래스가 주어지면 모든 특성은 조건부 독립입니다.

```
P(w1, w2, ..., wn | class) = P(w1 | class) * P(w2 | class) * ... * P(wn | class)
```

불가능한 결합 분포 하나 대신, 특성마다 하나씩인 단순한 분포 n개를 추정합니다. 각각은 개수 세기만 하면 됩니다.

이 가정은 명백히 틀렸습니다. 어떤 문서에서도 "machine"과 "learning"은 독립이 아닙니다. 하지만 분류기에는 정확한 확률 추정치가 필요하지 않습니다. 필요한 것은 정확한 순위입니다. 즉 어느 클래스의 확률이 가장 높은지요. 독립 가정은 체계적인 오류를 만들지만, 그 오류가 모든 클래스에 비슷하게 작용하기 때문에 순위는 옳게 유지됩니다.

### 그래도 잘 동작하는 이유

세 가지 이유입니다:

1. **캘리브레이션보다 순위.** 분류에는 1순위 클래스만 맞으면 됩니다. 실제 확률이 0.7일 때 P(spam) = 0.99999라고 나와도 분류기는 여전히 스팸을 올바르게 고릅니다. 정확한 확률이 필요 없습니다. 올바른 승자가 필요한 겁니다.

2. **높은 편향, 낮은 분산.** 독립 가정은 강한 사전 지식입니다. 모델을 크게 구속해서 과적합을 막아 줍니다. 학습 데이터가 부족할 때는 약간 틀리지만 안정적인 모델이, 이론적으로 옳지만 극도로 불안정한 모델을 이깁니다. 편향-분산 트레이드오프의 실전 작동 예입니다.

3. **특성의 중복이 상쇄됨.** 상관된 특성들은 중복된 증거를 제공합니다. 분류기는 이 증거를 두 번 셉니다만, 올바른 클래스에 대해서도 똑같이 두 번 셉니다. "machine"과 "learning"이 항상 같이 나온다면 둘 다 "tech" 클래스의 증거입니다. NB는 두 번 세지만, 올바른 클래스에 대해 두 번 셉니다.

네 번째 실용적인 이유: 나이브 베이즈는 극도로 빠릅니다. 학습은 빈도를 세는 데이터 한 번 훑기이고, 예측은 행렬 곱입니다. 백만 개의 문서를 몇 초 만에 학습할 수 있습니다. 이 속도 덕분에 더 빨리 반복하고, 더 많은 특성 집합을 시도하고, 느린 모델들보다 더 많은 실험을 돌릴 수 있습니다.

### 단계별 수학

구체적인 예제를 따라가 봅시다. 클래스가 두 개 있다고 합시다: 스팸과 정상. 어휘는 세 단어: "free", "money", "meeting".

학습 데이터:
- 스팸 이메일은 "free" 80회, "money" 60회, "meeting" 10회 언급(총 150 단어)
- 정상 이메일은 "free" 5회, "money" 10회, "meeting" 100회 언급(총 115 단어)
- 이메일의 40%가 스팸, 60%가 정상

라플라스 스무딩(alpha=1)을 적용하면:

```
P(free | spam)    = (80 + 1) / (150 + 3) = 81/153 = 0.529
P(money | spam)   = (60 + 1) / (150 + 3) = 61/153 = 0.399
P(meeting | spam) = (10 + 1) / (150 + 3) = 11/153 = 0.072

P(free | not-spam)    = (5 + 1) / (115 + 3) = 6/118 = 0.051
P(money | not-spam)   = (10 + 1) / (115 + 3) = 11/118 = 0.093
P(meeting | not-spam) = (100 + 1) / (115 + 3) = 101/118 = 0.856
```

새 이메일에 "free"(2회), "money"(1회), "meeting"(0회)이 포함되어 있습니다.

```
log P(spam | email) = log(0.4) + 2*log(0.529) + 1*log(0.399) + 0*log(0.072)
                    = -0.916 + 2*(-0.637) + (-0.919) + 0
                    = -3.109

log P(not-spam | email) = log(0.6) + 2*log(0.051) + 1*log(0.093) + 0*log(0.856)
                        = -0.511 + 2*(-2.976) + (-2.375) + 0
                        = -8.838
```

스팸이 큰 차이로 이깁니다. "free"가 두 번 나온 것은 스팸의 강한 증거입니다. "meeting"이 등장하지 않은 것은 두 로그 합 어디에도 0을 기여합니다(0 * log(P)) -- 멀티노미얼 NB에서는 없는 단어는 아무 영향이 없습니다. 단어의 부재를 명시적으로 모델링하는 것은 베르누이 NB입니다.

### 세 가지 변형

나이브 베이즈에는 세 가지 맛이 있습니다. 각각 `P(feature | class)`를 다르게 모델링합니다.

#### 멀티노미얼 나이브 베이즈

각 특성을 개수로 모델링합니다. 특성이 단어 빈도나 TF-IDF 값인 텍스트 데이터에 가장 좋습니다.

```
P(word_i | class) = (클래스 내 word_i 개수 + alpha) / (클래스 내 총 단어 수 + alpha * 어휘 크기)
```

`alpha`는 라플라스 스무딩입니다(아래에서 설명). 이 변형이 텍스트 분류의 일등 공신입니다.

#### 가우시안 나이브 베이즈

각 특성을 정규 분포로 모델링합니다. 연속형 특성에 가장 좋습니다.

```
P(x_i | class) = (1 / sqrt(2 * pi * var)) * exp(-(x_i - mean)^2 / (2 * var))
```

클래스마다 특성별로 자기만의 평균과 분산을 갖습니다. 특성이 각 클래스 안에서 실제로 종 모양 분포를 따를 때 잘 맞습니다.

#### 베르누이 나이브 베이즈

각 특성을 이진값(있음/없음)으로 모델링합니다. 짧은 텍스트나 이진 특성 벡터에 가장 좋습니다.

```
P(word_i | class) = (word_i를 포함한 클래스 내 문서 수 + alpha) / (클래스 내 총 문서 수 + 2 * alpha)
```

멀티노미얼과 달리 베르누이는 단어의 부재를 명시적으로 벌점화합니다. "free"가 보통 스팸에 나오는데 이 이메일에는 없다면, 베르누이는 그것을 스팸에 반대하는 증거로 셉니다.

### 변형별 사용 시점

| 변형 | 특성 유형 | 가장 잘 맞는 것 | 예 |
|---------|-------------|----------|---------|
| 멀티노미얼 | 개수 또는 빈도 | 텍스트 분류, bag-of-words | 이메일 스팸, 주제 분류 |
| 가우시안 | 연속값 | 정규 분포 비슷한 특성의 표 형태 데이터 | 붓꽃 분류, 센서 데이터 |
| 베르누이 | 이진(0/1) | 짧은 텍스트, 이진 특성 벡터 | SMS 스팸, 존재/부재 특성 |

### 라플라스 스무딩

어떤 단어가 테스트 데이터에는 있는데 특정 클래스의 학습 데이터에는 한 번도 안 나왔다면 어떻게 될까요?

스무딩이 없으면: `P(word | class) = 0/N = 0`. 곱 전체에 0이 하나만 곱해져도 `P(class | features) = 0`이 됩니다. 다른 증거가 아무리 많아도 본 적 없는 단어 하나가 예측 전체를 파괴합니다.

라플라스 스무딩은 모든 특성 개수에 작은 값 `alpha`(보통 1)를 더합니다:

```
P(word_i | class) = (count(word_i, class) + alpha) / (클래스 내 총 단어 수 + alpha * 어휘 크기)
```

alpha=1이면 모든 단어가 최소한 아주 작은 확률은 갖게 됩니다. 테스트 이메일에 "discombobulate"라는 단어가 나와도 스팸 확률을 죽이지 못합니다. 이 스무딩에는 베이지안 해석이 있습니다. 단어 분포에 균등 디리클레 사전분포를 놓는 것과 같습니다.

alpha가 크면 스무딩이 강합니다(더 균등한 분포). alpha가 작으면 모델이 데이터를 더 신뢰합니다. alpha는 여러분이 튜닝하는 하이퍼파라미터입니다.

alpha의 효과:

| Alpha | 효과 | 사용 시점 |
|-------|--------|-------------|
| 0.001 | 사실상 스무딩 없음, 데이터 신뢰 | 아주 큰 학습 세트, 미지 특성이 없을 것으로 예상될 때 |
| 0.1 | 가벼운 스무딩 | 큰 학습 세트 |
| 1.0 | 표준 라플라스 스무딩 | 기본 시작점 |
| 10.0 | 강한 스무딩, 분포를 평평하게 | 아주 작은 학습 세트, 미지 특성이 많을 것으로 예상될 때 |

### 로그 공간 계산

1보다 작은 확률 수백 개를 곱하면 부동소수점 언더플로(underflow)가 일어납니다. 실제 값은 아주 작은 양수인데 부동소수점에서는 곱이 0이 되어 버리죠.

해법: 로그 공간에서 작업합니다. 확률을 곱하는 대신 로그를 더합니다:

```
log P(class | x1, x2, ..., xn) = log P(class) + sum_i log P(xi | class)
```

이렇게 하면 예측이 내적(dot product)이 됩니다:

```
log_scores = X @ log_feature_probs.T + log_class_priors
prediction = argmax(log_scores)
```

행렬 곱입니다. 나이브 베이즈 예측이 그렇게 빠른 이유가 바로 이것입니다. 단층 선형 모델과 같은 연산입니다.

### 나이브 베이즈 vs 로지스틱 회귀

둘 다 텍스트용 선형 분류기입니다. 차이는 무엇을 모델링하느냐에 있습니다.

| 측면 | 나이브 베이즈 | 로지스틱 회귀 |
|--------|------------|-------------------|
| 유형 | 생성 모델(P(X\|Y) 모델링) | 판별 모델(P(Y\|X) 모델링) |
| 학습 | 빈도를 셈 | 손실 함수 최적화 |
| 적은 데이터 | 더 좋음(강한 사전 지식이 도움) | 더 나쁨(가중치 추정에 부족) |
| 많은 데이터 | 더 나쁨(틀린 가정이 발목) | 더 좋음(유연한 결정 경계) |
| 특성 | 독립 가정 | 상관 처리 가능 |
| 속도 | 한 번 훑기, 매우 빠름 | 반복 최적화 |
| 캘리브레이션 | 확률이 부정확 | 확률이 더 나음 |

경험 법칙: 나이브 베이즈로 시작하세요. 데이터가 충분하고 NB가 한계에 도달하면 로지스틱 회귀로 전환합니다.

### 분류 파이프라인

```mermaid
flowchart LR
    A[원시 텍스트] --> B[토큰화]
    B --> C[어휘 구축]
    C --> D[단어 빈도 세기]
    D --> E[스무딩 적용]
    E --> F[로그 확률 계산]
    F --> G[예측: 단어들이 주어졌을 때 P class 최대화]

    style A fill:#f9f,stroke:#333
    style G fill:#9f9,stroke:#333
```

실전에서는 부동소수점 언더플로를 피하려고 로그 공간에서 작업합니다. 작은 확률 여러 개를 곱하는 대신 로그를 더합니다:

```
log P(class | features) = log P(class) + sum_i log P(feature_i | class)
```

```figure
naive-bayes
```

## 직접 만들기

`code/naive_bayes.py`의 코드는 MultinomialNB와 GaussianNB를 둘 다 직접 구현합니다.

### MultinomialNB

직접 구현한 내용:

1. **fit(X, y)**: 클래스마다 각 특성의 빈도를 셉니다. 라플라스 스무딩을 더하고 로그 확률을 계산합니다. 클래스 사전 확률(클래스 빈도의 로그)을 저장합니다.

2. **predict_log_proba(X)**: 샘플마다 모든 클래스에 대해 log P(class) + log P(feature_i | class)의 합을 계산합니다. 이는 행렬 곱입니다: X @ log_probs.T + log_priors.

3. **predict(X)**: 로그 확률이 가장 높은 클래스를 반환합니다.

```python
class MultinomialNB:
    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y):
        classes = np.unique(y)
        n_classes = len(classes)
        n_features = X.shape[1]

        self.classes_ = classes
        self.class_log_prior_ = np.zeros(n_classes)
        self.feature_log_prob_ = np.zeros((n_classes, n_features))

        for i, c in enumerate(classes):
            X_c = X[y == c]
            self.class_log_prior_[i] = np.log(X_c.shape[0] / X.shape[0])
            counts = X_c.sum(axis=0) + self.alpha
            self.feature_log_prob_[i] = np.log(counts / counts.sum())

        return self
```

핵심 통찰: 피팅이 끝나면 예측은 그저 행렬 곱에 편향을 더하는 것입니다. 나이브 베이즈가 그렇게 빠른 이유입니다.

### GaussianNB

연속형 특성에는 클래스별, 특성별로 평균과 분산을 추정합니다:

```python
class GaussianNB:
    def __init__(self):
        pass

    def fit(self, X, y):
        classes = np.unique(y)
        self.classes_ = classes
        self.means_ = np.zeros((len(classes), X.shape[1]))
        self.vars_ = np.zeros((len(classes), X.shape[1]))
        self.priors_ = np.zeros(len(classes))

        for i, c in enumerate(classes):
            X_c = X[y == c]
            self.means_[i] = X_c.mean(axis=0)
            self.vars_[i] = X_c.var(axis=0) + 1e-9
            self.priors_[i] = X_c.shape[0] / X.shape[0]

        return self
```

예측은 특성별로 가우시안 PDF를 계산해 특성들에 걸쳐 곱합니다(로그 공간에서는 더합니다).

### 데모: 텍스트 분류

코드는 두 클래스(기술 아티클 vs 스포츠 아티클)를 시뮬레이션하는 합성 bag-of-words 데이터를 만듭니다. 각 클래스는 서로 다른 단어 빈도 분포를 갖습니다. MultinomialNB는 단어 개수로 분류합니다.

합성 데이터의 작동 방식: 200개의 "단어"(특성 컬럼)를 만듭니다. 0~39번 단어는 기술 아티클에서 빈도가 높고 스포츠에서 낮습니다. 80~119번 단어는 스포츠에서 높고 기술에서 낮습니다. 40~79번 단어는 양쪽에서 중간 빈도입니다. 이렇게 하면 어떤 단어는 강한 클래스 지시자이고 어떤 단어는 노이즈인 현실적인 시나리오가 만들어집니다.

### 데모: 연속형 특성

코드는 붓꽃(Iris) 비슷한 데이터(3클래스, 4특성, 가우시안 군집)를 만듭니다. GaussianNB는 클래스별 평균과 분산으로 분류합니다. 각 클래스는 다른 중심(평균 벡터)과 다른 퍼짐(분산)을 갖는데, 측정값이 카테고리 사이에 체계적으로 달라지는 실제 데이터를 흉내 낸 것입니다.

코드는 또한 다음을 보여 줍니다:
- **스무딩 비교:** 다른 alpha 값으로 MultinomialNB를 학습시켜 스무딩 강도가 정확도에 미치는 영향을 보여 줍니다.
- **학습 크기 실험:** 학습 데이터가 20개에서 1600개로 늘 때 NB 정확도가 어떻게 좋아지는지 보여 줍니다. NB는 샘플이 아주 적어도 그럴듯한 정확도에 도달합니다. 이것이 NB의 최대 장점입니다.
- **오차 행렬(confusion matrix):** 클래스별 정밀도, 재현율, F1 점수로 NB가 어디서 틀리는지 보여 줍니다.

### 예측 속도

나이브 베이즈의 예측은 행렬 곱입니다. d개 특성, k개 클래스에 대해 n개 샘플의 경우:
- MultinomialNB: 행렬 곱 한 번 (n x d) @ (d x k) = O(n * d * k)
- GaussianNB: d특성에 걸친 가우시안 PDF 평가 n * k회 = O(n * d * k)

둘 다 모든 차원에서 선형입니다. KNN(모든 학습 점과의 거리 계산 필요)이나 RBF 커널 SVM(모든 서포트 벡터에 대해 커널 평가 필요)과 비교해 보세요. NB는 예측 시점에 자릿수 단위로 빠릅니다.

## 실전 활용

sklearn으로는 두 변형 모두 한 줄입니다:

```python
from sklearn.naive_bayes import GaussianNB, MultinomialNB

gnb = GaussianNB()
gnb.fit(X_train, y_train)
print(f"GaussianNB accuracy: {gnb.score(X_test, y_test):.3f}")

mnb = MultinomialNB(alpha=1.0)
mnb.fit(X_train_counts, y_train)
print(f"MultinomialNB accuracy: {mnb.score(X_test_counts, y_test):.3f}")
```

sklearn으로 텍스트 분류하기:

```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

text_clf = Pipeline([
    ("vectorizer", CountVectorizer()),
    ("classifier", MultinomialNB(alpha=1.0)),
])

text_clf.fit(train_texts, train_labels)
accuracy = text_clf.score(test_texts, test_labels)
```

`naive_bayes.py`의 코드는 직접 구현한 것과 sklearn을 같은 데이터에서 비교해 정확성을 검증합니다.

### 나이브 베이즈와 TF-IDF

원시 단어 개수는 모든 단어에 등장 횟수만큼 똑같은 가중치를 줍니다. 하지만 "the", "is" 같은 흔한 단어는 모든 클래스에 자주 나오므로 정보가 없습니다. TF-IDF(Term Frequency - Inverse Document Frequency)는 흔한 단어의 가중치를 낮추고 희귀하면서 판별력 있는 단어의 가중치를 높입니다.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

text_clf = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("classifier", MultinomialNB(alpha=0.1)),
])
```

TF-IDF 값은 음수가 아니므로 MultinomialNB와 함께 쓸 수 있습니다. TF-IDF + MultinomialNB 조합은 텍스트 분류에서 가장 강력한 베이스라인 중 하나입니다. 학습 샘플이 10,000개 미만인 데이터셋에서는 더 복잡한 모델들을 자주 이깁니다.

### 짧은 텍스트에는 BernoulliNB

짧은 텍스트(트윗, SMS, 채팅 메시지)에는 BernoulliNB가 MultinomialNB를 이길 수 있습니다. 짧은 텍스트는 단어 개수가 적어서 MultinomialNB가 의존하는 빈도 정보가 노이즈가 많습니다. BernoulliNB는 있음/없음만 보는데, 짧은 텍스트에서는 이쪽이 더 신뢰할 만합니다.

```python
from sklearn.naive_bayes import BernoulliNB
from sklearn.feature_extraction.text import CountVectorizer

text_clf = Pipeline([
    ("vectorizer", CountVectorizer(binary=True)),
    ("classifier", BernoulliNB(alpha=1.0)),
])
```

CountVectorizer의 `binary=True` 플래그는 모든 개수를 0/1로 바꿉니다. 이것이 없어도 BernoulliNB는 동작하지만, 원래 설계되지 않은 개수 값을 보게 됩니다.

### NB 확률 캘리브레이션

NB의 확률은 캘리브레이션이 나쁩니다. NB가 P(spam) = 0.95라고 말할 때 실제 확률은 0.7일 수 있습니다. 신뢰할 수 있는 확률 추정치가 필요하다면(예: 임계값 설정이나 다른 모델과 결합), sklearn의 CalibratedClassifierCV를 쓰세요:

```python
from sklearn.calibration import CalibratedClassifierCV

calibrated_nb = CalibratedClassifierCV(MultinomialNB(), cv=5, method="sigmoid")
calibrated_nb.fit(X_train, y_train)
proba = calibrated_nb.predict_proba(X_test)
```

이것은 교차 검증을 사용해 NB의 원시 점수 위에 로지스틱 회귀를 피팅합니다. 결과 확률은 실제 클래스 빈도에 훨씬 가까워집니다.

### 흔한 함정

1. **음수 특성 값.** MultinomialNB는 음수가 아닌 특성을 요구합니다. 음수 값이 있다면(특정 설정의 TF-IDF나 표준화된 특성 등) GaussianNB를 대신 쓰거나, 특성을 양수로 이동하세요.

2. **분산이 0인 특성.** GaussianNB는 분산으로 나눕니다. 어떤 특성이 클래스 내에서 분산이 0이면(모든 값이 동일) 확률 계산이 깨집니다. 코드는 이를 막으려고 모든 분산에 작은 스무딩 항(1e-9)을 더합니다.

3. **클래스 불균형.** 이메일의 99%가 정상이라면 사전 확률 P(not-spam) = 0.99가 너무 강해서 가능도 증거를 압도합니다. 클래스 사전 확률을 수동으로 정하거나 sklearn의 class_prior 파라미터를 쓸 수 있습니다.

4. **특성 스케일링.** MultinomialNB는 스케일링이 필요 없습니다(개수로 동작). GaussianNB도 스케일링이 필요 없습니다(특성별 통계를 추정). 특성 스케일에 민감한 로지스틱 회귀와 SVM에 비해 이것은 장점입니다.

## 출시하기

이 레슨이 만드는 것:
- `outputs/skill-naive-bayes-chooser.md` -- 올바른 NB 변형을 고르는 의사결정 스킬
- `code/naive_bayes.py` -- 직접 구현한 MultinomialNB와 GaussianNB, sklearn 비교 포함

### 나이브 베이즈가 실패하는 경우

독립 가정이 틀린 확률이 아니라 틀린 순위를 낼 때 NB는 실패합니다. 이런 경우입니다:

1. **강한 특성 상호작용.** 클래스가 두 특성의 조합에 의존하고 각각 단독으로는 의존하지 않을 때(XOR 비슷한 패턴), NB는 그것을 완전히 놓칩니다. 각 특성 단독으로는 증거가 없고, NB는 그것들을 비선형적으로 결합할 수 없습니다.

2. **서로 반대 증거를 주는 강하게 상관된 특성.** 특성 A는 "스팸"이라고, 특성 B는 "정상"이라고 하는데 A와 B가 완벽하게 상관되어 있다면(현실에서 항상 같은 방향), NB는 실제로는 없는 충돌 증거를 보게 됩니다.

3. **아주 큰 학습 세트.** 데이터가 충분하면 로지스틱 회귀 같은 판별 모델이 진짜 결정 경계를 배워 NB를 이깁니다. 적은 데이터에서 도움이 됐던 독립 가정이 이제는 모델의 발목을 잡습니다.

실전에서 이런 실패 모드는 텍스트 분류에서는 드뭅니다. 텍스트 특성은 개수가 많고 개별적으로는 약하며, 독립 가정의 오류는 상쇄되는 경향이 있습니다. 강하게 상관된 특성이 몇 개 있는 표 형태 데이터라면 로지스틱 회귀나 트리 기반 모델을 먼저 고려하세요.

## 연습 문제

1. **스무딩 실험.** 텍스트 데이터에서 alpha를 0.01, 0.1, 1.0, 10.0, 100.0으로 바꿔 가며 MultinomialNB를 학습시키세요. 정확도 vs alpha 그래프를 그리세요. 성능은 어디서 정점을 찍나요? 아주 큰 alpha가 나쁜 이유는 무엇인가요?

2. **특성 독립 검증.** 실제 텍스트 데이터셋을 가져오세요. 명백히 상관된 두 단어("machine"과 "learning")를 고릅니다. P(word1 | class) * P(word2 | class)를 계산하고 P(word1 AND word2 | class)와 비교하세요. 독립 가정은 얼마나 틀렸나요? 분류 정확도에 영향을 주나요?

3. **베르누이 구현.** 코드에 BernoulliNB 클래스를 추가하세요. bag-of-words를 이진값(있음/없음)으로 바꾸고 텍스트 데이터에서 MultinomialNB와 정확도를 비교하세요. 언제 베르누이가 이기나요?

4. **NB vs 로지스틱 회귀.** 텍스트 데이터에서 둘 다 학습시키세요. 학습 샘플 100개에서 시작해 10,000개까지 늘립니다. 둘 다의 정확도 vs 학습 세트 크기 그래프를 그리세요. 어느 시점에 로지스틱 회귀가 나이브 베이즈를 추월하나요?

5. **스팸 필터.** 완전한 스팸 분류기를 만드세요: 원시 이메일 텍스트 토큰화, 어휘 구축, bag-of-words 특성 생성, MultinomialNB 학습, 정밀도와 재현율로 평가(정확도만이 아니라 -- 왜 그런지 생각해 보세요).

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| 나이브 베이즈 | "단순한 확률 분류기" | 베이즈 정리를 적용하되, 클래스가 주어지면 특성들이 조건부 독립이라고 가정하는 분류기 |
| 조건부 독립 | "특성들이 서로 영향을 주지 않음" | P(A, B \| C) = P(A \| C) * P(B \| C) -- C를 알고 나면 B를 아는 것이 A에 대해 새로 줄 정보가 없음 |
| 라플라스 스무딩 | "1 더하기 스무딩" | 모든 특성 개수에 작은 값을 더해 확률 0이 예측을 지배하지 않게 하는 것 |
| 사전 확률(prior) | "데이터를 보기 전의 믿음" | P(class) -- 어떤 특성도 관찰하기 전 각 클래스의 확률 |
| 가능도(likelihood) | "데이터가 얼마나 잘 맞는가" | P(features \| class) -- 클래스를 알고 있을 때 이 특성들이 관찰될 확률 |
| 사후 확률(posterior) | "데이터를 본 후의 믿음" | P(class \| features) -- 특성을 관찰한 뒤 갱신된 클래스의 확률 |
| 생성 모델 | "데이터가 생성되는 방식을 모델링" | P(X \| Y)와 P(Y)를 학습한 뒤 베이즈 정리로 P(Y \| X)를 구하는 모델 |
| 판별 모델 | "결정 경계를 모델링" | X가 생성되는 방식을 모델링하지 않고 P(Y \| X)를 직접 학습하는 모델 |
| 로그 확률 | "언더플로 회피" | P 대신 log P로 작업해 작은 수 여러 개의 곱이 부동소수점에서 0이 되는 것을 방지 |

## 더 읽을거리

- [scikit-learn Naive Bayes docs](https://scikit-learn.org/stable/modules/naive_bayes.html) -- 수학적 세부사항이 포함된 세 가지 변형 모두
- [McCallum and Nigam, A Comparison of Event Models for Naive Bayes Text Classification (1998)](https://www.cs.cmu.edu/~knigam/papers/multinomial-aaaiws98.pdf) -- 텍스트에서 멀티노미얼 vs 베르누이의 클래식한 비교
- [Rennie et al., Tackling the Poor Assumptions of Naive Bayes Text Classifiers (2003)](https://people.csail.mit.edu/jrennie/papers/icml03-nb.pdf) -- 텍스트용 NB 개선
- [Ng and Jordan, On Discriminative vs. Generative Classifiers (2001)](https://ai.stanford.edu/~ang/papers/nips01-discriminativegenerative.pdf) -- 적은 데이터에서 NB가 LR보다 빨리 수렴함을 증명
