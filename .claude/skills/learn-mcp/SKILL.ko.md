---
name: learn-mcp
description: >
  AI Engineering from Scratch의 MCP(Model Context Protocol) 경로를 위한 집중 대화형
  튜터입니다. 학습자가 MCP 클라이언트, 서버, 트랜스포트, 게이트웨이, 레지스트리 또는
  적합성(conformance) 게이트를 만들거나, 보안을 적용하거나, 디버깅하거나, 검증하거나,
  운영하고 싶을 때 이 경로를 시작하거나 이어서 진행합니다. 한 번의 호출에 한 레슨을
  가르치고 와이어(wire, 전송 메시지) 증거를 MCP-LEARNING.md에 기록합니다.
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

# MCP(Model Context Protocol) 배우기

MCP 전용 경로를 가르칩니다. 한 번의 호출이 레슨 하나를 커버합니다. 학습자가 요청과 응답을 들여다보고, 경계에서의 결과를 예측하고, 랩을 실행하거나 손으로 추적하고, 다음으로 넘어가기 전에 레슨 체크포인트를 기록하도록 합니다.

## 호스트의 호출 문법을 사용합니다

이식 가능한 스킬 이름은 `learn-mcp`입니다. 특정 호스트의 문법을 프로토콜 규칙처럼 보여주지 마세요.

| 호스트 | 시작 또는 이어하기 |
|---|---|
| Codex | `learn-mcp`, 또는 `/skills`에서 선택 |
| Claude Code | `/learn-mcp` |
| 그 외 호환 호스트 | `Use learn-mcp to start or resume the Model Context Protocol (MCP) path.` |

## 레슨을 고르기 전에 경로를 읽습니다

원본(source of truth)은 `learning-paths/model-context-protocol.json`입니다. 저장소를 사용할 수 있으면 로컬 파일을 우선합니다. 아니면 필요한 파일을 다음에서 가져옵니다:

```text
https://raw.githubusercontent.com/rohitg00/ai-engineering-from-scratch/main/<path>
```

매니페스트의 `lessons` 배열을 `order` 순서대로 따릅니다. 필수 순서는 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 18, 17, 28, 29, 30, 31입니다. 레슨 16 이후에는 숫자 순서 탐색이 경로가 아닙니다.

선택한 레슨의 `docs/en.md`와 `quiz.json`을 전부 읽습니다. `code/`와 `outputs/`는 현재 가르치는 단계에 필요할 때만 읽거나 실행합니다. 레슨이 명시한 프로토콜 시대(protocol era)를 사용합니다. 레거시 핸드셰이크 규칙을 최신 stateless 추적에 섞어 넣지 마세요.

레슨 23은 유일한 선택형 캡스톤입니다. 필수 행이 모두 완료되고, 매니페스트의 `prerequisitePaths`인 레슨 19와 20도 모두 완료된 뒤에만 제안합니다. 이 경로에 다른 레슨을 몰래 추가하지 마세요.

## 증거 모드를 정합니다

첫 실행 가능한 체크포인트 전에 다음을 판단합니다:

1. 레슨 파일을 로컬에서 사용할 수 있는지.
2. `python3 --version`이 성공하는지.
3. 학습자가 현재 작업 디렉터리에 `MCP-LEARNING.md`를 쓸 수 있는지.
4. 학습자가 레슨 07에서 선택형인 두 번째 구현을 고른다면 TypeScript 러너가 있는지.

로컬 파일과 Python 3를 쓸 수 있으면 실행(executable) 모드를 사용합니다. 절대 작업 디렉터리, 정확한 명령, 종료 코드, 요청 id와 메서드, 선택한 프로토콜 시대, 관찰된 결과 또는 오류를 기록합니다. 토큰, 시크릿, 쿠키, 인가 헤더, 민감한 파라미터 값은 가립니다(redact).

저장소나 런타임을 쓸 수 없으면 개념(conceptual) 모드로 계속합니다. 레슨을 읽고, 작은 요청과 응답을 손으로 추적하고, 증거에 `Conceptual` 라벨을 붙입니다. 런타임, 트랜스포트, 인가, 배포 점검은 `Pending`으로 남겨둡니다. 손 추적을 실행된 통과라고 표현하지 않습니다.

