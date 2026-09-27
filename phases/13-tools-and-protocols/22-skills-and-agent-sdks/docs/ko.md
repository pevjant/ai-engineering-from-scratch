> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 에이전트 스킬: 이식 가능한 계약과 런타임 경계

> 스킬은 파일명만 멋진 긴 프롬프트가 아닙니다. 스킬은 런타임 계약을 통해 에이전트의 컨텍스트에 들어오는, 명령어·리소스·실행 가능한 도우미를 담은 '발견 가능한 패키지'입니다.

**유형:** 빌드(Build)
**언어:** Python(표준 라이브러리)
**선수 지식:** 페이즈 13 · 01(도구 인터페이스), 페이즈 13 · 05(도구 스키마 설계)
**시간:** 약 90분

## 학습 목표

- 프롬프트, 저장소 지침, 도구, 훅, 서브에이전트, 플러그인과 헷갈리지 않고 에이전트 스킬을 정의합니다.
- 이식 가능한 `SKILL.md` 계약을 읽고, 런타임 전용 확장과 구분합니다.
- 발견(discovery), 선택(selection), 활성화(activation), 리소스 로딩, 도구 사용, 검증을 서로 다른 생명주기 단계로 설명합니다.
- 런타임이 에이전트의 카탈로그에 등록하기 전에 스킬 패키지를 검증합니다.
- 구체적인 작업에 대해 스킬, MCP 도구, 훅, 서브에이전트, 평범한 코드 중 알맞은 것을 고릅니다.

## 10분 만에 첫 성공 경험하기

긴 설명을 읽기 전에 먼저 해보세요. 작은 스킬을 하나 만들고, 리뷰어 번들 전체를 실제 에이전트 호스트에 설치한 뒤, 호출하고, 결과를 확인하고, 삭제까지 해봅니다. 눈으로 확인할 수 있는 결과로 생명주기 전체를 검증하는 과정입니다.

### 실제 호스트 실습 전 점검

실제 호스트를 쓰는 체크포인트를 진행하려면 Node.js, `npx`, Python 3, 스킬을 지원하는 호스트 하나, 그리고 설치 프로그램에서 고른 프로젝트 또는 사용자 스코프에 대한 쓰기 권한이 필요합니다. 먼저 로컬 명령어를 확인하세요:

```bash
node --version
npx --version
python3 --version
```

설치 전에 어떤 호스트와 스코프를 쓸지 정해 두세요. 요구 사항을 하나라도 충족할 수 없다면 이 레슨을 웹사이트에서 읽거나, 아래의 수동 패키지 실습으로 계속 진행하세요. 이 대체 방법으로도 계약 내용은 배울 수 있지만, 호스트의 발견·호출·번들 스크립트 실행·삭제 동작은 확인할 수 없습니다. 해당 항목은 '미확인'으로 표시해 두세요.

### 1. 빈 작업 디렉터리에서 시작하기

학습용 작업을 모아 두는 부모 디렉터리 어디서든 이 명령어를 실행하세요:

```bash
mkdir -p agent-skills-first-run
cd agent-skills-first-run
TARGET_ROOT="$(pwd -P)"
printf 'TARGET_ROOT=%s\n' "$TARGET_ROOT"
ls -A
```

마지막 명령어는 아무것도 출력하지 않아야 합니다. 파일이 출력된다면 리뷰 경계를 명확히 하기 위해 다른 빈 디렉터리를 고르세요.

첫 스킬을 담을 디렉터리를 만듭니다:

```bash
mkdir -p my-first-skill
```

다음 내용으로 `my-first-skill/SKILL.md` 파일을 만드세요:

```markdown
---
name: my-first-skill
description: Turn rough meeting notes into a compact decision record when the user asks to capture a technical decision.
---

# Decision record

Extract the decision, context, alternatives, owner, and next review date.
If the notes do not contain a decision, ask one clarifying question instead
of inventing one.
```

의도한 디렉터리에 파일을 만들었는지 확인합니다:

```bash
test -f my-first-skill/SKILL.md
```

출력이 없고 종료 코드가 0이면 파일이 존재한다는 뜻입니다.

### 2. 리뷰어 번들 전체 설치하기

`agent-skills-first-run` 디렉터리에 그대로 있는 상태에서 실행합니다:

```bash
npx skills add rohitg00/ai-engineering-from-scratch --skill skill-contract-reviewer --full-depth
```

