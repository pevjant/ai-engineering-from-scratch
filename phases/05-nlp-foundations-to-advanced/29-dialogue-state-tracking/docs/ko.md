# 대화 상태 추적 (Dialogue State Tracking)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> "북쪽에 싼 식당 원해요... 아니, 그냥 적당한 가격으로... 그리고 이탈리안 추가요." 세 턴, 세 번의 상태 갱신. DST가 슬롯-값 딕셔너리를 정확히 맞춰 줘야 예약이 제대로 됩니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 17(챗봇), 페이즈 5 · 20(구조화 출력)
**소요 시간:** 약 75분

## 문제 상황

작업 지향(task-oriented) 대화 시스템에서 사용자의 목표는 슬롯-값 쌍의 집합으로 인코딩됩니다: `{cuisine: italian, area: north, price: moderate}`. 사용자의 모든 턴은 슬롯을 추가하거나, 바꾸거나, 없앨 수 있습니다. 시스템은 대화 전체를 읽고 현재 상태를 정확히 출력해야 합니다.

슬롯 하나만 틀려도 시스템은 엉뚱한 식당을 예약하고, 엉뚱한 항공편을 잡고, 엉뚱한 카드에 결제합니다. DST는 사용자가 말한 것과 백엔드가 실행할 것을 잇는 경첩입니다.

LLM이 있는 2026년에도 여전히 중요한 이유:

- 컴플라이언스에 민감한 도메인(은행, 의료, 항공 예약)은 자유 형식 생성이 아니라 결정론적인 슬롯 값을 요구합니다.
- 도구 사용 에이전트도 API를 호출하기 전에 슬롯 해석이 필요합니다.
- 멀티턴 정정은 보기보다 어렵습니다: "아니다, 목요일로 해 줘."

현대의 파이프라인: 고전적 DST 개념 + LLM 추출기 + 구조화 출력 가드레일.

## 개념

![DST: 대화 이력 → 슬롯-값 상태](../assets/dst.svg)

**과제 구조.** 스키마는 도메인(restaurant, hotel, taxi)과 그 슬롯들(cuisine, area, price, people)을 정의합니다. 각 슬롯은 비어 있거나, 닫힌 집합에서 값을 취하거나(price: {cheap, moderate, expensive}), 자유 형식 값(name: "The Copper Kettle")일 수 있습니다.

**DST의 두 가지 정식화.**

- **분류.** 각 (슬롯, 후보 값) 쌍에 대해 예/아니오를 예측합니다. 폐쇄 어휘 슬롯에 적합합니다. 2020년 이전의 표준.
- **생성.** 대화가 주어지면 슬롯 값을 자유 텍스트로 생성합니다. 개방 어휘 슬롯에 적합합니다. 현대의 기본값.

**지표.** Joint Goal Accuracy(JGA) — *모든* 슬롯이 맞은 턴의 비율입니다. 전부 아니면 전무. MultiWOZ 2.4 리더보드는 2026년 기준 약 83%가 최고 수준입니다.

**아키텍처.**

1. **규칙 기반(슬롯 정규식 + 키워드).** 좁은 도메인에서 강력한 베이스라인. 디버깅이 쉽습니다.
2. **TripPy / BERT-DST.** BERT 인코딩에 복사 기반 생성을 얹은 방식. LLM 이전의 표준.
3. **LDST(LLaMA + LoRA).** 도메인-슬롯 프롬프팅을 적용한 지시 튜닝 LLM. MultiWOZ 2.4에서 ChatGPT급 품질에 도달합니다.
4. **온톨로지 프리(2024–26).** 스키마를 생략하고 슬롯 이름과 값을 직접 생성합니다. 열린 도메인을 다룹니다.
5. **프롬프트 + 구조화 출력(2024–26).** Pydantic 스키마 + 제약 디코딩을 쓰는 LLM. 코드 5줄로 프로덕션 준비 완료.

### 고전적인 실패 양상

- **턴에 걸친 상호 참조.** "첫 번째 옵션으로 할게요." 어떤 옵션인지 풀어야 합니다.
- **덮어쓰기 vs 추가.** 사용자가 "이탈리안 추가요"라고 합니다. cuisine을 교체할까요, 추가할까요?
- **암묵적 확인.** "네 좋아요" — 제안된 예약을 수락한 걸까요?
- **정정.** "아, 7시로 바꿔 줘." 다른 슬롯을 지우지 않고 시간만 갱신해야 합니다.
- **시스템 발화에 대한 참조.** "네, 그걸로요." "그게"가 뭘까요?

```figure
n5-slot-tracker
```

## 직접 만들기

