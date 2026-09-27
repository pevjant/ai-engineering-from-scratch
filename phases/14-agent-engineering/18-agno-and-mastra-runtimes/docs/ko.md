# 프로덕션 에이전트 런타임 — 빠른 인스턴스화와 타입 지정 워크플로

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 프로덕션 에이전트 런타임은 프로토타이핑 프레임워크가 외면하는 것을 최적화합니다: 인스턴스화 비용, 타입 지정 워크플로 표면, 서빙 준비가 된 백엔드. 2026년의 짝: Agno(Python)는 마이크로초 단위 에이전트 인스턴스화와 상태 없는 FastAPI 백엔드를 겨냥합니다. Mastra는 Vercel AI SDK 기판 위에 에이전트, 도구, 워크플로, 통합 모델 라우팅, 컴포지트 스토리지를 실어 나옵니다.

**유형:** 학습
**언어:** Python, TypeScript
**선수 지식:** 페이즈 14 · 01 (에이전트 루프), 페이즈 14 · 13 (LangGraph)
**시간:** 약 45분

## 학습 목표

- Agno의 성능 목표와 그것이 중요해지는 때를 가려낼 수 있습니다.
- Mastra의 세 기본 요소 — Agents, Tools, Workflows — 와 지원되는 서버 어댑터를 말할 수 있습니다.
- 상태 없는 세션 범위 FastAPI 백엔드가 권장되는 Agno 프로덕션 경로인 이유를 설명할 수 있습니다.
- 주어진 스택에서 Agno와 Mastra 중 고를 수 있습니다(Python 우선 vs TypeScript 우선).

## 문제

LangGraph, AutoGen, CrewAI는 프레임워크가 무겁습니다. "그냥 에이전트 루프만, 빠르게, 내 런타임에서"를 원하는 팀들은 Agno(Python)나 Mastra(TypeScript)를 꺼냅니다. 둘 다 프레임워크가 소유하던 기본 요소 일부를 날것의 속도와 주변 스택과의 더 촘촘한 결합으로 맞바꿉니다.

## 개념

### Agno

- Python 런타임, 예전 이름은 Phi-data.
- "그래프도, 체인도, 꼬인 패턴도 없다 — 순수 Python만 있을 뿐."
- 공식 문서가 내세우는 성능 목표: 에이전트 인스턴스화 약 2μs, 에이전트당 메모리 약 3.75 KiB, 모델 제공자 약 23곳.
- 프로덕션 경로: 상태 없는 세션 범위 FastAPI 백엔드. 요청마다 새 에이전트를 시작하고, 세션 상태는 DB에 삽니다.
- 네이티브 멀티모달(텍스트, 이미지, 오디오, 비디오, 파일)과 에이전틱 RAG.

속도 목표는 초당 수천 개의 단명 에이전트를 굴릴 때(채팅 팬인, 평가 파이프라인) 빛을 봅니다. 에이전트 하나가 10분씩 돌 때는 덜 중요하죠.

### Mastra

- TypeScript, Vercel AI SDK 위에 지어짐.
- 세 가지 기본 요소: **Agents**, **Tools**(Zod 타입), **Workflows**.
- 통합 모델 라우터 — 94개 제공자의 3,300개 이상 모델(2026년 3월 기준).
- 컴포지트 스토리지: 메모리, 워크플로, 관측 데이터를 서로 다른 백엔드로. 대규모 관측에는 ClickHouse를 권합니다.
- Apache 2.0이지만 `ee/` 디렉터리는 소스 공개 엔터프라이즈 라이선스입니다.
- Express, Hono, Fastify, Koa용 서버 어댑터. Next.js와 Astro는 일급 통합.
- 디버깅용 Mastra Studio(localhost:4111)를 실어 나옵니다.
- GitHub 스타 2.2만 이상, 1.0(2026년 1월) 기준 주간 npm 다운로드 30만 이상.

### 포지셔닝

둘 다 LangGraph가 되려 하지 않습니다. 겨루는 지점은:

- **언어 적합성.** Python 우선 팀엔 Agno, TypeScript 우선 팀엔 Mastra.
- **런타임 사용성.** Agno = 거의 0에 가까운 오버헤드. Mastra = Vercel 생태계와의 통합.
- **관측 가능성.** 둘 다 Langfuse/Phoenix/Opik(레슨 24)과 연동되지만 Mastra Studio는 자사 제품입니다.

### 언제 무엇을 고를까

