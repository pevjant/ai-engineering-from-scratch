> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 챗봇 — 규칙 기반에서 신경망, LLM 에이전트까지

> ELIZA는 패턴 매칭으로 답했습니다. DialogFlow는 인텐트를 매핑했습니다. GPT는 가중치에서 답을 만들어 냈습니다. Claude는 도구를 실행하고 검증합니다. 각 시대는 바로 앞 시대의 최악의 실패를 해결하며 등장했습니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 13(질의응답), 페이즈 5 · 14(정보 검색)
**시간:** 약 75분

## 문제 상황

사용자가 "비행기를 다른 편으로 바꾸고 싶어요"라고 말합니다. 시스템은 사용자가 무엇을 원하는지, 어떤 정보가 빠져 있는지, 그 정보를 어떻게 얻을지, 행동을 어떻게 완료할지 알아내야 합니다. 그런데 사용자가 이어서 "아니면 그냥 취소하면 어때요?"라고 하면, 시스템은 컨텍스트를 기억하고, 작업을 갈아타고, 상태를 유지해야 합니다.

대화는 ML 시스템에게 어렵습니다. 입력이 열려 있고, 출력은 여러 턴에 걸쳐 일관성을 유지해야 하고, 시스템은 세상에 실제로 작용해야 할 수도 있습니다(비행기 변경, 카드 결제). 잘못된 단계 하나하나가 사용자에게 그대로 보입니다.

챗봇 아키텍처는 네 가지 패러다임을 순환해 왔고, 각 패러다임은 앞선 것이 너무 뻔하게 실패했기 때문에 등장했습니다. 이 레슨은 그 순서대로 살펴봅니다. 2026년 프로덕션(운영 환경) 풍경은 마지막 두 가지의 하이브리드입니다.

## 핵심 개념

![챗봇의 진화: 규칙 기반 → 검색 → 신경망 → 에이전트](../assets/chatbot.svg)

### 대본으로 짜인 반세기, 1950-2001

첫 번째 패러다임은 5년을 버티지 못한 게 아니라 50년을 버텼습니다. 그 궤적을 아는 것이 중요한 이유는, 그 안의 모든 시스템이 같은 기계이기 때문입니다 — 입력을 매칭하고, 준비된 대답을 내놓고, 약간의 상태를 갱신하는 기계요. 이 기계에 규칙을 50년간 추가해도 일반적인 경우는 끝내 만들어지지 않았습니다. 그 한계선 때문에 두 번째부터 네 번째 패러다임이 존재합니다.

**1950.** Turing은 "기계는 생각할 수 있는가?"라는 질문을, 실행 가능한 대안으로 치환해 버립니다: 심문관이 타자기 대화로 기계와 사람을 구분하지 못한다면 그 철학적 질문은 논점이 아니라는 것이죠. 대화는 이 분야에 이름조차 붙기 전에 벤치마크가 되었습니다.

**1956.** 이름이 등장합니다 — 다트머스 여름 워크숍이 "지능의 모든 특성은 원리적으로 아주 정밀하게 기술될 수 있고, 그렇다면 기계로 그것을 시뮬레이트할 수 있다"는 추측에 근거해 "인공지능"이라는 말을 만들어 냅니다. 제안서는 실질적인 진전을 위해 두 달을 예산으로 잡았습니다.

**1966.** ELIZA가 단계 1에서 직접 만들 그 반사(reflection) 트릭을 출시합니다: 분해 규칙이 입력에서 조각을 뽑고, 재조립 규칙이 그 조각을 질문 형태로 되돌려 줍니다. 패턴은 총 200개 남짓, 상태 0, 이해 0 — 그런데도 사용자들은 이 프로그램에게 속마음을 털어놨습니다. Weizenbaum은 너무 적은 장치로 그런 일이 벌어졌다는 사실에 경악하며 남은 경력을 보냈습니다.

