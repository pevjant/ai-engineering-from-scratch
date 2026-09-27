> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [AGENTS.md](AGENTS.md)

# AGENTS.md

당신은 에이전트 워크벤치와 함께 돌아가는 저장소 안에서 작업하고 있습니다.

행동하기 전에 다음을 읽으세요:

1. `agent_state.json` — 마지막 세션이 어디서 멈췄는지.
2. `task_board.json` — 무엇이 진행 중이고 무엇이 다음인지.
3. `docs/agent-rules.md` — 시작, 금지, 완료, 불확실성, 승인.
4. `docs/reliability-policy.md` — 이 워크벤치가 흡수하도록 설계된 실패 양상.
5. `docs/handoff-protocol.md` — 세션 종료가 만들어야 할 것.
6. `docs/reviewer-rubric.md` — 완료된 작업을 어떻게 판정하는지.

검증 명령: 보드의 활성 태스크에 있는 `acceptance_criteria`를 참조하세요.

팩 버전: 1.0.0
