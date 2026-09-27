> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

---
name: migration-review
description: 변경 사항이 migrations/ 아래 경로를 추가하거나 수정할 때 데이터베이스 마이그레이션 파일을 리뷰합니다. 병합 전에 전방(forward) 동작, 롤백, 락킹, 데이터 안전성 증거를 모을 때 사용하세요.
allowed-tools: Read Grep Glob Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check_scope.py *)
---

# 마이그레이션 리뷰(Migration Review)

`$ARGUMENTS`에 지정된 마이그레이션 파일과, 호환성을 검증하는 데 필요한 코드만 리뷰합니다. 이 스킬은 마이그레이션 적용을 승인하지 않습니다.

1. `python3 ${CLAUDE_SKILL_DIR}/scripts/check_scope.py $ARGUMENTS`를 실행합니다.
2. 검사기가 `migrations/` 밖의 경로를 거부하면 중단합니다.
3. [references/review-checklist.md](references/review-checklist.md)를 읽습니다.
4. 승인된 각 파일과 그 파일의 스키마 가정을 검사합니다.
5. 전방 동작, 롤백 한계, 락(lock) 위험, 데이터 볼륨 위험, 검증 증거, 해결되지 않은 차단 요인을 보고합니다.

`Scope`, `Evidence`, `Risks`, `Rollback`, `Blockers`, `Decision` 제목을 사용해 보고하세요. 필요한 증거가 없으면 항상 `Decision: blocked`로 표시합니다.

번들된 검사기는 [scripts/check_scope.py](scripts/check_scope.py)입니다. `allowed-tools` 항목은 호출된 턴에 한해 그 명령 하나만 미리 승인할 뿐이며, 다른 도구를 제거하거나 프로젝트 권한 규칙을 대체하지 않습니다.
