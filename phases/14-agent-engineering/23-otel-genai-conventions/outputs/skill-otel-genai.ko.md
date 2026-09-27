---
name: otel-genai
description: 에이전트를 OpenTelemetry GenAI 시맨틱 컨벤션으로 계측합니다 — 올바른 속성과 옵트인 콘텐츠 수집을 갖춘 invoke_agent, chat, tool_call 스팬.
version: 1.0.0
phase: 14
lesson: 23
tags: [opentelemetry, genai, observability, tracing, semantic-conventions]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-otel-genai.md](skill-otel-genai.md)

에이전트 런타임이 주어지면 OTel GenAI 시맨틱 컨벤션을 연결합니다.

산출물:

1. 에이전트 실행마다 `invoke_agent` 스팬. 원격 에이전트 서비스는 CLIENT, 프로세스 내부 실행은 INTERNAL. 이름은 `invoke_agent {gen_ai.agent.name}`.
2. LLM 호출마다 `chat` 스팬. `gen_ai.operation.name=chat`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`을 포함합니다.
3. 도구 호출마다 `tool_call` 스팬. `gen_ai.tool.name`과, 해당되면 `gen_ai.data_source.id`(RAG 코퍼스 / 메모리 저장소)를 포함합니다.
4. 옵트인 콘텐츠 수집: 기본값은 OFF. 켜면 입력/출력을 외부에 저장하고 스팬에는 `*.reference_id`만 기록합니다.
5. 컨텍스트 전파: W3C 트레이스 컨텍스트 헤더를 사용해 다중 프로세스 실행(Claude Agent SDK CLI 서브프로세스)도 하나의 트레이스로 이어지게 합니다.

하드 리젝(무조건 거절):

- 기본값으로 프롬프트/출력 전문을 인라인 수집하는 경우. PII와 시크릿 유출 위험이 있고 스펙 위반이기도 합니다.
- `gen_ai.provider.name` 누락. 멀티 공급자 대시보드가 깨집니다.
- 고아 도구 스팬. 항상 활성 컨텍스트를 통해 부모-자식 관계를 설정해야 합니다.

거절 규칙:

- 런타임이 프로세스 경계를 넘어 컨텍스트를 전파할 수 없으면 거절합니다. Claude Agent SDK + CLI 사용자에게는 다중 프로세스 트레이스 연결이 필수입니다.
- 제품에 규제 제약(HIPAA, GDPR)이 있으면 인라인 콘텐츠 수집을 거절합니다. 접근 제어가 있는 외부 저장소만 허용합니다.
- 백엔드가 `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`을 설정하지 않으면 경고합니다. 컬렉터 업그레이드 시 속성 이름이 바뀔 수 있습니다.

출력: 스팬 구조, 안정성 옵트인, 콘텐츠 수집 정책을 설명하는 `tracer.py`, `attributes.py`, `content_store.py`, `README.md`. 마지막에는 "다음에 읽을 것"으로 레슨 24(백엔드: Langfuse, Phoenix, Opik) 또는 Claude Agent SDK 트레이스 컨텍스트 전파는 레슨 17을 가리킵니다.
