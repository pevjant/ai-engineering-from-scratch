> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# A2A — 에이전트 대 에이전트 프로토콜

> MCP는 에이전트가 도구를 쓰는(agent-to-tool) 방식입니다. A2A(Agent2Agent)는 에이전트끼리 대화하는(agent-to-agent) 방식 — 서로 다른 프레임워크로 만들어진, 내부가 보이지 않는 불투명(opaque) 에이전트들이 협업하게 해 주는 오픈 프로토콜입니다. 2025년 4월 구글이 공개했고, 2025년 6월 리눅스 재단에 기증했으며, 2026년 4월에 AWS, Cisco, Microsoft, Salesforce, SAP, ServiceNow 등 150개 이상의 지지 조직과 함께 v1.0에 도달했습니다. IBM의 ACP를 흡수했고 AP2 결제 확장을 추가했습니다. 이 레슨은 에이전트 카드(Agent Card), 작업(Task) 라이프사이클, 두 가지 전송 바인딩을 다룹니다.

**유형:** Build
**언어:** Python (stdlib, 에이전트 카드 + 작업 하네스)
**선수 지식:** 페이즈 13 · 06(MCP 기초), 페이즈 13 · 08(MCP 클라이언트)
**소요 시간:** 약 75분

## 학습 목표

- 에이전트-도구(MCP) 사용 사례와 에이전트-에이전트(A2A) 사용 사례를 구분할 수 있다.
- 스킬과 엔드포인트 메타데이터를 담은 에이전트 카드를 `/.well-known/agent.json`에 게시할 수 있다.
- 작업(Task) 라이프사이클(submitted → working → input-required → completed / failed / canceled / rejected)을 따라가 볼 수 있다.
- 파트(Part: 텍스트, 파일, 데이터)를 담은 메시지와 산출물인 아티팩트(Artifact)를 활용할 수 있다.

## 문제 상황

고객 서비스 에이전트가 보고서 작성을 전문 작성 에이전트에게 위임해야 한다고 합시다. A2A 이전의 선택지:

- 커스텀 REST API. 동작하지만 짝을 이룰 때마다 일회성 작업이 된다.
- 공유 코드베이스. 두 에이전트가 같은 프레임워크로 실행돼야 한다.
- MCP. 맞지 않습니다: MCP는 도구 호출용이지, 각자의 불투명한 내부 추론을 지키면서 두 에이전트가 협업하는 용도가 아닙니다.

A2A가 이 공백을 채웁니다. 상호작용을 "한 에이전트가 다른 에이전트에게 작업(Task)을 보낸다"로 모델링하며, 라이프사이클과 메시지, 아티팩트가 따라옵니다. 호출받은 에이전트의 내부 상태는 불투명하게 유지됩니다 — 호출자에게 보이는 것은 작업 상태 전이와 최종 산출물뿐입니다.

A2A는 "프레임워크가 다른 에이전트끼리 서로 대화하게 하자"는 프로토콜입니다. MCP를 대체하지 않으며, 둘은 보완 관계입니다.

## 개념

### 에이전트 카드(Agent Card)

A2A 호환 에이전트는 `/.well-known/agent.json`에 카드를 게시합니다:

```json
{
  "schemaVersion": "1.0",
  "name": "research-agent",
  "description": "Summarizes academic papers and drafts citations.",
  "url": "https://research.example.com/a2a",
  "version": "1.2.0",
  "skills": [
    {
      "id": "summarize_paper",
      "name": "Summarize a paper",
      "description": "Read a paper PDF and produce a 3-paragraph summary.",
      "inputModes": ["text", "file"],
      "outputModes": ["text", "artifact"]
    }
  ],
  "capabilities": {"streaming": true, "pushNotifications": true}
}
```

탐색은 URL 기반입니다: 카드를 가져오고, A2A 엔드포인트의 URL을 파악하고, 스킬을 나열합니다.

### 서명된 에이전트 카드(AP2)

AP2 확장(2025년 9월)은 에이전트 카드에 암호학적 서명을 더합니다. 게시자가 자기 카드를 JWT로 서명하고, 소비자가 검증합니다. 사칭을 막아 줍니다.

