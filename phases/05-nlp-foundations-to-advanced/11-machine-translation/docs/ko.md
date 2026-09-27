> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 기계 번역 (Machine Translation)

> 번역은 30년 동안 NLP 연구의 밥줄이었던 과제이고, 지금도 밥줄입니다.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 10(어텐션 메커니즘), 페이즈 5 · 04(GloVe, FastText, 하위 단어)
**소요 시간:** 약 75분

## 해결할 문제

모델이 한 언어의 문장을 읽고 다른 언어의 문장을 만들어 냅니다. 길이는 제각각이고, 어순도 제각각입니다. 어떤 원문 단어는 대상 단어 여러 개에 대응되고 그 반대도 있습니다. 관용구는 일대일 대응을 거부합니다. 프랑스어의 "I miss you"는 "tu me manques", 직역하면 "당신이 나에게 결핍되어 있다"입니다. 거기서 살아남는 단어 수준 정렬은 없습니다.

기계 번역은 NLP가 인코더-디코더, 어텐션, 트랜스포머, 그리고 결국 LLM 패러다임 전체를 발명하게 만든 과제입니다. 매 전진은 번역 품질이 측정 가능했고 인간과 기계 사이 격차가 꿈쩍도 하지 않았기 때문에 도달한 것입니다.

이 레슨은 역사 강의는 건너뛰고 2026년의 실전 파이프라인을 가르칩니다. 사전학습 다국어 인코더-디코더(NLLB-200 또는 mBART), 하위 단어 토큰화, 빔 서치, BLEU와 chrF 평가, 그리고 아직도 잡히지 않은 채 프로덕션(운영 환경)에 출시되는 몇 가지 실패 모드까지요.

## 핵심 개념

![MT 파이프라인: 토큰화 → 인코딩 → 어텐션으로 디코딩 → 디토큰화](../assets/mt-pipeline.svg)

현대 기계 번역은 병렬 텍스트로 학습한 트랜스포머 인코더-디코더입니다. 인코더는 원문을 해당 언어의 토큰화 방식으로 읽습니다. 디코더는 크로스 어텐션(레슨 10)을 통해 인코더의 출력을 이용해 대상 문장을 하위 단어 하나씩 생성합니다. 복호화에는 빔 서치를 써서 탐욕적 복호화의 함정을 피합니다. 출력은 디토큰화하고 대소문자를 복원한 뒤(detruecase) 참조 번역과 대조해 점수를 매깁니다.

실제 세상의 번역 품질을 좌우하는 운영 선택은 세 가지입니다.

- **토크나이저.** 혼합 언어 코퍼스로 학습한 SentencePiece BPE. 언어들에 걸친 공유 어휘집이야말로 NLLB에서 제로샷 언어 쌍을 가능하게 하는 것입니다.
- **모델 크기.** NLLB-200 distilled 600M는 노트북에 들어갑니다. NLLB-200 3.3B는 발표된 프로덕션 기본값이고, 54.5B는 연구용 천장입니다.
- **복호화.** 일반 콘텐츠에는 빔 폭 4~5. 너무 짧은 출력을 막으려면 길이 패널티. 용어 일관성이 필요하면 제약 복호화.

```figure
seq2seq-alignment
```

## 만들어 보기

### 단계 1: 사전학습 MT 호출 한 번

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_id = "facebook/nllb-200-distilled-600M"
tok = AutoTokenizer.from_pretrained(model_id, src_lang="eng_Latn")
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

src = "The cats are running."
inputs = tok(src, return_tensors="pt")