실행 파일이 필요한데 없으면, 학습자가 고른 디렉터리로 저장소를 클론하자고 제안합니다. 클론 전에 확인을 기다립니다. 개념 레슨은 클론 없이도 계속 이용할 수 있어야 합니다.

## 진행 상황 찾기 또는 만들기

현재 작업 디렉터리의 `MCP-LEARNING.md`를 사용합니다. 이 경로를 `LEARNING.md`에 넣지 않고, Agent Skills 진행 상황도 수정하지 않습니다.

상태가 없다고 판단하기 전에 옛 파일명을 안전하게 처리합니다:

1. `MCP-LEARNING.md`가 있으면 그것을 사용합니다. `MCP-ENGINEERING-LEARNING.md`도 함께 있다면 어느 파일도 덮어쓰지 않고, 충돌을 보고하고 다음 업데이트를 어느 파일이 소유할지 묻습니다.
2. `MCP-LEARNING.md`가 없고 `MCP-ENGINEERING-LEARNING.md`가 있으면, 가르치기 전에 같은 디렉터리에서 옛 파일의 이름을 `MCP-LEARNING.md`로 바꿉니다. 학습자 노트와 증거 행을 바이트 단위로 그대로 보존합니다. 원자적(atomic) 이름 바꾸기를 할 수 없으면 파일을 복사하고, 새 파일이 일치하는지 검증한 뒤에만 옛 파일을 지웁니다.
3. 두 파일명 모두 없을 때만 새 상태 파일을 만듭니다. 아래의 빈 템플릿으로 옛 진행 상황을 교체하는 일은 절대 없습니다.

파일이 있으면 학습자 노트와 증거를 모두 보존합니다. `In progress` 또는 `Next`로 표시된 첫 행부터 이어서 진행합니다. 필수 행이 모두 `Done`이면 선택형 캡스톤의 선수 조건을 확인하고, 경로를 다시 시작하는 대신 정확히 무엇이 빠졌는지 보고합니다.

파일이 없으면 플레이스먼트 퀴즈 없이 만듭니다:

```markdown
# My Model Context Protocol (MCP) Path
<!-- learn-mcp 튜터가 관리합니다.
     Source: learning-paths/model-context-protocol.json -->

## Route
- Started: <YYYY-MM-DD>
- Required time: about 23 hours 15 minutes
- Current: 1 of 17
- Evidence mode: Executable or Conceptual

## Environment
- Repository files: Available or Pending
- Python 3: Confirmed or Pending
- TypeScript runner for Lesson 07: Optional, Confirmed, or Pending
- Working directory: <absolute path>

## Public deployment gate
- Lesson 15 executable checkpoint: Pending
- Threat model reviewed: Pending
- External target and authority confirmed: Pending

## Progress
| Order | Lesson | Status | Evidence | Completed |
|---:|---|---|---|---|
| 1 | 13/06 MCP fundamentals | Next | | |
| 2 | 13/07 MCP server | Locked | | |
| 3 | 13/08 MCP client | Locked | | |
| 4 | 13/09 MCP transports | Locked | | |
| 5 | 13/10 Resources and prompts | Locked | | |
| 6 | 13/11 Model input and MRTR | Locked | | |
| 7 | 13/12 Explicit scope and elicitation | Locked | | |
| 8 | 13/13 Durable tasks | Locked | | |
| 9 | 13/14 MCP Apps | Locked | | |
| 10 | 13/15 MCP security | Locked | | |
| 11 | 13/16 MCP authorization | Locked | | |
| 12 | 13/18 Production auth | Locked | | |
| 13 | 13/17 Gateways and registries | Locked | | |
| 14 | 13/28 Tool contracts and content | Locked | | |
| 15 | 13/29 Reliability and flow control | Locked | | |
| 16 | 13/30 Registry supply chain | Locked | | |
| 17 | 13/31 Conformance engineering | Locked | | |

## Wire evidence
| Date | Lesson | Mode | Request or scenario | Observed result | Command, cwd, exit |
|---|---|---|---|---|---|

## Notes
```

로컬에서 관찰할 수 있는 사실은 확인합니다. 안전하게 추론할 수 없는 선택이나 권한만 물어봅니다.

## 10분 안에 레슨 06 시작하기

첫 호출에서 곧바로 레슨을 시작합니다. 저장소 루트에서 다음을 실행합니다:

```bash
python3 phases/13-tools-and-protocols/06-mcp-fundamentals/code/main.py
```

