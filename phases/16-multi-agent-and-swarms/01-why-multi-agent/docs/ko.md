> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 왜 멀티 에이전트인가?

> 에이전트 하나가 벽에 부딪힌다. 현명한 대응은 더 큰 에이전트가 아니라 — 더 많은 에이전트다.

**유형:** Learn
**언어:** TypeScript
**선수 지식:** 페이즈 14 (에이전트 엔지니어링)
**시간:** 약 60분

## 학습 목표

- 단일 에이전트의 한계(컨텍스트 오버플로, 뒤섞인 전문성, 순차 처리 병목)를 식별하고, 여러 에이전트로 나누는 것이 옳은 판단인 경우를 설명할 수 있다
- 오케스트레이션 패턴(파이프라인, 병렬 fan-out, 슈퍼바이저, 계층형)을 비교하고 주어진 과제 구조에 맞는 패턴을 고를 수 있다
- 명확한 역할 경계, 공유 상태, 커뮤니케이션 계약을 갖춘 멀티 에이전트 시스템을 설계할 수 있다
- 멀티 에이전트의 복잡성 비용(지연 시간, 비용, 디버깅 난이도)과 단일 에이전트의 단순함 사이 트레이드오프를 분석할 수 있다

## 문제 상황

페이즈 14에서 에이전트를 하나 만들었습니다. 잘 동작합니다. 파일을 읽고, 명령을 실행하고, API를 호출하고, 결과를 추론할 수 있습니다. 그런데 이 에이전트를 실제 코드베이스에 겨눠 봅니다: 파일 200개, 프로그래밍 언어 3개, 인프라에 의존하는 테스트, 그리고 코드를 작성하기 전에 외부 API를 조사해야 한다는 요구사항.

에이전트는 숨이 막힙니다. LLM이 멍어서가 아니라, 과제가 하나의 에이전트 루프가 감당할 수 있는 범위를 넘었기 때문입니다. 컨텍스트 윈도우가 파일 내용으로 가득 찹니다. 에이전트는 40번의 도구 호출 전에 읽은 내용을 잊어버립니다. 조사자, 코더, 리뷰어 역할을 한꺼번에 맡으려 하다가 셋 모두 엉망으로 합니다.

이것이 단일 에이전트의 한계입니다. 과제가 다음을 요구할 때마다 부딪히게 됩니다:

- **윈도우 하나에 담기보다 많은 컨텍스트** — 파일 50개를 읽으면 200k 토큰을 훌쩍 넘김
- **단계마다 다른 전문성** — 조사에는 코드 생성과 다른 프롬프팅이 필요함
- **병렬로 진행 가능한 작업** — 동시에 읽을 수 있는데 왜 파일 세 개를 순서대로 읽을까?

## 핵심 개념

### 단일 에이전트의 한계

단일 에이전트는 하나의 루프, 하나의 컨텍스트 윈도우, 하나의 시스템 프롬프트입니다. 그림으로 보면:

```
┌─────────────────────────────────────────┐
│            SINGLE AGENT                 │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │         Context Window            │  │
│  │                                   │  │
│  │  research notes                   │  │
│  │  + code files                     │  │
│  │  + test output                    │  │
│  │  + review feedback                │  │
│  │  + API docs                       │  │
│  │  + ...                            │  │
│  │                                   │  │
│  │  ██████████████████████ FULL ███  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  One system prompt tries to cover       │
│  research + coding + review + testing   │
│                                         │
│  Result: mediocre at everything         │
└─────────────────────────────────────────┘
```

셋이 무너집니다:

1. **컨텍스트 포화** — 도구 결과가 계속 쌓입니다. 30번째 턴쯤 되면 에이전트는 파일 내용, 명령 출력, 이전 추론으로 150k 토큰을 소진합니다. 5번째 턴의 중요한 세부 사항은 잃어버립니다.

2. **역할 혼동** — "너는 조사자이자 코더, 리뷰어, 테스터다"라고 말하는 시스템 프롬프트는 반쯤 조사하고 반쯤 코딩하면서 리뷰는 끝내지도 못하는 에이전트를 만들어냅니다.

3. **순차 처리 병목** — 에이전트는 파일 A를 읽고, 그다음 B, 그다음 C를 읽습니다. 세 번의 직렬 LLM 호출. 세 번의 직렬 도구 실행. 병렬성이 없습니다.

### 멀티 에이전트 해법

