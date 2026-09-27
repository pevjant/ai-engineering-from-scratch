> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mission.md](mission.md)

# 미션 - 캡스톤: 재사용 가능한 에이전트 워크벤치 팩 출시하기

## 목표
이전 열한 레슨을 버전 관리되는 `outputs/agent-workbench-pack/` 디렉터리로 조립하고, 어떤 대상 저장소에든 멱등하게 내려놓는 설치기를 갖춥니다.

## 입력
- 레슨 32부터 40까지의 스키마, 스크립트, 문서
- 팩 구성: `AGENTS.md`, `docs/`, `schemas/`, `scripts/`, `bin/`, `README.md`, `VERSION`

## 산출물
- 전체 구성이 채워진 `outputs/agent-workbench-pack/`
- `--force` 없이는 덮어쓰기를 거부하는 `bin/install.sh` (또는 `bin/install.py`)
- `VERSION` 파일과, 무엇이 들어가고 무엇이 안 들어가는지 설명하는 `README.md`

## 통과 기준
- `python3 code/main.py`가 종료 코드 0으로 끝나고 팩 트리를 출력한다
- 조립기를 다시 실행해도 멱등하다
- 새 대상에 `bin/install.sh`를 실행하면 동작하는 워크벤치가 남는다: 상태, 보드, 규칙, 범위, 초기화, 러너, 게이트, 리뷰어, 핸드오프가 모두 제자리에

## 범위 밖
- 프로젝트별 태스크 내용. 태스크는 대상 저장소의 보드에 있어야지 팩 안에 있으면 안 됩니다.
- 벤더 SDK 호출. 팩은 설계상 프레임워크 불가지론적입니다.

## 참고 자료
- `docs/en.md` - 전체 레슨
- `code/main.py` - 참조 구현
- `outputs/skill-workbench-pack.md` - 추출한 스킬
