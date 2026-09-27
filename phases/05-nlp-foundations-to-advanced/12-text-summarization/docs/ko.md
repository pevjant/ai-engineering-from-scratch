> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 텍스트 요약 (Text Summarization)

> 추출형 시스템은 문서가 무슨 말을 했는지 알려 주고, 생성형(abstractive) 시스템은 저자가 무슨 뜻이었는지 알려 줍니다. 다른 과제이고, 다른 함정이 있는 과제입니다.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 02(BoW + TF-IDF), 페이즈 5 · 11(기계 번역)
**소요 시간:** 약 75분

## 해결할 문제

2,000 단어짜리 뉴스 기사가 피드에 들어왔습니다. 그것을 담아 내는 120단어가 필요합니다. 기사에서 가장 중요한 문장 세 개를 고를 수도 있고(추출형), 내용을 여러분의 말로 다시 쓸 수도 있습니다(생성형). 둘 다 요약이라 불리지만 완전히 다른 문제입니다.

추출형 요약은 순위 매기기 문제입니다. 모든 문장에 점수를 매기고 상위 `k`개를 돌려줍니다. 원문을 그대로 뜯어 오기 때문에 출력은 항상 문법적으로 옳습니다. 위험은 기사 전체에 흩어져 있는 내용을 놓치는 것입니다.

생성형 요약은 생성 문제입니다. 트랜스포머가 입력에 조건화된 새 텍스트를 만들어 냅니다. 출력은 유창하고 압축적이지만 원문에 없던 사실을 환각할 수 있습니다. 위험은 자신만만한 날조입니다.

이 레슨은 둘 다 만들되, 각각이 소유한 실패 모드와 함께 만듭니다.

## 핵심 개념

![추출형 TextRank vs 생성형 트랜스포머](../assets/summarization.svg)

**추출형.** 기사를 그래프로 취급합니다. 노드는 문장이고 간선은 유사도입니다. 그래프 위에서 PageRank(또는 그 비슷한 것)를 돌려, 문장이 다른 모든 것과 얼마나 연결돼 있는지로 점수를 매깁니다. 점수가 가장 높은 문장들이 요약입니다. 정석 구현은 **TextRank**(Mihalcea와 Tarau, 2004)입니다.

**생성형.** 트랜스포머 인코더-디코더(BART, T5, Pegasus)를 문서-요약 쌍으로 파인튜닝합니다. 추론 때 모델은 문서를 읽고 크로스 어텐션을 통해 요약을 토큰 단위로 생성합니다. 특히 Pegasus는 갭 문장(gap-sentence) 사전학습 목표를 써서 파인튜닝을 많이 하지 않고도 요약에 탁월합니다.

평가는 **ROUGE**(Recall-Oriented Understudy for Gisting Evaluation)로 합니다. ROUGE-1과 ROUGE-2는 유니그램, 바이그램 겹침을 점수화하고, ROUGE-L은 최장 공통 부분 수열을 점수화합니다. 높을수록 좋지만 ROUGE-L 40은 "좋음", 50은 "예외적" 정도입니다. 논문들은 셋 다 보고합니다. `rouge-score` 패키지를 쓰세요.

```figure
summarize-collapse
```

## 만들어 보기

### 단계 1: TextRank(추출형)

```python
import math
import re
from collections import Counter


def sentence_split(text):
    return re.split(r"(?<=[.!?])\s+", text.strip())


def similarity(s1, s2):
    w1 = Counter(s1.lower().split())
    w2 = Counter(s2.lower().split())
    intersection = sum((w1 & w2).values())
    denom = math.log(len(w1) + 1) + math.log(len(w2) + 1)
    if denom == 0:
        return 0.0
    return intersection / denom


def textrank(text, top_k=3, damping=0.85, iterations=50, epsilon=1e-4):
    sentences = sentence_split(text)
    n = len(sentences)
    if n <= top_k:
        return sentences

    sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                sim[i][j] = similarity(sentences[i], sentences[j])

    scores = [1.0] * n
    for _ in range(iterations):
        new_scores = [1 - damping] * n
        for i in range(n):
            total_out = sum(sim[i]) or 1e-9
            for j in range(n):
                if sim[i][j] > 0:
                    new_scores[j] += damping * sim[i][j] / total_out * scores[i]
        if max(abs(s - ns) for s, ns in zip(scores, new_scores)) < epsilon:
            scores = new_scores
            break
        scores = new_scores

    ranked = sorted(range(n), key=lambda k: scores[k], reverse=True)[:top_k]
    ranked.sort()
    return [sentences[i] for i in ranked]
```