사용 중인 에이전트 호스트와 스코프를 선택하세요. 설치 프로그램이 `skill-contract-reviewer`와 설치된 위치를 목록으로 보여 줄 것입니다. 이 레슨의 스킬은 references, 스크립트, asset을 포함한 중첩 번들이므로 `--full-depth`가 필요합니다.

`SKILL_ROOT`를 설치 프로그램이 알려 준 절대 경로 디렉터리로 설정하세요. 설치된 `SKILL.md`가 들어 있는 디렉터리여야 하며, 레슨 소스 디렉터리나 현재 작업 공간이 아니어야 합니다:

```bash
# 자리 표시자를 설치 프로그램이 출력한 설치 위치로 바꾸세요.
SKILL_ROOT="$(cd "/absolute/path/to/skill-contract-reviewer" && pwd -P)"
test -f "$SKILL_ROOT/SKILL.md"
printf 'SKILL_ROOT=%s\n' "$SKILL_ROOT"
```

에이전트 세션이 이미 열려 있었다면 새 세션을 시작하거나 해당 호스트의 스킬 재스캔 명령을 사용하세요. 모든 호스트가 카탈로그를 핫 리로드한다고 가정하지 마세요.

### 3. 명시적으로 호출하기

설치된 에이전트에서 작업 디렉터리를 `agent-skills-first-run`으로 맞춘 뒤, 해당 호스트가 지원하는 문법으로 호출합니다:

| 호스트 | 명시적 호출 |
|---|---|
| Codex | `skill-contract-reviewer`를 입력하거나 `/skills`에서 선택한 뒤 리뷰 요청 전달 |
| Claude Code | `/skill-contract-reviewer` 입력 후 리뷰 요청 전달 |
| 이식 가능한 대체 방법 | `Use skill-contract-reviewer to review the target package.` |

요청에는 `SKILL_ROOT`와 `TARGET_ROOT`에 출력된 절대 경로 값을 그대로 넣으세요. 실행 전에 호스트가 이 값들을 실제 경로로 펼치도록 요구하고, 프로세스 작업 디렉터리에 의존하는 명령이 아니라 실제로 확정된 명령을 보여 달라고 요청하세요:

```text
Use skill-contract-reviewer to review <TARGET_ROOT>/my-first-skill. The installed bundle root is <SKILL_ROOT>. Run python3 <SKILL_ROOT>/scripts/check_skill.py <TARGET_ROOT>/my-first-skill. Before running it, show the fully resolved argv. Return the validation report, selected primitives, and one sentence for each selection. Include the resolved script path, resolved target path, cwd, argv, and exit code as execution evidence.
```

확정된 명령은 자리 표시자가 하나도 남지 않은 다음 형태여야 합니다:

```bash
python3 "/absolute/install/path/skill-contract-reviewer/scripts/check_skill.py" \
  "/absolute/workspace/path/agent-skills-first-run/my-first-skill"
```

성공한 결과는 다음 세 가지를 모두 만족합니다:

1. 호스트가 이름으로 `skill-contract-reviewer`를 찾습니다.
2. 리뷰어가 패키지 계약을 읽고, 함께 번들된 검증 스크립트를 실행합니다.
3. 응답에 샘플에 대한 구조적 오류가 없는 검증 보고서와, 근거가 있는 프리미티브 선택이 담겨 있습니다.

실행 증거에는 스크립트 경로, 대상 경로, cwd(작업 디렉터리), 정확한 인자 벡터(argv), 종료 코드도 함께 담겨야 합니다. 이 필드들이 없는 유창한 보고서만으로는 설치된 동반 스크립트가 실제로 실행됐다는 증거가 되지 않습니다.

호스트가 스킬을 사용할 수 없다고 보고하면 설치 위치를 확인하고, 한 번 재스캔 또는 재시작한 뒤 명시적 요청을 다시 시도하세요. 설치 실패를 감추려고 스킬 description을 고쳐 쓰면 안 됩니다.

### 4. 암시적 선택 확인해 보기

새 에이전트 턴을 시작하고, 스킬 이름을 언급하지 않은 채 같은 작업을 입력합니다:

```text
Review <TARGET_ROOT>/my-first-skill as a reusable agent package and tell me whether its package contract is valid.
```

