---
name: feedback-runner
description: 셸 명령을 감싸 stdout/stderr/종료/소요 시간을 결정론적으로 포착하고, 명령마다 JSONL 기록을 저장하며, 피드백이 없으면 에이전트 루프의 진행을 거부합니다.
version: 1.0.0
phase: 14
lesson: 37
tags: [feedback, subprocess, runner, jsonl, loop-control]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-feedback-runner.md](skill-feedback-runner.md)


에이전트 루프 안에서 셸 명령을 실행하는 프로젝트가 주어지면, 피드백 러너와 그것이 쓰는 JSONL을 만들어 냅니다.

만들 것:

1. `tools/run_with_feedback.py` — `run_with_feedback(command: list[str], agent_note: str, timeout_s: float) -> FeedbackRecord`를 제공합니다.
2. 워크벤치 아래의 `feedback_record.jsonl` 위치. 한 줄에 기록 하나.
3. `tools/feedback_loader.py` — 활성 태스크의 최근 N개 기록을 반환합니다.
4. 에이전트 루프가 성공을 주장하기 전에 호출하는 `loop_can_advance(record) -> bool` 헬퍼.
5. 테스트 — 다음을 다룹니다: 성공 경로, 0이 아닌 종료, 타임아웃, 없는 바이너리, 결정론적 머리/꼬리 잘라내기.

하드 거부(hard reject) 항목:

- 러너 안 어디든 `shell=True`를 쓰는 것. argv만 사용합니다.
- 실제 시간이나 무작위 샘플링에 의존하는 잘라내기. 같은 입력은 같은 기록을 만들어야 합니다.
- `duration_ms`가 없는 기록. 느린 점검은 워크벤치가 뻗었다(wedged)는 첫 신호입니다.
- 제한 없는 리스트를 반환하는 로더. 마지막 N개로 제한하거나 페이지로 나눕니다.

거부 규칙:

- 프로젝트가 stdout으로 비밀 값을 흘려보낸다면, 마스킹(redaction) 단계 없이는 러너 출시를 거부합니다. 포착됐을 줄들을 먼저 드러내세요.
- 무기한 멈출 수 있는 명령이 있다면, 기본 타임아웃과 명시적인 예외 목록 없이는 출시를 거부합니다.
- 러너가 상태를 공유하는 워커 안에서 돈다면, JSONL 덧붙이기 주변에 파일 잠금을 생략하는 것을 거부합니다. 여러 쓰기가 파일을 찢어 버립니다.

출력 구조:

```
<repo>/
├── feedback_record.jsonl
└── tools/
    ├── run_with_feedback.py
    ├── feedback_loader.py
    └── test_feedback_runner.py
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 기록을 소비하는 검증 게이트는 레슨 38.
- 실행을 채점할 때 피드백을 읽는 리뷰어 에이전트는 레슨 39.
- 피드백이 안정된 뒤 텔레메트리 쪽에 추가할 OTel GenAI 관례는 레슨 23.
