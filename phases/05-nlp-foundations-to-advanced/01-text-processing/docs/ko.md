> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 텍스트 처리 — 토큰화, 어간 추출, 표제어 추출

> 언어는 연속적입니다. 모델은 이산적입니다. 전처리는 그 둘을 잇는 다리입니다.

**유형:** 만들기
**언어:** Python
**선수 지식:** 페이즈 2 · 14 (나이브 베이즈)
**소요 시간:** 약 45분

## 문제 상황

모델은 "The cats were running."이라는 문장을 읽을 수 없습니다. 모델이 읽는 건 정수입니다.

모든 NLP 시스템은 똑같은 세 가지 질문으로 시작합니다. 단어는 어디서 시작하는가. 단어의 어근은 무엇인가. 그리고 "run", "running", "ran"을 도움이 될 때는 같은 것으로, 도움이 안 될 때는 다른 것으로 어떻게 다루는가.

토큰화를 잘못하면 모델은 쓰레기로부터 학습합니다. 토크나이저가 `don't`는 토큰 하나로 다루는데 `do n't`는 둘로 나눈다면, 학습 분포가 갈라집니다. 어간 추출기(stemmer)가 `organization`과 `organ`을 같은 어간으로 뭉개 버리면, 토픽 모델링은 망합니다. 표제어 추출기(lemmatizer)가 품사 문맥을 필요로 하는데 그걸 넘겨 주지 않으면, 동사가 명사처럼 취급됩니다.

이 레슨에서는 세 가지 전처리 단계를 처음부터 직접 만들어 본 뒤, NLTK와 spaCy가 같은 일을 어떻게 하는지 보여 줍니다. 그래야 트레이드오프가 눈에 보이니까요.

## 개념

세 가지 연산. 각각 맡은 일과 실패 지점이 있습니다.

**토큰화(Tokenization)** 는 문자열을 토큰으로 쪼갭니다. "토큰"이라는 말이 일부러 모호하게 쓰인 건, 알맞은 입자 크기가 작업에 따라 달라지기 때문입니다. 고전 NLP는 단어 단위. 트랜스포머는 서브워드(subword). 공백이 없는 언어는 문자 단위.

**어간 추출(Stemming)** 은 규칙으로 접미사를 잘라 냅니다. 빠르고, 공격적이고, 멍청합니다. `running -> run`. `organization -> organ`. 두 번째 예가 바로 실패 지점입니다.

**표제어 추출(Lemmatization)** 은 문법 지식을 동원해 단어를 사전 형태로 줄입니다. 더 느리고 정확하며, 조회 테이블이나 형태소 분석기가 필요합니다. `ran -> run` ("ran"이 "run"의 과거형임을 알아야 함). `better -> good` (비교급 형태를 알아야 함).

경험 법칙. 속도가 중요하고 어느 정도의 노이즈를 감내할 수 있으면(검색 색인, 대략적 분류) 어간 추출을 씁니다. 의미가 중요하면(질의응답, 의미 검색, 사용자가 직접 읽을 모든 것) 표제어 추출을 씁니다.

```figure
edit-distance
```

## 만들어 보기

### 단계 1: 정규식 단어 토크나이저

가장 단순하면서도 쓸 만한 토크나이저는 알파벳·숫자가 아닌 문자를 기준으로 나누되, 문장부호는 독립 토큰으로 남겨 둡니다. 완벽하지도, 최종 형태도 아니지만 한 줄로 동작합니다.

```python
import re

def tokenize(text):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[0-9]+|[^\sA-Za-z0-9]", text)
```

우선순위 순으로 세 가지 패턴입니다. 안쪽에 어포스트로피를 가질 수 있는 단어(`don't`, `it's`). 순수 숫자. 그리고 공백·알파벳·숫자가 아닌 문자 하나하나를 독립 토큰으로(문장부호).

```python
>>> tokenize("The cats weren't running at 3pm.")
['The', 'cats', "weren't", 'running', 'at', '3', 'pm', '.']
```

주목할 실패 지점들. `3pm`이 `['3', 'pm']`으로 나뉩니다. 알파벳 덩어리와 숫자 덩어리를 번갈아 매칭하기 때문입니다. 대부분의 작업엔 충분합니다. URL, 이메일, 해시태그는 전부 깨집니다. 프로덕션에서는 범용 패턴 앞에 전용 패턴을 추가하세요.

### 단계 2: 포터 어간 추출기 (1a 단계만)

포터(Porter) 알고리즘 전체는 다섯 페이즈의 규칙을 갖습니다. 1a 단계만으로도 가장 빈번한 영어 접미사를 커버하고 패턴을 익힐 수 있습니다.

```python
def stem_step_1a(word):
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies"):
        return word[:-2]
    if word.endswith("ss"):
        return word
    if word.endswith("s") and len(word) > 1:
        return word[:-1]
    return word
```

```python
>>> [stem_step_1a(w) for w in ["caresses", "ponies", "caress", "cats"]]
['caress', 'poni', 'caress', 'cat']
```

