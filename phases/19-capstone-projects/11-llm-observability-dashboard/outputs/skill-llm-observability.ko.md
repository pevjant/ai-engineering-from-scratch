---
name: llm-observability
description: OpenTelemetry GenAI 스팬을 흡수하고 평가를 돌리며 주입된 퇴보를 5분 안에 잡아내는 셀프 호스팅 LLM 관측 가능성 대시보드를 만듭니다.
version: 1.0.0
phase: 19
lesson: 11
tags: [capstone, observability, otel, langfuse, phoenix, evals, drift, clickhouse]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-llm-observability.md](skill-llm-observability.md)

최소 6개 SDK 계열(OpenAI, Anthropic, Google GenAI, LangChain, LlamaIndex, vLLM)에 걸친 프로덕션 LLM 트래픽이 주어지면, OTLP GenAI 시맨틱 컨벤션 스팬을 흡수하고, 평가를 돌리고, 드리프트를 탐지하고, 알림을 보내는 셀프 호스팅 관측 평면을 배포합니다.

만들기 계획:

1. OTLP HTTP 수신기, tail-sampling 프로세서(오류 100%, 성공 10%, 고독성/PII 100% 보존), ClickHouse + S3 익스포터를 갖춘 OpenTelemetry Collector.
2. GenAI 시맨틱 컨벤션을 그대로 반영하는 ClickHouse 스팬 스키마: gen_ai.system, gen_ai.request.model, usage.input/output_tokens, latency_ms, user_id, app_id, 그리고 프롬프트/컴플리션용 JSON 보관 컬럼.
3. 앱, 사용자, 세션, 어노테이션 큐를 위한 Postgres 메타데이터 저장소.
4. SDK 계열마다 클라이언트 앱에 OpenLLMetry 자동 계측 적용; 표준 스팬이 도착하는지 검증.
5. 샘플링된 트레이스 위에서 예약 실행되는 DeepEval + RAGAS + Phoenix 평가기 팩; PII와 정책 위반용 커스텀 LLM 심사관.
6. 합산 프롬프트 임베딩에 대한 주간 PSI / KL 드리프트 탐지기; 알림 임계값 0.2.
7. 평가 점수 집계와 지연 시간 백분위를 위한 Prometheus 익스포터; Alertmanager는 Slack(경고) + PagerDuty(심각)로 연결.
8. Next.js 15 App Router 대시보드: 개요, 트레이스 검색 + 워터폴, 평가 추이, 드리프트 차트, 알림.
9. 퇴보 프로브: 1% 확률로 가짜 주민등록번호(SSN)를 유출하는 응답 패턴을 주입; MTTR(알림 발사 시간)을 측정.

평가 루브릭:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | 트레이스 스키마 커버리지 | 표준 GenAI 스팬을 만들어 내는 SDK 계열 수 (목표 6개 이상) |
| 20 | 평가 정확성 | 수작업 레이블 셋 대비 DeepEval / RAGAS 점수 |
| 20 | 대시보드 UX | 주입된 퇴보의 MTTR (목표 5분 미만) |
| 20 | 비용 / 확장성 | 백로그 없이 초당 1k 스팬 지속 흡수 |
| 15 | 알림 + 드리프트 탐지 | 끝까지 검증된 Prometheus/Alertmanager 체인 |

즉각 탈락(Hard rejects):

- OpenTelemetry GenAI 시맨틱 컨벤션에 없는 속성 이름을 임의로 만들어 쓰는 스팬 스키마.
- 오류를 버리는 tail-sampling 정책 (잘 알려진 안티패턴입니다).
- 샘플링 없이 흡수율 그대로 도는 평가 (감당할 수 없는 비용).
- p50/p95/p99 구분 없이 "지연 시간"만 보여주는 대시보드.

거절 규칙(Refusal rules):

- PII 삭제(redaction) 정책 없이 프롬프트나 컴플리션을 저장하는 일을 거절합니다.
- SDK별 표준 스팬 퇴보 테스트 없이 "멀티 SDK 지원"을 주장하는 일을 거절합니다.
- 베이스라인 윈도우 없이 드리프트 탐지를 출시하는 일을 거절합니다; 베이스라인 없는 드리프트 탐지는 아무 소용이 없습니다.

산출물: 컬렉터 설정, ClickHouse 스키마, Next.js 15 대시보드, 평가 작업, 드리프트 탐지기, 알림 체인, 주석 달린 퇴보를 포함한 1만 트레이스 데모 데이터셋, 그리고 주입된 PII 퇴보의 MTTR과 반복 과정에서 MTTR을 낮춘 대시보드 UX 개선 상위 세 가지를 문서화한 보고서를 담은 저장소.
