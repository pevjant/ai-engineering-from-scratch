> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 토픽 모델링 — LDA와 BERTopic

> LDA: 문서는 토픽의 혼합이고, 토픽은 단어 위의 확률 분포입니다. BERTopic: 문서는 임베딩 공간에서 뭉치고, 그 뭉치(클러스터)가 토픽입니다. 목표는 같은데 분해 방식이 다를 뿐입니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 02(BoW + TF-IDF), 페이즈 5 · 03(Word2Vec)
**시간:** 약 45분

## 문제 상황

고객 지원 티켓 10,000건, 뉴스 기사 50,000개, 트윗 200,000개가 있다고 합시다. 아무것도 읽지 않고 이 컬렉션이 무슨 이야기를 하는지 알아야 합니다. 레이블이 달린 카테고리도 없고, 카테고리가 몇 개 존재하는지조차 모릅니다.

토픽 모델링은 비지도 학습으로 이 질문에 답합니다. 코퍼스를 넘기면, 일관성 있는 소수의 토픽과 문서별 토픽 분포를 돌려줍니다.

두 알고리즘 계열이 지배적입니다. LDA(2003)는 각 문서를 잠재 토픽들의 혼합으로, 각 토픽을 단어 위의 분포로 취급합니다. 추론은 베이지안 방식입니다. 문서마다 여러 토픽에 걸친 소속(mixed-membership) 할당과 설명 가능한 단어 수준 확률 분포가 필요한 프로덕션(운영 환경)에서는 지금도 쓰입니다.

BERTopic(2020)은 문서를 BERT로 인코딩하고, UMAP으로 차원을 축소하고, HDBSCAN으로 클러스터링하고, 클래스 기반 TF-IDF로 토픽 단어를 뽑아 냅니다. 짧은 텍스트, 소셜 미디어, 그리고 단어 겹침보다 의미적 유사성이 중요한 모든 곳에서 이깁니다. 문서 하나에 토픽 하나만 부여되는데, 이것이 긴 문서에는 한계입니다.

이 레슨은 두 방법 모두에 대한 직관을 만들어 주고, 주어진 코퍼스에 무엇을 골라야 하는지 알려 줍니다.

## 핵심 개념

![LDA 혼합 모델 vs BERTopic 클러스터링](../assets/topic-modeling.svg)

**LDA 생성 스토리.** 각 토픽은 단어 위의 분포입니다. 각 문서는 토픽들의 혼합입니다. 문서의 단어 하나를 생성하려면, 문서의 혼합에서 토픽을 뽑고(sample), 그 토픽의 분포에서 단어를 뽑습니다. 추론은 이 과정을 거꾸로 돌립니다: 관찰된 단어들이 주어지면, 문서별 토픽 분포와 토픽별 단어 분포를 추론합니다.Collapsed Gibbs 샘플링이나 변분 베이즈(variational Bayes)가 수학을 담당합니다.

LDA의 핵심 출력:

- `doc_topic`: `(n_docs, n_topics)` 행렬, 각 행의 합은 1(문서의 토픽 혼합).
- `topic_word`: `(n_topics, vocab_size)` 행렬, 각 행의 합은 1(토픽의 단어 분포).

**BERTopic 파이프라인.**

1. 각 문서를 문장 임베딩 모델(예: `all-MiniLM-L6-v2`)로 인코딩합니다. 384차원 벡터.
2. UMAP으로 약 5차원까지 차원을 축소합니다. BERT 임베딩은 클러스터링하기에 차원이 너무 높습니다.
3. HDBSCAN으로 클러스터링합니다. 밀도 기반이라 크기가 제각각인 클러스터를 만들고 "이상치(outlier)" 레이블도 내줍니다.
4. 클러스터마다 클래스 기반 TF-IDF를 계산해 상위 단어를 추출합니다.

출력은 문서당 토픽 하나입니다(추가로 -1 이상치 레이블). 선택적으로 HDBSCAN의 확률 벡터로 소프트 소속(soft membership)도 얻을 수 있습니다.

```figure
topic-drift
```

## 만들어 보기

### 단계 1: scikit-learn으로 LDA 돌리기

