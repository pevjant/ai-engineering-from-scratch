---
name: rule-set-builder
description: 프로젝트 소유자와 인터뷰하고 기존 산문 지시를 다섯 개 운영 카테고리로 분류한 뒤, 버전 관리되는 agent-rules.md와 Python 검사기 스텁을 내놓습니다.
version: 1.0.0
phase: 14
lesson: 33
tags: [rules, instructions, constraints, checker, workbench]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-rule-set-builder.md](skill-rule-set-builder.md)

저장소와 기존 산문 지시(`AGENTS.md`, `CONTRIBUTING.md`, 온보딩 문서)가 주어지면 워크벤치가 실행할 수 있는 다섯 카테고리 규칙 집합을 만듭니다.

다섯 카테고리:

1. `startup` — 작업 시작 전에 참이어야 하는 것.
2. `forbidden` — 절대 일어나면 안 되는 것.
3. `definition_of_done` — 무엇이 과제 완료를 증명하는가.
4. `uncertainty` — 확신이 없을 때 에이전트가 하는 것.
5. `approval` — 인간 서명을 요구하는 것.

산출물:

1. 규칙마다 `##` 제목 하나씩 있는 `docs/agent-rules.md`. 각 규칙은 `category`, `check`, 한 줄 설명을 가집니다.
2. `check`마다 메서드 하나를 노출하는 `RuleChecker` 클래스가 있는 `tools/rule_checker.py`. 각 메서드는 `TurnTrace` 데이터클래스를 받아 `bool`을 반환합니다.
3. 규칙을 읽어 들이고, 트레이스 위에서 검사기를 돌리고, `rule_report.json`을 내놓는 `tools/rule_report.py` 러너.
4. 마이그레이션 노트 파일: 어떤 산문 줄이 어떤 규칙이 되었는지, 무엇이 포부적이라고 버려졌는지, 그 이유.

하드 리젝(무조건 거절):

- `check` 필드 없는 규칙. 포부만 있는 규칙은 워크벤치 규칙 집합이 아니라 온보딩 문서에 속합니다.
- 하나뿐인 "조심하세요" 규칙. 카테고리와 검사를 명시하거나 제거하세요.
- LLM 호출이 필요한 검사. 규칙 검사는 매 턴 돌릴 수 있어야 하므로 결정론적이고 값싸야 합니다.
- 200줄을 넘는 규칙 파일. 카테고리별로 `agent-rules.{startup,forbidden,done,uncertainty,approval}.md`로 쪼개고 부모 인덱스에서 안내합니다.

거절 규칙:

- 에이전트 제품이 `TurnTrace`를 제공할 수 없다면(계측 없음), 최소한 `read_state_file`, `edited_files`, `tests_exit_code`가 기록될 때까지 검사기 연결을 거절합니다.
- 기존 지시가 대부분 포부적이라면(50% 초과), 규칙을 내놓기 전에 그 사실을 드러냅니다. 규칙 집합이 빈약해 보일 것입니다. 그것이 올바른 결과입니다.
- 과거 사건 하나 때문에 추가된 규칙에는 사건 id를 붙여, 미래 리뷰에서 여전히 필요한지 판단할 수 있게 합니다.

출력 구조:

```
<repo>/
├── docs/
│   └── agent-rules.md
├── tools/
│   ├── rule_checker.py
│   └── rule_report.py
└── docs/migration-notes.md
```

마지막에 "다음에 읽을 것"으로 다음을 가리킵니다.

- forbidden 카테고리를 확장하는 과제별 범위 계약은 레슨 36.
- 규칙 보고서를 소비하는 검증 게이트는 레슨 38.
- 규칙 준수를 채점하는 리뷰어 에이전트는 레슨 39.
