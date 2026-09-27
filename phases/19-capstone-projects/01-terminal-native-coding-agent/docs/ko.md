> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 01 — 터미널 네이티브 코딩 에이전트

> 2026년에 코딩 에이전트의 모습은 정형화되어 있습니다. TUI 하니스, 상태를 가진 플랜, 샌드박스 처리된 도구 표면, 그리고 플랜을 세우고 행동하고 관찰하고 복구하는 루프. Claude Code, Cursor 3, OpenCode는 50미터 밖에서 보면 전부 똑같아 보입니다. 이 캡스톤은 그런 에이전트를 끝까지 직접 만들어 보게 합니다 — CLI로 받아서 풀 리퀘스트로 돌려주는 것까지 — 그리고 SWE-bench Pro에서 mini-swe-agent와 Live-SWE-agent와 비교 측정하게 합니다. 어려운 부분은 모델 호출이 아니라 도구 루프, 샌드박스, 그리고 50턴 실행의 비용 상한이라는 사실을 몸으로 배우게 될 겁니다.

**유형:** Capstone
**언어:** TypeScript / Bun (하니스), Python (평가 스크립트)
**선수 지식:** 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구와 프로토콜), 페이즈 14 (에이전트), 페이즈 15 (자율 시스템), 페이즈 17 (인프라)
**활용하는 페이즈:** P0 · P5 · P7 · P10 · P11 · P13 · P14 · P15 · P17 · P18
**시간:** 35시간

## 문제

코딩 에이전트는 2026년 AI 애플리케이션의 지배적 카테고리가 되었습니다. Claude Code(Anthropic), Composer 2와 Agent Tabs를 갖춘 Cursor 3(Cursor), Amp(Sourcegraph), OpenCode(별 112k), Factory Droids, Google Jules가 전부 같은 아키텍처의 변형을 출시합니다: 터미널 하니스, 권한이 있는 도구 표면, 샌드박스, 그리고 프론티어 모델을 중심에 둔 플랜-행동-관찰 루프. 프론티어는 좁습니다 — Live-SWE-agent가 Opus 4.5로 SWE-bench Verified에서 79.2%에 도달했습니다 — 하지만 엔지니어링 기술의 폭은 넓습니다. 실패 모드 대부분은 모델의 실수가 아닙니다. 도구 루프의 불안정, 컨텍스트 오염, 걷잡을 토큰 비용, 파일시스템 파괴 작업입니다.

이런 에이전트는 바깥에서 관찰만 해서는 이해할 수 없습니다. 직접 하나 만들고, 47턴째에 ripgrep이 8MB짜리 매칭을 돌려줘서 루프가 터지는 걸 보고, 잘라내기(truncation) 계층을 다시 만들어 봐야 합니다. 그게 이 캡스톤의 목적입니다.

## 개념

하니스에는 네 개의 표면이 있습니다. **플랜(Plan)**은 모델이 매턴 다시 쓰는 TodoWrite 방식의 상태 객체를 유지합니다. **행동(Act)**은 도구 호출(read, edit, run, search, git)을 보냅니다. **관찰(Observe)**은 stdout / stderr / 종료 코드를 받아 잘라내고, 요약을 다시 모델에게 먹입니다. **복구(Recover)**는 컨텍스트 윈도우를 불리거나 무한 루프에 빠지지 않고 도구 오류를 처리합니다. 2026년 형태는 한 가지를 더 얹습니다: **훅(hooks)**입니다. `PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `Notification`, `Stop`, `PreCompact` — 운영자가 정책, 텔레메트리, 가드레일을 주입하는 설정 가능한 확장 지점입니다.

샌드박스는 E2B 또는 Daytona입니다. 각 작업은 읽기-쓰기로 마운트된 git 워크트리가 얹힌 새 devcontainer에서 돌아갑니다. 하니스는 절대 호스트 파일시스템을 만지지 않습니다. 워크트리는 성공하든 실패하든 철거됩니다. 비용 통제는 세 계층으로 강제됩니다: 턴당 토큰 상한, 세션당 달러 예산, 그리고 하드 턴 제한(보통 50). 관측 가능성 계층은 GenAI 시맨틱 컨벤션을 적용한 OpenTelemetry 스팬이며, 셀프 호스팅한 Langfuse로 보냅니다.

## 아키텍처

```
  user CLI  ->  harness (Bun + Ink TUI)
                  |
                  v
           plan / act / observe loop  <--->  Claude Sonnet 4.7 / GPT-5.4-Codex / Gemini 3 Pro
                  |                          (via OpenRouter, model-agnostic)
                  v
           tool dispatcher (MCP StreamableHTTP client)
                  |
     +------------+------------+----------+
     v            v            v          v
  read/edit    ripgrep     tree-sitter   git/run
     |            |            |          |
     +------------+------------+----------+
                  |
                  v
           E2B / Daytona sandbox  (worktree isolated)
                  |
                  v
           hooks: Pre/Post, Session, Prompt, Compact
                  |
                  v
           OpenTelemetry -> Langfuse (spans, tokens, $)
                  |
                  v
           PR via GitHub app
