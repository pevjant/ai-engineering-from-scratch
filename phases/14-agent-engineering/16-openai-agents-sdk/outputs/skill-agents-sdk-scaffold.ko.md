---
name: agents-sdk-scaffold
description: 분류 에이전트, 핸드오프, 입력/출력/도구 가드레일, 세션 저장소, 추적 프로세서를 갖춘 OpenAI Agents SDK 앱의 뼈대를 세웁니다.
version: 1.0.0
phase: 14
lesson: 16
tags: [openai, agents-sdk, handoffs, guardrails, tracing, session]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-agents-sdk-scaffold.md](skill-agents-sdk-scaffold.md)

제품 도메인과 전문가 에이전트 목록이 주어지면, OpenAI Agents SDK 앱의 뼈대를 세웁니다.

만들 것:

1. 전문가마다 `Agent` 하나씩, 그리고 핸드오프만 가진(도메인 도구 없는) `triage` 에이전트 하나.
2. 도메인 도구마다 타입 지정 입력 스키마, 명확한 설명(모델에게 언제 쓸지 알려 줌), 실행 샌드박스를 갖춘 `FunctionTool`.
3. 분류 에이전트에서 각 전문가로 가는 `Handoff`. 도구 이름이 `transfer_to_<agent>` 관례를 따르는지 확인합니다.
4. PII, 정책, 범위를 위한 `InputGuardrail`. 기본은 병렬 모드이되, 가드레일 LLM이 본 모델에 비해 크다면 차단 모드를 씁니다.
5. 길이, PII, 정책을 위한 `OutputGuardrail`. 안전이 중요한 출력은 프로덕션에서 항상 차단 모드입니다.
6. 네트워크나 파일시스템을 만지는 함수 도구에는 도구별 가드레일.
7. `Session` 저장소(기본은 SQLite, 프로덕션은 Redis).
8. `add_trace_processor`로 스팬을 OpenAI 추적 UI와 함께 여러분의 백엔드로 연결.

절대 반려 사항:

- 도메인 도구를 가진 분류 에이전트. 분류는 핸드오프만 합니다. 섞으면 라우터의 판단이 옅어집니다.
- 입력/출력을 변경하는 가드레일. 가드레일은 승인하거나 거부할 뿐 — 재작성하지 않습니다.
- 조용한 핸드오프 루프. 홉 카운터를 요구하세요(기본 최대 3).

거절 규칙:

- "가드레일 없이 빠르게만 가자"고 하면, 유료 사용자나 PII를 만지는 제품이라면 거절하세요.
- 전문가가 둘뿐인 제품이라면, 분류+핸드오프 대신 직접 분류기가 있는 `Agents` 라우팅(레슨 12)을 제안하세요 — 토큰 비용이 덜 듭니다.
- 프로덕션에서 추적이 꺼져 있으면 출시를 거절하세요. 추적 없이 다단계 실패는 디버깅이 불가능합니다.

출력: `agents.py`, `tools.py`, `guardrails.py`, `app.py`, 분류 에이전트 근거·가드레일 모드·추적 프로세서·세션 백엔드를 담은 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 레슨 23(OTel GenAI), 레슨 24(관측 백엔드), Claude Agent SDK 번역은 레슨 17을 가리킵니다.
