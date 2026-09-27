> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 추론 플랫폼 경제학 — Fireworks, Together, Baseten, Modal, Replicate, Anyscale

> 2026년의 추론(inference) 시장은 더 이상 GPU 시간 대여 사업이 아닙니다. 이제 시장은 셋으로 갈라집니다. 자체 설계 칩(커스텀 실리콘 — Groq, Cerebras, SambaNova), GPU 플랫폼(Baseten, Together, Fireworks, Modal), API 우선 마켓플레이스(Replicate, DeepInfra). Fireworks는 2026년 5월 1일부로 GPU당 가격을 $1/시간씩 올렸고, 하루 10조(10T)+ 토큰 처리량으로 $4B 기업가치를 인정받았습니다. 이는 물량 기반 비즈니스 모델이 실제로 통한다는 뜻입니다. Baseten은 2026년 1월 $5B 밸류에이션으로 $300M 시리즈 E를 마쳤습니다. 경쟁 포지셔닝 규칙은 단순합니다. Fireworks는 지연 시간(latency), Together는 카탈로그 폭, Baseten은 엔터프라이즈 완성도, Modal은 파이썬 네이티브 개발자 경험, Replicate는 멀티모달 커버리지, Anyscale는 분산 파이썬에 각각 최적화되어 있습니다. 이 레슨은 창업자에게 그대로 건넬 수 있는 비교 매트릭스를 만들어 줍니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 호출당 비용을 비교하는 장난감 수준 비교기)
**선수 지식:** Phase 17 · 01 (매니지드 LLM 플랫폼), Phase 17 · 04 (서빙 엔진 내부 구조)
**시간:** 약 60분

## 학습 목표

- 세 개의 시장 세그먼트(커스텀 실리콘, GPU 플랫폼, API 우선)를 말로 설명하고, 각 벤더가 어느 세그먼트에 속하는지 짝지을 수 있다.
- "토큰당" API 가격 모델이 하드웨어 원가가 아니라 서빙 엔진의 원가 곡선을 향해 수렴(압축)하는 이유를 설명할 수 있다.
- 최소 세 개 벤더에 대해 요청당 실효 비용을 계산하고, 언제 분당 과금(Baseten, Modal)이 토큰당 과금을 이기는지 설명할 수 있다.
- 주어진 워크로드(서버리스 버스트형, 꾸준한 고처리량, 파인튜닝 변형 모델, 멀티모달)에 어떤 플랫폼이 기본 선택으로 맞는지 판별할 수 있다.

## 문제 상황

여러분은 매니지드 하이퍼스케일러 플랫폼을 검토했고, 이제 더 좁고 더 빠른 프로바이더가 필요하다고 판단했습니다 — 지연 시간은 Fireworks, 폭은 Together, 파인튜닝한 커스텀 모델은 Baseten. 그런데 실제 선택지가 여섯 개가 되니 가격 페이지끼리 전혀 맞춰지지 않습니다. Fireworks는 $/백만 토큰을 보여주고, Baseten은 $/분, Modal은 $/초, Replicate는 $/예측(prediction)을 보여줍니다. 워크로드를 모델링하지 않으면 이들을 정면으로 비교할 수 없습니다.

더 곤란한 건, 가격 페이지 뒤에 숨은 비즈니스 모델 자체가 다르다는 점입니다. Fireworks는 공유 GPU 위에 자체 엔진(FireAttention)을 돌립니다. 토큰당 요금은 그들의 활용률 곡선을 반영한 값입니다. Baseten은 Truss + 전용 GPU를 줍니다. 분당 과금은 '나만 쓰는 배타성'의 값입니다. Modal은 진짜 파이썬 서버리스입니다. 초 단위 과금에 콜드 스타트가 1초 미만입니다. 똑같은 결과물(LLM 응답)인데 비용 함수가 세 가지입니다.

이 레슨은 여섯 플랫폼을 모델링하고, 각각이 언제 이기는지 알려줍니다.

## 개념

### 세 개의 세그먼트

**커스텀 실리콘** — Groq(LPU), Cerebras(WSE), SambaNova(RDU). 같은 모델을 GPU 기반 클러스터로 돌릴 때보다 보통 5~10배 빠른 디코드 속도를 냅니다. 토큰당 가격은 더 비쌉니다(2025년 말 기준 Groq가 Llama-70B에서 약 $0.99/M)만, 지연 시간에 민감한 용도에서는 적수가 없습니다. 음성 에이전트와 실시간 번역에는 Groq가 프로덕션(운영 환경) 선택지입니다.

**GPU 플랫폼** — Baseten, Together, Fireworks, Modal, Anyscale. NVIDIA(H100, H200, 2026년엔 B200) 위에서 돌리고, 가끔 AMD도 씁니다. "날 GPU 대여"(RunPod, Lambda)와 "하이퍼스케일러 매니지드 서비스"(Bedrock) 사이의 경제 계층입니다.

