# 관계 추출과 지식 그래프 구축 (Relation Extraction & Knowledge Graph Construction)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> NER이 개체를 찾았습니다. 개체 연결이 개체를 고정시켰습니다. 관계 추출은 개체 사이의 간선을 찾습니다. 지식 그래프는 노드와 간선, 그리고 그 출처(provenance)의 총합입니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 06(NER), 페이즈 5 · 25(개체 연결)
**소요 시간:** 약 60분

## 문제 상황

분석가가 "Tim Cook은 2011년에 Apple의 CEO가 되었다"라는 문장을 읽습니다. 네 개의 사실:

- `(Tim Cook, role, CEO)`
- `(Tim Cook, employer, Apple)`
- `(Tim Cook, start_date, 2011)`
- `(Apple, type, Organization)`

관계 추출(RE)은 자유 텍스트를 구조화된 트리플 `(subject, relation, object)`로 바꿉니다. 코퍼스 전체에 걸쳐 모으면 지식 그래프가 됩니다. 모아서 질의하면 RAG, 분석, 컴플라이언스 감사를 위한 추론 기반이 됩니다.

2026년의 문제: LLM은 매우 열정적으로 관계를 추출합니다. 너무 열정적입니다. 원본 텍스트가 뒷받침하지 않는 트리플을 환각으로 만들어 냅니다. 출처 추적(provenance)이 없으면 진짜 트리플과 그럴듯한 허구를 구분할 수 없습니다. 2026년의 해답은 AEVS 스타일의 앵커-검증(anchor-and-verify) 파이프라인입니다.

## 개념

![텍스트 → 트리플 → 지식 그래프](../assets/relation-extraction.svg)

**트리플 형태.** `(subject_entity, relation_type, object_entity)`. 관계는 닫힌 온톨로지(Wikidata 속성, FIBO, UMLS)에서 오거나, 열린 집합(OpenIE 스타일, 뭐든 허용)에서 옵니다.

**세 가지 추출 접근법.**

1. **규칙 / 패턴 기반.** Hearst 패턴: "X such as Y" → `(Y, isA, X)`. 여기에 수작업 정규식을 더합니다. 깨지기 쉽지만, 정확하고, 설명 가능합니다.
2. **지도 학습 분류기.** 문장 안의 두 개체 멘션이 주어지면 고정된 집합에서 관계를 예측합니다. TACRED, ACE, KBP로 학습합니다. 2015–2022년의 표준.
3. **생성형 LLM.** 모델에 트리플을 내놓으라고 프롬프트합니다. 별도 준비 없이 바로 동작합니다. 출처 추적이 없으면 그럴듯해 보이는 쓰레기를 환각으로 만들어 냅니다.

**AEVS(Anchor-Extraction-Verification-Supplement, 2026).** 현재의 환각 완화 프레임워크:

- **앵커(Anchor).** 모든 개체 span과 관계 구절 span을 정확한 위치와 함께 식별합니다.
- **추출(Extract).** 앵커 span에 연결된 트리플을 생성합니다.
- **검증(Verify).** 각 트리플 요소를 원본 텍스트와 대조합니다; 뒷받침되지 않는 것은 거부합니다.
- **보충(Supplement).** 커버리지 패스로 앵커된 span이 하나도 빠지지 않았는지 확인합니다.

환각이 급격히 줄어듭니다. 연산 비용은 더 들지만 감사 가능합니다.

**열림 vs 닫힘 트레이드오프.**

- **닫힌 온톨로지.** 고정된 속성 목록(예: Wikidata의 11,000개 이상 속성). 예측 가능하고, 질의하기 좋고, 새로 만들기는 어렵습니다.
- **오픈 IE.** 어떤 동사구든 관계가 됩니다. 재현율은 높지만 정밀도는 낮습니다. 질의하기 지저분합니다.

프로덕션 KG는 보통 섞어 씁니다: 발견용으로 오픈 IE를 쓰고, 메인 그래프에 병합하기 전에 관계를 닫힌 온톨로지로 정규화합니다.

```figure
relation-triples
```

## 직접 만들기

### 단계 1: 패턴 기반 추출

```python
PATTERNS = [
    (r"(?P<s>[A-Z]\w+) (?:is|was) (?:a|an|the) (?P<o>[A-Z]?\w+)", "isA"),
    (r"(?P<s>[A-Z]\w+) (?:is|was) born in (?P<o>\w+)", "bornIn"),
    (r"(?P<s>[A-Z]\w+) works? (?:at|for) (?P<o>[A-Z]\w+)", "worksAt"),
    (r"(?P<s>[A-Z]\w+) founded (?P<o>[A-Z]\w+)", "founded"),
]
```

