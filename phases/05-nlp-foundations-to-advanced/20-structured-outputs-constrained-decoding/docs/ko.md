> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 구조화된 출력과 제약 디코딩

> LLM에게 JSON을 달라고 합니다. 대부분의 때 JSON을 받습니다. 프로덕션(운영 환경)에서는 "대부분"이 문제입니다. 제약 디코딩(constrained decoding)은 샘플링 전에 로짓을 편집해서 "대부분"을 "항상"으로 바꿔 줍니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 17(챗봇), 페이즈 5 · 19(서브워드 토큰화)
**시간:** 약 60분

## 문제 상황

분류기가 LLM에게 프롬프트를 줍니다: "{positive, negative, neutral} 중 하나를 반환하라." 모델은 "The sentiment is positive — this review is overwhelmingly favorable because the customer explicitly states that they ..."를 돌려줍니다. 파서가 죽고, 분류기의 F1은 0.0이 됩니다.

자유 형식 생성은 계약이 아닙니다. 제안일 뿐입니다. 프로덕션 시스템에는 계약이 필요합니다.

2026년에는 세 계층이 존재합니다.

1. **프롬프팅.** 정중히 부탁합니다. "JSON 객체만 반환하라." 프론티어 모델에서 ~80% 정도 통하고, 작은 모델에서는 그보다 낮습니다.
2. **네이티브 구조화 출력 API.** OpenAI `response_format`, Anthropic 도구 사용, Gemini JSON 모드. 지원되는 스키마에서는 신뢰할 수 있습니다. 벤더 종속입니다.
3. **제약 디코딩.** 매 생성 단계에서 로짓을 수정해서 모델이 *유효하지 않은 토큰을 아예 내보낼 수 없게* 만듭니다. 구조적으로 100% 유효. 어떤 로컬 모델에도 동작합니다.

이 레슨은 세 가지 모두에 대한 직관을 만들고, 언제 무엇을 써야 하는지 알려 줍니다.

## 핵심 개념

![매 단계에서 유효하지 않은 토큰을 마스킹하는 제약 디코딩](../assets/constrained-decoding.svg)

**제약 디코딩의 동작 원리.** 매 생성 단계에서 LLM은 전체 어휘(약 10만 토큰)에 대한 로짓 벡터를 만듭니다. *로짓 프로세서*가 모델과 샘플러 사이에 앉습니다. 프로세서는 목표 문법 — JSON Schema, 정규식, 문맥 자유 문법 — 에서 현재 위치에서 유효한 토큰이 무엇인지 계산하고, 유효하지 않은 모든 토큰의 로짓을 음의 무한대로 설정합니다. 남은 로짓 위의 소프트맥스는 유효한 이어지기에만 확률 질량을 배분합니다.

2026년의 구현체들:

- **Outlines.** JSON Schema나 정규식을 유한 상태 기계(FSM)로 컴파일합니다. 모든 토큰에 대해 O(1) 유효 다음 토큰 룩업을 제공합니다. FSM 기반이라 재귀 스키마는 평탄화가 필요합니다.
- **XGrammar / llguidance.** 문맥 자유 문법(CFG) 엔진입니다. 재귀 JSON Schema를 처리합니다. 디코딩 오버헤드가 거의 없습니다. OpenAI가 2025년 자사 구조화 출력 구현에서 llguidance를 언급했습니다.
- **vLLM guided decoding.** Outlines, XGrammar, lm-format-enforcer 백엔드를 통한 내장 `guided_json`, `guided_regex`, `guided_choice`, `guided_grammar`.
- **Instructor.** 어떤 LLM이든 감싸는 Pydantic 기반 래퍼. 검증 실패 시 재시도합니다. 벤더에 구애받지 않지만 로짓을 수정하지는 않습니다 — 재시도 + 구조화 출력 인지 프롬프트에 의존합니다.

### 직관에 어긋나는 결과

제약 디코딩은 제약 없는 생성보다 종종 더 *빠릅니다*. 이유는 둘입니다. 첫째, 다음 토큰 탐색 공간을 줄입니다. 둘째, 영리한 구현은 강제된 토큰에 대해서는 토큰 생성을 아예 건너뜁니다(`{"name": "` 같은 비계(scaffolding)는 모든 바이트가 정해져 있으니까요).

### 비용을 치르게 되는 함정

필드 순서가 중요합니다. `answer`를 `reasoning`보다 앞에 두면, 모델은 생각하기 전에 답을 먼저 확정해 버립니다. JSON은 유효합니다. 답은 틀립니다. 어떤 검증도 이걸 잡지 못합니다.

