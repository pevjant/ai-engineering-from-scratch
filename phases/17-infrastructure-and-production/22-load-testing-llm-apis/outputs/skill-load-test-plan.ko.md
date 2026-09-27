---
name: load-test-plan
description: 현실적인 LLM 부하 테스트를 설계합니다 — 도구 선택(LLMPerf, k6, GenAI-Perf, guidellm), 네 가지 패턴 구축(정상, 램프, 스파이크, 소크), CI 관문.
version: 1.0.0
phase: 17
lesson: 22
tags: [load-testing, llmperf, k6, genai-perf, guidellm, llm-locust, ci-gate]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-load-test-plan.md](skill-load-test-plan.md)

워크로드(엔드포인트, TTFT/TPOT/오류 SLA), 목표 규모(동시성, RPS), CI 입장(PR 관문 또는 릴리스 전용)이 주어지면 부하 테스트 계획을 만들어 냅니다.

산출물:

1. 도구. 베이스라인 실행에는 LLMPerf; CI 관문에는 k6 + 스트리밍 확장; NVIDIA 참조 실행에는 GenAI-Perf; 대규모 합성에는 guidellm. LLM-Locust는 이미 Locust를 쓸 때만.
2. 프롬프트 분포. 실제 트래픽(있다면) 또는 공개된 분포(ShareGPT / HumanEval)에서 입력 토큰 평균 + 표준편차. 프롬프트 하나짜리 루프는 금지합니다.
3. 네 가지 패턴. 정상, 램프, 스파이크, 소크. 각각: 목표 RPS, 기간, 예상 실패 양상.
4. CI 관문. 구체적인 임계값: TTFT P95 < X, 5xx < 5%, TPOT < Y. PR당 실행 시간: 3-5분.
5. 메트릭 정렬. 보고 도구가 GenAI-Perf 방식(ITL이 TTFT 제외)인지 LLMPerf 방식(ITL이 TTFT 포함)인지 명시합니다. 하나를 고르고 일관되게 유지합니다.
6. 산출물. 저장소에 커밋된 스크립트 파일(k6 JS, LLMPerf CLI).

하드 리젝(무조건 거절):

- 균일 프롬프트로 부하 테스트하는 것. 거절하세요 — 숫자가 거짓말합니다.
- 스트리밍 지원 없이 부하 테스트하는 것. 거절하세요 — LLM 엔드포인트는 기본이 스트리밍입니다.
- 메트릭 정의 차이를 인정하지 않고 도구들 사이의 숫자를 비교하는 것. 거절하세요.

거절 규칙:

- 팀이 LLM-Locust 확장 없이 Locust 순정으로 돌리려 한다면 거절 — GIL 트랩입니다.
- CI 관문 예산이 PR당 60초 미만이면 풀 소크를 거절 — 빠른 정상 상태 + 별도의 밤샘 소크를 제안합니다.
- 프롬프트 분포 데이터가 없다면 문서화된 공개 분포(ShareGPT)를 요구하고 그 가정을 명시합니다.

출력: 도구, 프롬프트 분포, 목표를 갖춘 네 가지 패턴, CI 관문 임계값, 메트릭 정렬을 담은 한 페이지짜리 계획서. 단 하나의 CI 산출물로 마무리합니다: 모든 임계값을 충족하고 3회 실행 안정성을 보일 때만 PR이 초록불.
