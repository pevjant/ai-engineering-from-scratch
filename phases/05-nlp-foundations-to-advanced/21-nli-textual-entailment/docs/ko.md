> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 자연어 추론 — 텍스트 함의

> "t가 h를 함의한다"는 것은 t를 읽은 사람이라면 h가 참이라고 결론 내릴 것이라는 뜻입니다. NLI는 함의(entailment) / 모순(contradiction) / 중립(neutral)을 예측하는 과제입니다. 겉보기엔 지루하지만, 프로덕션(운영 환경)에서는 기둥 역할을 합니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 05(감성 분석), 페이즈 5 · 13(질의응답)
**시간:** 약 60분

## 문제 상황

요약기를 만들었습니다. 요약이 나왔습니다. 이 요약에 환각이 없다는 걸 어떻게 아나요?

챗봇을 만들었습니다. "네"라고 답했습니다. 이 답이 검색된 구절에 근거가 있다는 걸 어떻게 아나요?

뉴스 기사 10,000개를 주제별로 분류해야 합니다. 학습 레이블은 없습니다. 기존 모델을 재활용할 수 있을까요?

세 문제 모두 자연어 추론(NLI)으로 환원됩니다. NLI는 이렇게 묻습니다: 전제(premise) `t`와 가설(hypothesis) `h`가 주어졌을 때, `h`는 `t`에 의해 함의되는가, 모순되는가, 아니면 중립(무관한가)?

- **환각 검사:** `t` = 원본 문서, `h` = 요약의 주장. 함의가 아니면 = 환각.
- **근거 있는 QA:** `t` = 검색된 구절, `h` = 생성된 답변. 함의가 아니면 = 지어낸 것.
- **제로샷 분류:** `t` = 문서, `h` = 언어화된 레이블("이것은 스포츠에 관한 것이다"). 함의면 = 예측된 레이블.

과제 하나, 프로덕션 용도 셋. 모든 RAG 평가 프레임워크가 내부에 NLI 모델을 싣고 나오는 이유입니다.

## 핵심 개념

![NLI: 전제 vs 가설의 3-웨이 분류](../assets/nli.svg)

**세 레이블.**

- **함의(entailment).** `t` → `h`. "The cat is on the mat"은 "There is a cat"을 함의합니다.
- **모순(contradiction).** `t` → ¬`h`. "The cat is on the mat"은 "There is no cat"과 모순됩니다.
- **중립(neutral).** 어느 쪽 추론도 불가. "The cat is on the mat"은 "The cat is hungry"에 대해 중립입니다.

**논리적 함의가 아닙니다.** NLI는 *자연*어 추론입니다 — 엄격한 논리가 아니라 전형적인 사람 독자가 추론할 것입니다. "John walked his dog"은 NLI에서 "John has a dog"을 함의하지만, 엄격한 1차 논리는 소유를 공리화해야만 그 추론을 받아들일 겁니다.

**데이터셋.**

- **SNLI** (2015). 57만 쌍의 사람이 주석 달은 데이터, 이미지 캡션을 전제로 사용. 좁은 도메인.
- **MultiNLI** (2017). 10개 장르에 걸친 43만 3천 쌍. 2026년의 표준 학습 코퍼스.
- **ANLI** (2019). 적대적 NLI. 사람들이 기존 모델을 깨뜨리도록 특별히 설계한 예시를 작성했습니다. 더 어렵습니다.
- **DocNLI, ConTRoL** (2020-21). 문서 길이의 전제. 다중 홉(multi-hop)과 장거리 추론을 시험합니다.

**아키텍처.** 트랜스포머 인코더(BERT, RoBERTa, DeBERTa)가 `[CLS] premise [SEP] hypothesis [SEP]`를 읽습니다. `[CLS]` 표현이 3-웨이 소프트맥스로 들어갑니다. MNLI로 학습하고, 보류(held-out) 벤치마크에서 평가하면, 분포 내 쌍에서 90% 이상의 정확도를 얻습니다.

**NLI를 통한 제로샷.** 문서와 후보 레이블이 주어지면, 각 레이블을 가설로 바꿉니다("This text is about sports"). 각각의 함의 확률을 계산하고 최댓값을 고릅니다. Hugging Face의 `zero-shot-classification` 파이프라인 뒤에 있는 메커니즘이 바로 이것입니다.