### 단계 1: 규칙 기반 슬롯 추출기

`code/main.py`를 보세요. 정규식 + 동의어 사전이 좁은 도메인의 표준 발화 70%를 커버합니다:

```python
CUISINE_SYNONYMS = {
    "italian": ["italian", "pasta", "pizza", "italy"],
    "chinese": ["chinese", "chow mein", "noodles"],
}


def extract_cuisine(utterance):
    for canonical, synonyms in CUISINE_SYNONYMS.items():
        if any(syn in utterance.lower() for syn in synonyms):
            return canonical
    return None
```

표준 어휘 밖에서는 깨지기 쉽습니다. 결정론적인 슬롯 확인에는 유용합니다.

### 단계 2: 상태 갱신 루프

```python
def update_state(state, utterance):
    new_state = dict(state)
    for slot, extractor in SLOT_EXTRACTORS.items():
        value = extractor(utterance)
        if value is not None:
            new_state[slot] = value
    for slot in NEGATION_CLEARS:
        if is_negated(utterance, slot):
            new_state[slot] = None
    return new_state
```

세 가지 불변 조건:

- 사용자가 건드리지 않은 슬롯은 절대 리셋하지 않는다.
- 명시적 부정("cuisine은 그냥 무시해")은 반드시 지운다.
- 사용자 정정("아니었고...")은 추가가 아니라 반드시 덮어쓴다.

### 단계 3: 구조화 출력을 쓰는 LLM 기반 DST

```python
from pydantic import BaseModel
from typing import Literal, Optional
import instructor

class RestaurantState(BaseModel):
    cuisine: Optional[Literal["italian", "chinese", "indian", "thai", "any"]] = None
    area: Optional[Literal["north", "south", "east", "west", "center"]] = None
    price: Optional[Literal["cheap", "moderate", "expensive"]] = None
    people: Optional[int] = None
    day: Optional[str] = None


def llm_dst(history, llm):
    prompt = f"""You track the slot values of a restaurant booking across turns.
Dialogue so far:
{render(history)}

Update the state based on the latest user turn. Output only the JSON state."""
    return llm(prompt, response_model=RestaurantState)
```

Instructor + Pydantic이 유효한 상태 객체를 보장합니다. 정규식도, 스키마 불일치도, 환각된 슬롯도 없습니다.

### 단계 4: JGA 평가

```python
def joint_goal_accuracy(predicted_states, gold_states):
    correct = sum(1 for p, g in zip(predicted_states, gold_states) if p == g)
    return correct / len(predicted_states)
```

보정: 시스템이 모든 슬롯을 맞추는 턴은 몇 퍼센트인가? MultiWOZ 2.4 기준 2026년 최고 시스템은 80~83%입니다. 여러분의 도메인 시스템이 좁은 어휘에서도 이 수준을 못 넘는다면 LLM 베이스라인이 여러분을 이깁니다.

### 단계 5: 정정 처리

```python
CORRECTION_CUES = {"actually", "no wait", "on second thought", "change that to"}


def is_correction(utterance):
    return any(cue in utterance.lower() for cue in CORRECTION_CUES)
```

정정이 감지되면 추가하지 말고 마지막으로 갱신된 슬롯을 덮어쓰세요. LLM 도움 없이 정확히 하기는 어렵습니다. 현대의 패턴: 증분 갱신 대신 항상 LLM이 이력 전체에서 상태를 처음부터 다시 생성하게 하는 것 — 이렇게 하면 정정이 자연스럽게 처리됩니다.

## 흔한 실수

- **전체 이력 재생성 비용.** 매 턴 LLM이 상태를 다시 생성하게 하면 총 토큰이 O(n²)로 늘어납니다. 이력 길이를 제한하거나 오래된 턴을 요약하세요.
- **스키마 드리프트.** 나중에 슬롯을 추가하면 기존 학습 데이터가 깨집니다. 스키마에 버전을 다세요.
- **대소문자 구분.** "Italian" vs "italian" vs "ITALIAN" — 어디서든 정규화하세요.
- **암묵적 상속.** 사용자가 앞서 "4명이서"라고 했다면, 시간을 바꾸는 새 요청이 people을 지워서는 안 됩니다. 항상 전체 이력을 넘기세요.
- **자유 형식 vs 닫힌 집합.** 이름, 시간, 주소는 자유 형식 슬롯이 필요하고, 요리 종류와 지역은 닫힌 집합입니다. 스키마에 둘 다 섞으세요.

## 활용하기

2026년의 표준 스택:

| 상황 | 접근법 |
|-----------|----------|
| 좁은 도메인(인텐트 한두 개) | 규칙 기반 + 정규식 |
| 넓은 도메인, 레이블 데이터 있음 | LDST (MultiWOZ 스타일 데이터로 LLaMA + LoRA) |
| 넓은 도메인, 레이블 없음, 프로덕션 준비 | LLM + Instructor + Pydantic 스키마 |
| 음성 / 보이스 | ASR + 정규화기 + LLM-DST |
| 다중 도메인 예약 흐름 | 도메인별 Pydantic 모델을 쓰는 스키마 안내형 LLM |
| 컴플라이언스 민감 | 규칙 기반 주력 + 확인 흐름을 갖춘 LLM 폴백 |

## 출시하기

`outputs/skill-dst-designer.md`로 저장하세요:

```markdown
---
name: dst-designer
description: Design a dialogue state tracker — schema, extractor, update policy, evaluation.
version: 1.0.0
phase: 5
lesson: 29
tags: [nlp, dialogue, task-oriented]
---

사용 사례(도메인, 언어, 어휘 개방성, 컴플라이언스 요건)가 주어지면 다음을 출력합니다:

1. 스키마. 도메인 목록, 도메인별 슬롯, 슬롯별 개방형/폐쇄형 어휘 여부.
2. 추출기. 규칙 기반 / seq2seq / LLM+Pydantic. 근거를 제시합니다.
3. 갱신 정책. 상태 전체 재생성 / 증분 방식; 정정 처리; 부정(negation) 처리.
4. 평가. 홀드아웃 대화 셋에서 Joint Goal Accuracy, 슬롯 수준 정밀도/재현율, 가장 어려운 슬롯의 혼동(confusion).
5. 확인 흐름. 사용자에게 명시적으로 확인을 요청하는 시점(파괴적 작업, 낮은 신뢰도 추출).

컴플라이언스에 민감한 슬롯에 규칙 기반 2차 검사 없이 LLM 전용 DST를 쓰는 것은 거부합니다. 사용자 정정 시 슬롯을 되돌릴(rollback) 수 없는 DST는 거부합니다. 버전 태그 없는 스키마는 경고를 표시합니다.
```

## 연습 문제

1. **쉬움.** `code/main.py`의 규칙 기반 상태 추적기를 슬롯 3개(cuisine, area, price)용으로 만들어 보세요. 직접 만든 대화 10개로 테스트하고 JGA를 측정하세요.
2. **보통.** 같은 데이터셋에 Instructor + Pydantic + 작은 LLM을 적용해 보세요. JGA를 비교하고 가장 어려운 턴을 살펴 보세요.
3. **어려움.** 두 방식을 모두 구현하고 라우팅해 보세요: 규칙 기반 주력, 규칙 기반이 신뢰도 낮은 슬롯을 2개 미만 출력하면 LLM 폴백. 결합 JGA와 턴당 추론 비용을 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| DST | 대화 상태 추적 | 대화 턴에 걸쳐 슬롯-값 딕셔너리를 유지함. |
| 슬롯 | 사용자 의도의 단위 | 백엔드가 필요로 하는 이름 붙은 파라미터(cuisine, date). |
| 도메인 | 작업 영역 | restaurant, hotel, taxi — 슬롯들의 집합. |
| JGA | Joint Goal Accuracy | 모든 슬롯이 맞은 턴의 비율. 전부 아니면 전무. |
| MultiWOZ | 그 벤치마크 | 다중 도메인 WOZ 데이터셋; 표준 DST 평가. |
| 온톨로지 프리 DST | 스키마 없음 | 슬롯 이름과 값을 고정 목록 없이 직접 생성. |
| 정정(Correction) | "아니었고..." | 이미 채워진 슬롯을 덮어쓰는 턴. |

## 더 읽을거리

- [Budzianowski et al. (2018). MultiWOZ — A Large-Scale Multi-Domain Wizard-of-Oz](https://arxiv.org/abs/1810.00278) — 표준 벤치마크.
- [Feng et al. (2023). Towards LLM-driven Dialogue State Tracking (LDST)](https://arxiv.org/abs/2310.14970) — DST를 위한 LLaMA + LoRA 지시 튜닝.
- [Heck et al. (2020). TripPy — A Triple Copy Strategy for Value Independent Neural Dialog State Tracking](https://arxiv.org/abs/2005.02877) — 복사 기반 DST 주력 모델.
- [King, Flanigan (2024). Unsupervised End-to-End Task-Oriented Dialogue with LLMs](https://arxiv.org/abs/2404.10753) — EM 기반 비지도 TOD.
- [MultiWOZ 리더보드](https://github.com/budzianowski/multiwoz) — 표준 DST 결과.
