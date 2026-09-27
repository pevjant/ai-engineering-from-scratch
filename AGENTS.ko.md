> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [AGENTS.md](AGENTS.md)

# AGENTS.md

이 저장소에 손을 대는 기여자와 AI 에이전트를 위한 운용 매뉴얼입니다. PR을 열기 전에 꼭 읽어 주세요.

이 저장소는 SaaS 앱이 아니라 커리큘럼입니다. 레슨이 곧 제품입니다. 아래의 모든 규칙은 523개 레슨이 시간이 지나도 일관성을 잃지 않도록 지키기 위한 것입니다.

---

## 철학

523개 레슨. 20개 페이즈. 프레임워크를 단 하나 import하기 전에, 모든 알고리즘을 가장 낮은 수준의 수학부터 직접 만듭니다. 역전파, 토크나이저, 어텐션 메커니즘, 에이전트 루프를 Python, TypeScript, Rust, Julia로 손으로 직접 작성해 보는 것이죠. 그다음 같은 연산을 프로덕션(운영 환경) 라이브러리로도 돌려 봅니다. 그러면 프레임워크가 더 이상 블랙박스가 아니게 됩니다. 이 "Build It(직접 만들기) / Use It(가져다 쓰기)" 구분이 커리큘럼의 척추입니다. 각 레슨은 여러분의 일상 워크플로에 바로 꽂아 쓸 수 있는 재사용 가능한 산출물을 함께 배포합니다.

---

## 저장소 구조

```
phases/
  NN-phase-slug/
    NN-lesson-slug/
      docs/en.md              # 레슨 설명 문서
      code/                   # 구현 + 테스트
      quiz.json               # 문제 6개
      outputs/                # 재사용 가능한 산출물(스킬 / 프롬프트 / 에이전트 / MCP 서버)
README.md                     # 대외적인 얼굴; 레슨 개수 자동 동기화
ROADMAP.md                    # 페이즈/레슨 상태
glossary/terms.md             # 공식 용어 정의
site/
  build.js                    # README + ROADMAP + 글로서리를 읽어 data.js 생성
  data.js                     # 생성된 파일; main 푸시 시 CI가 재생성
certifications/claude/
  program.json                # 프로그램 메타데이터, 소스 정책, 공식 링크
  tracks/*.json               # 시험 블루프린트, 순서가 정해진 루트, 학습 계획
  lessons/NN-slug/            # 공유 인증 레슨 계약
  assessments/<exam-code>/    # 자체 제작 진단 평가와 풀 모의고사
scripts/                      # 자동화 스크립트
.github/workflows/
  curriculum.yml              # 불변식 검사 + 자동 동기화 워크플로
```

---

## 절대 규칙

1. **레슨 디렉터리당 커밋 1개.** 여러 레슨을 한 커밋에 몰아 넣지 않습니다. 레슨 10개짜리 PR은 커밋 10개입니다.
2. **컨벤셔널 커밋 제목**은 72자 이하: `feat(phase-NN/MM): <slug>`. 커밋 본문에는 '무엇을'이 아니라 '왜'를 씁니다.
3. 다이어그램은 **Mermaid 또는 SVG만** 사용합니다. ASCII / 유니코드 박스 그리기는 금지입니다.
4. **모든 펜스 코드 블록에는 언어 태그가 필요합니다.** 상황에 맞게 `text`, `json`, `python`, `typescript`, `rust`, `julia`, `bash`, `console`, `mermaid`, `yaml`을 사용하세요.
5. **자체 구현만 사용합니다.** 문서, 코드 주석, 커밋 메시지에서 외부 커리큘럼 저장소를 인용하지 않습니다. RFC, 공식 스펙, 학술 논문이 원전이라면 그것들은 인용합니다.
6. **의존성 허용 목록**(아래 `Dependencies` 참고)을 따릅니다. 표준 라이브러리 우선(stdlib-first)입니다.
7. **생성된 파일은 절대 커밋하지 않습니다**: `catalog.json`은 gitignore 대상이고, `site/data.js`는 CI가 재생성하며, `package-lock.json`은 추적하지 않습니다.

---

## 의존성(Dependencies)

| 언어       | 허용된 것                                                                  |
|------------|--------------------------------------------------------------------------|
| Python     | `numpy`, `torch`, `h5py`, `zstandard`, `safetensors`, 표준 라이브러리              |
| TypeScript | `hono`, `zod`, `ws`(WebSockets가 필요할 때만), `@hono/node-server`, Node 20+ 표준 라이브러리 |
| Rust       | 표준 라이브러리만 (단일 파일 `rustc --edition 2021`)                          |
| Julia      | `Random`, `Statistics`, `LinearAlgebra`, `Printf` (Julia 표준 라이브러리)      |