```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np


def fit_lda(documents, n_topics=5, max_features=1000):
    cv = CountVectorizer(
        max_features=max_features,
        stop_words="english",
        min_df=2,
        max_df=0.9,
    )
    X = cv.fit_transform(documents)
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        max_iter=50,
        learning_method="online",
    )
    doc_topic = lda.fit_transform(X)
    feature_names = cv.get_feature_names_out()
    return lda, cv, doc_topic, feature_names


def print_top_words(lda, feature_names, n_top=10):
    for idx, topic in enumerate(lda.components_):
        top_idx = np.argsort(-topic)[:n_top]
        words = [feature_names[i] for i in top_idx]
        print(f"topic {idx}: {' '.join(words)}")
```

주목할 점: 불용어를 제거하고, min_df와 max_df로 희귀 단어와 만연한 단어를 걸러내며, TfidfVectorizer가 아니라 CountVectorizer를 씁니다. LDA는 원본 카운트를 기대하기 때문입니다.

### 단계 2: BERTopic (프로덕션)

```python
from bertopic import BERTopic

topic_model = BERTopic(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    min_topic_size=15,
    verbose=True,
)

topics, probs = topic_model.fit_transform(documents)
info = topic_model.get_topic_info()
print(info.head(20))
valid_topics = info[info["Topic"] != -1]["Topic"].tolist()
for topic_id in valid_topics[:5]:
    print(f"topic {topic_id}: {topic_model.get_topic(topic_id)[:10]}")
```

`Topic != -1` 필터는 BERTopic의 이상치 버킷(HDBSCAN이 클러스터링하지 못한 문서들)을 걸러 냅니다. `min_topic_size`는 HDBSCAN의 최소 클러스터 크기를 조절합니다. 라이브러리 기본값은 10인데, 이 예제는 레슨 규모에 맞춰 명시적으로 15로 정했습니다. 문서 10,000개가 넘는 코퍼스라면 50이나 100으로 올리세요.

### 단계 3: 평가

두 방법 모두 토픽 단어를 출력합니다. 문제는 그 단어들이 일관성(coherence) 있게 뭉치는지입니다.

- **토픽 일관성(c_v).** 슬라이딩 윈도우 컨텍스트 위에서 상위 단어 쌍의 NPMI(정규화된 점별 상호 정보량)를 계산하고, 그 점수들을 토픽 벡터로 모아 코사인 유사도로 비교합니다. 높을수록 좋습니다. `gensim.models.CoherenceModel`을 `coherence="c_v"` 옵션으로 쓰세요.
- **토픽 다양성.** 모든 토픽의 상위 단어를 모았을 때 고유 단어의 비율. 높을수록 좋습니다(토픽끼리 겹치지 않는다는 뜻).
- **정성적 검토.** 각 토픽의 상위 단어를 직접 읽어 보세요. 실제 존재하는 무언가를 가리키나요? 사람의 판단은 여전히 마지막 방어선입니다.

## 언제 무엇을 고를까

| 상황 | 선택 |
|-----------|------|
| 짧은 텍스트(트윗, 리뷰, 헤드라인) | BERTopic |
| 토픽이 섞인 긴 문서 | LDA |
| GPU 없음 / 컴퓨팅 자원 제한 | LDA 또는 NMF |
| 문서 수준의 다중 토픽 분포 필요 | LDA |
| 토픽 레이블링에 LLM 통합 | BERTopic (직접 지원) |
| 자원 제약이 있는 엣지 배포 | LDA |
| 최대 의미적 일관성 | BERTopic |

가장 중요한 실무 고려 사항은 문서 길이입니다. BERT 임베딩은 잘라내고(truncate), LDA 카운트는 길이와 상관없이 동작합니다. 임베딩 모델의 컨텍스트보다 긴 문서는 청크로 나눠 집계하거나 LDA를 쓰세요.

## 사용해 보기

2026년 스택:

- **BERTopic.** 짧은 텍스트와 의미가 중요한 모든 곳의 기본값.
- **`gensim.models.LdaModel`.** 프로덕션용 클래식 LDA. 성숙하고 전장에서 검증됨.
- **`sklearn.decomposition.LatentDirichletAllocation`.** 실험용 간편 LDA.
- **NMF.** 음수 미포함 행렬 분해. LDA보다 빠른 대안으로, 짧은 텍스트에서는 품질이 비슷함.
- **Top2Vec.** BERTopic과 설계가 비슷함. 커뮤니티는 작지만 일부 벤치마크에서 좋은 성적.
- **FASTopic.** 더 최근 나왔으며, 아주 큰 코퍼스에서 BERTopic보다 빠름.
- **LLM 기반 레이블링.** 아무 클러스터링이나 돌린 다음, 모델에게 프롬프트를 줘서 각 클러스터의 이름을 붙임.

