---
name: a2a-agent-spec
description: A2A로 호출될 에이전트를 위한 에이전트 카드와 스킬 스키마를 산출한다.
version: 1.0.0
phase: 13
lesson: 18
tags: [a2a, agent-card, task-lifecycle, delegation]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-a2a-agent-spec.md](skill-a2a-agent-spec.md)

에이전트의 capability와 의도된 협업자들이 주어졌을 때, 그 에이전트의 A2A 에이전트 카드와 스킬 정의를 산출한다.

산출물:

1. 에이전트 카드. `name`, `description`, `url`, `version`, `schemaVersion`, `capabilities`(streaming, pushNotifications), `skills[]`.
2. 스킬 목록. 각각 `id`, `name`, `description`, `inputModes`, `outputModes`를 갖는다. description에는 "X일 때 사용. Y일 때는 사용 금지." 패턴을 쓴다.
3. 작업 상태 계획. 각 스킬마다 기대되는 상태 전이와 input_required 경로.
4. 서명 계획. AP2로 카드에 서명할지 여부(외부에서 호출 가능한 에이전트에는 권장).
5. 전송. HTTP 위의 JSON-RPC(기본) 또는 gRPC. v1.0과의 하위 호환성을 명시한다.

하드 리젝트(절대 거부):
- 안정적인 URL이 없는 에이전트 카드. 탐색이 깨진다.
- 입력·출력 모드가 선언되지 않은 스킬. 호출자가 호환성을 판단할 수 없다.
- AP2 서명 계획이 없는, 외부에서 호출 가능한 에이전트. 사칭 공격 경로가 된다.

거부 규칙:
- 에이전트의 사용 사례가 단일 도구 호출이라면 A2A 스캐폴딩을 거부하고 MCP를 권한다.
- 에이전트가 내부(도구 호출 트레이스, 사고 연쇄)를 노출하고 있다면 거부하고 불투명성을 의무화한다.
- 에이전트가 결제를 위해 A2A(AP2 사용 사례)가 필요하다면 AP2 확장 버전을 확인하고, AP2는 코어 A2A와 별개임을 표시한다.

출력: 한 페이지짜리 에이전트 카드 JSON, 각 작업별 스킬 스키마, 상태 전이 계획, 서명과 전송 선택. 마지막에 그 에이전트가 약속하는 최소한의 v1.0 하위 호환성 보장을 명시한다.