```figure
nli-router
```

## 만들어 보기

### 단계 1: 사전학습된 NLI 모델 돌리기

```python
from transformers import pipeline

nli = pipeline("text-classification",
               model="facebook/bart-large-mnli",
               top_k=None)  # 모든 레이블 반환; 폐기된 return_all_scores=True를 대체

premise = "The cat is sleeping on the couch."
hypothesis = "There is a cat in the room."

result = nli({"text": premise, "text_pair": hypothesis})[0]
print(result)
# [{'label': 'entailment', 'score': 0.97},
#  {'label': 'neutral', 'score': 0.02},
#  {'label': 'contradiction', 'score': 0.01}]
```

프로덕션 NLI에는 `facebook/bart-large-mnli`와 `microsoft/deberta-v3-large-mnli`가 오픈 기본값입니다. DeBERTa-v3가 리더보드 정점입니다.

### 단계 2: 제로샷 분류

```python
zs = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

text = "The stock market rallied after the central bank cut interest rates."
labels = ["finance", "sports", "politics", "technology"]

result = zs(text, candidate_labels=labels)
print(result)
# {'labels': ['finance', 'politics', 'technology', 'sports'],
#  'scores': [0.92, 0.05, 0.02, 0.01]}
```

템플릿은 기본값이 "This example is about {label}."입니다. `hypothesis_template`으로 바꿀 수 있습니다. 학습 데이터가 필요 없고, 파인튜닝도 없고, 바로 동작합니다.

### 단계 3: RAG 충실도(faithfulness) 검사

```python
def is_faithful(answer, context, threshold=0.5):
    result = nli({"text": context, "text_pair": answer})[0]
    entail = next(s for s in result if s["label"] == "entailment")
    return entail["score"] > threshold
```

RAGAS 충실도의 핵심입니다. 생성된 답변을 원자적 주장(atomic claims)으로 쪼개고, 각 주장을 검색된 컨텍스트와 대조하고, 함의되는 비율을 보고합니다.

### 단계 4: 손수 만드는 NLI 분류기 (개념용)

표준 라이브러리만 쓰는 장난감은 `code/main.py`를 보세요: 전제와 가설을 어휘 겹침 + 부정 탐지로 비교합니다. 트랜스포머 모델과 경쟁할 수준은 아니지만 과제의 형태를 보여 줍니다: 텍스트 둘이 들어가고, 3-웨이 레이블이 나오고, 손실은 `{entail, contradict, neutral}` 위의 크로스 엔트로피입니다.

## 함정들

- **가설만으로 치는 지름길.** 모델은 가설만 보고도 SNLI에서 약 60%를 맞힐 수 있습니다. "not", "nobody", "never"가 모순과 상관되기 때문입니다. 레이블 누수를 탐지하는 강력한 베이스라인입니다.
- **어휘 겹침 휴리스틱.** 부분수열 휴리스틱("모든 부분수열은 함의된다")은 SNLI는 통과하지만 HANS/ANLI에서 무너집니다. 적대적 벤치마크를 쓰세요.
- **문서 길이에서의 성능 저하.** 단일 문장 NLI 모델은 문서 길이 전제에서 F1이 20 이상 떨어집니다. 긴 컨텍스트에는 DocNLI로 학습된 모델을 쓰세요.
- **제로샷 템플릿 민감도.** "This example is about {label}" vs "{label}" vs "The topic is {label}" 사이에서 정확도가 10포인트 이상 요동칠 수 있습니다. 템플릿을 튜닝하세요.
- **도메인 불일치.** MNLI는 일반 영어로 학습됩니다. 법률, 의료, 과학 텍스트에는 도메인 전용 NLI 모델(예: SciNLI, MedNLI)이 필요합니다.

## 사용해 보기

2026년 스택:

| 사용 사례 | 모델 |
|---------|-------|
| 범용 NLI | `microsoft/deberta-v3-large-mnli` |
| 빠른 / 엣지 | `cross-encoder/nli-deberta-v3-base` |
| 제로샷 분류 (가벼운 것) | `facebook/bart-large-mnli` |
| 문서 수준 NLI | `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` |
| 다국어 | `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` |
| RAG 환각 탐지 | RAGAS / DeepEval 내부의 NLI 계층 |

