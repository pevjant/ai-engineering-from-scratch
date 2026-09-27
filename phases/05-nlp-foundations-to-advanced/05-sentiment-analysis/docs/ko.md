> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 감성 분석 (Sentiment Analysis)

> NLP의 대표 과제입니다. 고전 텍스트 분류에 대해 알아야 할 것들의 대부분이 바로 여기서 등장합니다.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 02(BoW + TF-IDF), 페이즈 2 · 14(나이브 베이즈)
**소요 시간:** 약 75분

## 해결할 문제

"The food was not great." 긍정일까요, 부정일까요?

감성 분석은 쉬워 보입니다. 리뷰어가 무언가를 좋아했는지 싫어했는지 말했으니, 그 문장에 레이블을 붙이면 되겠죠. 그런데 이 과제가 NLP의 대표 과제가 된 이유는, 쉬워 보이는 사례 하나하나가 까다로운 사례를 숨기고 있기 때문입니다. 부정어는 의미를 뒤집습니다. 비꼼(반어)은 의미를 정반대로 만듭니다. "Not bad at all"은 부정적인 단어가 두 개나 들었는데도 긍정입니다. 이모지는 주변 텍스트보다 더 강한 신호를 담습니다. 도메인 어휘도 중요합니다(음악 리뷰의 `tight`와 패션 리뷰의 `tight`는 다른 뜻입니다).

감성 분석은 고전 NLP를 위한 실습 실험실입니다. 순진해 보이는 베이스라인마다 특유의 실패 모드가 있는 이유를 이해하면, 더 정교한 모델이 왜 발명됐는지도 이해하게 됩니다. 이 레슨은 나이브 베이즈 베이스라인을 직접 만들고, 로지스틱 회귀를 얹고, 프로덕션(운영 환경) 감성 분석을 컴플라이언스 등급의 문제로 바꿔 놓는 함정들에 이름을 붙여 줍니다.

## 핵심 개념

고전적인 감성 분석은 두 단계짜리 레시피입니다.

1. **표현합니다(Represent).** 텍스트를 특성(feature) 벡터로 바꿉니다. BoW, TF-IDF, n-gram 중 하나를 씁니다.
2. **분류합니다(Classify).** 레이블이 달린 예시들로 선형 모델(나이브 베이즈, 로지스틱 회귀, SVM)을 학습합니다.

나이브 베이즈는 "그런데도 돌아가는" 모델 중 가장 단순한 모델입니다. 레이블이 주어졌을 때 모든 특성이 서로 독립이라고 가정합니다. 등장 횟수를 세서 `P(word | positive)`와 `P(word | negative)`를 추정하고, 추론 때는 그 확률들을 곱합니다. 이 "순진한(naive)" 독립 가정은 터무니없이 틀렸는데도 결과는 놀랄 만큼 강력합니다. 이유는 이렇습니다. 텍스트 특성은 희소(sparse)하고 데이터도 적당한 수준일 때, 분류기에게 중요한 것은 각 단어가 어느 쪽으로 기우는지이지 얼마나 크게 기우는지가 아닙니다.

로지스틱 회귀는 독립 가정이 빚는 문제를 고쳐 줍니다. 특성마다 가중치를 학습하는데, 음(-)의 가중치도 가능합니다. `not good`이 바이그램 특성으로 잡히면 음의 가중치를 받습니다. 나이브 베이즈는 한 번도 레이블된 적 없는 바이그램에는 이런 일을 해 줄 수 없습니다.

```figure
sentiment-logits
```

## 만들어 보기

### 단계 1: 실제로 쓸 만한 미니 데이터셋

```python
POSITIVE = [
    "absolutely loved this movie",
    "beautiful cinematography and a great story",
    "one of the best films of the year",
    "brilliant acting from the lead",
    "heartwarming and funny",
]

NEGATIVE = [
    "boring and far too long",
    "not worth your time",
    "the plot made no sense",
    "terrible acting, awful script",
    "i want my two hours back",
]
```

일부러 작게 만든 데이터셋입니다. 실제 작업에서는 수만 개의 예시(IMDb, SST-2, Yelp polarity)를 씁니다. 하지만 수학은 완전히 같습니다.

