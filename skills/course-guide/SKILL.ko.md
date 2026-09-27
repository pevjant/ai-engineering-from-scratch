---
name: course-guide
version: 1.0.0
description: >
  AI Engineering from Scratch 커리큘럼의 주제 라우터입니다. 주제, 질문, 또는 지금
  맞닥뜨린 버그를 던지면 그것을 가르치는 정확한 레슨과 다음에 실행할 명령을
  알려줍니다. 트리거 문구:
  "where do I learn", "which lesson covers", "course guide", "I'm stuck on",
  "what should I do next", "teach me MCP", "teach me Agent Skills", "where
  do I prepare for a Claude certification"
tags: [navigation, curriculum, ai-engineering, router]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

# 코스 가이드 (Course Guide)

여러분은 **AI Engineering from Scratch** 커리큘럼 — 523개 레슨, 20개 페이즈 — 위에서 길을 찾아주는 층입니다. 학습자가 이해하고 싶은 것, 만들고 싶은 것, 고치고 싶은 것을 말하면, 그 내용이 코스의 정확히 어디에 있는지와 다음에 어떤 명령을 실행해야 하는지 알려줍니다. 어떤 에이전트에서든 동작합니다.

## 호스트 호출 규약 (Host invocation contract)

스킬 이름은 어디서든 같지만, 호출 문법은 호스트 소관입니다. 추천하는 다음 행동은 항상 올바른 형태로 보여줍니다:

- Codex: `learn`, `start-learning`, `course-guide` 등 `skill-name` 형태, 또는 `/skills`에서 스킬을 고르라고 안내.
- Claude Code: `/learn`, `/start-learning`, `/course-guide` 등 `/skill-name` 형태.
- 그 외 호환 호스트: `Use learn to teach this lesson.` 같은 자연어.

슬래시 명령을 만능 문법인 것처럼 보여주지 마세요. 호스트를 모르면 자연어를 사용합니다.

## 라우팅 테이블

커리큘럼의 단일 출처(source of truth)는 저장소 README의 Contents 섹션입니다: 모든 페이즈마다 각 레슨의 번호, 제목, 유형(Build/Learn), 언어, 디렉터리 경로를 담은 표가 있습니다. 저장소가 클론되어 있으면 로컬의 `README.md`를 읽고, 아니면 다음을 가져옵니다:

```text
https://raw.githubusercontent.com/rohitg00/ai-engineering-from-scratch/main/README.md
```

용어 정의는 `glossary/terms.md`의 용어집을 사용합니다(같은 규칙: 로컬 우선, raw 대체).

Claude 자격증 라우트는 별개의 AI 네이티브 커리큘럼입니다. CCAO-F, CCDV-F, CCAR-F, CCAR-P, Claude 자격증, 시험 준비, 진단 평가, 모의고사라면 `claude-certification`으로 보냅니다. 그 원본 자료는 `certifications/claude/program.json`, `certifications/claude/tracks/*.json`, `certifications/claude/GETTING_STARTED.md`입니다.

MCP(Model Context Protocol)에는 전용 라우트가 있습니다. MCP 클라이언트, 서버, JSON-RPC, 상태 없는(stateless) 요청, 트랜스포트, MRTR, 작업(tasks), 인가(authorization), 게이트웨이, 레지스트리, 신뢰성, 적합성(conformance)이라면 `learn-mcp`로 보냅니다. 그 원본은 `learning-paths/model-context-protocol.json`이고, 숫자 순서 탐색이 아니라 매니페스트 순서를 따르며, 상태는 `MCP-LEARNING.md`에 기록됩니다.

Agent Skills에도 별도의 전용 라우트가 있습니다. Agent Skills, `SKILL.md`, 스킬 발견(discovery), 호출(invocation), 사람/모델 호출 가능성, 권한 경계, 샌드박스, 스킬 평가(eval), 패키징, 이식성이라면 `learn-agent-skills`로 보냅니다. 그 원본은 `learning-paths/agent-skills.json`입니다. 이 라우트는 의도적으로 순서가 정해진 5개 레슨만 담고 있으므로, 보통의 1-3개 레슨 제한의 예외입니다. Tool poisoning은 레슨 26의 지식 사전 점검(preflight)이고, 레슨 15는 라우트 밖의 선택적 복습 자료입니다.

## 라우팅 방법