### 작업(Task) 라이프사이클

```
submitted -> working -> completed | failed | canceled | rejected
             -> input_required -> working (loop via message)
```

클라이언트가 `tasks/send`로 시작합니다. 호출받은 에이전트가 상태들을 거쳐 전이되고, 클라이언트는 SSE로 상태 업데이트를 구독하거나 폴링합니다.

### 메시지와 파트

메시지는 하나 이상의 파트(Part)를 실습니다:

- `text` — 일반 콘텐츠.
- `file` — mimeType이 붙은 base64 블롭.
- `data` — 타입이 지정된 JSON 페이로드(호출받은 에이전트를 위한 구조화 입력).

예제:

```json
{
  "role": "user",
  "parts": [
    {"type": "text", "text": "Summarize this paper."},
    {"type": "file", "file": {"name": "paper.pdf", "mimeType": "application/pdf", "bytes": "..."}},
    {"type": "data", "data": {"targetLength": "3 paragraphs"}}
  ]
}
```

### 아티팩트(Artifact)

산출물은 날 문자열이 아니라 아티팩트입니다. 아티팩트는 이름과 타입이 지정된 산출물입니다:

```json
{
  "name": "summary",
  "parts": [{"type": "text", "text": "..."}],
  "mimeType": "text/markdown"
}
```

아티팩트는 청크 단위로 스트리밍될 수 있습니다. 호출자가 모아서 합칩니다.

### 두 가지 전송 바인딩

1. **HTTP 위의 JSON-RPC.** `/a2a` 엔드포인트, 요청은 POST, 스트리밍에는 선택적 SSE. 기본 바인딩.
2. **gRPC.** gRPC가 기본 언어처럼 쓰이는 엔터프라이즈 환경용.

두 바인딩 모두 같은 논리적 메시지 형태를 실습니다.

### 불투명성 유지

핵심 설계 원칙: 호출받은 에이전트의 내부 상태는 불투명합니다. 호출자가 보는 것은 작업 상태와 아티팩트입니다. 호출받은 에이전트의 사고 연쇄(chain-of-thought), 도구 호출, 하위 에이전트 위임 — 모두 보이지 않습니다. 도구 호출이 투명한 MCP와는 다른 점입니다.

이유: A2A는 경쟁자들이 내부를 드러내지 않고 협업하게 해 줍니다. 호출자가 그 에이전트가 서비스를 어떻게 구현했는지 배우지 않은 채로 "이 고객 서비스 에이전트를 호출하라"는 식으로 A2A를 쓸 수 있습니다.

### 타임라인

- **2025-04-09.** 구글이 A2A를 발표합니다.
- **2025-06-23.** 리눅스 재단에 기증합니다.
- **2025-08.** IBM의 ACP를 흡수합니다.
- **2025-09.** AP2 확장(Agent Payments)이 출시됩니다.
- **2026-04.** 150개 이상 지지 조직과 함께 v1.0이 출시됩니다.

### MCP와의 관계

| 차원 | MCP | A2A |
|-----------|-----|-----|
| 사용 사례 | 에이전트-도구 | 에이전트-에이전트 |
| 불투명성 | 투명한 도구 호출 | 불투명한 내부 추론 |
| 일반적인 호출자 | 에이전트 런타임 | 또 다른 에이전트 |
| 상태 | 도구 호출 결과 | 라이프사이클이 있는 작업 |
| 인가 | OAuth 2.1 (페이즈 13 · 16) | JWT 서명 에이전트 카드(AP2) |
| 전송 | Stdio / Streamable HTTP | HTTP 위의 JSON-RPC / gRPC |

특정 도구를 호출하고 싶으면 MCP를 쓰세요. 작업 전체를 다른 에이전트에게 위임하고 싶으면 A2A를 쓰세요. 많은 프로덕션(운영 환경) 시스템이 둘 다 씁니다: 에이전트가 도구 계층에는 MCP를, 협업 계층에는 A2A를 사용합니다.

```figure
a2a-task-lifecycle
```

## 활용하기

