> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 프롬프트 캐싱과 컨텍스트 캐싱

> 시스템 프롬프트가 4,000토큰이고 RAG 컨텍스트가 20,000토큰입니다. 둘 다 매 요청마다 전송하고, 둘 다 매번 요금을 냅니다. 프롬프트 캐싱을 쓰면 제공사가 그 접두사를 자기 쪽에 따뜻하게(웜 상태로) 유지해 주고, 재사용할 때는 정상 요금의 10%만 청구합니다. 제대로 쓰면 추론 비용을 50~90%, 첫 토큰 지연 시간을 40~85% 줄일 수 있습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 11 · 01(프롬프트 엔지니어링), 페이즈 11 · 05(컨텍스트 엔지니어링), 페이즈 11 · 11(캐싱과 비용)
**소요 시간:** 약 60분

## 문제 상황

코딩 에이전트가 대화의 매 턴마다 똑같은 15,000토큰짜리 시스템 프롬프트를 Claude에 보냅니다. 입력 토큰 100만 개당 $3라면 20턴에서 입력 비용만 $0.90입니다. 사용자가 실제로 뭔가를 말하기도 전에요. 여기에 하루 10,000건의 대화를 곱하면, 한 번도 바뀌지 않는 텍스트에 하루 $9,000이 청구됩니다.

품질을 해치지 않고 프롬프트를 줄일 수는 없습니다. 보내지 않을 수도 없습니다. 모델은 매 턴 이 프롬프트가 필요하니까요. 유일한 방법은 제공사가 이미 한 번 본 접두사에 정가를 지불하는 것을 그만두는 것입니다.

그 방법이 프롬프트 캐싱입니다. Anthropic은 2024년 8월에 출시했고(2025년에는 1시간 연장 TTL 변형 추가), OpenAI는 그해 말에 자동화했으며, Google은 Gemini 1.5와 함께 명시적 컨텍스트 캐싱을 내놓았습니다. 이제 세 곳 모두 최신 모델에서 일급 기능으로 제공합니다.

## 개념

![프롬프트 캐싱: 한 번 쓰고, 싸게 읽기](../assets/prompt-caching.svg)

**동작 원리.** 요청의 접두사가 최근 요청의 것과 일치하면, 제공사는 토큰을 다시 인코딩하는 대신 이전 실행의 KV-캐시를 그대로 사용합니다. 처음에는 약간의 쓰기 추가 요금을 내고, 그다음부터는 매번 큰 읽기 할인을 받습니다.

**2026년 기준 세 가지 제공사 방식.**

| 제공사 | API 스타일 | 캐시 히트 할인 | 쓰기 추가 요금 | 기본 TTL | 캐시 가능 최소 크기 |
|---------|-----------|--------------|---------------|-------------|---------------|
| Anthropic | 콘텐츠 블록에 명시적인 `cache_control` 마커 | 입력 90% 할인 | 25% 추가 요금 | 5분(1시간으로 연장 가능) | 1,024토큰(Sonnet/Opus), 2,048(Haiku) |
| OpenAI | 자동 접두사 감지 | 입력 50% 할인 | 없음 | 최대 1시간(최선 노력) | 1,024토큰 |
| Google (Gemini) | 명시적 `CachedContent` API | 스토리지 과금, 읽기는 정상가의 약 25% | 토큰·시간당 스토리지 요금 | 사용자 지정(기본 1시간) | 4,096토큰(Flash), 32,768(Pro) |

**불변의 법칙.** 세 제공사 모두 접두사만 캐시합니다. 요청 사이에 토큰 하나라도 다르면, 처음으로 달라진 토큰 뒤의 모든 것은 캐시 미스입니다. *안정적인* 부분은 위에, *변하는* 부분은 아래에 배치하세요.

### 캐시에 친화적인 배치

```
[시스템 프롬프트]          <-- 캐시할 부분
[도구 정의]               <-- 캐시할 부분
[few-shot 예시]           <-- 캐시할 부분
[검색된 문서]             <-- 재사용된다면 캐시, 아니면 안 함
[대화 기록]               <-- 마지막 턴까지 캐시
[현재 사용자 메시지]       <-- 절대 캐시 금지(매번 다름)
```

이 순서를 어기면(사용자 메시지를 시스템 프롬프트 위에 놓거나, few-shot 예시 사이에 매번 달라지는 검색 결과를 끼워 넣으면) 캐시는 절대 적중하지 않습니다.

### 손익분기 계산

