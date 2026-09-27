> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# GloVe, FastText, 서브워드 임베딩

> Word2Vec은 단어 하나당 임베딩 하나를 학습했다. GloVe는 동시출현 행렬을 분해했다. FastText는 조각들을 임베딩했다. BPE는 트랜스포머로 가는 다리를 놓았다.

**유형:** 만들기
**언어:** Python
**선수 지식:** 페이즈 5 · 03 (Word2Vec 처음부터 만들기)
**소요 시간:** 약 45분

## 문제 상황

Word2Vec은 두 개의 미해결 질문을 남겼습니다.

첫째, 온라인 skip-gram 갱신이 아니라 동시출현 행렬을 직접 분해하는 병행 연구 계열(LSA, HAL)이 있었습니다. Word2Vec의 반복적 접근이 근본적으로 더 나은 걸까, 아니면 두 방법이 개수를 다루는 방식의 차이가 만든 겉모습일까. **GloVe**가 답했습니다. 손수 고른 손실 함수를 얹은 행렬 분해는 Word2Vec에 맞먹거나 이기며, 학습 비용도 더 적게 듭니다.

둘째, 어느 쪽도 한 번도 본 적 없는 단어에 대한 이야기가 없었습니다. `Zoomer-approved`, `dogecoin`, 지난주에 탄생한 고유명사, 희귀 어근의 굴절형 전부. **FastText**가 문자 n-그램을 임베딩하는 방식으로 이걸 고쳤습니다. 단어는 형태소를 포함한 부분들의 합이므로, 어휘 밖 단어도 그럴듯한 벡터를 얻습니다.

셋째, 트랜스포머가 등장하자 질문이 또 바뀌었습니다. 단어 수준 어휘는 백만 개쯤에서 한계에 부딪히는데, 실제 언어는 그보다 훨씬 열려 있습니다. **바이트 페어 인코딩(BPE)** 과 그 친척들은 자주 쓰이는 서브워드 단위의 어휘를 학습해 모든 것을 커버하는 방식으로 이 문제를 풀었습니다. 모든 현대 LLM의 모든 현대 토크나이저는 서브워드 토크나이저입니다.

이 레슨은 세 가지를 모두 다룬 뒤, 언제 무엇을 집어 들어야 하는지 알려 줍니다.

## 개념

**GloVe (Global Vectors).** `X[i][j]`가 단어 `i`의 문맥에 단어 `j`가 얼마나 자주 나오는지를 담은 단어-단어 동시출현 행렬 `X`를 만듭니다. `v_i · v_j + b_i + b_j ≈ log(X[i][j])`가 되도록 벡터를 학습합니다. 자주 나오는 쌍이 손실을 지배하지 않도록 손실에 가중치를 겁니다. 끝.

**FastText.** 단어는 자기 문자 n-그램들과 단어 자신의 합입니다. `where`는 `<wh, whe, her, ere, re>, <where>`가 됩니다. 단어 벡터는 그 구성 요소 벡터들의 합입니다. 학습은 Word2Vec처럼 합니다. 이점: 처음 보는 단어(`whereupon`)도 알려진 n-그램들로 조합된다는 것.

**BPE (Byte-Pair Encoding).** 개별 바이트(또는 문자)의 어휘에서 시작합니다. 말뭉치의 모든 인접 쌍을 세고, 가장 빈번한 쌍을 새 토큰으로 병합합니다. 이걸 `k`번 반복합니다. 결과: `k + 256`개 토큰의 어휘. 빈번한 시퀀스(`ing`, `tion`, `the`)는 토큰 하나가 되고 희귀 단어는 익숙한 조각들로 깨집니다. 어떤 문장이든 반드시 토큰화됩니다.

```figure
n5-subword-merge
```

## 만들어 보기

### GloVe: 동시출현 행렬 분해하기

```python
import numpy as np
from collections import Counter


def build_cooccurrence(docs, window=5):
    pair_counts = Counter()
    vocab = {}
    for doc in docs:
        for token in doc:
            if token not in vocab:
                vocab[token] = len(vocab)
    for doc in docs:
        indexed = [vocab[t] for t in doc]
        for i, center in enumerate(indexed):
            for j in range(max(0, i - window), min(len(indexed), i + window + 1)):
                if i != j:
                    distance = abs(i - j)
                    pair_counts[(center, indexed[j])] += 1.0 / distance
    return vocab, pair_counts


def glove_train(vocab, pair_counts, dim=16, epochs=100, lr=0.05, x_max=100, alpha=0.75, seed=0):
    n = len(vocab)
    rng = np.random.default_rng(seed)
    W = rng.normal(0, 0.1, size=(n, dim))
    W_tilde = rng.normal(0, 0.1, size=(n, dim))
    b = np.zeros(n)
    b_tilde = np.zeros(n)

    for epoch in range(epochs):
        for (i, j), x_ij in pair_counts.items():
            weight = (x_ij / x_max) ** alpha if x_ij < x_max else 1.0
            diff = W[i] @ W_tilde[j] + b[i] + b_tilde[j] - np.log(x_ij)
            coef = weight * diff

            grad_W_i = coef * W_tilde[j]
            grad_W_tilde_j = coef * W[i]
            W[i] -= lr * grad_W_i
            W_tilde[j] -= lr * grad_W_tilde_j
            b[i] -= lr * coef
            b_tilde[j] -= lr * coef

    return W + W_tilde
```

