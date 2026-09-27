---
name: observability-stack
description: 스택, 규모, 예산, 라이선스 입장이 주어지면 LLM 관측 가능성 스택(개발 플랫폼 + 게이트웨이 + 선택적 스케일 계층)을 고르고 OpenTelemetry GenAI 속성 집합을 정의합니다.
version: 1.0.0
phase: 17
lesson: 13
tags: [observability, langfuse, langsmith, phoenix, arize, helicone, opik, opentelemetry, genai-conventions]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-observability-stack.md](skill-observability-stack.md)

스택(LangChain / DSPy / 순수 SDK), 규모(트레이스/일), 예산, 라이선스 입장(MIT 전용 vs 상용 OK), 셀프호스팅 요구사항이 주어지면 관측 가능성 계획을 만들어 냅니다.

산출물:

1. 개발 플랫폼 선택. Langfuse(오픈소스), LangSmith(LangChain 우선 상용), Opik(Comet 오픈소스), 또는 없음. 스택과 라이선스를 근거로 정당화합니다.
2. 게이트웨이/텔레메트리 선택. Helicone(프록시 + 게이트웨이), SigNoz(풀 APM), OpenLLMetry(순수 OTel). 이미 AI 게이트웨이(페이즈 17 · 19)를 쓰고 있다면 통합 방식을 명시합니다.
3. 스케일/레이크 계층. 선택 사항; 장기 분석에는 Arize AX 또는 날것의 Iceberg, RAG 드리프트에는 Phoenix.
4. OTel GenAI 컨벤션. 최소 속성 집합을 명시합니다: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.request.temperature`, `gen_ai.response.finish_reasons`, 그리고 조직 고유 속성(tenant_id, user_id, task).
5. 샘플링 정책. 에러 100%, 고비용(호출당 >$0.10) 100%, 성공은 N% 샘플링 비율. 원시 데이터 보관 기간(14일 / 30일 / 90일). 집계치는 더 오래 보관합니다.
6. 알림. 반드시 알림을 걸어야 할 다섯 가지 메트릭: 에러율, P99 TTFT, 요청당 비용, 프롬프트 캐시 적중률, 거절률.

하드 리젝(무조건 거절):

- OTel 폴백 없이 프레임워크 전용 SDK 안에서만 계측하는 것. 거절하세요 — 프레임워크 락인입니다.
- 규제 대상이 아닌 워크로드인데 Datadog급 가격(월 >$500)으로 트레이스 100% 보관하는 것. 거절하세요 — 샘플링을 권고합니다.
- OpenTelemetry GenAI 컨벤션을 무시하는 것. 거절하세요 — 2026년 상호 운용에는 필수입니다.

거절 규칙:

- 트레이스/일이 500만을 넘는데 팀이 Datadog 풀 보관을 고집한다면, 비용 전망 없이는 수용하지 않습니다.
- 팀이 MIT 전용인데 LangSmith를 고른다면 거절 — MIT 등가물은 Langfuse입니다.
- 팀에 AI 게이트웨이가 없고 Helicone을 게이트웨이 겸 관측 도구로 고른다면 수용 — 프록시가 초당 약 500 요청까지는 게이트웨이를 겸합니다(게이트웨이 규모는 페이즈 17 · 19에서 다룹니다).

출력: 개발 플랫폼, 게이트웨이, 스케일 계층(있다면), OTel 속성 집합, 샘플링 규칙, 다섯 가지 알림을 적은 한 페이지짜리 계획서. 마지막에 스택 드리프트를 알리는 단 하나의 지표로 마무리합니다: 최근 7일간 OTel GenAI 속성이 온전한 LLM 호출의 비율.
