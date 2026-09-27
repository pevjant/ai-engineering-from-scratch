> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 다국어 NLP

> 모델 하나, 100개 넘는 언어, 그 대다수 언어에는 학습 데이터 0. 교차 언어 전이(cross-lingual transfer)는 2020년대의 실용적인 기적입니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 04(GloVe, FastText, 서브워드), 페이즈 5 · 11(기계 번역)
**시간:** 약 45분

## 문제 상황

영어에는 레이블 달린 예시가 수십억 개 있습니다. 우르두어는 수천 개. 마이틸어는 거의 없습니다. 전 세계를 상대하는 실전 NLP 시스템은 과제별 학습 데이터가 존재하지 않는 언어들의 긴 꼬리 위에서도 동작해야 합니다.

다국어 모델은 하나의 모델을 여러 언어에 걸쳐 동시에 학습시켜 이 문제를 풉니다. 공유된 표현 덕분에 모델은 고자원(high-resource) 언어에서 배운 능력을 저자원(low-resource) 언어로 전이할 수 있습니다. 영어 감성 분석으로 모델을 파인튜닝하면, 우르두어에 대해서도 놀랄 만큼 좋은 감성 예측을 별도 학습 없이 바로 냅니다. 이것이 제로샷 교차 언어 전이고, NLP가 세계로 출시되는 방식을 바꿔 놓았습니다.

이 레슨은 트레이드오프와 대표 모델들, 그리고 다국어 작업이 처음인 팀들이 자주 걸려 넘어지는 단 하나의 결정 — 전이를 위한 소스 언어 선택 — 을 다룹니다.

## 핵심 개념

![공유 다국어 임베딩 공간을 통한 교차 언어 전이](../assets/multilingual.svg)

**공유 어휘.** 다국어 모델은 모든 대상 언어의 텍스트로 학습한 SentencePiece 또는 WordPiece 토크나이저를 씁니다. 어휘가 공유되므로, 같은 서브워드 단위가 관련 언어들에서 같은 형태소를 대표합니다. 영어와 이탈리아어의 `anti-`는 같은 토큰을 받습니다.

**공유 표현.** 여러 언어에 걸쳐 마스크드 언어 모델링으로 사전학습된 트랜스포머는, 서로 다른 언어에서 의미가 비슷한 문장들이 비슷한 은닉 상태를 만든다는 것을 학습합니다. mBERT, XLM-R, NLLB 모두 이 성질을 보입니다. 영어 "cat"의 임베딩은 프랑스어 "chat"과 스페인어 "gato" 근처에 뭉치고, 문장 전체 임베딩도 마찬가지입니다.

**제로샷 전이.** 한 언어(보통 영어)의 레이블 데이터로 모델을 파인튜닝합니다. 추론 시에는 모델이 지원하는 다른 어떤 언어로도 실행합니다. 대상 언어 레이블이 필요 없습니다. 유형적으로 가까운 언어에서는 결과가 강하고, 먼 언어에서는 약합니다.

**퓨샷 파인튜닝.** 대상 언어 레이블 예시 100-500개를 더합니다. 분류 과제에서 영어 베이스라인의 95-98% 수준으로 정확도가 뛰어오릅니다. 다국어 NLP에서 가장 비용 대비 효과가 좋은 단 하나의 지렛대입니다.

## 모델들

| 모델 | 연도 | 커버리지 | 비고 |
|-------|------|----------|-------|
| mBERT | 2018 | 104개 언어 | Wikipedia로 학습. 최초의 실용적 다국어 LM. 저자원 언어에는 약함. |
| XLM-R | 2019 | 100개 언어 | CommonCrawl 학습(Wikipedia보다 훨씬 큼). 교차 언어 베이스라인 확립. Base 270M, Large 550M. |
| XLM-V | 2023 | 100개 언어 | 100만 토큰 어휘를 가진 XLM-R(vs 25만). 저자원 언어에서 더 좋음. |
| mT5 | 2020 | 101개 언어 | 다국어 생성용 T5 아키텍처. |
| NLLB-200 | 2022 | 200개 언어 | Meta의 번역 모델; 저자원 언어 55개 포함. |
| BLOOM | 2022 | 46개 언어 + 13개 프로그래밍 언어 | 다국어로 학습된 오픈 176B LLM. |
| Aya-23 | 2024 | 23개 언어 | Cohere의 다국어 LLM. 아랍어, 힌디어, 스와힐리어에서 강함. |