작업을 쪼갭니다. 각 에이전트에게 하나의 직업, 하나의 컨텍스트 윈도우, 그 직업에 맞게 조율된 하나의 시스템 프롬프트를 줍니다:

```
┌──────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
│                                                          │
│  "Build a REST API for user management"                  │
│                                                          │
│         ┌──────────┬──────────┬──────────┐               │
│         │          │          │          │               │
│         ▼          ▼          ▼          ▼               │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│   │RESEARCHER│ │  CODER   │ │ REVIEWER │ │  TESTER  │  │
│   │          │ │          │ │          │ │          │  │
│   │ Reads    │ │ Writes   │ │ Checks   │ │ Runs     │  │
│   │ docs,    │ │ code     │ │ code     │ │ tests,   │  │
│   │ finds    │ │ based on │ │ quality, │ │ reports  │  │
│   │ patterns │ │ research │ │ finds    │ │ results  │  │
│   │          │ │ + spec   │ │ bugs     │ │          │  │
│   └─────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│         │           │            │             │         │
│         └───────────┴────────────┴─────────────┘         │
│                          │                               │
│                     Merge results                        │
└──────────────────────────────────────────────────────────┘
```

각 에이전트는 다음을 갖습니다:
- 집중된 시스템 프롬프트("너는 코드 리뷰어다. 네 유일한 임무는 버그를 찾는 것이다.")
- 자기 전용 컨텍스트 윈도우(다른 에이전트의 작업으로 오염되지 않음)
- 명확한 입력/출력 계약(조사 노트를 받아 코드를 출력)

### 실제로 이렇게 하는 시스템들

**Claude Code 서브에이전트** — Claude Code가 `Task`로 서브에이전트를 생성하면, 범위가 지정된 과제를 가진 자식 에이전트를 만듭니다. 부모는 자기 컨텍스트를 깨끗하게 유지하고, 자식은 집중된 작업을 한 뒤 요약을 반환합니다.

**Devin** — 플래너 에이전트, 코더 에이전트, 브라우저 에이전트를 실행합니다. 플래너는 작업을 단계로 나눕니다. 코더는 코드를 씁니다. 브라우저는 문서를 조사합니다. 각자 별도의 컨텍스트를 가집니다.

**멀티 에이전트 코딩 팀(SWE-bench)** — SWE-bench 상위 성능 시스템들은 코드베이스를 읽는 리서처, 수정을 설계하는 플래너, 구현하는 코더를 사용합니다. 단일 에이전트 시스템은 점수가 더 낮습니다.

**ChatGPT Deep Research** — 여러 검색 에이전트를 병렬로 생성해 각기 다른 각도를 탐색하게 한 뒤, 결과를 종합합니다.

### 스펙트럼

멀티 에이전트는 이분법이 아닙니다. 스펙트럼입니다:

```
SIMPLE ──────────────────────────────────────────── COMPLEX

 Single        Sub-         Pipeline      Team         Swarm
 Agent         agents

 ┌───┐       ┌───┐        ┌───┐───┐    ┌───┐───┐    ┌─┐┌─┐┌─┐
 │ A │       │ A │        │ A │ B │    │ A │ B │    │ ││ ││ │
 └───┘       └─┬─┘        └───┘─┬─┘    └─┬─┘─┬─┘    └┬┘└┬┘└┬┘
               │                │        │   │       ┌┴──┴──┴┐
             ┌─┴─┐          ┌───┘───┐    │   │       │shared │
             │ a │          │ C │ D │  ┌─┴───┴─┐    │ state │
             └───┘          └───┘───┘  │  msg   │    └───────┘
                                       │  bus   │
 1 loop      Parent +      Stage by    │       │    N peers,
 1 context   child tasks   stage       └───────┘    emergent
                                       Explicit      behavior
                                       roles
```

**단일 에이전트** — 하나의 루프, 하나의 프롬프트. 간단한 과제에 적합.

**서브에이전트** — 부모가 집중된 하위 과제를 위해 자식을 생성합니다. 부모가 계획을 유지하고 자식이 보고합니다. Claude Code가 하는 방식입니다.

**파이프라인** — 에이전트가 순서대로 실행됩니다. 에이전트 A의 출력이 에이전트 B의 입력이 됩니다. 단계형 워크플로(조사 -> 코드 -> 리뷰 -> 테스트)에 적합.

