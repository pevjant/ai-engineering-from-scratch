> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 질의응답 시스템 (Question Answering Systems)

> 세 가지 시스템이 현대 QA를 빚었습니다. 추출형은 범위를 찾았고, 검색 증강은 문서에 근거를 댔고, 생성형은 답을 만들어 냈습니다. 오늘날 모든 AI 어시스턴트는 이 셋의 혼합물입니다.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 11(기계 번역), 페이즈 5 · 10(어텐션 메커니즘)
**소요 시간:** 약 75분

## 해결할 문제

사용자가 "When did the first iPhone launch?"라고 입력하고 "2007년 6월 29일"이라는 대답을 기대합니다. "Apple의 역사는 길고 다채롭습니다"가 아니라, 문맥 없이 홀로 덩그러니 놓인 "2007"도 아니고. 직접적이고, 근거가 있고, 정확한 대답이죠.

지난 10년 동안 QA를 지배한 아키텍처는 세 가지입니다.

- **추출형 QA.** 질문과, 그 안에 답이 있다는 걸 아는 지문이 주어지면 지문 안에서 답 범위의 시작 인덱스와 끝 인덱스를 찾습니다. SQuAD가 정석 벤치마크입니다.
- **오픈 도메인 QA.** 지문이 주어지지 않습니다. 먼저 관련 지문을 검색한 다음 답을 추출하거나 생성합니다. 오늘날 모든 RAG 파이프라인의 기반입니다.
- **생성형/클로즈드북(closed-book) QA.** 대형 언어 모델이 파라메트릭 메모리로부터 대답합니다. 검색 없음. 추론은 가장 빠르지만 사실 관계에서는 가장 신뢰가 못 갑니다.

2026년의 흐름은 하이브리드입니다. 가장 나은 지문 몇 개를 검색한 뒤, 생성 모델에게 그 지문에 근거해 답하라고 프롬프트합니다. 그것이 RAG이고, 레슨 14가 검색 절반을 깊이 다룹니다. 이 레슨은 QA 절반을 만듭니다.

## 핵심 개념

![QA 아키텍처: 추출형, 검색 증강, 생성형](../assets/qa.svg)

**추출형.** 질문과 지문을 함께 트랜스포머(BERT 계열)로 인코딩합니다. 답의 시작 토큰 인덱스와 끝 토큰 인덱스를 예측하는 헤드 둘을 학습시킵니다. 손실은 유효한 위치들에 대한 교차 엔트로피입니다. 출력은 지문에서 뽑은 범위(span)입니다. 구조상 환각하지 않고, 구조상 지문이 답할 수 없는 질문은 처리하지 못합니다.

**검색 증강(RAG).** 두 단계입니다. 첫째, 검색기(retriever)가 코퍼스에서 상위 `k`개 지문을 찾습니다. 둘째, 판독기(reader, 추출형 또는 생성형)가 그 지문들을 이용해 답을 만듭니다. 검색기-판독기 분리 덕분에 둘을 따로따로 학습시키고 평가할 수 있습니다. 현대 RAG는 둘 사이에 재순위기(reranker)를 얹는 경우가 많습니다.

**생성형.** 디코더 전용 LLM(GPT, Claude, Llama)이 학습된 가중치로부터 대답합니다. 검색 단계 없음. 흔한 지식에는 탁월하고, 희귀하거나 최신 사실에는 재앙적입니다. 환각률은 사전학습 데이터에서의 사실 빈도와 반비례합니다.

```figure
qa-span
```

## 만들어 보기

### 단계 1: 사전학습 모델로 추출형 QA

```python
from transformers import pipeline

qa = pipeline("question-answering", model="deepset/roberta-base-squad2")

passage = (
    "Apple Inc. released the first iPhone on June 29, 2007. "
    "The device was announced by Steve Jobs at Macworld in January 2007."
)
question = "When was the first iPhone released?"

answer = qa(question=question, context=passage)
print(answer)
```

```python
{'score': 0.98, 'start': 57, 'end': 70, 'answer': 'June 29, 2007'}
```

`deepset/roberta-base-squad2`는 답할 수 없는 질문까지 포함한 SQuAD 2.0으로 학습됐습니다. 기본값에서 `question-answering` 파이프라인은 모델의 null 점수가 이기는 경우에도 점수가 가장 높은 범위를 돌려줍니다. 즉 자동으로 빈 답을 돌려주지는 *않습니다*. 명시적인 "답 없음" 동작을 원하면 파이프라인 호출에 `handle_impossible_answer=True`를 넘기세요. 그러면 null 점수가 모든 범위 점수를 넘어설 때만 빈 답을 돌려줍니다. 어느 쪽이든 항상 `score` 필드를 확인하세요.

### 단계 2: 검색 증강 파이프라인(개략)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

