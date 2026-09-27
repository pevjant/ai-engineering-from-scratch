# T5, BART — 인코더-디코더 모델

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 인코더는 이해합니다. 디코더는 생성합니다. 둘을 다시 합치면 입력 → 출력 과제를 위해 만들어진 모델이 나옵니다: 번역, 요약, 고쳐 쓰기, 받아쓰기.

**유형:** 학습(Learn)
**언어:** Python
**선수 지식:** 페이즈 7 · 05 (완전한 트랜스포머), 페이즈 7 · 06 (BERT), 페이즈 7 · 07 (GPT)
**시간:** 약 45분

## 문제 상황

디코더 전용 GPT와 인코더 전용 BERT는 2017년 아키텍처를 서로 다른 목표에 맞춰 각각 축소한 겁니다. 하지만 많은 과제는 본질적으로 입력-출력 형태입니다:

- 번역: 영어 → 프랑스어.
- 요약: 5,000토큰 기사 → 200토큰 요약.
- 음성 인식: 오디오 토큰 → 텍스트 토큰.
- 구조화된 추출: 산문 → JSON.

이런 과제에는 인코더-디코더가 가장 깔끔하게 맞습니다. 인코더가 소스의 밀집 표현을 만들고, 디코더가 그 표현을 매 단계 크로스 어텐션으로 참조하며 출력을 생성합니다. 학습은 출력 쪽에서 한 칸 밀기(shift-by-one)입니다. GPT와 같은 손실이되, 인코더 출력을 조건으로 붙인 것뿐입니다.

현대의 플레이북을 정의한 논문 두 편:

1. **T5** (Raffel et al. 2019). "Text-to-Text Transfer Transformer." 모든 NLP 과제를 텍스트 입력-텍스트 출력으로 다시 프레이밍했습니다. 단일 아키텍처, 단일 어휘, 단일 손실. 마스크드 스팬 예측(입력의 스팬을 망가뜨리고 출력에서 복원)으로 사전 학습합니다.
2. **BART** (Lewis et al. 2019). "Bidirectional and Auto-Regressive Transformer." 노이즈 제거 오토인코더: 입력을 여러 방식으로 망가뜨린 뒤(섞기, 가리기, 지우기, 회전), 디코더가 원본을 복원하게 합니다.

2026년에도 인코더-디코더 형식은 입력 구조가 중요한 곳에서 살아 있습니다:

- Whisper (음성 → 텍스트).
- Google의 번역 스택.
- 뚜렷한 "컨텍스트 + 편집" 구조를 가진 일부 코드 완성 / 수리 모델.
- 구조화된 추론 과제용 Flan-T5와 그 변형들.

주인공 자리는 디코더 전용이 가져갔지만, 인코더-디코더는 사라지지 않았습니다.

## 핵심 개념

![크로스 어텐션을 갖춘 인코더-디코더](../assets/encoder-decoder.svg)

### 순전파 루프

```
source tokens ─▶ encoder ─▶ (N_src, d_model)  ──┐
                                                 │
target tokens ─▶ decoder block                   │
                 ├─▶ masked self-attention       │
                 ├─▶ cross-attention ◀───────────┘
                 └─▶ FFN
                ↓
              next-token logits
```

중요한 점: 인코더는 입력마다 한 번만 돕니다. 디코더는 자기회귀적으로 돌지만 매 단계 *같은* 인코더 출력을 크로스 어텐션합니다. 인코더 출력을 캐싱해 두면 긴 입력에서 공짜 속도 향상이 됩니다.

### T5 사전 학습 — 스팬 망가뜨리기(span corruption)

입력에서 무작위 스팬(평균 길이 3토큰, 총 15%)을 고릅니다. 각 스팬을 고유한 센티널(sentinel)로 교체합니다: `<extra_id_0>`, `<extra_id_1>` 등. 디코더는 센티널 접두사와 함께 망가진 스팬들만 출력합니다:

```
source: The quick <extra_id_0> fox jumps <extra_id_1> dog
target: <extra_id_0> brown <extra_id_1> over the lazy
```

