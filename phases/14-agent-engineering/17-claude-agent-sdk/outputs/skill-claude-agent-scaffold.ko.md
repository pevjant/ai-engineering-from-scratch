---
name: claude-agent-scaffold
description: 서브에이전트, 라이프사이클 훅, 세션 저장소, MCP 서버 연결, W3C 추적 전파를 갖춘 Claude Agent SDK 앱의 뼈대를 세웁니다.
version: 1.0.0
phase: 14
lesson: 17
tags: [claude-agent-sdk, subagents, hooks, session-store, mcp]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-claude-agent-scaffold.md](skill-claude-agent-scaffold.md)

제품 도메인과 MCP 서버 목록이 주어지면, Claude Agent SDK 앱의 뼈대를 세웁니다.

만들 것:

1. 지침, 내장 도구 접근(read_file, write_file, shell, grep, glob, 웹 가져오기), 커스텀 함수 도구를 갖춘 메인 에이전트 정의.
2. 병렬화와 컨텍스트 격리를 위한 서브에이전트 생성기. 오케스트레이터가 컨텍스트 예산을 초과할 상황일 때 쓰세요.
3. 등록된 라이프사이클 훅: 감사용 PreToolUse + PostToolUse, 준비용 SessionStart, 정리용 SessionEnd, 규칙 강제용 UserPromptSubmit(pro-workflow 패턴 참조).
4. `list_subkeys`가 연결되어 서브에이전트 트리를 그리는 세션 저장소(기본은 SQLite).
5. 외부 도구/리소스 표면을 위한 MCP 서버 연결.
6. 호출자의 OTel 스팬이 CLI를 통과해 이어지도록 하는 W3C 추적 컨텍스트 전파.

절대 반려 사항:

- 도구 하나짜리 태스크에 서브에이전트 생성. 서브에이전트는 병렬화나 컨텍스트 격리를 위한 것이지 "read_file 호출 한 번"을 위한 게 아닙니다.
- 동기로 무거운 작업을 하는 훅. 훅은 마이크로초에서 밀리초여야 합니다. 긴 작업은 서브에이전트의 몫입니다.
- 연쇄 삭제 정책 없는 세션 저장소. 버려진 서브에이전트 세션이 저장소를 불룁니다.

거절 규칙:

- 제품이 장기 비동기 작업(수 시간~수 일)을 필요로 하면, 직접 호스팅 SDK를 거절하고 Claude Managed Agents로 안내하세요.
- `--session-mirror`를 공유 위치로 요구하면 거절하세요. 세션 기록에는 PII가 실립니다. 사용자별 암호화 저장소로 거울 복사하세요.
- 에이전트가 도구 사용 없이 UX를 위해 날것의 LLM 스트리밍에 의존한다면, Agent SDK를 거절하고 Client SDK를 직접 권하세요.

출력: `agent.py`, `tools.py`, `hooks.py`, `session.py`, 서브에이전트 정책·훅 레지스트리·세션 백엔드·MCP 연결·OTel 배선을 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 음성 핸드오프는 레슨 22, OTel 스팬 귀속은 레슨 23, 제품이 프로덕션 런타임 모양이 필요하면 레슨 18을 가리킵니다.