이름 붙일 것 둘. 유사도 함수는 로그 정규화된 단어 겹침을 쓰는데, 이것이 원조 TextRank 변형입니다. TF-IDF 벡터의 코사인도 통합니다. 감쇠 계수 0.85와 반복 횟수는 PageRank의 기본값입니다.

### 단계 2: BART로 생성형 요약

```python
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

article = """(long news article text)"""

summary = summarizer(article, max_length=120, min_length=60, do_sample=False)
print(summary[0]["summary_text"])
```

BART-large-CNN은 CNN/DailyMail 코퍼스로 파인튜닝돼 있습니다. 뉴스 스타일 요약을 바로 만들어 냅니다. 다른 도메인(학술 논문, 대화, 법률)에는 해당하는 Pegasus 체크포인트를 쓰거나 여러분의 대상 데이터로 파인튜닝하세요.

### 단계 3: ROUGE 평가

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
scores = scorer.score(reference_summary, generated_summary)
print({k: round(v.fmeasure, 3) for k, v in scores.items()})
```

어형 분석(stemming)은 항상 켜세요. 없으면 "running"과 "run"이 다른 단어로 세어져 ROUGE가 일치를 과소 계산합니다.

### ROUGE 너머(2026년의 요약 평가)

ROUGE는 20년 동안 요약 평가의 지배 지표였지만, 2026년에는 이것 하나로는 부족합니다. NLG 논문의 대규모 메타 분석에 따르면:

- **BERTScore**(문맥화 임베딩 유사도)는 2023년까지 입지를 넓혔고 이제 대부분의 요약 논문에서 ROUGE와 함께 보고됩니다.
- **BARTScore**는 평가를 생성으로 취급합니다. 사전학습 BART가 원문을 조건으로 요약을 얼마나 그럴듯하게 여기는지로 점수를 매기죠.
- **MoverScore**(문맥화 임베딩 위의 Earth Mover's Distance)는 의미적 겹침을 ROUGE보다 더 잘 포착해서 2025년 요약 벤치마크 정상을 차지했습니다.
- **FactCC**와 **QA 기반 충실성**은 2021~2023년에 흔했고, 지금은 흔히 **G-Eval**(일관성, 정합성, 유창성, 관련성을 사고 연쇄(chain-of-thought) 추론으로 채점하는 GPT-4 프롬프트 체인)으로 대체됐습니다.
- **G-Eval**과 같은 LLM 심판 방식은 평가 기준표(rubric)가 잘 설계돼 있으면 인간 판단의 약 80%에 도달합니다.

프로덕션 추천: 레거시 비교용 ROUGE-L, 의미적 겹침용 BERTScore, 일관성과 사실성용 G-Eval을 보고하세요. 사람이 레이블한 요약 50~100개로 보정(calibration)합니다.

### 단계 4: 사실성 문제

생성형 요약은 환각에 취약합니다. 추출형 요약은 출력이 원문을 그대로 들어 오는 것이기 때문에 환각 위험이 훨씬 낮습니다. 다만 원문 문장이 맥락에서 떨어져 있거나, 낡았거나, 순서를 바꿔 인용되면 오해를 부를 수는 있습니다. 이것이 컴플라이언스와 인접한 콘텐츠에서 프로덕션 시스템이 여전히 추출형을 선호하는 가장 큰 이유입니다.

이름 붙어야 할 환각 유형들:

- **개체 바꿔치기.** 원문은 "John Smith". 요약은 "John Brown".
- **숫자 표류.** 원문은 "25,000". 요약은 "25 million".
- **극성 뒤집기.** 원문은 "rejected the offer(제안을 거절했다)". 요약은 "accepted the offer(제안을 수락했다)".
- **사실 날조.** 원문은 CEO를 언급하지 않음. 요약은 CEO가 승인했다고 말함.

통하는 평가 방법들:

- **FactCC.** 원문 문장과 요약 문장 사이의 수반(entailment)으로 학습한 이진 분류기. 사실/비사실을 예측합니다.
- **QA 기반 사실성.** 답이 원문에 있는 질문을 QA 모델에게 던집니다. 요약이 다른 답을 지지하면 플래그를 세웁니다.
- **개체 수준 F1.** 원문과 요약의 개체명을 비교합니다. 요약에만 있는 개체는 용의자입니다.

사실성이 중요한 사용자 대면 콘텐츠(뉴스, 의료, 법률, 금융)라면 추출형이 더 안전한 기본값입니다. 생성형에는 반드시 사실성 점검을 파이프라인 안에 넣으세요.

## 활용하기

2026년의 스택:

| 사용 사례 | 추천 |
|---------|-------------|
| 뉴스, 3~5문장 요약, 영어 | `facebook/bart-large-cnn` |
| 학술 논문 | `google/pegasus-pubmed` 또는 튜닝된 T5 |
| 다중 문서, 장문 | 32k 이상 컨텍스트를 가진 아무 LLM, 프롬프트로 |
| 대화 요약 | `philschmid/bart-large-cnn-samsum` |
| 추출형, 구조적으로 낮은 환각 위험 | TextRank 또는 `sumy`의 LSA / LexRank |

연산이 제약이 아니라면 2026년에는 긴 컨텍스트를 가진 LLM이 흔히 특화 모델을 이깁니다. 트레이드오프는 비용과 재현성입니다. 특화 모델이 더 일관된 출력을 줍니다.

## 출시하기

`outputs/skill-summary-picker.md`로 저장하세요:

```markdown
---
name: summary-picker
description: 추출형/생성형을 고르고, 라이브러리를 정하고, 사실성 점검을 붙입니다.
version: 1.0.0
phase: 5
lesson: 12
tags: [nlp, summarization]
---

