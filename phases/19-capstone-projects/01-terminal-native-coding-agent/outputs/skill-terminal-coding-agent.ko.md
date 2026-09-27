---
name: terminal-coding-agent
description: 비용 상한과 샌드박스 처리된 도구, 전체 2026 훅 표면을 갖춘 터미널 네이티브 코딩 에이전트를 SWE-bench Pro 대상으로 만들고 평가합니다.
version: 1.0.0
phase: 19
lesson: 01
tags: [capstone, coding-agent, claude-code, swe-bench, mcp, hooks, sandbox]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-terminal-coding-agent.md](skill-terminal-coding-agent.md)

대상 저장소와 자연어 작업이 주어지면, 플랜을 세우고 샌드박스 안에서 실행하고 풀 리퀘스트를 여는 하니스를 만듭니다. 작업당 $5 예산 안에서 30작업 SWE-bench Pro 부분집합에서 mini-swe-agent 베이스라인과 맞먹거나 앞서게 만듭니다.

만들기 계획:

1. 플랜 창, 도구 호출 스트림, 실시간 토큰/달러 예산을 갖춘 Bun + Ink TUI 하니스를 세웁니다.
2. 여섯 도구(read_file, edit_file, ripgrep, tree_sitter_symbols, run_shell, git)를 Model Context Protocol StreamableHTTP 위에 정의합니다. 모든 호출은 최대 4k 토큰을 돌려줍니다.
3. 모든 도구 호출은 새 `git worktree add` 브랜치를 만든 E2B 또는 Daytona 샌드박스 안에서 실행합니다. 호스트 파일시스템은 절대 건드리지 않습니다.
4. 2026년의 여덟 훅 이벤트를 전부 연결합니다: SessionStart, SessionEnd, PreToolUse, PostToolUse, UserPromptSubmit, Notification, Stop, PreCompact. 사용자 작성 훅을 최소 넷 출시합니다(파괴적 명령 가드, 토큰 회계, OTel 스팬 발사기, 트레이스 번들 작성기).
5. 세 가지 예산을 강제합니다: 50턴, 200k 토큰, $5. PreCompact는 150k에서 발사되어 이전 턴들을 요약합니다.
6. GenAI 시맨틱 컨벤션을 적용한 OpenTelemetry 스팬을 셀프 호스팅 Langfuse로 보냅니다.
7. 성공 시 브랜치를 푸시하고, 본문에 플랜과 트레이스 번들을 넣어 PR을 엽니다.
8. 30이슈 SWE-bench Pro Python 부분집합에서 mini-swe-agent와 평가하고, 작업별 pass@1, 턴 수, 토큰, 달러를 기록합니다.

채점 기준:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 | 같은 30작업 부분집합에서 mini-swe-agent 베이스라인과 비교 |
| 20 | 아키텍처 명확성 | 플랜/행동/관찰 분리, 훅 표면, 도구 스키마 가독성 |
| 20 | 안전 | 샌드박스 탈출 레드팀 + 파괴적 명령 가드 감사 |
| 20 | 관측 가능성 | 도구 호출 100% 스팬, 턴별 토큰 회계 |
| 15 | 개발자 UX | 콜드 스타트 2초 미만, 충돌 복구, Ctrl-C 취소 의미론 |

하드 리젝트(무조건 반려):

- 샌드박스 안이 아니라 호스트 파일시스템에서 git을 셸 아웃하는 하니스.
- 명시적 허용 목록 훅 없이 워크트리 밖에 쓰거나 외부 URL을 curl할 수 있는 에이전트.
- 같은 30이슈에서 베이스라인을 같이 돌리지 않고 보고하는 평가 수치.
- 재시도 사이에 `git reset --hard`에 기대는 "통과율" 주장. SWE-bench Pro는 pass@1입니다.

거절 규칙:

- 어떤 설정으로도 main에 직접 푸시하는 것을 거절하세요. PR 브랜치만 허용합니다.
- 파괴적 명령 가드를 끄는 것을 거절하세요. 채점 기준의 하드 요구사항입니다.
- 예산 상한 없이 실행하는 것을 거절하세요. 무한정 실행은 평가 비교를 오염시킵니다.

출력: 하니스가 담긴 저장소, mini-swe-agent 베이스라인을 같이 돌린 고정 30작업 SWE-bench Pro 평가 하니스, 최소 5회 전체 실행의 OpenTelemetry 트레이스 아카이브, 그리고 베이스라인이 못 푸는 작업 중 내 하니스가 푸는 것과 그 반대를 이름으로 적은 보고서. 마지막에 관찰된 상위 세 실패 모드와 각각을 고친 훅 변경을 다루는 섹션으로 끝냅니다.