- **Agno** — Python 백엔드, 수많은 단명 에이전트, 강한 성능 요구, FastAPI 팀.
- **Mastra** — TypeScript 백엔드, Next.js / Vercel 배포, 통합 멀티 제공자 모델 라우팅, Zod 타입 도구.
- **LangGraph**(레슨 13) — 내구 상태와 명시적 그래프 추론이 날것의 속도보다 중요할 때.
- **OpenAI / Claude Agent SDK** — 제공자가 제품화한 모양을 원할 때(레슨 16~17).

### 이 패턴이 잘못되는 지점

- **성능을 위한 성능.** 워크로드가 요청당 느린 에이전트 호출 하나인데 "2μs"가 좋아 보인다는 이유로 Agno를 고르는 것. 오버헤드는 병목이 아닙니다.
- **생태계 종속.** Mastra의 Vercel 빛깔 통합은 Vercel에서는 플러스지만 그 밖에서는 마이너스입니다.
- **엔터프라이즈 라이선스 혼동.** Mastra의 `ee/` 디렉터리는 Apache 2.0이 아니라 소스 공개 라이선스입니다. 포크할 계획이라면 라이선스를 읽으세요.

```figure
wb-runtime-spawn
```

## 직접 만들기

이 레슨은 주로 비교입니다 — 단일 코드 산출물로는 두 프레임워크 모두에게 공정할 수 없습니다. `code/main.py`의 나란히 놓인 연습용 구현을 보세요: "에이전트 실행, 출력 스트리밍, 세션 영속화"라는 최소 흐름을 두 번 구현합니다(한 번은 Agno 모양, 한 번은 Mastra 모양).

실행 방법:

```
python3 code/main.py
```

구조는 다르지만 기능적으로 동등한 추적 두 개가 나옵니다.

## 활용하기

- **Agno** — 속도와 FastAPI 모양이 필요한 Python 백엔드.
- **Mastra** — 많은 제공자와 워크플로 기본 요소가 필요한 TypeScript 백엔드.
- 둘 다 자사 관측 훅을 실어 나오고, 둘 다 Langfuse와 연동됩니다.

## 산출물 내보내기

`outputs/skill-runtime-picker.md`는 스택, 지연 시간 예산, 운영 형태를 근거로 Agno, Mastra, LangGraph, 제공자 SDK 중 하나를 골라 줍니다.

## 연습 문제

1. Agno 문서를 읽어 보세요. 표준 라이브러리 ReAct 루프(레슨 01)를 Agno로 옮깁니다. 무엇이 사라졌나요? 무엇이 남았나요?
2. Mastra 문서를 읽어 보세요. 같은 루프를 Mastra로 옮깁니다. 도구 타이핑은 어떻게 달라지나요(Zod vs 없음)?
3. 벤치마크: 여러분의 스택에서 에이전트 인스턴스화 지연 시간을 측정하세요. Agno의 2μs가 여러분의 워크로드에 의미가 있나요?
4. 이전 설계: Python으로 CrewAI를 굴려 왔다면 Agno로 옮길 때 무엇이 깨질까요?
5. Mastra의 `ee/` 라이선스 조건을 읽어 보세요. 어떤 제한이 오픈소스 포크에 영향을 줄까요?

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| Agno | "빠른 Python 에이전트" | 상태 없는 세션 범위 에이전트 런타임 |
| Mastra | "Vercel AI SDK 위의 TypeScript 에이전트" | Agents + Tools + Workflows + Model Router |
| 통합 모델 라우터 | "멀티 제공자 접근" | 94개 제공자의 3,300개 이상 모델을 위한 단일 클라이언트 |
| 컴포지트 스토리지 | "여러 백엔드" | 메모리/워크플로/관측을 각각 다른 저장소로 |
| Mastra Studio | "로컬 디버거" | 에이전트를 들여다보는 localhost:4111 UI |
| 소스 공개 | "OSS 아님" | 소스 읽기는 허용하지만 상업적 사용은 제한하는 라이선스 |

## 더 읽을거리

- [Agno Agent Framework 문서](https://www.agno.com/agent-framework) — 성능 목표, FastAPI 통합
- [Mastra 문서](https://mastra.ai/docs) — 기본 요소, 서버 어댑터, Model Router
- [LangGraph 개요](https://docs.langchain.com/oss/python/langgraph/overview) — 상태 기반 그래프 대안
- [Comet Opik](https://www.comet.com/site/products/opik/) — Mastra 연동이 인용하는 관측 비교
