> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 품사 태깅과 구문 분석 (POS Tagging and Syntactic Parsing)

> 문법이 한동안 유행 뒤전이었던 적이 있습니다. 그러다 모든 LLM 파이프라인이 구조화 추출 검증을 필요로 하면서 다시 돌아왔죠.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 01(텍스트 처리), 페이즈 2 · 14(나이브 베이즈)
**소요 시간:** 약 45분

## 해결할 문제

레슨 01에서 표제어 추출(lemmatization)에는 품사 태그가 필요하다고 약속했습니다. `running`이 동사라는 것을 모르면 표제어 추출기는 이를 `run`으로 줄일 수 없습니다. `better`가 형용사라는 것을 모르면 `good`으로 줄일 수 없죠.

그 약속은 한 하위 분야 전체를 숨기고 있었습니다. 품사 태깅(part-of-speech tagging)은 토큰에 문법 범주를 붙입니다. 구문 분석(syntactic parsing)은 문장의 나무 구조를 복원합니다. 어떤 단어가 무엇을 수식하는지, 어떤 동사가 어떤 논항을 거느리는지요. 고전 NLP는 이 둘을 다듬는 데 20년을 썼습니다. 그러다 딥러닝이 이 둘을 사전학습 트랜스포머 위의 토큰 분류 과제로 압축해 버렸고, 연구 커뮤니티는 다음 주제로 넘어갔습니다.

하지만 응용 커뮤니티는 아닙니다. 모든 구조화 추출 파이프라인은 아직도 후드 아래에서 품사 태그와 의존 구문 트리를 씁니다. LLM이 생성한 JSON은 문법 제약 조건으로 검증됩니다. 질의응답 시스템은 의존 구문 분석으로 쿼리를 분해합니다. 기계 번역 품질 평가기는 구문 트리의 정렬을 확인합니다.

알아 둘 가치가 있습니다. 이 레슨은 태그 집합들과 베이스라인들, 그리고 "여기서부터는 직접 구현하지 말고 spaCy를 부른다"는 경계선을 소개합니다.

## 핵심 개념

**품사 태깅**은 각 토큰에 문법 범주를 붙입니다. 영어의 기본 태그 집합은 **Penn Treebank(PTB)**입니다. 36개 태그로, 가벼운 독자 눈에는 유난스러워 보이는 구분까지 있습니다. `NN` 단수 명사, `NNS` 복수 명사, `NNP` 단수 고유명사, `VBD` 과거 동사, `VBZ` 3인칭 단수 현재 동사 등입니다. **Universal Dependencies(UD)** 태그 집합은 더 거칠고(17개 태그) 언어 중립적이라 교차 언어 작업의 기본이 됐습니다.

```
The/DET cats/NOUN were/AUX running/VERB at/ADP 3pm/NOUN ./PUNCT
```

**구문 분석**은 나무를 만들어 냅니다. 크게 두 가지 스타일이 있습니다.

- **구성소 분석(constituency parsing).** 명사구, 동사구, 전치사구가 서로 안에 중첩됩니다. 출력은 단어를 잎으로 두고 비종단 범주(NP, VP, PP)로 이뤄진 나무입니다.
- **의존 분석(dependency parsing).** 각 단어는 자신이 의존하는 머리 단어(head)를 하나씩 가지며, 문법 관계 레이블이 붙습니다. 출력의 모든 간선이 (머리, 의존소, 관계) 삼중항인 나무입니다.

의존 분석이 2010년대에 이긴 이유는 언어, 특히 어순이 자유로운 언어들에 걸쳐 깔끔하게 일반화되기 때문입니다.

```
running is ROOT
cats is nsubj of running
were is aux of running
at is prep of running
3pm is pobj of at
```

```figure
pos-tagger
```

```figure
dependency-arcs
```

## 만들어 보기

### 단계 1: 최빈 태그 베이스라인

돌아가는 품사 태거 중 가장 단순한 것입니다. 각 단어에 대해 학습 데이터에서 가장 자주 붙었던 태그를 예측합니다.