corpus = [
    "Apple Inc. released the first iPhone on June 29, 2007.",
    "Macworld 2007 featured the iPhone announcement by Steve Jobs.",
    "Android launched in 2008 as Google's mobile operating system.",
    "The first iPod was released in 2001.",
]
corpus_embeddings = encoder.encode(corpus, normalize_embeddings=True)


def retrieve(question, top_k=2):
    q_emb = encoder.encode([question], normalize_embeddings=True)
    sims = (corpus_embeddings @ q_emb.T).squeeze()
    order = np.argsort(-sims)[:top_k]
    return [corpus[i] for i in order]


def answer(question):
    passages = retrieve(question, top_k=2)
    combined = " ".join(passages)
    return qa(question=question, context=combined)


print(answer("When was the first iPhone released?"))
```

2단계 파이프라인입니다. 밀집(dense) 검색기(Sentence-BERT)가 의미적 유사도로 관련 지문을 찾고, 추출형 판독기(RoBERTa-SQuAD)가 합쳐진 상위 지문들에서 답 범위를 뽑습니다. 작은 코퍼스에서는 잘 돌아갑니다. 백만 문서짜리 코퍼스에는 FAISS나 벡터 데이터베이스를 쓰세요.

### 단계 3: RAG를 곁들인 생성형

```python
def rag_generate(question, llm):
    passages = retrieve(question, top_k=3)
    prompt = f"""Context:
{chr(10).join('- ' + p for p in passages)}

Question: {question}

Answer using only the context above. If the context does not contain the answer, say "I don't know."
"""
    return llm(prompt)
```

프롬프트 패턴이 중요합니다. 모델에게 컨텍스트에 근거하라고, 컨텍스트가 부족하면 "I don't know"라고 답하라고 명시적으로 말해 주면, 순진한 프롬프팅에 비해 환각률이 40~60% 줄어듭니다. 더 정교한 패턴은 인용, 신뢰도 점수, 구조화된 추출을 더합니다.

### 단계 4: 실제 세상을 반영하는 평가

SQuAD는 **정확 일치(Exact Match, EM)**와 **토큰 수준 F1**을 씁니다. EM은 정규화(소문자화, 구두점 제거, 관사 제거) 후의 엄격한 일치입니다. 예측이 정확히 일치하거나 0점이거나 둘 중 하나죠. F1은 예측과 참조 사이의 토큰 겹침으로 계산해 부분 점수를 줍니다. 둘 다 바꿔 쓰기에는 후하답니다. "June 29, 2007" vs "June 29th, 2007"은 보통 EM 0점(서수사가 정규화를 깨뜨립니다)이지만 겹치는 토큰으로 꽤 많은 F1은 받습니다.

프로덕션 QA에서는:

- **답변 정확도**(LLM 판정 또는 사람 판정. 지표는 의미적 동치를 잡아 내지 못하기 때문).
- **인용 정확도.** 인용된 지문이 실제로 답을 뒷받침하는가? 생성된 인용과 검색된 지문 사이 문자열 매치로 자동 점검이 쉽습니다.
- **거절 보정(refusal calibration).** 답이 검색된 지문에 없을 때 시스템이 올바르게 "모르겠다"고 하는가? 거짓 확신률을 측정합니다.
- **검색 재현율.** 판독기를 평가하기 전에, 검색기가 올바른 지문을 상위 `k`에 넣는지 측정합니다. 빠진 지문은 판독기가 구원할 수 없습니다.

### RAGAS: 2026년의 프로덕션 평가 프레임워크

`RAGAS`는 RAG 시스템 전용으로 만들어졌고 2026년 출시 기본값입니다. 정답(gold reference)을 요구하지 않고 네 차원을 채점합니다.

- **충실성(Faithfulness).** 답변의 각 주장이 검색된 컨텍스트에서 왔는가? NLI 기반 수반(entailment)으로 측정합니다. 여러분의 1차 환각 지표입니다.
- **답변 관련성.** 답변이 질문에 부합하는가? 답변에서 가설 질문들을 생성해 실제 질문과 비교하는 방식으로 측정합니다.
- **컨텍스트 정밀도.** 검색된 청크 중 실제로 관련 있었던 것의 비율은? 정밀도가 낮으면 프롬프트에 노이즈가 섞인 겁니다.
- **컨텍스트 재현율.** 검색된 집합에 필요한 정보가 모두 담겼는가? 재현율이 낮으면 판독기가 성공할 수 없습니다.

참조 불필요 채점 덕분에 엄선된 정답 없이도 실시간 프로덕션 트래픽 위에서 평가할 수 있습니다. 정확 일치 지표가 무용지물인 개방형 질문에는 그 위에 LLM 심판을 얹으세요.

`pip install ragas`. 검색기 + 판독기를 꽂으세요. 쿼리당 스칼라 넷을 얻습니다. 회귀에 알림을 겁니다.

## 활용하기

2026년의 스택.

| 사용 사례 | 추천 |
|---------|-------------|
| 지문이 주어지고 답 범위를 찾기 | `deepset/roberta-base-squad2` |
| 고정된 코퍼스 위에서, 클로즈드북은 불허 | RAG: 밀집 검색기 + LLM 판독기 |
| 문서 저장소 위의 실시간 처리 | 하이브리드(BM25 + 밀집) 검색기 + 재순위기를 곁들인 RAG(레슨 14) |
| 대화형 QA(후속 질문) | 대화 기록을 가진 LLM + 매 턴마다 RAG |
| 고도의 사실성이 필요한 규제 도메인 | 권위 있는 코퍼스 위의 추출형. 생성형 단독은 결코 |

추출형 QA는 LLM을 곁들인 RAG가 더 많은 사례를 처리하는 2026년에 유행 뒤전입니다. 그래도 문자 그대로의 인용이 필요한 곳에서는 여전히 출시됩니다. 법률 리서치, 규제 준수, 감사 도구가 그렇습니다.

## 출시하기

`outputs/skill-qa-architect.md`로 저장하세요:

```markdown
---
name: qa-architect
description: QA 아키텍처, 검색 전략, 평가 계획을 고릅니다.
version: 1.0.0
phase: 5
lesson: 13
tags: [nlp, qa, rag]
---