전체 장난감 추출기는 `code/main.py`에 있습니다. Hearst 패턴은 디버깅이 쉽기 때문에 여전히 도메인 특화 파이프라인에 실제로 쓰입니다.

### 단계 2: 지도 학습 관계 분류

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tok = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSequenceClassification.from_pretrained("Babelscape/rebel-large")

text = "Tim Cook was born in Alabama. He later became CEO of Apple."
encoded = tok(text, return_tensors="pt", truncation=True)
output = model.generate(**encoded, max_length=200)
triples = tok.batch_decode(output, skip_special_tokens=False)
```

REBEL은 seq2seq 관계 추출기입니다: 텍스트가 들어가면 트리플이 나오고, 이미 Wikidata 속성 id로 표기됩니다. 원거리 감독(distant-supervision) 데이터로 파인튜닝됐습니다. 표준 오픈 웨이트 베이스라인입니다.

### 단계 3: 앵커링이 있는 LLM 프롬프트 추출

```python
prompt = f"""Extract (subject, relation, object) triples from the text.
For each triple, include the exact character span in the source text.

Text: {text}

Output JSON:
[{{"subject": {{"text": "...", "span": [start, end]}},
   "relation": "...",
   "object": {{"text": "...", "span": [start, end]}}}}, ...]

Only include triples fully supported by the text. No inference beyond what is stated.
"""
```

반환된 모든 span을 원본과 대조해 검증하세요. `text[start:end] != triple_entity`인 것은 전부 거부합니다. AEVS의 "검증" 단계를 최소 형태로 구현한 것입니다.

### 단계 4: 닫힌 온톨로지로 정규화

```python
RELATION_MAP = {
    "is the CEO of": "P169",       # "chief executive officer"
    "was born in":   "P19",         # "place of birth"
    "founded":        "P112",       # "founded by" (주어/목적어 뒤집힘)
    "works at":       "P108",       # "employer"
}


def canonicalize(relation):
    rel_low = relation.lower().strip()
    if rel_low in RELATION_MAP:
        return RELATION_MAP[rel_low]
    return None   # 매핑되지 않은 오픈 관계는 버리거나 수동 검토로 보냄
```

정규화(canonicalization)는 엔지니어링 작업의 60~80%를 차지하곤 합니다. 일정에 반영하세요.

### 단계 5: 작은 그래프 만들고 질의하기

```python
triples = extract(text)
graph = {}
for s, r, o in triples:
    graph.setdefault(s, []).append((r, o))


def neighbors(node, relation=None):
    return [(r, o) for r, o in graph.get(node, []) if relation is None or r == relation]


print(neighbors("Tim Cook", relation="P108"))    # -> [(P108, Apple)]
```

이것이 모든 KG 위 RAG 시스템의 기본 단위입니다. RDF 트리플 스토어(Blazegraph, Virtuoso), 프로퍼티 그래프(Neo4j), 벡터 증강 그래프 스토어로 확장하세요.

## 흔한 실수

- **RE 전에 상호 참조 해소.** "He founded Apple" — RE는 "he"가 누구인지 알아야 합니다. coref를 먼저 돌리세요(레슨 24).
- **개체 정규화.** "Apple Inc"와 "Apple"은 같은 노드로 해석되어야 합니다. 개체 연결을 먼저 하세요(레슨 25).
- **환각 트리플.** LLM은 텍스트가 뒷받침하지 않는 트리플을 내놓습니다. span 검증을 강제하세요.
- **관계 정규화 드리프트.** 오픈 IE 관계는 일관성이 없습니다("was born in," "came from," "is a native of"). 정식 id로 묶지 않으면 그래프를 질의할 수 없습니다.
- **시간 오류.** "Tim Cook is CEO of Apple" — 지금은 참이지만 2005년에는 거짓입니다. 많은 관계는 시간 제한이 있습니다. 한정자(qualifier)를 사용하세요(Wikidata의 `P580` 시작 시각, `P582` 종료 시각).
- **도메인 불일치.** REBEL은 Wikipedia로 학습됐습니다. 법률, 의료, 과학 텍스트는 도메인 파인튜닝된 RE 모델이 필요한 경우가 많습니다.

## 활용하기

2026년의 표준 스택:

| 상황 | 선택지 |
|-----------|------|
| 빠른 프로덕션, 범용 도메인 | REBEL 또는 LlamaPred + Wikidata 정규화 |
| 도메인 특화(바이오메디컬, 법률) | SciREX 스타일 도메인 파인튜닝 + 커스텀 온톨로지 |
| LLM 프롬프트, 감사 가능한 출력 | AEVS 파이프라인: 앵커 → 추출 → 검증 → 보충 |
| 대용량 뉴스 IE | 패턴 기반 + 지도 학습 하이브리드 |
| KG를 처음부터 구축 | 오픈 IE + 수동 정규화 패스 |
| 시간 정보가 있는 KG | 한정자(시작/종료 시각, 특정 시점)를 붙여 추출 |

통합 패턴: NER → coref → 개체 연결 → 관계 추출 → 온톨로지 매핑 → 그래프 적재. 모든 단계가 잠재적인 품질 게이트입니다.

## 출시하기

`outputs/skill-re-designer.md`로 저장하세요:

```markdown
---
name: re-designer
description: Design a relation extraction pipeline with provenance and canonicalization.
version: 1.0.0
phase: 5
lesson: 26
tags: [nlp, relation-extraction, knowledge-graph]
---