**API 우선 마켓플레이스** — Replicate, DeepInfra, OpenRouter, Fal. 카탈로그가 넓고, 예측당 또는 초당 과금하며, '첫 API 호출까지 걸리는 시간'을 강조합니다.

### Fireworks — 지연 시간 최적화 GPU 플랫폼

- FireAttention 엔진(자체 개발). 동등한 설정의 vLLM 대비 4배 낮은 지연 시간이라고 마케팅합니다.
- 비대화형(non-interactive) 워크로드용 배치 티어는 서버리스 요금의 약 50% 수준입니다.
- 파인튜닝된 모델도 베이스 모델과 같은 요금으로 서빙합니다 — 내 LoRA에 프리미엄을 붙이는 다른 프로바이더들과 구별되는 진짜 차별점입니다.
- 2026년 중반: 2026년 5월 1일부로 온디맨드 GPU 대여료를 $1/시간 인상. 물량이 크면 볼륨 가격 협상이 가능합니다.
- 재무 신호: $4B 밸류에이션, 하루 10조(10T)+ 토큰 처리.

### Together — 폭(카탈로그) 최적화

- 200개 이상의 모델. 오픈소스 모델도 상류(upstream) 공개 후 며칠 안에 올라옵니다.
- 동등한 LLM 모델 기준으로 Replicate보다 50~70% 저렴합니다 — "AI 네이티브 클라우드"라는 포지셔닝의 본질은 물량과 카탈로그입니다.
- 추론 + 파인튜닝 + 학습을 하나의 API로 제공합니다.

### Baseten — 엔터프라이즈 완성도 최적화

- Truss 프레임워크: 의존성, 시크릿, 서빙 설정을 매니페스트 하나에 담아 모델을 패키징합니다.
- T4부터 B200까지 GPU 스펙트럼을 커버합니다. 분당 과금이며, 콜드 스타트 완화 장치도 합리적입니다.
- SOC 2 Type II, HIPAA 대응. 핀테크와 헬스케어에서 자주 선택됩니다.
- $5B 밸류에이션, 2026년 1월 시리즈 E(CapitalG, IVP, NVIDIA가 $300M 투자).

### Modal — 파이썬 네이티브 최적화

- 순수 파이썬으로 인프라를 코드로 관리합니다. 함수에 `@modal.function(gpu="A100")` 데코레이터를 붙이고 명령어 한 줄로 배포합니다.
- 초 단위 과금. 워밍(pre-warming)을 하면 콜드 스타트는 2~4초, 작은 모델은 1초 미만입니다.
- $1.1B 밸류에이션으로 $87M 시리즈 B(2025). 독립 조사에서 개발자 경험 점수가 가장 높았습니다.

### Replicate — 멀티모달 폭

- 예측(prediction)당 과금. 이미지, 비디오, 오디오 모델의 기본 플랫폼입니다.
- 통합 생태계(Zapier, Vercel, CMS 플러그인)가 있습니다.
- LLM 토큰당 요금 경쟁력은 약하지만, 멀티모달 다양성에서는 이깁니다.

### Anyscale — Ray 네이티브

- Ray 위에 지어졌고, RayTurbo는 Anyscale의 자체 추론 엔진입니다(vLLM과 경쟁).
- 추론 단계가 더 큰 그래프의 노드 하나인 분산 파이썬 워크로드에 가장 잘 맞습니다.
- 매니지드 Ray 클러스터를 제공하고, Ray AIR와 Ray Serve와 긴밀하게 통합됩니다.

### 토큰당 vs 분당 — 언제 누가 이기는가

토큰당 과금은 워크로드가 지연 시간에 둔감하고 버스트성일 때 합리적입니다 — 쓴 만큼만 내면 되니까요. 분당 과금은 활용률이 높고 예측 가능할 때 합리적입니다 — GPU를 포화시키는 순간부터는 토큰당 과금을 이깁니다.

대략적인 규칙: 전용 GPU를 지속 활용률 약 30% 이상으로 쓰는 워크로드라면 분당 과금(Baseten, Modal)이 토큰당 과금(Fireworks, Together)을 따라잡기 시작합니다. 그 아래라면 토큰당 과금이 이깁니다. 놀고 있는 시간에 대한 요금을 내지 않아도 되기 때문입니다.

### 커스텀 엔진이 진짜 해자(moat)다

위에 나온 vLLM·SGLang 이상의 플랫폼은 모두 자체 엔진을 내세웁니다. FireAttention, RayTurbo, Baseten의 추론 스택이 그렇습니다. 커스텀 엔진 주장은 마케팅이 살짝 섞여 있습니다. 솔직하게 정리하면 이렇습니다. vLLM + SGLang이 오픈소스 추론의 약 80%를 차지하고, 플랫폼 계층에서 실제로 갈리는 요소는 개발자 경험(DX), 어트리뷰션(attribution, 사용량 귀속), SLA입니다.