### 단계 2: 다항 나이브 베이즈 직접 구현하기

```python
import math
from collections import Counter


def train_nb(docs_by_class, vocab, alpha=1.0):
    class_priors = {}
    class_word_probs = {}
    total_docs = sum(len(d) for d in docs_by_class.values())

    for cls, docs in docs_by_class.items():
        class_priors[cls] = len(docs) / total_docs
        counts = Counter()
        for doc in docs:
            for token in doc:
                counts[token] += 1
        total = sum(counts.values()) + alpha * len(vocab)
        class_word_probs[cls] = {
            w: (counts[w] + alpha) / total for w in vocab
        }
    return class_priors, class_word_probs


def predict_nb(doc, class_priors, class_word_probs):
    scores = {}
    for cls in class_priors:
        s = math.log(class_priors[cls])
        for token in doc:
            if token in class_word_probs[cls]:
                s += math.log(class_word_probs[cls][token])
        scores[cls] = s
    return max(scores, key=scores.get)
```

가산 스무딩(alpha=1.0)은 라플라스 스무딩입니다. 이게 없으면 어떤 클래스에서 한 번도 본 적 없는 단어의 확률이 0이 되어 로그가 폭발합니다. 실무에서는 `alpha=0.01`이 흔하고, `alpha=1.0`은 교육용 기본값입니다.

### 단계 3: 로지스틱 회귀 직접 구현하기

```python
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def train_lr(X, y, epochs=500, lr=0.05, l2=0.01):
    n_features = X.shape[1]
    w = np.zeros(n_features)
    b = 0.0
    for _ in range(epochs):
        logits = X @ w + b
        preds = sigmoid(logits)
        err = preds - y
        grad_w = X.T @ err / len(y) + l2 * w
        grad_b = err.mean()
        w -= lr * grad_w
        b -= lr * grad_b
    return w, b


def predict_lr(X, w, b):
    return (sigmoid(X @ w + b) >= 0.5).astype(int)
```

여기서는 L2 정규화가 중요합니다. 텍스트 특성은 희소하기 때문에, L2가 없으면 모델이 학습 예시를 그냥 외워 버립니다. `0.01`에서 시작해서 조정해 나가세요.

### 단계 4: 부정 처리하기(실패 모드 다루기)

"not good"과 "not bad"를 생각해 보세요. BoW 분류기는 `{not, good}`과 `{not, bad}`만 보고, 학습 데이터에서 더 자주 나온 쪽으로부터 배웁니다. 바이그램 분류기는 `not_good`과 `not_bad`을 서로 다른 특성으로 보고 각각 학습합니다. 보통은 이 정도면 충분합니다.

바이그램을 쓸 수 없을 때 통하는 더 투박한 해법이 **부정 범위 지정(negation scoping)**입니다. 부정어 다음에 오는 토큰들에, 다음 문장부호가 나올 때까지 `NOT_` 접두어를 붙입니다.

```python
NEGATION_WORDS = {"not", "no", "never", "nor", "none", "nothing", "neither"}
NEGATION_TERMINATORS = {".", "!", "?", ",", ";"}


def apply_negation(tokens):
    out = []
    negate = False
    for token in tokens:
        if token in NEGATION_TERMINATORS:
            negate = False
            out.append(token)
            continue
        if token in NEGATION_WORDS:
            negate = True
            out.append(token)
            continue
        out.append(f"NOT_{token}" if negate else token)
    return out
```

```python
>>> apply_negation(["not", "good", "at", "all", ".", "but", "funny"])
['not', 'NOT_good', 'NOT_at', 'NOT_all', '.', 'but', 'funny']
```

이제 `good`과 `NOT_good`은 서로 다른 특성이 됩니다. 분류기는 둘에 정반대의 가중치를 줄 수 있죠. 전처리 세 줄로 감성 벤치마크에서 측정 가능한 정확도 상승을 얻습니다.

### 단계 5: 진짜 중요한 평가 지표

