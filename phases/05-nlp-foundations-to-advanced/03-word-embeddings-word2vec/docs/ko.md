> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 단어 임베딩 — Word2Vec 처음부터 만들기

> 단어는 그 단어가 곁에 두는 벗을 보면 안다. 이 아이디어로 얕은 신경망을 학습시키면 기하학이 저절로 튀어나온다.

**유형:** 만들기
**언어:** Python
**선수 지식:** 페이즈 5 · 02 (BoW + TF-IDF), 페이즈 3 · 03 (역전파 처음부터 만들기)
**소요 시간:** 약 75분

## 문제 상황

TF-IDF는 `dog`과 `puppy`가 다른 단어라는 건 압니다. 하지만 둘이 거의 같은 뜻이라는 건 모릅니다. `dog`으로 학습한 분류기는 `puppy`에 대한 리뷰로 일반화하지 못합니다. 동의어 목록을 만들어 얼렁뚱땅 넘길 수도 있지만, 희귀 단어, 도메인 전문 용어, 그리고 예상하지 못한 모든 언어 앞에서는 실패합니다.

원하는 건 `dog`과 `puppy`가 공간에서 가까이 착지하는 표현입니다. `king - man + woman`이 `queen` 근처에 착지하는 표현. `dog`으로 학습한 모델이 공짜로 `puppy`에도 신호를 일부 전송하는 표현.

Word2Vec이 그 공간을 우리에게 줬습니다. 두 층짜리 신경망, 조 단위 토큰 학습, 2013년 발표. 아키텍처는 거의 민망할 만큼 단순한데, 그 결과물은 NLP를 10년간 바꿔 놓았습니다.

## 개념

**분포 가설(distributional hypothesis)** (Firth, 1957): "단어는 함께 다니는 벗을 보면 알 수 있다(you shall know a word by the company it keeps)." 비슷한 문맥에 등장하는 두 단어는 아마 비슷한 뜻일 겁니다.

Word2Vec은 이 아이디어를 활용하는 두 가지 방식이 있습니다.

- **Skip-gram.** 중심 단어가 주어지면 주변 단어를 예측합니다. 윈도우 크기 2일 때 `cat -> (the, sat, on)`.
- **CBOW (continuous bag of words).** 주변 단어가 주어지면 중심을 예측합니다. `(the, sat, on) -> cat`.

Skip-gram은 학습이 느리지만 희귀 단어를 더 잘 다룹니다. 그래서 기본 선택지가 됐습니다.

네트워크는 비선형성이 없는 은닉층 하나를 갖습니다. 입력은 어휘 위의 원-핫(one-hot) 벡터, 출력은 어휘 위의 소프트맥스(softmax)입니다. 학습이 끝나면 출력층은 버립니다. 은닉층 가중치가 바로 임베딩입니다.

```
one-hot(center) ── W ──▶ hidden (d-dim) ── W' ──▶ softmax(vocab)
                          ^
                          this is the embedding
```

비결: 10만 단어짜리 소프트맥스는 비용이 감당할 수 없을 만큼 큽니다. Word2Vec은 **네거티브 샘플링(negative sampling)**으로 이걸 이진 분류 문제로 바꿉니다. "이 문맥 단어가 이 중심 단어 근처에 나왔는가, 예/아니오"를 예측하는 것이죠. 전체 어휘에 소프트맥스를 계산하는 대신, 학습 쌍마다 네거티브(동시 출현하지 않는) 단어 몇 개를 샘플링합니다.

```figure
word-vector-arithmetic
```

## 만들어 보기

### 단계 1: 말뭉치에서 학습 쌍 뽑기

```python
def skipgram_pairs(docs, window=2):
    pairs = []
    for doc in docs:
        for i, center in enumerate(doc):
            for j in range(max(0, i - window), min(len(doc), i + window + 1)):
                if i == j:
                    continue
                pairs.append((center, doc[j]))
    return pairs
```

```python
>>> skipgram_pairs([["the", "cat", "sat", "on", "mat"]], window=2)
[('the', 'cat'), ('the', 'sat'),
 ('cat', 'the'), ('cat', 'sat'), ('cat', 'on'),
 ('sat', 'the'), ('sat', 'cat'), ('sat', 'on'), ('sat', 'mat'),
 ...]
```

