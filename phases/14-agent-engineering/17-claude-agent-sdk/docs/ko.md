# 라이브러리로서의 하네스스 — 서브에이전트와 세션 저장소

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 임포트할 수 있는 하네스스: 내장 도구, 컨텍스트 격리용 서브에이전트, 훅, W3C 추적 전파, 세션 영속화. Claude Agent SDK가 기준 예시입니다 — Claude Code 하네스스의 라이브러리 형태죠 — 그리고 장기 비동기 작업용 호스팅 대안이 Claude Managed Agents입니다.

**유형:** 학습 + 빌드
**언어:** Python (표준 라이브러리)
**선수 지식:** 페이즈 14 · 01 (에이전트 루프), 페이즈 14 · 10 (스킬 라이브러리)
**시간:** 약 75분

## 학습 목표

- Anthropic Client SDK(날것의 API)와 Claude Agent SDK(하네스스 모양)의 차이를 설명할 수 있습니다.
- 서브에이전트 — 병렬화와 컨텍스트 격리 — 를 설명하고 언제 꺼내 쓰는지 말할 수 있습니다.
- Python SDK의 세션 저장소 표면(`append`, `load`, `list_sessions`, `delete`, `list_subkeys`)과 `--session-mirror`의 역할을 말할 수 있습니다.
- 내장 도구, 격리된 컨텍스트로 서브에이전트 생성, 라이프사이클 훅, 세션 저장소를 갖춘 표준 라이브러리 하네스스를 구현합니다.

## 문제

날것의 LLM API는 왕복 한 번을 주지만, 프로덕션 에이전트는 도구 실행, MCP 서버, 라이프사이클 훅, 서브에이전트 생성, 세션 영속화, 추적 전파가 필요합니다. Claude Agent SDK는 이 모양을 라이브러리로 실어 나옵니다 — Claude Code가 쓰는 바로 그 하네스스를 커스텀 에이전트용으로 내어 놓은 것입니다.

## 개념

### Client SDK vs Agent SDK

- **Client SDK (`anthropic`).** 날것의 Messages API. 루프, 도구, 상태를 여러분이 소유합니다.
- **Agent SDK (`claude-agent-sdk`).** 내장 도구 실행, MCP 연결, 훅, 서브에이전트 생성, 세션 저장소. Claude Code 루프를 라이브러리로 만든 것.

### 내장 도구

SDK는 10개가 넘는 도구를 기본으로 실어 나옵니다: 파일 읽기/쓰기, 셸, grep, glob, 웹 가져오기 등. 커스텀 도구는 표준 도구 스키마 인터페이스로 등록합니다.

### 서브에이전트

Anthropic이 문서화한 두 가지 목적:

1. **병렬화.** 독립된 작업을 동시에 돌립니다. "이 20개 모듈 각각의 테스트 파일을 찾아줘"는 병렬 서브에이전트 태스크 20개입니다.
2. **컨텍스트 격리.** 서브에이전트는 자기만의 컨텍스트 윈도우를 쓰고, 결과만 오케스트레이터에게 돌아옵니다. 오케스트레이터의 예산은 지켜집니다.

Python SDK의 최근 추가 기능: 서브에이전트 기록을 읽기 위한 `list_subagents()`, `get_subagent_messages()`.

### 세션 저장소

TypeScript와의 프로토콜 동등성:

- `append(session_id, message)` — 턴을 추가합니다.
- `load(session_id)` — 대화를 복원합니다.
- `list_sessions()` — 나열합니다.
- `delete(session_id)` — 서브에이전트 세션으로 연쇄(cascade)됩니다.
- `list_subkeys(session_id)` — 서브에이전트 키를 나열합니다.

`--session-mirror`(CLI 플래그)는 스트리밍되는 대로 기록을 외부 파일로 거울처럼 복사해 디버깅에 씁니다.

### 훅

등록할 수 있는 라이프사이클 훅:

- `PreToolUse`, `PostToolUse` — 도구 호출을 막거나 감사합니다.
- `SessionStart`, `SessionEnd` — 준비하고 정리합니다.
- `UserPromptSubmit` — 모델이 보기 전에 사용자 입력에 개입합니다.
- `PreCompact` — 컨텍스트 압축 전에 실행됩니다.
- `Stop` — 에이전트 종료 시 청소합니다.
- `Notification` — 곁채널 알림입니다.

훅은 pro-workflow(페이즈 14 커리큘럼 참조) 같은 시스템이 횡단 관심사를 더하는 방식입니다.

### W3C 추적 컨텍스트

호출자에서 활성화된 OTel 스팬은 W3C 추적 컨텍스트 헤더를 통해 CLI 서브프로세스로 전파됩니다. 여러 프로세스에 걸친 추적 전체가 여러분의 백엔드에서 하나의 트레이스로 보입니다.

