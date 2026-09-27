> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [GETTING_STARTED.md](GETTING_STARTED.md)

# GitHub에서 MCPA 자격증 배우기

저장소와 웹사이트는 대등한 학습 표면입니다. 웹사이트에는 인터랙티브 그림과
브라우저 진행 상황이 더해집니다. GitHub는 여러분의 AI 코딩 하네스에게 단계별로
가르치는 데 필요한 레슨 소스, 시나리오 코드, 테스트, 산출물, 퀴즈, 진단, 루트
순서를 쥐여 줍니다.

## AI 튜터로 시작하기

튜터가 모든 랩과 테스트를 실행할 수 있도록 저장소를 복제하세요:

```bash
git clone https://github.com/rohitg00/ai-engineering-from-scratch.git
cd ai-engineering-from-scratch
```

Claude Code는 저장소 튜터를 자동으로 발견합니다. 다음으로 시작하세요:

```text
/mcpa-certification
```

`SKILL.md`를 읽는 Codex, Cursor 또는 다른 로컬 에이전트는 휴대 가능한 과정
스킬을 설치하세요:

```bash
npx skills add rohitg00/ai-engineering-from-scratch
```

그런 다음 `/mcpa-certification`을 호출합니다. ChatGPT처럼 로컬 스킬 설치나
슬래시 커맨드를 지원하지 않는 하네스는 이 저장소를 첨부하거나 열고 다음
프롬프트를 붙여 넣으세요:

```text
skills/mcpa-certification/SKILL.md를 끝까지 읽으세요. 그 내용으로 MCPA 자격증
준비를 시켜 주고, 나의 학습 계획을 세워 주고, 이 저장소의 실제 랩, 산출물,
퀴즈, 보충 학습을 활용해 한 번에 한 레슨씩 가르쳐 주세요.
```

튜터는 MCP 경험, 진행 속도, 지금 진단을 받을지 여부를 물어봅니다.
`MCPA-CERTIFICATION.md` 파일을 만든 뒤, 이후 세션에서는 그 파일부터 이어서
진행합니다. 각 레슨에서 여러분은 다음을 해야 합니다:

1. 결정을 자기 말로 설명하기;
2. 레슨 시나리오를 예측하고 조작하기;
3. 저장소에 들어 있는 랩과 테스트 실행하기;
4. 자신만의 산출물을 만들거나 방어하기;
5. 레슨 퀴즈 통과하기;
6. 진도를 나가기 전에 약한 시험 도메인 보충하기.

여러분의 작업물은 `learning-artifacts/mcpa/` 아래에 둡니다. 각 레슨의 완성된
참조 산출물과는 별도입니다.

## 트랙

MCPA는 하나의 트랙이지, 선택지 메뉴가 아닙니다.

| 항목 | 값 |
|-------|-------|
| 시험 코드 | MCPA |
| 자격증명 | Model Context Protocol Associate |
| 시행 기관 | Agentic AI Foundation (Linux Foundation Training and Certification 통해) |
| 수준 | 초급, 벤더 중립 |
| 프로토콜 리비전 | 2026-07-28, 무상태 코어. 출처와 함께 [프로토콜 브리프](research/mcp-2026-07-28-brief.md)에 요약됨 |
| 루트 | [34개 레슨 루트](tracks/mcpa-f.json) |
| 진단 | `assessments/mcpa-f/diagnostic.json`의 30문항 진단 |
| 풀 모의고사 | 60문항 독창 모의고사 3개 — `assessments/mcpa-f/`의 `mock-01.json`, `mock-02.json`, `mock-03.json` |

트랙 JSON은 루트 순서, 도메인 가중치, 그리고 선언된 평가 경로의 기계 판독
가능한 원본입니다. 튜터는 일반 학습 계획에서 추측하는 대신 이 파일을 읽습니다.

## MCPA는 가이드형 노코드 모드로 배우기

MCPA는 소프트웨어 개발 경험을 요구하지 않습니다. 지식 시험이기 때문입니다.
그럼에도 레슨에 Python이 실리는 이유는, 결정론적 모의고사와 검증기가 프로토콜
동작, 스키마, 라이프사이클, 동의(consent) 루브릭을 검사 가능하게 만들어 주기
때문입니다. 튜터가 그 코드를 대신 실행해 줄 수 있으니 여러분이 직접 쓸 필요는
없습니다.

튜터를 설치하거나 연 뒤 다음을 붙여 넣으세요:

```text
MCPA를 가이드형 노코드 모드로 시작해 줘. 로컬 모의고사와 검증기를 대신 실행해
주고, 모든 시나리오를 대화형으로 가르쳐 줘, 그리고 내 결정에서 학습자 소유의
각 산출물을 만들도록 도와줘. 실습과 퀴즈를 건너뛰지 말고, Python 작성을
요구하지도 마.
```

그래도 결과를 예측하고, 시나리오를 조작하고, 선택을 방어하고, 실패한 산출물을
고치고, 독창적인 평가를 치러야 합니다. 인터페이스가 바뀔 뿐, 증거 기준은 바뀌지
않습니다.

## 레슨 하나를 직접 배우기

모든 자격증 레슨은 같은 GitHub 구조를 지닙니다:

```text
certifications/mcpa/lessons/NN-lesson/
├── docs/en.md          레슨 전문과 인터랙티브 랩 추론
├── code/main.py        시나리오 실행기, 시뮬레이터, 채점기, 또는 검증기
├── code/tests/         결정론적 검증
├── outputs/            완성된 참조 산출물
└── quiz.json           근거가 있는 여섯 문항과 해설
```