윈도우 안의 모든 (중심, 문맥) 쌍이 하나의 긍정(positive) 학습 예시입니다.

### 단계 2: 임베딩 테이블

행렬 두 개입니다. `W`는 중심 단어 임베딩 테이블(우리가 남겨 두는 것)이고, `W'`는 문맥 단어 테이블(보통 버려지지만, 때로 `W`와 평균 내어 쓰기도 함)입니다.

```python
import numpy as np


def init_embeddings(vocab_size, dim, seed=0):
    rng = np.random.default_rng(seed)
    W = rng.normal(0, 0.1, size=(vocab_size, dim))
    W_prime = rng.normal(0, 0.1, size=(vocab_size, dim))
    return W, W_prime
```

작은 무작위 초기화입니다. 어휘 1만, 차원 100이면 현실적인 규모이고, 교육용으로는 어휘 50 x 차원 16만으로도 기하학을 볼 수 있습니다.

### 단계 3: 네거티브 샘플링 목적함수

긍정 쌍 `(center, context)`마다 어휘에서 무작위 단어 `k`개를 네거티브로 샘플링합니다. 긍정 쌍에서는 내적 `W[center] · W'[context]`이 높아지고 네거티브에서는 낮아지도록 모델을 학습시킵니다.

```python
def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def train_pair(W, W_prime, center_idx, context_idx, negative_indices, lr):
    v_c = W[center_idx]
    u_pos = W_prime[context_idx]
    u_negs = W_prime[negative_indices]

    pos_score = sigmoid(v_c @ u_pos)
    neg_scores = sigmoid(u_negs @ v_c)

    grad_center = (pos_score - 1) * u_pos
    for i, u in enumerate(u_negs):
        grad_center += neg_scores[i] * u

    W[context_idx] = W[context_idx]
    W_prime[context_idx] -= lr * (pos_score - 1) * v_c
    for i, neg_idx in enumerate(negative_indices):
        W_prime[neg_idx] -= lr * neg_scores[i] * v_c
    W[center_idx] -= lr * grad_center
```

마법의 공식: 긍정 쌍에 대한 로지스틱 손실(시그모이드가 1 근처가 되길 원함)에 네거티브 쌍에 대한 로지스틱 손실(시그모이드가 0 근처가 되길 원함)을 더한 것입니다. 그래디언트는 두 테이블 모두로 흐릅니다. 전체 유도 과정은 원논문에 있으니, 머리에 넣고 싶다면 연필과 종이로 한 번 따라 가 보세요.

### 단계 4: 장난감 말뭉치로 학습하기

```python
def train(docs, dim=16, window=2, k_neg=5, epochs=100, lr=0.05, seed=0):
    vocab = build_vocab(docs)
    vocab_size = len(vocab)
    rng = np.random.default_rng(seed)
    W, W_prime = init_embeddings(vocab_size, dim, seed=seed)
    pairs = skipgram_pairs(docs, window=window)

    for epoch in range(epochs):
        rng.shuffle(pairs)
        for center, context in pairs:
            c_idx = vocab[center]
            ctx_idx = vocab[context]
            negs = rng.integers(0, vocab_size, size=k_neg)
            negs = [n for n in negs if n != ctx_idx and n != c_idx]
            train_pair(W, W_prime, c_idx, ctx_idx, negs, lr)
    return vocab, W
```

큰 말뭉치에서 에포크를 충분히 돌리면, 문맥을 공유하는 단어들이 비슷한 중심 임베딩을 갖게 됩니다. 장난감 말뭉치에서는 효과가 희미하게 보입니다. 수십억 토큰에서는 극적으로 보입니다.

### 단계 5: 유추(analogy) 기법

```python
def nearest(vocab, W, target_vec, topk=5, exclude=None):
    exclude = exclude or set()
    inv_vocab = {i: w for w, i in vocab.items()}
    norms = np.linalg.norm(W, axis=1, keepdims=True) + 1e-9
    W_norm = W / norms
    target = target_vec / (np.linalg.norm(target_vec) + 1e-9)
    sims = W_norm @ target
    order = np.argsort(-sims)
    out = []
    for i in order:
        if i in exclude:
            continue
        out.append((inv_vocab[i], float(sims[i])))
        if len(out) == topk:
            break
    return out


def analogy(vocab, W, a, b, c, topk=5):
    v = W[vocab[b]] - W[vocab[a]] + W[vocab[c]]
    return nearest(vocab, W, v, topk=topk, exclude={vocab[a], vocab[b], vocab[c]})
```

