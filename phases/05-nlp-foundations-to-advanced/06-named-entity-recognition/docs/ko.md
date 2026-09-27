> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 개체명 인식 (Named Entity Recognition)

> 이름을 뽑아 내는 일입니다. 애매한 경계, 중첩된 개체, 도메인 전문 용어를 만나기 전까지는 쉬워 보이죠.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 02(BoW + TF-IDF), 페이즈 5 · 03(단어 임베딩)
**소요 시간:** 약 75분

## 해결할 문제

"Apple sued Google over its iPhone search deal in the US." 여기엔 개체가 다섯 개 있습니다. Apple(ORG), Google(ORG), iPhone(PRODUCT), search deal(어쩌면), US(GPE). 좋은 NER 시스템은 이 전부를 올바른 타입과 함께 뽑아 냅니다. 나쁜 시스템은 iPhone을 놓치고, 회사 Apple을 과일 Apple과 헷갈리고, "US"를 PERSON이라고 붙입니다.

NER은 모든 구조화 추출 파이프라인 밑에서 일하는 말일꾼입니다. 이력서 파싱, 컴플라이언스 로그 검사, 의료 기록 익명화, 검색 쿼리 이해, 챗봇 응답의 근거 찾기(grounding), 법률 계약서 추출까지. 눈에는 잘 보이지 않지만 언제나 의존하고 있는 것입니다.

이 레슨은 고전적인 길(규칙 기반, HMM, CRF)을 따라 현대적인 길(BiLSTM-CRF, 그다음 트랜스포머)까지 걸어 갑니다. 각 단계는 바로 앞 단계의 특정 한계를 해결합니다. 이 패턴 자체가 이 레슨의 핵심입니다.

## 핵심 개념

**BIO 태깅**(또는 BILOU)은 개체 추출을 시퀀스 레이블링 문제로 바꿔 줍니다. 토큰마다 `B-TYPE`(개체의 시작), `I-TYPE`(개체 내부), `O`(개체 밖) 레이블을 붙입니다.

```
Apple    B-ORG
sued     O
Google   B-ORG
over     O
its      O
iPhone   B-PRODUCT
search   O
deal     O
in       O
the      O
US       B-GPE
.        O
```

여러 토큰으로 이뤄진 개체는 이어집니다. `New B-GPE`, `York I-GPE`, `City I-GPE`. BIO를 이해하는 모델은 임의의 범위(span)를 추출할 수 있습니다.

아키텍처의 발전 과정은 이렇습니다.

- **규칙 기반.** 정규식 + 개체명 사전(gazetteer) 조회. 알려진 개체에는 정밀도가 높지만, 새로운 개체에는 커버리지가 0입니다.
- **HMM.** 은닉 마르코프 모델(Hidden Markov Model). 태그가 주어졌을 때 토큰이 나올 방출 확률(emission probability)과 태그에서 태그로 넘어가는 전이 확률을 씁니다. 비터비(Viterbi) 디코딩으로 복호화하고, 레이블된 데이터로 학습합니다.
- **CRF.** 조건부 확률장(Conditional Random Field). HMM 같지만 판별(discriminative) 모델이라 임의의 특성(단어 모양, 대소문자, 이웃 단어)을 자유롭게 섞을 수 있습니다. 2026년에도 저자원 환경 배포에서는 여전히 고전 프로덕션의 말일꾼입니다.
- **BiLSTM-CRF.** 손으로 만든 특성 대신 신경망 특성을 씁니다. LSTM이 문장을 양방향으로 읽고, 그 위의 CRF 레이어가 일관된 태그 시퀀스를 강제합니다.
- **트랜스포머 기반.** 토큰 분류 헤드를 붙여 BERT를 파인튜닝합니다. 정확도 최고, 연산량 최대.

```figure
ner-bio-tagging
```

## 만들어 보기

### 단계 1: BIO 태깅 도우미 함수

```python
def spans_to_bio(tokens, spans):
    labels = ["O"] * len(tokens)
    for start, end, label in spans:
        labels[start] = f"B-{label}"
        for i in range(start + 1, end):
            labels[i] = f"I-{label}"
    return labels


def bio_to_spans(tokens, labels):
    spans = []
    current = None
    for i, label in enumerate(labels):
        if label.startswith("B-"):
            if current:
                spans.append(current)
            current = (i, i + 1, label[2:])
        elif label.startswith("I-") and current and current[2] == label[2:]:
            current = (current[0], i + 1, current[2])
        else:
            if current:
                spans.append(current)
                current = None
    if current:
        spans.append(current)
    return spans
```

