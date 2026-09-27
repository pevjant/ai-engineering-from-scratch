---
name: minimal-workbench
description: 어떤 저장소에든 세 파일 최소 실행 가능 에이전트 워크벤치를 깔아 줍니다 — 짧은 AGENTS.md 라우터, 내구성 있는 agent_state.json, 프로젝트의 현재 백로그에 맞춘 JSON task_board.json.
version: 1.0.0
phase: 14
lesson: 32
tags: [workbench, agents-md, state, task-board, scaffold]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-minimal-workbench.md](skill-minimal-workbench.md)

저장소 경로와 짧은 백로그가 주어지면 최소 실행 가능 에이전트 워크벤치의 뼈대를 만듭니다.

산출물:

1. 80줄을 넘지 않는 `AGENTS.md`. 다음으로 안내해야 합니다. 상태 파일, 작업 보드, 더 깊은 규칙 문서(비어 있더라도), 검증 명령. 이 파일에 산문 튜토리얼은 넣지 않습니다.
2. 다음 키를 가진 `agent_state.json`: `active_task_id`, `touched_files`, `assumptions`, `blockers`, `next_action`. 선택적 필드는 모두 빈 배열 또는 빈 문자열을 기본값으로 하며, 배열에 `null`을 쓰지 않습니다.
3. JSON 배열 형태의 `task_board.json`. 각 과제는 `id`, `goal`, `owner` (`builder` | `reviewer` | `human`), `acceptance`(문자열 목록), `status` (`todo` | `in_progress` | `done` | `blocked`)를 가집니다.
4. 표면마다 H2 하나씩만 있는 `docs/agent-rules.md` 플레이스홀더. 이후 레슨이 채워 넣을 수 있게 합니다.

하드 리젝(무조건 거절):

- 80줄을 넘거나 10줄에 못 미치는 `AGENTS.md`. 너무 길면 에이전트가 건너뛰고, 너무 짧으면 안내를 담지 못합니다.
- 저장소 대신 채팅 기록을 참조하는 상태 파일. 저장소가 기록의 시스템입니다.
- `acceptance` 없는 작업 보드. 수용 기준 없는 과제는 "괜찮아 보임" 도장이 됩니다.
- `owner`가 `agent`나 `model`인 과제. 소유자는 역할이지 개체가 아닙니다.

거절 규칙:

- 저장소에 검증 명령이 없으면 하나가 제공되거나 스텁으로 만들어질 때까지 `AGENTS.md` 작성을 거절합니다. 없는 게이트를 가리키는 라우터는 라우터가 아예 없는 것보다 나쁩니다.
- 백로그의 열린 과제가 12개를 넘으면 거절하고 사용자에게 분할을 요청합니다. 한 화면을 넘는 보드는 계획 쇼로 흘러갑니다.
- 프로젝트가 버전 관리되는 파일에 시크릿을 담고 출시된다면 상태 파일 작성을 거절하고, 시크릿 유출을 먼저 차단 사항으로 드러냅니다.

출력 구조:

```
<repo>/
├── AGENTS.md
├── agent_state.json
├── task_board.json
└── docs/
    └── agent-rules.md
```

마지막에 "다음에 읽을 것"으로 다음을 가리킵니다.

- 규칙 플레이스홀더를 실행 가능한 제약으로 바꾸는 것은 레슨 33.
- 내구성 상태 스키마는 레슨 34.
- 과제별 범위 계약은 레슨 36.
