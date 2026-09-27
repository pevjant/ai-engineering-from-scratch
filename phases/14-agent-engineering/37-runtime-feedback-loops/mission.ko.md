> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mission.md](mission.md)

# 미션 - 런타임 피드백 루프

## 목표
`subprocess.run`을 감싸 stdout, stderr, 종료 코드, 소요 시간을 포착하고, 출력을 결정론적으로 잘라내며, 다음 차례와 검증 게이트가 모두 읽는 JSONL 기록을 덧붙이는 `run_with_feedback`을 만듭니다.

## 입력
- 러너를 시험할 세 개의 데모 명령: 성공 하나, 실패 하나, 느린 것 하나
- 토큰 예산: `...truncated N lines...` 표식과 함께 결정론적인 머리 + 꼬리

## 산출물
- `feedback_record.jsonl`에 쓰는 `run_with_feedback(command, agent_note)`
- JSONL을 스트리밍해서 Python 리스트로 만드는 로더
- 명령별 마지막 기록을 보여주는 프린터

## 통과 기준
- `python3 code/main.py`가 종료 코드 0으로 끝난다
- 재실행할 때마다 `feedback_record.jsonl`에 명령당 기록 하나씩 쌓인다
- `exit_code: null`인 명령은 루프가 성공으로 표시할 수 없다

## 범위 밖
- 텔레메트리 파이프라인 (OTel, Langfuse). 피드백은 다음 차례용, 텔레메트리는 운영자용입니다.
- 마스킹 단계와 로테이션 정책. 레슨 연습 문제가 다룹니다.

## 참고 자료
- `docs/en.md` - 전체 레슨
- `code/main.py` - 참조 구현
- `outputs/skill-feedback-runner.md` - 추출한 스킬