용도에 따라 고르세요. 분류는 상식적인 기본값인 XLM-R-base로 잘 해결됩니다. 생성 과제는 번역이냐 열린 생성이냐에 따라 mT5 또는 NLLB가 필요합니다. LLM 스타일 작업은 명시적인 다국어 프롬프팅과 함께 Aya-23이나 Claude와 어울립니다.

## 소스 언어 결정 (2026년 연구)

대부분의 팀은 파인튜닝 소스 언어의 기본값으로 영어를 고릅니다. 최근 연구(2026)에 따르면 이것은 자주 틀린 선택입니다.

언어 유사성이 원시 코퍼스 크기보다 전이 품질을 더 잘 예측합니다. 슬라브 계열 대상 언어에는 독일어나 러시아어가 영어를 자주 이기고, 인도 계열 대상 언어에는 힌디어가 영어를 자주 이깁니다. **qWALS** 유사도 지표(2026, World Atlas of Language Structures 특성 기반)가 이를 정량화합니다. **LANGRANK**(Lin et al., ACL 2019)는 별개의 더 이른 방법으로, 언어학적 유사성, 코퍼스 크기, 계통 관련성을 조합해 후보 소스 언어들의 순위를 매깁니다.

실용 규칙: 대상 언어와 유형적으로 가까운 고자원 친척 언어가 있다면, 먼저 그 언어로 파인튜닝해 보고 영어 파인튜닝과 비교하세요.

```figure
n5-crosslingual-bridge
```

## 만들어 보기

### 단계 1: 제로샷 교차 언어 분류

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tok = AutoTokenizer.from_pretrained("joeddav/xlm-roberta-large-xnli")
model = AutoModelForSequenceClassification.from_pretrained("joeddav/xlm-roberta-large-xnli")