`code/main.py`는 최소한의 A2A 하네스를 구현합니다: 리서치 에이전트가 자기 카드를 게시하고, 작성 에이전트가 PDF와 텍스트 지시를 포함한 파트를 담은 `tasks/send`를 받아, working → input_required → working → completed로 전이하며, 텍스트 아티팩트를 돌려줍니다. 전부 stdlib이며, 메시지 형태에 집중하기 위해 인메모리 전송을 씁니다.

볼 지점:

- 에이전트 카드 JSON 형태.
- 작업 id 할당과 상태 전이.
- 혼합 타입 파트를 담은 메시지.
- 작업 중간의 input-required 분기.
- 완료 시 아티팩트 반환.

## 출시하기

이 레슨은 `outputs/skill-a2a-agent-spec.md`를 산출합니다. 다른 에이전트가 호출할 수 있어야 하는 새 에이전트가 주어지면, 이 스킬은 에이전트 카드 JSON, 스킬 스키마, 엔드포인트 설계도를 산출합니다.

## 연습 문제

1. `code/main.py`를 실행하고, 호출받은 에이전트가 명확화를 요청하는 input-required 일시 정지를 포함해 전체 작업 라이프사이클을 추적하세요.

2. 서명된 에이전트 카드를 추가하세요. 카드의 캐노니컬 JSON에 대해 HMAC으로 서명하세요. 검증기를 작성하고, 변형된 카드에서 실패하는지 확인하세요.

3. 작업 스트리밍을 구현하세요: 작성 에이전트가 SSE로 세 개의 증분 아티팩트 청크를 내보내고, 호출자가 그것들을 모아 합칩니다.

4. MCP 서버를 감싸는 A2A 에이전트를 설계하세요. 각 MCP 도구를 A2A 스킬에 매핑하세요. 트레이드오프를 적어 보세요 — 어떤 불투명성이 사라지는가?

5. A2A v1.0 발표를 읽고, 2026년 4월 기준 어떤 프레임워크도 아직 구현하지 않은 단 하나의 기능을 찾으세요. (힌트: 다단 홉(multi-hop) 작업 위임과 관련이 있습니다.)

## 핵심 용어

| 용어 | 사람들이 부르는 이름 | 실제 의미 |
|------|----------------|------------------------|
| A2A | "Agent-to-Agent 프로토콜" | 불투명한 에이전트 협업을 위한 오픈 프로토콜 |
| 에이전트 카드 | "`.well-known/agent.json`" | 에이전트의 스킬과 엔드포인트를 기술하는 게시된 메타데이터 |
| 스킬 | "호출 가능한 단위" | 에이전트가 지원하는 이름 있는 작업(MCP 도구에 해당) |
| 작업(Task) | "위임 단위" | 라이프사이클과 최종 아티팩트를 가진 작업 항목 |
| 메시지 | "작업 입력" | 파트(텍스트, 파일, 데이터)를 실음 |
| 파트(Part) | "타입이 지정된 청크" | 메시지의 `text` / `file` / `data` 구성 요소 |
| 아티팩트 | "작업 출력" | 완료 시 돌려주는 이름·타입이 지정된 산출물 |
| AP2 | "Agent Payments Protocol" | 신뢰와 결제를 위한 서명된 에이전트 카드 확장 |
| 불투명성(Opacity) | "블랙박스 협업" | 호출받은 에이전트의 내부가 호출자에게 숨겨짐 |
| Input-required | "작업 일시 정지" | 에이전트가 더 많은 정보를 필요로 할 때의 라이프사이클 상태 |

## 더 읽을거리

- [a2a-protocol.org](https://a2a-protocol.org/latest/) — 공식 A2A 명세
- [a2aproject/A2A — GitHub](https://github.com/a2aproject/A2A) — 참조 구현과 SDK
- [Linux Foundation — A2A 출범 보도자료](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents) — 2025년 6월 거버넌스 이관
- [Google Cloud — A2A 프로토콜 업그레이드](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade) — 로드맵과 파트너 동향
- [Google Dev — A2A 1.0 마일스톤](https://discuss.google.dev/t/the-a2a-1-0-milestone-ensuring-and-testing-backward-compatibility/352258) — v1.0 릴리스 노트와 하위 호환성 가이드
