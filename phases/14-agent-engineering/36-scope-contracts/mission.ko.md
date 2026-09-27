> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mission.md](mission.md)

# 미션 - 범위 계약과 태스크 경계

## 목표
태스크별 `scope_contract.json`과, 에이전트의 diff를 계약과 비교해 금지되거나 범위 밖인 쓰기를 표시하는 글롭 인식 검사기를 작성합니다.

## 입력
- 허용 글롭, 금지 글롭, 수용 명령, 롤백 단락, 필요 승인이 적힌 태스크 설명
- 두 개의 데모 실행: 하나는 범위 안에 머물고, 하나는 범위를 넘음

## 산출물
- `scope_contract.json` 스키마 검증기 (JSON 스키마의 일부, 글롭 배열)
- 건드린 파일과 실행된 명령으로 `RunSummary`를 만드는 diff 파서
- `scope_check(contract, run) -> (violations, in_scope, off_scope)`
- 스크립트 옆에 저장된 `scope_report.json`

## 통과 기준
- `python3 code/main.py`가 종료 코드 0으로 끝난다
- 범위 안 실행은 위반 0건을 보고한다
- 범위 확산 실행은 정확한 범위 밖 파일과 각각의 이유를 보고한다

## 범위 밖
- 시간 예산, 네트워크 이그레스(egress) 허용 목록. 레슨은 파일 글롭을 다루고, 연습 문제가 확장합니다.
- 런타임 인터럽트 연결. 레슨은 리포트에서 끝납니다.

## 참고 자료
- `docs/en.md` - 전체 레슨
- `code/main.py` - 참조 구현
- `outputs/skill-scope-contract.md` - 추출한 스킬