Anthropic의 25% 쓰기 추가 요금 때문에 캐시된 블록은 최소 두 번은 읽혀야 돈이 아낌니다. 쓰기 1회 + 읽기 1회면 요청당 평균 비용이 0.675배(32% 절약), 쓰기 1회 + 읽기 10회면 평균 0.205배(80% 절약)입니다. 경험 법칙: TTL 안에서 최소 3회 이상 재사용할 것이라 예상되는 내용은 전부 캐시하세요.

```figure
prompt-cache-hit
```

## 직접 만들어 보기

### 단계 1: 명시적 마커를 사용하는 Anthropic 프롬프트 캐싱

```python
import anthropic

client = anthropic.Anthropic()

SYSTEM = [
    {
        "type": "text",
        "text": "You are a senior Python reviewer. Follow the rubric exactly.\n\n" + RUBRIC_15K_TOKENS,
        "cache_control": {"type": "ephemeral"},
    }
]

def review(code: str):
    return client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": code}],
    )
```

`cache_control` 마커는 해당 블록을 5분간 저장하라고 Anthropic에 알려 줍니다. 그 시간 안에 재사용하면 히트하고, 만료 뒤에 재사용하면 만료되었다가 다시 씁니다.

**응답 usage 필드:**

```python
response = review(code_a)
response.usage
# InputTokensUsage(
#     input_tokens=120,
#     cache_creation_input_tokens=15023,   # 1.25배 과금
#     cache_read_input_tokens=0,
#     output_tokens=340,
# )

response_b = review(code_b)
response_b.usage
# cache_creation_input_tokens=0
# cache_read_input_tokens=15023           # 0.1배 과금
```

두 필드를 모두 CI에서 확인하세요. 요청마다 `cache_read_input_tokens`가 계속 0이라면 캐시 키가 계속 흔들리고 있다는 뜻입니다.

### 단계 2: 1시간 연장 TTL

오래 도는 배치 작업에서는 기본값인 5분이 작업 사이에 만료됩니다. `ttl`을 지정하세요:

```python
{"type": "text", "text": RUBRIC, "cache_control": {"type": "ephemeral", "ttl": "1h"}}
```

1시간 TTL은 쓰기 추가 요금이 2배입니다(기준 대비 25% 대신 50%). 하지만 접두사를 5번 넘게 재사용하는 배치라면 금방 본전을 뽑습니다.

### 단계 3: OpenAI 자동 캐싱

OpenAI는 설정할 것이 하나도 없습니다. 최근 요청과 일치하는 1,024토큰이 넘는 접두사에는 자동으로 50% 할인이 적용됩니다.

```python
from openai import OpenAI
client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},   # 길고 안정적인 프롬프트
        {"role": "user", "content": user_msg},
    ],
)
resp.usage.prompt_tokens_details.cached_tokens  # 할인이 적용되는 부분
```

캐시에 친화적인 배치 규칙은 여기도 똑같이 적용됩니다. 단, Anthropic에는 해당 없지만 OpenAI 캐시를 깨뜨리는 두 가지가 있습니다. `user` 필드를 바꾸는 것(캐시 키 구성 요소로 쓰임)과 도구 순서를 바꾸는 것입니다.

### 단계 4: Gemini 명시적 컨텍스트 캐싱

Gemini는 캐시를 직접 만들고 이름을 붙이는 일급 객체로 취급합니다:

```python
from google import genai
from google.genai import types

client = genai.Client()

cache = client.caches.create(
    model="gemini-3-pro",
    config=types.CreateCachedContentConfig(
        display_name="rubric-v3",
        system_instruction=RUBRIC,
        contents=[FEW_SHOT_EXAMPLES],
        ttl="3600s",
    ),
)

resp = client.models.generate_content(
    model="gemini-3-pro",
    contents=["Review this code:\n" + code],
    config=types.GenerateContentConfig(cached_content=cache.name),
)
```

Gemini는 캐시가 살아 있는 동안 토큰·시간당 스토리지 요금을 청구하고, 읽기는 정상 입력 요금의 약 25%입니다. 며칠에 걸쳐 여러 세션에서 같은 거대한 프롬프트를 재사용할 때 알맞은 방식입니다.

### 단계 5: 프로덕션에서 히트율 측정하기

`code/main.py`에는 세 제공사의 쓰기/읽기/미스 횟수를 추적하고 1,000건 요청당 혼합 비용을 계산하는 시뮬레이션 회계사가 들어 있습니다. 배포는 목표 히트율을 기준으로 판단하세요. 대부분의 프로덕션(운영 환경) Anthropic 구성은 워밍업 후 읽기 비율이 80%를 넘어야 합니다.