### Claude Managed Agents

호스팅 대안입니다(베타 헤더 `managed-agents-2026-04-01`). 장기 비동기 작업, 내장 프롬프트 캐싱, 내장 압축. 관리형 인프라와 통제권을 맞바꿉니다.

### 이 패턴이 잘못되는 지점

- **서브에이전트 과다 생성.** 아주 작은 태스크 100개에 서브에이전트 100개. 오버헤드가 지배합니다. 배치로 묶으세요.
- **훅 불어나기.** 팀마다 훅을 더해 시작 시간이 풍선처럼 불어납니다. 훅을 분기마다 점검하세요.
- **세션 비대.** 세션이 쌓이고 크기가 자랍니다. `list_sessions` + 만료 정책을 쓰세요.

```figure
ae-subagent-isolation
```

## 직접 만들기

`code/main.py`는 SDK 모양을 표준 라이브러리로 구현합니다:

- 내장 `read_file`, `write_file`, `list_dir`을 갖춘 `Tool`, `ToolRegistry`.
- `Subagent` — 비공개 컨텍스트, 격리된 실행, 결과 반환.
- `SessionStore` — append, load, list, delete, list_subkeys.
- `Hooks` — `pre_tool_use`, `post_tool_use`, `session_start`, `session_end`.
- 데모: 메인 에이전트가 서브에이전트 3개를 병렬로 생성하고(각각 격리됨) 결과를 모아 세션을 영속화합니다.

실행 방법:

```
python3 code/main.py
```

추적 결과에는 서브에이전트 컨텍스트 격리(오케스트레이터 컨텍스트 크기가 한도 안에 머뭄), 훅 실행, 세션 영속화가 나옵니다.

## 활용하기

- Claude Code 하네스스 모양을 원하는 Claude 우선 제품에는 **Claude Agent SDK**.
- 호스팅되는 장기 비동기 작업에는 **Claude Managed Agents**.
- OpenAI 우선 짝에는 **OpenAI Agents SDK**(레슨 16).
- 대신 그래프 모양 상태 기계를 원한다면 **LangGraph + 커스텀 도구**.

## 산출물 내보내기

`outputs/skill-claude-agent-scaffold.md`는 서브에이전트, 훅, 세션 저장소, MCP 서버 연결, W3C 추적 전파를 갖춘 Claude Agent SDK 앱의 뼈대를 만들어 줍니다.

## 연습 문제

1. 태스크 20개를 병렬 서브에이전트 5개 묶음으로 배치하는 서브에이전트 생성기를 추가하세요. 태스크당 하나일 때와 오케스트레이터 컨텍스트 크기를 비교합니다.
2. `write_file` 호출을 비율 제한(세션당 분당 5회)하는 `PreToolUse` 훅을 구현하세요. 동작을 추적합니다.
3. `list_subkeys`를 연결해 서브에이전트 트리를 그려 보세요. 깊은 중첩은 어떤 모습일까요?
4. 연습용 구현을 진짜 `claude-agent-sdk` Python 패키지로 옮기세요. 도구 등록은 어떻게 달라지나요?
5. Claude Managed Agents 문서를 읽어 보세요. 직접 호스팅에서 관리형으로 언제 바꾸겠나요?

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| Agent SDK | "라이브러리로서의 Claude Code" | 하네스스 모양: 도구, MCP, 훅, 서브에이전트, 세션 저장소 |
| Subagent | "자식 에이전트" | 별개 컨텍스트, 자기 예산. 결과는 위로 올라옴 |
| 세션 저장소 | "대화 DB" | 서브에이전트 연쇄 삭제를 곁들인 턴 영속화·복원·나열·삭제 |
| Hook | "라이프사이클 콜백" | 도구 전/후, 세션, 프롬프트 제출, 압축, 정지 |
| W3C 추적 컨텍스트 | "교차 프로세스 추적" | 부모 스팬이 CLI 서브프로세스로 전파됨 |
| Managed Agents | "호스팅 하네스스" | Anthropic이 호스팅하는 장기 비동기 작업 |
| `--session-mirror` | "기록 거울" | 스트리밍되는 대로 세션 턴을 외부 파일에 기록 |
| MCP 서버 | "도구 표면" | 에이전트에 붙는 외부 도구/리소스 공급원 |

## 더 읽을거리

- [Claude Agent SDK 개요](https://platform.claude.com/docs/en/agent-sdk/overview) — 라이브러리 형태의 Claude Code
- [Anthropic, Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — 프로덕션 패턴
- [Claude Managed Agents 개요](https://platform.claude.com/docs/en/managed-agents/overview) — 호스팅 대안
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — 짝이 되는 SDK
