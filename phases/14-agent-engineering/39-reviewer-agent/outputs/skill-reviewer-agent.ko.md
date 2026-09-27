---
name: reviewer-agent
description: 빌더 산출물을 읽고 구조화된 리뷰 리포트를 만들어, 사람의 리뷰가 백지가 아니라 쓰인 페이지에서 시작되게 하는 5차원 루브릭의 리뷰어 에이전트 역할을 세웁니다.
version: 1.0.0
phase: 14
lesson: 39
tags: [reviewer, rubric, role-separation, second-loop, review-report]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-reviewer-agent.md](skill-reviewer-agent.md)


이미 워크벤치 산출물을 만들어 내고 있는 빌더 에이전트가 주어지면, 그것들을 읽고 구조화된 리포트를 쓰는 리뷰어를 세웁니다.

만들 것:

1. `agents/reviewer.md` — 리뷰어 시스템 프롬프트: 읽기 전용 접근, 5차원 루브릭, 점수마다 산출물 경로를 인용해야 함.
2. `tools/reviewer.py` — 워크벤치에서 `ReviewerInputs`를 읽어 차원별로 LLM 채점기를 돌립니다.
3. `outputs/review/<task_id>.json` — 정준(canonical) 리뷰 리포트 경로.
4. `docs/reviewer-rubric.md` — 다섯 차원, 각 차원이 답하는 질문, 0-1-2 앵커 설명을 나열합니다.
5. 빌더 태스크가 닫힐 때마다 리뷰 리포트를 PR 코멘트로 게시하는 CI 단계.

하드 거부(hard reject) 항목:

- diff에 쓰기 권한이 있는 리뷰어. 빌더와 리뷰어 사이의 간극이 곧 신호 전부입니다. 그걸 무너뜨리면 신뢰성도 무너집니다.
- 점수별 앵커 설명이 없는 루브릭. 앵커 없는 "0에서 2점으로 채점하라"는 분위기(vibes)로 퇴화합니다.
- 인용을 빠뜨린 리뷰 리포트. 모든 점수는 파일이나 추적(trace) 항목을 가리켜야 합니다.
- 빌더의 시스템 프롬프트를 공유하는 것. 같은 모델은 괜찮지만, 같은 프롬프트는 안 됩니다.

거부 규칙:

- 빌더가 검증 리포트를 만들지 않았다면, 리뷰어 실행을 거부합니다. 판단을 구할 가치가 있으려면 수용 검증이 먼저 성립해야 합니다.
- 프로젝트에 닫힌 태스크가 3개 미만이라면, 루브릭이 보정됐다고 주장하는 것을 거부합니다. 첫 리포트들을 보정 집합으로 저장하세요.
- 리뷰어에게 최소 신뢰도 미만의 채점이 요구된다면, 거부하고 불확실한 차원을 사람에게 드러냅니다.

출력 구조:

```
<repo>/
├── agents/reviewer.md
├── tools/reviewer.py
├── outputs/review/
│   └── <task_id>.json
├── docs/reviewer-rubric.md
└── .github/workflows/review.yml
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 검증 + 리뷰를 결합하는 핸드오프 패킷은 레슨 40.
- 빌더/리뷰어 분리를 끝까지 시험하는 실전형 태스크는 레슨 41.
- 이 레슨이 개선하는 단일 에이전트 자기 리뷰 베이스라인은 레슨 05 (Self-Refine과 CRITIC).
