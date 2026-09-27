---
name: check-understanding
version: 1.0.0
description: AI Engineering from Scratch 코스의 페이즈 퀴즈. "quiz me", "test phase", "check my understanding", "do I know phase 3" 또는 `/check-understanding <phase>`로 실행합니다.
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

# 이해도 점검 (Check Understanding)

AI Engineering from Scratch 코스에서 끝낸 페이즈에 대해 얼마나 알고 있는지 확인하는 퀴즈입니다.

## 실행 조건 (Activation)

사용자가 다음과 같이 말하면 이 스킬이 실행됩니다:
- `/check-understanding 3` 또는 `/check-understanding deep-learning`
- "quiz me on phase 2" (2페이즈로 퀴즈 내줘)
- "test phase 1" (1페이즈 시험해 줘)
- "check my understanding of transformers" (트랜스포머 이해도 확인해 줘)
- "do I know phase 3" (3페이즈 알고 있는 걸까?)
- "am I ready for the next phase" (다음 페이즈로 넘어가도 될까?)

## 입력 (Input)

페이즈 번호(0-19) 또는 페이즈 이름을 인자로 받습니다. 인자가 주어지지 않으면 20개 페이즈 전체 목록을 보여주고, 어느 페이즈를 시험할지 물어봅니다.

## 페이즈 맵 (Phase Map)

인자를 `phases/` 아래의 올바른 페이즈 디렉터리에 연결합니다:

| 입력 | 디렉터리 | 페이즈 이름 |
|-------|-----------|------------|
| 0, setup, tooling | `00-setup-and-tooling` | 환경 설정 & 도구 |
| 1, math, math-foundations | `01-math-foundations` | 수학 기초 |
| 2, ml, ml-fundamentals | `02-ml-fundamentals` | ML 기초 |
| 3, deep-learning, dl | `03-deep-learning-core` | 딥러닝 핵심 |
| 4, cv, computer-vision, vision | `04-computer-vision` | 컴퓨터 비전 |
| 5, nlp | `05-nlp-foundations-to-advanced` | NLP -- 기초부터 고급까지 |
| 6, speech, audio | `06-speech-and-audio` | 음성 & 오디오 |
| 7, transformers | `07-transformers-deep-dive` | 트랜스포머 심화 |
| 8, generative, gen-ai, genai | `08-generative-ai` | 생성형 AI |
| 9, rl, reinforcement-learning | `09-reinforcement-learning` | 강화 학습 |
| 10, llms, llm, llms-from-scratch | `10-llms-from-scratch` | LLM 처음부터 만들기 |
| 11, llm-engineering, llm-eng | `11-llm-engineering` | LLM 엔지니어링 |
| 12, multimodal | `12-multimodal-ai` | 멀티모달 AI |
| 13, tools, protocols, mcp | `13-tools-and-protocols` | 도구 & 프로토콜 |
| 14, agents, agent-engineering | `14-agent-engineering` | 에이전트 엔지니어링 |
| 15, autonomous | `15-autonomous-systems` | 자율 시스템 |
| 16, multi-agent, swarms | `16-multi-agent-and-swarms` | 멀티 에이전트 & 스웜 |
| 17, infrastructure, production, infra | `17-infrastructure-and-production` | 인프라 & 프로덕션(운영 환경) |
| 18, ethics, safety, alignment | `18-ethics-safety-alignment` | 윤리, 안전 & 정렬 |
| 19, capstone, projects | `19-capstone-projects` | 캡스톤 프로젝트 |

## 진행 절차 (Procedure)

### 단계 1: 페이즈 확인

인자를 해석합니다. 숫자라면 0 이상 19 이하인지 확인합니다. 범위를 벗어나면 사용자에게 "페이즈 [N]은(는) 존재하지 않습니다. 유효한 페이즈는 0-19입니다."라고 말한 뒤 전체 목록을 보여주고 고르게 합니다. 이름이나 키워드라면 위의 페이즈 맵에서 찾아봅니다. 키워드가 맵의 어떤 항목과도 맞지 않으면 "'[keyword]'은(는) 알 수 없는 페이즈입니다. 아래 목록에서 고르세요:"라고 말하고 20개 페이즈 전체를 보여줍니다. 인자가 아예 없으면 전체 목록에서 고르라고 물어봅니다.

### 단계 2: 페이즈 내용 읽기

저장소가 클론되어 있다면(현재 디렉터리 또는 상위에 `phases/` 디렉터리가 있다면) `phases/<phase-dir>/` 아래에서 모든 레슨 디렉터리를 찾고, 각 레슨의 `docs/en.md`를 읽습니다. 클론되어 있지 않다면 README의 Contents 섹션에서 해당 페이즈의 레슨 목록을 가져오고(`https://raw.githubusercontent.com/rohitg00/ai-engineering-from-scratch/main/README.md` 사용), 같은 raw 기본 URL로 각 레슨의 `docs/en.md`를 가져옵니다. 이 문서들이 곧 여러분이 문제를 만들 재료가 되는 학습 자료입니다.

페이즈 전체를 두루 커버할 만큼 레슨 문서를 읽습니다. 레슨이 많은 페이즈(15개 이상)라면 대표적으로 골고루 읽는 것을 우선합니다: 처음 몇 개, 가운데, 마지막 몇 개.

### 단계 3: 문제 8개 만들기

방금 읽은 레슨 내용에서 정확히 8개의 객관식 문제를 만듭니다:

**문제 1-4: 개념형 (What/Why)**
아이디어, 정의, 추론에 대한 이해를 확인합니다. 예시:
- "X의 목적은 무엇인가요?"
- "Z일 때 왜 Y가 일어나나요?"
- "A와 B의 관계를 가장 잘 설명한 것은 무엇인가요?"
- "X는 어떤 문제를 해결하나요?"

