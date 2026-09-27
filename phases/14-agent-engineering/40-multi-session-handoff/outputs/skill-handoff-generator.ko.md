---
name: handoff-generator
description: 워크벤치 산출물에서 세션 종료 핸드오프 패킷을 생성하되, 사람이 읽는 Markdown과 기계가 읽는 JSON을 일곱 개의 정준 필드에 맞춰 함께 만들어 냅니다.
version: 1.0.0
phase: 14
lesson: 40
tags: [handoff, generator, session-end, packet, next-action]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-handoff-generator.md](skill-handoff-generator.md)


워크벤치(상태, 판정, 리뷰, 피드백 로그, diff)가 주어지면, 에이전트 런타임에 연결된 세션 종료 핸드오프 생성기를 만들어 냅니다.

만들 것:

1. `tools/generate_handoff.py` — `generate_handoff(snapshot) -> (markdown, payload)`를 제공합니다.
2. `outputs/handoff/<session_id>/handoff.md`와 `handoff.json`.
3. `handoff.schema.json` — 일곱 필수 필드와 피드백 꼬리(tail) 형식을 다룹니다.
4. 세션 종료 훅 스크립트 — 생성기를 실행하고, 필드가 하나라도 빠지면 세션 닫기를 거부합니다.
5. `docs/handoff.md` — 일곱 필드, 그 출처, 잘라내기 정책을 나열합니다.

하드 거부(hard reject) 항목:

- `next_action`이 없는 핸드오프. 핸드오프인 척하는 상태 보고서는 다음 세션을 오염시킵니다.
- 요약을 손으로 직접 쓰는 생성기. 에이전트의 일은 워크벤치를 "생성 가능한 상태"로 남겨 두는 것입니다.
- JSON과 어긋나는 마크다운 패킷. JSON이 원본이고, 마크다운은 JSON의 렌더링입니다.
- 30개 항목을 넘는 피드백 꼬리. 전체 로그는 버전 관리 안에 있으니, 패킷은 작게 유지해야 합니다.

거부 규칙:

- 검증 리포트가 없다면, 패킷 생성을 거부합니다. 판정 없는 핸드오프는 그저 소원입니다.
- 리뷰 리포트가 없는데 사람 리뷰어가 예상됐다면, 거부하고 리뷰 통과를 먼저 요구합니다.
- diff 요약이 비어 있는데 세션이 5분보다 길게 돌았다면, 생성 전에 그 이상을 드러냅니다. 실제 no-op이기보다 뻗은(wedged) 세션을 의심하세요.

출력 구조:

```
<repo>/
├── outputs/handoff/<session_id>/
│   ├── handoff.md
│   └── handoff.json
├── tools/generate_handoff.py
├── handoff.schema.json
└── docs/handoff.md
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 실전형 샘플 앱으로 끝까지 시험하기는 레슨 41.
- 생성기를 캡스톤 워크벤치 팩으로 묶기는 레슨 42.
- 큐, 이벤트, 크론 트리거에 세션 종료를 연결하는 것은 레슨 29 (프로덕션 런타임).