호스트가 선택된 스킬을 보여 준다면 `skill-contract-reviewer`를 골랐는지 기록하세요. 라우팅 정보를 보여 주지 않는다면 암시적 선택은 '미확인'으로 표시합니다. 명시적 호출이 이식 가능한 대체 방법입니다.

### 5. 정리하기

설치된 리뷰어 번들만 제거합니다:

```bash
npx skills remove skill-contract-reviewer
```

설치 때 사용한 것과 같은 호스트와 스코프를 선택하세요. 재스캔이나 새 세션 이후에는 `skill-contract-reviewer`를 명시적으로 요청했을 때 '사용할 수 없음'이 보고되어야 합니다. `my-first-skill`은 이후 레슨에서 쓰니 남겨 두고, 트랙을 모두 마친 후에 실습 디렉터리를 지우면 됩니다.

## 문제 상황

팀에 믿을 만한 릴리스 워크플로가 있다고 칩시다. 이 워크플로는 병합된 변경 사항을 찾고, 마이그레이션 노트를 확인하고, 체인지로그를 갱신하고, 패키징 명령을 실행하고, 리뷰 체크리스트를 만들어 냅니다.

이 워크플로를 프롬프트 하나에 담으면 붙여 넣기는 쉽지만 운영하기는 어렵습니다. 프롬프트에는 안정적인 정체성도, 발견 규칙도, 리소스 경계도, 검증 가능한 패키지 형태도 없고, 기본적인 질문에 대한 답도 없습니다. 누가 호출할 수 있나? 모델은 언제 이것을 선택해야 하나? 어떤 스크립트를 실행할 수 있나? 어떤 파일을 신뢰할 수 있나? 컨텍스트가 압축되면 무엇이 남나?

반대로 모든 재사용 가능한 지침을 스킬로 만드는 실수도 있습니다. 저장소 관례, 결정론적 자동화, 외부 도구, 이벤트 훅, 위임된 에이전트는 각각 다른 문제를 풉니다. 이것을 전부 `SKILL.md`에 욱여 넣으면 겉보기에는 이식 가능해 보이지만 실제로는 한 호스트의 문서화되지 않은 동작에 의존하는 디렉터리가 만들어집니다.

첫 번째 엔지니어링 과제는 분류입니다. 어떻게 패키징할지 정하기 전에, 이 산출물이 무엇인지부터 정하세요.

## 개념

### 스킬은 절차 지식을 담는다

에이전트 스킬은 `SKILL.md`를 진입점으로 갖는 디렉터리입니다. 진입 파일에는 YAML 프론트매터와 그 뒤를 따르는 Markdown 지침이 들어 있습니다. 디렉터리에는 references, scripts, assets 같은 것도 담을 수 있습니다.

```figure
skill-package-anatomy
```

배포 단위는 Markdown 파일 하나가 아니라 디렉터리 전체입니다. references가 빠진 채 복사된 `SKILL.md`는 프론트매터가 문제없이 파싱되더라도 깨진 패키지입니다.

### 인접한 추상화들

| 산출물 | 주된 역할 | 언제 로드/실행되나 | 흉내 내서는 안 되는 것 |
|---|---|---|---|
| 프롬프트 | 모델과의 한 번의 상호작용을 모양 잡기 | 애플리케이션이나 사용자가 포함시킬 때 | 리소스를 가진 버전 관리되는 패키지 |
| 저장소 지침 | 한 코드베이스의 상시 규칙 설명 | 코딩 런타임이 그 스코프에 들어올 때 | 재사용 가능한 작업 워크플로 |
| 에이전트 스킬 | 재사용 가능한 절차 지식 공급 | 명시적 또는 암시적 활성화 | 엄격한 권한 부여 경계 |
| MCP 도구 | 타입이 정의된 원격 기능 노출 | 모델이나 애플리케이션이 호출할 때 | 상세한 운영 절차 |
| 훅 | 이벤트가 발생하면 결정론적 로직 실행 | 선언된 이벤트가 발생할 때 | 확률적 모델 라우팅 |
| 서브에이전트 | 별도 컨텍스트와 상태로 작업 위임 | 오케스트레이터가 생성하거나 호출할 때 | 정적 지침 번들 |
| 플러그인 | 더 큰 런타임 확장 배포 | 호스트가 설치하거나 활성화할 때 | 이식 가능한 스킬 계약 그 자체 |
| 학습된 스킬 라이브러리 | 경험을 통해 발견한 행동 저장 | 정책이 이전 프로그램이나 궤적을 검색할 때 | 표준 기반 `SKILL.md` 패키지 |