**팀** — 에이전트가 공유 메시지 버스와 함께 병렬로 실행됩니다. 각자 역할이 있고 오케스트레이터가 조율합니다. 서로 다른 스킬이 동시에 필요할 때 적합.

**스웜** — 공유 상태를 가진, 동일하거나 거의 동일한 많은 에이전트. 고정된 오케스트레이터가 없습니다. 에이전트들이 큐에서 작업을 가져갑니다. 높은 처리량의 병렬 과제에 적합.

### 네 가지 멀티 에이전트 패턴

#### 패턴 1: 파이프라인

```
Input ──▶ Agent A ──▶ Agent B ──▶ Agent C ──▶ Output
          (research)  (code)      (review)
```

각 에이전트는 데이터를 변환해 다음으로 넘깁니다. 추론이 단순합니다. 한 단계의 실패가 나머지 전체를 막습니다.

#### 패턴 2: Fan-out / Fan-in

```
                ┌──▶ Agent A ──┐
                │              │
Input ──▶ Split ├──▶ Agent B ──├──▶ Merge ──▶ Output
                │              │
                └──▶ Agent C ──┘
```

작업을 병렬 에이전트들에게 나눈 뒤 결과를 합칩니다. 독립적인 하위 과제로 분해되는 과제에 적합.

#### 패턴 3: 오케스트레이터-워커

```
                    ┌──────────┐
                    │  Orch.   │
                    └──┬───┬───┘
                  task │   │ task
                 ┌─────┘   └─────┐
                 ▼               ▼
           ┌──────────┐   ┌──────────┐
           │ Worker A │   │ Worker B │
           └──────────┘   └──────────┘
```

영리한 오케스트레이터가 무엇을 할지 결정하고, 워커에게 위임하고, 결과를 종합합니다. 오케스트레이터 자체도 워커를 생성하는 도구를 갖춘 에이전트입니다.

#### 패턴 4: 피어 스웜

```
         ┌───┐ ◄──── msg ────▶ ┌───┐
         │ A │                  │ B │
         └─┬─┘                  └─┬─┘
           │                      │
      msg  │    ┌───────────┐     │ msg
           └───▶│  Shared   │◄────┘
                │  State    │
           ┌───▶│  / Queue  │◄────┐
           │    └───────────┘     │
      msg  │                      │ msg
         ┌─┴─┐                  ┌─┴─┐
         │ C │ ◄──── msg ────▶ │ D │
         └───┘                  └───┘
```

중앙 오케스트레이터가 없습니다. 에이전트들이 피어 투 피어로 통신합니다. 결정은 상호작용에서 창발합니다. 디버깅이 어렵지만 많은 에이전트로 확장됩니다.

### 멀티 에이전트를 쓰지 말아야 할 때

멀티 에이전트는 복잡성을 더합니다. 에이전트 사이의 모든 메시지는 잠재적 실패 지점입니다. 디버깅이 "대화 하나 읽기"에서 "다섯 에이전트에 걸친 메시지 추적"으로 변합니다.

**단일 에이전트를 유지할 조건:**
- 과제가 하나의 컨텍스트 윈도우에 들어갈 때(작업 데이터가 ~100k 토큰 미만)
- 단계마다 다른 시스템 프롬프트가 필요 없을 때
- 순차 실행으로도 충분히 빠를 때
- 과제가 너무 단순해서 나누는 오버헤드가 가치보다 클 때

**복잡성 비용:**
- 에이전트 경계마다 손실 압축이 일어납니다: 에이전트 A의 전체 컨텍스트는 에이전트 B에게 보낼 메시지로 요약되면서 줄어듭니다
- 조율 논리(누가 무엇을, 언제, 어떤 순서로 하는가) 자체가 버그의 원천입니다
- 지연 시간이 늘어납니다: N개의 에이전트는 최소 N번의 직렬 LLM 호출을 의미하고, 주고받아야 하면 더 늘어납니다
- 비용이 곱해집니다: 각 에이전트가 독립적으로 토큰을 소모합니다

경험 법칙: 과제가 도구 호출 20회 미만이고 100k 토큰 안에 들어간다면, 단일 에이전트를 유지하세요.

```figure
swarm-messages
```

## 만들어 보기

### 단계 1: 과부하 걸린 단일 에이전트

모든 것을 혼자 하려는 단일 에이전트입니다. 하나의 거대한 시스템 프롬프트와, 조사·코드·리뷰를 전부 담는 하나의 컨텍스트 윈도우를 가집니다:

