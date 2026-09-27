---
name: multi-agent-team
description: 아키텍트, 병렬 코더, 리뷰어, 테스터로 이루어진 멀티 에이전트 소프트웨어 팀을 만들어 SWE-bench Pro로 측정하고 핸드오프 사후 분석을 산출합니다.
version: 1.0.0
phase: 19
lesson: 10
tags: [capstone, multi-agent, swe-bench, langgraph, a2a, worktree, roles]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-multi-agent-team.md](skill-multi-agent-team.md)

GitHub 이슈 URL과 병렬 수준이 주어지면, 병합 준비가 된 PR을 만들어 내는 멀티 에이전트 소프트웨어 팀을 배포합니다. 50개 SWE-bench Pro 이슈로 평가하고 핸드오프 실패 히스토그램을 공개합니다.

만들기 계획:

1. 작업 보드: 타입화된 메시지의 파일 기반(또는 Redis) JSONL 저장소. 메시지 종류: plan_request, subtask, diff_ready, review_needed, review_feedback, approved, test_needed, test_passed, test_failed, replan_needed.
2. 아키텍트(Opus 4.7): 이슈를 읽고 계획을 쓰고, 명시적인 인터페이스(건드리는 파일, 공개 함수, 테스트 영향)를 갖춘 하위 작업 DAG를 내보냅니다.
3. 코더 N명(Sonnet 4.7): 각자 하위 작업을 가져가고 새로운 `git worktree add` + Daytona 샌드박스를 만들어 독립적으로 구현합니다.
4. 병합 코디네이터: 3-way 병합; 파일 수준 겹침이 있을 때만 LLM 중재 충돌 해소.
5. 리뷰어(GPT-5.4): 병합된 diff를 읽습니다; 자신이 작성한 diff는 승인할 수 없습니다; approved 또는 관련 코더에게 전달되는 review_feedback을 내보냅니다.
6. 테스터(Gemini 2.5 Pro): 깨끗한 샌드박스에서 테스트 스위트를 돌리고 산출물과 함께 test_passed 또는 test_failed를 내보냅니다.
7. 핸드오프 회계: 역할을 넘나드는 모든 메시지는 페이로드 크기와 모델을 담은 Langfuse 스팬이 됩니다. 토큰 증폭률 = total_tokens / single_agent_baseline_tokens를 계산합니다.
8. 눈에 띄는 버그 주입 프로브(실행의 10%)를 넣어 리뷰어의 잘못된 승인 비율을 측정합니다.
9. 50개 SWE-bench Pro 이슈에서 실행; pass@1, 단일 에이전트 베이스라인 대비 벽시계 시간, 역할별 토큰 분해, 핸드오프 실패 히스토그램을 공개합니다.

평가 루브릭:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 | 50이슈 서브셋 pass@1 |
| 20 | 병렬 가속 | 단일 에이전트 베이스라인 대비 벽시계 시간 |
| 20 | 리뷰 품질 | 주입된 버그 프로브에서의 잘못된 승인 비율 |
| 20 | 토큰 효율 | 단일 에이전트 대비 해결 이슈당 총 토큰 |
| 15 | 조율 엔지니어링 | 병합 충돌 해소, 핸드오프 실패 히스토그램 |

즉각 탈락(Hard rejects):

- 자신이 작성하거나 제안한 diff를 승인할 수 있는 리뷰어. 하드 제약입니다.
- 짝을 맞춘 단일 에이전트 베이스라인 실행이 없는 보고서. 멀티 에이전트는 단순히 pass@1이 아니라 *달러당* 이겨야 합니다.
- 메시지가 타입화된 A2A 메시지가 아니라 자유 형식 문자열인 작업 보드.
- 재계획을 위해 되돌려 보내는 대신 충돌하는 diff를 조용히 버리는 병합 코디네이터.

거절 규칙(Refusal rules):

- 역할별 예산 상한(토큰 + 달러)이 없으면 실행을 거절합니다.
- 깨끗한 샌드박스에서 테스터가 검증하지 않은 PR을 여는 일을 거절합니다.
- 단일 실행에서 코더를 8명 넘게 늘리는 일을 거절합니다. 그 이상은 조율 오버헤드가 지배합니다.

산출물: 작업 보드 + 역할 워커, 50이슈 SWE-bench Pro 실행 로그, 짝을 맞춘 단일 에이전트 베이스라인 실행, 역할 태그 스팬과 역할별 토큰 분해를 보여주는 Langfuse 대시보드, 주입 버그 프로브 보고서, 그리고 가장 자주 깨진 세 가지 핸드오프와 각각을 줄인 메시지 스키마·프롬프트 변경점을 적은 사후 분석 보고서를 담은 저장소.