규칙을 위에서 아래로 읽으세요. `ies -> i` 규칙 때문에 `ponies`가 `pony`가 아니라 `poni`가 됩니다. 진짜 포터는 이걸 고쳐 주는 1b 단계를 갖고 있습니다. 규칙들은 서로 경쟁하고, 먼저 온 규칙이 이깁니다. 개별 규칙보다 순서가 더 중요합니다.

### 단계 3: 조회 기반 표제어 추출기

제대로 된 표제어 추출은 형태론(morphology)이 필요합니다. 가르치기 용으로는 작은 표제어 테이블과 폴백(fallback) 규칙을 쓰면 다룰 만합니다.

```python
LEMMA_TABLE = {
    ("running", "VERB"): "run",
    ("ran", "VERB"): "run",
    ("runs", "VERB"): "run",
    ("better", "ADJ"): "good",
    ("best", "ADJ"): "good",
    ("cats", "NOUN"): "cat",
    ("cat", "NOUN"): "cat",
    ("were", "VERB"): "be",
    ("was", "VERB"): "be",
    ("is", "VERB"): "be",
}

def lemmatize(word, pos):
    key = (word.lower(), pos)
    if key in LEMMA_TABLE:
        return LEMMA_TABLE[key]
    if pos == "VERB" and word.endswith("ing"):
        return word[:-3]
    if pos == "NOUN" and word.endswith("s"):
        return word[:-1]
    return word.lower()
```

```python
>>> lemmatize("running", "VERB")
'run'
>>> lemmatize("cats", "NOUN")
'cat'
>>> lemmatize("better", "ADJ")
'good'
>>> lemmatize("watched", "VERB")
'watched'
```

마지막 사례가 핵심 학습 포인트입니다. `watched`는 테이블에 없고 폴백은 `ing`만 다룹니다. 진짜 표제어 추출은 `ed`, 불규칙 동사, 비교급 형용사, 소리가 변하는 복수형(`children -> child`)까지 커버합니다. 프로덕션 시스템이 WordNet, spaCy의 형태론 분석기(morphologizer), 또는 완전한 형태소 분석기를 쓰는 이유입니다.

### 단계 4: 하나로 연결하기

```python
def preprocess(text, pos_tagger=None):
    tokens = tokenize(text)
    stems = [stem_step_1a(t.lower()) for t in tokens]
    tags = pos_tagger(tokens) if pos_tagger else [(t, "NOUN") for t in tokens]
    lemmas = [lemmatize(word, pos) for word, pos in tags]
    return {"tokens": tokens, "stems": stems, "lemmas": lemmas}
```

빠진 조각은 POS 태거입니다. 페이즈 5 · 07(품사 태깅)에서 하나를 만듭니다. 지금은 전부 `NOUN`으로 기본값을 두고 한계를 인정하는 선에서 마무리합니다.

## 활용하기

NLTK와 spaCy는 프로덕션용 구현을 갖고 있습니다. 각각 몇 줄이면 됩니다.

### NLTK

```python
import nltk
nltk.download("punkt_tab")
nltk.download("wordnet")
nltk.download("averaged_perceptron_tagger_eng")

from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk import pos_tag

text = "The cats were running."
tokens = word_tokenize(text)
stems = [PorterStemmer().stem(t) for t in tokens]
lemmatizer = WordNetLemmatizer()
tagged = pos_tag(tokens)


def nltk_pos_to_wordnet(tag):
    if tag.startswith("V"):
        return "v"
    if tag.startswith("J"):
        return "a"
    if tag.startswith("R"):
        return "r"
    return "n"


lemmas = [lemmatizer.lemmatize(t, nltk_pos_to_wordnet(tag)) for t, tag in tagged]
```

`word_tokenize`는 축약형, 유니코드, 정규식이 놓치는 예외 상황을 처리해 줍니다. `PorterStemmer`는 다섯 페이즈 전부를 실행합니다. `WordNetLemmatizer`는 NLTK의 Penn Treebank 체계 품사 태그를 WordNet의 약어 체계로 번역해야 합니다. 위의 번역 연결부가 대부분의 튜토리얼이 건너뛰는 부분입니다.

### spaCy

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("The cats were running.")

for token in doc:
    print(token.text, token.lemma_, token.pos_)
