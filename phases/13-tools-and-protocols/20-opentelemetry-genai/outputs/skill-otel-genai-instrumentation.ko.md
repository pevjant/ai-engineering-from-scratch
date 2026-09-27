---
name: otel-genai-instrumentation
description: 에이전트 코드베이스가 엔드투엔드로 OTel GenAI 스팬을 방출하게 하기 위한 계측 계획을 산출한다.
version: 1.0.0
phase: 13
lesson: 19
tags: [otel, observability, gen-ai, tracing]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-otel-genai-instrumentation.md](skill-otel-genai-instrumentation.md)

에이전트 코드베이스(LLM 호출, 도구 디스패치, MCP 클라이언트, 하위 에이전트)가 주어졌을 때, OTel GenAI 계측 계획을 산출한다.

산출물:

1. 스팬 계층. 루트 `agent.invoke_agent`(INTERNAL)와 자식들: `llm.chat`(CLIENT), `tool.execute`(INTERNAL), `mcp.call`(CLIENT), `subagent.invoke`(INTERNAL).
2. 스팬별 속성 체크리스트. `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.*`, `gen_ai.tool.name`, `gen_ai.agent.name`.
3. 전파(propagation) 규칙. 모든 원격 호출에 W3C traceparent를 주입; MCP stdio에는 과도기 필드로 `_meta.traceparent`를 사용.
4. 콘텐츠 캡처 정책. 기본적으로 꺼짐; 어떤 환경 변수가 켜는지 문서화; PII 위험을 지목.
5. 익스포터 선택. Jaeger / Tempo / Langfuse / Phoenix / Datadog / Honeycomb; 와이어는 OTLP.

하드 리젝트(절대 거부):
- MCP 또는 하위 에이전트 경계를 넘는 트레이스 전파가 빠진 계획.
- 콘텐츠 캡처가 기본으로 켜져 있는 계획. 프롬프트와 PII가 새어 나간다.
- `gen_ai.` 또는 명시적인 벤더 접두사 없이 임의의 커스텀 속성을 방출하는 계획.

거부 규칙:
- 코드베이스가 OTel 자동 계측이 내장된 프레임워크(Pydantic AI, LangGraph, AgentOps)를 쓴다면 프레임워크 훅을 먼저 권한다.
- 익스포터 백엔드가 온프레미스인데 팀에 SRE 지원이 없다면 관리형(managed) 백엔드를 권한다.
- 프로덕션(운영 환경) 디버깅을 위해 콘텐츠 캡처를 요청한다면, 타입이 지정된 동의 정책과 PII 마스킹 파이프라인이 없는 한 거부한다.

출력: 스팬 계층, 스팬별 속성 체크리스트, 전파 규칙, 콘텐츠 캡처 정책, 익스포터 선택이 담긴 한 페이지짜리 계획. 마지막에 알림(alert)을 걸 최상위 메트릭을 명시한다(보통 p95 `gen_ai.client.operation.duration`).
