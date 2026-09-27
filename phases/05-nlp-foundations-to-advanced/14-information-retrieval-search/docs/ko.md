> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 정보 검색과 검색 시스템

> BM25는 정확하지만 잘 부서집니다. dense 검색은 그물을 넓게 던지지만 키워드를 놓칩니다. 하이브리드가 2026년의 기본값입니다. 나머지는 전부 튜닝 문제입니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 02(BoW + TF-IDF), 페이즈 5 · 04(GloVe, FastText, 서브워드)
**시간:** 약 75분

## 문제 상황

사용자가 "누군가 거짓말로 돈을 받으면 어떻게 되나"라고 입력하고, 그 상황을 실제로 다루는 조문("형법 제347조 사기죄" 같은)을 찾길 기대합니다. 키워드 검색은 이를 완전히 놓칩니다(겹치는 어휘가 없으니까요). 의미 기반 검색도 임베딩이 법률 텍스트로 학습되지 않았다면 놓칩니다. 진짜 검색 시스템은 둘 다 처리할 수 있어야 합니다.

정보 검색(IR)은 모든 RAG 시스템, 모든 검색창, 모든 문서 사이트의 퍼지(fuzzy) 조회 뒤에서 돌아가는 파이프라인입니다. 프로덕션(운영 환경)에서 통하는 2026년형 아키텍처는 단일 메서드가 아닙니다. 서로를 보완하는 메서드들의 사슬이고, 각 메서드는 바로 앞 단계가 놓친 실패를 잡아 줍니다.

이 레슨은 각 조각을 직접 만들어 보고, 각 조각이 어떤 실패를 잡아 주는지 이름을 붙여 줍니다.

## 핵심 개념

![하이브리드 검색: BM25 + dense + RRF + 크로스 인코더 리랭크](../assets/retrieval.svg)

네 층입니다. 필요한 것만 고르면 됩니다.

1. **스파스(sparse) 검색(BM25).** 빠르고, 정확한 일치에는 강력하지만, 의미에는 엉망입니다. 역색인(inverted index) 위에서 돌립니다. 수백만 문서에서도 쿼리당 10ms 미만. 법 조문 참조, 제품 코드, 에러 메시지, 고유명사를 정확히 잡아 줍니다.
2. **Dense 검색.** 쿼리와 문서를 벡터로 인코딩합니다. 최근접 이웃 검색을 합니다. 바꿔 말하기와 의미적 유사성을 잡아 냅니다. 한 글자만 달라도 정확한 키워드 일치는 놓칩니다. FAISS나 벡터 DB 기준 쿼리당 50-200ms.
3. **퓨전(fusion).** 스파스와 dense의 순위 목록을 합칩니다. RRF(Reciprocal Rank Fusion, 역수 순위 융합)가 쉬운 기본값입니다. 원 점수(스케일이 제각각이라)를 무시하고 순위 위치만 쓰기 때문입니다. 도메인에서 한 신호가 압도한다는 걸 알면 가중 퓨전도 선택지입니다.
4. **크로스 인코더 리랭크.** 퓨전 결과 상위 30개를 가져옵니다. 크로스 인코더(쿼리 + 문서를 함께 넣어 각 쌍의 점수를 매김)를 돌립니다. 상위 5개를 남깁니다. 크로스 인코더는 쌍당 처리 속도가 바이 인코더보다 느리지만 훨씬 정확합니다. 상위 30개에만 돌려서 비용을 분산시키는 겁니다.

3-웨이 검색(BM25 + dense + SPLADE 같은 learned-sparse)은 2026년 벤치마크에서 2-웨이보다 성능이 좋지만, learned-sparse 인덱스를 위한 인프라가 필요합니다. 대부분의 팀에게는 2-웨이 + 크로스 인코더 리랭크가 최적점입니다.

```figure
gx-hybrid-retrieval
```

## 만들어 보기

### 단계 1: 밑바닥부터 BM25 만들기

