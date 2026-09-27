---
name: provider-portability-audit
description: 한 프로바이더에 맞춘 함수 호출 통합을 감사해, 나머지 둘로 포팅할 때 무엇이 깨지는지 짚어 냅니다.
version: 1.0.0
phase: 13
lesson: 02
tags: [function-calling, openai, anthropic, gemini, portability]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-provider-portability-audit.md](skill-provider-portability-audit.md)

한 프로바이더(OpenAI, Anthropic, 또는 Gemini) 위에서 돌아가는 함수 호출 통합이 주어지면, 같은 로직을 나머지 두 프로바이더에 올릴 때 나타나는 모든 필드 이름 변경, 동작 차이, 하드 리밋 충돌을 나열한 포터빌리티 감사를 만들어 냅니다.

산출물:

1. 선언 diff. 통합의 각 도구마다, 나머지 두 프로바이더 각각에 필요한 봉투 / 필드 이름 변경 / 스키마 번역을 보여 줍니다. 대상 프로바이더가 지원하지 않는 JSON Schema 구성은 표시합니다(Gemini: OpenAPI 3.0 서브셋; OpenAI strict: `$ref` 금지, 모호한 `oneOf` 금지).
2. 응답 diff. 각 프로바이더의 응답 형태에서 도구 호출이 어디 사는지(`tool_calls[]` vs `content[]` 블록 vs `parts[]` 항목)와, `arguments` 파싱을 누가 책임지는지(OpenAI는 문자열, Anthropic과 Gemini는 객체)를 문서화합니다.
3. `tool_choice` diff. 통합의 현재 선택 설정(auto / forbid / force / required)을 대상 프로바이더 형태로 매핑하고, 없는 모드는 표시합니다.
4. 한도 충돌. 도구 수(128 / 64 / 64), 스키마 깊이(5 / 10 / 사실상 무제한), 인자당 길이 한도를 보고합니다. 대상 프로바이더의 한도를 넘는 통합은 block 심각도로 올립니다.
5. Strict 모드 매핑. 대상에서 strict 모드 의미론이 보존되는지 명시합니다. OpenAI `strict: true`에는 Anthropic에 정확히 대응하는 것이 없고, Gemini `responseSchema`는 비슷하지만 요청 수준입니다.

즉시 반려 사항:
- OpenAI가 아닌 대상에서 `arguments`가 문자열이라고 가정하는 통합. 조용히 잘못된 결과를 만들어 냅니다.
- 라우터 없이 Anthropic 또는 Gemini로 포팅할 때 도구 수가 64를 넘는 통합.
- 대상이 OpenAI strict 모드인데 스키마에 `$ref`를 쓰는 통합.

거절 규칙:
- 대응물이 없는 프로바이더 고유 기능(예: OpenAI Responses API의 상태 유지 턴, Anthropic의 컴퓨터 사용 블록)에 의존하는 통합의 포팅을 요청받으면 거절하고, 어떤 기능에 대상 대응물이 없는지 설명하세요.
- 승자를 골라 달라고 요청받으면 거절하세요. 선택은 호스트의 strict 모드 필요성, 비용 프로필, 병렬 호출 요구사항에 달려 있습니다.

출력: 도구별 diff 표와 한도 표, 그리고 대상 프로바이더별 최종 "포트 판정"(ship / needs-router / blocked-by-feature)이 담긴 한 페이지짜리 감사 보고서. 가장 효과가 큰 마이그레이션 변경 한 가지를 한 문장으로 짚으며 마무리하세요.
