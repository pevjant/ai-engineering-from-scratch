---
name: gateway-picker
description: 규모, 지연 시간 예산, 컴플라이언스, 운영 입장, 가격 허용도가 주어지면 AI 게이트웨이(LiteLLM, Portkey, Kong AI, Cloudflare/Vercel)를 고릅니다.
version: 1.0.0
phase: 17
lesson: 19
tags: [ai-gateway, litellm, portkey, kong, cloudflare, vercel, bifrost, fallback, rate-limit, guardrails]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-gateway-picker.md](skill-gateway-picker.md)

RPS(현재 및 향후 12개월 예상), 지연 시간 예산, 컴플라이언스(셀프호스팅 필수?), 가드레일 필요성(PII 마스킹, 탈옥 감지, 감사), 가격 허용도가 주어지면 게이트웨이 추천을 만들어 냅니다.

산출물:

1. 기본 게이트웨이. 도구 이름을 말합니다. RPS 상한, 오버헤드, 기능 적합성으로 정당화합니다.
2. 폴백 체인. 순서대로 세 프로바이더; OpenAI → Anthropic → 셀프호스팅이 대표 조합입니다. 예상 가용성을 계산합니다.
3. 속도 제한 정책. 500 RPS 초과에는 슬라이딩 윈도우 권장; 그 외에는 토큰 버킷 허용. 테넌트별 등급제.
4. 가드레일. PII/탈옥이 필요하면 Portkey; 규모 + 가드레일이면 Kong; 개발 티어 전용이면 LiteLLM.
5. 관측 인계. 페이즈 17 · 13의 선택지로 연결; OTel GenAI 컨벤션이 그대로 흐르는지 확인합니다.
6. 마이그레이션. 앱 수준 통합에서 옮겨온다면 단계적 롤아웃(게이트웨이 위에서 1% 카나리, 성공 시 확대).

하드 리젝(무조건 거절):

- 2000 RPS 초과에서 LiteLLM. 거절하세요 — Kong 벤치마크가 연쇄 장애를 보여줍니다; 먼저 마이그레이션하세요.
- TTFT P99 < 100ms SLA에서 Portkey. 거절하세요 — 30ms 오버헤드가 예산을 너무 많이 잠식합니다.
- 온프레미스를 요구하는 규제 고객에게 Cloudflare AI Gateway. 거절하세요 — 관리형 전용; 셀프호스팅 없음.

거절 규칙:

- 규모 모호성이 크다면(현재 100 RPS, 6개월 내 2K+ 계획), LiteLLM에 확정하기 전에 마이그레이션 계획을 요구합니다.
- 컴플라이언스가 SOC 2 Type II를 요구하는데 선택한 게이트웨이가 관리형 SLA 없는 오픈소스 전용이라면, 고객 자체의 SOC 2 증명을 요구합니다.
- 팀에 Kubernetes가 없는데 Kong 셀프호스팅을 고른다면 거절 — 관리형 Kong 또는 Portkey 관리형을 권고합니다.

출력: 게이트웨이, 폴백 체인, 속도 제한 정책, 가드레일 입장, 관측 흐름, 마이그레이션 계획을 담은 한 페이지짜리 결정서. 마지막에 지표 하나로 마무리합니다: 직전 1시간의 게이트웨이 지연 P99; 위반 시 알림.