```python
import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return TOKEN_RE.findall(text.lower())


class BM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        if not corpus:
            raise ValueError("corpus must not be empty")
        self.corpus = [tokenize(d) for d in corpus]
        self.k1 = k1
        self.b = b
        self.n_docs = len(self.corpus)
        self.avg_dl = sum(len(d) for d in self.corpus) / self.n_docs
        self.df = Counter()
        for doc in self.corpus:
            for term in set(doc):
                self.df[term] += 1

    def idf(self, term):
        n = self.df.get(term, 0)
        return math.log(1 + (self.n_docs - n + 0.5) / (n + 0.5))

    def score(self, query, doc_idx):
        q_tokens = tokenize(query)
        doc = self.corpus[doc_idx]
        dl = len(doc)
        freq = Counter(doc)
        score = 0.0
        for term in q_tokens:
            f = freq.get(term, 0)
            if f == 0:
                continue
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
            score += self.idf(term) * numerator / denominator
        return score

    def rank(self, query, top_k=10):
        scored = [(self.score(query, i), i) for i in range(self.n_docs)]
        scored.sort(reverse=True)
        return scored[:top_k]
```

알아 둘 만한 파라미터 두 개입니다. `k1=1.5`는 단어 빈도 포화(saturation)를 조절합니다. 값이 클수록 단어 반복에 더 큰 가중치를 둡니다. `b=0.75`는 길이 정규화를 조절합니다. 0이면 문서 길이를 무시하고, 1이면 완전히 정규화합니다. 기본값은 원 논문에서 Robertson이 권장한 값이며 튜닝이 필요한 경우는 드뭅니다.

### 단계 2: 바이 인코더로 dense 검색하기

```python
from sentence_transformers import SentenceTransformer
import numpy as np


def build_dense_index(corpus, model_id="sentence-transformers/all-MiniLM-L6-v2"):
    encoder = SentenceTransformer(model_id)
    embeddings = encoder.encode(corpus, normalize_embeddings=True)
    return encoder, embeddings


def dense_search(encoder, embeddings, query, top_k=10):
    q_emb = encoder.encode([query], normalize_embeddings=True)
    sims = (embeddings @ q_emb.T).flatten()
    order = np.argsort(-sims)[:top_k]
    return [(float(sims[i]), int(i)) for i in order]
```

임베딩을 L2 정규화하면 내적이 코사인 유사도와 같아집니다. `all-MiniLM-L6-v2`는 384차원에 빠르고, 대부분의 영어 검색에 충분히 강력합니다. 다국어 작업이라면 `paraphrase-multilingual-MiniLM-L12-v2`를 쓰세요. 최고 정확도가 필요하면 `bge-large-en-v1.5`나 `e5-large-v2`를 쓰세요.

### 단계 3: 역수 순위 융합(RRF)

```python
def reciprocal_rank_fusion(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, (_, doc_idx) in enumerate(ranking):
            scores[doc_idx] = scores.get(doc_idx, 0.0) + 1.0 / (k + rank + 1)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(score, doc_idx) for doc_idx, score in fused]
```

`k=60` 상수는 RRF 원 논문에서 나온 값입니다. `k`가 클수록 순위 차이가 기여도에 미치는 영향이 평평해지고, 작을수록 상위 순위가 지배합니다. 60은 논문에 발표된 기본값이라 튜닝이 필요한 경우는 드뭅니다.

### 단계 4: 하이브리드 검색 + 리랭크

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def hybrid_search(query, bm25, encoder, dense_embeddings, corpus, top_k=5, pool_size=30, reranker=reranker):
    sparse_ranking = bm25.rank(query, top_k=pool_size)
    dense_ranking = dense_search(encoder, dense_embeddings, query, top_k=pool_size)
    fused = reciprocal_rank_fusion([sparse_ranking, dense_ranking])[:pool_size]

    pairs = [(query, corpus[doc_idx]) for _, doc_idx in fused]
    scores = reranker.predict(pairs)
    reranked = sorted(zip(scores, [doc_idx for _, doc_idx in fused]), reverse=True)
    return reranked[:top_k]