검토 결과 금지된 의존성이 필요하다는 결론이 나오면, "교육적 명확성을 위해 표준 라이브러리 우선(stays stdlib-first for educational clarity)"을 이유로 들어 건너뜁니다.

---

## 레슨 계약

### docs/en.md 프론트매터

```markdown
# <제목>

> <한 줄 후크>

**Type:** <Learn | Build | Reference>
**Languages:** <code/의 main.* 파일과 일치하는 언어 목록>
**Prerequisites:** <상위 레슨 목록, 없으면 "None">
**Time:** ~<예상 소요 시간(분)>

## Learning Objectives
- <동사로 시작하는 불릿 4~6개>
```

`**Languages:**` 필드는 `code/` 안에 `main.*` 파일이 있는 언어와 일치해야 합니다.

### quiz.json 스키마

```json
{
  "lesson": "<dir-slug>",
  "title": "<Lesson Title>",
  "questions": [
    {"stage": "pre",   "question": "...", "options": ["a","b","c","d"], "correct": 0, "explanation": ""},
    {"stage": "check", "question": "...", "options": ["a","b","c","d"], "correct": 1, "explanation": ""},
    {"stage": "check", "question": "...", "options": ["a","b","c","d"], "correct": 2, "explanation": ""},
    {"stage": "check", "question": "...", "options": ["a","b","c","d"], "correct": 1, "explanation": ""},
    {"stage": "post",  "question": "...", "options": ["a","b","c","d"], "correct": 3, "explanation": ""},
    {"stage": "post",  "question": "...", "options": ["a","b","c","d"], "correct": 0, "explanation": ""}
  ]
}
```

정확히 문제 6개: pre 1개 + check 3개 + post 2개. `correct`는 0부터 시작하는 인덱스입니다. 사이트 렌더러는 이 모양만 이해합니다 — 옛날 방식의 `q/choices/answer` 스키마를 넣으면 에러 메시지 없이 조용히 깨집니다.

오답 선택지(디스트랙터)는 정답과 길이가 비슷하게 유지하세요. 정답만 유난히 길면, 내용을 모르는 독자도 정답을 눈치챌 수 있습니다. `scripts/check_quiz_bias.py --check`가 이를 검사하고, `scripts/debias_quizzes.py`가 정답 위치를 여러 자리에 고르게 분산시킵니다.

### Claude 인증 계약

`certifications/claude/lessons/` 아래의 인증 레슨은 페이즈 레슨과 동일한 문서화, 퀴즈, 다이어그램, 의존성, 레슨당 커밋 1개 규칙을 따릅니다. 모든 인증 레슨은 실행 가능한 메인 파일과 최소 5개의 결정론적(deterministic) 테스트가 필요합니다. 트랙은 안정적인 레슨 경로를 참조하므로, 하나의 레슨이 중복 없이 여러 자격 과정에 재사용될 수 있습니다. 개념 중심 레슨도 실습이 필요합니다. 인위적인 프로바이더 API 코드 대신 시나리오 러너, 정책 스코어러, 산출물 검증기, 승인 시뮬레이터, 위협 모델 검사기, 증거 채점기 등을 사용하세요. 트랙은 기존 `phases/` 레슨을 선택 사항인 심화 학습 자료로 참조할 수도 있습니다.

완전 동등(full-parity) 인증 레슨은 가장 탄탄한 페이즈 레슨들과 같은 설명(explain) → 조작(manipulate) → 구축(build) → 출시(ship) → 검증(verify) 루프를 사용합니다. 모든 인증 레슨은 정확히 `Interactive Lab`, `Practice Lab`, `Shipped Artifact`, `Verify It`, `Capstone Connection` 섹션을 포함해야 하고, 등록된 `figure` 메커니즘을 심어 넣어야 하며, `outputs/` 아래에 최소 1개의 파일을 배포해야 하고, 테스트와 함께 실행 가능한 시나리오·시뮬레이터·스코어러·산출물 검증기 중 하나를 제공해야 합니다. 개념 레슨의 코드도 그 레슨의 판단 내용을 실제로 다뤄 봐야 합니다. 실행 가능한 표면을 채우려고 가짜 API 연동을 억지로 추가하지 마세요. 거버넌스 레슨은 모의 사고, 정책 스코어러, 위협 모델 검사, ADR 검증, 승인 워크플로, 증거 번들 채점기를 활용할 수 있습니다.