### 기억해야 할 숫자들

- Fireworks GPU 대여: 2026년 5월 1일부로 $1/시간 인상.
- Fireworks 주장: 동등한 설정의 vLLM 대비 4배 낮은 지연 시간.
- Together: LLM 기준 Replicate보다 50~70% 저렴.
- Baseten 밸류에이션: $5B (시리즈 E, 2026년 1월, $300M 라운드).
- Modal 밸류에이션: $1.1B (시리즈 B, 2025).
- 지속 활용률 약 30%를 넘으면 분당 과금이 토큰당 과금을 이긴다.

```figure
cost-per-token
```

## 직접 써보기

`code/main.py`는 합성(synthetic) 워크로드에 대해 여섯 벤더를 과금 모델별로 비교합니다. $/일과 실효 $/백만 토큰을 보고합니다. 실행해 보면 토큰당 과금과 분당 과금의 손익분기점을 찾을 수 있습니다.

## 산출물

이 레슨은 `outputs/skill-inference-platform-picker.md`를 만듭니다. 워크로드 프로파일, SLA, 예산이 주어지면 주 추론 플랫폼을 고르고 차순위(러너업)까지 이름을 붙여 줍니다.

## 연습 문제

1. `code/main.py`를 실행하세요. H100 한 장에서 70B 모델을 돌릴 때, 지속 활용률이 몇 %부터 Baseten(분당)이 Fireworks(토큰당)를 이기나요? 교차점(crossover)을 직접 유도해 보고, 위의 경험 법칙과 비교해 보세요.
2. 여러분의 제품이 이미지 생성 + 채팅 + 음성 인식(STT)을 함께 서빙합니다. 모달리티별로 플랫폼을 고르고, 이들을 하나로 묶는 게이트웨이 패턴의 이름을 말해 보세요.
3. Fireworks가 여러분의 주 모델에 $1/시간 인상을 단행했습니다. 트래픽의 40%를 배치 티어(50% 할인)로 옮길 때의 혼합(blended) 비용 영향을 모델링해 보세요.
4. 규제 산업 고객이 SOC 2 Type II + HIPAA + 전용 GPU를 요구합니다. 가능한 플랫폼 셋은 무엇이고, FinOps 관점에서는 어느 쪽이 이기나요?
5. Llama 3.1 70B에 대해 Fireworks 서버리스, Together 온디맨드, Baseten 전용, Replicate API의 1,000회 예측당 비용을 비교하세요. 하루 10회 예측일 때 최저가는 어디인가요? 10,000회라면?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| 커스텀 실리콘 | "GPU 아닌 칩" | Groq LPU, Cerebras WSE, SambaNova RDU — 디코드에 최적화 |
| FireAttention | "Fireworks 엔진" | 자체 어텐션 커널. vLLM 대비 4배 낮은 지연 시간이라고 마케팅 |
| Truss | "Baseten 포맷" | 모델 패키징 매니페스트. 의존성 + 시크릿 + 서빙 설정 |
| 토큰당 | "API 과금" | 소비한 토큰 수로 과금. 유휴(idle) 비용 없음 |
| 분당 | "전용 과금" | 실제 GPU 가동 시간으로 과금. 고활용률에서 유리 |
| 예측당 | "Replicate 과금" | 모델 호출 1회당 과금. 이미지/비디오에서 흔함 |
| RayTurbo | "Anyscale 엔진" | Ray 위의 자체 추론 엔진. Ray 클러스터에서 vLLM과 경쟁 |
| 배치 티어 | "50% 할인" | 비대화형 큐를 할인된 요금으로 처리. Fireworks, OpenAI에서 흔함 |
| 베이스 요금 파인튜닝 | "Fireworks LoRA" | LoRA로 서빙한 요청도 베이스 모델 요금으로 청구(차별점) |

## 더 읽을거리

- [Fireworks Pricing](https://fireworks.ai/pricing) — 토큰당 요금, 배치 티어, GPU 대여.
- [Baseten Pricing](https://www.baseten.co/pricing/) — 분당 요금, 약정 용량, 엔터프라이즈 티어.
- [Modal Pricing](https://modal.com/pricing) — 초당 GPU 요금과 무료 티어.
- [Together AI Pricing](https://www.together.ai/pricing) — 모델 카탈로그와 토큰당 요금.
- [Anyscale Pricing](https://www.anyscale.com/pricing) — RayTurbo와 매니지드 Ray 요금.
- [Northflank — Fireworks AI Alternatives](https://northflank.com/blog/7-best-fireworks-ai-alternatives-for-inference) — 비교 평가.
- [Infrabase — AI Inference API Providers 2026](https://infrabase.ai/blog/ai-inference-api-providers-compared) — 벤더 랜드스케이프.