클래스가 불균형하면 정확도만 보는 것은 오해를 부릅니다. 실제 감성 코퍼스는 대개 긍정이 70~80%이거나 부정이 70~80%입니다. 무조건 다수 클래스만 찍는 분류기도 정확도 80%를 받지만 전혀 쓸모가 없죠. 다음 항목은 모두 보고해야 합니다.

- **클래스별 정밀도와 재현율.** 클래스마다 한 쌍씩 나옵니다. 매크로 평균을 내면 클래스 균형을 존중하는 숫자 하나를 얻습니다.
- **매크로 F1(불균형 데이터의 1차 지표).** 클래스별 F1 점수의 평균으로, 모든 클래스를 똑같은 가중치로 둡니다. 클래스가 불균형할 때는 정확도 대신 이것을 쓰세요.
- **가중 F1(대안).** 매크로와 같지만 클래스 빈도로 가중합니다. 불균형 자체가 비즈니스적으로 의미가 있을 때는 매크로 F1과 함께 보고하세요.
- **오차 행렬(confusion matrix).** 날카운트 그대로입니다. 어떤 스칼라 지표든 믿기 전에 반드시 들여다보세요. 모델이 어떤 클래스 쌍을 헷갈리는지 드러납니다.
- **클래스별 오류 샘플.** 클래스당 틀린 예측 5개를 뽑아 직접 읽어 보세요. 실제 오류를 읽는 일을 대신해 줄 것은 없습니다.

극심하게 불균형한 데이터(비율이 95:5를 넘을 때)에서는 정확도 대신 **AUROC**와 **AUPRC**를 보고하세요. AUPRC가 소수 클래스에 더 민감한데, 보통 우리가 진짜 신경 쓰는 것이 바로 소수 클래스입니다(스팸, 사기, 드문 감성).

**흔히 저지르는 버그.** 불균형 데이터에서 매크로 F1 대신 마이크로 F1을 보고하면, 다수 클래스가 숫자를 지배하는 바람에 높아만 보이는 값이 나옵니다. 매크로 F1은 소수 클래스 성능을 반드시 보게 만듭니다.

```python
def evaluate(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": precision, "recall": recall, "f1": f1}
```

## 활용하기

scikit-learn은 같은 일을 여섯 줄로, 정확하게 해 냅니다.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words=None)),
    ("clf", LogisticRegression(C=1.0, max_iter=1000)),
])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))
```

주목할 점 세 가지. `stop_words=None`은 부정어를 살려 둡니다. `ngram_range=(1, 2)`는 바이그램을 추가해서 `not_good`이 특성이 되게 합니다. `sublinear_tf=True`는 반복 단어의 영향을 누그러뜨립니다. 이 세 플래그가 SST-2에서 75%짜리 베이스라인과 85%짜리 베이스라인의 차이입니다.

### 언제 트랜스포머로 넘어갈까

- 비꼼(반어) 탐지. 고전 모델은 여기서 실패합니다. 이상입니다.
- 문서 중간에 감성이 바뀌는 긴 리뷰.
- 측면별(aspect-based) 감성 분석. "카메라는 좋았는데 배터리는 끔찍했다." 감성을 특정 측면에 귀속시켜야 합니다. 트랜스포머나 구조화된 출력 모델만이 방법입니다.
- 영어가 아닌 저자원(low-resource) 언어. 다국어 BERT는 제로샷 베이스라인을 공짜로 줍니다.

위 중 하나라도 필요하면 페이즈 7(트랜스포머 심화)로 건너뛰세요. 아니라면, TF-IDF에 바이그램과 부정 처리를 얹은 나이브 베이즈 또는 로지스틱 회귀가 여러분의 2026년 프로덕션 베이스라인입니다.

### 재현성의 함정(또다시)

감성 모델을 다시 학습하는 일은 흔합니다. 다시 평가하는 일은 그렇지 않죠. 논문에 보고된 정확도 숫자는 특정 데이터 분할, 특정 전처리, 특정 토크나이저를 써서 나온 것입니다. 완전히 같은 파이프라인을 쓰지 않고 새 모델을 베이스라인과 비교하면, 그 델타(delta)는 오도됩니다. 항상 여러분의 파이프라인 위에서 베이스라인을 다시 계산하세요. 논문의 숫자를 가져오는 게 아니라요.

## 출시하기

`outputs/prompt-sentiment-baseline.md`로 저장하세요:

```markdown
---
name: sentiment-baseline
description: 새 데이터셋을 위한 감성 분석 베이스라인을 설계합니다.
phase: 5
lesson: 05
---