과제(문서 유형, 컴플라이언스 요건, 길이, 연산 예산)가 주어지면 다음을 출력합니다:

1. 접근 방식. 추출형 또는 생성형(abstractive). 이유를 한 문장으로 설명합니다.
2. 시작 모델/라이브러리. 이름을 밝힙니다. `sumy.TextRankSummarizer`, `facebook/bart-large-cnn`, `google/pegasus-pubmed`, 또는 LLM 프롬프트.
3. 평가 계획. ROUGE-1, ROUGE-2, ROUGE-L(어형 분석(stemming)을 켠 `rouge-score` 사용). 생성형이라면 사실성 점검도 추가.
4. 파고들 실패 모드 하나. 개체 바꿔치기(entity swap)가 생성형 뉴스 요약에서 가장 흔합니다. 원문 개체가 요약에 나타나지 않는 샘플을 표시합니다.

의료, 법률, 금융, 규제 대상 콘텐츠에 사실성 게이트 없이 생성형 요약을 추천하는 일은 거부합니다. 모델의 컨텍스트 윈도우를 넘는 입력은 단순 잘림이 아니라 청크 단위 맵-리듀스(map-reduce) 요약이 필요하다고 표시합니다.
```

## 연습 문제

1. **(쉬움)** 뉴스 기사 5개에 TextRank를 돌리세요. 상위 3문장을 참조 요약과 비교하고 ROUGE-L을 측정합니다. CNN/DailyMail 스타일 기사에서 ROUGE-L 30~45가 나올 겁니다.
2. **(보통)** 개체 수준 사실성 평가를 구현하세요. 원문과 요약에서 개체명을 추출하고(spaCy), 원문 개체의 요약 내 재현율과 요약 개체의 원문 대비 정밀도를 계산합니다. 정밀도가 높고 재현율이 낮으면 안전하지만 짧다는 뜻이고, 정밀도가 낮으면 환각된 개체가 있다는 뜻입니다.
3. **(어려움)** CNN/DailyMail 기사 50개에서 BART-large-CNN을 LLM(Claude 또는 GPT-4)과 비교하세요. ROUGE-L, 사실성(개체 F1 기준), 요약당 비용을 보고합니다. 각각이 이기는 지점을 문서화합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 추출형 | 문장 고르기 | 원문의 문장을 그대로 돌려줌. 환각하지 않음. |
| 생성형(Abstractive) | 다시 쓰기 | 원문에 조건화된 새 텍스트를 생성. 환각할 수 있음. |
| ROUGE | 요약 지표 | 시스템 출력과 참조 요약 사이의 n-gram/LCS 겹침. |
| TextRank | 그래프 기반 추출형 | 문장 유사도 그래프 위의 PageRank. |
| 사실성 | 맞는지 여부 | 요약의 주장이 원문에 의해 뒷받침되는지 여부. |
| 환각 | 지어낸 내용 | 원문이 뒷받침하지 않는 요약 속 내용. |

## 더 읽을거리

- [Mihalcea and Tarau (2004). TextRank: Bringing Order into Texts](https://aclanthology.org/W04-3252/) — 추출형의 정석 논문.
- [Lewis et al. (2019). BART: Denoising Sequence-to-Sequence Pre-training](https://arxiv.org/abs/1910.13461) — BART 논문.
- [Zhang et al. (2019). PEGASUS: Pre-training with Extracted Gap-sentences](https://arxiv.org/abs/1912.08777) — Pegasus와 갭 문장 목표.
- [Lin (2004). ROUGE: A Package for Automatic Evaluation of Summaries](https://aclanthology.org/W04-1013/) — ROUGE 논문.
- [Maynez et al. (2020). On Faithfulness and Factuality in Abstractive Summarization](https://arxiv.org/abs/2005.00661) — 사실성 지형을 그린 논문.