```python
from collections import Counter, defaultdict


def train_mft(train_examples):
    word_tag_counts = defaultdict(Counter)
    all_tags = Counter()
    for tokens, tags in train_examples:
        for token, tag in zip(tokens, tags):
            word_tag_counts[token.lower()][tag] += 1
            all_tags[tag] += 1
    word_best = {w: c.most_common(1)[0][0] for w, c in word_tag_counts.items()}
    default_tag = all_tags.most_common(1)[0][0]
    return word_best, default_tag


def predict_mft(tokens, word_best, default_tag):
    return [word_best.get(t.lower(), default_tag) for t in tokens]
```

Brown 코퍼스에서 이 베이스라인은 정확도 약 85%를 냅니다. 좋지는 않지만, 진지한 모델이라면 떨어져서는 안 될 바닥선입니다.

### 단계 2: 바이그램 HMM 태거

시퀀스의 결합 확률을 모델링합니다.

```
P(tags, words) = prod P(tag_i | tag_{i-1}) * P(word_i | tag_i)
```

테이블 두 개가 필요합니다. 전이 확률(이전 태그가 주어졌을 때의 태그)과 방출 확률(태그가 주어졌을 때의 단어)입니다. 둘 다 카운트에 라플라스 스무딩을 얹어 추정합니다. 복호화는 비터비(Viterbi) 알고리즘(태그 격자 위의 동적 계획법)으로 합니다.

```python
import math


def train_hmm(train_examples, alpha=0.01):
    transitions = defaultdict(Counter)
    emissions = defaultdict(Counter)
    tags = set()
    vocab = set()

    for tokens, ts in train_examples:
        prev = "<BOS>"
        for token, tag in zip(tokens, ts):
            transitions[prev][tag] += 1
            emissions[tag][token.lower()] += 1
            tags.add(tag)
            vocab.add(token.lower())
            prev = tag
        transitions[prev]["<EOS>"] += 1

    return transitions, emissions, tags, vocab


def log_prob(table, given, key, smooth_denom, alpha):
    return math.log((table[given].get(key, 0) + alpha) / smooth_denom)


def viterbi(tokens, transitions, emissions, tags, vocab, alpha=0.01):
    tags_list = list(tags)
    n = len(tokens)
    V = [[0.0] * len(tags_list) for _ in range(n)]
    back = [[0] * len(tags_list) for _ in range(n)]

    for j, tag in enumerate(tags_list):
        em_denom = sum(emissions[tag].values()) + alpha * (len(vocab) + 1)
        tr_denom = sum(transitions["<BOS>"].values()) + alpha * (len(tags_list) + 1)
        tr = log_prob(transitions, "<BOS>", tag, tr_denom, alpha)
        em = log_prob(emissions, tag, tokens[0].lower(), em_denom, alpha)
        V[0][j] = tr + em
        back[0][j] = 0

    for i in range(1, n):
        for j, tag in enumerate(tags_list):
            em_denom = sum(emissions[tag].values()) + alpha * (len(vocab) + 1)
            em = log_prob(emissions, tag, tokens[i].lower(), em_denom, alpha)
            best_prev = 0
            best_score = -1e30
            for k, prev_tag in enumerate(tags_list):
                tr_denom = sum(transitions[prev_tag].values()) + alpha * (len(tags_list) + 1)
                tr = log_prob(transitions, prev_tag, tag, tr_denom, alpha)
                score = V[i - 1][k] + tr + em
                if score > best_score:
                    best_score = score
                    best_prev = k
            V[i][j] = best_score
            back[i][j] = best_prev

    last_best = max(range(len(tags_list)), key=lambda j: V[n - 1][j])
    path = [last_best]
    for i in range(n - 1, 0, -1):
        path.append(back[i][path[-1]])
    return [tags_list[j] for j in reversed(path)]
```

Brown 코퍼스에서 바이그램 HMM은 정확도 약 93%를 냅니다. 85%에서 93%로의 점프는 대부분 전이 확률 덕분입니다. 모델이 `DET NOUN`은 흔하고 `NOUN DET`는 드물다는 것을 배우는 거죠.

### 단계 3: 현대 태거가 왜 이걸 이기는가

