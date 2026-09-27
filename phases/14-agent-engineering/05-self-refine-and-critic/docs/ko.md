> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# Self-Refine과 CRITIC: 반복적인 출력 개선

> Self-Refine(Madaan 등, 2023)은 LLM 하나로 세 역할 — 생성, 피드백, 다듬기 — 을 루프로 수행합니다. 평균 이득: 7개 과제에서 절대 +20. CRITIC(Gou 등, 2023)은 검증을 외부 도구로 돌려 피드백 단계를 단단하게 만듭니다. 2026년에는 이 패턴이 모든 프레임워크에 "evaluator-optimizer"(Anthropic) 또는 가드레일 루프(OpenAI Agents SDK)로 실려 나옵니다.

**유형:** Build
**언어:** Python (표준 라이브러리)
**선수 지식:** 페이즈 14 · 01 (에이전트 루프), 페이즈 14 · 03 (Reflexion)
**시간:** ~60분

## 학습 목표

- Self-Refine의 세 프롬프트(생성, 피드백, 다듬기)를 말하고, 다듬기 프롬프트에 히스토리가 왜 중요한지 설명합니다.
- CRITIC의 핵심 통찰을 설명합니다. 외부 근거 없이는 LLM의 자기 검증이 믿을 수 없다는 것.
- 히스토리와 선택적 외부 검증기를 갖춘 표준 라이브러리 기반 Self-Refine 루프를 구현합니다.
- 이 패턴을 Anthropic의 "evaluator-optimizer" 워크플로와 OpenAI Agents SDK의 출력 가드레일에 대응시킵니다.

## 문제 상황

에이전트가 거의 맞는 답을 만들어 냈습니다. 코드 한 줄에 문법 오류가 있을 수도 있고, 요약이 너무 길 수도 있고, 계획이 예외 사례 하나를 빠뜨릴 수도 있습니다. 원하는 것은 이것입니다. 에이전트가 자기 출력을 스스로 비판하고 고치는 것.

Self-Refine은 모델 하나, 학습 데이터 없이, RL 없이 이게 된다는 것을 보여 줍니다. 하지만 함정이 있습니다. LLM은 어려운 사실 관계의 자기 검증에 약합니다. CRITIC이 해결책에 이름을 붙였습니다. 검증 단계를 외부 도구(검색, 코드 실행기, 계산기, 테스트 러너)로 돌려라.

두 논문이 함께 2026년 반복 개선의 기본값을 정의합니다. 생성하고, 검증하고(가능하면 외부로), 다듬고, 검증기가 통과하면 멈춘다.

## 개념

### Self-Refine (Madaan 등, NeurIPS 2023)

LLM 하나, 세 역할:

```
generate(task)            -> output_0
feedback(task, output_0)  -> critique_0
refine(task, output_0, critique_0, history) -> output_1
feedback(task, output_1)  -> critique_1
refine(task, output_1, critique_1, history) -> output_2
...
feedback가 "문제 없음"이라 하거나 예산이 소진되면 정지.
```

핵심 디테일: `refine`은 전체 히스토리 — 지금까지의 모든 출력과 비판 — 를 봅니다. 그래서 같은 실수를 반복하지 않습니다. 논문은 이를 제거 실험(ablation)으로 확인했습니다. 히스토리를 빼면 품질이 크게 떨어집니다.

헤드라인: 수학, 코드, 두문자어, 대화 등 7개 과제 평균 절대 +20 개선, GPT-4 포함. 학습 없음, 외부 도구 없음, 모델 하나.

### CRITIC (Gou 등, arXiv:2305.11738, 2024년 2월 v4)

Self-Refine의 약점: 피드백 단계는 LLM이 자기 자신을 채점하는 것입니다. 사실 관계 주장에서는 믿을 수 없습니다(환각은 그걸 만들어 낸 모델 눈에조차 그럴듯해 보이곤 합니다). CRITIC은 `feedback(task, output)`을 `verify(task, output, tools)`로 바꿉니다. `tools`에는 다음이 포함됩니다:

- 사실 주장을 위한 검색 엔진.
- 코드 정확성을 위한 코드 실행기.
- 산술을 위한 계산기.
- 도메인 전용 검증기(단위 테스트, 타입 검사기, 린터).

검증기는 도구 결과에 근거를 둔 구조화된 비판을 만들어 냅니다. 다듬기는 이 비판을 조건으로 삼습니다.

헤드라인: 비판이 근거를 갖기 때문에 CRITIC은 사실성 과제에서 Self-Refine을 이깁니다. 외부 검증기가 없는 과제(창작 글쓰기, 포매팅)에서는 CRITIC이 Self-Refine으로 퇴화합니다.

### 정지 조건

흔한 두 가지 형태:

1. **검증기 통과.** 외부 테스트가 성공을 반환합니다. 있으면 이쪽이 좋습니다(단위 테스트, 타입 검사기, 가드레일 단언).
2. **피드백 없음.** 모델이 "출력은 괜찮다"고 말합니다. 더 싸지만 믿음직하지 않습니다. 최대 반복 상한과 함께 쓰세요.

2026년 기본값: 둘을 결합합니다. "검증기가 통과했거나, 모델이 괜찮다고 했고 반복이 2회 이상이거나, 반복이 max_iterations에 도달하면 정지."

### Evaluator-Optimizer (Anthropic, 2024)

Anthropic의 2024년 12월 글은 이것을 다섯 가지 워크플로 패턴 중 하나로 이름 붙였습니다. 두 역할:

- 평가자(Evaluator): 출력을 채점하고 비판을 만들어 냅니다.
- 최적화자(Optimizer): 비판을 받아 출력을 고칩니다.

평가자가 통과할 때까지 루프를 돕니다. Anthropic의 프레임으로 표현한 Self-Refine/CRITIC입니다. Anthropic이 추가하는 결정적인 엔지니어링 디테일: 모델이 그냥 도장 찍기로 넘어가지 않도록 평가자와 최적화자 프롬프트는 실질적으로 달라야 합니다.

### OpenAI Agents SDK 출력 가드레일

OpenAI Agents SDK는 이 패턴을 "출력 가드레일"로 제공합니다. 가드레일은 에이전트의 최종 출력 위에서 도는 검증기입니다. 가드레일이 발동하면(`OutputGuardrailTripwireTriggered` 예외), 출력은 거부되고 에이전트는 재시도할 수 있습니다. 가드레일은 도구를 호출할 수도(CRITIC식) 있고 순수 함수일 수도 있습니다(Self-Refine식).

### 2026년의 함정들

- **도장 찍기 루프.** 같은 모델이 같은 프롬프트 스타일로 생성과 비판을 맡으면 "괜찮아 보이네요"로 수렴합니다. 구조적으로 다른 프롬프트를 쓰거나, 더 작고 싼 모델로 비판하게 하세요.
- **과도한 다듬기.** 다듬기 한 번마다 지연 시간과 토큰이 늘어납니다. 1~3회를 예산으로 잡고, 그 뒤에는 사람 검토로 넘기세요.
- **사소한 과제에 CRITIC.** 외부 검증기가 없으면 CRITIC은 Self-Refine으로 퇴화합니다. 껍데기뿐인 검증기에 지연 시간을 지불하지 마세요.

```figure
self-refine
```

## 만들어 보기

`code/main.py`는 장난감 과제 위에서 Self-Refine과 CRITIC을 구현합니다. 주제가 주어지면 짧은 글머리표 목록을 만들기입니다. 검증기는 형식(글머리표 3개, 각 60자 미만)을 검사합니다. CRITIC은 알려진 환각에 벌점을 주는 외부 "사실 검증기"를 추가합니다.

구성 요소:

- `generate` — 스크립트된 생산자.
- `feedback` — LLM식 자기 비판.
- `verify_external` — CRITIC식 근거 기반 검증기.
- `refine` — 히스토리를 받아 출력을 다시 씁니다.
- 정지 조건 — 검증기 통과 또는 최대 4회 반복.