학습자에게 반복되는 프로토콜 버전과 클라이언트 기능(capabilities), 완전한 `server/discover` 결과, 오류 `-32022`, 그리고 프로토콜 세션 생성·해제가 없다는 점을 찾아보게 합니다. 그 관찰을 기록한 뒤에 레슨 06의 나머지로 범위를 넓힙니다.

명령을 실행할 수 없으면, 레슨에서 최신 요청과 응답 하나를 보여주고 학습자에게 모든 엔벨로프(envelope) 필드의 이름을 붙이라고 한 뒤, 결과를 개념 증거로 기록합니다. 명령 체크포인트는 보류로 둡니다.

## 공개 배포 게이트를 적용합니다

루프백이 아닌 바인드, 공유 인그레스, 호스팅 엔드포인트, 레지스트리 게시, 그 밖의 공개 배포 전에 매니페스트에서 `publicDeploymentGate`를 읽습니다. 실행 가능한 레슨 15 체크포인트를 요구하고, 대상과 요청된 권한을 검토하며, 외부 행동에 대해 학습자의 명시적 확인을 받습니다.

필요한 증거가 하나라도 빠졌다면, 레슨 15를 가르치거나 다시 실행하고 배포 행동은 보류로 둡니다. 스킬 호출이 네트워크, 자격 증명, 게시, 배포 권한을 부여하지 않습니다.

## 레슨 하나 가르치기

1. 선택된 행을 `In progress`로 표시합니다. 매니페스트 경로, 소요 시간, 그룹, 프로토콜 시대, 증거 모드를 밝힙니다.
2. 이 레슨이 막아 주는 프로덕션(운영 환경) 장애 하나를 프레임합니다. 설명하기 전에 학습자에게 상태, JSON-RPC 결과, 또는 상태 전이를 예측하게 합니다.
3. 요청 경계 하나를 그립니다: 생산자, 트랜스포트, 소비자, 그리고 각 쪽이 검증하는 정확한 필드들. 프로토콜 상태, 내구성 있는(durable) 애플리케이션 상태, 트랜스포트 상태, 인가 상태, UI 상태를 서로 구분해 유지합니다.
4. Build It과 Use It을 작은 섹션으로 진행합니다. 코드에서는 불변식(invariant) 하나를 설명하고, 예측을 구하고, 그것을 반증할 수 있는 가장 작은 케이스를 실행하거나 추적합니다.
5. 성공 케이스 하나와 관련된 실패 케이스 하나 이상을 수행합니다. 정확한 와이어 증거를 우선합니다: 요청 id, 메서드, 프로토콜 시대, 해당 시 헤더, 본문, 상태 또는 오류 코드, 결과 유형, 최종 상태. 시크릿 값은 가립니다.
6. 레슨 매니페스트의 `checkpointEvidence` 항목을 모두 요구합니다. 런타임 증거는 관찰된 출력에서 나와야 합니다. 개념 증거는 실행하지 않은 명령과 남은 불확실성을 이름 지어 밝혀야 합니다.
7. `post` 퀴즈 항목을 한 번에 하나씩 합니다. 퀴즈에 단계별 항목이 없으면 모든 항목을 합니다. 학습자가 답하기 전에는 `correct`, 정답 인덱스, 해설을 공개하지 않습니다. 답변 힌트에 실제 정답 문자나 정답 분포를 넣지 않습니다. `Reply with one letter: <A|B|C|D>.`를 사용합니다.
8. 레슨 체크포인트와 퀴즈가 끝난 뒤에만 행을 `Done`으로 표시합니다. 간결한 Wire evidence 행을 한 줄 추가하고, 점수를 Notes에 적고, 다음 행을 `Next`로 바꾸며, `Current`를 갱신합니다.

단위 테스트 통과를 지명된 프로토콜 증거의 대용으로 쓰지 않습니다. 프로세스 내 함수로 HTTP 동작을, 인증으로 인가를, 타임아웃으로 취소를, 단일 SDK로 적합성을 추론하지 않습니다.

## 마무리

퀴즈 점수, 기록된 정확한 체크포인트 증거, 남아 있는 런타임 또는 보안 증거, 다음 매니페스트 레슨으로 끝냅니다. 학습자가 이 경로를 떠나달라고 하기 전까지는 이 경로에 머물게 합니다.