## 출시하기

`outputs/skill-topic-picker.md`로 저장하세요:

```markdown
---
name: topic-picker
description: 코퍼스에 LDA 또는 BERTopic을 고르기. 라이브러리, 설정값, 평가 방법까지 명시.
version: 1.0.0
phase: 5
lesson: 15
tags: [nlp, topic-modeling]
---

코퍼스 설명(문서 수, 평균 길이, 도메인, 언어, 컴퓨팅 예산)이 주어지면 다음을 출력하세요:

1. 알고리즘. LDA / NMF / BERTopic / Top2Vec / FASTopic. 한 문장 근거.
2. 설정. 토픽 수: `recommended = max(5, round(sqrt(n_docs)))`, 40,000개 미만 코퍼스에서는 200으로 상한 적용; 200 초과는 코퍼스가 정말로 클 때(>4만)만 허용하고 컴퓨팅 비용 증가를 명시. 신경망 기반 접근의 `min_df` / `max_df` 필터와 임베딩 모델도 여기에 포함.
3. 평가. `gensim.models.CoherenceModel`을 통한 토픽 일관성(c_v), 토픽 다양성, 그리고 20개 표본의 사람이 읽는 검토.
4. 점검할 실패 양상. LDA는 불용어와 빈번한 단어를 빨아들이는 "정크 토픽". BERTopic은 모호한 문서들을 삼키는 -1 이상치 클러스터.

임베딩 모델의 컨텍스트 윈도우보다 긴 문서에 청킹 전략 없이 BERTopic을 쓰는 안은 받아들이지 마세요. 아주 짧은 텍스트(10토큰 미만의 트윗, 리뷰)에 LDA를 쓰면 일관성이 무너지므로 받아들이지 마세요. n_topics을 5 미만으로 정하는 안은 틀렸을 가능성이 높다고 표시하세요; 4만 개 미만 코퍼스에서 200 초과는 과도한 분할일 가능성이 높다고 표시하세요.
```

## 연습 문제

1. **쉬움.** 20 Newsgroups 데이터셋에 토픽 5개로 LDA를 학습시키세요. 토픽별 상위 10개 단어를 출력하고 각 토픽에 손으로 레이블을 붙여 보세요. 알고리즘이 실제 카테고리를 찾았나요?
2. **중간.** 같은 20 Newsgroups 부분집합에 BERTopic을 학습시키세요. LDA와 발견한 토픽 수, 상위 단어, 정성적 일관성을 비교하세요. 어느 쪽이 실제 카테고리를 더 깔끔하게 드러내나요?
3. **어려움.** 여러분 코퍼스에서 LDA와 BERTopic 모두의 c_v 일관성을 계산하세요. 각각 토픽 5, 10, 20, 50개로 돌려 보고, 일관성 대 토픽 수 그래프를 그리세요. 어느 방법이 토픽 수 변화에 더 안정적인지 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| 토픽 | 코퍼스가 다루는 주제 하나 | 단어 위의 확률 분포(LDA) 또는 비슷한 문서들의 묶음(BERTopic). |
| 혼합 소속(mixed membership) | 문서가 여러 토픽에 걸침 | LDA는 각 문서에 모든 토픽에 대한 분포를 부여함. |
| UMAP | 차원 축소 | 국소 구조를 보존하는 다양체 학습; BERTopic에서 사용. |
| HDBSCAN | 밀도 클러스터링 | 크기가 제각각인 클러스터를 찾음; 이상치에 "노이즈" 레이블(-1)을 부여. |
| c_v 일관성 | 토픽 품질 지표 | 슬라이딩 윈도우 안에서 상위 토픽 단어들의 점별 상호 정보량 평균. |

## 더 읽을거리

- [Blei, Ng, Jordan (2003). Latent Dirichlet Allocation](https://www.jmlr.org/papers/volume3/blei03a/blei03a.pdf) — LDA 원 논문.
- [Grootendorst (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure](https://arxiv.org/abs/2203.05794) — BERTopic 원 논문.
- [Röder, Both, Hinneburg (2015). Exploring the Space of Topic Coherence Measures](https://svn.aksw.org/papers/2015/WSDM_Topic_Evaluation/public.pdf) — c_v 등 일관성 척도를 소개한 논문.
- [BERTopic documentation](https://maartengr.github.io/BERTopic/) — 프로덕션 레퍼런스. 예제가 훌륭합니다.
