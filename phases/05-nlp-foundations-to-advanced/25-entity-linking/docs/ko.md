# 개체 연결과 개체 판별 (Entity Linking & Disambiguation)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> NER이 "Paris"를 찾아 냈습니다. 개체 연결(entity linking)은 이제 결정합니다: 프랑스 파리? 파리스 힐튼? 텍사스주 파리? 트로이의 왕자 파리스? 연결이 없으면 지식 그래프는 계속 모호한 채로 남습니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 06(NER), 페이즈 5 · 24(상호 참조 해소)
**소요 시간:** 약 60분

## 문제 상황

"Jordan beat the press."라는 문장이 있습니다. NER이 "Jordan"을 PERSON으로 태깅했습니다. 좋습니다. 그런데 *어느* Jordan일까요?

- 마이클 조던(농구 선수)?
- 마이클 B. 조던(배우)?
- 마이클 I. 조던(버클리 ML 교수 — 맞습니다, ML 논문에서 실제로 벌어지는 혼동입니다)?
- 요르단(국가)?
- Jordan(히브리어 이름)?

개체 연결(EL)은 각 멘션을 지식 베이스의 유일한 항목 하나에 연결합니다: Wikidata, Wikipedia, DBpedia, 또는 여러분의 도메인 KB. 두 가지 하위 과제가 있습니다:

1. **후보 생성.** "Jordan"이 주어졌을 때, 가능성 있는 KB 항목은 무엇일까?
2. **개체 판별(disambiguation).** 문맥이 주어졌을 때, 어느 후보가 옳은가?

두 단계 모두 학습 가능하고, 모두 벤치마크로 평가됩니다. 결합된 파이프라인은 10년째 그대로입니다 — 바뀌는 것은 개체 판별기의 품질입니다.

## 개념

![개체 연결 파이프라인: 멘션 → 후보 → 판별된 개체](../assets/entity-linking.svg)

**후보 생성.** 멘션의 표면형("Jordan")이 주어지면 별칭 인덱스에서 후보를 찾습니다. Wikipedia 별칭 사전은 대부분의 고유명사 개체를 커버합니다: "JFK" → John F. Kennedy, Jacqueline Kennedy, JFK 공항, JFK(영화). 전형적인 인덱스는 멘션당 10~30개의 후보를 반환합니다.

**개체 판별: 세 가지 접근법.**

1. **사전 확률 + 문맥(Milne & Witten, 2008).** `P(entity | mention) × context-similarity(entity, text)`. 잘 동작하고, 빠르고, 학습이 필요 없습니다.
2. **임베딩 기반(ESS / REL / Blink).** 멘션 + 문맥을 인코딩하고, 각 후보의 설명을 인코딩한 뒤, 코사인 유사도가 최대인 것을 고릅니다. 2020-2024년의 기본값.
3. **생성형(GENRE, 2021; LLM 기반, 2023+).** 개체의 정식(canonical) 이름을 토큰 단위로 디코딩합니다. 유효한 개체 이름의 트라이(trie)로 제약해 출력이 반드시 유효한 KB id가 되도록 보장합니다.

**엔드투엔드 vs 파이프라인.** 현대 모델(ELQ, BLINK, ExtEnD, GENRE)은 NER + 후보 생성 + 개체 판별을 한 번에 돌립니다. 그래도 파이프라인 방식이 프로덕션(운영 환경)에서는 우세합니다. 구성 요소를 교체할 수 있기 때문입니다.

### 두 가지 측정값

- **멘션 재현율(후보 생성).** 정답 멘션 중에서 올바른 KB 항목이 후보 목록에 들어 있는 비율. 파이프라인 전체의 하한선입니다.
- **개체 판별 정확도 / F1.** 후보가 올바를 때, top-1이 맞는 빈도.

항상 둘 다 보고하세요. 후보 재현율 80%에서 개체 판별 정확도 99%인 시스템은 결국 80%짜리 파이프라인입니다.

```figure
gx-entity-linking
```

## 직접 만들기

### 단계 1: Wikipedia 리다이렉트로 별칭 인덱스 만들기

```python
alias_to_entities = {
    "jordan": ["Q41421 (Michael Jordan)", "Q810 (Jordan, country)", "Q254110 (Michael B. Jordan)"],
    "paris":  ["Q90 (Paris, France)", "Q663094 (Paris, Texas)", "Q55411 (Paris Hilton)"],
    "apple":  ["Q312 (Apple Inc.)", "Q89 (apple, fruit)"],
}
```

