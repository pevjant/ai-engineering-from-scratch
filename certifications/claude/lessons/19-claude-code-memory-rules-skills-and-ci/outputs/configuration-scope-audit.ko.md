> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [configuration-scope-audit.md](configuration-scope-audit.md)

# 구성 범위 감사(Configuration Scope Audit): Python 서비스

## 지침 위계(Hierarchy)

루트 가이드에는 목적, 레이아웃, 표준 명령, 보안 경계, 링크가 들어갑니다. API, 마이그레이션, 문서 작성 지침은 각 경로 범위에 남겨 둡니다.

## 경로 규칙 픽스처

API allow 픽스처인 `src/api/orders.py`에는 계약과 인가 지침이 로드됩니다. deny 픽스처인 `docs/orders.md`에는 로드되지 않습니다. 마이그레이션 픽스처는 append-only(추가 전용) 지침이 `migrations/**` 아래에서만 로드됨을 증명합니다.

## 스킬과 커맨드

migration-review 스킬은 재사용 가능한 증거 수집 절차를 패키지로 묶습니다. 레거시 명시적 ADR 커맨드도 계속 호환되지만, 새로운 다단계 절차는 스킬을 사용해서 관련 파일이 필요할 때 로드되게 합니다. 둘 중 어느 쪽도 인가 권한을 부여하지는 않습니다.

## 스킬 패키지

`migration-review-skill/SKILL.md`는 트리거가 되는 설명과 좁은 `allowed-tools` 허용을 정의합니다. 상세 증거는 `references/review-checklist.md`로 안내하고, 모든 인수는 `scripts/check_scope.py`로 검증합니다. 이 허용은 호출된 턴에 한해 번들된 검사기 하나를 미리 승인하는 것일 뿐, 다른 모든 도구를 제한하거나 deny 규칙을 무시하지 않습니다.

## 서브에이전트 계약

`/agents`는 읽기 전용 도구, `maxTurns: 10`, 그리고 편집이 요청될 때 `isolation: worktree`를 가진 마이그레이션 감사자(auditor)를 등록합니다. 응답에는 `status`, `evidence`, `blockers`, `next_step`이 들어갑니다. 서브에이전트는 턴 상자(한도)에서 멈추고, 성공을 주장하거나 범위를 넓히는 대신 장애물을 보고합니다.

## 플러그인 배포

프로젝트 스킬과 에이전트는 `.claude/` 아래에 커밋됩니다. 공유 플러그인 소스와 기본값은 폴더 신뢰와 리뷰를 거쳐 `extraKnownMarketplaces`와 `enabledPlugins`로 `.claude/settings.json`에 들어갑니다. 조직 관리형 설정은 허용된 마켓플레이스와 협상 불가능한(양보할 수 없는) 권한을 제한합니다. 버전과 롤백은 배포 전에 기록합니다.

## 훅(Hook)

결정론적인 pre-write 훅은 선언된 범위 밖의 경로를 차단합니다. post-edit 훅은 변경된 파일만 포맷합니다. pre-command 훅은 시크릿 출력과 파괴적 연산을 차단합니다. `PreToolUse` 구조화 결정은 JSON과 함께 exit 0을 사용합니다. exit 2 훅은 차단 이유를 stderr에 쓰고 JSON은 출력하지 않습니다. `PermissionRequest` 훅은 자체적인 중첩 결정 형식을 사용합니다.

## 헤드리스 CI

CI는 버전 관리되는 프로젝트 구성, 읽기 전용 리뷰 도구, 제한된 실행 시간, 구조화된 발견 항목, 별도의 결정론적 테스트를 갖춘 신선한 체크아웃에서 시작합니다. 인터랙티브 세션을 절대 상속하지 않습니다. 2026-08-09 기준으로 확인한 바, 관리형 Code Review는 Team 및 Enterprise 리서치 프리뷰이며, 게이트(gate, 통과 기준)를 대체하지 않고 발견 사항만 보고합니다. 저장소 자동화는 명시적인 워크플로 권한과 도구와 함께 `anthropics/claude-code-action@v1`을 사용합니다.

## 보완(Remediation)

안정적인 발견 항목 ID, 원본 증거, 현재 diff, 테스트, 수용 규칙을 보완 리뷰에 전달합니다. 개인의 로컬 선호 설정은 제외합니다.