out = model.generate(
    **inputs,
    forced_bos_token_id=tok.convert_tokens_to_ids("fra_Latn"),
    num_beams=5,
    length_penalty=1.0,
    max_new_tokens=64,
)
print(tok.batch_decode(out, skip_special_tokens=True)[0])
```

```text
Les chats courent.
```

여기서 중요한 것 셋. `src_lang`은 토크나이저에게 어떤 문자 체계와 분할을 적용할지 알려 줍니다. `forced_bos_token_id`는 디코더에게 어떤 언어를 생성할지 알려 줍니다. 둘 다 NLLB 전용 트릭입니다. mBART와 M2M-100은 자기들만의 관례를 쓰며 서로 호환되지 않습니다.

### 단계 2: BLEU와 chrF

BLEU는 출력과 참조 번역 사이의 n-gram 겹침을 측정합니다. 네 가지 참조 n-gram 크기(1~4), 정밀도들의 기하평균, 너무 짧은 출력에 대한 길이 패널티(brevity penalty). 점수는 [0, 100] 범위입니다. 가장 흔하게 쓰이지만 해석이 답답합니다. BLEU 30은 "쓸 만함", 40은 "좋음", 50은 "예외적"이고, 1 미만의 차이는 노이즈입니다.

chrF는 문자 수준 F-점수를 측정합니다. BLEU가 일치를 과소 계산하는 형태론이 풍부한 언어에 더 민감합니다. 보통 BLEU와 함께 보고됩니다.

```python
import sacrebleu

hypotheses = ["Les chats courent."]
references = [["Les chats courent."]]

bleu = sacrebleu.corpus_bleu(hypotheses, references)
chrf = sacrebleu.corpus_chrf(hypotheses, references)
print(f"BLEU: {bleu.score:.1f}  chrF: {chrf.score:.1f}")
```

항상 `sacrebleu`를 쓰세요. 토큰화를 정규화해 주기 때문에 논문들 사이에서 점수 비교가 가능해집니다. BLEU 계산을 직접 만드는 것이 오도되는 벤치마크가 생기는 길입니다.

### 3단계 평가 체계(2026)

현대 MT 평가는 서로 보완적인 지표 계열 세 가지를 씁니다. 출시할 때는 최소 둘 이상을 쓰세요.

- **휴리스틱** (BLEU, chrF). 빠르고, 참조 기반이고, 해석 가능하고, 바꿔 쓰기(paraphrase)에는 둔감합니다. 레거시 비교와 회귀 감지에 씁니다.
- **학습된 지표** (COMET, BLEURT, BERTScore). 인간 판단으로 학습한 신경망 모델로, 번역과 원문·참조의 의미 유사도를 비교합니다. COMET은 2023년 이후 MT 연구와의 연관성이 가장 높고, 품질이 중요한 2026년 프로덕션 기본값입니다.
- **LLM 심판(LLM-as-judge)** (참조 불필요). 큰 모델에게 번역을 유창성, 충실성, 어조, 문화적 적절성 기준으로 채점하라고 프롬프트합니다. 평가 기준표(rubric)가 잘 설계돼 있으면 GPT-4 심판이 인간 일치율의 약 80%에 도달합니다. 참조가 존재하지 않는 개방형 콘텐츠에 씁니다.

실전 2026 스택: BLEU와 chrF에는 `sacrebleu`, COMET에는 `unbabel-comet`, 최종 인간 대면 신호에는 프롬프트한 LLM. 프로덕션 데이터를 믿기 전에 사람이 레이블한 예시 50~100개로 모든 지표를 보정(calibration)하세요.

참조 불필요 지표(COMET-QE, BLEURT-QE, LLM 심판)는 참조 번역 없이도 번역을 평가하게 해 줍니다. 참조 번역이 존재하지 않는 롱테일 언어 쌍에서 이것이 빛을 발합니다.

### 단계 3: 프로덕션에서 무너지는 것

위의 실전 파이프라인은 80%의 시간에는 유창하게 번역하고 나머지 20%에서는 조용히 실패합니다. 이름 붙은 실패 모드들:

- **환각.** 모델이 원문에 없던 내용을 지어냅니다. 낯선 도메인 어휘에서 흔합니다. 증상: 출력은 유창한데 원문이 말하지 않은 사실을 주장합니다. 완화책: 도메인 용어에 제약 복호화, 규제 대상 콘텐츠는 사람 검수, 입력보다 훨씬 긴 출력 모니터링.
- **엉뚱 언어 생성(off-target generation).** 모델이 잘못된 언어로 번역합니다. NLLB는 희귀 언어 쌍에서 의외로 이것에 취약합니다. 완화책: `forced_bos_token_id`를 검증하고, 출력에 언어 식별(language-ID) 모델 점검을 항상 붙입니다.
- **용어 표류.** "Sign up"이 문서 1에서는 "s'inscrire"가 되고 문서 2에서는 "créer un compte"가 됩니다. UI 텍스트와 사용자 대면 문자열에서는 원시 품질보다 일관성이 더 중요합니다. 완화책: 용어집(glossary) 제약 복호화 또는 사후 편집 사전.
- **격식 불일치.** 프랑스어의 "tu" vs "vous", 일본어의 경어 수준. 모델은 학습 데이터에서 더 흔했던 형태를 고릅니다. 고객 대면 콘텐츠에서는 보통 틀립니다. 완화책: 모델이 지원한다면 격식 토큰을 프롬프트 접두어로 붙이거나, 격식체 전용 코퍼스로 소형 모델을 파인튜닝.
- **짧은 입력에서의 길이 폭발.** 아주 짧은 입력 문장은 지나치게 긴 번역을 낳는 경우가 잦습니다. 원문 토큰이 약 5개 이하면 길이 패널티가 낭떠러지로 떨어지기 때문입니다. 완화책: 원문 길이에 비례한 하드 최대 길이 제한.

### 단계 4: 도메인용 파인튜닝

사전학습 모델은 만능 타입입니다. 법률, 의료, 게임 대화 번역은 도메인 병렬 데이터로 파인튜닝하면 측정 가능한 이득을 봅니다. 레시피는 별것 아닙니다.

```python
from transformers import Trainer, TrainingArguments
from datasets import Dataset