```python
>>> tokens = ["Apple", "sued", "Google", "over", "iPhone", "sales", "."]
>>> labels = ["B-ORG", "O", "B-ORG", "O", "B-PRODUCT", "O", "O"]
>>> bio_to_spans(tokens, labels)
[(0, 1, 'ORG'), (2, 3, 'ORG'), (4, 5, 'PRODUCT')]
```

### 단계 2: 손으로 만든 특성

고전적인(비신경망) NER에서는 특성 설계가 승부처입니다. 쓸모 있는 특성들은 이렇습니다.

```python
def token_features(token, prev_token, next_token):
    return {
        "lower": token.lower(),
        "is_upper": token.isupper(),
        "is_title": token.istitle(),
        "has_digit": any(c.isdigit() for c in token),
        "suffix_3": token[-3:].lower(),
        "shape": word_shape(token),
        "prev_lower": prev_token.lower() if prev_token else "<BOS>",
        "next_lower": next_token.lower() if next_token else "<EOS>",
    }


def word_shape(word):
    out = []
    for c in word:
        if c.isupper():
            out.append("X")
        elif c.islower():
            out.append("x")
        elif c.isdigit():
            out.append("d")
        else:
            out.append(c)
    return "".join(out)
```

`word_shape("iPhone")`은 `xXxxxx`를 돌려주고, `word_shape("USA-2024")`는 `XXX-dddd`를 돌려줍니다. 대소문자 패턴은 고유명사를 가려내는 강력한 신호입니다.

### 단계 3: 규칙 기반 + 사전 조회 베이스라인

```python
ORG_GAZETTEER = {"Apple", "Google", "Microsoft", "OpenAI", "Meta", "Amazon", "Netflix"}
GPE_GAZETTEER = {"US", "USA", "UK", "India", "Germany", "France"}
PRODUCT_GAZETTEER = {"iPhone", "Android", "Windows", "ChatGPT", "Claude"}


def rule_based_ner(tokens):
    labels = []
    for token in tokens:
        if token in ORG_GAZETTEER:
            labels.append("B-ORG")
        elif token in GPE_GAZETTEER:
            labels.append("B-GPE")
        elif token in PRODUCT_GAZETTEER:
            labels.append("B-PRODUCT")
        else:
            labels.append("O")
    return labels
```

실제 프로덕션 개체명 사전은 Wikipedia와 DBpedia에서 긁어 모은 수백만 개 항목을 담습니다. 커버리지는 좋습니다. 하지만 중의성 해소(`Apple`이 회사인지 과일인지)는 끔찍합니다. 통계 모델이 이겨 버린 이유가 바로 이것입니다.

### 단계 4: CRF 단계(개략 구현)

확률론 기초 없이 CRF 전체를 50줄로 짜면 깨달음보다 혼란만 남습니다. 대신 `sklearn-crfsuite`를 쓰세요.

```python
import sklearn_crfsuite

def to_features(tokens):
    out = []
    for i, tok in enumerate(tokens):
        prev = tokens[i - 1] if i > 0 else ""
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        out.append({
            "word.lower()": tok.lower(),
            "word.isupper()": tok.isupper(),
            "word.istitle()": tok.istitle(),
            "word.isdigit()": tok.isdigit(),
            "word.suffix3": tok[-3:].lower(),
            "word.shape": word_shape(tok),
            "prev.word.lower()": prev.lower(),
            "next.word.lower()": nxt.lower(),
            "BOS": i == 0,
            "EOS": i == len(tokens) - 1,
        })
    return out


crf = sklearn_crfsuite.CRF(algorithm="lbfgs", c1=0.1, c2=0.1, max_iterations=100, all_possible_transitions=True)
X_train = [to_features(s) for s in sentences_tokenized]
crf.fit(X_train, bio_labels_train)
```

`c1`과 `c2`는 각각 L1, L2 정규화입니다. `all_possible_transitions=True`는 모델이 "불법적인 시퀀스(예: `O` 뒤의 `I-ORG`)는 일어나기 어렵다"는 것을 학습하게 해 줍니다. 여러분이 제약 조건을 직접 쓰지 않고도 CRF가 BIO 일관성을 강제하는 방식입니다.

### 단계 5: BiLSTM-CRF가 더하는 것

특성이 학습되는 것으로 바뀝니다. 입력은 토큰 임베딩(GloVe나 fastText)입니다. LSTM이 문장을 왼쪽에서 오른쪽으로, 그리고 오른쪽에서 왼쪽으로 읽습니다. 이어 붙인 은닉 상태가 CRF 출력 레이어를 통과합니다. 태그 시퀀스 일관성은 여전히 CRF가 강제하고, LSTM이 손으로 만든 특성을 학습된 특성으로 대체합니다.

