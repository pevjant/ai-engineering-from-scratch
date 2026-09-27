---
name: state-schema
description: 에이전트 상태와 태스크 보드를 위한 프로젝트 전용 JSON 스키마, 원자적 쓰기를 갖춘 Python StateManager, 그리고 스키마 버전 올림이 워크벤치를 망가뜨리지 못하게 하는 마이그레이션 스캐폴드를 생성합니다.
version: 1.0.0
phase: 14
lesson: 34
tags: [state, schema, json-schema, atomic-writes, migrations]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-state-schema.md](skill-state-schema.md)


저장소와 그 안에서 돌아가는 에이전트 제품이 주어지면, 워크벤치를 위한 스키마 우선(state-schema-first) 상태 파일을 만들어 냅니다.

만들 것:

1. `schemas/agent_state.schema.json` — 필수 키, 허용되는 status 값, "배열인지 null인지"의 규율, `schema_version` 정수를 다룹니다.
2. `schemas/task_board.schema.json` — 태스크 ID 패턴, 허용되는 담당자, 허용되는 상태, 수용 기준(acceptance) 배열을 다룹니다.
3. `tools/state_manager.py` — 임시 파일 + 이름 바꾸기 원자적 쓰기를 갖춘 `load`, `commit`, `update`를 제공합니다.
4. `tools/migrate_state.py` — 다음 스키마 버전 올림을 위한 스캐폴드. 알 수 없는 버전의 파일이면 큰 소리로 실패(fail-loud)합니다.
5. `schema_version: 1`로 시드한 `agent_state.json`과 `task_board.json`, 그리고 깨끗한 초기 백로그.

하드 거부(hard reject) 항목:

- `schema_version` 필드가 없는 스키마. 마이그레이션은 선택이 아닙니다.
- 배열이 와야 할 자리에 `null`을 허용하는 것. `null`은 데이터인 척하는 쓰기 시점의 버그입니다.
- 평범한 `open(path, "w")`를 쓰는 작성 코드. 원자적 쓰기만 허용됩니다. 부분적으로 쓰인 파일은 단일 진실 공급원을 망가뜨립니다.
- 상태 안에 토큰, 원본 채팅 전사문, PII(개인 식별 정보)를 저장하는 것. 상태는 저장소와 관련된 사실을 위한 자리입니다.

거부 규칙:

- 저장소에 버전 관리가 없다면, 상태 파일 출시를 거부합니다. 원자적 쓰기 + git diff가 곧 내구성 전략입니다.
- 프로젝트에 `done` 전이를 검증할 수 있는 수용 명령이 하나도 없다면, `status: done` enum 값을 거부합니다. 수용 검증 없는 `done` 추가는 눈가속(보여주기)일 뿐입니다.
- 프로젝트가 잠금(lock) 전략 없이 여러 프로세스가 상태를 공유하려 한다면, 출시 전에 그 사실을 먼저 드러냅니다. 원자적 이름 바꾸기는 필요 조건이지 충분 조건이 아닙니다.

출력 구조:

```
<repo>/
├── agent_state.json
├── task_board.json
├── schemas/
│   ├── agent_state.schema.json
│   └── task_board.schema.json
└── tools/
    ├── state_manager.py
    └── migrate_state.py
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 시작 때 관리자를 호출하는 초기화 스크립트는 레슨 35.
- 상태를 읽어 완성도를 채점하는 검증 게이트는 레슨 38.
- 같은 스키마를 소비하는 핸드오프 생성기는 레슨 40.