def classify(text, candidate_labels, hypothesis_template="This text is about {}."):
    scores = {}
    for label in candidate_labels:
        hypothesis = hypothesis_template.format(label)
        inputs = tok(text, hypothesis, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = model(**inputs).logits[0]
        entail_score = torch.softmax(logits, dim=-1)[2].item()
        scores[label] = entail_score
    return dict(sorted(scores.items(), key=lambda x: -x[1]))


print(classify("I love this product!", ["positive", "negative", "neutral"]))
print(classify("मुझे यह उत्पाद पसंद है!", ["positive", "negative", "neutral"]))
print(classify("J'adore ce produit !", ["positive", "negative", "neutral"]))
```

모델 하나, 세 언어, 같은 API입니다. NLI 데이터로 학습한 XLM-R은 함의(entailment) 트릭을 통해 분류로 잘 전이됩니다.

### 단계 2: 다국어 임베딩 공간

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

pairs = [
    ("The cat is sleeping.", "Le chat dort."),
    ("The cat is sleeping.", "El gato está durmiendo."),
    ("The cat is sleeping.", "Die Katze schläft."),
    ("The cat is sleeping.", "The dog is barking."),
]

for eng, other in pairs:
    emb_eng = model.encode([eng], normalize_embeddings=True)[0]
    emb_other = model.encode([other], normalize_embeddings=True)[0]
    sim = float(np.dot(emb_eng, emb_other))
    print(f"  {eng!r} <-> {other!r}: cos={sim:.3f}")
```

번역문들은 임베딩 공간에서 가까이 떨어집니다. 다른 의미의 영어 문장은 더 멀리 떨어집니다. 교차 언어 검색, 클러스터링, 유사도가 동작하는 원리가 바로 이것입니다.

### 단계 3: 퓨샷 파인튜닝 전략

```python
from transformers import TrainingArguments, Trainer
from datasets import Dataset


def few_shot_finetune(base_model, base_tokenizer, examples):
    ds = Dataset.from_list(examples)

    def tokenize_fn(ex):
        out = base_tokenizer(ex["text"], truncation=True, max_length=128)
        out["labels"] = ex["label"]
        return out

    ds = ds.map(tokenize_fn)
    args = TrainingArguments(
        output_dir="out",
        per_device_train_batch_size=8,
        num_train_epochs=5,
        learning_rate=2e-5,
        save_strategy="no",
    )
    trainer = Trainer(model=base_model, args=args, train_dataset=ds)
    trainer.train()
    return base_model
```

대상 언어 예시 100-500개라면 `num_train_epochs=5`와 `learning_rate=2e-5`가 안전한 기본값입니다. 더 높은 학습률은 다국어 정렬(alignment)을 무너뜨려서 영어 전용 모델을 만들어 버립니다.

## 실제로 통하는 평가

- **언어별 보류(held-out) 셋 정확도.** 집계하지 말 것. 집계치는 긴 꼬리를 숨깁니다.
- **단일 언어 베이스라인과 비교.** 데이터가 충분한 언어에서는 밑바닥부터 학습한 단일 언어 모델이 다국어 모델을 이기기도 합니다. 직접 테스트하세요.
- **개체(entity) 수준 테스트.** 대상 언어의 고유명사. 다국어 모델은 라틴 문자에서 먼 문자 체계에 대해 토큰화가 약한 경우가 많습니다.
- **교차 언어 일관성.** 두 언어에서 같은 의미라면 같은 예측이 나와야 합니다. 그 간극을 측정하세요.

## 사용해 보기

2026년 스택:

| 과제 | 추천 |
|-----|-------------|
| 분류, 100개 언어 | 파인튜닝한 XLM-R-base (~270M) |
| 제로샷 텍스트 분류 | `joeddav/xlm-roberta-large-xnli` |
| 다국어 문장 임베딩 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| 번역, 200개 언어 | `facebook/nllb-200-distilled-600M` (레슨 11 참조) |
| 생성형 다국어 | Claude, GPT-4, Aya-23, mT5-XXL |
| 저자원 언어 NLP | XLM-V 또는 관련 고자원 언어의 도메인별 파인튜닝 |

성능이 중요하다면 항상 대상 언어 파인튜닝 비용을 예산에 넣으세요. 제로샷은 출발점이지 최종 답이 아닙니다.

### 토큰화 세금 (저자원 언어에서 무엇이 잘못되는가)

다국어 모델은 모든 언어에서 하나의 토크나이저를 공유합니다. 그 어휘는 영어, 프랑스어, 스페인어, 중국어, 독일어가 지배하는 코퍼스로 학습됐습니다. 지배 집합 밖의 언어에는 세 가지 세금이 조용히 겹쳐 부과됩니다:

- **생산성(fertility) 세금.** 저자원 언어 텍스트는 영어보다 단어당 훨씬 많은 토큰으로 쪼개집니다. 힌디어 문장은 같은 뜻의 영어 문장보다 3-5배의 토큰이 필요할 수 있습니다. 이 3-5배가 컨텍스트 윈도우, 학습 효율, 지연 시간을 잠식합니다.
- **변이 복원 세금.** 오타, 발음 구별 부호 변형, 유니코드 정규화 불일치, 대소문자 변화가 전부 임베딩 공간에서 차가운(무관한) 시퀀스가 됩니다. 원어민에게는 자명한 철자 대응 관계를 모델은 배울 수 없습니다.
- **용량 월세 세금.** 1번과 2번 세금이 컨텍스트 위치, 레이어 깊이, 임베딩 차원을 소모합니다. 실제 추론에 남는 것은 같은 모델에서 고자원 언어가 받는 몫보다 체계적으로 작습니다.

실전 증상: 모델이 힌디어로 정상적으로 학습되고, 손실 곡선은 멀쩡하고, 평가 퍼플렉시티도 그럴듯한데, 프로덕션 출력은 미묘하게 틀립니다. 문장 중간에 형태론이 무너지고, 희귀 굴절형은 복원되지 않습니다. **망가진 토크나이저는 데이터를 늘린다고 해결되지 않습니다.**

완화책: 대상 언어 커버리지가 좋은 토크나이저를 고르세요(XLM-V의 100만 토큰 어휘가 직접적인 처방); 학습 전에 보류 대상 텍스트로 토큰화 생산성을 확인하세요; 정말 긴 꼬리 문자 체계에는 바이트 수준 폴백(SentencePiece `byte_fallback=True`, GPT-2 스타일 바이트 수준 BPE)을 써서 OOV가 절대 생기지 않게 하세요.

## 출시하기

`outputs/skill-multilingual-picker.md`로 저장하세요:

```markdown
---
name: multilingual-picker
description: 다국어 NLP 과제를 위한 소스 언어, 대상 모델, 평가 계획 고르기.
version: 1.0.0
phase: 5
lesson: 18
tags: [nlp, multilingual, cross-lingual]
---

요구 사항(대상 언어, 과제 유형, 언어별 사용 가능한 레이블 데이터)이 주어지면 다음을 출력하세요:

1. 파인튜닝용 소스 언어. 기본값은 영어; 대상 언어와 유형적으로 가까운 고자원 언어가 있다면 LANGRANK 또는 qWALS 확인.
2. 베이스 모델. XLM-R(분류), mT5(생성), NLLB(번역), Aya-23(생성형 LLM).
3. 퓨샷 예산. 대상 언어 예시 100-500개부터 시작(가능하다면). 레이블링이 불가능할 때만 제로샷.
4. 평가 계획. 언어별 정확도(집계 아님), 교차 언어 일관성, 비라틴 문자 체계에서의 개체 수준 F1.

언어별 평가 없이 다국어 모델을 출시하는 안은 받아들이지 마세요 — 집계 지표는 긴 꼬리의 실패를 숨깁니다. 토큰화 커버리지가 낮은 문자 체계(암하라어, 티그리냐어, 많은 아프리카 언어)는 바이트 폴백이 있는 모델(SentencePiece에 byte_fallback=True, 또는 GPT-2 같은 바이트 수준 토크나이저)이 필요하다고 표시하세요.
```

## 연습 문제

1. **쉬움.** 영어, 프랑스어, 힌디어, 아랍어 각각 10문장으로 제로샷 분류 파이프라인을 돌려 보세요. 언어별 정확도를 보고하세요. 프랑스어는 강하고, 힌디어는 나쁘지 않고, 아랍어는 들쑥날쑥한 걸 볼 수 있을 겁니다.
2. **중간.** `paraphrase-multilingual-MiniLM-L12-v2`로 작은 혼합 언어 코퍼스 위의 교차 언어 리트리버를 만드세요. 영어로 질의하고, 어떤 언어의 문서든 검색합니다. Recall@5를 측정하세요.
3. **어려움.** 힌디어 분류 과제에서 영어 소스 파인튜닝과 힌디어 소스 파인튜닝을 비교하세요. 두 체제 모두 대상 언어 예시 500개로 퓨샷 파인튜닝합니다. 어느 소스가 더 나은 힌디어 정확도를 내는지, 얼마나 차이 나는지 보고하세요. 이것이 축소판 LANGRANK 명제입니다.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| 다국어 모델 | 모델 하나, 언어 여러 개 | 언어들에 걸친 공유 어휘와 공유 파라미터. |
| 교차 언어 전이 | 한 언어로 학습, 다른 언어로 실행 | 소스로 파인튜닝하고, 대상 언어 레이블 없이 대상에서 평가. |
| 제로샷 | 대상 언어 레이블 없음 | 대상 언어 파인튜닝 없이 전이. |
| 퓨샷 | 적은 대상 언어 레이블 | 파인튜닝에 쓰는 대상 언어 예시 100-500개. |
| mBERT | 최초의 다국어 LM | Wikipedia로 사전학습한 104개 언어 BERT. |
| XLM-R | 표준 교차 언어 베이스라인 | CommonCrawl로 사전학습한 100개 언어 RoBERTa. |
| NLLB | Meta의 200개 언어 기계번역 | No Language Left Behind. 저자원 언어 55개 포함. |

## 더 읽을거리

- [Conneau et al. (2019). Unsupervised Cross-lingual Representation Learning at Scale](https://arxiv.org/abs/1911.02116) — XLM-R 원 논문.
- [Pires, Schlinger, Garrette (2019). How Multilingual is Multilingual BERT?](https://arxiv.org/abs/1906.01502) — 교차 언어 전이 연구 계열을 연 분석 논문.
- [Costa-jussà et al. (2022). No Language Left Behind](https://arxiv.org/abs/2207.04672) — NLLB-200 논문.
- [Üstün et al. (2024). Aya Model: An Instruction Finetuned Open-Access Multilingual Language Model](https://arxiv.org/abs/2402.07827) — Aya, Cohere의 다국어 LLM.
- [Language Similarity Predicts Cross-Lingual Transfer Learning Performance (2026)](https://www.mdpi.com/2504-4990/8/3/65) — qWALS / LANGRANK 소스 언어 논문.