Wikipedia 별칭 데이터: 약 1,800만 개의 (별칭, 개체) 쌍. Wikidata 덤프에서 내려받으세요. 역색인(inverted index)으로 저장합니다.

### 단계 2: 문맥 기반 개체 판별

```python
def disambiguate(mention, context, alias_index, entity_desc):
    candidates = alias_index.get(mention.lower(), [])
    if not candidates:
        return None, 0.0
    context_words = set(tokenize(context))
    best, best_score = None, -1
    for entity_id in candidates:
        desc_words = set(tokenize(entity_desc[entity_id]))
        union = len(context_words | desc_words)
        score = len(context_words & desc_words) / union if union else 0.0
        if score > best_score:
            best, best_score = entity_id, score
    return best, best_score
```

자카드(Jaccard) 중첩은 장난감 수준입니다. 임베딩의 코사인 유사도로 바꾸세요(트랜스포머 버전은 `code/main.py`의 step-2 참조).

### 단계 3: 임베딩 기반(BLINK 스타일)

```python
from sentence_transformers import SentenceTransformer
encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_mention(text, mention_span):
    start, end = mention_span
    marked = f"{text[:start]} [MENTION] {text[start:end]} [/MENTION] {text[end:]}"
    return encoder.encode([marked], normalize_embeddings=True)[0]

def embed_entity(entity_id, description):
    return encoder.encode([f"{entity_id}: {description}"], normalize_embeddings=True)[0]
```

인덱싱 시점에 모든 KB 개체를 한 번씩 임베딩해 둡니다. 질의 시점에는 멘션 + 문맥을 한 번 임베딩하고, 후보 풀과 내적해서 최댓값을 고릅니다.

### 단계 4: 생성형 개체 연결(개념)

GENRE는 개체의 Wikipedia 제목을 글자 단위로 디코딩합니다. 제약 디코딩(레슨 20 참조)은 유효한 제목만 출력되도록 보장합니다. KB 기반 트라이와 긴밀하게 결합됩니다. 현대의 후속 기술은 REL-GEN과 구조화 출력을 쓰는 LLM 프롬프트 방식 EL입니다.

```python
prompt = f"""Text: {text}
Mention: {mention}
List the best Wikipedia title for this mention.
Respond with JSON: {{"title": "..."}}"""
```

화이트리스트(Outlines의 `choice`)와 결합하면, 2026년에 출시할 수 있는 가장 간단한 EL 파이프라인입니다.

### 단계 5: AIDA-CoNLL로 평가하기

AIDA-CoNLL은 표준 EL 벤치마크입니다: Reuters 기사 1,393개, 멘션 3만 4천 개, Wikipedia 개체. KB 내 정확도(`P@1`)와 KB 외 NIL 탐지율을 보고합니다.

## 흔한 실수

- **NIL 처리.** 어떤 멘션은 KB에 없습니다(신생 개체, 잘 모르는 인물). 시스템은 잘못된 개체를 지어낼 게 아니라 NIL을 예측해야 합니다. 별도로 측정합니다.
- **멘션 경계 오류.** 상류의 NER이 일부 span만 잡아냅니다("Bank of America"를 "Bank"만 태깅). EL 재현율이 떨어집니다.
- **인기 편향.** 학습된 시스템은 자주 등장하는 개체를 과도하게 예측합니다. ML 논문에서 나온 "Michael I. Jordan" 멘션이 종종 농구 선수 조던으로 연결됩니다.
- **교차 언어 EL.** 중국어 텍스트의 멘션을 영어 Wikipedia 개체에 연결하는 문제입니다. 다국어 인코더나 번역 단계가 필요합니다.
- **KB의 노후화.** 새 회사, 새 사건, 새 인물은 작년 Wikipedia 덤프에 없습니다. 프로덕션 파이프라인에는 갱신 루프가 필요합니다.

## 활용하기

2026년의 표준 스택:

| 상황 | 선택지 |
|-----------|------|
| 범용 영어 + Wikipedia | BLINK 또는 REL |
| 교차 언어, KB = Wikipedia | mGENRE |
| LLM 친화적, 하루 멘션 수가 적음 | 후보 목록 + 제약 JSON으로 Claude/GPT-4 프롬프트 |
| 도메인 특화 KB(의료, 법률) | KB 인지 검색을 얹은 커스텀 BERT + 도메인 AIDA 스타일 셋으로 파인튜닝 |
| 극저지연 | 정확 일치 사전 확률만 사용(Milne-Witten 베이스라인) |
| 연구 SOTA | GENRE / ExtEnD / 생성형 LLM-EL |

