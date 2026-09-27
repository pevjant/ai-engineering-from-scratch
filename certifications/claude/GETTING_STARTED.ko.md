> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [GETTING_STARTED.md](GETTING_STARTED.md)

# GitHub에서 Claude 인증 배우기

저장소와 웹사이트는 대등한 학습 공간입니다. 웹사이트는 인터랙티브 그림과 브라우저 진행 상황 저장을 더해 주고, GitHub는 당신의 AI 코딩 하네스(에이전트 실행 환경)에게 레슨 원본, 시나리오 코드, 테스트, 산출물, 퀴즈, 진단 테스트, 학습 순서를 제공해서 한 단계씩 가르칠 수 있게 해 줍니다.

## AI 튜터로 시작하기

튜터가 모든 랩과 테스트를 실행할 수 있도록 저장소를 클론하세요:

```bash
git clone https://github.com/rohitg00/ai-engineering-from-scratch.git
cd ai-engineering-from-scratch
```

Claude Code는 저장소 튜터를 자동으로 찾아냅니다. 다음으로 시작하세요:

```text
/claude-certification
```

`SKILL.md`를 읽는 Codex, Cursor 또는 다른 로컬 에이전트라면, 이동식(course portable) 코스 스킬을 설치하세요:

```bash
npx skills add rohitg00/ai-engineering-from-scratch
```

그다음 `/claude-certification`을 실행하세요. ChatGPT처럼 로컬 스킬 설치나 슬래시 명령을 지원하지 않는 하네스라면, 이 저장소를 첨부하거나 열고 아래 프롬프트를 붙여 넣으세요:

```text
Read skills/claude-certification/SKILL.md completely. Use it to choose my
Claude certification track, create my learning plan, and teach me one lesson
at a time with the real labs, artifacts, quizzes, and remediation in this repo.
```

튜터는 당신의 목표, 경험, 학습 속도, 트랙 진단 테스트를 원하는지 물어봅니다. 그리고 `CLAUDE-CERTIFICATION.md` 파일을 작성한 뒤, 이후 세션에서는 이 파일에서 이어서 학습을 재개합니다. 각 레슨에서 당신이 해야 할 일은 다음과 같습니다:

1. 판단(결정)을 자기 말로 설명하기;
2. 레슨 시나리오의 결과를 예측하고 직접 조작해 보기;
3. 저장소에 포함된 랩과 테스트 실행하기;
4. 자신만의 산출물을 만들거나 변호(방어)하기;
5. 레슨 퀴즈 통과하기;
6. 약한 시험 도메인(영역)을 보완한 뒤에 다음으로 넘어가기.

당신이 만든 결과물은 `learning-artifacts/claude/` 아래에 두어야 하며, 각 레슨에 완성본으로 들어 있는 참고용 산출물과는 분리됩니다.

## 학습 경로(루트) 고르기

| 트랙 | 잘 맞는 사람 | 루트 | 진단 테스트 | 전체 모의고사 |
|-------|----------|-------|------------|-----------|
| CCAO-F | 지식 노동, 분석, 검증, 책임감 있는 Claude 활용 | [9개 레슨 루트](tracks/ccao-f.json) | [16문항](assessments/ccao-f/diagnostic.json) | [60문항](assessments/ccao-f/mock-01.json) |
| CCDV-F | Claude 애플리케이션을 만들고 보안을 챙기는 엔지니어 | [15개 레슨 루트](tracks/ccdv-f.json) | [16문항](assessments/ccdv-f/diagnostic.json) | [53문항](assessments/ccdv-f/mock-01.json) |
| CCAR-F | Claude Code, Agent SDK, API, MCP, 오케스트레이션 선택을 변호해야 하는 빌더 | [21개 레슨 루트](tracks/ccar-f.json) | [15문항](assessments/ccar-f/diagnostic.json) | [60문항](assessments/ccar-f/mock-01.json) |
| CCAR-P | 발굴(디스커버리)부터 운영까지 책임지는 시니어 엔지니어와 아키텍트 | [25개 레슨 루트](tracks/ccar-p.json) | [14문항](assessments/ccar-p/diagnostic.json) | [63문항](assessments/ccar-p/mock-01.json) |

트랙 JSON은 루트 순서, 선수 지식 커버리지, 도메인 가중치, 학습 계획, 평가 경로를 담은 기계가 읽을 수 있는 원본(source)입니다. 튜터는 일반적인 학습 계획을 억지로 끼워 맞추는 게 아니라 이 파일을 읽습니다.

## 어소시에이트(Associate)는 가이드형 노코드 모드로 학습하기

CCAO-F는 소프트웨어 개발 경험을 요구하지 않습니다. 그럼에도 레슨에 Python 코드가 포함되어 있는 이유는, 결정론적 검증기(밸리데이터)가 있어야 정책, 증거, 워크플로, 리뷰 루브릭(채점 기준)을 테스트할 수 있기 때문입니다. 튜터가 그 코드를 대신 실행해 줄 수 있으니, 직접 작성할 필요는 없습니다.

튜터를 설치하거나 연 뒤에 이 내용을 붙여 넣으세요:

```text
Start me on CCAO-F in guided no-code mode. Run the local validators for me,
teach every scenario interactively, and help me create each learner-owned
workflow, policy, evidence, or review artifact from my decisions. Do not skip
the practical work or quizzes, and do not require me to write Python.
```

