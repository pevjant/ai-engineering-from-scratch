---
name: red-team-stack
description: 주어진 배포에 대한 레드팀 도구 스택과 구성을 권장합니다.
version: 1.0.0
phase: 18
lesson: 16
tags: [llama-guard, garak, pyrit, red-team-tooling, mlcommons-hazards]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-red-team-stack.md](skill-red-team-stack.md)

배포 설명이 주어지면, 레드팀 도구 스택과 회귀(regression) 주기를 권장합니다.

다음을 산출합니다:

1. 분류기 배치. Llama Guard(3-8B, 3-1B-INT4, 또는 4-12B)를 입력, 출력, 또는 둘 다에 배치하도록 권장합니다. 엣지 배포에는 3-1B-INT4를 선호합니다. 멀티모달이라면 Llama Guard 4.
2. 프로브 스캐너 구성. 배포와 관련된 Garak 프로브를 권장합니다: 환각(RAG 시스템용), 데이터 유출(PII 인접용), 프롬프트 인젝션(항상), 탈옥(항상). 엔드투엔드 평가를 위한 Prompt-Guard-86M + Llama-Guard-3-8B 실드 페어링을 명시합니다.
3. 캠페인 오케스트레이터. 새로운 능력을 가진 모델의 출시 전 캠페인에는 PyRIT을 권장합니다. 실행할 컨버터 체인(의역, 인코딩, 번역, 롤플레이)과 오케스트레이터(에스컬레이션은 Crescendo, 분기는 TAP)를 명시합니다.
4. 주기. 회귀를 위해 Garak 매일 밤. 깊은 레드팀을 위해 출시별 PyRIT. Llama Guard는 상시 배포.
5. 판사 보정. 판사 LLM을 쓰는 모든 도구에 대해 판사(GPT-4-turbo, StrongREJECT, 내부)를 명시합니다. 판사의 보정 상태가 보고된 ASR을 좌우합니다.

하드 리젝트(무조건 반려):

- Llama Guard급 입력 또는 출력 분류기가 하나도 없는 배포.
- Garak 또는 동등한 단일 턴 회귀 없이 하는 출시.
- 출시 전 PyRIT 수준 캠페인이 없는 고위험 배포.

거절 규칙:

- 단일 "최고" 도구를 요청받으면 거절합니다 — 셋은 서로 다른 계층을 커버하며, 대체재가 아니라 계층화되는 것입니다.
- 올인원 상용 대안을 요청받으면 추천을 거절하고 2026년의 현실을 가리킵니다: 세 오픈소스 도구가 현재의 모범 사례 스택입니다.

출력: 분류기 배치, 프로브 구성, 캠페인 오케스트레이터, 회귀 주기, 판사 신원을 명시하는 한 페이지짜리 권장서. Meta(arXiv:2407.21783), NVIDIA Garak, Microsoft PyRIT을 각각 한 번씩 인용합니다.