릴리스 스킬은 에이전트에게 릴리스를 검사하는 방법을 알려 줍니다. MCP 서버는 릴리스 레지스트리를 노출할 수 있습니다. 훅은 직접 푸시를 금지할 수 있습니다. 서브에이전트는 후보 릴리스를 독립적으로 감사할 수 있습니다. 이 조각들은 서로 다른 책임을 맡기 때문에 조합이 가능합니다.

### '스킬'이라는 단어는 서로 다른 두 개념을 가리킨다

연구 시스템에서는 학습된 프로그램, 성공적인 궤적, 환경별 정책 조각을 '스킬'이라고 부르기도 합니다. 에이전트는 탐색 중에 이런 산출물을 만들고, 작업 유사도로 검색하고, 실행하고, 피드백으로 라이브러리를 다듬을 수 있습니다. 페이즈 14 · 10이 바로 그런 평생 학습 라이브러리를 만듭니다.

이 미니 트랙에서 다루는 에이전트 스킬(Agent Skill)은 다릅니다. 파일시스템 계약, 카탈로그 메타데이터, 점진적 공개(progressive disclosure), 런타임이 중재하는 호출, 호스트가 통제하는 도구를 선언하는 '작성된' 패키지입니다. 에이전트가 생성하거나 개선할 수도 있지만, 이 형식 자체에 학습은 필수가 아닙니다.

| 차원 | 에이전트 스킬 패키지 | 학습된 스킬 라이브러리 |
|---|---|---|
| 기본 단위 | `SKILL.md` 디렉터리 | 프로그램, 정책, 궤적, 메모리 레코드 |
| 생성 | 작성, 생성 또는 큐레이션 | 대개 환경 경험에서 발견 |
| 선택 | 카탈로그 description + 런타임 정책 | 작업 상태에 대한 검색 또는 정책 |
| 실행 | 모델이 지침을 따르고 호스트 도구 호출 | 환경이 저장된 행동이나 코드 산출물을 실행 |
| 이식성 | 패키지 계약이 호환 호스트 간 이동 가능 | 대개 하나의 환경과 행동 공간에 묶임 |
| 평가 | 라우팅, 산출물, 안전성, 호스트 호환성 | 보상, 성공률, 전이, 라이브러리 성장 |

두 개념 모두 재사용 가능한 능력을 패키지로 담습니다. 이름이 같다는 이유만으로 구현상의 주장까지 공유해서는 안 됩니다.

### 이식 가능한 핵심

Agent Skills 규격은 프론트매터에 두 필드를 요구합니다:

```yaml
---
name: release-readiness
description: Inspect a release candidate when the user asks whether a version is ready to publish.
---
```

`name`은 안정적인 식별자입니다. 규격의 이름 규칙을 만족해야 하고 부모 디렉터리 이름과 일치해야 합니다. `description`은 문서이자 라우팅 메타데이터입니다. 스킬이 무엇을 하는지, 언제 적용되는지를 담아야 합니다.

이식 가능한 선택 필드는 다음과 같습니다:

| 필드 | 용도 | 이식성 참고 |
|---|---|---|
| `license` | 패키지의 이용 조건 명시 | 핵심 규격 |
| `compatibility` | 환경 요구 사항 명시 | 핵심 규격 |
| `metadata` | 문자열 값 확장 데이터 전달 | 핵심 규격 |
| `allowed-tools` | 사전 승인된 도구 제안 | 실험적 기능. 호스트 지원 여부는 제각각 |

Markdown 본문에는 운영 지침이 들어갑니다. 워크플로, 의사 결정 지점, 실패 시 동작, 참고 리소스로 가는 직접 경로를 정의해야 합니다.

```markdown
# Release readiness

Use this workflow for a release candidate, not for ordinary development builds.

1. Read `references/release-policy.md`.
2. Run `python3 scripts/inspect_release.py --format json`.
3. Stop if the report contains a blocking failure.
4. Produce the checklist from `assets/release-checklist.md`.
5. Ask for approval before any publish or tag action.
```

### 런타임 확장은 제2의 계층이다

일부 호스트는 추가 프론트매터나 별도 구성 파일을 받아들입니다. 이런 필드는 유용할 수 있지만 자동으로 이식 가능하지는 않습니다.