`program.json`은 독립 과정 고지 문구, 검증 날짜, 공식 링크를 관리합니다. `prerequisites.json`은 기계가 읽을 수 있는 인증 레슨 의존성 그래프를 관리합니다. 모든 필수 트랙 루트는 어떤 레슨이 내부 선수 레슨을 사용한다면, 그 선수 레슨을 반드시 해당 레슨보다 앞에 포함해야 합니다. `tracks/`의 각 파일은 하나의 공개 시험 블루프린트, 정확한 도메인 가중치, 순서가 정해진 레슨 루트, 평가 선언, 학습 계획을 관리합니다.
시험 사실은 반드시 최신 공식 가이드에서 가져와야 합니다. 제품과 모델 정보는 날짜를 명시하고 최신 공식 문서와 대조해 확인해야 합니다.

진단 평가(diagnostic)와 모의고사(mock)는 다중 응답 문제를 지원하기 때문에 별도의 평가 스키마를 사용합니다:

```json
{
  "id": "claude-ccar-f-diagnostic",
  "version": 1,
  "track": "claude-ccar-f",
  "kind": "diagnostic",
  "title": "Architect Foundations Diagnostic",
  "timeLimitMinutes": 30,
  "questions": [
    {
      "id": "ccar-f-agent-001",
      "domain": "agentic-architecture-orchestration",
      "objective": "choose-an-orchestration-pattern",
      "type": "single",
      "prompt": "A self-contained original scenario...",
      "options": ["a", "b", "c", "d"],
      "correct": [1],
      "explanation": "Why the decision fits and the alternatives do not.",
      "references": ["certifications/claude/lessons/16-multi-agent-orchestration-and-delegation"]
    }
  ]
}
```

`correct`는 항상 배열입니다. `single` 문제는 인덱스를 정확히 하나만 가지고, `multiple` 문제는 두 개 이상 가집니다. 문제는 반드시 자체 제작이어야 하고, 공개된 평가 목표(objective)에 대응해야 하며, 실질적인 설명을 포함해야 하고, 기밀 시험 내용을 재현하거나 재구성하려 시도해서는 안 됩니다. 연습 점수 백분율은 원점수이지 Anthropic의 환산 점수가 아니며, 이 커리큘럼은 합격을 절대 보장하지 않습니다.
공개 인증 페이지와 레슨 컨텍스트에는 또한 이것이 Anthropic과 제휴하거나, 승인받거나, 후원받거나, 위임받지 않은 독립 커뮤니티 커리큘럼임을 밝혀야 합니다.

### AI 네이티브 인증 학습자 모드

사용자가 Claude 인증 과정을 선택, 시작, 재개, 학습, 연습, 평가해 달라고 요청하면, 가르치기 전에 `skills/claude-certification/SKILL.md`를 읽고 따르세요. 이 규칙은 `AGENTS.md`를 읽는 Codex와 다른 모든 하네스에도 적용됩니다. Claude Code는 `.claude/skills/` 아래에서 대응하는 래퍼도 찾아냅니다.

이 저장소를 학습자 모드의 대화형 튜터로 다루세요. 선택한 트랙 매니페스트를 읽고, 루트 레슨을 한 번에 하나씩 가르치고, 해당 레슨의 실제 시나리오와 테스트를 실행하고, `learning-artifacts/` 아래에 학습자 소유 산출물을 요구하고, 저장된 퀴즈나 평가를 채점하고, 진행 상황을 `CLAUDE-CERTIFICATION.md`에 보존하세요. 저장소에 커밋된 참고용 산출물을 학습자 과제로 수정하지 마세요. 인증 커리큘럼은 GitHub과 웹사이트를 통해 제공되며, 책 생성 파이프라인에서는 일부러 제외되어 있습니다.
영어로만 제공되며, 기계 번역 파이프라인에서도 의도적으로 제외되어 있습니다.

### code/

- 해당 언어의 대표 명령으로 끝까지 실행되고 종료 코드 0으로 끝납니다.
- 스스로 종료하는 데모여야 합니다. 무한 stdin 루프 금지, API 키가 없을 때 멈춰 버리는 것도 금지입니다.
- 레슨의 `docs/en.md` 경로와 참고한 스펙이나 RFC 출처를 밝히는 4~6줄 헤더 주석을 넣습니다.

### code/tests/

- 단위 테스트 5개 이상이 최소 기준입니다.
- 해당 언어의 표준 라이브러리 러너로 실행합니다(`python3 -m unittest discover`, `npx tsx --test`, Rust/Julia는 인라인).

---

## PR별 검증

푸시하기 전에 로컬에서 실행하세요:

