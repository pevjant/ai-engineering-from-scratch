> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 16 — GitHub 이슈→PR 자율 에이전트

> 이슈에 레이블을 붙이면 PR이 돌아옵니다 — 이것이 2026년 자율 코딩 에이전트의 제품 형태입니다: 클라우드 샌드박스에서 에이전트를 돌리고, 테스트가 통과하는지 검증하고, 근거 설명과 함께 검토 준비가 된 PR을 올립니다. AWS Remote SWE Agents, Cursor Background Agents, OpenAI Codex 클라우드, Google Jules가 모두 이 방식을 출시했습니다. 어려운 부분은 저장소의 빌드 환경을 자동으로 재현하는 것, 자격 증명 누출을 막는 것, 저장소별 예산을 강제하는 것, 그리고 에이전트가 강제 푸시(force-push)를 하지 못하게 만드는 것입니다. 이 캡스톤은 자체 호스팅 버전을 만들고, 비용과 통과율을 호스티드(관리형) 대안들과 비교합니다.

**유형:** 캡스톤
**사용 언어:** Python(에이전트), TypeScript(GitHub App), YAML(Actions)
**선수 지식:** 페이즈 11(LLM 엔지니어링), 페이즈 13(도구), 페이즈 14(에이전트), 페이즈 15(자율성), 페이즈 17(인프라)
**활용하는 페이즈:** P11 · P13 · P14 · P15 · P17
**소요 시간:** 30시간

## 문제

비동기 클라우드 코딩 에이전트는 대화형 코딩 에이전트(캡스톤 01)와는 별개의 제품 카테고리입니다. 사용자 경험(UX)의 전부는 GitHub 레이블 하나입니다. 이슈에 `@agent fix this` 레이블을 붙이면, 워커가 클라우드 샌드박스에서 실행되어 저장소를 클론하고, 테스트를 돌리고, 파일을 고치고, 검증한 뒤, 본문에 에이전트의 근거 설명을 적어 PR을 엽니다. 대화형 루프도, 터미널도 없습니다. AWS Remote SWE Agents, Cursor Background Agents, OpenAI Codex 클라우드, Google Jules, Factory Droids가 모두 이 형태로 수렴하고 있습니다.

엔지니어링 난제는 구체적입니다: 환경 재현(에이전트가 캐시된 개발 이미지 없이 저장소를 처음부터 빌드해야 함), 깨지기 쉬운 테스트(재실행하거나 격리해야 함), 자격 증명 범위 한정(최소한의 세밀한(fine-grained) 권한을 가진 GitHub App), 저장소·일자별 예산 강제, 그리고 강제 푸시 금지 정책입니다. 이 캡스톤은 통과율, 비용, 안전성을 호스티드 대안들과 비교해 측정합니다.

## 개념

트리거는 GitHub 웹훅(이슈 레이블 또는 PR 코멘트)입니다. 디스패처가 작업을 ECS Fargate나 Lambda에 넣습니다. 워커는 저장소에서 추론한 범용 Dockerfile(언어, 프레임워크)과 함께 저장소를 Daytona 또는 E2B 샌드박스로 가져옵니다. 에이전트는 Claude Opus 4.7 또는 GPT-5.4-Codex를 대상으로 mini-swe-agent 또는 SWE-agent v2 루프를 돌립니다. 반복 작업은 이렇습니다: 코드 읽기, 수정안 제안, 패치 적용, 테스트 실행.

검증이 관문 단계입니다. PR이 열리기 전에 샌드박스 안에서 전체 CI가 통과해야 합니다. 커버리지 변화량(delta)을 계산해서, 임계값을 넘게 줄었다면 PR은 열되 `needs-review` 레이블이 붙습니다. 에이전트는 근거 설명을 PR 설명으로 달고, 검토자가 후속 질문을 던질 수 있는 `@agent` 스레드도 만듭니다.

안전은 서로 다른 두 GitHub 영역으로 나눠 관리합니다: App은 `workflows: read` 권한과 좁은 저장소 콘텐츠/PR 권한을 가진 수명이 짧은 설치 토큰(installation token)을 제공합니다; "main에 직접 쓰기 금지"와 "강제 푸시 금지"는 (App 권한이 아니라) 브랜치 보호 규칙이 강제합니다 — App은 우회 목록(bypass list)에 절대 넣지 않습니다. `.github/workflows`에 대한 경로별 읽기 전용 접근은 실제 GitHub App 기능이 아니므로, 파일 수정에 대한 에이전트의 허용 목록(allow-list)이 워커 쪽에서 이를 강제해야 합니다. 저장소·일자별 비용 상한은 디스패처에서 강제합니다(예: 저장소당 하루 최대 5개 PR, PR당 20달러).

