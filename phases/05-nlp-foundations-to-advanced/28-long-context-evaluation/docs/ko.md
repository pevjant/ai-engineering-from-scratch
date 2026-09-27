# 롱 컨텍스트 평가 — NIAH, RULER, LongBench, MRCR (Long-Context Evaluation)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> Gemini 3 Pro는 1,000만 토큰 컨텍스트를 내세웁니다. 하지만 100만 토큰에서 8-needle MRCR 점수는 26.3%로 떨어집니다. 광고 문구 ≠ 실제 사용 가능치. 롱 컨텍스트 평가는 여러분이 출시할 모델의 실제 용량을 알려 줍니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 13(질의응답), 페이즈 5 · 23(청킹 전략)
**소요 시간:** 약 60분

## 문제 상황

200페이지짜리 계약서가 있습니다. 모델은 100만 토큰 컨텍스트를 주장합니다. 계약서를 통째로 붙여 넣고 묻습니다: "해지 조항이 뭐야?" 모델이 답은 합니다 — 하지만 표지에서 답합니다. 해지 조항은 12만 토큰 깊이, 모델이 실제로 어텐션을 주는 범위를 훨씬 넘어 자리 잡고 있기 때문입니다.

이것이 2026년의 컨텍스트 용량 격차입니다. 스펙 시트는 100만 또는 1,000만을 말합니다. 현실은 그중 60~70%만 사용 가능하다고 말하고, "사용 가능"의 기준은 작업에 따라 달라집니다.

- **검색(건초 더미의 바늘 하나):** 최첨단 모델은 광고된 최대치까지 거의 완벽합니다.
- **멀티홉 / 집계:** 대부분의 모델에서 약 128k를 넘으면 급격히 저하됩니다.
- **흩어진 사실들에 대한 추론:** 가장 먼저 실패하는 작업.

롱 컨텍스트 평가는 이 축들을 측정합니다. 이 레슨은 벤치마크들의 이름, 각각이 실제로 측정하는 것, 그리고 여러분 도메인용 커스텀 바늘 테스트를 만드는 방법을 다룹니다.

## 개념

![NIAH 베이스라인, RULER 멀티태스크, LongBench 총체적 평가](../assets/long-context-eval.svg)

**Needle-in-a-Haystack(NIAH, 2023).** 긴 컨텍스트의 통제된 깊이에 사실 하나("마법의 단어는 pineapple이다")를 심습니다. 모델에게 그것을 찾으라고 합니다. 깊이 × 길이를 쓸어(sweep) 측정합니다. 최초의 롱 컨텍스트 벤치마크입니다. 이제 최첨단 모델들은 이걸 포화시킵니다. 필요하지만 충분하지는 않은 베이스라인입니다.

**RULER(Nvidia, 2024).** 4개 카테고리에 걸친 13가지 작업 유형: 검색(단일 / 다중 키 / 다중 값), 멀티홉 추적(변수 추적), 집계(자주 나오는 단어 빈도), QA. 컨텍스트 길이 설정 가능(4k ~ 128k+). NIAH는 포화시키지만 멀티홉에서 실패하는 모델을 적발합니다. 2024년 릴리스에서는 32k+ 컨텍스트를 내세운 17개 모델 중 절반만 32k에서도 품질을 유지했습니다.

**LongBench v2 (2024).** 객관식 문제 503개, 8k~2백만 단어 컨텍스트, 여섯 작업 카테고리: 단일 문서 QA, 다중 문서 QA, 롱 인컨텍스트 학습, 긴 대화, 코드 저장소, 긴 구조화 데이터. 실세계 롱 컨텍스트 동작에 대한 프로덕션 벤치마크입니다.

**MRCR(Multi-Round Coreference Resolution).** 대규모 멀티턴 상호 참조입니다. 8-needle, 24-needle, 100-needle 변형이 있습니다. 어텐션이 저하되기 전에 모델이 몇 개의 사실을 동시에 쥐고 있을 수 있는지 드러냅니다.

**NoLiMa.** "비어휘적 바늘(non-lexical needle)." 바늘과 질의가 글자 수준에서 겹치지 않습니다; 검색에 의미 추론 한 단계가 필요합니다. NIAH보다 어렵습니다.

**HELMET.** 많은 문서를 이어 붙이고 그중 하나에서 질문을 합니다. 선택적 어텐션을 시험합니다.

**BABILong.** bAbI 추론 사슬을 상관없는 잡동사니 속에 심습니다. 단순 검색이 아니라 건초 더미 속 추론을 시험합니다.

### 실제로 보고해야 할 것

- **광고된 컨텍스트 윈도우.** 스펙 시트의 숫자.
- **유효 검색 길이.** 어떤 임계값(예: 90%)에서 NIAH 통과.
- **유효 추론 길이.** 같은 임계값에서 멀티홉 또는 집계 통과.
- **저하 곡선.** 정확도 대 컨텍스트 길이, 작업 유형별로 그린 그래프.

