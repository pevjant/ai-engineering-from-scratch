> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 트랜스포머 이전의 텍스트 생성 — N-그램 언어 모델

> 어떤 단어가 놀라운 단어라면, 그 모델은 나쁜 모델입니다. 퍼플렉시티(perplexity)는 이 '놀람'을 숫자로 만들고, 스무딩(smoothing)은 그 숫자를 무한대로 뛰지 않게 잡아 줍니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 01(텍스트 처리), 페이즈 2 · 14(나이브 베이즈)
**시간:** 약 45분

## 문제 상황

트랜스포머 이전, RNN 이전, 단어 임베딩 이전의 언어 모델은 다음 단어를 예측할 때 바로 앞의 `n-1`개 단어 뒤에 그 단어가 나온 횟수를 셌습니다. "the cat" → "sat"은 47번, "the cat" → "jumped"는 12번, "the cat" → "refrigerator"는 0번. 그 카운트를 정규화하면 확률 분포가 됩니다.

이것이 n-그램 언어 모델입니다. 1980년부터 2015년까지 모든 음성 인식기, 모든 맞춤법 검사기, 모든 구구절절한(phrase-based) 기계 번역 시스템이 이걸로 돌아갔습니다. 지금도 기기 위에서 돌아가는 값싼 언어 모델링이 필요하면 쓰입니다.

흥미로운 문제는 학습에서 한 번도 본 적 없는 n-그램을 어떻게 처리하느냐입니다. 카운트만 세는 날것의 모델은 본 적 없는 것에 확률 0을 부여하는데, 문장은 길고 거의 모든 긴 문장에는 본 적 없는 시퀀스가 최소 하나씩 있으니 이건 치명적입니다. 50년에 걸친 스무딩 연구가 이 문제를 해결했고, 그 결실이 Kneser-Ney 스무딩입니다. 현대 딥러닝은 이 연구의 경험적 전통을 물려받았습니다.

## 핵심 개념

![N-그램 모델: 세기, 스무딩하기, 생성하기](../assets/ngram.svg)

### 예측 게임

이런 장치들이 존재하기 전에, 하나의 실험이 언어 모델이 무엇인지를 정의했습니다. 영어 문장의 다음 글자를 가리고, 누군가에게 맞힐 때까지 한 번에 하나씩 추측하게 합니다. 추측 횟수를 기록하고, 이를 수백 글자에 걸쳐 반복합니다.

이 추측 횟수는 잡지식이 아닙니다. 텍스트의 무손실 재인코딩입니다. 횟수 시퀀스를 똑같은 추측꾼 둘째에게 넘기면 모든 글자를 복원할 수 있습니다. 각 위치에서 어떤 추측이 먼저 나왔는지 정확히 알 수 있기 때문입니다. 더 적은 기호로 다시 인코딩할 수 있는 메시지는 기호당 담고 있는 정보가 적은 것이므로, 추측 횟수 통계는 영어의 엔트로피 상한선을 정합니다.

Shannon은 1951년에 이 실험을 돌렸고, 지금도 이 분야를 지배하는 숫자를 얻었습니다. 27개 기호 알파벳(알파벳 26자 + 공백)은 글자당 최대 `log2(27) ≈ 4.75` 비트를 담을 수 있습니다. 100글자 컨텍스트를 가진 사람 추측꾼은 글자당 0.6~1.3 비트 사이에 들어왔습니다. 영어는 대략 4분의 3이 강제된 수라는 뜻입니다. 모델이 배워야 할 구조가, 그것을 배울 모델이 존재하기도 전에 측정된 셈입니다.

그 이후의 모든 언어 모델은 이 게임의 기계 플레이어이고, 이 레슨의 모든 평가 숫자는 이 게임의 점수표입니다:

- **크로스 엔트로피 손실**은 모델이 기호 하나당 필요로 하는 평균 비트 수입니다. LM을 학습시킨다는 건 문자 그대로 이 추측 게임 점수를 최소화하는 겁니다.
- **퍼플렉시티**는 `2^bits`(또는 `e^nats`)입니다. 추측이 끝난 뒤에도 모델 앞에 남아 있는 갈래 수(branching factor)입니다. 27개 기호를 균등하게 찍는 추측꾼의 퍼플렉시티는 27이고, 글자당 1비트짜리 플레이어는 퍼플렉시티 2입니다.
- **컨텍스트 길이는 플레이어의 기억력입니다.** 트라이그램 모델은 토큰 2개짜리 기억으로 게임을 하고, 트랜스포머는 10만 토큰 기억으로 같은 게임을 합니다. 규칙은 한 번도 바뀌지 않았고, 플레이어만 나아졌습니다.

