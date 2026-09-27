> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 서브워드 토큰화 — BPE, WordPiece, Unigram, SentencePiece

> 단어 단위 토크나이저는 처음 보는 단어에서 목이 졸립니다. 문자 단위 토크나이저는 시퀀스 길이가 폭발합니다. 서브워드 토크나이저는 그 사이의 타협점을 잡습니다. 지금의 모든 LLM이 하나를 실고 나옵니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 01(텍스트 처리), 페이즈 5 · 04(GloVe / FastText / 서브워드)
**시간:** 약 60분

## 문제 상황

여러분의 어휘에 단어 50,000개가 있다고 합시다. 사용자가 "untokenizable"을 입력합니다. 토크나이저는 `[UNK]`를 돌려주고, 모델은 이제 그 단어에 대한 신호를 전혀 갖지 못합니다. 더 나쁜 것은: 코퍼스의 상위 90퍼센타일 문서에는 희귀 단어가 40개쯤 있다는 겁니다. 즉 문서마다 40조각의 정보가 버려진다는 뜻입니다.

서브워드 토큰화가 이걸 해결합니다. 흔한 단어는 토큰 하나로 남습니다. 희귀 단어는 의미 있는 조각으로 분해됩니다: `untokenizable` → `un`, `token`, `izable`. 어떤 문자열이든 결국 바이트의 시퀀스이므로 학습 데이터가 모든 것을 커버합니다.

2026년의 모든 프론티어 LLM은 세 가지 알고리즘(BPE, Unigram, WordPiece) 중 하나와 세 가지 라이브러리(tiktoken, SentencePiece, HF Tokenizers) 중 하나의 조합으로 출시됩니다. 하나를 고르지 않고는 언어 모델을 출시할 수 없습니다.

## 핵심 개념

![BPE vs Unigram vs WordPiece, 글자 단위 비교](../assets/subword-tokenization.svg)

**BPE(Byte-Pair Encoding).** 문자 수준 어휘에서 출발합니다. 인접한 모든 쌍을 세고, 가장 빈번한 쌍을 새 토큰으로 병합합니다. 목표 어휘 크기에 도달할 때까지 반복합니다. 지배적인 알고리즘입니다: GPT-2/3/4, Llama, Gemma, Qwen2, Mistral.

**바이트 수준 BPE.** 같은 알고리즘이지만 유니코드 문자 대신 날것의 바이트(기본 토큰 256개) 위에서 돌립니다. `[UNK]` 토큰이 0개임을 보장합니다 — 어떤 바이트 시퀀스든 인코딩되니까요. GPT-2는 50,257개 토큰을 씁니다(바이트 256 + 병합 50,000 + 특수 1).

**Unigram.** 아주 큰 어휘에서 출발합니다. 각 토큰에 유니그램 확률을 부여하고, 제거했을 때 코퍼스 로그 가능도가 가장 조금 늘어나는 토큰부터 반복적으로 잘라 냅니다. 추론이 확률적입니다: 토큰화 결과를 샘플링할 수 있어(서브워드 정규화를 통한 데이터 증강에 유용) T5, mBART, ALBERT, XLNet, Gemma가 사용합니다.

**WordPiece.** 원 빈도 대신 학습 코퍼스의 가능도를 최대화하는 쌍을 병합합니다. BERT, DistilBERT, ELECTRA가 사용합니다.

**SentencePiece vs tiktoken.** SentencePiece는 날것의 유니코드 텍스트 위에서 직접 어휘를 *학습*하는 라이브러리(BPE 또는 Unigram)로, 공백을 `▁`로 인코딩합니다. tiktoken은 미리 만들어진 어휘에 대한 OpenAI의 빠른 *인코더*로, 학습은 하지 않습니다.

경험 법칙:

- **새 어휘를 학습할 때:** SentencePiece(다국어, 사전 토큰화 불필요) 또는 HF Tokenizers.
- **GPT 어휘에 대한 빠른 추론:** tiktoken (cl100k_base, o200k_base).
- **둘 다:** HF Tokenizers — 하나의 라이브러리로 학습 + 서빙.

```figure
bpe-merge
```

## 만들어 보기

### 단계 1: 밑바닥부터 BPE 만들기

`code/main.py`를 보세요. 루프는 이렇습니다:

```python
def train_bpe(corpus, num_merges):
    vocab = {tuple(word) + ("</w>",): count for word, count in corpus.items()}
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for symbols, freq in vocab.items():
            for a, b in zip(symbols, symbols[1:]):
                pairs[(a, b)] += freq
        if not pairs:
            break
        best = pairs.most_common(1)[0][0]
        merges.append(best)
        vocab = apply_merge(vocab, best)
    return merges
```

알고리즘이 담고 있는 사실 세 가지입니다. `</w>`는 단어의 끝을 표시해서 "low"(접미 쪽)와 "lower"(접두 쪽)가 서로 구분되게 합니다. 빈도 가중치 덕분에 빈도 높은 쌍이 초반에 이깁니다. 병합 목록은 순서가 있는 리스트이고, 추론은 학습 순서대로 병합을 적용합니다.

### 단계 2: 학습된 병합으로 인코딩하기

```python
def encode_bpe(word, merges):
    symbols = list(word) + ["</w>"]
    for a, b in merges:
        i = 0
        while i < len(symbols) - 1:
            if symbols[i] == a and symbols[i + 1] == b:
                symbols = symbols[:i] + [a + b] + symbols[i + 2:]
            else:
                i += 1
    return symbols
```

순진한 O(n·|merges|)입니다. 프로덕션 구현(tiktoken, HF Tokenizers)은 병합 순위 룩업과 우선순위 큐를 써서 거의 선형 시간에 실행됩니다.

### 단계 3: 실전 SentencePiece

```python
import sentencepiece as spm

spm.SentencePieceTrainer.train(
    input="corpus.txt",
    model_prefix="my_tokenizer",
    vocab_size=8000,
    model_type="bpe",          # 또는 "unigram"
    character_coverage=0.9995, # CJK에서는 낮춘다 (영어 0.9995, 일본어 0.995 등)
    normalization_rule_name="nmt_nfkc",
)

sp = spm.SentencePieceProcessor(model_file="my_tokenizer.model")
print(sp.encode("untokenizable", out_type=str))
# ['▁un', 'token', 'izable']
```

주목할 점: 사전 토큰화가 필요 없고, 공백이 `▁`로 인코딩되며, `character_coverage`는 희귀 문자를 얼마나 공격적으로 보존할지 아니면 `<unk>`로 매핑할지를 조절합니다.

### 단계 4: OpenAI 호환 어휘용 tiktoken

```python
import tiktoken
enc = tiktoken.get_encoding("o200k_base")
print(enc.encode("untokenizable"))        # [127340, 101028]
print(len(enc.encode("Hello, world!")))   # 4
```

인코딩 전용입니다. 빠릅니다(Rust 백엔드). 바이트 수 계산, 비용 추정, 컨텍스트 윈도우 예산 편성에서 GPT-4/5 토큰화와 정확히 일치합니다.

## 2026년에도 출시되고 있는 함정들

- **토크나이저 드리프트.** 어휘 A로 학습하고 어휘 B로 배포합니다. 토큰 ID가 달라지고 모델은 엉터리를 냅니다. CI에서 `tokenizer.json` 해시를 확인하세요.
- **공백 모호성.** BPE에서 "hello"와 " hello"는 서로 다른 토큰이 됩니다. `add_special_tokens`와 `add_prefix_space`는 항상 명시적으로 지정하세요.
- **다국어 저학습(undertraining).** 영어 중심 코퍼스는 비라틴 문자를 5-10배 더 많은 토큰으로 쪼개는 어휘를 만듭니다. 같은 프롬프트가 GPT-3.5의 일본어/아랍어에서는 5-10배 비쌌습니다. o200k_base가 이 문제를 부분적으로 고쳤습니다.
- **이모지 분할.** 이모지 하나가 토큰 5개를 잡아먹을 수 있습니다. 컨텍스트 예산을 잡을 때 이모지 처리를 확인하세요.

## 사용해 보기

2026년 스택:

| 상황 | 선택 |
|-----------|------|
| 단일 언어 모델을 밑바닥부터 학습 | HF Tokenizers (BPE) |
| 다국어 모델 학습 | SentencePiece (Unigram, `character_coverage=0.9995`) |
| OpenAI 호환 API 서빙 | tiktoken (GPT-4+는 `o200k_base`) |
| 도메인 전용 어휘(코드, 수학, 단백질) | 도메인 코퍼스로 커스텀 BPE 학습 후 베이스 어휘와 병합 |
| 엣지 추론, 소형 모델 | Unigram (작은 어휘에서 더 잘 동작) |

