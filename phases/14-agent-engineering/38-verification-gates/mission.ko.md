> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mission.md](mission.md)

# 미션 - 검증 게이트

## 목표
범위 리포트, 규칙 리포트, 피드백 로그, diff 위의 순수한 결정론적 함수로 `verify(task_id, artifacts)`를 구현해서, 태스크 종료마다 `verification_report.json` 하나를 내보냅니다.

## 입력
- `scope_report.json`, `rule_report.json`, `feedback_record.jsonl`, diff를 위한 스텁 로더
- 검사 표: 수용 명령 실행 여부, 수용 명령 종료 코드 0, 범위 청결, `null` 종료 없음, 모든 차단 심각도 규칙 통과

## 산출물
- 순수한 `verify(task_id, artifacts) -> VerdictReport`
- 검사별 결과와 최종 통과/실패를 보여주는 프린터
- 디스크에 기록된 세 가지 데모 시나리오: 깨끗한 통과, 범위 확산, 수용 누락

## 통과 기준
- `python3 code/main.py`가 종료 코드 0으로 끝난다
- 깨끗한 통과 시나리오는 `passed: true`를, 나머지 둘은 `passed: false`를 보고한다
- 각 시나리오는 `outputs/verification/` 아래에 별개의 `verification_report.json`을 쓴다

## 범위 밖
- LLM-as-judge 로직. 게이트는 결정론적으로 유지하고, 정성적 판단은 레슨 39의 리뷰어 몫입니다.
- 서명된 재정의 감사 로그. 연습 문제가 그 방향으로 확장합니다.

## 참고 자료
- `docs/en.md` - 전체 레슨
- `code/main.py` - 참조 구현
- `outputs/skill-verification-gate.md` - 추출한 스킬