단위 하나만 짚고 넘어가면: 이 게임은 비트(`log2`) 단위로 글자당 점수를 매기는 반면, 아래의 n-그램 공식은 nat(자연로그) 단위로 단어 토큰당 점수를 매깁니다. 그리고 nat 단위 퍼플렉시티 `e^H`는 비트 단위 `2^H`와 같으므로, 두 관점은 단위만 다른 같은 측정입니다.

```figure
prediction-game
```

**N-그램 확률:** `P(w_i | w_{i-n+1}, ..., w_{i-1})`. `n`을 고정합니다(보통 트라이그램은 3, 4-그램은 4). 카운트에서 계산합니다:

```text
P(w | context) = count(context, w) / count(context)
```

**카운트 0 문제.** 학습에서 본 적 없는 n-그램은 확률 0을 받습니다. 2007년 Brown 코퍼스 연구에 따르면 4-그램 모델조차 평가용 4-그램의 30%가 학습에 등장하지 않았습니다. 스무딩 없이는 어떤 실제 텍스트로도 평가할 수 없습니다.

**스무딩 접근법, 정교해지는 순서대로:**

1. **라플라스(add-one).** 모든 카운트에 1을 더합니다. 단순하지만 희귀 이벤트에서는 끔찍합니다.
2. **Good-Turing.** '빈도의 빈도'를 근거로, 높은 빈도 이벤트에서 확률 질량을 떼어 본 적 없는 이벤트에 재분배합니다.
3. **보간(interpolation).** n-그램, (n-1)-그램 등의 추정치를 조절 가능한 가중치로 합칩니다.
4. **백오프(backoff).** n-그램 카운트가 0이면 (n-1)-그램으로 물러납니다. Katz 백오프가 이를 정규화합니다.
5. **절대 할인(absolute discounting).** 모든 카운트에서 고정 할인치 `D`를 빼고, 그 몫을 미관측 이벤트에 재분배합니다.
6. **Kneser-Ney.** 절대 할인에 더해 하위 차수 모델을 위한 영리한 선택: 원 빈도 대신 *연속 확률(continuation probability)*, 즉 그 단어가 몇 개의 컨텍스트에서 나타나는지를 사용합니다.

Kneser-Ney의 통찰은 깊습니다. "San Francisco"는 흔한 바이그램입니다. 유니그램 "Francisco"는 거의 "San" 뒤에만 나오죠. 순진한 절대 할인은 카운트가 크다는 이유로 "Francisco"에 높은 유니그램 확률을 줍니다. Kneser-Ney는 "Francisco"가 단 하나의 컨텍스트에만 나타난다는 점을 짚고, 연속 확률을 그에 맞게 낮춥니다. 결과: "Francisco"로 끝나는 처음 보는 바이그램이 알맞게 낮은 확률을 받습니다.

**평가: 퍼플렉시티.** 보류해 둔(held-out) 테스트셋에서 단어당 평균 음의 로그 가능도의 지수 값입니다. 낮을수록 좋습니다. 퍼플렉시티 100은 모델이 100개 단어 중 균등하게 찍을 때와 같은 수준으로 헷갈린다는 뜻입니다.

```text
perplexity = exp(- (1/N) * Σ log P(w_i | context_i))
```

```figure
ngram-backoff
```

## 만들어 보기

### 단계 1: 트라이그램 카운트

```python
from collections import Counter, defaultdict


def train_ngram(corpus_tokens, n=3):
    ngrams = Counter()
    contexts = Counter()
    for sentence in corpus_tokens:
        padded = ["<s>"] * (n - 1) + sentence + ["</s>"]
        for i in range(len(padded) - n + 1):
            ctx = tuple(padded[i:i + n - 1])
            word = padded[i + n - 1]
            ngrams[ctx + (word,)] += 1
            contexts[ctx] += 1
    return ngrams, contexts


def raw_probability(ngrams, contexts, context, word):
    ctx = tuple(context)
    if contexts.get(ctx, 0) == 0:
        return 0.0
    return ngrams.get(ctx + (word,), 0) / contexts[ctx]
```

입력은 토큰화된 문장들의 목록입니다. 출력은 n-그램 카운트와 컨텍스트 카운트입니다. `<s>`와 `</s>`는 문장 경계입니다.

### 단계 2: 라플라스 스무딩

```python
def laplace_probability(ngrams, contexts, vocab_size, context, word):
    ctx = tuple(context)
    numerator = ngrams.get(ctx + (word,), 0) + 1
    denominator = contexts.get(ctx, 0) + vocab_size
    return numerator / denominator
```

