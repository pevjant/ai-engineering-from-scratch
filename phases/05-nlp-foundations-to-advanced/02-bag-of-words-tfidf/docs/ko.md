> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 단어 가방(BoW), TF-IDF, 텍스트 표현

> 먼저 세고, 나중에 생각한다. 2026년에도 잘 정의된 작업에서는 TF-IDF가 임베딩을 여전히 이긴다.

**유형:** 만들기
**언어:** Python
**선수 지식:** 페이즈 5 · 01 (텍스트 처리), 페이즈 2 · 02 (선형 회귀 처음부터 만들기)
**소요 시간:** 약 75분

## 문제 상황

모델은 숫자가 필요합니다. 그런데 당신 손에는 문자열이 있죠.

모든 NLP 파이프라인은 같은 질문에 답해야 합니다. 길이가 들쭉날쭉한 토큰 스트림을 분류기가 먹을 수 있는 고정 크기 벡터로 어떻게 바꿀 것인가. 이 분야가 처음 내놓은 답은 동작하는 방법 중 가장 멍청한 방법이었습니다. 단어를 세고, 벡터를 만든다.

그 벡터는 어떤 임베딩 모델보다도 많은 프로덕션(운영 환경) NLP를 떠받쳤습니다. 스팸 필터, 토픽 분류기, 로그 이상 감지, 검색 랭킹(BM25 이전), 감성 분석의 첫 물결, 학술 NLP 벤치마크의 첫 10년. 2026년 실무자들도 좁은 분류 작업에서는 여전히 이 방법을 먼저 손에 넣습니다. 빠르고, 해석 가능하고, 단어 존재 여부가 중요한 작업에서는 4억 파라미터짜리 임베딩 모델과 구분이 안 될 때도 많습니다.

이 레슨에서는 단어 가방(bag of words)과 TF-IDF를 처음부터 만들어 봅니다. 그다음 scikit-learn이 같은 일을 세 줄로 처리하는 모습을 보고, 마지막으로 임베딩으로 갈아타게 만드는 실패 지점의 이름을 짚습니다.

## 개념

**단어 가방(Bag of Words, BoW)** 은 순서를 버립니다. 문서마다 어휘(vocabulary)의 각 단어가 몇 번 나오는지 셉니다. 벡터 길이는 어휘 크기이고, 위치 `i`는 단어 `i`의 등장 횟수입니다.

**TF-IDF** 는 BoW에 가중치를 다시 매깁니다. 모든 문서에 나오는 단어는 정보가 없으므로 가중치를 낮춥니다. 말뭉치 전체에서는 드물지만 한 문서 안에서 자주 나오는 단어는 신호이므로 가중치를 높입니다.

```
TF-IDF(w, d) = TF(w, d) * IDF(w)
             = count(w in d) / |d| * log(N / df(w))
```

여기서 `TF`는 문서 안 단어 빈도, `df`는 문서 빈도(그 단어를 담은 문서 수), `N`은 전체 문서 수입니다. `log`는 어디에나 있는 단어의 가중치가 무한정 커지지 않게 묶어 둡니다.

핵심 성질: 둘 다 해석 가능한 축을 가진 희소(sparse) 벡터를 만듭니다. 학습된 분류기의 가중치를 들여다보면 어떤 단어가 문서를 어느 클래스 쪽으로 밀어 넣는지 읽을 수 있습니다. 768차원 BERT 임베딩으로는 이게 불가능합니다.

```figure
bow-tfidf
```

## 만들어 보기

### 단계 1: 어휘 만들기

```python
def build_vocab(docs):
    vocab = {}
    for doc in docs:
        for token in doc:
            if token not in vocab:
                vocab[token] = len(vocab)
    return vocab
```

입력: 토큰화된 문서 목록(어떤 단어 단위 토크나이저든 무방합니다. 이 레슨의 `code/main.py`는 소문자화 변형을 씁니다). 출력: `{word: index}` 딕셔너리. 삽입 순서가 유지되므로 단어 인덱스 0은 첫 문서에서 처음 본 단어입니다. 관례는 제각각이라 scikit-learn은 알파벳순으로 정렬합니다.

### 단계 2: 단어 가방