```bash
python3 scripts/audit_lessons.py
python3 scripts/audit_certifications.py
python3 scripts/check_readme_counts.py        # 권고 사항 — CI가 머지 시 수정함

# 수정한 각 레슨에 대해:
cd phases/NN-phase/MM-lesson/code
python3 main.py && python3 -m unittest discover tests -v   # 또는 해당 언어의 동등한 명령
```

CI 게이트(`.github/workflows/curriculum.yml`):

| 작업                             | 트리거        | 동작                                                   |
|----------------------------------|--------------|-------------------------------------------------------|
| `audit`                          | push + PR    | `audit_lessons.py` 실행. 차단(merge 불가)함.                    |
| `readme-counts-sync` (main 전용) | main 푸시    | 카탈로그 재구축 + README 개수 자동 수정.                        |
| `site-rebuild` (main 전용)       | main 푸시    | `node site/build.js` 재실행, `site/data.js` 커밋.              |
| `readme-counts-drift`            | PR           | 권고만 표시 — main은 머지 시 자가 치유됨.                       |

---

## 자동화 계약

**CI가 자동으로 처리합니다 — PR에서 건드리지 마세요:**

| 대상                 | 봇                              | 시점                 |
|----------------------|--------------------------------|---------------------|
| `catalog.json`       | 필요할 때 재생성(gitignore 대상) | 모든 CI 작업        |
| `README.md` 개수     | `readme-counts-sync`           | main 푸시 시        |
| `site/data.js`       | `site-rebuild`                 | main 푸시 시        |

**직접 처리할 것:**

| 대상                          | 시점                                                             |
|-------------------------------|------------------------------------------------------------------|
| `README.md` 레슨 링크 행      | 새 레슨을 추가할 때 — `[Title](phases/NN-phase/MM-lesson/)` 링크 추가 |
| `ROADMAP.md` 상태             | 레슨을 완료 또는 진행 중(WIP)으로 표시할 때                        |
| `glossary/terms.md`           | 둘 이상의 레슨에서 쓰이는 용어를 새로 소개할 때                     |

**자주 있는 버그**: 머지 후 `grep -c 'tree/main/phases/NN-' site/data.js` 결과가 0이면, 페이즈 NN의 README 행이 일반 텍스트라서 `[Title](phases/NN-...)` 마크다운 링크가 빠져 있다는 뜻입니다. `site/build.js`는 그 링크에서 URL을 만들어 냅니다.

---

## 충돌 해결

```bash
git fetch origin main
git merge --no-edit origin/main

# 카탈로그 충돌(옛날 브랜치만 — 이제 catalog.json은 gitignore 대상):
git rm catalog.json
git commit --no-edit

# README 개수 충돌:
git checkout --theirs README.md
python3 scripts/build_catalog.py
python3 scripts/check_readme_counts.py --fix
git add README.md && git commit --no-edit

# site/data.js 충돌:
git checkout --theirs site/data.js
node site/build.js
git add site/data.js && git commit --no-edit

git push origin <your-branch>
```

리뷰 코멘트가 달려 있는 브랜치에는 `git push --force`를 쓰지 마세요. 강제 푸시하면 코멘트들이 브랜치에서 떨어져 나갑니다.

---

## 새 레슨 온보딩

```bash
mkdir -p phases/NN-phase-slug/MM-new-lesson/{docs,code/tests,outputs}

# 1. 위의 프론트매터 형식으로 docs/en.md를 작성합니다.
# 2. 4~6줄 헤더 주석과 함께 code/main.<lang>을 작성합니다.
# 3. 테스트 5개 이상으로 code/tests/test_main.*을 작성합니다.
# 4. 위의 스키마로 quiz.json을 작성합니다.
# 5. (선택) 레슨이 스킬을 배포한다면 outputs/skill-<slug>.md를 추가합니다.

# 6. README.md에 추가합니다:
#    | MM | [Lesson Title](phases/NN-phase-slug/MM-new-lesson/) | Type | Lang |

# 7. ROADMAP.md 상태 행을 갱신합니다.

# 8. 로컬에서 검증합니다.

# 9. 원자적(atomic) 커밋:
git add phases/NN-phase-slug/MM-new-lesson README.md ROADMAP.md
git commit -m "feat(phase-NN/MM): add <slug>"
git push -u origin <your-branch>
gh pr create --title "feat(phase-NN/MM): add <slug>" --body "<5-line summary>"
```

`site/data.js`는 머지 시점에 재생성됩니다 — CI에 맡겨 두세요.

---

마지막 검토: 2026-05-27.