요구 사항(코퍼스 크기, 질문 유형, 사실성 제약, 지연 시간 예산)이 주어지면 다음을 출력합니다:

1. 아키텍처. 추출형, 추출형 판독기를 곁들인 RAG, 생성형 판독기를 곁들인 RAG, 또는 클로즈드북 LLM. 한 문장으로 이유를 댑니다.
2. 검색기. 없음, BM25, 밀집(인코더 이름을 밝힘), 또는 하이브리드.
3. 판독기. SQuAD 튜닝 모델, 이름을 밝힌 LLM, 또는 "도메인 파인튜닝 DistilBERT".
4. 평가. 추출형 벤치마크에는 EM + F1. 프로덕션에는 답변 정확도 + 인용 정확도 + 거절 보정. 무엇을 어떻게 측정하는지 밝힙니다.

규제나 컴플라이언스에 민감한 질문에 클로즈드북 LLM 답변을 권하는 일은 거부합니다. 검색 재현율 베이스라인이 없는 QA 시스템도 거부합니다(검색기가 올바른 지문을 가져왔는지 모르면 판독기를 평가할 수 없습니다). 멀티홉(multi-hop) 추론이 필요한 질문은 HotpotQA로 학습된 시스템 같은 전용 멀티홉 검색기가 필요하다고 표시합니다.
```

## 연습 문제

1. **(쉬움)** 위의 SQuAD 추출형 파이프라인을 Wikipedia 지문 10개에 세팅하세요. 질문 10개를 손으로 만들고 답이 얼마나 자주 맞는지 측정합니다. 지문과 질문이 깨끗하면 7~9개는 맞게 나올 겁니다.
2. **(보통)** 거절 분류기를 추가하세요. 상위 검색 점수가 임계값(예: 코사인 0.3) 미만이면 판독기를 부르는 대신 "모르겠습니다"를 돌려줍니다. 홀드아웃 세트로 임계값을 조정합니다.
3. **(어려움)** 원하는 코퍼스 1만 문서 위에 RAG 파이프라인을 만드세요. RRF 융합을 곁들인 하이브리드 검색(BM25 + 밀집)을 구현합니다(레슨 14 참조). 하이브리드 단계가 있을 때와 없을 때의 답변 정확도를 측정하고, 어떤 질문 유형이 가장 이득 보는지 문서화합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 추출형 QA | 답 범위 찾기 | 주어진 지문 안에서 답의 시작/끝 인덱스를 예측함. |
| 오픈 도메인 QA | 코퍼스 위의 QA | 주어진 지문이 없음. 검색한 다음 답해야 함. |
| RAG | 검색 후 생성 | 검색 증강 생성(Retrieval-Augmented Generation). 검색기 + 판독기 파이프라인. |
| SQuAD | 정석 벤치마크 | Stanford Question Answering Dataset. EM + F1 지표. |
| 환각 | 지어낸 답 | 검색된 컨텍스트가 뒷받침하지 않는 판독기 출력. |
| 거절 보정 | 침묵할 때를 앎 | 답할 수 없을 때 시스템이 올바르게 "모르겠다"고 말함. |

## 더 읽을거리

- [Rajpurkar et al. (2016). SQuAD: 100,000+ Questions for Machine Comprehension of Text](https://arxiv.org/abs/1606.05250) — 그 벤치마크 논문.
- [Karpukhin et al. (2020). Dense Passage Retrieval for Open-Domain QA](https://arxiv.org/abs/2004.04906) — DPR, QA의 정석 밀집 검색기.
- [Lewis et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) — RAG라는 이름을 붙인 논문.
- [Gao et al. (2023). Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997) — 종합적인 RAG 서베이.