실행:

```
python3 code/main.py
```

Self-Refine 실행과 CRITIC 실행을 비교해 보세요. CRITIC은 Self-Refine이 놓친 사실 오류를 잡아 냅니다. 외부 검증기가 자기 비판에는 없는 근거를 갖고 있기 때문입니다.

## 활용하기

Anthropic의 evaluator-optimizer는 이 패턴을 Claude 친화적 언어로 표현한 것입니다. OpenAI Agents SDK의 출력 가드레일은 CRITIC 형태입니다(가드레일이 도구를 호출할 수 있음). LangGraph는 Self-Refine처럼 읽히는 반성 노드를 제공합니다. Google의 Gemini 2.5 Computer Use는 단계별 안전 평가자를 더하는데, 이것도 CRITIC 변형입니다. 모든 행동이 확정 전에 검증됩니다.

## 출시하기

`outputs/skill-refine-loop.md`는 과제 형태, 검증기 가용성, 반복 예산이 주어지면 evaluator-optimizer 루프를 구성합니다. 생성자, 평가자/검증기, 최적화자의 프롬프트와 정지 정책을 내놓습니다.

## 연습 문제

1. 장난감을 max_iterations=1로 돌려 보세요. CRITIC은 여전히 도움이 될까요?
2. 외부 검증기를 시끄러운 것(무작위 30% 오탐)으로 바꿔 보세요. 루프는 어떻게 될까요? 이것이 대부분의 가드레일 스택이 겪는 2026년의 현실입니다.
3. "서로 다른 모델의 생성자-비판자" 변형을 구현해 보세요. 큰 모델이 생성하고 작은 모델이 비판합니다. 같은 모델 방식을 이길까요?
4. CRITIC 3절(arXiv:2305.11738 v4)을 읽어 보세요. 검증 도구의 세 범주를 말하고 각각 예를 들어 보세요.
5. OpenAI Agents SDK의 `output_guardrails`를 CRITIC의 검증기 역할에 대응시켜 보세요. SDK가 잘못 잡은 것은 무엇이고, 잘 잡은 것은 무엇일까요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| Self-Refine | "스스로 고치는 LLM" | 한 모델 안의 생성 → 피드백 → 다듬기 루프, 히스토리 포함 |
| CRITIC | "도구 근거 검증" | 피드백을 외부 검증기(검색, 코드, 계산기, 테스트)로 대체 |
| Evaluator-Optimizer | "Anthropic 워크플로 패턴" | 두 역할 — 평가자가 채점, 최적화자가 수정 — 수렴까지 루프 |
| 출력 가드레일(Output guardrail) | "사후 검사" | 에이전트가 출력을 낸 뒤에 도는 OpenAI Agents SDK 검증기 |
| 검증 단계(Verify step) | "비판 단계" | 빠지면 안 되는 결정: 근거 기반인지 자기 채점인지 |
| 다듬기 히스토리(Refine history) | "모델이 이미 시도한 것" | 다듬기 프롬프트 앞에 붙는 이전 출력 + 비판, 빼면 품질 붕괴 |
| 도장 찍기 루프(Rubber-stamp loop) | "자기 동의 실패" | 같은 프롬프트의 비판은 "괜찮아 보임"만 반환, 구조적으로 다른 프롬프트로 해결 |
| 정지 조건(Stop condition) | "수렴 검사" | 검증기 통과 또는 피드백 없음 + 반복 상한, 단일 조건은 금물 |

## 더 읽을거리

- [Madaan 등, Self-Refine (arXiv:2303.17651)](https://arxiv.org/abs/2303.17651) — 표준이 되는 원 논문
- [Gou 등, CRITIC (arXiv:2305.11738)](https://arxiv.org/abs/2305.11738) — 도구 근거 검증
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — evaluator-optimizer 워크플로 패턴
- [OpenAI Agents SDK 문서](https://openai.github.io/openai-agents-python/) — CRITIC 형태 검증기로서의 출력 가드레일
