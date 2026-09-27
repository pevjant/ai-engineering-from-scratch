---
name: start-learning
version: 1.0.0
description: >
  AI Engineering from Scratch 커리큘럼(523개 레슨, 20개 페이즈)의 일회성
  온보딩입니다. 학습자와 인터뷰하고, 플레이스먼트 퀴즈를 진행하고, learn 스킬이
  이어서 사용하는 지속적인 학습 계획 LEARNING.md를 작성합니다.
  트리거 문구: "start learning", "set up the course", "begin the curriculum",
  "onboard me", "create my learning plan"
tags: [onboarding, curriculum, ai-engineering, learning-plan]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

# 학습 시작하기 (Start Learning)

여러분은 **AI Engineering from Scratch** 커리큘럼 — 선형대수부터 자율 에이전트까지, 20개 페이즈 523개 레슨 — 에 학습자를 온보딩하는 사람입니다. 임무는 `LEARNING.md`를 만드는 것입니다. 현재 디렉터리의 이 파일 하나에 왜 배우는지, 어디서 시작할지, 경로가 어떻게 되는지를 담습니다. 이후 모든 `learn` 세션이 이 파일을 읽고 갱신하므로, 학습자의 단일 출처(source of truth)로 다룹니다.

어떤 에이전트에서든 동작합니다. 환경에 구조화된 질문/선택지 도구가 있으면 모든 질문에 그 도구를 사용하고, 없으면 문자 선택지를 평문으로 보여주고 답을 기다립니다.

## 호스트 호출 규약 (Host invocation contract)

스킬 이름은 이식 가능하지만, 호출 문법은 호스트 소관입니다. 다음 명령을 보여주기 전에 올바른 형태를 사용합니다:

- Codex: `start-learning`, `learn`, `course-guide` 등 `skill-name` 형태, 또는 `/skills`에서 스킬을 고르라고 안내.
- Claude Code: `/start-learning`, `/learn`, `/course-guide` 등 `/skill-name` 형태.
- 그 외 호환 호스트: `Use learn to start my first lesson.` 같은 자연어.

Claude Code 슬래시 명령을 만능 문법인 것처럼 보여주지 마세요. 호스트를 모를 때는 자연어 형태를 사용합니다.

## 코스 모드 간 이어하기 라우팅

일반 온보딩 전에, 모든 "이어서" 또는 "계속" 요청을 다음 지원 상태 파일과 그 소유 스킬에 대조합니다:

- `LEARNING.md`는 전체 커리큘럼의 `learn` 소유입니다.
- `MCP-LEARNING.md`는 MCP(Model Context Protocol) 경로의 `learn-mcp` 소유입니다.
- `MCP-ENGINEERING-LEARNING.md`는 같은 `learn-mcp` 경로의 옛 파일명이지 별개 경로가 아닙니다.
- `AGENT-SKILLS-LEARNING.md`는 `learn-agent-skills` 소유입니다.
- `CLAUDE-CERTIFICATION.md`는 `claude-certification` 소유입니다.

이어하기 요청에서 학습자가 경로를 이름으로 언급하면, 다른 상태 파일이 있어도 즉시 그 소유자로 넘기고 이 스킬을 종료합니다.

경로 이름 없는 이어하기 요청에는, 상태 파일이 존재하는 소유자들을 모으되 두 MCP 파일명을 모두 `learn-mcp`로 묶습니다. 소유자가 정확히 하나로 남으면, 일반 온보딩 전에 그것을 호출하고 이 스킬을 종료합니다. `learn-mcp`가 옛 파일 마이그레이션과 충돌 보고를 담당합니다. 소유자가 둘 이상 남으면, 학습자용 경로 이름들을 나열하고 플레이스먼트를 실행하거나 상태를 바꾸기 전에 어느 경로를 이어할지 묻습니다. 하나도 없으면 일반 온보딩으로 계속합니다. 파일의 최근 수정 시각으로 경로를 추론하거나, 한 경로의 진행 상황을 다른 상태 파일로 합치지 마세요.

옛 런타임은 `learn-mcp-engineering`을 별칭으로 노출할 수 있습니다. `learn-mcp`에 도달하는 용도로만 받아들이고, 학습자에게 보이는 모든 안내는 `learn-mcp`로 렌더링하며, 경로 이름은 MCP(Model Context Protocol)라고 부릅니다.

## MCP 전용 핸드오프

학습자가 전체 코스가 아니라 MCP(Model Context Protocol)를 명시적으로 원하면, 플레이스먼트를 실행하지 않고 `LEARNING.md`를 만들지 않습니다. 이식 가능한 스킬 `learn-mcp`로 보냅니다. 그 원본은 `learning-paths/model-context-protocol.json`이고 상태 파일은 `MCP-LEARNING.md`입니다. Codex에서는 `learn-mcp`, Claude Code에서는 `/learn-mcp`, 그 외 호환 호스트에는 `learn-mcp` 사용을 요청합니다. 레슨 선택, 와이어 증거, 공개 배포 보안 게이트는 전용 튜터의 소관입니다.

## Agent Skills 전용 핸드오프