**문제 5-8: 실전형 (How/Build)**
적용 지식과 구현 감각을 확인합니다. 예시:
- "X를 어떻게 구현할 건가요?"
- "어떤 접근이 Y를 올바르게 풀까요?"
- "Z를 만들 때 단계 순서로 올바른 것은 무엇인가요?"
- "학습 중에 X가 관찰되면 어떻게 해야 할까요?"

각 문제에는 A, B, C, D로 표시된 선택지 4개가 정확히 있어야 하고, 정답은 하나뿐입니다. 오답 선택지는 그럴듯하지만, 자료를 제대로 공부한 사람에게는 명확히 틀린 것으로 보여야 합니다.

각 문제에 출처 레슨을 표시합니다(예: "레슨 03: 행렬 변환").

### 단계 4: 한 문제씩 출제하기

AskUserQuestion 도구(또는 이에 상응하는 대화형 질문 도구)를 사용해 각 문제를 하나씩 보여줍니다. 형식:

```text
Question 1/8 (Conceptual) -- from Lesson 03: Matrix Transformations

What is the geometric interpretation of an eigenvalue?

A) The angle of rotation applied by the matrix
B) The factor by which the eigenvector is scaled during transformation
C) The determinant of the transformation matrix
D) The rank of the matrix after transformation
```

다음 문제로 넘어가기 전에 사용자의 답을 기다립니다.

### 정답 격리

학습자가 현재 문제에 답하기 전까지는 정답 선택지와 해설을 공개하지 않습니다. 답변 형식을 알려주는 힌트에 실제 정답 문자, 정답으로 보이는 선택지, 생성된 정답 분포를 절대 넣지 않습니다. 평문 힌트가 필요하면 정확히 이렇게 씁니다: `Reply with one letter: <A|B|C|D>.`

### 단계 5: 기록하고 점수 매기기

점수를 계속 집계합니다:
- 8문제 중 맞힌 개수
- 틀린 문제마다 기록: 문제 번호, 사용자의 답, 정답, 출처 레슨

### 단계 6: 결과 보여주기

8문제가 모두 끝나면 점수와 등급을 보여줍니다:

**7-8개 정답: 마스터(Mastered)**
페이즈가 19(캡스톤 프로젝트)라면: "19페이즈, 마지막 페이즈를 마스터했습니다." 그리고 커리큘럼의 나머지 전체를 끝냈다는 것을 확인할 수 있을 때만(현재 디렉터리의 `LEARNING.md`에 있는 Path 표가 페이즈 0-18을 Done 또는 Skip으로 표시할 때) "축하합니다. 커리큘럼 전체를 완주했습니다."를 추가합니다. 페이즈 하나의 퀴즈만으로 전체 수료를 증명할 수는 없습니다.
그 외에는: "N페이즈를 탄탄하게 이해하고 있습니다. N+1페이즈([다음 페이즈 이름])(으)로 넘어갈 준비가 되었습니다."

**5-6개 정답: 거의 다 왔어요(Almost)**
"기초는 탄탄합니다. 넘어가기 전에 다음 부분을 복습하세요:"
그다음 틀린 문제와 연결된 레슨들을 나열합니다.

**3-4개 정답: 발전 중(Developing)**
"이해가 쌓이고 있지만, 다음 레슨들을 다시 봐야 합니다:"
그다음 틀린 문제마다 다시 읽을 레슨과 함께 나열합니다.

**0-2개 정답: 처음부터 다시(Start Over)**
"이 페이즈에는 더 많은 시간이 필요합니다. 처음부터 레슨을 다시 진행하되, 다음 부분에 집중하세요:"
그다음 틀린 주제 전체를 나열합니다.

### 단계 7: 틀린 문제 해설

사용자가 틀린 모든 문제에 대해 보여줍니다:

```text
Question N: [question text, abbreviated]
Your answer: B
Correct answer: C -- [the correct option text]
Why: [1-2 sentence explanation of why C is correct]
Review: Lesson NN -- [lesson name] (phases/<phase-dir>/NN-<lesson-slug>/docs/en.md)
```

### 단계 8: 다음은?

세 가지 선택지를 제안하며 마무리합니다:

1. **이 퀴즈 다시 풀기** -- 같은 페이즈에서 새로운 8문제 세트를 생성
2. **다른 페이즈 도전** -- 다른 페이즈를 골라 시험
3. **주제 설명 듣기** -- 틀린 문제에서 나온 개념 아무거나 질문

사용자의 선택을 기다리고, 그에 맞게 행동합니다.

## 규칙

- 문제 풀이가 고갈되기 전까지는 재도전에서 같은 문제를 반복하지 않습니다. 문제가 고갈되면 이후 재도전에서는 문제를 섞거나 표현을 바꿉니다.
- 문제는 일반 상식이 아니라 반드시 레슨 문서에 직접 근거해야 합니다.
- 사용자가 답하기 전에는 정답을 보여주지 않습니다.
- 학습자에게 답변 형식을 알려주는 예시에 실제 정답 문자를 넣지 않습니다. 자리표는 `<A|B|C|D>`를 사용합니다.
- 문제 본문은 간결하게 유지합니다. 최대 한두 문장.
- 오답 선택지는 그럴듯해야 합니다. 농담 같은 선택지 금지.
- 페이즈에 아직 레슨 문서가 없다면(`en.md` 파일을 찾지 못했다면) 사용자에게 "N페이즈에는 아직 레슨 내용이 없습니다. 완성된 페이즈를 골라 퀴즈를 보세요."라고 말합니다.
