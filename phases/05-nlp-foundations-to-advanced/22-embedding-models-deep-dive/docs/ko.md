> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 임베딩 모델 — 2026년 심층 탐구

> Word2Vec은 단어당 벡터 하나를 줬습니다. 요즘 임베딩 모델은 구절당 벡터 하나를 줍니다. 교차 언어 지원에, 스파스·dense·멀티 벡터 관점을 모두 갖추고, 여러분의 인덱스에 맞는 크기로요. 잘못 고르면 RAG가 엉뚱한 것을 검색합니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 03(Word2Vec), 페이즈 5 · 14(정보 검색)
**시간:** 약 60분

## 문제 상황

여러분의 RAG 시스템은 40%의 확률로 엉뚱한 구절을 검색합니다. 범인은 벡터 데이터베이스나 프롬프트가 아닌 경우가 많습니다. 임베딩 모델입니다.

2026년에 임베딩을 고른다는 건 다섯 축을 넘나드는 선택입니다:

1. **Dense vs 스파스 vs 멀티 벡터.** 구절당 벡터 하나, 토큰당 벡터 하나, 아니면 가중치가 학습된 스파스 단어 주머니.
2. **언어 커버리지.** 영어 단일 언어 모델은 영어 전용 과제에서 여전히 이깁니다. 코퍼스가 섞여 있으면 다국어 모델이 이깁니다.
3. **컨텍스트 길이.** 512 토큰 vs 8,192 vs 32,768 — 그리고 실제 유효 용량은 광고된 최댓값의 60-70%인 경우가 흔합니다.
4. **차원 예산.** 전체 정밀도의 3,072개 float = 벡터당 12 KB. 1억 벡터면 저장 비용이 월 $1,300입니다. Matryoshka 절단으로 4배를 줄일 수 있습니다.
5. **오픈 vs 호스티드.** 오픈 웨이트는 스택과 데이터를 여러분이 통제한다는 뜻입니다. 호스티드는 통제를 '항상 최신'과 맞바꾸는 겁니다.

이 레슨은 트레이드오프를 이름 붙여 줍니다. 분기에 유행하던 걸 따라가는 게 아니라 근거로 고를 수 있게요.

## 핵심 개념

![Dense, 스파스, 멀티 벡터 임베딩](../assets/embedding-modes.svg)

**Dense 임베딩.** 구절당 벡터 하나(보통 384-3,072차원). 코사인 유사도가 의미적 근접성으로 구절의 순위를 매깁니다. OpenAI `text-embedding-3-large`, BGE-M3 dense 모드, Voyage-3. 기본 선택지.

**스파스 임베딩.** SPLADE 스타일입니다. 트랜스포머가 모든 어휘 토큰에 가중치를 예측한 뒤 대부분을 0으로 만듭니다. 결과는 크기 |vocab|의 스파스 벡터입니다. 어휘 매칭(BM25처럼)을 잡아내되 단어 가중치는 학습됩니다. 키워드가 많은 쿼리에 강합니다.

**멀티 벡터(late interaction).** ColBERTv2, Jina-ColBERT. 토큰당 벡터 하나입니다. MaxSim으로 점수를 매깁니다: 각 쿼리 토큰에 대해 가장 비슷한 문서 토큰을 찾아 점수를 합산합니다. 저장과 채점 비용이 더 크지만, 긴 쿼리와 도메인 특화 코퍼스에서 이깁니다.

**BGE-M3: 세 가지를 한 번에.** 하나의 모델이 dense, 스파스, 멀티 벡터 표현을 동시에 출력합니다. 각각 독립적으로 질의할 수 있고 점수는 가중 합으로 퓨전합니다. 하나의 체크포인트에서 유연성을 원할 때의 2026년 기본값입니다.

**Matryoshka Representation Learning.** 벡터의 앞 N개 차원만으로 유용한 독립 임베딩이 되도록 학습합니다. 1,536차원 벡터를 256차원으로 잘라도 정확도 약 1%를 지불하고 저장 공간 6배를 아낍니다. OpenAI text-3, Cohere v4, Voyage-4, Jina v5, Gemini Embedding 2, Nomic v1.5+가 지원합니다.

### MTEB 리더보드는 이야기의 일부만 말합니다

Massive Text Embedding Benchmark — 출시(2022) 때 8개 과제 유형에 걸친 56개 과제, MTEB v2에서는 100개 이상으로 확장됐습니다. 2026년 초 기준 Gemini Embedding 2가 검색 정점(67.71 MTEB-R)입니다. Cohere embed-v4가 범용 선두(65.2 MTEB), BGE-M3가 오픈 웨이트 다국어 선두(63.0)입니다. 리더보드는 필요하지만 충분하지 않습니다 — 반드시 여러분의 도메인에서 벤치마크하세요.

### 3계층 패턴