```typescript
type AgentResult = {
  content: string;
  tokensUsed: number;
  toolCalls: number;
};

async function singleAgentApproach(task: string): Promise<AgentResult> {
  const systemPrompt = `You are a full-stack developer. You must:
1. Research the requirements
2. Write the code
3. Review the code for bugs
4. Write tests
Do ALL of these in a single conversation.`;

  const contextWindow: string[] = [];
  let totalTokens = 0;
  let totalToolCalls = 0;

  const research = await fakeLLMCall(systemPrompt, `Research: ${task}`);
  contextWindow.push(research.output);
  totalTokens += research.tokens;
  totalToolCalls += research.calls;

  const code = await fakeLLMCall(
    systemPrompt,
    `Given this research:\n${contextWindow.join("\n")}\n\nNow write code for: ${task}`
  );
  contextWindow.push(code.output);
  totalTokens += code.tokens;
  totalToolCalls += code.calls;

  const review = await fakeLLMCall(
    systemPrompt,
    `Given all previous context:\n${contextWindow.join("\n")}\n\nReview the code.`
  );
  contextWindow.push(review.output);
  totalTokens += review.tokens;
  totalToolCalls += review.calls;

  return {
    content: contextWindow.join("\n---\n"),
    tokensUsed: totalTokens,
    toolCalls: totalToolCalls,
  };
}
```

이 접근의 문제점:
- 컨텍스트 윈도우가 단계마다 자랍니다. 리뷰 단계쯤 되면 조사 노트와 코드와 이전 추론이 전부 들어 있습니다.
- 시스템 프롬프트가 범용적입니다. 단계별로 조율할 수 없습니다.
- 병렬로 실행되는 것이 아무것도 없습니다.

### 단계 2: 전문 에이전트들

이제 쪼갭니다. 각 에이전트는 하나의 직업을 맡습니다:

```typescript
type SpecialistAgent = {
  name: string;
  systemPrompt: string;
  run: (input: string) => Promise<AgentResult>;
};

function createSpecialist(name: string, systemPrompt: string): SpecialistAgent {
  return {
    name,
    systemPrompt,
    run: async (input: string) => {
      const result = await fakeLLMCall(systemPrompt, input);
      return {
        content: result.output,
        tokensUsed: result.tokens,
        toolCalls: result.calls,
      };
    },
  };
}

const researcher = createSpecialist(
  "researcher",
  "You are a technical researcher. Read documentation, find patterns, and summarize findings. Output only the facts needed for implementation."
);

const coder = createSpecialist(
  "coder",
  "You are a senior TypeScript developer. Given requirements and research notes, write clean, tested code. Nothing else."
);

const reviewer = createSpecialist(
  "reviewer",
  "You are a code reviewer. Find bugs, security issues, and logic errors. Be specific. Cite line numbers."
);
```

각 전문가는 집중된 프롬프트를 가집니다. 각자 필요한 입력만 담은 깨끗한 컨텍스트 윈도우를 받습니다.

### 단계 3: 메시지로 조율하기

명시적인 메시지 전달로 전문가들을 연결합니다:

```typescript
type AgentMessage = {
  from: string;
  to: string;
  content: string;
  timestamp: number;
};

async function multiAgentApproach(task: string): Promise<AgentResult> {
  const messages: AgentMessage[] = [];
  let totalTokens = 0;
  let totalToolCalls = 0;

  const researchResult = await researcher.run(task);
  messages.push({
    from: "researcher",
    to: "coder",
    content: researchResult.content,
    timestamp: Date.now(),
  });
  totalTokens += researchResult.tokensUsed;
  totalToolCalls += researchResult.toolCalls;

  const coderInput = messages
    .filter((m) => m.to === "coder")
    .map((m) => `[From ${m.from}]: ${m.content}`)
    .join("\n");

  const codeResult = await coder.run(coderInput);
  messages.push({
    from: "coder",
    to: "reviewer",
    content: codeResult.content,
    timestamp: Date.now(),
  });
  totalTokens += codeResult.tokensUsed;
  totalToolCalls += codeResult.toolCalls;

  const reviewerInput = messages
    .filter((m) => m.to === "reviewer")
    .map((m) => `[From ${m.from}]: ${m.content}`)
    .join("\n");

  const reviewResult = await reviewer.run(reviewerInput);
  messages.push({
    from: "reviewer",
    to: "orchestrator",
    content: reviewResult.content,
    timestamp: Date.now(),
  });
  totalTokens += reviewResult.tokensUsed;
  totalToolCalls += reviewResult.toolCalls;

  return {
    content: messages.map((m) => `[${m.from} -> ${m.to}]: ${m.content}`).join("\n\n"),
    tokensUsed: totalTokens,
    toolCalls: totalToolCalls,
  };
}
```