```python
def bag_of_words(docs, vocab):
    matrix = [[0] * len(vocab) for _ in docs]
    for i, doc in enumerate(docs):
        for token in doc:
            if token in vocab:
                matrix[i][vocab[token]] += 1
    return matrix
```

```python
>>> docs = [["cat", "sat", "on", "mat"], ["cat", "cat", "ran"]]
>>> vocab = build_vocab(docs)
>>> bag_of_words(docs, vocab)
[[1, 1, 1, 1, 0], [2, 0, 0, 0, 1]]
```

행은 문서, 열은 어휘 인덱스입니다. 칸 `[i][j]`는 "단어 `j`가 문서 `i`에 몇 번 나오는가"입니다. 문서 1에 `cat`이 두 번인 건 실제로 두 번 나왔기 때문이고, 문서 0에 `ran`이 0인 건 나오지 않았기 때문입니다.

### 단계 3: 단어 빈도와 문서 빈도

```python
import math


def term_frequency(doc_bow, doc_length):
    return [c / doc_length if doc_length else 0 for c in doc_bow]


def document_frequency(bow_matrix):
    df = [0] * len(bow_matrix[0])
    for row in bow_matrix:
        for j, count in enumerate(row):
            if count > 0:
                df[j] += 1
    return df


def inverse_document_frequency(df, n_docs):
    return [math.log((n_docs + 1) / (d + 1)) + 1 for d in df]
```

이름 붙일 만한 스무딩 요령이 두 가지 있습니다. `(n+1)/(d+1)`은 `log(x/0)`를 피해 줍니다. 뒤에 붙는 `+1`은 모든 문서에 나오는 단어도 IDF가 0이 아니라 1을 갖게 해서 scikit-learn의 기본값과 맞춰 줍니다. 다른 구현은 날것의 `log(N/df)`를 씁니다. 둘 다 동작하고, 스무딩 버전이 좀 더 다루기 편합니다.

### 단계 4: TF-IDF

```python
def tfidf(bow_matrix):
    n_docs = len(bow_matrix)
    df = document_frequency(bow_matrix)
    idf = inverse_document_frequency(df, n_docs)
    out = []
    for row in bow_matrix:
        length = sum(row)
        tf = term_frequency(row, length)
        out.append([tf_j * idf_j for tf_j, idf_j in zip(tf, idf)])
    return out
```

```python
>>> docs = [
...     ["the", "cat", "sat"],
...     ["the", "dog", "sat"],
...     ["the", "cat", "ran"],
... ]
>>> vocab = build_vocab(docs)
>>> bow = bag_of_words(docs, vocab)
>>> tfidf(bow)
```

문서 3개, 어휘 단어 5개(`the`, `cat`, `sat`, `dog`, `ran`). `the`는 세 문서 모두에 나오므로 IDF가 낮습니다. `dog`은 한 문서에만 나오므로 IDF가 높습니다. 벡터는 희소하고(대부분의 칸이 작음), 판별적인 단어가 도드라집니다.

### 단계 5: 행 L2 정규화

```python
def l2_normalize(matrix):
    out = []
    for row in matrix:
        norm = math.sqrt(sum(x * x for x in row))
        out.append([x / norm if norm else 0 for x in row])
    return out
```

정규화가 없으면 긴 문서가 더 큰 벡터를 가져 유사도 점수를 지배합니다. L2 정규화는 모든 문서를 단위 초구면 위에 올려 놓습니다. 이제 행 사이의 코사인 유사도는 그냥 내적입니다.

## 활용하기

scikit-learn이 프로덕션용 구현을 갖고 있습니다.

```python
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

docs = ["the cat sat on the mat", "the dog sat on the mat", "the cat ran"]

bow_vectorizer = CountVectorizer()
bow = bow_vectorizer.fit_transform(docs)
print(bow_vectorizer.get_feature_names_out())
print(bow.toarray())

tfidf_vectorizer = TfidfVectorizer()
tfidf = tfidf_vectorizer.fit_transform(docs)
print(tfidf.toarray().round(3))
```