사전학습된 300차원 Google News 벡터에서:

```python
>>> analogy(vocab, W, "man", "king", "woman")
[('queen', 0.71), ('monarch', 0.62), ('princess', 0.59), ...]
```

`king - man + woman = queen`. 모델이 왕족이 뭔지 알아서가 아닙니다. 벡터 `(king - man)`이 대략 "왕족스러움" 같은 것을 잡아 내고, 그걸 `woman`에 더하면 왕족-여성 영역 근처에 착지하기 때문입니다.

## 활용하기

Word2Vec을 처음부터 쓰는 건 교육용입니다. 프로덕션 NLP는 `gensim`을 씁니다.

```python
from gensim.models import Word2Vec

sentences = [
    ["the", "cat", "sat", "on", "the", "mat"],
    ["the", "dog", "ran", "across", "the", "room"],
]

model = Word2Vec(
    sentences,
    vector_size=100,
    window=5,
    min_count=1,
    sg=1,
    negative=5,
    workers=4,
    epochs=30,
)

print(model.wv["cat"])
print(model.wv.most_similar("cat", topn=3))
```

실무에서는 Word2Vec을 직접 학습시키는 일이 거의 없습니다. 사전학습 벡터를 내려받습니다.

- **GloVe** — 스탠퍼드의 동시출현 행렬 분해 방식. 50d, 100d, 200d, 300d 체크포인트. 전반적인 커버리지가 좋습니다. 레슨 04에서 GloVe를 따로 다룹니다.
- **fastText** — Facebook이 만든 Word2Vec 확장으로 문자 n-그램을 임베딩합니다. 서브워드를 조합해 어휘 밖 단어를 처리합니다. 레슨 04.
- **Google News 사전학습 Word2Vec** — 300d, 300만 단어 어휘, 2013년 공개. 지금도 매일 내려받아 씁니다.

### 2026년에도 Word2Vec이 이기는 경우

- 가벼운 도메인 특화 검색. 노트북에서 의학 초록 데이터로 한 시간 학습하면, 범용 모델이 잡아 내지 못하는 특화 벡터를 얻습니다.
- 유추식 특성(feature) 엔지니어링. `gender_vector = mean(man - woman pairs)`. 다른 단어에서 이걸 빼면 성별 중립 축이 나옵니다. 공정성(fairness) 연구에서 아직 쓰입니다.
- 해석 가능성. 100d면 PCA나 t-SNE로 그려서 클러스터가 형성되는 걸 실제로 볼 수 있을 만큼 작습니다.
- GPU 없이 온디바이스에서 추론해야 하는 모든 곳. Word2Vec 조회는 행 하나를 읽는 것에 불과합니다.

### Word2Vec이 실패하는 곳

다의어(polysemy)의 벽입니다. `bank`는 벡터 하나를 갖습니다. `river bank`와 `financial bank`가 그 벡터를 공유합니다. `table`(스프레드시트 vs 가구)도 마찬가지입니다. 하위의 분류기는 그 벡터만으로 의미를 구분할 수 없습니다.

문맥적 임베딩(ELMo, BERT, 그 이후의 모든 트랜스포머)은 단어가 등장할 때마다 주변 문맥에 따라 다른 벡터를 내놓는 방식으로 이 문제를 해결했습니다. Word2Vec에서 BERT로의 도약, 즉 정적(static)에서 문맥적(contextual)으로의 전환이 바로 이것입니다. 트랜스포머 쪽 절반은 페이즈 7이 다룹니다.

어휘 밖(out-of-vocabulary) 문제도 또 하나의 실패입니다. 학습 데이터에 없었다면 Word2Vec은 `Zoomer-approved`를 본 적이 없습니다. 폴백도 없습니다. fastText는 서브워드 조합으로 이걸 고칩니다(레슨 04).

