---
name: computer-use-safety
description: 컴퓨터 사용 에이전트를 위한 단계별 안전 분류기 + 확인 게이트를 허용 목록 내비게이션과 인젝션 마커 필터와 함께 만듭니다.
version: 1.0.0
phase: 14
lesson: 21
tags: [computer-use, safety, claude, openai-cua, gemini]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-computer-use-safety.md](skill-computer-use-safety.md)

컴퓨터 사용 에이전트와 대상 앱 목록이 주어지면, 모든 행동을 실행 전에 분류하는 안전 레이어를 만들어 냅니다.

만들 것:

1. `allow`, `reason`, `needs_confirmation` 필드를 가진 `SafetyClassifier.assess(action, screen) -> SafetyVerdict`.
2. 에이전트가 클릭할 수 있는 요소 라벨의 허용 목록. 그 외에는 거부.
3. 에이전트가 이동할 수 있는 URL의 허용 목록. 목록 밖으로 나가는 리다이렉트는 거부.
4. DOM 텍스트, 검색된 콘텐츠, 입력 텍스트에 대한 인젝션 마커 필터. 하나라도 걸리면 행동을 막습니다.
5. 민감한 행동(로그인, 구매, 삭제, 게시)을 위한 확인 게이트. 휴먼인더루프 콜백 인터페이스.
6. 추적 방출기: 모든 판단이 (action, verdict, reason)과 함께 기록됩니다.

절대 반려 사항:

- 첫 행동에만 도는 안전 분류기. 모든 행동은 분류돼야 합니다.
- `*` 모양의 허용 목록. 모든 걸 허용하는 허용 목록은 허용 목록이 아닙니다.
- 모델이 "확신에 찬 듯 보인다"는 이유로 확인 건너뛰기. 확신은 안전이 아닙니다.

거절 규칙:

- 에이전트가 단계별 안전 없이 컴퓨터 사용 권한을 가지고 있다면 출시를 거절하세요.
- 에이전트가 임의 URL로 이동할 수 있다면 거절하세요. 허용 목록이나 차단 목록을 요구하세요.
- 어떤 모드에서든 민감 행동이 확인 게이트를 우회한다면 거절하세요.

출력: `classifier.py`, `allowlist.py`, `confirmation.py`, `trace.py`, 게이트 정책·인젝션 마커·허용 목록 유지보수 절차를 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 레슨 27(프롬프트 인젝션)과 레슨 23(안전 판단의 OTel 스팬 귀속)을 가리킵니다.
