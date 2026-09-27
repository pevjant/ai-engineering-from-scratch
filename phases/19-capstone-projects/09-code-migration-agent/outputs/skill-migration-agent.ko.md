---
name: migration-agent
description: 결정론적 레시피에 에이전트 폴백 루프를 결합한 저장소 단위 코드 마이그레이션 에이전트를 만들어 MigrationBench를 통과하고 실패 분류표를 공개합니다.
version: 1.0.0
phase: 19
lesson: 09
tags: [capstone, code-migration, openrewrite, libcst, migrationbench, agent, sandbox]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-migration-agent.md](skill-migration-agent.md)

Java 8 또는 Python 2 저장소가 주어지면, 테스트 스위트가 녹색이고 커버리지 퇴보가 최소화된 마이그레이션 브랜치(Java 17 또는 Python 3.12로)를 만들어 냅니다. 50저장소 MigrationBench 서브셋 전체에서 평가합니다.

만들기 계획:

1. 결정론적 패스: OpenRewrite(Java) 또는 libcst(Python)가 기계적인 재작성을 먼저 실행합니다. 깔끔한 diff로 "recipe" 커밋으로 커밋합니다.
2. Daytona 샌드박스: 대상 런타임 미리 설치, 브랜치별 빌드, 읽기 전용 소스 마운트.
3. 에이전트 루프: Claude Opus 4.7 + GPT-5.4-Codex 위에서 LangGraph 또는 OpenAI Agents SDK. 도구: `run_build`, `read_file`, `edit_file`, `run_test`, `git_diff`. 실패를 분류하고(의존성, 문법, 테스트, 빌드 도구) 표적화된 수정을 적용한 뒤 재실행합니다.
4. 예산 상한: 30분, 8달러, 20턴. 하나라도 넘기면 중단하고 현재 diff와 함께 `budget_exhausted`로 분류합니다.
5. 테스트 + 커버리지 게이트: 빌드가 녹색이고 그다음 테스트가 녹색이어야 하며, 커버리지는 2% 이상 떨어지면 안 됩니다.
6. 레시피 커밋 + 에이전트 커밋 + 요약 코멘트를 담아 PR을 엽니다.
7. 실패 분류표: 저장소마다 `{dep_upgrade_required, build_tool_drift, custom_annotation, test_flake, syntax_edge_case, budget_exhausted, coverage_regression}`에서 태그를 붙입니다.
8. MigrationBench 전체에서 50저장소 실행; 클래스별 통과율, 저장소당 비용, 커버리지 보존율을 공개하고 결정론적 도구만 쓴 베이스라인과 비교합니다.

평가 루브릭:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | MigrationBench 통과율 | 50저장소 서브셋 pass@1 |
| 20 | 테스트 커버리지 보존 | 베이스 브랜치 대비 평균 커버리지 변화량 |
| 20 | 마이그레이션 저장소당 비용 | 통과한 실행 기준 평균 저장소당 달러($/repo) |
| 20 | 에이전트 / 결정론적 도구 통합 | OpenRewrite가 처리한 수정 대비 에이전트가 처리한 수정의 비율 |
| 15 | 실패 분석 보고서 | 대표 사례를 갖춘 분류표의 완성도 |

즉각 탈락(Hard rejects):

- 결정론적 패스를 건너뛰는 파이프라인. OpenRewrite는 기계적인 70~80%를 어떤 에이전트보다도 싸고 안정적으로 처리합니다.
- 2%를 넘는 커버리지 퇴보를 통과로 처리하는 경우.
- 기계적 변경과 에이전트 작성 변경을 한 커밋에 뭉뚱그린 PR. 반드시 분리해야 합니다.
- 같은 50개 저장소에서 짝을 이루는 결정론적 전용 베이스라인 없이 통과율만 보고하는 경우.

거절 규칙(Refusal rules):

- 마이그레이션 브랜치를 베이스 위에 강제 푸시(force-push)하는 일을 거절합니다. 항상 새 브랜치 + PR로 합니다.
- 샌드박스에서 CI가 녹색으로 바뀌지 않은 PR을 여는 일을 거절합니다.
- 수정 허가가 명시적으로 없는 기업 저장소에서 실행하는 일을 거절합니다.

산출물: 두 레이어 마이그레이션 파이프라인, 50저장소 MigrationBench 실행 로그, 실패 분류표 대시보드, 짝을 이루는 결정론적 전용 베이스라인 실행, 그리고 가장 흔한 세 가지 실패 클래스와 각각을 없앨 수 있는 레시피 변경점을 적은 보고서를 담은 저장소.