| 동작 | 호스트 확장 예시 | 이식 가능한 핵심? |
|---|---|:---:|
| 모델 라우팅에서는 숨기고 사용자 직접 호출은 유지 | `disable-model-invocation` | 아니요 |
| 사용자 명령 메뉴에서는 숨기고 모델 라우팅은 허용 | `user-invocable` | 아니요 |
| 명령 메뉴에 인자 도움말 표시 | `argument-hint` | 아니요 |
| 스킬을 위임된 컨텍스트에서 실행 | `context`, `agent` | 아니요 |
| 모델이나 추론 설정 고정 | `model`, `effort` | 아니요 |
| 생명주기 자동화 등록 | `hooks` | 아니요 |
| Codex에서 암시적 호출 비활성화 | `agents/openai.yaml` 정책 | 아니요 |

각 확장은 어댑터로 취급하세요. 확장이 없어도 핵심 워크플로는 유효하게 유지하고, 대체 방법을 문서화하고, 이 확장을 소비하는 호스트에서 테스트하세요. 런타임은 모르는 필드를 무시할 수도, 거부할 수도 있고, 동작을 구현하지 않은 채 그냥 보존할 수도 있습니다.

### 프론트매터는 실행 가능한 메타데이터다

메타데이터는 스킬 본문을 읽기도 전에 시스템 동작을 바꿉니다.

- 형식이 잘못된 `name`은 발견 단계의 실패로 이어질 수 있습니다.
- 모호한 `description`은 엉뚱한 요청을 라우팅할 수 있습니다.
- 사람 전용 플래그 하나가 모델의 카탈로그에서 스킬을 빼버릴 수 있습니다.
- 도구 허용 설정에 따라 호스트가 권한을 묻는지가 달라질 수 있습니다.
- 컨텍스트 설정에 따라 실행이 별도의 에이전트 세션으로 옮겨질 수 있습니다.

프론트매터를 설정 코드처럼 다루세요. 검증하고, 버전을 관리하고, 그 동작을 평가(eval)에 포함시키세요.

### 스킬 생명주기

```figure
skill-runtime-lifecycle
```

화살표 하나하나가 저마다의 실패 모드를 가진 경계입니다.

1. **발견(Discovery)**: 설정된 위치에서 가능한 패키지를 찾습니다.
2. **검증(Validation)**: 카탈로그 등록 전에 형식이 잘못되었거나 위험한 패키지를 거부합니다.
3. **카탈로그 등록(Cataloging)**: 패키지 전체가 아니라 요약된 `name`과 `description`만 노출합니다.
4. **선택(Selection)**: 이 스킬이 관련 있는지 판단합니다.
5. **활성화(Activation)**: 본문을 모델이 볼 수 있는 컨텍스트에 로드합니다.
6. **공개(Disclosure)**: 분기가 필요로 할 때만 references나 assets를 읽습니다.
7. **실행(Execution)**: 호스트의 권한·격리 규칙 안에서 호스트 도구를 사용합니다.
8. **검증(Verification)**: 산출물을 모델의 주장과 무관하게 독립적으로 확인합니다.

이 단계들을 하나로 뭉개면 잘못된 멘탈 모델이 생깁니다. 발견된 스킬이 곧 활성화된 스킬은 아닙니다. 활성화된 스킬이 자신이 묘사하는 모든 일을 할 권한이 있는 것도 아닙니다. 허용된 도구 호출이 결과가 옳다는 증거도 아닙니다.

### 스킬과 도구는 서로 직교한다

MCP는 "이 애플리케이션이 호출할 수 있는 기능은 무엇이고, 그 스키마는 무엇인가?"라는 질문에 답합니다. 스킬은 "에이전트는 이런 부류의 작업에 어떻게 접근해야 하는가?"라는 질문에 답합니다.

```figure
skill-tool-orthogonality
```

스킬이 도구 이름을 언급할 수는 있지만, 실제 기능 레지스트리는 호스트가 소유합니다. 도구가 없다면 스킬은 대체 방법을 밝히거나 명확하게 실패해야 합니다. 기능의 이름을 부른다고 그 기능이 생겨나는 것처럼 보여서는 안 됩니다.

### 스킬과 저장소 지침은 스코프가 다르다