모든 카운트에 1을 더합니다. 스무딩은 되지만 미관측 이벤트에 질량을 과하게 배분해서, 희귀하지만 알려진 이벤트까지 해를 봅니다.

### 단계 3: Kneser-Ney (바이그램, 보간식)

```python
def kneser_ney_bigram_model(corpus_tokens, discount=0.75):
    unigrams = Counter()
    bigrams = Counter()
    unigram_contexts = defaultdict(set)

    for sentence in corpus_tokens:
        padded = ["<s>"] + sentence + ["</s>"]
        for i, w in enumerate(padded):
            unigrams[w] += 1
            if i > 0:
                prev = padded[i - 1]
                bigrams[(prev, w)] += 1
                unigram_contexts[w].add(prev)

    total_unique_bigrams = sum(len(ctx_set) for ctx_set in unigram_contexts.values())
    continuation_prob = {
        w: len(ctx_set) / total_unique_bigrams for w, ctx_set in unigram_contexts.items()
    }

    context_totals = Counter()
    for (prev, w), count in bigrams.items():
        context_totals[prev] += count

    unique_follow = defaultdict(set)
    for (prev, w) in bigrams:
        unique_follow[prev].add(w)

    def prob(prev, w):
        count = bigrams.get((prev, w), 0)
        denom = context_totals.get(prev, 0)
        if denom == 0:
            return continuation_prob.get(w, 1e-9)
        first_term = max(count - discount, 0) / denom
        lambda_prev = discount * len(unique_follow[prev]) / denom
        return first_term + lambda_prev * continuation_prob.get(w, 1e-9)

    return prob
```

움직이는 부품은 셋입니다. `continuation_prob`는 "이 단어가 서로 다른 컨텍스트 몇 개에서 나오나?"를 담습니다(Kneser-Ney의 혁신). `lambda_prev`는 할인으로 확보된 질량으로, 백오프 항의 가중치로 쓰입니다. 최종 확률은 할인된 주항에 가중치가 곱해진 연속 확률 항을 더한 것입니다.

### 단계 4: 샘플링으로 텍스트 생성하기

```python
import random


def generate(prob_fn, vocab, prefix, max_len=30, seed=0):
    rng = random.Random(seed)
    tokens = list(prefix)
    for _ in range(max_len):
        candidates = [(w, prob_fn(tokens[-1], w)) for w in vocab]
        total = sum(p for _, p in candidates)
        r = rng.random() * total
        acc = 0.0
        for w, p in candidates:
            acc += p
            if r <= acc:
                tokens.append(w)
                break
        if tokens[-1] == "</s>":
            break
    return tokens
```

확률에 비례해서 샘플링합니다. 시드만 다르면 항상 다른 출력이 나옵니다. 빔 검색(beam search) 비슷한 출력을 원하면 매 단계 최댓값(argmax)을 고르고(그리디), 작은 무작위성 손잡이(temperature)를 추가하세요.

### 단계 5: 퍼플렉시티

```python
import math


def perplexity(prob_fn, sentences):
    total_log_prob = 0.0
    total_tokens = 0
    for sentence in sentences:
        padded = ["<s>"] + sentence + ["</s>"]
        for i in range(1, len(padded)):
            p = prob_fn(padded[i - 1], padded[i])
            total_log_prob += math.log(max(p, 1e-12))
            total_tokens += 1
    return math.exp(-total_log_prob / total_tokens)
```

낮을수록 좋습니다. Brown 코퍼스에서 잘 튜닝된 4-그램 KN 모델은 퍼플렉시티 140 근처에 도달합니다. 같은 테스트셋에서 트랜스포머 LM은 15-30을 기록합니다. 격차는 약 10배입니다. 그 격차가 이 분야가 다음 단계로 넘어간 이유입니다.

## 사용해 보기

- **클래식 NLP 교육.** 스무딩, MLE(최대 가능도 추정), 퍼플렉시티를 가장 선명하게 접할 수 있는 소재입니다.
- **KenLM.** 프로덕션용 n-그램 라이브러리. 지연 시간이 중요한 음성·기계번역 시스템에서 재채점기(rescorer)로 쓰입니다.
- **기기 위 자동완성.** 키보드 안의 트라이그램 모델. 지금도 그렇습니다.
- **베이스라인.** 신경망 LM이 좋다고 선언하기 전에 반드시 n-그램 LM 퍼플렉시티를 계산하세요. 여러분의 트랜스포머가 KN을 큰 격차로 이기지 못한다면 뭔가 잘못된 겁니다.

## 출시하기

`outputs/prompt-lm-baseline.md`로 저장하세요:

```markdown
---
name: lm-baseline
description: 신경망 LM을 학습하기 전에 재현 가능한 n-그램 언어 모델 베이스라인 만들기.
phase: 5
lesson: 16
---

코퍼스와 목적(다음 단어 예측, 재채점, 퍼플렉시티 베이스라인)이 주어지면 다음을 출력하세요:

1. N-그램 차수. 일반 영어는 트라이그램, 코퍼스가 크면 4-그램, 음성 재채점은 5-그램.
2. 스무딩. Modified Kneser-Ney가 기본값; 라플라스는 교육용으로만.
3. 라이브러리. 프로덕션은 `kenlm`, 교육은 `nltk.lm`, 직접 만드는 건 수학을 배우려는 경우에만.
4. 평가. 학습셋과 테스트셋 사이 토큰화를 일관되게 유지한 보류(held-out) 퍼플렉시티.

비교하려는 시스템들끼리 토큰화가 다른 상태에서 계산한 퍼플렉시티는 보고하지 마세요 — 퍼플렉시티 숫자는 토큰화가 완전히 같을 때만 비교 가능합니다. 테스트셋의 OOV(어휘 외 단어) 비율도 표시하세요. KN은 학습 중 특별한 <UNK> 토큰을 따로 두지 않으면 OOV를 잘 처리하지 못합니다.
```

## 연습 문제

1. **쉬움.** 셰익스피어 문장 1,000개 코퍼스로 트라이그램 LM을 학습시키세요. 문장 20개를 생성해 보면 국소적으로는 그럴듯하지만 전체적으로는 형편없는 결과가 나옵니다. 이게 바로 정석 데모입니다.
2. **중간.** 보류해 둔 셰익스피어 스플릿에서 KN 모델의 퍼플렉시티를 구현하세요. 라플라스와 비교하면 KN이 퍼플렉시티를 30-50% 낮추는 걸 볼 수 있어야 합니다.
3. **어려움.** 트라이그램 맞춤법 교정기를 만드세요: 오타 낸 단어와 그 컨텍스트가 주어지면 교정 후보를 생성하고, LM 아래에서의 컨텍스트 확률로 순위를 매깁니다. 공개된 Birkbeck 철자 코퍼스로 평가하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| N-그램 | 단어 시퀀스 | 연속된 `n`개 토큰의 시퀀스. |
| 스무딩 | 0 피하기 | 본 적 없는 이벤트도 0이 아닌 확률을 갖도록 확률 질량을 재분배하는 것. |
| 퍼플렉시티 | LM 품질 지표 | 보류(held-out) 데이터에서의 `exp(-평균 로그 확률)`. 낮을수록 좋음. |
| 백오프 | 더 짧은 컨텍스트로 물러남 | 트라이그램 카운트가 0이면 바이그램을 사용. Katz 백오프가 이를 형식화함. |
| Kneser-Ney | n-그램 최고의 스무딩 | 절대 할인 + 하위 차수 모델을 위한 연속 확률. |
| 연속 확률 | KN 고유 개념 | 원 카운트가 아니라 단어 `w`가 나타나는 컨텍스트 수로 가중한 `P(w)`. |
| 텍스트의 엔트로피 | 기호당 정보량 | 컨텍스트가 주어졌을 때 다음 기호를 인코딩하는 데 필요한 평균 비트. Shannon의 1951년 추정치 — 100글자까지의 컨텍스트를 쓴 인쇄 영어 기준 0.6-1.3 비트/글자로, 어떤 모델도 존재하기 전에 측정됨. |

## 더 읽을거리

- [Shannon (1951). Prediction and Entropy of Printed English](https://www.princeton.edu/~wbialek/rome/refs/shannon_51.pdf) — 지금의 모든 언어 모델이 최적화하는 목표를 정의한 추측 게임 실험.
- [Jurafsky and Martin — Speech and Language Processing, 3장 (2026 초안)](https://web.stanford.edu/~jurafsky/slp3/3.pdf) — n-그램 LM과 스무딩의 정석적 정리.
- [Chen and Goodman (1998). An Empirical Study of Smoothing Techniques for Language Modeling](https://dash.harvard.edu/handle/1/25104739) — Kneser-Ney가 최고의 n-그램 스무더임을 확정한 논문.
- [Kneser and Ney (1995). Improved Backing-off for M-gram Language Modeling](https://ieeexplore.ieee.org/document/479394) — KN 원 논문.
- [KenLM](https://kheafield.com/code/kenlm/) — 빠른 프로덕션용 n-그램 LM. 2026년에도 지연 시간에 민감한 애플리케이션에서 사용 중.
