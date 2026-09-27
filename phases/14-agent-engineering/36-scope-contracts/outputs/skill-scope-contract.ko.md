---
name: scope-contract
description: 허용/금지 글롭, 수용 기준, 롤백 계획이 담긴 태스크별 범위 계약과, 모든 에이전트 diff에 대해 돌릴 수 있는 CI 준비된 글롭 인식 검사기를 생성합니다.
version: 1.0.0
phase: 14
lesson: 36
tags: [scope, contract, globs, diff-check, ci]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-scope-contract.md](skill-scope-contract.md)


태스크 설명과 저장소 구조가 주어지면, 범위 계약과 diff 인식 검사기를 만들어 냅니다.

만들 것:

1. 태스크를 위한 `scope_contract.json` — 필드: `task_id`, `goal`, `allowed_files`(글롭), `forbidden_files`(글롭), `acceptance_criteria`, `rollback_plan`, `approvals_required`.
2. `tools/scope_check.py` — 계약 경로와 건드린 파일 목록을 받아 `ScopeReport`를 반환하고, 위반이 있으면 0이 아닌 종료 코드로 끝납니다.
3. CI 단계(`.github/workflows/scope-check.yml` 또는 이에 준하는 것) — 병합 diff에 대해 검사기를 실행합니다.
4. `outputs/scope/closed/<task_id>.json` 보관 관례 — 계약이 변경 이력과 함께 출시되게 합니다.

하드 거부(hard reject) 항목:

- `forbidden_files`가 없는 계약. 부정 공간(금지 목록)도 계약의 일부입니다.
- 코드 디렉터리를 글롭이 아니라 날경로(raw path)로 적은 계약. 리팩토링이면 하룻밤에 날경로는 무효가 됩니다.
- 비어 있거나 "런북 참조"뿐인 `rollback_plan` 필드. 직접 써 넣어야 합니다.
- "케이스 바이 케이스"로 적힌 승인. 승인 경계는 열거 가능해야 합니다.

거부 규칙:

- 태스크 설명이 저장소의 어떤 영역도 제한하지 않는다면, 설명만으로 `allowed_files`를 작성하는 것을 거부합니다. 태스크가 속한 디렉터리를 물어보세요.
- 저장소에 테스트 명령이 없다면, 하나가 제공되거나 스텁으로라도 만들어지기 전까지 `acceptance_criteria` 추가를 거부합니다. 검증할 수 없는 계약은 그저 소원입니다.
- 에이전트 런타임이 승인 경계를 지킬 수 없다면(사람 개입(human-in-the-loop) 불가), 출시 전에 그 공백을 드러냅니다. 승인이 필요한 행동으로의 범위 확산이 가장 큰 실패가 될 것입니다.

출력 구조:

```
<repo>/
├── scope_contract.json
├── outputs/scope/closed/
│   └── T-XXX.json
├── tools/
│   └── scope_check.py
└── .github/
    └── workflows/
        └── scope-check.yml
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 실행된 명령을 계약으로 되돌려 연결하는 런타임 피드백은 레슨 37.
- 범위 리포트를 소비하는 검증 게이트는 레슨 38.
- 닫힌 계약 보관소를 감사하는 리뷰어 에이전트는 레슨 39.