```json
// 나쁜 예
{"answer": "yes", "reasoning": "because ..."}

// 좋은 예
{"reasoning": "... therefore ...", "answer": "yes"}
```

스키마 필드 순서는 포맷팅이 아니라 로직입니다.

```figure
constrained-decoder
```

## 만들어 보기

### 단계 1: 밑바닥부터 정규식 제약 생성 만들기

독립 실행형 FSM 구현은 `code/main.py`를 보세요. 30줄로 압축한 핵심 아이디어:

```python
def mask_logits(logits, valid_token_ids):
    mask = [float("-inf")] * len(logits)
    for tid in valid_token_ids:
        mask[tid] = logits[tid]
    return mask


def generate_constrained(model, tokenizer, prompt, fsm):
    ids = tokenizer.encode(prompt)
    state = fsm.initial_state
    while not fsm.is_accept(state):
        logits = model.next_token_logits(ids)
        valid = fsm.valid_tokens(state, tokenizer)
        logits = mask_logits(logits, valid)
        tok = sample(logits)
        ids.append(tok)
        state = fsm.transition(state, tok)
    return tokenizer.decode(ids)
```

FSM은 문법의 어느 부분까지 충족했는지 추적합니다. `valid_tokens(state, tokenizer)`는 어떤 어휘 토큰이 수용 경로를 벗어나지 않고 FSM을 전진시킬 수 있는지 계산합니다.

### 단계 2: JSON Schema를 위한 Outlines

```python
from pydantic import BaseModel
from typing import Literal
import outlines


class Review(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float
    evidence_span: str


model = outlines.models.transformers("meta-llama/Llama-3.2-3B-Instruct")
generator = outlines.generate.json(model, Review)

result = generator("Classify: 'The wait staff was attentive and the food arrived hot.'")
print(result)
# Review(sentiment='positive', confidence=0.93, evidence_span='attentive ... hot')
```

검증 오류 0개입니다. 항상요. FSM이 유효하지 않은 출력을 도달할 수 없는 상태로 만듭니다.

### 단계 3: 벤더에 구애받지 않는 Pydantic을 위한 Instructor

```python
import instructor
from anthropic import Anthropic
from pydantic import BaseModel, Field


class Invoice(BaseModel):
    vendor: str
    total_usd: float = Field(ge=0)
    line_items: list[str]


client = instructor.from_anthropic(Anthropic())
invoice = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    response_model=Invoice,
    messages=[{"role": "user", "content": "Extract from: 'Acme Corp $420. Widget, Gizmo.'"}],
)
```

다른 메커니즘입니다. Instructor는 로짓을 건드리지 않습니다. 스키마를 프롬프트에 넣고, 출력을 파싱하고, 검증 실패 시 재시도합니다(기본 3회). 어떤 벤더와도 동작합니다. 재시도는 지연 시간과 비용을 더합니다. 벤더 불문 이식성이 판매 포인트입니다.

### 단계 4: 네이티브 벤더 API

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-5",
    input=[{"role": "user", "content": "Classify: 'The food was cold.'"}],
    text={"format": {"type": "json_schema", "name": "sentiment",
          "schema": {"type": "object", "required": ["sentiment"],
                     "properties": {"sentiment": {"type": "string",
                                                  "enum": ["positive", "negative", "neutral"]}}}}},
)
print(response.output_parsed)
```

서버 측 제약 디코딩입니다. 지원되는 스키마에서는 Outlines와 신뢰성이 동등합니다. 로컬 모델 관리가 필요 없습니다. 벤더에 묶이게 됩니다.

## 함정들

- **재귀 스키마.** Outlines는 재귀를 고정 깊이로 평탄화합니다. 트리 구조 출력(중첩 댓글, AST)에는 XGrammar나 llguidance(CFG 기반)가 필요합니다.
- **거대한 열거형.** 옵션 10,000개짜리 enum은 컴파일이 느리거나 시간 초과됩니다. 리트리버로 전환하세요: 먼저 상위 k 후보를 예측하고, 그것들로만 제약을 겁니다.
- **지나치게 엄격한 문법.** `date: "YYYY-MM-DD"` 정규식을 강제하면 모델은 빠진 날짜에 대해 "unknown"을 출력할 수 없습니다. 모델은 날짜를 지어내면서 보상합니다. `null`이나 센티널 값을 허용하세요.
- **조숙한 확정.** 위의 필드 순서 함정을 보세요. 추론을 항상 앞에 두세요.
- **스키마 없는 벤더 JSON 모드.** 순수 JSON 모드는 유효한 JSON만 보장하지, *여러분의 용도에* 유효하다는 건 보장하지 않습니다. 항상 전체 스키마를 제공하세요.

## 사용해 보기

2026년 스택:

| 상황 | 선택 |
|-----------|------|
| OpenAI/Anthropic/Google 모델, 단순 스키마 | 네이티브 벤더 구조화 출력 |
| 어떤 벤더든, Pydantic 워크플로, 재시도를 견딜 수 있음 | Instructor |
| 로컬 모델, 100% 유효성 필요, 평면적 스키마 | Outlines (FSM) |
| 로컬 모델, 재귀 스키마 | XGrammar 또는 llguidance |
| 셀프 호스팅 추론 서버 | vLLM guided decoding |
| 배치 처리, 재시도 가능 | Instructor + 가장 싼 모델 |

## 출시하기

`outputs/skill-structured-output-picker.md`로 저장하세요:

```markdown
---
name: structured-output-picker
description: 구조화 출력 접근법, 스키마 설계, 검증 계획 고르기.
version: 1.0.0
phase: 5
lesson: 20
tags: [nlp, llm, structured-output]
---

