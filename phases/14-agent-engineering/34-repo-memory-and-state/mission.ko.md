> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mission.md](mission.md)

# 미션 - 저장소 메모리와 영속 상태

## 목표
`agent_state.json`과 `task_board.json`을 위한 JSON 스키마를 작성하고, 상태를 읽고·검증하고·변경하고·원자적으로 쓰는 `StateManager`를 만들어, 두 차례에 걸친 왕복(round-trip)을 증명합니다.

## 입력
- 레슨 32의 세 파일 워크벤치 구성
- required, type, enum, pattern, items를 다루는 표준 라이브러리 전용 검증기

## 산출물
- 코드 옆에 놓인 `agent_state.schema.json`과 `task_board.schema.json`
- 임시 파일 + 이름 바꾸기 쓰기를 갖춘 `StateManager.load`, `StateManager.update`, `StateManager.commit`
- 두 차례에 걸쳐 상태를 변경하고 깔끔하게 다시 읽는 데모 실행

## 통과 기준
- `python3 code/main.py`가 종료 코드 0으로 끝난다
- 나쁜 쓰기(필수 필드 누락, 잘못된 enum)는 저장되지 않고 거부된다
- 실행 뒤의 `workdir/agent_state.json`이 스키마 검증을 통과한다

## 범위 밖
- SQLite나 외부 저장 백엔드. 이 레슨의 주인공은 로컬 파일입니다.
- LangGraph 체크포인터, Letta 메모리 블록. 같은 아이디어지만 저장소가 다를 뿐이며, 여기서는 범위 밖입니다.

## 참고 자료
- `docs/en.md` - 전체 레슨
- `code/main.py` - 참조 구현
- `outputs/skill-state-schema.md` - 추출한 스킬
