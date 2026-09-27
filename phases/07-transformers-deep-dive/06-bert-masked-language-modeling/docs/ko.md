# BERT — 마스크드 언어 모델링

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> GPT는 다음 단어를 예측합니다. BERT는 빠진 단어를 예측합니다. 한 문장 차이 — 그런데 그 차이가 임베딩을 쓰는 거의 모든 분야를 5년 동안 지배했습니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 7 · 05 (완전한 트랜스포머), 페이즈 5 · 02 (텍스트 표현)
**시간:** 약 45분

## 문제 상황

2018년에는 모든 NLP 과제 — 감성 분석, 개체명 인식, 질의응답, 함의 판별 — 이 자기 레이블 데이터로 모델을 처음부터 새로 학습시켰습니다. 파인튜닝할 수 있는 사전 학습된 "영어 이해" 체크포인트 같은 건 없었습니다. ELMo(2018)가 양방향 LSTM으로 맥락을 반영한 임베딩을 사전 학습할 수 있음을 보여 줬지만, 도움이 됐을 뿐 일반화되지는 않았습니다.

BERT(Devlin et al. 2018)는 이렇게 물었습니다: 트랜스포머 인코더를 인터넷의 모든 문장으로 학습시키면서, 양쪽 문맥으로부터 빠진 단어를 맞히도록 강제하면 어떨까? 그런 다음 다운스트림 과제에는 헤드 하나만 파인튜닝하면 됩니다. 파라미터 효율은 혁명이었습니다.

그 결과: 18개월 안에 BERT와 그 변형들(RoBERTa, ALBERT, ELECTRA)이 존재하는 모든 NLP 리더보드를 지배했습니다. 2020년이면 세상의 모든 검색 엔진, 콘텐츠 모더레이션 파이프라인, 의미 기반 검색 시스템 안에 BERT가 들어 있었습니다.

2026년에도 인코더 전용 모델은 분류, 검색, 구조화된 추출에는 여전히 옳은 도구입니다 — 디코더보다 토큰당 5-10배 빠르게 돌고, 그 임베딩은 모든 현대 검색 스택의 등뼈입니다. ModernBERT(2024년 12월)는 Flash Attention + RoPE + GeGLU로 이 아키텍처를 8K 컨텍스트까지 밀어 올렸습니다.

## 핵심 개념

![마스크드 언어 모델링: 토큰을 골라 가리고, 원래 토큰을 예측한다](../assets/bert-mlm.svg)

### 학습 신호

문장을 하나 가져옵니다: `the quick brown fox jumps over the lazy dog`.

토큰의 15%를 무작위로 가립니다:

```
input:  the [MASK] brown fox jumps [MASK] the lazy dog
target: the  quick brown fox jumps  over  the lazy dog
```

가려진 위치의 원래 토큰을 예측하도록 모델을 학습시킵니다. 인코더는 양방향이므로 위치 1의 `[MASK]`를 예측할 때 위치 2 이후의 `brown fox jumps`를 쓸 수 있습니다. 바로 GPT가 못 하는 일입니다.

### BERT의 마스크 규칙

예측 대상으로 고른 토큰 15% 중에서:

- 80%는 `[MASK]`로 교체합니다.
- 10%는 무작위 토큰으로 교체합니다.
- 10%는 그대로 둡니다.

왜 항상 `[MASK]`로 가리지 않을까요? 추론 시점에는 `[MASK]`가 절대 등장하지 않기 때문입니다. 가려진 위치의 100%가 `[MASK]`라고 기대하도록 학습시키면 사전 학습과 파인튜닝 사이에 분포가 어긋납니다. 10% 무작위 + 10% 그대로가 모델을 정직하게 유지해 줍니다.

### 다음 문장 예측(NSP) — 그리고 버려진 이유

원조 BERT는 NSP도 학습했습니다: 두 문장 A와 B가 주어지면 B가 A 뒤에 오는지 맞히는 과제입니다. RoBERTa(2019)가 이를 제거 실험(ablation)해 보니 NSP는 도움이 아니라 해가 됐습니다. 현대 인코더는 건너뜁니다.