사용 사례(벤더, 지연 시간 예산, 스키마 복잡도, 실패 허용도)가 주어지면 다음을 출력하세요:

1. 메커니즘. 네이티브 벤더 구조화 출력, Instructor 재시도, Outlines FSM, 또는 XGrammar CFG. 한 문장 근거.
2. 스키마 설계. 필드 순서(추론 먼저, 답 마지막), "unknown"을 위한 nullable 필드, enum vs 정규식, 필수 필드.
3. 실패 전략. 최대 재시도 횟수, 폴백 모델, 우아한 `null` 처리, 분포 외 입력 거부.
4. 검증 계획. 스키마 준수율(목표 100%), 의미적 유효성(LLM 심판), 필드 커버리지율, 지연 시간 p50/p99.

`answer`나 `decision`을 추론 필드보다 앞에 두는 설계는 받아들이지 마세요. 스키마 없이 맨바닥 JSON 모드를 쓰는 방안은 받아들이지 마세요. FSM 전용 라이브러리 뒤에 재귀 스키마를 두는 안은 표시하세요.
```

## 연습 문제

1. **쉬움.** 작은 오픈 웨이트 모델(예: Llama-3.2-3B)에게 제약 디코딩 없이 `Review(sentiment, confidence, evidence_span)`을 프롬프트로 요구하세요. 리뷰 100개에서 유효한 JSON으로 파싱되는 비율을 측정하세요.
2. **중간.** 같은 코퍼스를 Outlines JSON 모드로 처리하세요. 준수율, 지연 시간, 의미적 정확도를 비교하세요.
3. **어려움.** 전화번호(`\d{3}-\d{3}-\d{4}`)를 위한 정규식 제약 디코더를 밑바닥부터 구현하세요. 샘플 1,000개에서 유효하지 않은 출력이 0개임을 검증하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| 제약 디코딩 | 유효한 출력 강제 | 매 생성 단계에서 유효하지 않은 토큰의 로짓을 마스킹. |
| 로짓 프로세서 | 제약을 거는 그것 | 함수: `(logits, state) -> masked_logits`. |
| FSM | 유한 상태 기계 | 컴파일된 문법 표현; O(1) 유효 다음 토큰 룩업. |
| CFG | 문맥 자유 문법 | 재귀를 처리하는 문법; FSM보다 느리지만 표현력이 더 높음. |
| 스키마 필드 순서 | 중요한가? | 중요함 — 첫 필드가 확정을 만들고, 항상 추론을 답보다 앞에 둘 것. |
| Guided decoding | vLLM에서 부르는 이름 | 같은 개념을 추론 서버에 통합한 것. |
| JSON 모드 | OpenAI의 초기 버전 | JSON 문법은 보장하지만 스키마 일치는 보장하지 않음. |

## 더 읽을거리

- [Willard, Louf (2023). Efficient Guided Generation for LLMs](https://arxiv.org/abs/2307.09702) — Outlines 원 논문.
- [XGrammar paper (2024)](https://arxiv.org/abs/2411.15100) — 빠른 CFG 기반 제약 디코딩.
- [vLLM — Structured Outputs](https://docs.vllm.ai/en/latest/features/structured_outputs.html) — 추론 서버 통합.
- [OpenAI — Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs) — API 레퍼런스 + 함정들.
- [Instructor library](https://python.useinstructor.com/) — 벤더 불문 Pydantic + 재시도.
- [JSONSchemaBench (2025)](https://arxiv.org/abs/2501.10868) — 제약 디코딩 프레임워크 6개 벤치마크.