```

```
The      the     DET
cats     cat     NOUN
were     be      AUX
running  run     VERB
.        .       PUNCT
```

spaCy는 전체 파이프라인을 `nlp(text)` 뒤에 숨겨 둡니다. 토큰화, 품사 태깅, 표제어 추출이 전부 돌아갑니다. 규모가 커지면 NLTK보다 빠르고, 바로 써도 더 정확합니다. 트레이드오프는 개별 구성 요소를 쉽게 갈아끼울 수 없다는 점입니다.

### 언제 무엇을 고를까

| 상황 | 선택 |
|-----------|------|
| 교육, 연구, 구성 요소 교체 | NLTK |
| 프로덕션(운영 환경), 다국어, 속도가 중요 | spaCy |
| 트랜스포머 파이프라인(어차피 모델의 토크나이저로 토큰화함) | `tokenizers` / `transformers`를 쓰고 고전 전처리는 생략 |

### 아무도 경고해 주지 않는 두 가지 실패 지점

대부분의 튜토리얼은 알고리즘만 가르치고 끝납니다. 실제 전처리 파이프라인을 물어 뜯는 문제 두 가지는 거의 다뤄지지 않습니다.

**재현성 드리프트.** NLTK와 spaCy는 버전 사이에서 토큰화와 표제어 추출 동작이 바뀝니다. spaCy 2.x에서 `['do', "n't"]`가 나오던 것이 3.x에서는 `["don't"]`가 나올 수 있습니다. 모델은 한쪽 분포로 학습했는데, 추론 시점에는 다른 분포에서 돌아가는 거죠. 정확도가 조용히 떨어지고 아무도 이유를 모릅니다. `requirements.txt`에 라이브러리 버전을 고정하세요. 샘플 문장 20개의 기대 토큰화 결과를 얼려 두는 전처리 회귀 테스트를 작성하고, 업그레이드 때마다 돌리세요.

**학습/추론 불일치.** 공격적인 전처리(소문자화, 불용어 제거, 어간 추출)로 학습하고, 날것 그대로의 사용자 입력으로 배포하면, 성능이 곤두박질칩니다. 프로덕션 NLP 실패 중 단연 1위 사례입니다. 학습 때 전처리를 했다면 추론에서도 완전히 동일한 함수를 실행해야 합니다. 전처리는 서빙 팀이 노트북 셀에서 재작성하는 게 아니라, 모델 패키지 안에 함수로 담아 출시하세요.

## 출시하기

엔지니어가 교과서 세 권을 읽지 않고도 전처리 전략을 고를 수 있게 도와 주는 재사용 가능한 프롬프트입니다.

`outputs/prompt-preprocessing-advisor.md`로 저장하세요:

```markdown
---
name: preprocessing-advisor
description: NLP 작업에 맞는 토큰화, 어간 추출, 표제어 추출 설정을 추천한다.
phase: 5
lesson: 01
---

당신은 고전 NLP 전처리를 자문합니다. 작업 설명이 주어지면 다음을 출력합니다:

1. 토큰화 선택(regex, NLTK word_tokenize, spaCy, 또는 트랜스포머 토크나이저). 이유를 설명한다.
2. 어간 추출, 표제어 추출, 둘 다, 또는 둘 다 아님 중 무엇을 할지. 이유를 설명한다.
3. 구체적인 라이브러리 호출. 함수 이름을 적는다. NLTK가 관련되면 품사 태그 번역도 인용한다.
4. 사용자가 테스트해야 할 실패 지점 하나.

사용자가 직접 보는 텍스트에는 어간 추출을 권하지 않는다. 품사 태그 없이 표제어 추출을 권하지 않는다. 영어가 아닌 입력은 다른 파이프라인이 필요하다고 표시한다.
```

## 연습 문제

1. **쉬움.** `tokenize`를 확장해 URL을 토큰 하나로 유지해 보세요. 테스트: `tokenize("Visit https://example.com today.")`가 URL 토큰 하나를 만들어야 합니다.
2. **보통.** 포터 1b 단계를 구현해 보세요. 단어에 모음이 포함되어 있고 `ed` 또는 `ing`로 끝나면 잘라 냅니다. 이중 자음 규칙도 처리하세요(`hopping -> hop`, `hopp`가 아님).
3. **어려움.** WordNet을 조회 테이블로 쓰되 WordNet에 항목이 없으면 포터 어간 추출기로 폴백하는 표제어 추출기를 만들어 보세요. 태그가 달린 말뭉치에서 순수 WordNet과 순수 포터 대비 정확도를 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 토큰 | 단어 | 모델이 소비하는 단위 무엇이든. 단어, 서브워드, 문자, 바이트 모두 가능. |
| 어간(stem) | 단어의 뿌리 | 규칙 기반 접미사 제거의 결과. 실제 단어가 아닐 수도 있다. |
| 표제어(lemma) | 사전 형태 | 사전에서 찾을 그 형태. 올바르게 계산하려면 문법적 문맥이 필요하다. |
| POS 태그 | 품사 | NOUN, VERB, ADJ 같은 범주. 정확한 표제어 추출에 필요하다. |
| 형태론 | 단어 모양 변화 규칙 | 시제, 수, 격에 따라 단어 형태가 변하는 방식. 표제어 추출이 여기에 의존한다. |

## 더 읽을거리

- [Porter, M. F. (1980). An algorithm for suffix stripping](https://tartarus.org/martin/PorterStemmer/def.txt) — 원논문. 5페이지인데 지금도 가장 명쾌한 설명.
- [spaCy 101 — linguistic features](https://spacy.io/usage/linguistic-features) — 실제 파이프라인이 어떻게 연결되는지.
- [NLTK book, chapter 3](https://www.nltk.org/book/ch03.html) — 아직 생각지도 못한 토큰화 예외 사례들.
