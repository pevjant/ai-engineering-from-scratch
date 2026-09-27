---
name: workbench-pack
description: 프로젝트에 맞춰진 드롭인 에이전트 워크벤치 팩을 생성합니다. 팀의 이력에 맞게 갈아 세운 규칙, 저장소에 맞춘 범위 글롭, 도메인 고유 항목 하나로 확장된 루브릭 차원이 담깁니다.
version: 1.0.0
phase: 14
lesson: 42
tags: [capstone, workbench-pack, installer, schemas, drop-in]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-workbench-pack.md](skill-workbench-pack.md)


저장소, 팀의 장애(incident) 이력, 그 안에서 돌아가는 에이전트 제품이 주어지면, 맞춤화된 agent-workbench-pack과 설치기를 내놓습니다.

만들 것:

1. 정준 구성을 따르는 `agent-workbench-pack/` 디렉터리: AGENTS.md, docs/, schemas/, scripts/, bin/, README.md, VERSION.
2. `--force` 없이 기존 팩을 덮어쓰는 것을 거부하고, 대상 저장소에 `.workbench-version`을 기록하는 `bin/install.sh`.
3. 프로젝트 맞춤 버전의 `agent-rules.md`(팀의 최근 6개 장애에서 파생한 규칙을 카테고리별로 최소 하나씩), `reviewer-rubric.md`(여섯 번째 도메인 차원 추가), `scope_contract.schema.json`(프로젝트 고유 글롭).
4. 스크립트와 스키마 사이의 어긋남, 또는 VERSION과 스키마의 `schema_version` 사이의 어긋남에서 실패하는 `lint_pack.py` 스크립트.
5. 선택적 CI 통합 — 데모 브랜치에 팩을 설치하고 검증 게이트를 알려진 정상 태스크에 대해 돌립니다.

하드 거부(hard reject) 항목:

- 프로젝트 고유 태스크를 담은 팩. 태스크는 대상 저장소의 보드에 삽니다.
- 단일 벤더 SDK에 묶인 팩. 프레임워크 불가지론만 허용됩니다. SDK 연결은 대상 저장소의 몫입니다.
- 상태 파일을 변경하는 설치기. 설치기는 멱등하고 표면만 다룹니다. 상태는 에이전트와 사람의 것입니다.
- 대응하는 검사 함수가 없는 규칙. 막연한 이상 규칙은 온보딩에 있어야지 팩에 있으면 안 됩니다.

거부 규칙:

- 장애 이력이 비어 있다면, 맞춤화된 `agent-rules.md` 출시를 거부합니다. 정준 기본값을 쓰고 그 공백을 드러내세요.
- 대상 저장소의 CI가 설치와 호환되지 않는다면(`.github/workflows/`도, 이에 준하는 것도 없음), 선택적 CI 단계를 거부하고 수동 경로를 문서화하세요.
- 팀이 팩의 비공개 포크를 쓴다면, 공개 설치기 작성을 거부합니다. 비공개 설치기에는 비공개 불변 조건이 실려 있습니다.

출력 구조:

```
agent-workbench-pack/
├── AGENTS.md
├── docs/
├── schemas/
├── scripts/
├── bin/install.sh
├── lint_pack.py
├── VERSION
└── README.md
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 이 팩이 개선하는 전/후 벤치마크는 레슨 41.
- 팩의 판정을 소비하는 평가 루프는 레슨 30 (평가 주도 에이전트 개발).
- 팩을 32개 AI 에이전트에 배포하려면 [SkillKit](https://github.com/rohitg00/skillkit).