```python
import torch
import torch.nn as nn


class BiLSTM_CRF_Head(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, n_labels):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, bidirectional=True, batch_first=True)
        self.fc = nn.Linear(hidden_dim * 2, n_labels)

    def forward(self, token_ids):
        e = self.embed(token_ids)
        h, _ = self.lstm(e)
        emissions = self.fc(h)
        return emissions
```

CRF 레이어는 `torchcrf.CRF`(pip install pytorch-crf)를 쓰세요. 손으로 만든 특성을 쓴 CRF에 비해 얻는 이득은 측정 가능하지만, 레이블된 문장이 수만 개 있지 않은 한 기대만큼 크지는 않습니다.

## 활용하기

spaCy는 프로덕션급 NER을 기본 탑재하고 나옵니다.

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("Apple sued Google over its iPhone search deal in the US.")
for ent in doc.ents:
    print(f"{ent.text:20s} {ent.label_}")
```

```
Apple                ORG
Google               ORG
iPhone               ORG
US                   GPE
```

`iPhone`이 `PRODUCT`가 아니라 `ORG`로 레이블된 것을 보세요. spaCy의 소형 모델은 제품 개체 커버리지가 약합니다. 대형 모델(`en_core_web_lg`)은 더 잘하고, 트랜스포머 모델(`en_core_web_trf`)은 더더욱 잘합니다.

BERT 기반 NER에는 Hugging Face를 씁니다.

```python
from transformers import pipeline

ner = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
print(ner("Apple sued Google over its iPhone in the US."))
```

```
[{'entity_group': 'ORG', 'word': 'Apple', ...},
 {'entity_group': 'ORG', 'word': 'Google', ...},
 {'entity_group': 'MISC', 'word': 'iPhone', ...},
 {'entity_group': 'LOC', 'word': 'US', ...}]
```

`aggregation_strategy="simple"`은 붙어 있는 B-X, I-X 토큰들을 하나의 범위로 합쳐 줍니다. 이 옵션이 없으면 토큰 수준 레이블만 돌아오므로 직접 합쳐야 합니다.

### LLM 기반 NER(2026년의 선택지)

제로샷 및 퓨샷 LLM NER은 이제 많은 도메인에서 파인튜닝 모델에 필적하고, 레이블 데이터가 부족할 때는 압도적으로 낫습니다.

- **제로샷 프롬프팅.** LLM에게 개체 타입 목록과 예시 스키마를 주고 JSON 출력을 요구합니다. 바로 동작하며, 새로운 도메인에서 정확도는 보통 수준입니다.
- **ZeroTuneBio 스타일 프롬프팅.** 과제를 후보 추출 → 의미 설명 → 판단 → 재확인으로 쪼갭니다. 한 번에 끝내는 프롬프트가 아니라 여러 단계로 나눈 프롬프트가 생의학 NER에서 정확도를 크게 끌어올립니다. 같은 패턴이 법률, 금융, 과학 도메인에서도 통합니다.
- **RAG를 곁들인 동적 프롬프팅.** 추론을 호출할 때마다 작은 주석 달린 시드 집합에서 가장 비슷한 레이블 예시를 검색해 와, 퓨샷 프롬프트를 그 자리에서 조립합니다. 2026년 벤치마크 기준으로 이 방식은 정적 프롬프팅보다 GPT-4 생의학 NER F1을 11~12% 끌어올립니다.
- **개체 타입별 분해.** 긴 문서에서는 모든 개체 타입을 한 번에 뽑는 단일 호출이 길이가 늘어날수록 재현율이 떨어집니다. 개체 타입마다 추출 패스를 하나씩 돌리세요. 추론 비용은 높아지지만 정확도는 훨씬 올라갑니다. 임상 기록과 법률 계약서의 표준 패턴입니다.

2026년 현재 프로덕션 추천: 학습 데이터를 모으기 전에 LLM 제로샷 베이스라인부터 시작하세요. F1이 충분히 좋아서 파인튜닝이 한 번도 필요 없는 경우가 흔합니다.

### 고전 NER이 여전히 이기는 곳

LLM이 있어도 고전 NER이 이기는 경우는 다음과 같습니다.

- 지연 시간 예산이 50ms 미만일 때.
- 레이블 예시가 수천 개 있고 F1 98% 이상이 필요할 때.
- 도메인에 안정적인 온톨로지가 있어 사전학습된 CRF나 BiLSTM이 잘 전이될 때.
- 규제 요건 때문에 온프레미스의 비생성(non-generative) 모델이 필요할 때.

### 어디서 무너지나

- **도메인 시프트.** CoNLL로 학습한 NER은 법률 계약서에서 개체명 사전보다 못합니다. 여러분의 도메인으로 파인튜닝하세요.
- **중첩 개체.** "Bank of America Tower"는 동시에 ORG이면서 FACILITY입니다. 표준 BIO는 겹치는 범위를 표현하지 못합니다. 중첩 NER(멀티패스 또는 span 기반 모델)이 필요합니다.
- **긴 개체.** "United States Federal Deposit Insurance Corporation." 토큰 수준 모델은 이걸 가끔 쪼개 버립니다. `aggregation_strategy`를 쓰거나 후처리로 이어 주세요.
- **희귀 타입.** 의료 NER의 레이블은 DRUG_BRAND, ADVERSE_EVENT, DOSE 같은 것들입니다. 범용 모델은 도무히 감을 잡지 못합니다. 이 분야의 출발점은 Scispacy와 BioBERT입니다.

## 출시하기

`outputs/skill-ner-picker.md`로 저장하세요:

```markdown
---
name: ner-picker
description: 주어진 추출 과제에 맞는 NER 접근 방식을 고릅니다.
version: 1.0.0
phase: 5
lesson: 06
tags: [nlp, ner, extraction]
---