2026년의 메타 패턴: NLI는 텍스트 이해의 청테이프(duct tape)입니다. "A가 B를 뒷받침하나?", "A가 B와 모순되나?"가 필요한 순간이면 — LLM 호출을 하나 더 추가하기 전에 NLI부터 꺼내세요.

## 출시하기

`outputs/skill-nli-picker.md`로 저장하세요:

```markdown
---
name: nli-picker
description: 분류 / 충실도 / 제로샷 과제를 위한 NLI 모델, 레이블 템플릿, 평가 구성 고르기.
version: 1.0.0
phase: 5
lesson: 21
tags: [nlp, nli, zero-shot]
---

사용 사례(충실도 검사, 제로샷 분류, 문서 수준 추론)가 주어지면 다음을 출력하세요:

1. 모델. 이름이 명시된 NLI 체크포인트. 도메인, 길이, 언어에 근거를 댈 것.
2. 템플릿(제로샷이라면). 언어화 패턴. 예시 포함.
3. 임계값. 결정 규칙의 함의 컷오프. 보정(calibration)에 근거를 댈 것.
4. 평가. 보류(held-out) 레이블 셋 정확도, 가설 전용 베이스라인, 적대적 부분집합.

예시 100개짜리 레이블 점검 없이 제로샷 분류를 출시하지 마세요. 문서 길이 전제에 문장 수준 NLI 모델을 쓰지 마세요. NLI가 환각을 해결한다는 주장은 표시하세요 — 환각을 줄일 뿐, 없애지는 않습니다.
```

## 연습 문제

1. **쉬움.** 세 클래스를 모두 커버하는 손수 만든 (전제, 가설, 레이블) 삼중항 20개로 `facebook/bart-large-mnli`를 돌려 보세요. 정확도를 측정하세요. 적대적인 "부분수열 휴리스틱" 함정("I did not eat the cake" vs "I ate the cake")을 추가하고 무너지는지 확인하세요.
2. **중간.** AG News 헤드라인 100개에서 제로샷 템플릿 `"This text is about {label}"`, `"The topic is {label}"`, `"{label}"`을 비교하세요. 정확도 요동을 보고하세요.
3. **어려움.** RAG 충실도 검사기를 만드세요: 원자적 주장 분해 + 주장마다 NLI. 골드 컨텍스트가 있는 RAG 생성 답변 50개로 평가하고, 손 레이블 대비 거짓 양성률과 거짓 음성률을 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| NLI | Natural Language Inference | 전제-가설 관계의 3-웨이 분류. |
| RTE | Recognizing Textual Entailment | NLI의 옛 이름; 같은 과제. |
| 함의(entailment) | "t가 h를 함의" | 전형적인 독자라면 t가 주어지면 h가 참이라고 결론 내림. |
| 모순(contradiction) | "t가 h를 배제" | 전형적인 독자라면 t가 주어지면 h가 거짓이라고 결론 내림. |
| 중립(neutral) | "판단 불가" | t에서 h로 어느 방향의 추론도 불가. |
| 제로샷 분류 | 분류기로서의 NLI | 레이블을 가설로 언어화하고 최대 함의를 고름. |
| 충실도(faithfulness) | 답변이 근거가 있는가? | (검색된 컨텍스트, 생성된 답변)에 대한 NLI. |

## 더 읽을거리

- [Bowman et al. (2015). A large annotated corpus for learning natural language inference](https://arxiv.org/abs/1508.05326) — SNLI.
- [Williams, Nangia, Bowman (2017). A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference](https://arxiv.org/abs/1704.05426) — MultiNLI.
- [Nie et al. (2019). Adversarial NLI](https://arxiv.org/abs/1910.14599) — ANLI 벤치마크.
- [Yin, Hay, Roth (2019). Benchmarking Zero-shot Text Classification](https://arxiv.org/abs/1909.00161) — NLI-분류기로 쓰기.
- [He et al. (2021). DeBERTa: Decoding-enhanced BERT with Disentangled Attention](https://arxiv.org/abs/2006.03654) — 2026년 NLI의 일용할 말.