이름 붙일 만한 움직이는 부품이 둘 있습니다. 가중치 함수 `f(x) = (x/x_max)^alpha`는 매우 빈번한 쌍(`(the, and)` 같은)의 비중을 낮춰 손실을 지배하지 못하게 합니다. 최종 임베딩은 `W`(중심)와 `W_tilde`(문맥) 테이블의 합입니다. 둘을 더하는 건 논문으로 발표된 요령으로, 하나만 쓰는 것보다 보통 더 잘 나옵니다.

### FastText: 서브워드를 아는 임베딩

```python
def char_ngrams(word, n_min=3, n_max=6):
    wrapped = f"<{word}>"
    grams = {wrapped}
    for n in range(n_min, n_max + 1):
        for i in range(len(wrapped) - n + 1):
            grams.add(wrapped[i:i + n])
    return grams
```

```python
>>> char_ngrams("where")
{'<where>', '<wh', 'whe', 'her', 'ere', 're>', '<whe', 'wher', 'here', 'ere>', '<wher', 'where', 'here>'}
```

각 단어는 자기 n-그램 집합(보통 3~6자)으로 표현됩니다. 단어 임베딩은 그 n-그램 임베딩들의 합입니다. skip-gram 학습에서는 Word2Vec이 벡터 하나를 쓰던 자리에 이걸 끼워 넣으면 됩니다.

```python
def fasttext_vector(word, ngram_table):
    grams = char_ngrams(word)
    vecs = [ngram_table[g] for g in grams if g in ngram_table]
    if not vecs:
        return None
    return np.sum(vecs, axis=0)
```

처음 보는 단어라도 n-그램 일부가 알려져 있으면 벡터를 얻습니다. `whereupon`은 `where`와 `<wh`, `her`, `ere`, `<where`를 공유하므로, 둘은 서로 가깝게 착지합니다.

### BPE: 학습된 서브워드 어휘

```python
def learn_bpe(corpus, k_merges):
    vocab = Counter()
    for word, freq in corpus.items():
        tokens = tuple(word) + ("</w>",)
        vocab[tokens] = freq

    merges = []
    for _ in range(k_merges):
        pair_freq = Counter()
        for tokens, freq in vocab.items():
            for a, b in zip(tokens, tokens[1:]):
                pair_freq[(a, b)] += freq
        if not pair_freq:
            break
        best = pair_freq.most_common(1)[0][0]
        merges.append(best)

        new_vocab = Counter()
        for tokens, freq in vocab.items():
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i + 1 < len(tokens) and (tokens[i], tokens[i + 1]) == best:
                    new_tokens.append(tokens[i] + tokens[i + 1])
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            new_vocab[tuple(new_tokens)] = freq
        vocab = new_vocab
    return merges


def apply_bpe(word, merges):
    tokens = list(word) + ["</w>"]
    for a, b in merges:
        new_tokens = []
        i = 0
        while i < len(tokens):
            if i + 1 < len(tokens) and tokens[i] == a and tokens[i + 1] == b:
                new_tokens.append(a + b)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        tokens = new_tokens
    return tokens
```

```python
>>> corpus = Counter({"low": 5, "lower": 2, "newest": 6, "widest": 3})
>>> merges = learn_bpe(corpus, k_merges=10)
>>> apply_bpe("lowest", merges)
['low', 'est</w>']
```

첫 반복에서 가장 흔한 인접 쌍을 병합합니다. 반복이 충분히 쌓이면 빈번한 부분 문자열(`low`, `est`, `tion`)은 토큰 하나가 되고, 희귀 단어는 깔끔하게 쪼개집니다.

실제 GPT / BERT / T5 토크나이저는 3만~10만 개의 병합을 학습합니다. 결과: 어떤 텍스트든 알려진 ID의 길이 제한된 시퀀스로 토큰화됩니다. OOV는 이제 존재하지 않습니다.

## 활용하기

실전에서는 이것들을 직접 학습시킬 일이 거의 없습니다. 사전학습 체크포인트를 불러 옵니다.

```python
import fasttext.util
fasttext.util.download_model("en", if_exists="ignore")
ft = fasttext.load_model("cc.en.300.bin")
print(ft.get_word_vector("whereupon").shape)
print(ft.get_word_vector("zoomerapproved").shape)
```

트랜스포머 시대의 BPE 스타일 서브워드 토큰화:

```python
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("gpt2")
print(tok.tokenize("unbelievably tokenized"))
```

```
['un', 'bel', 'iev', 'ably', 'Ġtoken', 'ized']
```