```

## 스택

- 하니스 런타임: Bun 1.2 + Ink 5 (터미널 안의 React)
- 모델 접근: OpenRouter 통합 API — Claude Sonnet 4.7, GPT-5.4-Codex, Gemini 3 Pro, Opus 4.5 (가장 어려운 작업용)
- 도구 전송: Model Context Protocol StreamableHTTP (MCP 2026 개정판)
- 샌드박스: E2B 샌드박스(JS SDK) 또는 Daytona devcontainer
- 코드 검색: ripgrep 서브프로세스, 17개 언어용 tree-sitter 파서(사전 컴파일)
- 격리: 작업별 `git worktree add`, 성공/실패 시 정리
- 평가 하니스: SWE-bench Pro (verified 부분집합) + Terminal-Bench 2.0 + 자체 30작업 홀드아웃
- 관측 가능성: `gen_ai.*` 시맨틱 컨벤션을 적용한 OpenTelemetry SDK → 셀프 호스팅 Langfuse
- PR 게시: 세분화된 권한 토큰을 쓰는 GitHub App, 범위는 대상 저장소로 한정

```figure
ce-agent-loop
```

## 만들기

1. **TUI와 명령 루프.** Ink로 Bun 프로젝트의 뼈대를 세웁니다. `agent run <repo> "<task>"`를 받습니다. 분할 화면을 출력합니다: 플랜 창(위), 도구 호출 스트림(가운데), 토큰 예산(아래). Ctrl-C로 취소를 추가하고, 종료 전에 `SessionEnd` 훅을 발사하게 합니다.

2. **플랜 상태.** 타입이 지정된 TodoWrite 스키마를 정의합니다(노트가 붙은 pending / in_progress / done 항목). 모델이 매턴 전체 상태를 도구 호출로 다시 쓰게 합니다 — 조금씩 고쳐 쓰게 두지 마세요. 플랜을 `.agent/state.json`에 저장해서 충돌 후 이어서 진행할 수 있게 합니다.

3. **도구 표면.** 여섯 도구를 정의합니다: `read_file`, `edit_file`(diff 미리보기 포함), `ripgrep`, `tree_sitter_symbols`, `run_shell`(타임아웃 포함), `git`(status / diff / commit / push). 하니스가 전송 방식에 얽매이지 않도록 MCP StreamableHTTP로 노출합니다. 모든 도구는 잘라낸 출력을 돌려줍니다(호출당 4k 토큰 상한).

4. **샌드박스 감싸기.** 각 작업은 E2B 샌드박스를 하나 띄웁니다. `git worktree add -b agent/$TASK_ID`로 새 브랜치를 만듭니다. 모든 도구 호출은 샌드박스 안에서 실행됩니다. 호스트 파일시스템에는 닿을 수 없습니다.

5. **훅.** 2026년의 여덟 훅 유형을 전부 구현합니다. 사용자 작성 훅을 최소 넷 연결합니다: (a) 워크트리 밖의 `rm -rf`를 막는 `PreToolUse` 파괴적 명령 가드, (b) `PostToolUse` 토큰 회계, (c) `SessionStart` 예산 초기화, (d) 최종 트레이스 번들을 쓰는 `Stop`.

6. **평가 루프.** SWE-bench Pro Python의 30이슈 부분집합을 클론합니다. 각각에 하니스를 돌립니다. mini-swe-agent(최소 베이스라인)와 pass@1, 작업당 턴 수, 작업당 달러로 비교합니다. 결과를 `eval/results.jsonl`에 씁니다.

7. **비용 통제.** 하드 컷오프: 50턴, 200k 컨텍스트, 작업당 $5. `PreCompact` 훅은 150k 지점에서 이전 턴들을 이전 상태 블록으로 요약해, 플랜을 잃지 않으면서 새 관찰이 들어올 공간을 만듭니다.

8. **PR 게시.** 성공 시 마지막 단계는 `git push` + GitHub API 호출입니다. 본문에 플랜과 diff 요약을 넣어 PR을 엽니다.

## 사용해 보기

```
$ agent run ./my-repo "Fix the race condition in worker.rs"
[plan]  1 locate worker.rs and enumerate mutex uses
        2 identify shared state under contention
        3 propose fix, verify tests
