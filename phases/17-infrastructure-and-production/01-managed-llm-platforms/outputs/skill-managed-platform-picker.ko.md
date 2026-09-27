---
name: managed-platform-picker
description: 워크로드, SLA, 컴플라이언스 요건을 바탕으로 관리형 LLM 플랫폼(Bedrock, Azure OpenAI, Vertex AI)과 이중화용 두 번째 플랫폼을 고르고, FinOps 계측 계획을 산출합니다.
version: 1.0.0
phase: 17
lesson: 01
tags: [bedrock, azure-openai, vertex-ai, ptu, finops, managed-platforms]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-managed-platform-picker.md](skill-managed-platform-picker.md)


워크로드 프로필(필요한 모델, 월간 토큰 수, P50/P99 TTFT SLA, 컴플라이언스 제약, 기존 클라우드 자산)이 주어지면, 플랫폼 추천을 산출합니다.

다음을 산출합니다:

1. 주 플랫폼. 플랫폼 이름, 그것이 커버하는 구체적 모델, 그리고 이용률을 고려할 때 온디맨드가 맞는지 아니면 PTU(Provisioned Throughput Units) / Provisioned Throughput이 맞는지를 밝히세요. 손익분기 산수를 인용하세요(PTU는 대략 지속 이용률 40~60%에서 분기).
2. 보조 플랫폼. 최소 두 제공자 정책의 폴백을 밝히세요. 조합을 정당화하세요 — 이중화는 모델 중복(Bedrock의 Claude + Azure OpenAI의 GPT가 흔한 조합)과 리전 중복을 모두 커버해야 합니다.
3. FinOps 계측. 첫날 켤 것들: Bedrock Application Inference Profiles, Azure 스코프 + 비용 객체로서의 PTU 예약, Vertex 팀별 프로젝트 + BigQuery Billing Export. 귀속 차원을 명시하세요 — 사용자별, 태스크별, 테넌트별.
4. SLA 점검. 목표 TTFT P99를 공개된 벤치마크와 비교하세요(Azure OpenAI PTU ≈ 50 ms P50; Bedrock 온디맨드 ≈ 75 ms P50). SLA가 온디맨드로 감당할 수 있는 것보다 엄격하면 PTU를 요구하세요.
5. 컴플라이언스 점검. 필요에 따라 BAA, SOC 2 Type II, HIPAA, EU 데이터 레지던시를 확인하세요. 셋 모두 기본선은 충족하지만, 보존 정책과 남용 모니터링 옵트아웃은 다르다는 점을 밝히세요.
6. 마이그레이션 경로. 팀이 이번 주에 취할 수 있는 되돌릴 수 있는 한 단계(예: 제공자를 추상화하는 AI 게이트웨이로 배포; 귀속 헤더 계측)와 장기적인 한 단계(PTU 약정; 교차 리전 페일오버)를 밝히세요.

하드 리젝(무조건 거부) 기준:
- 이름 붙은 폴백 없이 단일 플랫폼을 추천하는 것. 거부하고 최소 두 제공자를 고집하세요.
- 이용률 추정 없이 PTU를 고르는 것. 거부하고 지속 이용률 데이터를 요구하세요.
- 귀속이 요건으로 명시됐는데 Bedrock Application Inference Profiles를 무시하는 것 — 그것이 가장 깔끔한 네이티브 표면입니다.

거부 규칙:
- 워크로드가 Claude, Gemini, GPT를 모두 P0로 요구한다면, 한 플랫폼이 셋을 다 서빙할 수 있다고 꾸미지 말고 세 플랫폼 현실(Bedrock + Vertex + Azure OpenAI를 게이트웨이 뒤에)을 이름으로 밝히세요.
- SLA가 TTFT P99 < 100 ms인데 예상 예산이 PTU를 감당할 수 없다면, 그 SLA를 약속하는 것을 거부하세요 — 온디맨드의 분산 상한을 설명하세요.
- 고객이 "가장 싼 제공자를 쓰자"고 하면 거부하세요 — 가격은 다차원입니다(토큰 단가 + 전용 용량 + 귀속 오버헤드 + 종속 비용).

출력: 주 플랫폼, 보조 플랫폼, PTU vs 온디맨드, 계측 목록, SLA/컴플라이언스 검증, 마이그레이션 두 단계가 담긴 한 페이지 결정서. 마지막에 계획에서 이탈을 잡아 낼 단 하나의 지표(지속 이용률, PTU 낭비, 또는 귀속 커버리지)로 끝냅니다.