각 에이전트는 자신에게 주소 지정된 메시지만 받습니다. 컨텍스트 오염이 없습니다. 리서처가 문서를 읽으며 쓴 50k 토큰은 리뷰어의 컨텍스트에 절대 들어가지 않습니다.

### 단계 4: 비교하기

```typescript
async function compare() {
  const task = "Build a rate limiter middleware for an Express.js API";

  console.log("=== Single Agent ===");
  const single = await singleAgentApproach(task);
  console.log(`Tokens: ${single.tokensUsed}`);
  console.log(`Tool calls: ${single.toolCalls}`);

  console.log("\n=== Multi-Agent ===");
  const multi = await multiAgentApproach(task);
  console.log(`Tokens: ${multi.tokensUsed}`);
  console.log(`Tool calls: ${multi.toolCalls}`);
}
```

멀티 에이전트 버전은 총 토큰을 더 씁니다(에이전트 셋, 별도의 LLM 호출 셋)하지만 각 에이전트의 컨텍스트는 깨끗하게 유지됩니다. 시스템 프롬프트가 전문화돼 있기 때문에 각 단계의 품질이 향상됩니다.

## 직접 사용해 보기

이 레슨은 언제 멀티 에이전트로 갈지 판단하는 재사용 가능한 프롬프트를 산출합니다. `outputs/prompt-multi-agent-decision.md`를 보세요.

## 연습 문제

1. 네 번째 전문가를 추가하세요: 코더에게서 코드를, 리뷰어에게서 리뷰 피드백을 받아 테스트를 작성하는 "tester" 에이전트
2. 파이프라인을 수정해 리뷰어가 코더에게 피드백을 되돌려 보내 수정 루프(최대 2회전)를 만들 수 있게 하세요
3. 순차 파이프라인을 fan-out으로 바꾸세요: 리서처와 "요구사항 분석기" 에이전트를 병렬로 실행한 뒤, 두 출력을 합쳐서 코더에게 전달하세요

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| 스웜 | "AI 에이전트의 군집 지능" | 공유 상태와 고정된 리더가 없는 피어 에이전트 집합. 행동은 국소 상호작용에서 창발한다. |
| 오케스트레이터 | "보스 에이전트" | 다른 에이전트를 생성·관리하는 도구를 가진 에이전트. 계획하고 위임하지만 실제 작업은 하지 않을 수도 있다. |
| 코디네이터 | "교통 정리 담당" | 규칙에 따라 에이전트 간 메시지를 라우팅하는 비에이전트 구성요소(보통 LLM이 아닌 그냥 코드). |
| 합의(Consensus) | "에이전트들이 동의한다" | 진행 전에 여러 에이전트가 합의에 도달해야 하는 프로토콜. 충돌하는 출력을 해결해야 할 때 사용. |
| 창발 행동 | "에이전트들이 스스로 알아냈다" | 에이전트 상호작용에서 생겨나지만 명시적으로 프로그래밍되지 않은 시스템 수준 패턴. 유익할 수도 해로울 수도 있다. |
| Fan-out / fan-in | "에이전트용 map-reduce" | 과제를 병렬 에이전트들에게 나누고(fan-out) 그 결과를 합치는 것(fan-in). |
| 메시지 전달 | "에이전트들이 서로 대화한다" | 에이전트 간 통신 메커니즘: 한 에이전트가 다른 에이전트에게 보내는 구조화된 데이터. 공유 컨텍스트 윈도우를 대체한다. |

## 더 읽을거리

- [The Landscape of Emerging AI Agent Architectures](https://arxiv.org/abs/2409.02977) - 멀티 에이전트 패턴 서베이
- [AutoGen: Enabling Next-Gen LLM Applications](https://arxiv.org/abs/2308.08155) - Microsoft의 멀티 에이전트 대화 프레임워크
- [Claude Code 서브에이전트 문서](https://docs.anthropic.com/en/docs/claude-code) - Claude Code가 Task로 위임하는 방식
- [CrewAI 문서](https://docs.crewai.com/) - 역할 기반 멀티 에이전트 프레임워크
