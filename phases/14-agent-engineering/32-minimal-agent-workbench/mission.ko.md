> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mission.md](mission.md)

# 미션 - 최소 에이전트 워크벤치

## 목표
새 `workdir/`에 세 파일 최소 워크벤치(라우터, 상태, 작업 보드)를 깔고, 에이전트 턴 하나가 상태를 읽고, 과제를 꺼내고, 범위 안에 쓰고, 갱신된 상태를 저장할 수 있음을 증명합니다.

## 입력
- 레슨 코드 옆의 빈 `workdir/` 디렉터리
- 세 파일에 대한 지식: `AGENTS.md`, `agent_state.json`, `task_board.json`

## 산출물
- 세 파일을 만들고 턴 하나를 실행하는 `code/main.py`
- 상태, 보드, 검증 명령을 가리키는 짧은 라우터 `workdir/AGENTS.md`
- 활성 과제 id, 건드린 파일, 다음 행동이 담긴 `workdir/agent_state.json`
- 작은 백로그와 상태가 담긴 `workdir/task_board.json`

## 수용 기준
- `python3 code/main.py`가 첫 실행과 두 번째 실행 모두 종료 코드 0으로 끝남
- 두 번째 실행이 처음부터가 아니라 첫 실행이 끝난 지점에서 이어받음
- 스크립트가 출력하는 diff에 그 턴이 건드린 파일 하나가 보임

## 범위 밖
- 범위 계약, 검증 게이트, 리뷰어 에이전트. 이것들은 이후 레슨에서 위에 얹습니다.
- 긴 모놀리식 `AGENTS.md`. 라우터는 의도적으로 짧게 유지합니다.

## 참조
- `docs/en.md` - 전체 레슨
- `code/main.py` - 참조 구현
- `outputs/skill-minimal-workbench.md` - 추출된 스킬