| 용도 | 패턴 |
|----------|---------|
| 빠른 1차 필터 | Dense 바이 인코더 (BGE-M3, text-3-small) |
| 리콜 부스트 | 스파스 (SPLADE, BGE-M3 sparse) + RRF 퓨전 |
| 상위 50개 정밀도 | 멀티 벡터 (ColBERTv2) 또는 크로스 인코더 리랭커 |

대부분의 프로덕션(운영 환경) 스택은 세 가지를 모두 씁니다.

```figure
gx-matryoshka
```

## 만들어 보기

### 단계 1: 베이스라인 — Sentence-BERT로 dense 임베딩

```python
from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")
corpus = [
    "The first iPhone launched in 2007.",
    "Apple released the iPod in 2001.",
    "Android is an operating system from Google.",
]
emb = encoder.encode(corpus, normalize_embeddings=True)

query = "When was the iPhone released?"
q_emb = encoder.encode([query], normalize_embeddings=True)[0]
scores = emb @ q_emb
print(sorted(enumerate(scores), key=lambda x: -x[1]))
```

`normalize_embeddings=True`는 내적이 코사인 유사도와 같아지게 만듭니다. 항상 설정하세요.

### 단계 2: Matryoshka 절단

```python
def truncate(vectors, dim):
    out = vectors[:, :dim]
    return out / np.linalg.norm(out, axis=1, keepdims=True)

emb_256 = truncate(emb, 256)
emb_128 = truncate(emb, 128)
```

절단 후 반드시 재정규화하세요. Nomic v1.5, OpenAI text-3, Voyage-4는 처음 몇 단계까지는 이 절단이 무손실이 되도록 학습돼 있습니다. Matryoshka가 아닌 모델(원조 Sentence-BERT)은 잘라내면 급격히 저하됩니다.

### 단계 3: BGE-M3 다기능성

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

output = model.encode(
    corpus,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=True,
)
# output["dense_vecs"]:    (n_docs, 1024)
# output["lexical_weights"]: {token_id: 가중치} 딕셔너리의 목록
# output["colbert_vecs"]:  (n_tokens, 1024) 배열들의 목록
```

인덱스 셋, 추론 호출 한 번. 점수 퓨전:

```python
dense_score = ... # dense_vecs 위의 코사인
sparse_score = model.compute_lexical_matching_score(q_lex, d_lex)
colbert_score = model.colbert_score(q_col, d_col)
final = 0.4 * dense_score + 0.2 * sparse_score + 0.4 * colbert_score
```

가중치는 여러분 도메인에서 튜닝하세요.

### 단계 4: 커스텀 과제에서 MTEB 평가

```python
from mteb import MTEB

tasks = ["ArguAna", "SciFact", "NFCorpus"]
evaluation = MTEB(tasks=tasks)
results = evaluation.run(encoder, output_folder="./mteb-results")
```

후보 모델들을 *대표성 있는* 부분집합에서 돌리세요. 리더보드 순위만 믿지 마세요 — 여러분 도메인이 중요합니다.

### 단계 5: 밑바닥부터 코사인 만들기

`code/main.py`를 보세요. 평균 해싱 트릭 임베딩(표준 라이브러리만 사용)입니다. 트랜스포머 임베딩과 경쟁할 수준은 아니지만 형태를 보여 줍니다: 토큰화 → 벡터 → 정규화 → 내적.

## 함정들

- **쿼리와 문서에 같은 모델.** 일부 모델(Voyage, Jina-ColBERT)은 비대칭 인코딩을 씁니다 — 쿼리와 문서가 서로 다른 경로를 지나갑니다. 모델 카드를 항상 확인하세요.
- **접두어 누락.** `bge-*` 모델은 쿼리 앞에 `"Represent this sentence for searching relevant passages: "`을 붙여야 합니다. 깜빡하면 리콜이 3-5포인트 벌어집니다.
- **과도한 Matryoshka 절단.** 1,536 → 256은 보통 안전합니다. 1,536 → 64는 아닙니다. 평가셋에서 검증하세요.
- **컨텍스트 잘림.** 대부분의 모델은 최대 길이를 넘는 입력을 조용히 잘라 버립니다. 긴 문서는 청킹이 필요합니다(레슨 23 참조).
- **지연 시간 꼬리 무시.** MTEB 점수는 p99 지연 시간을 숨깁니다. 600M 모델이 335M 모델보다 2포인트 나을 수 있지만 쿼리당 3배 비용이 들 수 있습니다.

## 사용해 보기

2026년 스택:

| 상황 | 선택 |
|-----------|------|
| 영어 전용, 빠름, API | `text-embedding-3-large` 또는 `voyage-3-large` |
| 오픈 웨이트, 영어 | `BAAI/bge-large-en-v1.5` |
| 오픈 웨이트, 다국어 | `BAAI/bge-m3` 또는 `Qwen3-Embedding-8B` |
| 긴 컨텍스트 (32k+) | Voyage-3-large, Cohere embed-v4, Qwen3-Embedding-8B |
| CPU 전용 배포 | Nomic Embed v2 (137M 파라미터, MoE) |
| 저장 공간 제약 | Matryoshka 절단 + int8 양자화 |
| 키워드 중심 쿼리 | SPLADE 스파스 추가, dense와 RRF 퓨전 |

2026년 패턴: BGE-M3 또는 text-3-large로 시작하고, MTEB로 여러분 도메인에서 평가하고, 도메인 특화 모델이 3포인트 이상 이기면 교체하세요.

## 출시하기

`outputs/skill-embedding-picker.md`로 저장하세요:

```markdown
---
name: embedding-picker
description: 주어진 코퍼스와 배포 환경에 맞는 임베딩 모델, 차원, 검색 모드 고르기.
version: 1.0.0
phase: 5
lesson: 22
tags: [nlp, embeddings, retrieval]
---