```

세 단계가 조합된 겁니다. BM25가 어휘 일치를 찾고, dense가 의미 일치를 찾고, RRF가 점수 보정 없이 두 순위를 합칩니다. 크로스 인코더는 상위 30개를 쿼리-문서 쌍으로 함께 넣고 재채점하는데, 이렇게 해야 바이 인코더가 놓친 세밀한 관련성을 잡을 수 있습니다. 상위 5개를 남깁니다.

### 단계 5: 평가

| 지표 | 의미 |
|--------|---------|
| Recall@k | 정답 문서가 존재하는 쿼리 중, 그 문서가 상위 k 안에 들어오는 비율 |
| MRR(Mean Reciprocal Rank, 평균 역수 순위) | 첫 번째 관련 문서 순위의 역수(1/rank) 평균 |
| nDCG@k | 관련/비관련의 이분법이 아니라 관련성의 단계까지 반영 |

RAG 특성상 가장 중요한 숫자는 리트리버(retriever)의 **Recall@k**입니다. 검색된 목록에 올바른 구절이 없다면, 리더(reader) 모델은 아무리 똑똑해도 답을 할 수 없습니다.

디버깅 팁: 실패하는 쿼리는 스파스 순위와 dense 순위를 diff 해 보세요. 한쪽은 정답 문서를 찾고 다른 쪽은 못 찾는다면, 어휘 불일치(해법: 빠진 쪽을 추가)이거나 의미적 모호함(해법: 더 좋은 임베딩 또는 리랭커)입니다.

## 사용해 보기

2026년 스택:

| 규모 | 스택 |
|-------|-------|
| 1k-100k 문서 | 인메모리 BM25 + `all-MiniLM-L6-v2` 임베딩 + RRF. 별도 DB 불필요. |
| 100k-1000만 문서 | dense에는 FAISS 또는 pgvector + BM25에는 Elasticsearch / OpenSearch. 병렬로 실행. |
| 1000만+ 문서 | 하이브리드를 지원하는 Qdrant / Weaviate / Vespa / Milvus. 상위 30개에 크로스 인코더 리랭크. |
| 최고 품질 프론티어 | 3-웨이(BM25 + dense + SPLADE) + ColBERT late-interaction 리랭킹 |

무엇을 고르든 평가 비용을 예산에 넣으세요. 엔드투엔드 RAG 정확도를 벤치마크하기 전에 검색 리콜부터 벤치마크하세요. 리더는 리트리버가 놓친 것을 만들어 낼 수 없습니다.

### 2026년 프로덕션 RAG에서 값비싸게 얻은 교훈

- **RAG 실패의 80%는 모델이 아니라 수집(ingestion)과 청킹에서 비롯됩니다.** 팀들은 LLM을 갈아끼우고 프롬프트를 튜닝하며 몇 주를 보내지만, 리트리버는 3번에 한 번씩 틀린 컨텍스트를 조용히 돌려주고 있죠. 청킹부터 고치세요.
- **청킹 전략이 청크 크기보다 중요합니다.** 고정 크기 분할은 표, 코드, 중첩된 헤더를 부숩니다. 문장 인지(sentence-aware) 분할이 기본값이고, 기술 문서와 제품 매뉴얼에는 의미 기반 또는 LLM 기반 청킹이 값을 합니다.
- **부모 문서(parent-doc) 패턴.** 정밀도를 위해 작은 "자식" 청크를 검색합니다. 같은 부모 섹션에서 나온 자식이 여러 개 나오면, 컨텍스트를 보존하기 위해 부모 블록으로 바꿔 넣습니다. 재학습 없이 답변 품질을 꾸준히 끌어올려 줍니다.
- **k_rerank=3이 보통 최적입니다.** 그 이상의 청크 하나하나는 답변 품질을 올리지 못한 채 토큰 비용과 생성 지연 시간만 더합니다. 여러분 환경에서 k=8이 여전히 k=3보다 낫다면, 리랭커가 제 몫을 못 하고 있는 겁니다.
- **HyDE / 쿼리 확장.** 쿼리로부터 가상의 답변을 생성하고, 그것을 임베딩해서 검색합니다. 짧은 질문과 긴 문서 사이의 표현 간극을 메워 줍니다. 학습 없이 공짜로 정밀도를 올리는 방법입니다.
- **컨텍스트 예산은 8K 토큰 미만.** 그 한도에 일관되게 걸린다면 리랭커 임계값이 너무 느슨하다는 뜻입니다.
- **모든 것의 버전을 남기세요.** 프롬프트, 청킹 규칙, 임베딩 모델, 리랭커. 아무 드리프트(drift)나 답변 품질을 조용히 망가뜨립니다. 충실도(faithfulness), 컨텍스트 정밀도, 미답변률에 CI 게이트를 걸면 사용자가 보기 전에 회귀를 막아 줍니다.
- **3-웨이 검색(BM25 + dense + SPLADE 같은 learned-sparse)은 2-웨이보다 낫습니다** 2026년 벤치마크에서, 특히 고유명사와 의미가 섞인 쿼리에서 그렇습니다. 인프라가 SPLADE 인덱스를 지원하면 도입하세요.

2026년 업계 측정에 따르면 제대로 된 검색 설계는 환각을 70-90% 줄입니다. RAG 성능 향상의 대부분은 모델 파인튜닝이 아니라 더 나은 검색에서 나옵니다.

## 출시하기

`outputs/skill-retrieval-picker.md`로 저장하세요:

```markdown
---
name: retrieval-picker
description: 주어진 코퍼스와 쿼리 패턴에 맞는 검색 스택을 고르기.
version: 1.0.0
phase: 5
lesson: 14
tags: [nlp, retrieval, rag, search]
---

