> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mission.md](mission.md)

# 미션 - 멀티 세션 핸드오프

## 목표
세션 종료 때 워크벤치 산출물에서 `handoff.md`와 `handoff.json`을 생성해서, 다음 세션이 첫 1분 안에 생산적이게 만듭니다. 두 형태 모두 같은 일곱 필드를 실으며, 어긋나면 JSON이 이깁니다.

## 입력
- 이전 레슨들의 `agent_state.json`, `verification_report.json`, `review_report.json`, `feedback_record.jsonl`
- 일곱 필드: summary, changed_files, commands_run, failed_attempts, open_risks, next_action, verdict_pointer

## 산출물
- 네 산출물을 묶는 `WorkbenchSnapshot` 로더
- `generate_handoff(snapshot) -> (markdown, payload)`
- 마지막 K개 기록과 0이 아닌 종료 전부를 고르는 피드백 필터
- 스크립트 옆에 쓰인 `handoff.md`와 `handoff.json`

## 통과 기준
- `python3 code/main.py`가 종료 코드 0으로 끝난다
- 두 파일 모두 일곱 필드 전부와 비어 있지 않은 `next_action`을 담는다
- 같은 입력으로 스크립트를 다시 돌리면 동일한 패킷이 나온다

## 범위 밖
- 컴팩션 전략 (Codex compact 엔드포인트, Claude Code 5단계). 핸드오프는 세션을 닫고, 컴팩션은 세션을 연장합니다.
- PR 템플릿화. 마크다운은 PR 본문으로 재활용할 수 있지만 레슨은 파일까지만 갑니다.

## 참고 자료
- `docs/en.md` - 전체 레슨
- `code/main.py` - 참조 구현
- `outputs/skill-handoff-generator.md` - 추출한 스킬