2026년에 실제로 출시되는 프로덕션 패턴: NER → coref → 멘션마다 EL → 클러스터를 정리해 클러스터당 하나의 정식 개체로. 출력: 문서의 각 개체당 KB id 하나(멘션당 하나가 아님).

## 출시하기

`outputs/skill-entity-linker.md`로 저장하세요:

```markdown
---
name: entity-linker
description: Design an entity linking pipeline — KB, candidate generator, disambiguator, evaluation.
version: 1.0.0
phase: 5
lesson: 25
tags: [nlp, entity-linking, knowledge-graph]
---

사용 사례(도메인 KB, 언어, 처리량, 지연 시간 예산)가 주어지면 다음을 출력합니다:

1. 지식 베이스. Wikidata / Wikipedia / 자체 KB. 버전 날짜. 갱신 주기.
2. 후보 생성기. 별칭 인덱스(alias-index), 임베딩, 또는 하이브리드. 목표 mention recall @ K.
3. 개체 판별기(disambiguator). 사전 확률 + 문맥, 임베딩 기반, 생성형, 또는 LLM 프롬프트.
4. NIL 전략. 최고 점수에 임계값 적용, 분류기, 또는 명시적 NIL 후보.
5. 평가. 홀드아웃 셋에서 mention recall @ 30, top-1 정확도, NIL 탐지 F1.

mention-recall 베이스라인 없는 EL 파이프라인은 거부합니다(후보 생성이 올바른 개체를 찾아냈는지 모르면 개체 판별기를 평가할 수 없습니다). 유효한 KB id로 출력을 제약하지 않는 LLM 프롬프트 방식 EL 파이프라인은 거부합니다. 도메인 파인튜닝 없이 인기 편향이 소수 개체(예: 이름 충돌)에 영향을 주는 시스템은 경고를 표시합니다.
```

## 연습 문제

1. **쉬움.** 모호한 멘션 10개(Paris, Jordan, Apple)에 `code/main.py`의 사전 확률+문맥 개체 판별기를 구현해 보세요. 올바른 개체를 직접 레이블링하고 정확도를 측정하세요.
2. **보통.** 모호한 멘션 50개를 문장 트랜스포머로 인코딩하세요. 각 후보의 설명도 임베딩하세요. 임베딩 기반 개체 판별과 자카드 문맥 중첩을 비교하세요.
3. **어려움.** 1천 개 개체짜리 도메인 KB를 만들어 보세요(예: 회사 직원 + 제품). NER + EL을 엔드투엔드로 구현하고, 홀드아웃 문장 100개에서 정밀도와 재현율을 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| 개체 연결(EL) | Wikipedia에 연결 | 멘션을 유일한 KB 항목에 매핑. |
| 후보 생성 | 누구일 수 있지? | 멘션에 대해 가능성 있는 KB 항목 후보 목록을 반환. |
| 개체 판별 | 올바른 것 고르기 | 문맥으로 후보에 점수를 매기고 승자를 고름. |
| 별칭 인덱스 | 조회 테이블 | 표면형 → 후보 개체 매핑. |
| NIL | KB에 없음 | 어떤 KB 항목도 일치하지 않는다는 명시적 예측. |
| KB | 지식 베이스 | Wikidata, Wikipedia, DBpedia, 또는 여러분의 도메인 KB. |
| AIDA-CoNLL | 그 벤치마크 | 정답 개체 연결이 달린 Reuters 기사 1,393개. |

## 더 읽을거리

- [Milne, Witten (2008). Learning to Link with Wikipedia](https://www.cs.waikato.ac.nz/~ihw/papers/08-DM-IHW-LearningToLinkWithWikipedia.pdf) — 기초가 되는 사전 확률+문맥 접근법.
- [Wu et al. (2020). Zero-shot Entity Linking with Dense Entity Retrieval (BLINK)](https://arxiv.org/abs/1911.03814) — 임베딩 기반의 주력.
- [De Cao et al. (2021). Autoregressive Entity Retrieval (GENRE)](https://arxiv.org/abs/2010.00904) — 제약 디코딩을 쓰는 생성형 EL.
- [Hoffart et al. (2011). Robust Disambiguation of Named Entities in Text (AIDA)](https://www.aclweb.org/anthology/D11-1072.pdf) — 벤치마크 논문.
- [REL: An Entity Linker Standing on the Shoulders of Giants (2020)](https://arxiv.org/abs/2006.01969) — 오픈소스 프로덕션 스택.