**1972.** 편집증(paranoia)을 모델링하려고 스탠퍼드에서 만든 PARRY는 ELIZA에게 없던 부품을 더합니다: 내부 상태입니다. 두려움, 분노, 불신을 나타내는 수치 변수들이 매 턴 갱신되고 다음에 어떤 대본이 발동할지 결정하므로, 같은 입력도 지금까지의 대화에 따라 다른 반응을 냅니다. 눈가림 전사(transcript) 테스트에서 정신과 의사들은 PARRY와 실제 환자를 확률 수준으로밖에 구분하지 못했습니다. 이것이 페르소나 조건화(persona conditioning)의 직계 조상입니다 — 세 개의 float 값으로 구현된 시스템 프롬프트죠. 같은 해, 두 봇은 ARPANET을 통해 서로 마주 보게 됩니다. 치료사 대본이 편집증 상태 기계를 인터뷰하는, 네트워크에서 벌어진 최초의 봇 대 봇 대화입니다.

**1995.** ALICE는 ELIZA 레시피를 AIML이라는, 패턴-템플릿 쌍을 담는 XML 방언으로 확장합니다. 손으로 쓴 카테고리 약 4만 개, Loebner Prize 3회 우승. 규칙 기반 시스템의 스케일링 법칙을 증명했습니다: 규칙을 더하면 커버리지는 늘지만 일반성은 결코 늘지 않는다. 모든 규칙은 누군가 유지보수해야 하는 부채입니다.

**2001.** SmarterChild는 이 레시피를 인스턴트 메신저 사용자 3천만 명 앞에 내놓고, 날씨·주식·영화 상영 시간 같은 백엔드 조회를 템플릿에 접목합니다. 눈을 가늘게 뜨면 이것은 2001년 의상을 입은 도구 호출입니다: 인텐트를 파싱하고, 서비스를 호출하고, 결과를 답변에 렌더링하죠.

50년, 단 하나의 메커니즘, 늘어나기만 한 규칙 수. 이 패러다임이 끝난 건 반증됐어서가 아닙니다. 손으로 쓴 상태 기계의 유지보수 비용은 커버리지에 비례해 늘어나는 반면, 사용자 기대치는 그들이 지난주 본 무언가를 따라 늘어나기 때문입니다.

```figure
chatbot-lineage
```

**규칙 기반(ELIZA, AIML, DialogFlow).** 손으로 만든 패턴이 사용자 입력에 매칭되어 응답을 만듭니다. 인텐트 분류기가 미리 정의된 플로우로 안내하고, 슬롯 채우기(slot filling) 상태 기계가 필요한 정보를 모읍니다. 설계된 좁은 범위 안에서는 빛나게 잘 동작하고, 그 밖에서는 즉시 실패합니다. 환각이 용납되지 않는 안전 필수 도메인(은행 인증, 항공사 예약)에서는 지금도 출시되고 있습니다.

**검색 기반.** FAQ 스타일 시스템입니다. (발화, 응답) 쌍을 모두 인코딩해 두고, 런타임에 사용자 메시지를 인코딩해 가장 가까운 저장된 응답을 검색합니다. Zendesk의 클래식한 "비슷한 문서" 기능을 떠올리면 됩니다. 규칙보다 바꿔 말하기를 잘 처리합니다. 생성이 없으니 환각도 없습니다.

**신경망(seq2seq).** 대화 로그로 학습한 인코더-디코더입니다. 응답을 밑바닥부터 생성합니다. 유창하지만 만연한 출력("모르겠어요")과 사실성 이탈에 취약하고, 주제를 끝내 벗어납니다. 2016-2019년 Google, Facebook, Microsoft의 챗봇이 모두 실망스러웠던 이유입니다.

**LLM 에이전트.** 계획을 세우고, 도구를 호출하고, 결과를 검증하는 루프로 감싼 언어 모델입니다. 긴 프롬프트를 단 챗봇이 아니라, 에이전트 루프입니다: 계획 → 도구 호출 → 결과 관찰 → 다음 단계 결정. 검색 우선 그라운딩(RAG)이 환각을 막아 주고, 도구 호출이 실제로 일을 하게 해 줍니다. 이것이 2026년 아키텍처입니다.

