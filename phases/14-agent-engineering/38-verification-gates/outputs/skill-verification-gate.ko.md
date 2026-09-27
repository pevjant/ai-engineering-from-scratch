---
name: verification-gate
description: 범위·규칙·피드백 산출물을 결합해 태스크마다 하나의 verification_report.json을 만드는 결정론적 검증 게이트와, 초록 판정 없이는 병합을 거부하는 CI 연결을 생성합니다.
version: 1.0.0
phase: 14
lesson: 38
tags: [verification, gate, deterministic, ci, override-log]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-verification-gate.md](skill-verification-gate.md)


프로젝트의 수용 기준과 기존 워크벤치 산출물이 주어지면, 검증 게이트와 재정의 감사 로그를 만들어 냅니다.

만들 것:

1. `tools/verify_agent.py` — `verify(task_id, artifacts) -> VerdictReport`를 제공. 순수 함수, 결정론적, LLM 호출 없음.
2. `outputs/verification/<task_id>.json` — 단일 진실 공급원 판정.
3. `tools/override.py` — 서명된 재정의 항목을 `outputs/verification/overrides.jsonl`에 덧붙임 (사유, 사용자 ID, 타임스탬프, 발견 항목 코드 필수).
4. `passed: false`에서 실패하고 리포트를 인라인으로 드러내는 CI 워크플로.
5. `docs/verification.md` — 모든 검사, 심각도, 원본 산출물, 재정의 정책을 나열합니다.

하드 거부(hard reject) 항목:

- LLM을 호출하는 검사. 게이트는 결정론적 배관입니다. LLM 판단은 리뷰어의 몫입니다.
- 에이전트가 서명된 항목 없이 통과할 수 있는 재정의 경로. 재정의는 사람 전용입니다.
- 소비한 산출물 경로를 빠뜨린 검증 리포트. 리포트는 감사 가능해야 합니다.
- 워크플로가 조용히 낮출 수 있는 차단 심각도 발견 항목. 심각도는 쓰는 시점에 고정되지, 읽는 시점에 정해지는 게 아닙니다.

거부 규칙:

- 프로젝트에 수용 명령이 없다면, 하나가 생길 때까지 게이트 출시를 거부합니다. 아무것도 증명하지 않는 게이트는 쇼에 불과합니다.
- 규칙 리포트가 존재하지 않는다면, 규칙 검사를 건너뛰는 것을 거부합니다. 안전 쪽으로 실패(fail closed)합니다.
- 피드백 로그가 존재하지 않는다면, 수용 검사를 건너뛰는 것을 거부합니다. 로그가 없다는 것 자체가 차단 사항입니다.
- 재정의 항목이 버전 관리되지 않는다면, 재정의 경로 연결을 거부합니다. 기록 밖의 재정의는 게이트를 무력화합니다.

출력 구조:

```
<repo>/
├── tools/
│   ├── verify_agent.py
│   └── override.py
├── outputs/verification/
│   ├── overrides.jsonl
│   └── <task_id>.json
├── docs/verification.md
└── .github/workflows/verify.yml
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 초록 판정 뒤를 이어받는 리뷰어 에이전트는 레슨 39.
- 판정을 패킷에 담는 핸드오프 생성기는 레슨 40.
- 실제에 가까운 샘플 앱에 게이트를 돌려 보는 것은 레슨 41.
