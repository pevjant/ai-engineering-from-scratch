> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [agent-rules.md](agent-rules.md)

# 에이전트 규칙

## startup/state-file-fresh
- category: startup
- check: state_file_fresh
에이전트는 어떤 도구 호출보다 먼저 agent_state.json을 읽어야 합니다.

## forbidden/no-release-script-edits
- category: forbidden
- check: no_release_script_edits
승인된 릴리스 과제 밖에서는 scripts/release.sh를 절대 편집하지 않습니다.

## done/tests-pass
- category: definition_of_done
- check: tests_pass
과제는 수용 명령이 종료 코드 0으로 끝날 때만 완료됩니다.

## uncertainty/open-question-note
- category: uncertainty
- check: opened_question_when_unsure
신뢰도가 임계값 미만이면 추측하는 대신 질문 노트를 작성합니다.

## approval/new-dependency
- category: approval
- check: new_dependency_approved
런타임 의존성을 추가하려면 명시적인 인간 승인이 필요합니다.