루트에서 다음 레슨 경로를 열고 `docs/en.md`를 읽어 시나리오 결과를 예측한 뒤
실행합니다:

```bash
LESSON=certifications/mcpa/lessons/14-multi-round-trip-requests-and-elicitation
python3 "$LESSON/code/main.py"
python3 -m unittest discover -s "$LESSON/code/tests" -v
```

레슨 14는 멀티 라운드트립 예제입니다: 배포 도구가 `input_required`로 답하고,
일루시테이션(elicitation)을 통해 사람에게 확인을 구하며, 재시도가 새로운 요청
id와 서버의 `requestState`를 그대로 되돌려 받아 왔을 때만 배포합니다. 실행기는
또한 변조된, 만료된, 재생된, 대상이 바뀐 `requestState`가 각각 거부되는 모습도
보여 줍니다. 개념적 주제에 인위적인 프로바이더 코드를 얹지 않습니다. 다른
레슨에는 스키마 검증기, 탐색·캐싱 실행기, 오류 채널과 라이프사이클 모의 객체,
OAuth 흐름 모델, 감사 사슬(audit chain) 검사기, 그리고 전체 캡스톤 교환
검증기가 실려 있습니다.

`outputs/`를 완성된 예제로 활용하세요. `learning-artifacts/mcpa/<lesson-slug>/`
에 여러분만의 버전을 만들고, 지원되는 경우 복사본으로 검증기를 실행하고, 그
증거를 `MCPA-CERTIFICATION.md`에 기록하세요.

## 로컬 검증 스위트 전체 실행하기

저장소 루트에서:

```bash
python3 scripts/audit_certifications.py

find certifications/mcpa/lessons -path '*/code/main.py' -print0 \
  | xargs -0 -n1 python3

find certifications/mcpa/lessons -path '*/code/tests/test_*.py' -print0 \
  | xargs -0 -n1 python3

python3 scripts/check_mcpa_wire.py
```

와이어 검사기는 모든 레슨의 대화 전사(transcript)를 불러와 2026-07-28 형식을
갖추지 못한 메시지를 표시합니다: `_meta`에 프로토콜 버전과 클라이언트 기능이
없는 요청, `resultType`이 없는 결과, `initialize` 같은 구식 메서드를 현재
것처럼 보여 주는 경우, 또는 사양에 정의되지 않은 오류 코드.

모든 MCPA 랩은 오프라인 표준 라이브러리 모의 객체입니다. 네트워크 API를
호출하거나 키가 필요한 곳은 없고, 실전 와이어(live-wire) 모드도 없습니다. 이
스위트는 설계부터 완전히 로컬에서 돌며 자격 증명이 필요 없습니다.

## GitHub에서 평가 치르기

`mcpa-f` 트랙은 진단 하나와 독창적인 풀 모의고사 세 개를 선언합니다. 각
모의고사는 서로 다른 능력에 실립니다: 운영 시나리오, 와이어 수준 메시지, 설계와
보안 트레이드오프. 재응시 때마다 아직 안 본 모의고사를 쓰세요. AI 튜터가 JSON을
읽고 한 번에 한 문항씩 시행할 수 있습니다:

- `single` 문항은 한 글자로 답한다;
- `multiple` 문항은 전체 글자 묶음으로 답한다;
- 부분 점수 없는 완전 일치 채점을 쓴다;
- 제출 전까지 답과 해설을 숨긴다;
- 원점수 백분율과 도메인별 결과를 보고한다;
- 틀린 문항마다 레슨 내부 참조로 따라간다.

연습 백분율은 과정 점수입니다. 공식 MCPA 점수나 자격증, 합격 보장이 아니며,
공식 문항 수와 합격 점수는 공개되지 않으므로 연습 결과로 공식 결과를 예측할 수
없습니다.

## 웹사이트도 함께 쓰기

같은 커리큘럼이 웹사이트
[aiengineeringfromscratch.com/certification?id=mcpa-f](https://aiengineeringfromscratch.com/certification?id=mcpa-f)에도
있습니다. 직접 조작하는 그림, 브라우저 로컬 진행 상황, 타이머, 시각적 평가
보충에 활용하세요. AI 튜터에게 코드 실행, 산출물 검사, 상세한 학습 계획 보관을
맡기려면 GitHub가 여전히 더 나은 표면입니다.

로컬 웹사이트 미리 보기:

```bash
node site/build.js
python3 -m http.server 4173 --bind 127.0.0.1
```

`http://127.0.0.1:4173/site/certification.html?id=mcpa-f`를 여세요.

## 독립성과 출판 경계

이것은 독립적인 커뮤니티 준비 자료입니다. Agentic AI Foundation이나 Linux
Foundation과 제휴하거나, 승인받거나, 후원받거나, 허가받은 바 없습니다. 목표는
공개된 도메인과 하위 역량(sub-competency) 이름, MCP 사양에서 가져왔고, 독창적인
시나리오를 쓰며, 실제 시험 문항을 담고 있지 않고, 자격증을 발급하거나 합격을
보장하지도 않습니다. 등록 전에 현재 공식 페이지와 응시 자격 규칙을 확인하세요.

자격증 콘텐츠는 GitHub와 웹사이트를 통해 공개됩니다. 랩, 평가, 루트 상태,
인터랙티브 메커니즘이 곧 과정이기 때문에, 저장소의 EPUB/PDF 북(book) 워크플로에는
의도적으로 넣지 않았습니다.