스펙 시트에 적을 두 숫자: 검색 유효 길이와 추론 유효 길이. 보통 추론 유효 길이는 광고된 윈도우의 25~50%입니다.

```figure
gx-niah-decay
```

## 직접 만들기

### 단계 1: 여러분 도메인용 커스텀 NIAH

`code/main.py`를 보세요. 뼈대는 다음과 같습니다:

```python
def build_haystack(filler_text, needle, depth_ratio, total_tokens):
    if not (0.0 <= depth_ratio <= 1.0):
        raise ValueError(f"depth_ratio must be in [0, 1], got {depth_ratio}")
    if total_tokens <= 0:
        raise ValueError(f"total_tokens must be positive, got {total_tokens}")

    filler_tokens = tokenize(filler_text)
    needle_tokens = tokenize(needle)
    if not filler_tokens:
        raise ValueError("filler_text produced no tokens")

    # 건초 더미 본문을 채울 만큼 길어질 때까지 필러를 반복한다.
    body_len = max(total_tokens - len(needle_tokens), 0)
    while len(filler_tokens) < body_len:
        filler_tokens = filler_tokens + filler_tokens
    filler_tokens = filler_tokens[:body_len]

    insert_at = min(int(body_len * depth_ratio), body_len)
    haystack = filler_tokens[:insert_at] + needle_tokens + filler_tokens[insert_at:]
    return " ".join(haystack)


def score_niah(model, haystack, question, expected):
    answer = model.complete(f"Context: {haystack}\nQ: {question}\nA:", max_tokens=50)
    return 1 if expected.lower() in answer.lower() else 0
```

`depth_ratio` ∈ {0, 0.25, 0.5, 0.75, 1.0} × `total_tokens` ∈ {1k, 4k, 16k, 64k}를 쓸어 측정하세요. 히트맵을 그리세요. 그것이 여러분 대상 모델의 NIAH 카드입니다.

### 단계 2: 멀티 바늘 변형

```python
def build_multi_needle(filler, needles, total_tokens):
    depths = [0.1, 0.4, 0.7]
    chunks = [filler[:int(total_tokens * 0.1)]]
    for depth, needle in zip(depths, needles):
        chunks.append(needle)
        next_chunk = filler[int(total_tokens * depth): int(total_tokens * (depth + 0.3))]
        chunks.append(next_chunk)
    return " ".join(chunks)
```

"세 개의 마법의 단어는 무엇인가?" 같은 질문은 세 개를 모두 찾아야 합니다. 단일 바늘 성공이 멀티 바늘 성공을 예측하지 못합니다.

### 단계 3: 멀티홉 변수 추적(RULER 스타일)

```python
haystack = """X1 = 42. ... (filler) ... X2 = X1 + 10. ... (filler) ... X3 = X2 * 2."""
question = "What is X3?"
```

답을 내려면 세 번의 대입을 사슬처럼 이어야 합니다. 128k에서 최첨단 모델조차 여기서 정확도가 50~70%로 떨어지곤 합니다.

### 단계 4: 여러분 스택 위에서 LongBench v2 돌리기

```python
from datasets import load_dataset
longbench = load_dataset("THUDM/LongBench-v2")

def eval_model_on_longbench(model, subset="single-doc-qa"):
    tasks = [x for x in longbench["test"] if x["task"] == subset]
    correct = 0
    for x in tasks:
        answer = model.complete(x["context"] + "\n\nQ: " + x["question"], max_tokens=20)
        if normalize(answer) == normalize(x["answer"]):
            correct += 1
    return correct / len(tasks)
```

카테고리별 정확도를 보고하세요. 집계 점수는 큰 작업 수준 차이를 가립니다.

## 흔한 실수

- **NIAH 전용 평가.** 100만 토큰에서 NIAH를 통과해도 멀티홉에 관해서는 아무 말도 해 주지 않습니다. 항상 RULER나 커스텀 멀티홉 테스트를 함께 돌리세요.
- **균일한 깊이 샘플링.** 많은 구현이 depth=0.5만 테스트합니다. depth=0, 0.25, 0.5, 0.75, 1.0을 모두 테스트하세요 — "lost in the middle" 효과는 실제로 존재합니다.
- **필러와의 어휘 중첩.** 바늘이 필러와 키워드를 공유하면 검색이 너무 쉬워집니다. NoLiMa 스타일의 겹치지 않는 바늘을 쓰세요.
- **지연 시간 무시.** 100만 토큰 프롬프트의 프리필(prefill)에는 30~120초가 걸립니다. 정확도와 함께 time-to-first-token을 측정하세요.
- **벤더 자체 보고 숫자.** OpenAI, Google, Anthropic 모두 자기 점수를 발표합니다. 항상 여러분의 사용 사례에서 독립적으로 다시 돌리세요.