그래도 결과를 예측하고, 시나리오를 조작하고, 선택을 변호하고, 실패한 산출물을 고치고, 자체 제작 평가를 응시해야 합니다. 인터페이스(조작 방식)만 바뀔 뿐, 증거의 기준은 바뀌지 않습니다.

## 한 레슨씩 직접 학습하기

모든 인증 레슨은 같은 GitHub 구조(계약)를 따릅니다:

```text
certifications/claude/lessons/NN-lesson/
├── docs/en.md          full lesson and interactive-lab reasoning
├── code/main.py        scenario runner, simulator, scorer, or validator
├── code/tests/         deterministic verification
├── outputs/            completed reference artifact
└── quiz.json           six grounded questions with explanations
```

선택한 트랙에서 다음 레슨 경로를 찾아 열어 보세요. `docs/en.md`를 읽고 시나리오 결과를 예측해 본 뒤 실행합니다:

```bash
LESSON=certifications/claude/lessons/27-enterprise-governance-compliance-and-hitl
python3 "$LESSON/code/main.py"
python3 -m unittest discover -s "$LESSON/code/tests" -v
```

레슨 27은 거버넌스(통치 규칙) 예시입니다. 이 레슨의 실행 코드는 정책과 사람 검토 패킷을 검증하며, 개념적 주제에 억지로 프로바이더(공급사) 코드를 얹지 않습니다. 다른 레슨들은 위협 모델, ADR(아키텍처 결정 기록), 승인 흐름, 증거 번들, 도구 루프 시뮬레이터, RAG 보고서, API 라이프사이클 랩, 캡스톤 검증기 등을 포함합니다.

`outputs/`는 완성된 예시로 사용하세요. 당신의 버전은 `learning-artifacts/claude/<exam-code>/<lesson-slug>/`에 만들고, 지원되는 경우 복사본을 검증기로 검사한 뒤, 증거를 `CLAUDE-CERTIFICATION.md`에 기록합니다.

## 전체 로컬 검증 스위트 실행하기

저장소 루트에서:

```bash
python3 scripts/audit_certifications.py

find certifications/claude/lessons -path '*/code/main.py' -print0 \
  | xargs -0 -n1 env -u ANTHROPIC_API_KEY -u ANTHROPIC_MODEL python3

find certifications/claude/lessons -path '*/code/tests/test_*.py' -print0 \
  | xargs -0 -n1 env -u ANTHROPIC_API_KEY -u ANTHROPIC_MODEL python3
```

레슨 30의 실시간 Messages API 테스트는 자격 증명(크리덴셜)을 명시적으로 제공하지 않으면 건너뜁니다. 기본 커리큘럼은 로컬에서 실행되며 자격 증명이 필요 없습니다. 선택적인 실제 네트워크 와이어 확인을 하려면 환경 변수만 사용하고 해당 레슨의 지침을 따르세요. API 키를 소스 코드, 프롬프트, 학습 상태 파일 어디에도 넣지 마세요.

## GitHub에서 평가 응시하기

각 트랙은 진단 테스트 하나와 오리지널 전체 모의고사 하나를 선언합니다. AI 튜터는 JSON을 읽어 한 번에 한 문항씩 시험을 치룰 수 있습니다:

- `single` 문항은 알파벳 하나로 답하기;
- `multiple` 문항은 알파벳 전체 집합으로 답하기;
- 부분 점수 없이 정확 일치(exact-set) 채점 사용;
- 제출 전까지 답과 해설 숨겨 두기;
- 원점수 백분율과 도메인별 결과 보고;
- 틀린 문항마다 내부 레슨 참조로 이동해 보완하기.

연습 백분율은 코스 점수입니다. Anthropic의 환산 점수, 자격증, 합격 보장이 아닙니다.

## 웹사이트도 함께 활용하기

같은 커리큘럼이 [aiengineeringfromscratch.com/certifications.html](https://aiengineeringfromscratch.com/certifications.html)에서도 제공됩니다. 웹사이트는 직접 조작할 수 있는 그림, 브라우저 로컬 진행 상황, 타이머, 시각적 평가 보완에 유용합니다. AI 튜터가 코드를 실행하고 산출물을 검사하고 상세한 학습 계획을 유지하게 하고 싶다면 GitHub이 여전히 더 좋은 선택입니다.

로컬에서 웹사이트를 미리 보려면:

```bash
node site/build.js
python3 -m http.server 4173 --bind 127.0.0.1
```

`http://127.0.0.1:4173/site/certifications.html`을 여세요.

## 독립성과 공개(퍼블리싱) 경계

이것은 독립적인 커뮤니티 학습 자료입니다. Anthropic과 제휴하거나, 승인받거나, 후원받거나, 공식 허가를 받은 것이 아닙니다. 공개된 시험 목표와 오리지널 시나리오를 사용하고, 실제 시험 문제를 담고 있지 않으며, 자격증을 발급하거나 합격을 보장하지 않습니다. 등록 전에 최신 공식 가이드와 응시 자격 규칙을 확인하세요.

인증 콘텐츠는 GitHub과 웹사이트를 통해 공개됩니다. 랩, 평가, 루트 상태, 인터랙티브 메커니즘이 곧 과정의 일부이기 때문에, 저장소의 EPUB/PDF 책 워크플로에는 의도적으로 포함하지 않습니다.