pairs = [
    {"src": "The defendant pleaded guilty.", "tgt": "L'accusé a plaidé coupable."},
]

ds = Dataset.from_list(pairs)


def preprocess(ex):
    return tok(
        ex["src"],
        text_target=ex["tgt"],
        truncation=True,
        max_length=128,
        padding="max_length",
    )


ds = ds.map(preprocess, remove_columns=["src", "tgt"])

args = TrainingArguments(output_dir="out", per_device_train_batch_size=4, num_train_epochs=3, learning_rate=3e-5)
Trainer(model=model, args=args, train_dataset=ds).train()
```

고품질 병렬 예시 몇천 개가 노이즈 가득한 웹 스크래핑 예시 수십만 개를 이깁니다. 학습 데이터의 품질이 단연 큰 프로덕션 레버입니다.

## 활용하기

2026년 현재 MT 프로덕션 스택:

| 사용 사례 | 추천 시작점 |
|---------|---------------------------|
| 어떤 언어든 어떤 언어로, 200개 언어 | `facebook/nllb-200-distilled-600M` (노트북) 또는 `nllb-200-3.3B` (프로덕션) |
| 영어 중심, 고품질, 50개 언어 | `facebook/mbart-large-50-many-to-many-mmt` |
| 짧은 실행, 싼 추론, 영어-프랑스어/독일어/스페인어 | Helsinki-NLP / Marian 모델 |
| 지연 시간이 생명인 브라우저 측 | ONNX 양자화 Marian (약 50 MB) |
| 최대 품질, 비용 감수 | 번역 프롬프트를 곁들인 GPT-4 / Claude / Gemini |

2026년 현재 LLM은 여러 언어 쌍에서 특화 MT 모델을 앞지릅니다. 특히 관용적 표현과 긴 컨텍스트에서 그렇습니다. 트레이드오프는 토큰당 비용과 지연 시간입니다. 컨텍스트 길이, 문체 일관성, 프롬프트를 통한 도메인 적응이 처리량보다 중요하다면 LLM을 고르세요.

## 출시하기

`outputs/skill-mt-evaluator.md`로 저장하세요:

```markdown
---
name: mt-evaluator
description: 출시 전 기계 번역 출력을 평가합니다.
version: 1.0.0
phase: 5
lesson: 11
tags: [nlp, translation, evaluation]
---