네 패러다임은 순차적인 교체가 아닙니다. 2026년 프로덕션 챗봇은 넷을 모두 거칩니다: 인증과 파괴적 작업은 규칙 기반, FAQ는 검색, 자연스러운 문장은 신경망 생성, 모호한 열린 질문은 LLM 에이전트.

## 만들어 보기

### 단계 1: 규칙 기반 패턴 매칭

```python
import re


class RulePattern:
    def __init__(self, pattern, response_template):
        self.regex = re.compile(pattern, re.IGNORECASE)
        self.template = response_template


PATTERNS = [
    RulePattern(r"my name is (\w+)", "Nice to meet you, {0}."),
    RulePattern(r"i (need|want) (.+)", "Why do you {0} {1}?"),
    RulePattern(r"i feel (.+)", "Why do you feel {0}?"),
    RulePattern(r"(.*)", "Tell me more about that."),
]


def rule_based_respond(user_input):
    for pattern in PATTERNS:
        m = pattern.regex.match(user_input.strip())
        if m:
            return pattern.template.format(*m.groups())
    return "I don't understand."
```

20줄짜리 ELIZA입니다. 반사 트릭("I feel sad" → "Why do you feel sad")은 Weizenbaum 1966의 정석 사이코테라피스트 데모입니다. 지금도 배울 점이 많습니다.

### 단계 2: 검색 기반 (FAQ)

이 예시 스니펫은 `pip install sentence-transformers`(torch를 함께 끌어옵니다)가 필요합니다. 이 레슨의 실행 가능한 `code/main.py`는 대신 표준 라이브러리의 Jaccard 유사도를 사용하므로, 외부 의존성 없이 레슨을 실행할 수 있습니다.

```python
from sentence_transformers import SentenceTransformer
import numpy as np


FAQ = [
    ("how do i reset my password", "Go to Settings > Security > Reset Password."),
    ("how do i cancel my order", "Go to Orders, find the order, click Cancel."),
    ("what is your return policy", "30-day returns on unused items, original packaging."),
]


encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
faq_questions = [q for q, _ in FAQ]
faq_embeddings = encoder.encode(faq_questions, normalize_embeddings=True)


def faq_respond(user_input, threshold=0.5):
    q_emb = encoder.encode([user_input], normalize_embeddings=True)[0]
    sims = faq_embeddings @ q_emb
    best = int(np.argmax(sims))
    if sims[best] < threshold:
        return None
    return FAQ[best][1]
```

임계값 기반 거절이 핵심 설계 선택입니다. 최고 점수 매치가 충분히 가깝지 않으면 `None`을 돌려주고 시스템이 상위로 넘기게(escalate) 하세요.

### 단계 3: 신경망 생성 (베이스라인)

작은 instruction-tuned 인코더-디코더(FLAN-T5)나 파인튜닝된 대화 모델을 쓰세요. 2026년 기준 단독으로는 프로덕션에 쓸 수 없지만(모순, 주제 이탈, 사실과 다른 헛소리), 자연스러운 문장을 위해 하이브리드 시스템 안에서는 출시됩니다. DialoGPT 스타일의 디코더 전용 모델은 일관된 답변을 내려면 명시적인 턴 구분자와 EOS 처리가 필요합니다; FLAN-T5 text2text 파이프라인은 교육용 예제로 바로 동작합니다.

```python
from transformers import pipeline

chatbot = pipeline("text2text-generation", model="google/flan-t5-small")

response = chatbot("Respond politely to: Hi there!", max_new_tokens=40)
print(response[0]["generated_text"])
```

### 단계 4: LLM 에이전트 루프

2026년 프로덕션 형태:

