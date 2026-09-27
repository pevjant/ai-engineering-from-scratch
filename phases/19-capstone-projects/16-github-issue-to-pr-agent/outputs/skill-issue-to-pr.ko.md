---
name: issue-to-pr
description: 클라우드 샌드박스에서 실행되어 빌드 환경을 재현하고, 테스트를 검증하고, 저장소별 엄격한 예산 안에서 검토 준비가 된 PR을 열어 주는 비동기 GitHub 이슈→PR 에이전트를 만듭니다.
version: 1.0.0
phase: 19
lesson: 16
tags: [capstone, async-agent, github, fargate, daytona, swe-bench, budget, safety]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-issue-to-pr.md](skill-issue-to-pr.md)

`@agent fix this` 레이블이 붙은 이슈가 있는 GitHub 저장소가 주어지면, 각 레이블 이슈를 자격 증명 범위가 좁고 비용이 한정된 검토 준비 완료된 PR로 바꿔 주는 자체 호스팅 클라우드 에이전트를 출시합니다.

빌드 계획:

1. 세밀한 권한의 토큰을 가진 GitHub App: issues rw, PRs write, contents rw, workflows read. 강제 푸시 금지. main의 브랜치 보호가 직접 쓰기를 막습니다.
2. 웹훅 수신기(Lambda 또는 Fly.io)가 레이블 / PR 코멘트 이벤트를 걸러서 SQS에 적재합니다.
3. 디스패처가 저장소·일자별 금액 및 PR 수 상한을 강제합니다; 허용된 작업마다 ECS Fargate 작업을 띄웁니다.
4. 환경 추론: 저장소 내용에서 언어 + 패키지 매니저 + 런타임을 감지합니다. Dockerfile이 없으면 그 자리에서 생성합니다.
5. 작업당 Daytona 또는 E2B 샌드박스. 저장소를 새로운 `git worktree` + 에이전트 브랜치로 클론합니다.
6. 에이전트 루프(Claude Opus 4.7 또는 GPT-5.4-Codex 위의 mini-swe-agent 또는 SWE-agent v2). 도구: ripgrep, tree-sitter repo-map, read_file, edit_file, run_tests, git. 상한: 20달러, 30턴, 30분.
7. 검증: 샌드박스 안에서 전체 CI 실행; jacoco / coverage.py로 커버리지 변화량 측정; 변화량 < -2%면 `needs-review` 레이블; CI가 빨간색이면 중단.
8. GitHub API로 근거 설명, diff 요약, 트레이스 URL, 비용, 턴 수를 넣어 PR을 엽니다.
9. 관측 가능성(옵저버빌리티): PR별 Langfuse 트레이스; 로그에서 시크릿 제거; 저장소별 예산 대시보드.
10. 시드한 내부 이슈 30개로 평가(eval); 세 이슈 공유 부분집합에서 Cursor Background Agents 및 AWS Remote SWE Agents와 비교.

평가 루브릭:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | 30개 이슈에서의 통과율 | 엔드투엔드 성공(CI 초록 + 커버리지 OK) |
| 20 | PR 품질 | diff 크기, 커버리지 변화량, 스타일 일관성 |
| 20 | 해결된 이슈 하나당 비용과 지연 시간 | PR당 달러와 실제 경과 시간 |
| 20 | 안전성 | 범위가 한정된 토큰, 저장소별 예산, 강제 푸시 금지, 자격 증명 위생 |
| 15 | 운영자 UX | 근거 설명 코멘트, 재시도 수단, @멘션 후속 조치 |

하드 리젝트(절대 탈락):

- 강제 푸시가 가능한 에이전트는 무조건 탈락입니다.
- 예산 검사를 건너뛰는 디스패처. 폭주 루프가 대표적인 실패입니다.
- 샌드박스 안에서 전체 CI가 통과하기도 전에 열어 버린 PR.
- 마스킹되지 않은 토큰이나 개인정보(PII)가 남아 있는 트레이스 아카이브.

거부 규칙:

- main에 브랜치 보호가 없으면 설치를 거부합니다.
- 저장소별 일일 예산(금액과 PR 수)이 없으면 실행을 거부합니다.
- 실패한 실행을 자동으로 재시도하지 않습니다. 모든 재시도에는 사람이 레이블을 다시 붙여야 합니다.

산출물: GitHub App, 웹훅 수신기, 디스패처 + 예산 장부, Fargate 작업 정의, 샌드박스 수명주기 관리자, mini-swe-agent 루프, 30이슈 평가 실행 결과, Cursor Background Agents 및 AWS Remote SWE Agents와의 나란히 비교한 자료, 그리고 상위 세 가지 빌드 추론 실패와 각각을 줄인 Dockerfile 합성 변경점을 정리한 보고서를 담은 저장소.