전이 확률 + 방출 확률은 지역적(local)입니다. "I bought a saw"에서 `saw`는 명사이고 "I saw the movie"에서는 동사라는 사실을 잡아 내지 못합니다. 임의의 특성(접미사, 단어 모양, 앞뒤 단어, 단어 자체)을 쓰는 CRF는 약 97%에 도달합니다. BiLSTM-CRF나 트랜스포머는 98% 이상입니다.

이 과제의 천장은 어노테이터(주석 담당자) 간 불일치가 정합니다. Penn Treebank에서 사람 어노테이터의 일치율은 약 97%입니다. 98%를 넘는 모델은 아마 테스트 세트에 과적합하고 있는 것입니다.

### 단계 4: 의존 분석 개요

의존 분석기를 처음부터 통째로 구현하는 것은 범위를 넘습니다. 정석적인 교과서 다루기는 Jurafsky와 Martin에 있습니다. 알아 둘 고전 계열 둘은 이렇습니다.

- **전이 기반(transition-based)** 파서(arc-eager, arc-standard)는 시프트-리듀스 파서처럼 동작합니다. 토큰을 읽어 스택에 쌓고, 간선(arc)을 만드는 리듀스 액션을 적용하죠. 탐욕적 복호화는 빠릅니다. 고전 구현은 MaltParser입니다. 현대의 신경망 버전은 Chen과 Manning의 전이 기반 파서입니다.
- **그래프 기반(graph-based)** 파서(Eisner 알고리즘, Dozat-Manning biaffine)는 가능한 모든 머리-의존소 간선에 점수를 매기고 최대 신장 트리를 고릅니다. 느리지만 더 정확합니다.

대부분의 응용 작업에서는 spaCy를 부르세요.

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("The cats were running at 3pm.")
for token in doc:
    print(f"{token.text:10s} tag={token.tag_:5s} pos={token.pos_:6s} dep={token.dep_:10s} head={token.head.text}")
```

```
The        tag=DT    pos=DET    dep=det        head=cats
cats       tag=NNS   pos=NOUN   dep=nsubj      head=running
were       tag=VBD   pos=AUX    dep=aux        head=running
running    tag=VBG   pos=VERB   dep=ROOT       head=running
at         tag=IN    pos=ADP    dep=prep       head=running
3pm        tag=NN    pos=NOUN   dep=pobj       head=at
.          tag=.     pos=PUNCT  dep=punct      head=running
```

`dep` 열을 아래에서 위로 읽으면 문장의 문법 구조가 그대로 드러납니다.

## 활용하기

모든 프로덕션 NLP 라이브러리는 표준 파이프라인의 일부로 품사 태거와 의존 파서를 싣고 나옵니다.

- **spaCy** (`en_core_web_sm` / `md` / `lg` / `trf`). 빠르고 정확하며 토큰화 + NER + 표제어 추출과 통합돼 있습니다. `token.tag_`(Penn), `token.pos_`(UD), `token.dep_`(의존 관계).
- **Stanford NLP (stanza)**. CoreNLP의 스탠퍼드 후속작. 60개 이상 언어에서 최고 수준.
- **trankit**. 트랜스포머 기반, UD 정확도가 좋습니다.
- **NLTK**. `pos_tag`. 쓸 만하고, 느리고, 오래됐습니다. 가르치기엔 충분합니다.

### 2026년에도 여전히 중요한 곳

- **표제어 추출.** 레슨 01이 올바른 표제어 추출을 위해 품사를 필요로 합니다. 언제나요.
- **LLM 출력의 구조화 추출.** 생성된 문장이 문법 제약 조건(예: 주어-동사 수 일치, 필수 수식어)을 지키는지 검증합니다.
- **측면별 감성 분석.** 의존 구문 분석이 어떤 형용사가 어떤 명사를 수식하는지 알려 줍니다.
- **쿼리 이해.** "movies directed by Wes Anderson starring Bill Murray"는 구문 분석을 통해 구조화된 제약 조건들로 분해됩니다.
- **교차 언어 전이.** UD 태그와 의존 관계는 언어 중립적이라, 새로운 언어를 제로샷으로 구조화 분석할 수 있게 해 줍니다.
- **저연산 파이프라인.** 트랜스포머를 실을 수 없다면, 품사 태그 + 의존 구문 분석 + 개체명 사전으로도 의외로 멀리 갑니다.

## 출시하기

`outputs/skill-grammar-pipeline.md`로 저장하세요:

```markdown
---
name: grammar-pipeline
description: 다운스트림 NLP 과제를 위한 고전 품사 + 의존 분석 파이프라인을 설계합니다.
version: 1.0.0
phase: 5
lesson: 07
tags: [nlp, pos, parsing]
---