## 아키텍처

```
GitHub 이슈에 `@agent fix` 레이블 또는 PR 코멘트
            |
            v
    GitHub App 웹훅 -> AWS Lambda 디스패처
            |
            v
    ECS Fargate 작업 (또는 GitHub Actions 자체 호스팅 러너)
       - 저장소 풀(pull)
       - Dockerfile 추론 (언어, 패키지 매니저)
       - 대상 런타임을 갖춘 Daytona / E2B 샌드박스
       - 클론 -> git worktree -> 에이전트 브랜치
            |
            v
    mini-swe-agent / SWE-agent v2 루프
       Claude Opus 4.7 또는 GPT-5.4-Codex
       도구: ripgrep, tree-sitter, read/edit, run_tests, git
            |
            v
    샌드박스 안에서 CI 통과 검증 + 커버리지 변화량 확인
            |
            v (검증 완료)
    git push + GitHub App으로 PR 열기
       PR 본문 = 근거 설명 + diff 요약 + 트레이스 URL
       레이블: needs-review
            |
            v
    운영자가 검토; @멘션으로 에이전트에게 후속 작업 요청 가능
```

## 스택

- 트리거: 세밀한 권한의 토큰을 가진 GitHub App; 웹훅 수신기는 Lambda 또는 Fly.io
- 워커: ECS Fargate 작업 (또는 GitHub Actions 자체 호스팅 러너)
- 샌드박스: 작업당 Daytona devcontainer 또는 E2B 샌드박스
- 에이전트 루프: Claude Opus 4.7 / GPT-5.4-Codex 위에서 도는 mini-swe-agent 베이스라인 또는 SWE-agent v2
- 검색(retrieval): tree-sitter 저장소 지도(repo-map) + ripgrep
- 검증: 샌드박스 안 전체 CI + 커버리지 변화량 관문
- 관측 가능성(옵저버빌리티): PR 본문에서 링크되는 PR별 Langfuse 트레이스 아카이브
- 예산: 저장소별 일일 금액 상한; 저장소별 하루 최대 PR 수

```figure
cf-issue-to-pr
```

## 만들어 보기

1. **GitHub App.** 세밀한 권한의 설치 토큰: issues read+write, pull_requests write, contents read+write, workflows read. 브랜치 보호(이 기능을 할 수 있는 유일한 수단)가 "main에 직접 푸시 금지"와 "강제 푸시 금지"를 강제합니다; App은 우회 목록에 없습니다. 워커는 제안된 diff에 대한 허용 목록 검사로 "`.github/workflows` 아래 쓰기 금지"를 강제합니다. GitHub App 권한은 경로별로 나뉘지 않기 때문입니다.

2. **웹훅 수신기.** Lambda 함수가 이슈 레이블 / PR 코멘트 웹훅을 받습니다. `@agent fix this` 레이블로 필터링하고 SQS에 적재합니다.

3. **디스패처.** SQS에서 작업을 꺼냅니다. 저장소·일자별 예산을 강제합니다. 저장소 URL, 이슈 본문, 새로 만든 Daytona 샌드박스와 함께 ECS Fargate 작업을 띄웁니다.

4. **환경 추론.** 언어(Python, Node, Go, Rust)와 패키지 매니저(uv, pnpm, go mod, cargo)를 감지합니다. Dockerfile이 없으면 그 자리에서 생성합니다.

5. **에이전트 루프.** Claude Opus 4.7을 쓰는 mini-swe-agent 또는 SWE-agent v2. 도구: ripgrep, tree-sitter repo-map, read_file, edit_file, run_tests, git. 하드 리밋: 20달러 비용, 30분 실제 경과 시간, 30 에이전트 턴.

6. **검증.** 루프가 끝나면 샌드박스 안에서 전체 테스트 스위트를 실행합니다. jacoco / coverage.py로 커버리지 변화량을 계산합니다. CI가 빨간색이면: 중단하고 PR을 열지 않습니다. 커버리지가 2% 이상 떨어지면: `needs-review` 레이블을 달고 PR을 엽니다.

7. **PR 게시.** 에이전트 브랜치를 푸시합니다. GitHub API로 제목, 근거 설명, diff 요약, 트레이스 URL, 비용, 턴 수를 넣어 PR을 엽니다.

8. **자격 증명 위생.** 워커는 수명이 짧은 GitHub App 설치 토큰으로 실행됩니다. 로그는 보관 전에 시크릿(비밀값)을 제거합니다.