## 활용하기

2026년의 표준 스택:

| 상황 | 벤치마크 |
|-----------|-----------|
| 빠른 동작 확인 | 3 깊이 × 3 길이의 커스텀 NIAH |
| 프로덕션용 모델 선택 | 목표 길이에서 RULER (13 작업) |
| 실세계 QA 품질 | LongBench v2 single-doc-QA 서브셋 |
| 멀티홉 추론 | BABILong 또는 커스텀 변수 추적 |
| 대화형 / 다이얼로그 | 목표 길이에서 MRCR 8-needle |
| 모델 업그레이드 회귀 | 고정된 사내 NIAH + RULER 하네스, 새 모델마다 실행 |

프로덕션의 경험칙: 의도한 길이에서 NIAH + 추론 작업 1개를 돌려 보기 전까지는 컨텍스트 윈도우를 절대 믿지 마세요.

## 출시하기

`outputs/skill-long-context-eval.md`로 저장하세요:

```markdown
---
name: long-context-eval
description: Design a long-context evaluation battery for a given model and use case.
version: 1.0.0
phase: 5
lesson: 28
tags: [nlp, long-context, evaluation]
---

대상 모델, 목표 컨텍스트 길이, 사용 사례가 주어지면 다음을 출력합니다:

1. 테스트. NIAH 깊이 × 길이 그리드; RULER 멀티홉; 커스텀 도메인 작업.
2. 샘플링. 각 길이에서 깊이 0, 0.25, 0.5, 0.75, 1.0.
3. 지표. 검색 통과율; 추론 통과율; time-to-first-token; 질의당 비용.
4. 컷오프. 유효 검색 길이(통과율 90%)와 유효 추론 길이(통과율 70%). 둘 다 보고합니다.
5. 회귀. 고정된 테스트 하네스, 모델 업그레이드 때마다 재실행, 변화량(delta) 보고.

모델 카드만 믿고 컨텍스트 윈도우를 신뢰하는 것은 거부합니다. 멀티홉 작업에 NIAH 전용 평가를 쓰는 것은 거부합니다. 벤더가 자체 보고한 롱 컨텍스트 점수를 독립적 근거로 받아들이는 것은 거부합니다.
```

## 연습 문제

1. **쉬움.** 3 깊이(0.25, 0.5, 0.75) × 3 길이(1k, 4k, 16k)의 NIAH를 만들어 보세요. 아무 모델에나 돌리고 통과율을 3×3 히트맵으로 그리세요.
2. **보통.** 3-needle 변형을 추가하세요. 각 길이에서 세 개 모두의 검색을 측정하고, 같은 길이의 단일 바늘 통과율과 비교하세요.
3. **어려움.** 변수 추적 작업(X1 → X2 → X3, 홉 3개)을 만들어 64k 필러 속에 심으세요. 최첨단 모델 3개의 정확도를 측정하고, 모델별 유효 추론 길이를 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| NIAH | 건초 더미 속 바늘 | 잡동사니 속에 사실을 심고 모델에게 찾으라고 함. |
| RULER | 강화판 NIAH | 검색 / 멀티홉 / 집계 / QA에 걸친 13가지 작업 유형. |
| 유효 컨텍스트 | 실제 용량 | 정확도가 임계값 위로 유지되는 길이. |
| Lost in the middle | 깊이 편향 | 모델이 긴 입력의 중간 내용에 어텐션을 덜 줌. |
| 멀티 바늘 | 여러 사실을 한꺼번에 | 여러 개를 심음; 단순 검색이 아니라 어텐션 분배 능력을 시험. |
| MRCR | 멀티라운드 coref | 8, 24, 100-needle 상호 참조; 어텐션 포화를 드러냄. |
| NoLiMa | 비어휘적 바늘 | 바늘과 질의가 글자 토큰을 공유하지 않음; 추론이 필요. |

## 더 읽을거리

- [Kamradt (2023). Needle in a Haystack analysis](https://github.com/gkamradt/LLMTest_NeedleInAHaystack) — 최초의 NIAH 저장소.
- [Hsieh et al. (2024). RULER: What's the Real Context Size of Your Long-Context LMs?](https://arxiv.org/abs/2404.06654) — 멀티태스크 벤치마크.
- [Bai et al. (2024). LongBench v2](https://arxiv.org/abs/2412.15204) — 실세계 롱 컨텍스트 평가.
- [Modarressi et al. (2024). NoLiMa: Non-lexical needles](https://arxiv.org/abs/2404.06666) — 더 어려운 바늘.
- [Kuratov et al. (2024). BABILong](https://arxiv.org/abs/2406.10149) — 건초 더미 속 추론.
- [Liu et al. (2024). Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) — 깊이 편향 논문.