```python
def agent_loop(user_message, tools, llm, max_steps=5):
    history = [{"role": "user", "content": user_message}]
    for _ in range(max_steps):
        response = llm(history, tools=tools)
        tool_call = response.get("tool_call")
        if tool_call:
            tool_name = tool_call.get("name")
            args = tool_call.get("arguments")
            if not isinstance(tool_name, str) or tool_name not in tools:
                history.append({"role": "assistant", "tool_call": tool_call})
                history.append({"role": "tool", "name": str(tool_name), "content": f"error: unknown tool {tool_name!r}"})
                continue
            if not isinstance(args, dict):
                history.append({"role": "assistant", "tool_call": tool_call})
                history.append({"role": "tool", "name": tool_name, "content": f"error: arguments must be a dict, got {type(args).__name__}"})
                continue
            fn = tools[tool_name]
            result = fn(**args)
            history.append({"role": "assistant", "tool_call": tool_call})
            history.append({"role": "tool", "name": tool_name, "content": result})
        else:
            return response["content"]
    return "I could not complete the task in the step budget."
```

이름 붙일 것은 셋입니다. 도구(tools)는 LLM이 호출할 수 있는 함수입니다. 루프는 LLM이 도구 호출 대신 최종 답변을 돌려주면 끝납니다. 단계 예산(step budget)은 모호한 작업에서 무한 루프에 빠지는 걸 막습니다.

실제 프로덕션에서는 여기에 더합니다: 검색 우선 그라운딩(각 LLM 호출 전에 관련 문서를 주입), 가드레일(확인 없이 파괴적 작업 거부), 관측 가능성(모든 단계 로깅), 평가(에이전트 동작이 명세를 벗어나지 않는지 자동 검사).

### 단계 5: 하이브리드 라우팅

```python
def hybrid_chat(user_input):
    if is_destructive_action(user_input):
        return structured_flow(user_input)

    faq_answer = faq_respond(user_input, threshold=0.6)
    if faq_answer:
        return faq_answer

    return agent_loop(user_input, tools, llm)


def is_destructive_action(text):
    danger_words = ["delete", "cancel", "charge", "refund", "transfer"]
    return any(w in text.lower() for w in danger_words)
```

패턴은 이렇습니다: 파괴적인 것은 전부 결정적 규칙으로, 준비된 FAQ는 검색으로, 나머지는 LLM 에이전트로. 2026년 고객 지원 시스템이 실제로 출시하는 형태입니다.

## 사용해 보기

2026년 스택:

| 사용 사례 | 아키텍처 |
|---------|---------------|
| 예약, 결제, 인증 | 규칙 기반 상태 기계 + 슬롯 채우기 |
| 고객 지원 FAQ | 선별된 답변 위의 검색 |
| 열린 도움말 채팅 | RAG + 도구 호출을 갖춘 LLM 에이전트 |
| 내부 도구 / IDE 어시스턴트 | 도구 호출(검색, 읽기, 쓰기)이 있는 LLM 에이전트 |
| 컴패니언 / 캐릭터 챗봇 | 페르소나 시스템 프롬프트를 얹은 튜닝된 LLM + 지식 검색 |

프로덕션에서는 반드시 하이브리드 라우팅을 쓰세요. 모든 요청을 잘 처리하는 단일 아키텍처는 없습니다. 라우팅 계층 자체는 보통 작은 인텐트 분류기입니다.

## 여전히 출시되고 있는 실패 양상