9. **평가(eval).** 난이도가 다른 30개의 시드(seed) 내부 이슈. 통과율, PR 품질(diff 크기, 스타일, 커버리지), 비용, 지연 시간을 측정합니다. 같은 이슈들로 Cursor Background Agents 및 AWS Remote SWE Agents와 비교합니다.

## 사용 예

```
# github.com에서
  - 사용자가 이슈 #842에 `@agent fix this` 레이블을 붙임
  - 14분 뒤 PR #1903이 나타남
  - 본문:
    > null comparator 항목 때문에 생긴 widget.dedupe()의 NPE를 수정했습니다.
    > 회귀 테스트 widget_test.go::TestDedupeNullComparator를 추가했습니다.
    > 커버리지 변화량: +0.12%
    > 턴: 7  비용: $1.80  트레이스: langfuse:...
    > 레이블: needs-review
```

## 출시하기

`outputs/skill-issue-to-pr.md`가 산출물입니다. 레이블이 붙은 이슈를, 비용이 한정되고 자격 증명 범위가 좁은 검토 준비 완료된 PR로 바꿔 주는 GitHub App + 비동기 클라우드 워커입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 30개 이슈에서의 통과율 | 엔드투엔드 성공(CI 초록 + 커버리지 OK) |
| 20 | PR 품질 | diff 크기, 커버리지 변화량, 스타일 일관성 |
| 20 | 해결된 이슈 하나당 비용과 지연 시간 | PR당 달러와 실제 경과 시간 |
| 20 | 안전성 | 범위가 한정된 토큰, 저장소별 예산, 강제 푸시 금지, 자격 증명 위생 |
| 15 | 운영자 UX | 근거 설명 코멘트, 재시도 수단, @멘션 후속 조치 |
| **100** | | |

## 연습 문제

1. "깨진 테스트 고치기" 모드를 추가하세요: `@agent stabilize-flake TestX` 레이블이 붙으면 샌드박스 안에서 그 테스트를 50번 실행하고, 이를 안정화하는 최소한의 변경을 제안합니다.

2. 세 개의 공유 이슈에서 Cursor Background Agents와 비용을 비교하세요. 어느 도구가 어디에서 이기는지 보고하세요.

3. 예산 대시보드를 구현하세요: 저장소·일자별 비용, 사용자별 비용. 이상 징후가 생기면 알림을 보냅니다.

4. CI를 돌리지 않고 초안(draft) PR을 여는 "드라이런(dry-run)" 모드를 만드세요. 검토자가 값싸게 계획을 살펴볼 수 있습니다.

5. 보존 정책을 추가하세요: 7일 넘게 병합 없이 방치된 PR 브랜치는 자동으로 삭제합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| GitHub App | "범위가 한정된 봇 신원" | 세밀한 권한 + 수명이 짧은 설치 토큰을 가진 App |
| 비동기 클라우드 에이전트 | "백그라운드 에이전트" | 터미널이 아니라 클라우드 샌드박스에서 도는 비대화형 워커 |
| 환경 추론 | "Dockerfile 합성" | 언어 + 패키지 매니저를 감지하고, 없으면 Dockerfile 생성 |
| 검증 | "샌드박스 안의 CI" | PR을 열기 전에 워커 안에서 전체 테스트 스위트 실행 |
| 커버리지 변화량 | "커버리지 보존" | 베이스 브랜치에서 에이전트 브랜치로의 테스트 커버리지 % 변화 |
| 저장소별 예산 | "일일 상한" | 디스패처에서 강제하는 금액 및 PR 수 상한 |
| 근거 설명(rationale) | "PR 본문 설명" | 무엇을 왜 바꿨는지에 대한 에이전트의 요약; PR 본문에 필수 |

## 더 읽을 거리

- [AWS Remote SWE Agents](https://github.com/aws-samples/remote-swe-agents) — 대표적인 비동기 클라우드 에이전트 레퍼런스
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) — CLI 레퍼런스
- [Cursor Background Agents](https://docs.cursor.com/background-agent) — 상용 대안
- [OpenAI Codex (cloud)](https://openai.com/codex) — 호스티드 경쟁 서비스
- [Google Jules](https://jules.google) — Google의 호스티드 버전
- [Factory Droids](https://www.factory.ai) — 다른 상용 레퍼런스
- [GitHub App 문서](https://docs.github.com/en/apps) — 범위가 한정된 봇 신원
- [Daytona 클라우드 샌드박스](https://daytona.io) — 레퍼런스 샌드박스