원문 텍스트와 후보 번역이 주어지면 다음을 출력합니다:

1. 자동 점수 추정. 예상되는 BLEU와 chrF 범위. 참조 번역이 있는지 없는지 밝힙니다.
2. 사람이 직접 확인 가능한 5항목 체크리스트: (a) 내용 보존(환각 없음), (b) 올바른 언어, (c) 레지스터/격식 일치, (d) 용어집이 있다면 용어 일관성, (e) 잘림이나 길이 폭발 없음.
3. 추가로 파고들 도메인 특화 이슈 하나. 예: 법률은 고유명사와 법령 인용. 의료는 약품명과 용량. UI는 `{name}` 같은 플레이스홀더 변수.
4. 신뢰도 플래그. "출시" / "검수 후 출시" / "출시 금지". 2번에서 발견된 이슈의 심각도와 연동합니다.

출력에 언어 식별(language-ID) 점검 없이 번역을 출시하는 일은 거부합니다. 사용자가 참조 불필요 채점(COMET-QE, BLEURT-QE)에 명시적으로 동의하지 않는 한 참조 없이 평가하는 일도 거부합니다. 1000토큰이 넘는 콘텐츠는 청크 단위 번역이 필요할 가능성이 높다고 표시합니다.
```

## 연습 문제

1. **(쉬움)** 영어 단락 5문장을 `nllb-200-distilled-600M`으로 프랑스어로 번역했다가 다시 영어로 돌려 보세요. 왕복 결과가 원문과 얼마나 가까운지 측정합니다. 단어 선택은 흘러가지만 의미는 보존되는 모습을 보게 될 겁니다.
2. **(보통)** `fasttext lid.176`이나 `langdetect`로 번역 출력에 언어 식별 점검을 구현하세요. MT 호출에 통합해서 엉뚱 언어 생성이 반환되기 전에 잡히게 만듭니다.
3. **(어려움)** 원하는 도메인 코퍼스 5,000쌍으로 `nllb-200-distilled-600M`을 파인튜닝하세요. 파인튜닝 전후로 홀드아웃 세트의 BLEU를 측정합니다. 어떤 종류의 문장이 나아지고 어떤 문장이 나빠졌는지 보고합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| BLEU | 번역 점수 | 길이 패널티를 곁들인 n-gram 정밀도. [0, 100]. |
| chrF | 문자 F-점수 | 문자 수준 F-점수. 형태론이 풍부한 언어에 더 민감함. |
| NMT | 신경망 기계 번역 | 병렬 텍스트로 학습한 트랜스포머 인코더-디코더. 2017년 이후의 기본값. |
| NLLB | No Language Left Behind | Meta의 200개 언어 MT 모델 계열. |
| 제약 복호화 | 통제된 출력 | 특정 토큰이나 n-gram이 출력에 나타나거나/나타나지 않도록 강제함. |
| 환각 | 지어낸 내용 | 원문이 뒷받침하지 않는 모델 출력. |

## 더 읽을거리

- [Costa-jussà et al. (2022). No Language Left Behind: Scaling Human-Centered Machine Translation](https://arxiv.org/abs/2207.04672) — NLLB 논문.
- [Post (2018). A Call for Clarity in Reporting BLEU Scores](https://aclanthology.org/W18-6319/) — BLEU 보고에 `sacrebleu`만이 올바른 방법인 이유.
- [Popović (2015). chrF: character n-gram F-score for automatic MT evaluation](https://aclanthology.org/W15-3049/) — chrF 논문.
- [Hugging Face MT 가이드](https://huggingface.co/docs/transformers/tasks/translation) — 실전 파인튜닝 워크스루.