코퍼스(크기, 언어, 도메인, 평균 길이), 배포 대상(클라우드 / 엣지 / 온프레미스), 지연 시간 예산, 저장 예산이 주어지면 다음을 출력하세요:

1. 모델. 이름이 명시된 체크포인트 또는 API. 한 문장 근거.
2. 차원. 전체 / Matryoshka 절단 / int8 양자화. 저장 예산에 근거를 댈 것.
3. 모드. Dense / 스파스 / 멀티 벡터 / 하이브리드. 근거.
4. 모델 카드가 요구한다면 쿼리 접두어 / 템플릿.
5. 평가 계획. 도메인과 관련된 MTEB 과제 + nDCG@10을 쓰는 보류(held-out) 도메인 평가.

도메인 검증 없이 Matryoshka를 64차원 미만으로 자르는 추천은 받아들이지 마세요. 1만 구절 미만 코퍼스에 ColBERTv2를 추천하지 마세요(오버헤드가 정당화되지 않음). 512토큰 윈도우 모델에 긴 문서 코퍼스(8천 토큰 초과)를 보내는 구성은 표시하세요.
```

## 연습 문제

1. **쉬움.** `bge-small-en-v1.5`로 문장 100개를 전체 차원(384)과 Matryoshka 128로 각각 인코딩하세요. 쿼리 10개에서 MRR 하락을 측정하세요.
2. **중간.** 여러분 도메인의 구절 500개에서 BGE-M3의 dense, 스파스, colbert를 비교하세요. Recall@10에서 어느 쪽이 이기나요? RRF 퓨전이 최고의 단일 모드를 이기나요?
3. **어려움.** 후보 모델 세 개를 도메인 상위 2개 과제에서 MTEB로 돌리세요. MTEB 점수, 쿼리 100개 배치의 p99 지연 시간, 백만 쿼리당 비용($/1M queries)을 보고하세요. 파레토 최적인 모델을 고르세요.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| Dense 임베딩 | 그 벡터 | 텍스트당 고정 크기 벡터 하나. 순위 매기기에 코사인 유사도. |
| 스파스 임베딩 | 학습된 BM25 | 어휘 토큰당 가중치 하나; 대부분 0; 엔드투엔드로 학습. |
| 멀티 벡터 | ColBERT 스타일 | 토큰당 벡터 하나; MaxSim 채점; 인덱스는 더 크고 리콜은 더 좋음. |
| Matryoshka | 러시아 인형 트릭 | 앞 N개 차원이 그 자체로 유효한 더 작은 임베딩이 됨. |
| MTEB | 그 벤치마크 | Massive Text Embedding Benchmark — 출시 때 56개 과제, v2에서는 100개 이상. |
| BEIR | 검색 벤치마크 | 제로샷 검색 과제 18개; 교차 도메인 강건성 인용에 자주 등장. |
| 비대칭 인코딩 | 쿼리 ≠ 문서 경로 | 모델이 쿼리와 문서에 서로 다른 투영(projection)을 사용. |

## 더 읽을거리

- [Reimers, Gurevych (2019). Sentence-BERT](https://arxiv.org/abs/1908.10084) — 바이 인코더 원 논문.
- [Muennighoff et al. (2022). MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316) — 리더보드 원 논문.
- [Chen et al. (2024). BGE-M3: Multi-lingual, Multi-functionality, Multi-granularity](https://arxiv.org/abs/2402.03216) — 세 모드를 통합한 모델.
- [Kusupati et al. (2022). Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147) — 차원 사다리 학습 목표.
- [Santhanam et al. (2022). ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction](https://arxiv.org/abs/2112.01488) — 프로덕션의 late interaction.
- [MTEB leaderboard on Hugging Face](https://huggingface.co/spaces/mteb/leaderboard) — 실시간 랭킹.
