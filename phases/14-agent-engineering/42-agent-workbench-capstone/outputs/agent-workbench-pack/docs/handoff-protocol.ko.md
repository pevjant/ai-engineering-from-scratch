> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [handoff-protocol.md](handoff-protocol.md)

# 핸드오프 프로토콜

모든 세션은 다음을 담은 핸드오프 패킷으로 끝납니다:

- summary (요약)
- changed_files (변경된 파일)
- commands_run (실행된 명령)
- failed_attempts (실패한 시도)
- open_risks (열린 위험 — 심각도 + 상세)
- next_action (다음 행동 — 하나의 구체적 단계)
- verdict_pointer (판정 포인터 — 검증 + 리뷰 리포트 경로)

패킷은 handoff.md(사람용)와 handoff.json(다음 에이전트용) 두 형태로 나갑니다.
필드가 빠지면 세션 종료 훅이 멈춥니다.
