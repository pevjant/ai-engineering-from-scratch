> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [agent-rules.md](agent-rules.md)

# 에이전트 규칙

## startup/state-file-fresh
- category: startup
- check: state_file_fresh
에이전트는 어떤 도구 호출보다 먼저 agent_state.json을 읽어야 합니다.

## forbidden/no-out-of-scope-writes
- category: forbidden
- check: no_out_of_scope_writes
활성 태스크의 범위 계약 밖 파일은 절대 편집하지 않습니다.

## done/tests-pass
- category: definition_of_done
- check: tests_pass
모든 수용 명령이 종료 코드 0으로 끝났을 때만 태스크가 완료됩니다.

## uncertainty/open-question-note
- category: uncertainty
- check: opened_question_when_unsure
확신이 임계값 미만이면 추측하는 대신 질문 노트를 엽니다.

## approval/new-dependency
- category: approval
- check: new_dependency_approved
런타임 의존성을 추가하려면 명시적인 사람의 승인이 필요합니다.