## 2026년에도 여전히 출시되는 함정들

- **맨 위의 동적 타임스탬프.** 시스템 프롬프트 맨 위에 `"Current time: 2026-04-22 15:30:02"` 같은 문구를 넣으면 매 요청이 미스입니다. 타임스탬프는 캐시 중단점 아래로 내리세요.
- **도구 순서 변경.** 도구는 안정적인 순서로 직렬화하세요. 배포 사이에 dict 순서가 뒤섞이면 모든 히트가 깨집니다.
- **자유 텍스트의 근사 중복.** "You are helpful."과 "You are a helpful assistant." — 한 바이트 차이 = 완전한 미스.
- **너무 작은 블록.** Anthropic은 1,024토큰 하한(Haiku는 2,048)을 강제합니다. 그보다 작은 블록은 아무 말 없이 캐시되지 않습니다.
- **비용 대시보드를 통째로 보기.** "입력 토큰"을 캐시됨/캐시 안 됨으로 나눠 보세요. 그렇지 않으면 트래픽 감소가 캐시 효과처럼 보입니다.

## 사용해 보기

2026년 캐싱 선택 가이드:

| 상황 | 선택 |
|-----------|------|
| 안정적인 10k+ 시스템 프롬프트를 쓰는 여러 턴짜리 에이전트 | 5분 TTL의 Anthropic `cache_control` |
| 30분 이상 같은 접두사를 재사용하는 배치 작업 | `ttl: "1h"`를 쓰는 Anthropic |
| GPT-5의 서버리스 엔드포인트, 별도 인프라 없음 | OpenAI 자동(접두사를 길고 안정적으로만 유지하면 됨) |
| 거대한 코드/문서 코퍼스를 며칠에 걸쳐 재사용 | Gemini 명시적 `CachedContent` |
| 여러 제공사 간 폴백 | 캐시 가능한 접두사 배치를 제공사마다 똑같이 유지해 어느 쪽 히트든 작동하게 |

사용자 메시지 계층에는 시맨틱 캐싱(페이즈 11 · 11)과 결합하세요. 프롬프트 캐싱은 *토큰이 동일한* 재사용을, 시맨틱 캐싱은 *의미가 동일한* 재사용을 처리합니다.

## 출시하기

다음 내용을 `outputs/skill-prompt-caching-planner.md`로 저장합니다:

```markdown
---
name: prompt-caching-planner
description: 캐시에 친화적인 프롬프트 배치를 설계하고 올바른 제공사 캐싱 모드를 고른다
version: 1.0.0
phase: 11
lesson: 15
tags: [llm-engineering, caching, cost]
---

프롬프트(시스템 + 도구 + few-shot + 검색 + 대화 기록 + 사용자)와 사용 패턴(시간당 요청 수, 필요한 TTL, 제공사)이 주어지면 다음을 출력합니다:

1. 배치. 캐시 중단점 하나를 표시해 섹션 순서를 재배치합니다. 어떤 섹션이 안정적이고 어떤 섹션이 변동적인지 설명합니다.
2. 제공사 모드. Anthropic cache_control, OpenAI 자동, 또는 Gemini CachedContent 중 고르고, TTL과 재사용 패턴을 근거로 정당화합니다.
3. 손익분기. TTL 안의 쓰기당 예상 읽기 횟수. 계산 과정과 함께 캐시 없음 대비 순비용을 제시합니다.
4. 검증 계획. 동일한 두 번째 요청에서 cache_read_input_tokens > 0임을 확인하는 CI 어설션. 캐시됨/캐시 안 됨 토큰으로 나눈 대시보드.
5. 실패 모드. 이 구성에서 캐시 미스가 날 가장 가능성 높은 세 가지 이유(동적 타임스탬프, 도구 재정렬, 근사 중복 텍스트)와 각각의 예방 방법을 나열합니다.

동적 필드를 중단점 위에 두는 캐시 계획은 출시를 거부합니다. 2배 쓰기 추가 요금을 복구할 만한 재사용 횟수 없이 1시간 TTL을 켜는 것도 거부합니다.
```

## 연습 문제