- **자신만만한 허위 보고.** LLM 에이전트가 하지 않은 작업을 했다고 주장합니다. 완화책: 결과를 검증하고, 도구 호출을 로깅하고, 성공한 도구 반환 없이는 LLM이 무언가를 했다고 주장하지 못하게 하세요.
- **프롬프트 인젝션.** 사용자가 시스템 프롬프트를 덮어쓰는 텍스트를 넣습니다. OWASP Top 10 for LLM Applications 2025에서 LLM01로 선정됐습니다. 두 종류가 있습니다: 직접 인젝션(채팅에 붙여넣음)과 간접 인젝션(에이전트가 읽는 문서, 이메일, 도구 출력에 숨겨짐).

  공격 성공률은 시나리오마다 다릅니다. 일반 도구 사용·코딩 벤치마크에서 측정된 성공률은 프론티어 모델 기준 약 0.5-8.5%입니다. 특정 고위험 구성(AI 코딩 에이전트를 겨냥한 적응형 공격, 취약한 오케스트레이션)에서는 약 84%에 이르기도 했습니다. 프로덕션 CVE 사례로는 EchoLeak(CVE-2025-32711, CVSS 9.3)이 있습니다 — 공격자가 조작한 이메일로 발동되는 Microsoft 365 Copilot의 제로클릭 데이터 유출 취약점이죠.

  완화책: 루프 전체에서 사용자 입력을 신뢰할 수 없는 것으로 취급; 도구 호출 전에 입력을 소독(sanitize); 도구 출력을 메인 프롬프트에서 격리; Plan-Verify-Execute(PVE) 패턴 사용 — 에이전트가 먼저 계획을 세운 뒤, 실행 전에 각 행동을 그 계획과 대조해 검증(이렇게 하면 도구 결과가 계획에 없던 새 행동을 주입하지 못함); 파괴적 작업에는 사용자 확인 요구; 도구 범위에 최소 권한 적용.

  아무리 프롬프트 엔지니어링을 해도 이 위험을 완전히 없앨 수는 없습니다. 외부 런타임 방어 계층(LLM Guard, 허용목록 검증, 의미 기반 이상 탐지)이 필요합니다.
- **범위 확장(scope creep).** 도구 호출이 무관한 정보를 돌려주는 바람에 에이전트가 본래 작업에서 벗어납니다. 완화책: 도구 계약을 좁히고, 시스템 프롬프트를 집중되게 유지하고, 이탈률에 대한 평가를 추가하세요.
- **무한 루프.** 에이전트가 같은 도구만 계속 호출합니다. 완화책: 단계 예산, 도구 호출 중복 제거, "우리 진전이 있나?"를 묻는 LLM 심판.
- **컨텍스트 윈도우 소진.** 긴 대화는 가장 이른 턴들을 컨텍스트 밖으로 밀어냅니다. 완화책: 오래된 턴을 요약하거나, 유사도로 관련 과거 턴을 검색하거나, 롱컨텍스트 모델을 쓰세요.

## 출시하기

`outputs/skill-chatbot-architect.md`로 저장하세요:

```markdown
---
name: chatbot-architect
description: 주어진 사용 사례를 위한 챗봇 스택 설계하기.
version: 1.0.0
phase: 5
lesson: 17
tags: [nlp, agents, chatbot]
---

제품 맥락(사용자 니즈, 컴플라이언스 제약, 사용 가능한 도구, 데이터 볼륨)이 주어지면 다음을 출력하세요:

1. 아키텍처. 규칙 기반, 검색, 신경망, LLM 에이전트, 또는 하이브리드(어떤 경로가 어디로 가는지 명시).
2. 해당 시 LLM 선택. 모델 계열 이름(Claude, GPT-4, Llama-3.1, Mixtral). 도구 사용 품질과 비용에 맞춥니다.
3. 그라운딩 전략. RAG 소스, 검색 방법(레슨 14 참조), 도구 계약.
4. 평가 계획. 보류(held-out) 대화에서의 작업 성공률, 도구 호출 정확도, 이탈률, 환각률.

파괴적 작업(결제, 계정 삭제, 데이터 수정)에 구조화된 확인 절차 없이 순수 LLM 에이전트를 추천하지 마세요. 에이전트가 무엇이든 쓰기 권한을 갖고 있다면 프롬프트 인젝션 감사를 건너뛰는 방안을 받아들이지 마세요.
```

## 연습 문제