[tool]  ripgrep mutex.*lock -t rust           (44 matches, truncated)
[tool]  read_file src/worker.rs 120..180
[tool]  edit_file src/worker.rs (+8 -3)
[tool]  run_shell cargo test worker::          (passed)
[plan]  1 done · 2 done · 3 done
[done]  PR opened: #482   turns=9   tokens=38k   cost=$0.41
```

## 출시하기

산출물 스킬은 `outputs/skill-terminal-coding-agent.md`에 있습니다. 저장소 경로와 작업 설명이 주어지면 샌드박스 안에서 플랜-행동-관찰 루프 전체를 돌리고, PR URL과 트레이스 번들을 돌려줍니다. 이 캡스톤의 채점 기준:

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 vs 베이스라인 | 같은 Python 작업 30개에서 내 하니스 vs mini-swe-agent |
| 20 | 아키텍처 명확성 | 플랜/행동/관찰 분리, 훅 표면, 도구 스키마 — Live-SWE-agent 구성과 대조 검토 |
| 20 | 안전 | 샌드박스 탈출 테스트, 권한 확인 프롬프트, 파괴적 명령 가드가 레드팀을 통과 |
| 20 | 관측 가능성 | 트레이스 완전성(도구 호출 100% 스팬), 턴별 토큰 회계 |
| 15 | 개발자 UX | 콜드 스타트 < 2초, 충돌 복구 시 플랜 이어하기, Ctrl-C가 도구 실행 중에도 깔끔히 취소 |
| **100** | | |

## 연습 문제

1. 배경 모델을 Claude Sonnet 4.7에서 vLLM으로 서빙하는 Qwen3-Coder-30B로 바꿔 보세요. pass@1과 작업당 달러를 비교하고, 오픈 모델이 어디서 밀리는지 보고하세요.

2. PR 게시 전에 diff를 읽고 수정 루프를 요구할 수 있는 `reviewer` 서브 에이전트를 추가해 보세요. 오탐 리뷰가 SWE-bench 통과율을 단일 에이전트 베이스라인 밑으로 떨어뜨리는지 측정하세요(힌트: 보통 그렇습니다).

3. 샌드박스를 스트레스 테스트하세요: 외부 URL을 `curl`하려는 작업과 워크트리 밖에 쓰려는 작업을 만드세요. 둘 다 PreToolUse 훅에 막히는지 확인하고, 시도 기록을 남기세요.

4. 더 작은 모델(Haiku 4.5)로 `PreCompact` 요약을 구현해 보세요. 3배 압축 시점에서 플랜 충실도가 얼마나 깨지는지 측정하세요.

5. MCP StreamableHTTP 전송을 stdio로 바꿔 보세요. 콜드 스타트와 호출당 지연 시간을 벤치마크하고, 로컬 전용 용도의 승자를 고르세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| 하니스(Harness) | "에이전트 루프" | 모델을 감싸는 코드. 도구를 보내고, 플랜 상태를 유지하고, 예산을 강제한다 |
| 훅(Hook) | "에이전트 이벤트 리스너" | 여덟 생명주기 이벤트 중 하나에서 하니스가 실행하는 사용자 작성 스크립트 |
| 워크트리(Worktree) | "git 샌드박스" | 별도 경로에 있는 연결된 git 체크아웃. 메인 클론을 건드리지 않고 버릴 수 있다 |
| TodoWrite | "플랜 상태" | 모델이 매턴 다시 쓰는 pending/in-progress/done 항목의 타입 지정 목록 |
| StreamableHTTP | "MCP 전송" | 2026 MCP 개정판: 양방향 스트리밍이 가능한 오래 유지되는 HTTP 연결. SSE를 대체 |
| 토큰 상한 | "컨텍스트 예산" | 턴당 또는 세션당 입력+출력 토큰 상한. 압축(compaction)이나 종료를 유발 |
| pass@1 | "한 번 시도 통과율" | 재시도나 테스트셋 훔쳐보기 없이 첫 실행에 푼 SWE-bench 작업 비율 |

## 더 읽을거리

- [Claude Code 문서](https://docs.anthropic.com/en/docs/claude-code) — Anthropic의 참고용 하니스
- [Cursor 3 체인지로그](https://cursor.com/changelog) — Agent Tabs와 Composer 2 제품 노트
- [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) — SWE-bench 하니스 비교용 최소 베이스라인
- [Live-SWE-agent](https://github.com/OpenAutoCoder/live-swe-agent) — Opus 4.5로 SWE-bench Verified 79.2%
- [OpenCode](https://opencode.ai) — 오픈 하니스, 별 112k
- [SWE-bench Pro 리더보드](https://www.swebench.com) — 이 캡스톤이 겨냥하는 평가
- [Model Context Protocol 2026 로드맵](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — StreamableHTTP, 캐퍼빌리티 메타데이터
- [OpenTelemetry GenAI 시맨틱 컨벤션](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 도구 호출과 토큰 사용량의 스팬 스키마