시퀀스 전체를 예측하는 것보다 싼 신호입니다. T5 논문의 제거 실험에서 MLM(BERT) 및 prefix-LM(UniLM)과 경쟁력이 있었습니다.

### BART 사전 학습 — 다중 노이즈 제거

BART는 다섯 가지 노이즈 함수를 시도합니다:

1. 토큰 마스킹.
2. 토큰 삭제.
3. 텍스트 인필링(스팬을 가리고, 디코더가 알맞은 길이만큼 채워 넣음).
4. 문장 순열.
5. 문서 회전.

텍스트 인필링 + 문장 순열 조합이 가장 좋은 다운스트림 수치를 냈습니다. 디코더는 항상 원본 전체를 복원합니다. BART의 출력은 망가진 스팬만이 아니라 전체 시퀀스입니다 — 그래서 사전 학습 연산량이 T5보다 많이 듭니다.

### 추론

GPT와 같은 자기회귀 생성입니다. Greedy / beam / top-p 샘플링이 모두 적용됩니다. 빔 서치(폭 4-5)는 번역과 요약의 표준입니다. 출력 분포가 채팅보다 좁기 때문입니다.

### 2026년에 각 변형을 고르는 기준

| 과제 | 인코더-디코더? | 이유 |
|------|------------------|-----|
| 번역 | 그렇다, 보통 | 명확한 소스 시퀀스; 고정된 출력 분포; 빔 서치가 잘 동작 |
| 음성-텍스트 | 그렇다 (Whisper) | 입력 모달리티가 출력과 다름; 인코더가 오디오 특성을 다듬음 |
| 채팅 / 추론 | 아니다, 디코더 전용 | 지속되는 "입력"이 없음 — 대화 자체가 시퀀스 |
| 코드 완성 | 보통 아니다 | 장기 컨텍스트 디코더 전용이 이김; Qwen 2.5 Coder 같은 코드 모델도 디코더 전용 |
| 요약 | 둘 다 가능 | BART, PEGASUS가 초기 디코더 전용 베이스라인을 이겼지만 현대 디코더 전용 LLM이 따라잡음 |
| 구조화된 추출 | 둘 다 | T5가 깔끔함 — "텍스트 → 텍스트"라서 어떤 출력 형식도 흡수 |

2022년 무렵 이후의 흐름: 인코더-디코더가 갖고 있던 과제들을 디코더 전용이 가져갔습니다. 그 이유는 (a) 인스트럭션 튜닝된 디코더 전용 LLM이 프롬프트만으로 무엇이든 일반화되고, (b) 아키텍처 하나가 둘보다 확장이 쉽고, (c) RLHF는 디코더를 전제하기 때문입니다. 인코더-디코더는 입력 모달리티가 다른 곳(음성, 이미지)이나 빔 서치 품질이 중요한 곳에서 버티고 있습니다.

```figure
encoder-decoder
```

## 만들어 보기

`code/main.py`를 보세요. 장난감 코퍼스에 T5 스타일 스팬 망가뜨리기를 구현합니다 — 이 레슨에서 가장 유용한 단일 조각입니다. 그 이후의 모든 인코더-디코더 사전 학습 레시피에 등장하니까요.

### 단계 1: 스팬 망가뜨리기

```python
def corrupt_spans(tokens, mask_rate=0.15, mean_span=3.0, rng=None):
    """Pick spans summing to ~mask_rate of tokens. Return (corrupted_input, target)."""
    n = len(tokens)
    n_mask = max(1, int(n * mask_rate))
    n_spans = max(1, int(round(n_mask / mean_span)))
    ...
```

타깃 형식은 T5 관례를 따릅니다: `<sent0> span0 <sent1> span1 ...`. 망가진 입력은 변하지 않은 토큰과 스팬 위치의 센티널 토큰을 섞어 배치합니다.

### 단계 2: 왕복 검증하기

망가진 입력과 타깃이 주어지면 원래 문장을 복원합니다. 망가뜨리기가 되돌릴 수 있으면 순전파가 잘 정의된 것입니다. 온전성 검사입니다 — 실제 학습에서는 절대 이러지 않지만, 테스트가 싸고 스팬 장부 관리의 off-by-one 버그를 잡아 줍니다.

