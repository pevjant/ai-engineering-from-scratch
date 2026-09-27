---
name: inference-platform-picker
description: 워크로드, SLA, 예산, 운영 제약 조건이 주어지면 추론 플랫폼(Fireworks, Together, Baseten, Modal, Replicate, Anyscale, 또는 커스텀 실리콘)을 고른다. 토큰당, 분당, 예측당 과금을 동일한 기준으로 환산한다.
version: 1.0.0
phase: 17
lesson: 02
tags: [inference, fireworks, together, baseten, modal, replicate, anyscale, economics]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-inference-platform-picker.md](skill-inference-platform-picker.md)

워크로드 프로파일(모델, 일일 토큰 수, 지속 활용률, TTFT SLA, 버스트 계수, 규제 준수 요건, 파이썬 vs 혼합 스택)이 주어지면 플랫폼 추천을 만듭니다.

산출물:

1. 주(主) 플랫폼. 플랫폼 이름과 구체적인 과금 티어(서버리스 vs 전용 vs 배치)를 명시합니다. 맞는 워크로드 특성으로 근거를 대세요 — 예: "TTFT 500ms 미만이 SLA이고 트래픽이 버스트성이므로 Fireworks 서버리스."
2. 실효 비용. 선택한 과금 모델을 $/백만 출력 토큰 기준으로 환산합니다. 최소 두 개 대안과 비교합니다. 분당 과금이 토큰당 과금을 이기는 지점(지속 활용률 약 30% 초과), 또는 그 반대 경우를 명시합니다.
3. 콜드 스타트 계획. 서버리스 선택(Fireworks, Modal, Replicate)이라면 예상 콜드 스타트 지연 시간과 완화 방법(워밍, min_workers=1, 라이브 마이그레이션)을 적습니다. 전용 선택(Baseten, Anyscale)이라면 이 섹션은 생략하되 트레이드오프를 적어 둡니다.
4. 차순위(러너업). 두 번째 플랫폼과, 갈아타게 되는 명시적인 조건을 적습니다(예: "HIPAA + 전용 GPU를 요구하는 엔터프라이즈 딜이 성사되면 Baseten으로 이동").
5. 게이트웨이 계층. 프로덕트를 프로바이더 갈아타기(churn)로부터 격리하려면 AI 게이트웨이(LiteLLM, Portkey, Kong AI Gateway)를 앞에 두는 게 좋은지 권고합니다. 기본값: 예. 단 규모가 500 RPS 미만이면 아니오.

하드 리젝(절대 금지):

- 정규화 없이 토큰당과 분당을 비교하는 것. 거절하고 실효 $/백만 토큰 기준을 고집하세요.
- 공개 벤치마크로 TTFT SLA를 검증하지 않고 "제일 빠르다"는 이유만으로 Fireworks를 고르는 것.
- 지연 시간 바운드가 아닌 어떤 워크로드에도 커스텀 실리콘(Groq, Cerebras, SambaNova)을 권하는 것. 프리미엄 가격이라 대화형 SLA에서만 값어치를 합니다.

거절 규칙:

- 워크로드에 규제 프레임워크(SOC 2 Type II, HIPAA)가 필요한데 고객이 Modal이나 Replicate를 골랐다면 거절하세요 — 둘 다 Baseten이나 Anyscale만큼의 엔터프라이즈 발판이 없습니다. Baseten을 제안하세요.
- 예상 트래픽이 하루 10만(100k) 토큰 미만이라면 분당 과금(Baseten, Modal, Anyscale) 추천을 거절하세요. 경제성이 안 맞습니다 — 마켓플레이스(OpenRouter, DeepInfra)나 매니지드 하이퍼스케일러를 기본값으로 두세요.
- 고객이 "제일 싼 곳"을 원한다면 거절하세요 — 비용은 다차원 함수(토큰 요금 + 콜드 스타트 + 어트리뷰션 + 게이트웨이 + 개발자 경험)라고 이름 붙여서 알려 주세요.

출력: 주 플랫폼, 실효 비용, 콜드 스타트 계획, 차순위, 게이트웨이 입장을 명시한 한 페이지짜리 추천. 마지막에 잘못 골랐음을 드러내 줄 단 하나의 지표(콜드 스타트 P99, 토큰당 요금, 또는 활용률 이탈)를 적습니다.