1. **쉬움.** Claude를 상대로 5,000토큰짜리 시스템 프롬프트를 쓰는 10턴 대화를 진행합니다. `cache_control` 없이 한 번, 넣어서 한 번 실행하고 각각의 입력 토큰 청구액을 보고합니다.
2. **보통.** 프롬프트 템플릿과 요청 로그가 주어지면 제공사별(Anthropic 5분, Anthropic 1시간, OpenAI 자동, Gemini 명시적) 예상 히트율과 절감액(달러)을 계산하는 테스트 하네스를 작성합니다.
3. **어려움.** 배치 최적화기를 만듭니다. 프롬프트와 `stable=True/False`로 표시된 필드 목록이 주어지면, 정보를 잃지 않으면서 캐시 중단점 하나를 가장 캐시에 유리한 최대 위치에 놓도록 프롬프트를 다시 씁니다. 실제 Anthropic 엔드포인트에서 검증합니다.

## 핵심 용어

| 용어 | 흔히 하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| 프롬프트 캐싱 | "긴 프롬프트를 싸게 만든다" | 일치하는 접두사에 제공사 쪽 KV-캐시를 재사용. 반복 입력 토큰에 50~90% 할인. |
| `cache_control` | "Anthropic 마커" | "여기까지는 캐시 가능"이라고 선언하는 콘텐츠 블록 속성. `{"type": "ephemeral"}`. |
| 캐시 쓰기 | "추가 요금 내기" | 캐시를 처음 채우는 요청. Anthropic에서는 입력 요금의 약 1.25배, OpenAI는 무료. |
| 캐시 읽기 | "할인" | 접두사가 일치하는 이후 요청. Anthropic 10%, OpenAI 50%, Gemini 약 25% 과금. |
| TTL | "얼마나 사나" | 캐시가 따뜻하게 유지되는 시간(초). Anthropic 기본 5분(1시간 연장 가능), OpenAI 최선 노력 최대 1시간, Gemini 사용자 지정. |
| 연장 TTL | "1시간 Anthropic 캐시" | `{"type": "ephemeral", "ttl": "1h"}`. 쓰기 추가 요금 2배지만 배치 재사용에는 값어치가 있음. |
| 접두사 일치 | "캐시가 왜 미스였지" | 시작부터 중단점까지 모든 토큰이 바이트 단위로 동일해야만 캐시가 히트함. |
| 컨텍스트 캐싱(Gemini) | "명시적 방식" | Google의 이름을 붙이는 스토리지 과금 캐시 객체. 대형 코퍼스를 며칠에 걸쳐 재사용할 때 최적. |

## 더 읽을거리

- [Anthropic — 프롬프트 캐싱](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — `cache_control`, 1시간 TTL, 손익분기 표.
- [OpenAI — 프롬프트 캐싱](https://platform.openai.com/docs/guides/prompt-caching) — 자동 접두사 일치.
- [Google — 컨텍스트 캐싱](https://ai.google.dev/gemini-api/docs/caching) — `CachedContent` API와 스토리지 가격.
- [Anthropic 엔지니어링 — 긴 컨텍스트 워크로드를 위한 프롬프트 캐싱](https://www.anthropic.com/news/prompt-caching) — 지연 시간 수치가 담긴 최초 출시 소식.
- 페이즈 11 · 05(컨텍스트 엔지니어링) — 캐시가 적중하도록 프롬프트를 자르는 위치.
- 페이즈 11 · 11(캐싱과 비용) — 사용자 메시지에는 프롬프트 캐싱과 시맨틱 캐시를 짝지어 쓰기.
- [Pope et al., "Efficiently Scaling Transformer Inference" (2022)](https://arxiv.org/abs/2211.05102) — 프롬프트 캐싱이 사용자에게 노출하는 KV-캐시 메모리 모델. 캐시된 접두사를 재계산하는 것보다 다시 읽는 것이 약 10배 싼 이유를 설명합니다.
- [Agrawal et al., "SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills" (2023)](https://arxiv.org/abs/2308.16369) — 프리필(prefill)은 프롬프트 캐싱이 지름길을 내주는 단계입니다. 캐시 히트 시 TTFT는 크게 줄고 TPOT은 영향받지 않는 이유를 설명합니다.
- [Leviathan et al., "Fast Inference from Transformers via Speculative Decoding" (2023)](https://arxiv.org/abs/2211.17192) — 프롬프트 캐싱은 추론 비용 곡선을 휘게 하는 레버인 스페큘레이티브 디코딩, Flash Attention, MQA/GQA와 나란히 있습니다. 나머지 셋은 이 논문에서 읽어 보세요.
