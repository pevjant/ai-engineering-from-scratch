---
name: obs-platform-wiring
description: 관측 가능성 플랫폼(Langfuse, Phoenix, Opik, Datadog)을 선택하고 기존 에이전트에 트레이스 + 평가 + 프롬프트 버전을 연결합니다.
version: 1.0.0
phase: 14
lesson: 24
tags: [observability, langfuse, phoenix, opik, datadog, tracing]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-obs-platform-wiring.md](skill-obs-platform-wiring.md)

에이전트 런타임과 제품 요구 사항이 주어지면 관측 가능성 플랫폼을 선택하고 연결 구조의 뼈대를 만듭니다.

의사결정:

1. 프롬프트 관리 + 세션 리플레이를 한곳에서 -> **Langfuse**.
2. 깊은 RAG 관련성 + 드리프트/이상 감지 -> **Phoenix**.
3. 자동 프롬프트 최적화 + PII 가드레일 -> **Opik**.
4. 이미 Datadog를 운영 중 -> **Datadog LLM Observability** (v1.37+부터 GenAI를 네이티브 매핑).
5. ELv2가 아닌 라이선스 필요 -> **Langfuse**(MIT) 또는 **Opik**(Apache 2.0). 순수 OSS 배포라면 Phoenix는 피하세요.

산출물:

1. OTel GenAI 계측(레슨 23) — 모든 선택지의 공통 기반입니다.
2. 플랫폼별 SDK 또는 OTel 익스포터 설정.
3. 도메인에 맞는 LLM 판정 루브릭(사실 정확성, 범위, 어조, 거절 품질).
4. 트레이스와 묶인 프롬프트 버전 관리(Langfuse) 또는 트레이스 클러스터링 설정(Phoenix) 또는 실험 정의(Opik).
5. 기록되는 콘텐츠에 대한 가드레일: PII 마스킹, 시크릿 스크러빙.
6. 대시보드: 세션 건강도, 실패 분류 체계, 지연 시간 분포, 세션당 비용.

하드 리젝(무조건 거절):

- 평가 없이 출시. 트레이싱만으로는 비싼 로깅에 불과합니다.
- 외부 검증이 없는 자체 제작 LLM 판정. CRITIC 패턴(레슨 05): 판정자는 사실 근거를 위해 외부 도구가 필요합니다.
- 스팬 본문에 PII 저장. 항상 외부 저장소 + 참조 ID를 사용합니다.

거절 규칙:

- "모든 걸 다 하는 플랫폼 하나"를 요구하면 거절하고 위 의사결정 기준을 제시하세요. 세 축을 모두 지배하는 단일 플랫폼은 없습니다.
- 각 에이전트 작업에 대한 수용 기준이 없으면 평가 출시를 거절합니다. LLM 판정자에는 루브릭이 필요하고, 루브릭에는 제품 결정이 필요합니다.
- "샘플링 없이 전부 수집"을 원하면 거절합니다. 트레이스 양은 트래픽에 비례해 늘어나며, 규모가 커지면 샘플링(head 기반 또는 tail 기반)이 필수입니다.

출력: 플랫폼 선택, 루브릭, 샘플링 전략, 장애 대응을 설명하는 `instrumentation.py`, `judge.py`, `dashboards.md`, `README.md`. 마지막에는 "다음에 읽을 것"으로 레슨 30(평가 기반 개발) 또는 레슨 26(실패 모드 분류 체계)을 가리킵니다.