`Ġ` 접두사가 단어 경계를 표시합니다(GPT-2의 관례). 모든 현대 토크나이저는 BPE 변형, WordPiece(BERT), 또는 SentencePiece(T5, LLaMA) 중 하나입니다.

### 언제 무엇을 고를까

| 상황 | 선택 |
|-----------|------|
| 사전학습 범용 단어 벡터, OOV 감내가 필요 없음 | GloVe 300d |
| 사전학습 범용 단어 벡터, 오타/신조어/굴절이 풍부한 언어를 반드시 처리해야 함 | FastText |
| 트랜스포머로 들어가는 모든 것(학습이든 추론이든) | 모델이 출고 때 들고 나온 그 토크나이저. 절대 교체 금지. |
| 자기만의 언어 모델을 처음부터 학습 | 먼저 자기 말뭉치로 BPE 또는 SentencePiece 토크나이저를 학습 |
| 선형 모델로 하는 프로덕션 텍스트 분류 | 여전히 TF-IDF. 레슨 02. |

## 출시하기

`outputs/skill-embeddings-picker.md`로 저장하세요:

```markdown
---
name: tokenizer-picker
description: 새 언어 모델이나 텍스트 파이프라인을 위한 토큰화 방식을 고른다.
version: 1.0.0
phase: 5
lesson: 04
tags: [nlp, tokenization, embeddings]
---

작업과 데이터셋 설명이 주어지면 다음을 출력합니다:

1. 토큰화 전략(단어 수준, BPE, WordPiece, SentencePiece, 바이트 수준). 한 문장 근거.
2. 목표 어휘 크기(예: 영어 전용 LM은 32k, 다국어는 64k-100k).
3. 정확한 학습 명령이 들어간 라이브러리 호출. 라이브러리 이름을 적고 인자를 인용한다.
4. 재현성 함정 하나. 토크나이저-모델 불일치는 가장 흔한 조용한 프로덕션 버그다. 어떤 조합이 함께 쓰여야 하는지 짚어 준다.

사용자가 사전학습 LLM을 파인튜닝하는 중이라면 커스텀 토크나이저 학습을 권하지 않는다. 프로덕션 추론을 목표로 하는 모델에는 단어 수준 토큰화를 권하지 않는다. 영어가 아닌/다중 문자 체계 말뭉치는 바이트 폴백이 있는 SentencePiece가 필요하다고 표시한다.
```

## 연습 문제

1. **쉬움.** `char_ngrams("playing")`과 `char_ngrams("played")`를 돌려 보세요. 두 n-그램 집합의 자카드(Jaccard) 겹침을 계산하세요. 공유 조각이 상당할 겁니다(`pla`, `lay`, `play`). FastText가 형태론적 변형에 걸쳐 잘 전이되는 이유가 바로 이것입니다.
2. **보통.** `learn_bpe`에 어휘 성장 추적을 추가해 보세요. 병합 횟수의 함수로 말뭉치 글자당 토큰 수를 그래프로 그리세요. 처음엔 빠르게 압축되다가 토큰당 약 2~3자 근처로 수렴하는 모습이 보일 겁니다.
3. **어려움.** 셰익스피어 전집으로 병합 1,000개짜리 BPE를 학습시켜 보세요. 흔한 단어 vs 희귀 고유명사의 토큰화를 비교하고, 전후의 단어당 평균 토큰 수를 측정하세요. 놀라웠던 점을 적어 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 동시출현 행렬 | 단어-단어 빈도표 | `X[i][j]` = 단어 `i` 주변 윈도우에 단어 `j`가 나오는 빈도. |
| 서브워드 | 단어의 조각 | 문자 n-그램(FastText) 또는 학습된 토큰(BPE/WordPiece/SentencePiece). |
| BPE | 바이트 페어 인코딩 | 가장 빈번한 인접 쌍을 어휘가 목표 크기에 도달할 때까지 반복 병합. |
| OOV | 어휘 밖(Out of Vocabulary) | 모델이 한 번도 본 적 없는 단어. Word2Vec/GloVe는 실패. FastText와 BPE는 처리. |
| 바이트 수준 BPE | 날것 바이트 위의 BPE | GPT-2의 방식. 어휘가 256바이트에서 시작하므로 어떤 것도 절대 OOV가 아니다. |

## 더 읽을거리

- [Pennington, Socher, Manning (2014). GloVe: Global Vectors for Word Representation](https://nlp.stanford.edu/pubs/glove.pdf) — GloVe 논문. 7페이지인데 지금도 손실 함수에 관한 최고의 유도.
- [Bojanowski et al. (2017). Enriching Word Vectors with Subword Information](https://arxiv.org/abs/1607.04606) — FastText.
- [Sennrich, Haddow, Birch (2016). Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — BPE를 현대 NLP에 도입한 논문.
- [Hugging Face tokenizer summary](https://huggingface.co/docs/transformers/tokenizer_summary) — BPE, WordPiece, SentencePiece가 실전에서 실제로 어떻게 다른지.