`CountVectorizer`는 토큰화, 어휘 생성, BoW를 한 번의 호출로 처리합니다. `TfidfVectorizer`는 여기에 IDF 가중치와 L2 정규화를 더합니다. 둘 다 희소 행렬을 반환합니다. 문서 10만 개면 밀집(dense) 버전은 메모리에 안 들어가니, 분류기가 밀집을 요구할 때까지 희소 형태를 유지하세요.

모든 것을 바꿔 놓는 손잡이들:

| 인자 | 효과 |
|-----|--------|
| `ngram_range=(1, 2)` | 바이그램 포함. 분류 성능을 보통 끌어올린다. |
| `min_df=2` | 문서 2개 미만에서 나오는 단어 제외. 노이즈 섞인 데이터에서 어휘를 정리한다. |
| `max_df=0.95` | 문서의 95% 초과에서 나오는 단어 제외. 고정된 목록 없이 불용어 제거를 흉내 낸다. |
| `stop_words="english"` | scikit-learn 내장 불용어 목록. 작업에 따라 갈린다 — 감성 분석은 부정어를 버리면 *안 된다*. |
| `sublinear_tf=True` | 날것의 `tf` 대신 `1 + log(tf)` 사용. 한 문서에서 같은 단어가 수없이 반복될 때 도움이 된다. |

### TF-IDF가 아직 이기는 경우 (2026년 기준)

- 스팸 탐지, 토픽 라벨링, 로그 이상 징후 표시. 단어 존재 여부가 중요하고 의미적 뉘앙스는 중요하지 않은 작업.
- 데이터가 적은 상황(라벨 달린 예시 수백 개). TF-IDF + 로지스틱 회귀는 사전학습 비용이 없습니다.
- 지연 시간이 중요한 모든 곳. TF-IDF + 선형 모델은 마이크로초 만에 답합니다. 트랜스포머로 문서를 임베딩하면 10~100ms가 듭니다.
- 예측을 설명해야 하는 시스템. 분류기의 계수를 들여다보면, 양수 상위 단어가 그 근거입니다.

### TF-IDF가 실패하는 경우

의미적 맹목 실패입니다. 문서 두 개를 봅시다.

- "The movie was not good at all."
- "The movie was excellent."

하나는 부정 리뷰고 하나는 긍정 리뷰입니다. 그런데 두 문서의 TF-IDF 겹침은 정확히 `{the, movie, was}`입니다. 단어 가방 분류기는 `good` 근처의 `not`이 레이블을 뒤집는다는 걸 외워야 합니다. 데이터가 충분하면 배울 수는 있지만, 통법(syntax)을 이해하는 모델만큼 우아하게는 절대 못 배웁니다.

또 하나의 실패: 추론 시점의 어휘 밖(out-of-vocabulary) 단어. IMDb 리뷰로 학습한 BoW 모델은 `Zoomer-approved` 같은 토큰이 학습에 한 번도 안 나왔다면 어떻게 해야 할지 모릅니다. 서브워드 임베딩(레슨 04)은 이걸 처리합니다. TF-IDF는 안 됩니다.

### 하이브리드: TF-IDF 가중 임베딩

중간 규모 데이터 분류를 위한 2026년 실용적 기본값: TF-IDF 가중치를 단어 임베딩 위의 어텐션처럼 쓰는 방식입니다.

```python
def tfidf_weighted_embedding(doc, tfidf_scores, embedding_table, dim):
    vec = [0.0] * dim
    total_weight = 0.0
    for token in doc:
        if token not in embedding_table or token not in tfidf_scores:
            continue
        weight = tfidf_scores[token]
        emb = embedding_table[token]
        for i in range(dim):
            vec[i] += weight * emb[i]
        total_weight += weight
    if total_weight == 0:
        return vec
    return [v / total_weight for v in vec]
```

임베딩에서 의미적 표현력을 얻고, TF-IDF에서 희귀 단어 강조를 얻습니다. 분류기는 풀링된 벡터로 학습합니다. 라벨 예시 5만 개 이하의 감성, 토픽, 의도(intent) 분류에서는 어느 한쪽 단독보다 이 조합이 이깁니다.

## 출시하기

`outputs/prompt-vectorization-picker.md`로 저장하세요:

```markdown
---
name: vectorization-picker
description: 텍스트 분류 작업이 주어지면 BoW, TF-IDF, 임베딩, 하이브리드 중 하나를 추천한다.
phase: 5
lesson: 02
---

당신은 텍스트 벡터화 전략을 추천합니다. 작업 설명이 주어지면 다음을 출력합니다:

1. 표현 방식(BoW, TF-IDF, 트랜스포머 임베딩, 또는 하이브리드). 이유를 한 문장으로 설명한다.
2. 구체적인 벡터화기(vectorizer) 설정. 라이브러리 이름을 적고 인자를 인용한다(`ngram_range`, `min_df`, `max_df`, `sublinear_tf`, `stop_words`).
3. 출시 전에 테스트할 실패 지점 하나.

라벨 예시가 500개 미만인데 TF-IDF 베이스라인에서 의미적 실패의 증거를 보여 주지 않는다면 임베딩을 권하지 않는다. 감성 분석에서 불용어 제거를 권하지 않는다(부정어가 신호를 갖고 있다). 클래스 불균형은 벡터화기 변경만으로 해결되는 문제가 아니라고 표시한다.

입력 예시: "Classifying 30k customer support tickets into 12 categories. Most tickets are 2-3 sentences. English only. Need explainability for audit logs."

출력 예시:

- 표현: TF-IDF. 3만 개 예시는 작지 않고, 설명 가능성 요구사항이 밀집 임베딩을 배제한다.
- 설정: `TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.95, sublinear_tf=True, stop_words=None)`. 불용어를 유지한다. 범주 키워드가 불용어인 경우가 있기 때문이다("not working" vs "working").
- 테스트할 실패 지점: `min_df=3`이 희귀 범주 키워드를 버리지 않는지 확인한다. 클래스별로 `get_feature_names_out`을 필터링해 눈으로 검토한다.
```

## 연습 문제

1. **쉬움.** L2 정규화된 TF-IDF 출력 위에서 `cosine_similarity(doc_vec_a, doc_vec_b)`를 구현해 보세요. 동일한 문서는 1.0, 어휘가 겹치지 않는 문서는 0.0이 나오는지 확인하세요.
2. **보통.** `bag_of_words`에 `n-gram` 지원을 추가해 보세요. 파라미터 `n`이 `n`-그램 개수를 세게 합니다. `["the", "cat", "sat"]`에 `n=2`를 적용하면 `["the cat", "cat sat"]`의 바이그램 개수가 나오는지 테스트하세요.
3. **어려움.** 위의 TF-IDF 가중 임베딩 하이브리드를 GloVe 100d 벡터(한 번 다운로드해서 캐시)로 만들어 보세요. 20 Newsgroups 데이터셋에서 순수 TF-IDF와 순수 평균 풀링 임베딩과 분류 정확도를 비교하고, 어디서 무엇이 이기는지 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| BoW | 단어 빈도 벡터 | 한 문서 안 어휘 단어들의 개수. 순서는 버린다. |
| TF | 단어 빈도(Term Frequency) | 문서 안 단어 개수. 문서 길이로 나눠 정규화하기도 한다. |
| DF | 문서 빈도(Document Frequency) | 그 단어를 최소 한 번 담은 문서의 개수. |
| IDF | 역문서 빈도(Inverse Document Frequency) | 스무딩된 `log(N / df)`. 어디에나 나오는 단어의 가중치를 낮춘다. |
| 희소 벡터 | 대부분 0 | 어휘는 보통 1만~10만 단어인데, 주어진 문서에는 대부분이 없다. |
| 코사인 유사도 | 벡터 각도 | L2 정규화된 벡터의 내적. 1은 동일, 0은 직교. |

## 더 읽을거리

- [scikit-learn — feature extraction from text](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction) — 정통 API 레퍼런스. 모든 손잡이에 대한 설명 포함.
- [Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval](https://www.sciencedirect.com/science/article/pii/0306457388900210) — TF-IDF를 10년간 기본값으로 만든 논문.
- ["Why TF-IDF Still Beats Embeddings" — Ashfaque Thonikkadavan (Medium)](https://medium.com/@cmtwskb/why-tf-idf-still-beats-embeddings-ad85c123e1b2) — 옛 방법이 언제, 왜 이기는지에 대한 2026년 시각.