저장소 지침은 이미 들어와 있는 환경을 묘사합니다. 명령어, 관례, 생성된 파일, 경계 같은 것들이죠. 스킬은 여러 저장소에 걸쳐 일어날 수 있는 작업을 위한 재사용 가능한 절차를 제공합니다.

둘 다 적용될 때는 현재의 사용자 요청과 저장소 규칙이 스킬을 구속합니다. 일반적인 리팩토링 스킬이 생성 파일 편집을 금지하는 저장소 규칙을 무시해서는 안 됩니다.

### 스킬은 서로 임포트하지 않는다

한 스킬이 에이전트에게 다른 스킬의 호출을 지시할 수는 있지만, 이는 언어 수준의 임포트가 아닙니다. 두 번째 스킬도 런타임의 발견, 자격 확인, 활성화, 권한, 컨텍스트 처리를 그대로 거칩니다.

스킬 간 의존 관계는 관찰 가능한 워크플로 간선으로 적으세요:

```markdown
After producing the candidate changelog, invoke the `release-risk-review` skill.
Pass the candidate path and require a blocking or non-blocking verdict.
If that skill is unavailable, stop and report the missing dependency.
```

이렇게 하면 의존 관계를 테스트할 수 있고, 호스트에 정책을 강제할 기회도 줍니다.

## 만들어 보기

`code/main.py`는 작은 규격 중심 검증기와 산출물 선택기를 구현합니다. 표준 라이브러리만 사용해 모든 규칙이 눈에 보입니다.

검증기가 제공하는 것:

- 본문에서 메타데이터를 분리하는 `parse_frontmatter(text)`
- 필수 필드, 이름 규칙, 알 수 없는 확장, 본문 존재, 이식 가능한 길이 제한을 검사하는 `validate_skill_text(text, directory_name, allowed_runtime_extensions=())`
- 불투명한 불리언 하나 대신 구조화된 증거를 돌려주는 `ValidationIssue`와 `SkillReport`
- 안전하게 해석할 수 없는 입력을 위한 `FrontmatterSyntaxError`

선택기는 `TaskShape`와 `select_primitives(task)`를 제공합니다. 작업의 요구를 평범한 코드, 저장소 지침, 스킬, 훅, 서브에이전트, MCP 도구 중 하나에 대응시킵니다.

실습을 실행해 보세요:

```bash
cd "$(git rev-parse --show-toplevel)"
cd phases/13-tools-and-protocols/22-skills-and-agent-sdks
python3 code/main.py
python3 -m unittest discover -s code/tests -v
```

이 명령 블록은 로컬 클론이 필요하고, `git rev-parse --show-toplevel`이 저장소 루트를 찾을 수 있도록 클론 내부 어디선가 시작해야 합니다.

데모는 유효한 이식 가능 스킬 하나, 호스트 확장을 쓰는 스킬 하나, 잘못된 패키지 하나, 그리고 여러 작업 형태 판단을 JSON으로 출력합니다. 이슈 코드를 살펴보세요. 패키지 검증기는 작성자를 대신해 추측하는 대신, 산출물을 고치는 방법을 설명해야 합니다.

### 검증 순서가 중요하다

깊은 내용 규칙 전에 값싸게 확인할 수 있는 구조적 사실부터 검증하세요:

```figure
skill-validation-order
```

이 순서 덕분에 2차 오류가 첫 번째로 깨진 불변 조건을 가리지 않습니다.

## 사용해 보기

스킬을 쓰기 전에 이 의사 결정 카드를 채워 보세요:

| 질문 | 그렇다면 | 유력한 프리미티브 |
|---|---|---|
| 여러 단계에 걸쳐 재사용 가능한 모델 판단이 필요한가? | 절차는 안정적인데 판단은 매번 달라진다 | 스킬 |
| 이벤트가 발생할 때마다 반드시 실행돼야 하는가? | 한 번이라도 빠지면 안 된다 | 훅 또는 애플리케이션 코드 |
| 모델에 타입이 정의된 입력을 갖는 외부 기능이 필요한가? | 그 연산은 모델 컨텍스트 밖에 있다 | 도구 또는 MCP 서버 |
| 작업에 격리된 컨텍스트, 상태, 소유권이 필요한가? | 별도 작업자가 한정된 결과를 돌려준다 | 서브에이전트 |
| 이 지침이 특정 저장소에만 해당되는가? | 로컬 명령어와 제약을 묘사한다 | 저장소 지침 |
| 상호작용 한 번이면 충분한가? | 패키지 생명주기가 필요 없다 | 프롬프트 |