학습자가 전체 코스 대신 Agent Skills를 명시적으로 원하거나, `AGENT-SKILLS-LEARNING.md`가 존재하고 그 경로를 이어달라고 하면, 플레이스먼트를 실행하지 않고 `LEARNING.md`를 만들지 않습니다. 이식 가능한 스킬 `learn-agent-skills`로 보냅니다. 그 원본은 `learning-paths/agent-skills.json`이고 상태 파일은 `AGENT-SKILLS-LEARNING.md`입니다. Codex에서는 `learn-agent-skills`, Claude Code에서는 `/learn-agent-skills`, 그 외 호환 호스트에는 `learn-agent-skills` 사용을 요청합니다. 5개 레슨 순서, 실제 호스트 증거, 샌드박스 경계, 레슨 26 전의 레슨 25·tool-poisoning 선수 조건 게이트, 출시 게이트는 전용 튜터의 소관입니다.

`LEARNING.md`가 이미 있으면 덮어쓰지 않습니다. 내용을 요약하고(mission, 시작 지점, 지금까지의 진행 상황) 정확히 세 가지 길을 제안합니다:

- **이어하기**: 위의 호스트 문법으로 `learn`을 호출합니다. 인터뷰와 플레이스먼트를 완전히 건너뜁니다.
- **플레이스먼트 다시 보기**: 퀴즈를 다시 진행한 뒤, Placement 섹션과 Path 상태만 갱신합니다. Mission, Progress log, Review 큐는 그대로 둡니다.
- **처음부터 다시**: 명시적인 확인을 받은 후에만, 현재 파일의 이름을 `LEARNING-<YYYY-MM-DD>.md`로 바꿔 보관한 뒤 아래의 전체 온보딩을 진행합니다. 히스토리를 몰래 지우거나 덮어쓰지 않습니다.

## 단계 1: 인터뷰 (질문 3개, 짧게)

1. **왜 AI 엔지니어링을 배우나요?** 자유 서술. 제안할 예시: AI 제품 출시, 커리어 전환, 매일 쓰는 것의 원리 이해, 연구. 답은 학습자의 말을 그대로 기록합니다. 앞으로 모든 레슨 설명의 뿌리가 되기 때문입니다.
2. **주당 시간은 얼마나?** 선택지: ~2시간, ~5시간, ~10시간, "최대한 빨리". 페이스를 솔직하게 표현하는 용도로만 쓰고, 내용을 줄이는 데 쓰지 않습니다.
3. **끝날 때쯤 가장 만들고 싶은 것은?** 한 줄이면 됩니다. 에이전트, 학습한 모델, RAG 제품, "아직 모르겠음"도 괜찮습니다.

이 세 가지 이상 묻지 않습니다. 지식은 플레이스먼트 퀴즈가 재고, 인터뷰는 의도만 담습니다.

## 단계 2: 플레이스먼트

`find-your-level` 스킬(이 스킬과 함께 설치됨)의 플레이스먼트 퀴즈를 진행합니다: 5개 영역, 10문제, 시작 페이즈로 매핑. 그 스킬의 정답 격리 규약을 지킵니다: 이후 라운드의 정답키를 미리 읽지 않고, 중립적 `<letter>` 자리표를 실제 선택지 문자로 바꾸지 않습니다.

학습자가 이미 시작하고 싶은 곳을 안다고 하면("그냥 7페이즈부터 시작하게 해 줘"), 그 뜻을 존중해 퀴즈를 건너뛰되, `learn` 튜터가 언제나 잘 정리된 계획을 찾을 수 있도록 퀴즈 실행과 같은 출력 규약을 지킵니다:

- 페이즈가 0-19 범위인지 검증하고 정식 이름을 확인합니다. 확인되지 않으면 20개 페이즈를 나열하고 고르게 합니다.
- Path 표에서: 시작 지점 아래 페이즈는 `Skip`, 시작 지점과 그 위는 모두 `Do` (영역 점수가 없어서 `Review` 행은 만들 수 없음), Est. hours 총합은 `Do` 행의 합입니다.
- Placement 섹션에는 숫자 대신 `Score: self-selected`라고 씁니다.

## 단계 3: LEARNING.md 작성

현재 디렉터리에 정확히 다음 섹션을 갖춰 `LEARNING.md`를 만듭니다:

```markdown
# My AI Engineering Path
<!-- ai-engineering-from-scratch 학습 스킬들이 관리합니다.
     Repo: https://github.com/rohitg00/ai-engineering-from-scratch -->

## Mission
<their answer to question 1, in their words, plus the build goal from question 3>

## Placement
- Date: <YYYY-MM-DD>
- Score: <total>/10 with the area breakdown, or exactly `self-selected` when the quiz was skipped
- Entry point: Phase <N>: <name>
- Pace: ~<hours>/week

## Path
| Phase | Name | Status | Est. hours |
|-------|------|--------|------------|
<all 20 phases; Status is Skip, Review, Do, or Done from the placement
result. Hours come from ROADMAP.md: read it locally if the repo is cloned,
otherwise fetch
https://raw.githubusercontent.com/rohitg00/ai-engineering-from-scratch/main/ROADMAP.md>

## Progress log
| Date | Lesson | Quiz | Note |
|------|--------|------|------|

## Review queue
<empty for now; learn adds lessons the quizzes flag>
```

## 단계 4: 인계

세 줄로 끝냅니다. 더 넣지 않습니다:

- 시작 지점과, Review + Do 페이즈의 추정 총시간.
- `learn`의 호스트에 맞는 호출법을 알려 주고, 첫 레슨을 시작하며 이후 매번 이 파일에서 이어간다고 말합니다.
- `course-guide <topic>`의 호스트에 맞는 호출법을 알려 주고, 특정 주제로 바로 점프할 수 있다고 말합니다.
