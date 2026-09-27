---
name: parallel-call-safety-check
description: 도구 레지스트리의 안전한 병렬화를 감사합니다. 각 도구에 parallel_safe를 표시하고, 순서 의존성을 기록하고, 다운스트림 레이트 리밋 위험을 표시합니다.
version: 1.0.0
phase: 13
lesson: 03
tags: [parallel-tool-calls, streaming, correlation, rate-limits]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-parallel-call-safety-check.md](skill-parallel-call-safety-check.md)

도구 레지스트리(이름, 설명, 실행기를 가진 도구 목록)가 주어지면, `parallel_safe: bool`, `ordering_deps: [tool_name]`, `rate_limit_group: name` 필드를 추가한 주석 달린 사본을 돌려줍니다.

산출물:

1. 도구별 분류. 각 도구에 대해 판단합니다. 같은 턴 안에서 병렬로 돌려도 안전한지(순수 읽기, 서로 다른 리소스), 안전하지 않은지(변경 작업, 공유 리소스, 외부 레이트 리밋).
2. 의존성 그래프. 한 도구의 출력이 다른 도구의 입력으로 흘러가야 하는 쌍을 찾습니다. 한 턴 안에서는 병렬화할 수 없습니다. `ordering_deps`로 표시합니다.
3. 레이트 리밋 그룹화. 같은 다운스트림 API를 치는 도구들은 하나의 그룹을 공유합니다. 호스트는 도구별이 아니라 그룹별로 동시성을 제한해야 합니다.
4. 안전 권고. 안전하지 않은 각 도구에 대해, 그 턴의 병렬을 끌지, 대기열에 넣을지, 리소스별로 샤딩할지를 명시합니다.
5. 프로바이더별 플래그. 안전하지 않은 도구가 집합에 하나라도 있으면 OpenAI의 `parallel_tool_calls=false` 또는 Anthropic의 `disable_parallel_tool_use=true`를 권합니다.

즉시 반려 사항:
- 감사 후에도 분류가 없는 레지스트리. 기본 거부(default-deny)입니다. 미지는 곧 안전하지 않다는 뜻입니다.
- 공유 리소스에 쓰기를 하는 도구인데 `parallel_safe: true`로 표시된 것. 경쟁 상태(race condition)가 납니다.
- `rate_limit_group` 없이 레이트 리밋이 있는 외부 API를 치는 도구.

거절 규칙:
- 검사 없이 모든 도구를 병렬 안전하다고 표시해 달라는 요청은 거절합니다.
- 레지스트리에 같은 리소스를 다루는 결과형 도구가 있으면(같은 경로의 `delete_file`과 `write_file`) 병렬화를 거절하고, 샌드박스 수준 직렬화는 페이즈 14 · 09로 안내하세요.
- 사용자가 자기 도구는 절대 경쟁하지 않는다고 주장하면 거절하고 증거(테스트, 로그, 또는 형식적 논증)를 요구하세요. 경쟁 상태는 프로덕션에서 조용히 일어납니다.

출력: 도구마다 세 새 필드를 담은 JSON 덩어리 형태의 수정된 레지스트리, 그에 이어 가장 위험한 병렬화 선택과 권고 완화책을 짚는 짧은 요약. 현재 턴에 대한 제안 `tool_choice` 오버라이드로 마무리하세요.