실제 프로덕션(운영 환경) 워크플로는 여러 행을 조합하는 경우가 많습니다. 이 카드는 하나의 산출물이 모든 성질을 다 제공하는 척하는 것을 막아 줍니다.

## 출시하기

이 레슨은 `outputs/` 아래에 `skill-contract-reviewer` 번들을 만듭니다. 구성은 다음과 같습니다:

- 제안된 스킬 패키지를 리뷰하는 이식 가능한 `SKILL.md`
- 이식 가능한 계약과 프리미티브 선택을 위한 참고 체크리스트
- 결정론적 검증 스크립트
- 프롬프트, 스킬, 도구, 훅, 평범한 코드, 서브에이전트를 다루는 작업 형태 픽스처(fixture)

진입 파일만 말고 번들 전체를 설치하세요:

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/install_skills.py /tmp/aiefs-skills --phase 13 --type skill
```

코스 설치 프로그램은 복사된 각 페이즈 13 스킬을 보고하고 `/tmp/aiefs-skills/manifest.json`을 기록합니다. 이 깨끗한 설치 위치는 패키지 형태를 확인하고, 위의 첫 성공 루프는 실제 호스트에서의 발견과 호출을 확인합니다.

이어지는 레슨들은 생명주기 각 단계를 더 깊게 파봅니다. 레슨 24는 발견과 점진적 공개를, 레슨 25는 호출 정책과 라우팅을, 레슨 26은 권한과 샌드박스를 분리해 다루고, 레슨 27은 패키지 전체를 평가된 릴리스 산출물로 만듭니다.

## 연습 문제

1. 여러분 팀의 워크플로 다섯 개를 `TaskShape`로 분류해 보세요. 프리미티브를 둘 이상 고른 경우마다 근거를 설명하세요.
2. 500자 `compatibility` 값은 통과하고 501자 값은 규격 오류로 실패함을 증명하는 경계 테스트를 추가하세요.
3. 허용 목록에 런타임 확장 하나를 추가하세요. 같은 파일이 여전히 '이식 가능 전용' 스킬과 구별됨을 증명하는 테스트를 작성하세요.
4. 400줄짜리 프롬프트를 `SKILL.md`, 참고 문서 하나, 스크립트 계약 하나, 출력 템플릿 하나로 나눠 보세요. 모든 파일이 한 종류의 정보만 담당하게 유지하세요.
5. 사용할 수 없는 MCP 도구를 참조하는 스킬을 위한 실패 응답을 설계하세요. 더 넓은 권한을 가진 도구로 조용히 대체하면 안 됩니다.
6. 기존 스킬 하나를 리뷰하면서 모든 문장을 라우팅, 절차, 정책, 참조 포인터, 출력 계약 중 하나로 분류하세요. 어울리지 않는 문장은 옮기세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|---|---|---|
| 에이전트 스킬 | "저장해 둔 프롬프트" | 절차 지침과 선택적 리소스를 담은, 발견 가능한 디렉터리 |
| 이식 가능한 핵심 | "모든 런타임이 공유하는 필드" | Agent Skills 규격이 정의한 계약 |
| 런타임 확장 | "추가 프론트매터" | 동작하려면 호환 어댑터가 필요한 호스트 전용 구성 |
| 활성화 | "스킬이 실행됐다" | 스킬 본문이 모델이 보이는 컨텍스트에 들어간 것. 실행은 그 뒤에 일어날 수도 있음 |
| 스킬 의존성 | "다른 스킬 임포트" | 가용성·정책 검사를 거치는, 런타임이 중재하는 호출 간선 |
| 도구 계약 | "함수 스키마" | 기능의 입력, 출력, 권한, 부수 효과, 오류, 증거 |

## 더 읽을거리

- [Agent Skills 규격](https://agentskills.io/specification): 이식 가능한 디렉터리와 프론트매터 계약.
- [Agent Skills 베스트 프랙티스](https://agentskills.io/skill-creation/best-practices): 스코프, 지침, 리소스 구성.
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills): 현재 Codex의 발견과 호출 동작.
- [Claude Code skills](https://code.claude.com/docs/en/skills): 한 런타임의 호출, 인자, 도구, 위임 컨텍스트 확장.