과제 설명(도메인, 레이블 집합, 언어, 지연 시간, 데이터 양)이 주어지면 다음을 출력합니다:

1. 접근 방식. 규칙 기반 + 개체명 사전, CRF, BiLSTM-CRF, 또는 트랜스포머 파인튜닝.
2. 시작 모델. 이름을 밝힙니다(spaCy 모델 ID, Hugging Face 체크포인트 ID, 또는 "custom, trained from scratch").
3. 레이블링 전략. BIO, BILOU, 또는 span 기반. 한 문장으로 근거를 댑니다.
4. 평가. `seqeval`을 씁니다. 항상 개체 수준(entity-level) F1을 보고합니다(토큰 수준이 아니라).

레이블 예시가 500개 미만인데 트랜스포머 파인튜닝을 추천하는 일은 거부합니다. 단, 사용자가 이미 사전학습된 도메인 모델을 갖고 있는 경우는 예외입니다. 중첩 개체가 있으면 span 기반 또는 멀티패스 모델이 필요하다고 표시합니다. 사용자가 "프로덕션 규모"를 언급하면서 레이블이 CoNLL-2003 그대로라면 개체명 사전 감사(audit)를 요구합니다.
```

## 연습 문제

1. **(쉬움)** `bio_to_spans`(`spans_to_bio`의 역함수)를 구현하고, 문장 10개에서 왕복 일관성을 검증하세요.
2. **(보통)** 위의 sklearn-crfsuite CRF를 CoNLL-2003 영어 NER 데이터셋으로 학습시키고, `seqeval`로 개체별 F1을 보고하세요. 흔한 결과는 F1 ~84입니다.
3. **(어려움)** 도메인 특화 NER 데이터셋(의료, 법률, 또는 금융)으로 `distilbert-base-cased`를 파인튜닝하고, spaCy 소형 모델과 비교하세요. 데이터 누수 점검 과정을 문서화하고, 놀라웠던 점을 정리해서 쓰세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| NER | 이름 뽑아내기 | 토큰 범위에 타입(PERSON, ORG, GPE, DATE, ...) 레이블을 붙임. |
| BIO | 태깅 체계 | `B-X`는 시작, `I-X`는 계속, `O`는 밖. |
| BILOU | 더 나은 BIO | 더 깔끔한 경계를 위해 `L-X`(마지막), `U-X`(단독)를 추가. |
| CRF | 구조화 분류기 | 방출(emission)만이 아니라 레이블 사이의 전이까지 모델링. 유효한 시퀀스를 강제함. |
| 중첩 NER | 겹치는 개체 | 어떤 범위가 자기 부분 범위와 다른 개체인 경우. BIO로는 표현할 수 없음. |
| 개체 수준 F1 | 제대로 된 NER 지표 | 예측 범위가 실제 범위와 정확히 일치해야 함. 토큰 수준 F1은 정확도를 과장함. |

## 더 읽을거리

- [Lample et al. (2016). Neural Architectures for Named Entity Recognition](https://arxiv.org/abs/1603.01360) — BiLSTM-CRF 논문. 원전입니다.
- [Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers](https://arxiv.org/abs/1810.04805) — 이후 표준이 된 토큰 분류 패턴을 소개한 논문.
- [spaCy 언어 분석 기능 — 개체명](https://spacy.io/usage/linguistic-features#named-entities) — `Doc.ents`와 `Span`의 모든 속성에 관한 실전 레퍼런스.
- [seqeval](https://github.com/chakki-works/seqeval) — 올바른 지표 라이브러리. 언제나 이것을 쓰세요.