다운스트림 과제(정보 추출, 재작성 검증, 쿼리 분해, 표제어 추출)가 주어지면 다음을 출력합니다:

1. 사용할 태그 집합. 영어 전용 레거시 파이프라인에는 Penn Treebank, 다국어나 교차 언어에는 Universal Dependencies.
2. 라이브러리. 대부분의 프로덕션(운영 환경)에는 spaCy, 학술급 다국어에는 stanza, 최고 UD 정확도에는 trankit. 구체적인 모델 ID를 밝힙니다.
3. 통합 패턴. 라이브러리를 호출하고 필요한 속성(`.pos_`, `.dep_`, `.head`)을 소비하는 3~5줄을 보여 줍니다.
4. 테스트할 실패 모드. 명사-동사 중의성(`saw`, `book`, `can`)과 전치사구 부착 중의성이 고전적인 함정입니다. 출력 20개를 표본으로 뽑아 직접 눈으로 확인합니다.

자체 파서를 만들라는 추천은 거부합니다. 파서를 처음부터 만드는 일은 연구 프로젝트지 응용 과제가 아닙니다. 대소문자 변형을 처리하지 않고 품사 태그를 소비하는 파이프라인은 취약하다고 표시합니다.
```

## 연습 문제

1. **(쉬움)** 작은 태그 달린 코퍼스(예: NLTK의 Brown 부분집합)로 최빈 태그 베이스라인을 돌려, 홀드아웃 문장에서 정확도를 측정하세요. 약 85%라는 결과를 확인합니다.
2. **(보통)** 위의 바이그램 HMM을 학습시키고 태그별 정밀도/재현율을 보고하세요. HMM이 가장 많이 헷갈리는 태그는 무엇인가요?
3. **(어려움)** spaCy의 의존 구문 분석으로 1000문장 표본에서 주어-동사-목적어 삼중항을 추출하세요. 수작업으로 레이블한 50개 삼중항으로 평가합니다. 추출이 실패하는 지점을 문서화하세요(보통 수동태, 병렬 구조, 생략된 주어입니다).

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 품사 태그 | 단어의 유형 | 문법 범주. PTB는 36개, UD는 17개. |
| Penn Treebank | 표준 태그 집합 | 영어 전용. 세밀한 동사 시제와 명사 수 구분. |
| Universal Dependencies | 다국어 태그 집합 | PTB보다 거칠고 언어 중립적. 교차 언어 작업의 기본. |
| 의존 구문 분석 | 문장 나무 | 각 단어는 머리를 하나씩 가지고, 각 간선에는 문법 관계가 붙음. |
| 비터비(Viterbi) | 동적 계획법 | 방출 확률과 전이 확률이 주어졌을 때 가장 확률 높은 태그 시퀀스를 찾음. |

## 더 읽을거리

- [Jurafsky and Martin — Speech and Language Processing, 8장과 18장](https://web.stanford.edu/~jurafsky/slp3/) — 품사와 구문 분석의 정석적인 교과서 다루기.
- [Universal Dependencies 프로젝트](https://universaldependencies.org/) — 모든 다국어 파서가 쓰는 교차 언어 태그 집합과 트리뱅크 모음.
- [spaCy 언어 분석 기능 가이드](https://spacy.io/usage/linguistic-features) — `Token`이 노출하는 모든 속성의 실전 레퍼런스.
- [Chen and Manning (2014). A Fast and Accurate Dependency Parser using Neural Networks](https://nlp.stanford.edu/pubs/emnlp2014-depparser.pdf) — 신경망 파서를 주류로 끌어올린 논문.