어휘 크기는 상수가 아니라 확장 결정입니다. 대략적인 경험칙: 1B 파라미터 미만은 32k, 1-10B는 5-10만, 다국어/프론티어는 20만 이상.

## 출시하기

`outputs/skill-bpe-vs-wordpiece.md`로 저장하세요:

```markdown
---
name: tokenizer-picker
description: 주어진 코퍼스와 배포 대상에 맞는 토크나이저 알고리즘, 어휘 크기, 라이브러리 고르기.
version: 1.0.0
phase: 5
lesson: 19
tags: [nlp, tokenization]
---

코퍼스(크기, 언어, 도메인)와 배포 대상(밑바닥부터 학습 / 파인튜닝 / API 호환 추론)이 주어지면 다음을 출력하세요:

1. 알고리즘. BPE, Unigram, 또는 WordPiece. 한 문장 근거.
2. 라이브러리. SentencePiece, HF Tokenizers, 또는 tiktoken. 근거.
3. 어휘 크기. 가장 가까운 1k 단위로 반올림. 모델 크기와 언어 커버리지에 근거를 댈 것.
4. 커버리지 설정. `character_coverage`, `byte_fallback`, 특수 토큰 목록.
5. 검증 계획. 보류(held-out) 셋의 단어당 평균 토큰 수, OOV 비율, 압축 비율, 왕복 디코딩 일치 여부.

희귀 문자 체계 콘텐츠가 섞인 코퍼스에는 character-coverage 0.995 미만 토크나이저를 학습하지 마세요. CI에 고정된 `tokenizer.json` 해시 검사 없이 어휘를 출시하지 마세요. 16k 미만 어휘의 단일 언어 토크나이저는 스펙 미달일 가능성이 높다고 표시하세요.
```

## 연습 문제

1. **쉬움.** `code/main.py`의 작은 코퍼스로 병합 500개짜리 BPE를 학습시키세요. 보류해 둔 단어 세 개를 인코딩해 보세요. 정확히 1토큰이 나온 단어와 1토큰 초과가 나온 단어는 각각 몇 개였나요?
2. **중간.** 영어 Wikipedia 문장 100개에서 `cl100k_base`, `o200k_base`, 그리고 어휘 32k로 직접 학습한 SentencePiece BPE의 토큰 수를 비교하세요. 각각의 압축 비율을 보고하세요.
3. **어려움.** 같은 코퍼스로 BPE, Unigram, WordPiece를 학습시키세요. 각각을 작은 감성 분류기에 적용했을 때의 다운스트림 정확도를 측정하세요. 선택이 F1 기준 1포인트 이상을 움직이나요?

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| BPE | Byte-Pair Encoding | 목표 어휘 크기에 도달할 때까지 가장 빈번한 문자 쌍을 탐욕적으로 병합. |
| 바이트 수준 BPE | 알 수 없는 토큰이 영원히 없음 | 날것의 256바이트 위의 BPE; GPT-2 / Llama가 사용. |
| Unigram | 확률적 토크나이저 | 큰 후보 집합에서 로그 가능도로 잘라냄; T5, Gemma가 사용. |
| SentencePiece | 공백 처리하는 그것 | 날것 텍스트로 BPE/Unigram을 학습하는 라이브러리; 공백을 `▁`로 인코딩. |
| tiktoken | 빠른 그것 | 미리 만들어진 어휘를 위한 OpenAI의 Rust 기반 BPE 인코더. 학습은 없음. |
| 병합 목록 | 마법의 숫자들 | `(a, b) → ab` 병합의 순서 있는 목록; 추론은 순서대로 적용. |
| 문자 커버리지 | 얼마나 희귀해야 너무 희귀한가? | 토크나이저가 커버해야 하는 학습 코퍼스 문자의 비율; 보통 ~0.9995. |

## 더 읽을거리

- [Sennrich, Haddow, Birch (2015). Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — BPE 원 논문.
- [Kudo (2018). Subword Regularization with Unigram Language Model](https://arxiv.org/abs/1804.10959) — Unigram 원 논문.
- [Kudo, Richardson (2018). SentencePiece: A simple and language independent subword tokenizer](https://arxiv.org/abs/1808.06226) — 그 라이브러리.
- [Hugging Face — Summary of the tokenizers](https://huggingface.co/docs/transformers/tokenizer_summary) — 간결한 레퍼런스.
- [OpenAI tiktoken repo](https://github.com/openai/tiktoken) — 쿡북 + 인코딩 목록.