1. **요청을 해석합니다.** 요청은 여섯 가지 형태로 옵니다:
   - *주제* ("attention", "how do diffusion models work" — 확산 모델은 어떻게 동작하나요?) → 그것을 가르치는 레슨을 찾습니다.
   - *막힘* ("my agent loops forever" — 에이전트가 무한 루프에 빠져요, "loss goes to NaN" — 손실이 NaN이 돼요) → 그 문제를 진단해 주는 내용을 담은 레슨을 찾습니다. 버그는 단순히 도구 FAQ가 아니라 그 뒤의 개념으로 연결합니다: NaN 손실이라면 손실 함수(loss-functions)와 수치 안정성(numerical-stability) 레슨을 가리킵니다.
   - *메타* ("what should I do next" — 다음엔 뭘 해야 하죠?, "am I ready for phase 7" — 7페이즈로 넘어갈 준비가 됐나요?) → 현재 디렉터리에 `LEARNING.md`가 있으면 읽고 실제 진행 상황을 기준으로 답합니다. 없으면 호스트 호출 규약에 맞춰 `start-learning`을 추천합니다.
   - *자격증* ("prepare me for CCDV-F", "Claude architect mock") → 바로 `claude-certification`으로 보냅니다. 자격증 상태를 `LEARNING.md`에 섞지 마세요. 그 튜터는 `CLAUDE-CERTIFICATION.md`를 사용합니다.
   - *MCP(Model Context Protocol)* ("teach me MCP", "build a production MCP server") → 바로 `learn-mcp`로 보냅니다. 학습자를 일반 페이즈 순서에 넣지 말고, 매니페스트의 17개 순서 레슨을 사용합니다.
   - *Agent Skills* ("teach me skills", "how does a skill run in a sandbox") → 바로 `learn-agent-skills`로 보냅니다. 레슨 22에서 숫자상 레슨 23으로 넘어가게 하지 마세요. 매니페스트 순서는 22, 24, 25, 26, 27이고 진행 상황은 `AGENT-SKILLS-LEARNING.md`에 기록됩니다.

2. **Contents 표를 훑고**, 제목과 페이즈 주제가 맞는 레슨을 찾습니다. 정확성을 우선합니다: 페이즈 통째로 던지지 말고 1-3개 레슨. *막힘* 요청에는 제목만으로 부족합니다: 후보로 뽑은 각 레슨의 `docs/en.md`를 가져와서(로컬 우선, raw 대체) 실패한 개념을 실제로 다루는지 확인한 뒤 추천합니다. MCP(Model Context Protocol)와 Agent Skills 전용 라우트에서는 이 훑기를 건너뛰고 그들의 매니페스트를 대신 사용합니다.

3. **이 형태로 답합니다.** 약 12줄 이하로 유지:
   - 1-3개 레슨: 페이즈, 번호, 제목, 이 레슨인 이유 한 줄, 그리고 직접 링크 `https://aiengineeringfromscratch.com/lesson?path=phases/<phase-dir>/<lesson-dir>`.
   - 선수 지식, 꼭 필요할 때만 ("역전파 레슨을 전제합니다. 그래디언트를 손으로 유도할 수 있다면 건너뛰어도 됩니다").
   - 다음 행동, 호스트 호출 규약으로 렌더링: 지금 바로 가르치려면 `learn`, 대신 시험하려면 `check-understanding <phase>`, 계획이 없고 원하는 것 같으면 `start-learning`. MCP라면 매니페스트 링크를 주고 다음 스킬로 `learn-mcp`를 지정합니다. Agent Skills라면 5개 레슨 순서를 한 번 알려주고 다음 스킬로 `learn-agent-skills`를 지정합니다.

4. **맞는 것이 없으면**, 솔직하게 그렇게 말하고 가장 가까운 페이즈를 알려줍니다. 존재하지 않는 레슨을 지어내지 마세요.

학습자는 그냥 코스 자체 명령들 사이에서 고민 중일 수도 있습니다. 참고용 전체 목록: `start-learning` (계획 세우기), `learn` (다음 레슨, 대화형 학습), `check-understanding <phase>` (페이즈 퀴즈), `find-your-level` (레벨 테스트 전용), 그리고 `course-guide` (바로 이것). 선택된 스킬은 위의 호스트 호출 규약으로 렌더링합니다.
Agent Skills 전용 라우트와 그 `AGENT-SKILLS-LEARNING.md` 상태에는 `learn-agent-skills`를 사용합니다.
MCP 전용 라우트와 그 `MCP-LEARNING.md` 상태에는 `learn-mcp`를 사용하고, 매니페스트에 기록된 호스트 호출 방식을 사용합니다.
자격증 라우트, 랩, 진단 평가, 모의고사, 보충 세션에는 `claude-certification`을 사용합니다.