## 출시하기

`outputs/skill-embedding-probe.md`로 저장하세요:

```markdown
---
name: embedding-probe
description: 학습된 word2vec 모델을 검사한다. 유추를 돌리고, 이웃을 찾고, 품질을 진단한다.
version: 1.0.0
phase: 5
lesson: 03
tags: [nlp, embeddings, debugging]
---

당신은 학습된 단어 임베딩을 검사(probe)해 제대로 동작하는지 확인합니다. `gensim.models.KeyedVectors` 객체와 어휘가 주어지면 다음을 실행합니다:

1. 정통 유추 테스트 세 개. `king : man :: queen : woman`. `paris : france :: tokyo : japan`. `walking : walked :: swimming : ?`. 최상위(top-1) 결과와 코사인 값을 보고한다.
2. 사용자가 제공한 도메인 특화 단어로 최근접 이웃 테스트 다섯 개. 코사인과 함께 상위 5개 이웃을 출력한다.
3. 대칭성 검사 하나. `similarity(a, b) == similarity(b, a)`가 부동소수점 정밀도 수준에서 성립하는지 확인한다.
4. 퇴화(degenerate) 검사 하나. 임베딩의 노름(norm)이 0.01 미만이거나 100 초과인 것이 있으면 학습 버그다. 표시한다.

유추 정확도만으로 모델이 좋다고 선언하지 않는다. 유추 벤치마크는 속이기 쉽고 하위 과제로 전이되지 않는다. 고유(intrinsic) 평가와 하위 과제 평가를 함께 권한다.
```

## 연습 문제

1. **쉬움.** 아주 작은 말뭉치(고양이와 개에 관한 20문장)로 학습 루프를 돌려 보세요. 200 에포크 후 `nearest(vocab, W, W[vocab["cat"]])`의 상위 3개 안에 `dog`이 나오는지 확인하세요. 나오지 않으면 에포크나 어휘를 늘리세요.
2. **보통.** 빈도가 높은 단어의 서브샘플링을 추가해 보세요. 빈도가 `10^-5`를 넘는 단어는 빈도에 비례하는 확률로 학습 쌍에서 제외합니다. 희귀 단어 유사도에 미치는 영향을 측정하세요.
3. **어려움.** 20 Newsgroups 말뭉치로 모델을 학습시켜 보세요. 편향 축 두 개, `he - she`와 `doctor - nurse`를 계산합니다. 직업 단어를 두 축에 투영하고, 어떤 직업이 가장 큰 편향 격차를 보이는지 보고하세요. 공정성 연구자들이 쓰는 바로 그런 탐침(probe)입니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 단어 임베딩 | 벡터로 된 단어 | 문맥에서 학습된 조밀한(dense) 저차원(보통 100~300) 표현. |
| Skip-gram | Word2Vec 비법 | 중심 단어에서 문맥 단어를 예측. CBOW보다 느리지만 희귀 단어에 강하다. |
| 네거티브 샘플링 | 학습 지름길 | 전체 어휘 소프트맥스를, 무작위 단어 `k`개와의 이진 분류로 대체. |
| 정적 임베딩 | 단어당 벡터 하나 | 문맥과 무관하게 같은 벡터. 다의어에서 실패한다. |
| 문맥적 임베딩 | 문맥 민감 벡터 | 주변 단어에 따라 등장마다 다른 벡터. 트랜스포머가 만들어 내는 것. |
| OOV | 어휘 밖(Out of Vocabulary) | 학습에서 본 적 없는 단어. Word2Vec은 이런 단어의 벡터를 만들 수 없다. |

## 더 읽을거리

- [Mikolov et al. (2013). Distributed Representations of Words and Phrases and their Compositionality](https://arxiv.org/abs/1310.4546) — 네거티브 샘플링 논문. 짧고 읽기 쉽다.
- [Rong, X. (2014). word2vec Parameter Learning Explained](https://arxiv.org/abs/1411.2738) — 원논문의 수식이 어렵게 느껴진다면, 그래디언트를 가장 명쾌하게 유도한 글.
- [gensim Word2Vec tutorial](https://radimrehurek.com/gensim/models/word2vec.html) — 실제로 동작하는 프로덕션 학습 설정.