### 2026년에 바뀐 것: ModernBERT

2024년 ModernBERT 논문은 2026년의 부품으로 블록을 새로 지었습니다:

| 구성 요소 | 원조 BERT (2018) | ModernBERT (2024) |
|-----------|----------------------|-------------------|
| 위치 | 학습형 절대 | RoPE |
| 활성화 | GELU | GeGLU |
| 정규화 | LayerNorm | Pre-norm RMSNorm |
| 어텐션 | 풀 밀집 | 국소(128) + 전역 교대 |
| 컨텍스트 길이 | 512 | 8192 |
| 토크나이저 | WordPiece | BPE |

그리고 2018년 스택과 달리 Flash Attention 네이티브입니다. 시퀀스 길이 8K에서 추론이 DeBERTa-v3보다 2-3배 빠르면서 GLUE 점수는 더 좋습니다.

### 2026년에도 여전히 인코더를 고르는 사용 사례

| 과제 | 인코더가 디코더를 이기는 이유 |
|------|---------------------------|
| 검색 / 의미 검색 임베딩 | 양방향 컨텍스트 = 토큰당 더 나은 임베딩 품질 |
| 분류 (감성, 의도, 유해성) | 순전파 한 번; 생성 오버헤드 없음 |
| NER / 토큰 레이블링 | 위치별 출력, 기본적으로 양방향 |
| 제로샷 함의 판별 (NLI) | 인코더 위에 분류 헤드 |
| RAG용 리랭커(reranker) | 크로스 인코더 스코어링, LLM 리랭커보다 10배 빠름 |

```figure
transformer-residual
```

## 만들어 보기

### 단계 1: 마스킹 로직

`code/main.py`를 보세요. `create_mlm_batch` 함수는 토큰 ID 목록, 어휘 크기, 마스크 확률을 받습니다. 입력 ID(마스크 적용)와 레이블(가려진 위치에만 있고 나머지는 -100 — PyTorch의 무시 인덱스 관례)을 돌려줍니다.

```python
def create_mlm_batch(tokens, vocab_size, mask_prob=0.15, rng=None):
    input_ids = list(tokens)
    labels = [-100] * len(tokens)
    for i, t in enumerate(tokens):
        if rng.random() < mask_prob:
            labels[i] = t
            r = rng.random()
            if r < 0.8:
                input_ids[i] = MASK_ID
            elif r < 0.9:
                input_ids[i] = rng.randrange(vocab_size)
            # else: keep original
    return input_ids, labels
```

### 단계 2: 아주 작은 코퍼스에서 MLM 예측 돌리기

어휘 20개 단어, 200개 문장으로 2층 인코더 + MLM 헤드를 학습합니다. 기울기는 없습니다 — 순전파 온전성 검사만 합니다. 제대로 학습하려면 PyTorch가 필요합니다.

### 단계 3: 마스크 유형 비교하기

세 갈래 규칙이 `[MASK]` 없이도 모델을 쓸 수 있게 유지하는 모습을 보여 줍니다. 가리지 않은 문장과 가린 문장 각각에 예측을 수행합니다. 둘 다 그럴듯한 토큰 분포를 내놓아야 합니다. 모델이 학습 중 두 패턴을 모두 봤기 때문입니다.

### 단계 4: 헤드 파인튜닝

MLM 헤드를 장난감 감성 데이터셋용 분류 헤드로 교체합니다. 학습되는 건 헤드뿐입니다. 인코더는 얼려 둡니다. 모든 BERT 응용이 따르는 패턴입니다.

## 활용하기

```python
from transformers import AutoModel, AutoTokenizer

tok = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
model = AutoModel.from_pretrained("answerdotai/ModernBERT-base")

text = "Attention is all you need."
inputs = tok(text, return_tensors="pt")
out = model(**inputs).last_hidden_state   # (1, N, 768)
```