데이터셋 설명(도메인, 언어, 크기, 레이블 세분화, 지연 시간 예산)이 주어지면 다음을 출력합니다:

1. 특성 추출 레시피. 토크나이저, n-gram 범위, 불용어 정책(보통 유지), 부정 처리(범위 지정 접두어 또는 바이그램)를 명시합니다.
2. 분류기. 베이스라인은 나이브 베이즈, 프로덕션은 로지스틱 회귀, 도메인이 비꼼/측면/교차 언어를 요구할 때만 트랜스포머.
3. 평가 계획. 정밀도, 재현율, F1, 오차 행렬, 클래스별 오류 샘플을 보고합니다(스칼라 숫자만이 아니라).
4. 배포 후 감시할 실패 모드 하나. 도메인 드리프트와 비꼼이 상위 두 가지입니다.

감성 과제에서 불용어 제거를 추천하는 일은 거부합니다. 클래스가 불균형할 때(예: 긍정 90%) 정확도를 유일한 지표로 보고하는 일도 거부합니다. 하위 단어가 풍부한 언어에는 단어 수준 TF-IDF 대신 FastText나 트랜스포머 임베딩이 필요하다고 표시합니다.
```

## 연습 문제

1. **(쉬움)** `apply_negation`을 scikit-learn 파이프라인의 전처리 단계로 추가하고, 작은 감성 데이터셋에서 F1 변화를 측정하세요.
2. **(보통)** 클래스 가중치를 적용한 로지스틱 회귀를 구현하세요(scikit-learn에 `class_weight="balanced"`를 넘기거나, 그래디언트를 직접 유도). 합성으로 만든 90-10 클래스 불균형에서 그 효과를 측정하세요.
3. **(어려움)** 감성 모델의 잔차(residual)로 두 번째 분류기를 학습시켜 비꼼 탐지기를 만드세요. 실험 설정을 문서화하고, 정확도가 동전 던지기 수준에 머물면 독자에게 경고하세요(2클래스 비꼼 탐지에서 동전 던지기 수준은 약 50%이고, 첫 시도 대부분이 정확히 거기에 머뭅니다).

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 극성(polarity) | 긍정 또는 부정 | 이진 레이블. 가끔 중립이나 세밀한 등급(5점 척도)으로 확장되기도 함. |
| 측면별 감성 분석 | 측면별 극성 | 텍스트에 언급된 특정 개체나 속성에 감성을 귀속시킴. |
| 부정 범위 지정 | 근처 토큰 뒤집기 | "not" 뒤의 토큰들에 문장부호가 나올 때까지 `NOT_` 접두어를 붙임. |
| 라플라스 스무딩 | 카운트에 1 더하기 | 나이브 베이즈에서 확률 0짜리 특성이 생기는 것을 막아 줌. |
| L2 정규화 | 가중치 줄이기 | 손실에 `lambda * sum(w^2)`를 더함. 희소한 텍스트 특성에는 필수. |

## 더 읽을거리

- [Pang and Lee (2008). Opinion Mining and Sentiment Analysis](https://www.cs.cornell.edu/home/llee/opinion-mining-sentiment-analysis-survey.html) — 이 분야의 기초가 되는 서베이(survey)입니다. 길지만 처음 네 섹션이 고전의 전부를 다룹니다.
- [Wang and Manning (2012). Baselines and Bigrams: Simple, Good Sentiment and Topic Classification](https://aclanthology.org/P12-2018/) — 짧은 텍스트에서는 바이그램 + 나이브 베이즈를 이기기 어렵다는 것을 보여 준 논문.
- [scikit-learn 텍스트 특성 추출 문서](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction) — `CountVectorizer`, `TfidfVectorizer`, 그리고 여러분이 조정하게 될 모든 옵션의 레퍼런스.