코퍼스(도메인, 언어, 처리량)와 하위 용도(KG-RAG, 분석, 컴플라이언스)가 주어지면 다음을 출력합니다:

1. 추출기. 패턴 기반 / 지도 학습 / LLM / AEVS 하이브리드. 정밀도 대 재현율 목표에 근거를 둡니다.
2. 온톨로지. 닫힌 속성 목록(Wikidata / 도메인) 또는 정규화 단계를 거치는 오픈 IE.
3. 출처 추적(provenance). 모든 트리플에 원본 문자 범위(char-span) + 문서 id를 첨부. 감사(audit)를 위해 타협 불가.
4. 병합 전략. 정규 개체 id + 관계 id + 시간 한정자(qualifier); 중복 제거 정책.
5. 평가. 수작업 레이블 트리플 200개에서 정밀도 / 재현율 + LLM 추출 샘플의 환각 비율.

span 검증(원본 출처) 없는 LLM 기반 RE 파이프라인은 거부합니다. 정규화 없이 오픈 IE 결과가 프로덕션(운영 환경) 그래프로 흘러 들어가는 것은 거부합니다. 시간 한정 관계(고용주, 배우자, 직위)에 시간 한정자가 없는 파이프라인은 경고를 표시합니다.
```

## 연습 문제

1. **쉬움.** 뉴스 기사 문장 5개에 `code/main.py`의 패턴 추출기를 실행해 보세요. 정밀도를 직접 확인하세요.
2. **보통.** 같은 문장에 REBEL(또는 작은 LLM)을 적용해 보세요. 트리플을 비교하세요. 어느 추출기의 정밀도가 더 높나요? 재현율은?
3. **어려움.** AEVS 파이프라인을 만들어 보세요: LLM으로 추출하고 span을 원본과 대조해 검증합니다. Wikipedia 스타일 문장 50개에서 검증 단계 전후의 환각 비율을 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| 트리플(Triple) | 주어-관계-목적어 | KG의 원자 단위인 `(s, r, o)` 튜플. |
| 오픈 IE | 뭐든 추출 | 개방형 어휘의 관계 구절; 재현율 높고 정밀도 낮음. |
| 닫힌 온톨로지 | 고정된 스키마 | 유한한 관계 유형 집합(Wikidata, UMLS, FIBO). |
| 정규화(Canonicalization) | 전부 표준형으로 | 표면 이름/관계를 정식 id로 매핑. |
| AEVS | 근거 있는 추출 | Anchor-Extraction-Verification-Supplement 파이프라인(2026). |
| 출처 추적(Provenance) | 원본 연결 | 모든 트리플이 자기 원본의 문서 id + 문자 범위를 가짐. |
| 원거리 감독 | 값싼 레이블 | 기존 KG와 텍스트를 정렬해 학습 데이터를 만드는 기법. |

## 더 읽을거리

- [Mintz et al. (2009). Distant supervision for relation extraction without labeled data](https://www.aclweb.org/anthology/P09-1113.pdf) — 원거리 감독 원 논문.
- [Huguet Cabot, Navigli (2021). REBEL: Relation Extraction By End-to-end Language generation](https://aclanthology.org/2021.findings-emnlp.204.pdf) — seq2seq RE 주력 모델.
- [Wadden et al. (2019). Entity, Relation, and Event Extraction with Contextualized Span Representations (DyGIE++)](https://arxiv.org/abs/1909.03546) — 통합 IE.
- [AEVS — Anchor-Extraction-Verification-Supplement framework](https://www.mdpi.com/2073-431X/15/3/178) — 2026년 환각 완화 설계.
- [Wikidata SPARQL 튜토리얼](https://www.wikidata.org/wiki/Wikidata:SPARQL_tutorial) — 정식 그래프 질의.