**임베딩 모델은 파인튜닝된 BERT입니다.** `all-MiniLM-L6-v2` 같은 `sentence-transformers` 모델은 대조 손실(contrastive loss)로 학습된 BERT입니다. 인코더는 같고, 손실 함수만 바뀐 겁니다.

**크로스 인코더 리랭커도 파인튜닝된 BERT입니다.** `[CLS] query [SEP] doc [SEP]`에 대한 쌍 분류입니다. 쿼리와 문서 사이의 양방향 어텐션이야말로 크로스 인코더가 바이인코더(biencoder)보다 품질에서 우위를 갖는 이유입니다.

**2026년에 BERT를 고르지 말아야 할 때.** 생성이 필요한 모든 것. 인코더에는 토큰을 자기회귀적으로 만들어 내는 말이 되는 방법이 없습니다. 그리고 10억 파라미터 미만에서 작은 디코더가 더 유연하게 같은 품질을 낼 수 있는 영역도 있습니다(Phi-3-Mini, Qwen2-1.5B).

## 출시하기

`outputs/skill-bert-finetuner.md`를 보세요. 이 스킬은 새로운 분류 또는 추출 과제에 대해 BERT 파인튜닝(백본 선택, 헤드 명세, 데이터, 평가, 중단 조건)의 범위를 잡아 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 1만 개 토큰에 걸친 마스크 분포를 출력합니다. 약 15%가 선택되고, 그중 약 80%가 `[MASK]`가 되는지 확인합니다.
2. **보통.** 단어 단위 마스킹(whole-word masking)을 구현합니다. 한 단어가 서브워드로 분할됐다면 서브워드 전부를 함께 가리거나 아예 가리지 않습니다. 500문장 코퍼스에서 MLM 정확도가 개선되는지 측정합니다.
3. **어려움.** 공개 데이터셋의 1만 문장으로 아주 작은(2층, d=64) BERT를 학습합니다. SST-2 감성 분석용으로 `[CLS]` 토큰을 파인튜닝합니다. 같은 파라미터 수의 디코더 전용 베이스라인과 비교해 보세요 — 어느 쪽이 이기나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| MLM | "마스크드 언어 모델링" | 학습 신호: 토큰의 15%를 무작위로 `[MASK]`로 바꾸고 원래 토큰을 예측한다. |
| 양방향 (Bidirectional) | "양쪽을 다 본다" | 인코더 어텐션에는 인과 마스크가 없다 — 모든 위치가 모든 위치를 본다. |
| `[CLS]` | "풀러(pooler) 토큰" | 모든 시퀀스 앞에 붙는 특수 토큰; 마지막 임베딩이 문장 수준 표현으로 쓰인다. |
| `[SEP]` | "세그먼트 구분자" | 쌍으로 주어지는 시퀀스(예: 쿼리/문서, 문장 A/B)를 나눈다. |
| NSP | "다음 문장 예측" | BERT의 두 번째 사전 학습 과제; RoBERTa가 무용을 입증해 2019년 이후 사라졌다. |
| 파인튜닝 | "과제에 맞게 조정" | 인코더는 대체로 얹혀 두고(얼려 두고), 그 위의 작은 헤드를 다운스트림 과제로 학습한다. |
| 크로스 인코더 | "리랭커" | 쿼리와 문서를 모두 입력으로 받고 관련 점수 하나를 내놓는 BERT. |
| ModernBERT | "2024년 리프레시" | RoPE, RMSNorm, GeGLU, 국소/전역 교대 어텐션, 8K 컨텍스트로 다시 지은 인코더. |

## 더 읽을거리

- [Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805) — 원조 논문.
- [Liu et al. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach](https://arxiv.org/abs/1907.11692) — BERT를 제대로 학습시키는 법; NSP를 폐기.
- [Clark et al. (2020). ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators](https://arxiv.org/abs/2003.10555) — 같은 연산량에서 교체 토큰 탐지가 MLM을 이긴다.
- [Warner et al. (2024). Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder](https://arxiv.org/abs/2412.13663) — ModernBERT 논문.
- [HuggingFace `modeling_bert.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/bert/modeling_bert.py) — 표준 인코더 참조 구현.
