> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [ccar-f-exact-mechanics.md](ccar-f-exact-mechanics.md)

# CCAR-F 정확한 작동 방식 복습

> 아키텍처를 이해한 뒤에 날짜가 표시된 조회 훈련(드릴)으로 활용하세요. 워크플로를 직접 만드는 일을 대신해 주지는 않습니다.

**가이드:** Claude Certified Architect - Foundations, version 1.0
**가이드 시행:** 2026년 7월
**검증일:** 2026-08-09

공개 CCAR-F 가이드는 오래 쓸 수 있는 판단력과 정확한 작동 방식을 시험합니다.
이 복습 자료는 가이드가 이름을 붙인 인터페이스들을 모아서, 그럴듯해 보이는
명령·경로·필드와 올바른 설계를 구별할 수 있게 도와줍니다. 활용하기 전에 현재
공식 가이드와 문서로 모든 항목을 다시 확인하세요.

## 에이전트 루프와 세션 상태

| 작동 방식 | 떠올릴 내용 | 결정 경계 |
|---|---|---|
| `stop_reason: "tool_use"` | 요청된 도구를 실행하고, 짝이 맞는 결과를 덧붙인 뒤 계속 진행 | 자연어 표현으로 루프 상태를 추측하지 않는다 |
| `stop_reason: "end_turn"` | 모델이 정상 종료 턴에 도달했다 | 프로덕션에서는 오류, 한도, 취소 등 다른 종료 상태도 처리한다 |
| 도구 결과 식별 | 각 결과를 원래 tool-use 식별자에 맞춰 반환한다 | 동시에 도착한 결과를 배열 위치로 짝짓지 않는다 |
| 대화 상태 | 다음 요청에 필요한 콘텐츠 블록을 보존한다 | 정보가 손실되는 요약 밖에 오래 쓸 사실을 추출해 둔다 |
| `--resume <session-name>` | 이름 붙은 이전 세션을 이어서 진행 | 오래된 도구 관찰 내용이 상했다면 명시적인 요약과 함께 새로 시작한다 |
| `fork_session` | 공유 베이스라인에서 독립적인 탐색 분기를 만든다 | 접근 방식이 서로 섞이면 안 될 때는 별도 분기를 사용한다 |

## 도구 선택과 구조화된 출력

| 작동 방식 | 의미 |
|---|---|
| `tool_choice: "auto"` | 모델이 도구를 호출하거나 텍스트를 반환할 수 있다 |
| `tool_choice: "any"` | 모델이 제공된 도구 중 하나를 반드시 호출해야 한다 |
| `tool_choice: {"type":"tool","name":"..."}` | 이름이 지정된 도구를 반드시 선택해야 한다 |
| Strict JSON Schema | 구문·형태 실패를 줄여 준다; 의미 검증은 여전히 필요하다 |
| Pydantic validation | 형태와 도메인 검사를 위한 Python 구현 옵션이지, 추출한 사실이 참이라는 증명이 아니다 |

강제 선택은 워크플로가 그 첫 번째 형식화된(typed) 연산을 정말로 필요로 할 때만
쓰세요. 오케스트레이션, 권한 부여, 의미 검증을 일반적으로 대신하지 않습니다.

## MCP 구성

| 범위 또는 동작 | 공개 가이드의 작동 방식 |
|---|---|
| 공유 프로젝트 서버 | 버전 관리 하의 `.mcp.json` |
| 개인 또는 실험용 서버 | `~/.claude.json` |
| 비밀 값 | `${GITHUB_TOKEN}` 같은 환경 변수 확장; 값은 절대 커밋하지 않는다 |
| 탐색 | 구성된 서버의 도구는 연결 시점에 발견된다 |
| 리소스 | 반복된 도구 호출로 일일이 훑어보기 아깝다면 콘텐츠 카탈로그와 스키마를 노출한다 |

현재 MCP 전송 방식과 배포 세부 사항은 레슨 11에 있습니다. stdio와 Streamable
HTTP는 현재 전송 방식으로, 구식 HTTP+SSE는 폐기(deprecated)된 것으로 다루세요.

## Claude Code 팀 표면

| 표면 | 정확한 검토 지점 |
|---|---|
| 프로젝트 커맨드 | `.claude/commands/` |
| 개인 커맨드 | `~/.claude/commands/` |
| 스킬 | `.claude/skills/<skill-name>/SKILL.md` |
| 스킬 frontmatter | 가이드에 `context: fork`, `allowed-tools`, `argument-hint`가 언급된다 |
| 조건부 규칙 | `.claude/rules/` 아래 마크다운 + YAML frontmatter의 `paths` glob |
| 비대화형 실행 | `-p` 또는 `--print` |
| 기계 판독 가능한 CI | `--output-format json`과 `--json-schema` |

범위(scope)도 답의 일부입니다. 쓸모 있는 지시라도 사용자, 프로젝트, 경로별
위치가 틀리면 구성 실패입니다.

## 메시지 배치

2026년 7월 가이드는 이런 시험 참고 사실을 언급합니다:

- 표준 처리 대비 50% 비용 절감.
- 최대 24시간의 처리 윈도우, 보장된 지연 시간 SLA 없음.
- 요청/결과 대조를 위한 `custom_id`.
- 하나의 배치 요청 안에서는 멀티턴 도구 실행 불가.
- 실패를 분류한 뒤 안전한 실패 항목만 재제출.

이것들은 날짜가 표시된 제품 사실입니다. 실제 비용이나 SLA 결정에 쓰기 전에 현재
Message Batches 문서를 확인하세요.

## 내장 도구 선택

가이드는 Read, Write, Edit, Bash, Grep, Glob을 명시적으로 언급합니다. 인기
순위를 외우는 대신 경계를 검토하세요:

- 살펴 보지 않은 내용을 바꾸기 전에는 Read를 먼저 한다.
- Edit에는 믿을 만한 일치가 필요하다; 통제된 교체가 더 안전할 때만 파일 전체
  쓰기를 쓴다.
- Grep은 내용을 검색하고, Glob은 패턴으로 경로를 찾는다.
- Bash는 강력한 실행 경계를 넘으므로 더 엄격한 권한, 검증, 샌드박스 통제가
  필요하다.

## 백지 훈련(클로즈드북 드릴)

위 표의 각 행마다:

1. 정확한 경로, 플래그, 필드, 상태를 기억으로 적는다.
2. 그것이 옳은 선택이 되는 시나리오를 하나 든다.
3. 그럴듯한 대안 하나와 그것이 어기는 제약을 든다.
4. 공식 자료에서 정확한 작동 방식을 확인한다.
5. 그 결정을 연습하는 링크된 레슨 산출물을 만들거나 실행한다.

범위, 실패 양상, 더 안전한 대안을 설명할 수 있기 전에는 외운 문자열을 숙달로
치지 마세요.

## 공식 자료

- [CCAR-F 시험 가이드](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542750%2FClaude+Certified+Architect+%E2%80%93+Foundations+Exam+Guide.pdf)
- [Claude Code 문서](https://code.claude.com/docs/en/overview)
- [Claude Agent SDK 문서](https://code.claude.com/docs/en/agent-sdk/overview)
- [도구 사용 문서](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [구조화된 출력 문서](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Message Batches 문서](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- [MCP 문서](https://modelcontextprotocol.io/docs/getting-started/intro)