요구 사항(코퍼스 크기, 쿼리 패턴, 지연 시간 예산, 품질 기준, 인프라 제약)이 주어지면 다음을 출력하세요:

1. 스택. BM25만, dense만, 하이브리드(BM25 + dense + RRF), 하이브리드 + 크로스 인코더 리랭크, 또는 3-웨이(BM25 + dense + learned-sparse).
2. Dense 인코더. 구체적인 모델 이름을 말하세요. 언어, 도메인, 컨텍스트 길이에 맞춥니다.
3. 리랭커. 사용한다면 구체적인 크로스 인코더 모델 이름을 말하세요. 상위 30개에 리랭크하면 30-100ms의 지연 시간이 추가된다는 점을 표시하세요.
4. 평가 계획. Recall@10이 리트리버의 1차 지표입니다. 다중 정답에는 MRR. 먼저 베이스라인을 세우고, 증분 개선은 그 기준으로 측정합니다.

고유명사, 에러 코드, 제품 SKU가 섞인 코퍼스에는, dense가 정확한 일치를 잘 처리한다는 근거를 사용자가 제시하지 않는 한 dense-only를 추천하지 마세요. 최종 상위 5개가 사용자의 답변을 결정하는 고위험 검색(법률, 의료)에서는 리랭킹을 건너뛰는 방안을 받아들이지 마세요.
```

## 연습 문제

1. **쉬움.** 위의 `hybrid_search`를 500문서 코퍼스에 구현하세요. 20개 쿼리로 테스트하고, BM25만 썼을 때, dense만 썼을 때, 하이브리드일 때의 Recall@5를 비교하세요.
2. **중간.** MRR 계산을 추가하세요. 정답 문서를 아는 테스트 쿼리마다 BM25, dense, 하이브리드 순위에서 정답 문서의 순위를 찾고, 각각의 MRR을 보고하세요.
3. **어려움.** MultipleNegativesRankingLoss(Sentence Transformers)로 여러분 도메인의 dense 인코더를 파인튜닝하세요. 쿼리-문서 쌍 500개로 학습셋을 만들고, 파인튜닝 전후 리콜을 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| BM25 | 키워드 검색 | Okapi BM25. 단어 빈도, IDF, 길이로 문서 점수를 매김. |
| Dense 검색 | 벡터 검색 | 쿼리 + 문서를 벡터로 인코딩해 최근접 이웃을 찾음. |
| 바이 인코더 | 임베딩 모델 | 쿼리와 문서를 독립적으로 인코딩. 쿼리 시점에 빠름. |
| 크로스 인코더 | 리랭커 모델 | 쿼리 + 문서를 함께 인코딩. 느리지만 정확함. |
| RRF | 순위 융합 | `1/(k + rank)`를 합산해 두 순위를 결합. |
| Recall@k | 검색 지표 | 관련 문서가 상위 k 안에 들어오는 쿼리의 비율. |

## 더 읽을거리

- [Robertson and Zaragoza (2009). The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf) — BM25의 정석적인 정리.
- [Karpukhin et al. (2020). Dense Passage Retrieval for Open-Domain QA](https://arxiv.org/abs/2004.04906) — DPR, 바이 인코더의 대표주자.
- [Formal et al. (2021). SPLADE: Sparse Lexical and Expansion Model](https://arxiv.org/abs/2107.05720) — dense와의 격차를 메우는 learned-sparse 리트리버.
- [Cormack, Clarke, Büttcher (2009). Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) — RRF 원 논문.
- [Khattab and Zaharia (2020). ColBERT: Efficient and Effective Passage Search](https://arxiv.org/abs/2004.12832) — late-interaction 검색.