1. **쉬움.** 위의 규칙 기반 응답기를 커피숍 주문 봇용 패턴 10개로 구현하세요. 경계 사례를 테스트하세요: 이중 주문, 변경, 취소, 불분명한 인텐트.
2. **중간.** 하이브리드 FAQ + LLM 폴백을 만드세요. SaaS 제품용 준비된 FAQ 항목 50개와, 문서 사이트를 검색하는 LLM 폴백입니다. 실제 지원 질문 100개로 거절률과 정확도를 측정하세요.
3. **어려움.** 위의 에이전트 루프를 도구 셋(search, read-user-data, send-email)으로 구현하세요. 프롬프트 인젝션 시도를 포함한 50개 테스트 시나리오로 평가를 돌리고, 이탈률, 실패 작업률, 인젝션 성공 여부를 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 말 | 실제 의미 |
|------|-----------------|-----------------------|
| 인텐트 | 사용자가 원하는 것 | 범주형 레이블(book_flight, reset_password). 핸들러로 라우팅됨. |
| 슬롯 | 정보 조각 하나 | 봇이 필요로 하는 파라미터(날짜, 목적지). 슬롯 채우기는 그 정보를 묻는 질문들의 연속. |
| RAG | 검색 + 생성 | 관련 문서를 검색한 뒤 LLM의 응답을 그 근거 위에 고정(ground). |
| 도구 호출 | 함수 호출 | LLM이 이름 + 인수가 담긴 구조화된 호출을 만들어 냄. 런타임이 실행하고 결과를 돌려줌. |
| 에이전트 루프 | 계획, 실행, 검증 | 작업이 끝날 때까지 LLM 호출과 도구 호출을 번갈아 수행하는 컨트롤러. |
| 프롬프트 인젝션 | 프롬프트에 대한 사용자 공격 | 시스템 프롬프트를 덮어쓰려는 악의적 입력. |

## 더 읽을거리

- [Turing (1950). Computing Machinery and Intelligence](https://academic.oup.com/mind/article/LIX/236/433/986238) — 대화를 이 분야의 벤치마크로 만든 논문.
- [Weizenbaum (1966). ELIZA — A Computer Program For the Study of Natural Language Communication](https://web.stanford.edu/class/cs124/p36-weizenabaum.pdf) — 최초의 규칙 기반 챗봇 논문.
- [Colby, Weber, Hilf (1971). Artificial Paranoia](https://doi.org/10.1016/0004-3702(71)90002-6) — PARRY의 정서 변수 아키텍처, 최초의 상태 보유(stateful) 챗봇.
- [Thoppilan et al. (2022). LaMDA: Language Models for Dialog Applications](https://arxiv.org/abs/2201.08239) — LLM 에이전트가 판을 잡기 직전의, Google의 말기 신경망 챗봇 논문.
- [Yao et al. (2022). ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) — 에이전트 루프 패턴에 이름을 붙인 논문.
- [Anthropic's guide on building effective agents](https://www.anthropic.com/research/building-effective-agents) — 2024년 프로덕션 가이드로, 2026년에도 유효합니다.
- [Greshake et al. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173) — 프롬프트 인젝션의 대표 논문.
- [OWASP Top 10 for LLM Applications 2025 — LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — 프롬프트 인젝션을 최상위 보안 관심사로 만든 랭킹.
- [AWS — Securing Amazon Bedrock Agents against Indirect Prompt Injections](https://aws.amazon.com/blogs/machine-learning/securing-amazon-bedrock-agents-a-guide-to-safeguarding-against-indirect-prompt-injections/) — Plan-Verify-Execute와 사용자 확인 절차를 포함한 실용적인 오케스트레이션 계층 방어.
- [EchoLeak (CVE-2025-32711)](https://www.vectra.ai/topics/prompt-injection) — 간접 프롬프트 인젝션으로 인한 대표적인 제로클릭 데이터 유출 CVE. 쓰기 권한을 가진 에이전트에 런타임 방어가 필요한 이유의 참고 사례.