### 단계 3: BART 노이즈

다섯 개 함수: `token_mask`, `token_delete`, `text_infill`, `sentence_permute`, `document_rotate`. 그중 둘을 조합해 결과를 보여 줍니다.

## 활용하기

HuggingFace 기준 예제:

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer
tok = T5Tokenizer.from_pretrained("google/flan-t5-base")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")

inputs = tok("translate English to French: Attention is all you need.", return_tensors="pt")
out = model.generate(**inputs, max_new_tokens=32)
print(tok.decode(out[0], skip_special_tokens=True))
```

T5의 트릭: 과제 이름을 입력 텍스트 안에 넣습니다. 같은 모델이 수십 가지 과제를 처리합니다. 각 과제가 텍스트 입력-텍스트 출력이기 때문입니다. 2026년에는 이 패턴이 인스트럭션 튜닝된 디코더 전용 모델로 일반화됐지만, 처음 코드로 정리한 건 T5입니다.

## 출시하기

`outputs/skill-seq2seq-picker.md`를 보세요. 이 스킬은 입력-출력 구조, 지연 시간, 품질 목표가 주어진 새 과제에 인코더-디코더와 디코더 전용 중 하나를 골라 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 30토큰 문장에 스팬 망가뜨리기를 적용하고, 센티널이 아닌 소스 토큰과 디코딩된 타깃 스팬을 이어 붙이면 원본이 복원되는지 확인합니다.
2. **보통.** BART의 `text_infill` 노이즈를 구현합니다: 무작위 스팬을 `<mask>` 토큰 하나로 바꾸고, 디코더는 알맞은 스팬 길이와 내용을 추론해야 합니다. 예시 하나를 보여 주세요.
3. **어려움.** 아주 작은 영어 → 피그 라틴 코퍼스(200쌍)로 `flan-t5-small`을 파인튜닝합니다. 홀드아웃 50쌍에서 BLEU를 측정합니다. 같은 데이터, 같은 연산량으로 `Llama-3.2-1B`를 파인튜닝한 결과와 비교합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 인코더-디코더 | "seq2seq 트랜스포머" | 두 스택: 입력용 양방향 인코더, 크로스 어텐션이 달린 출력용 인과적 디코더. |
| 크로스 어텐션 | "소스와 타깃이 만나는 곳" | 디코더의 Q × 인코더의 K/V. 인코더 정보가 디코더로 들어오는 유일한 통로. |
| 스팬 망가뜨리기 (Span corruption) | "T5의 사전 학습 트릭" | 무작위 스팬을 센티널 토큰으로 바꾸고 디코더가 그 스팬들을 출력하게 한다. |
| 노이즈 제거 목적 함수 | "BART의 게임" | 입력에 노이즈 함수를 적용하고, 디코더가 깨끗한 시퀀스를 복원하도록 학습한다. |
| 센티널 토큰 | "`<extra_id_N>` 자리표시자" | 소스에서 망가진 스팬에 표시를 하고 타깃에서 다시 표시하는 특수 토큰. |
| Flan | "인스트럭션 튜닝된 T5" | 1,800개가 넘는 과제로 파인튜닝한 T5; 인코더-디코더를 인스트럭션 따르기에서 경쟁력 있게 만들었다. |
| 빔 서치 (Beam search) | "디코딩 전략" | 매 단계 상위 k개 부분 시퀀스를 유지한다; 번역/요약의 표준. |
| Teacher forcing | "학습 시점의 입력" | 학습 중 샘플링한 토큰이 아니라 실제 이전 출력 토큰을 디코더에 먹인다. |

## 더 읽을거리

- [Raffel et al. (2019). Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer](https://arxiv.org/abs/1910.10683) — T5.
- [Lewis et al. (2019). BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension](https://arxiv.org/abs/1910.13461) — BART.
- [Chung et al. (2022). Scaling Instruction-Finetuned Language Models](https://arxiv.org/abs/2210.11416) — Flan-T5.
- [Radford et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — Whisper, 2026년 인코더-디코더의 표준.
- [HuggingFace `modeling_t5.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/t5/modeling_t5.py) — 참조 구현.
