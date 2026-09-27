> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# AI 게이트웨이 — LiteLLM, Portkey, Kong AI Gateway, Bifrost

> 게이트웨이는 여러분의 앱과 모델 프로바이더 사이에 앉습니다. 핵심 기능은 프로바이더 라우팅, 폴백, 재시도, 속도 제한, 시크릿 참조, 관측, 가드레일입니다. 2026년 시장 구도: **LiteLLM**은 MIT 오픈소스에 100개 이상 프로바이더, OpenAI 호환이지만 약 2000 RPS 부근에서 무너집니다(공개 벤치마크에서 8 GB 메모리, 연쇄 장애); Python, 500 RPS 미만, 개발/프로토타이핑에 최적입니다. **Portkey**는 컨트롤 플레인 포지션(가드레일, PII 마스킹, 탈옥 감지, 감사 로그)이며 2026년 3월 Apache 2.0 오픈소스가 됐고, 지연 오버헤드 20-40ms, 프로덕션(운영 환경) 티어 월 $49입니다. **Kong AI Gateway**는 Kong Gateway 위에 지어졌습니다 — 같은 12 CPU에서 Kong 자체 벤치마크 기준 Portkey보다 228% 빠르고, LiteLLM보다 859% 빠릅니다; 모델당 월 $100 가격(Plus 티어 최대 5개); 이미 Kong을 쓰고 있다면 엔터프라이즈에 적합합니다. **Bifrost**(Maxim AI) — 구성 가능한 백오프를 갖춘 자동 재시도, OpenAI 429 시 Anthropic으로 폴백. **Cloudflare / Vercel AI Gateway** — 관리형, 운영 제로, 기본 재시도. 데이터 레지던시(데이터 저장 위치 요건)가 셀프호스팅 결정을 좌우합니다; Portkey와 Kong은 오픈소스 + 선택적 관리형으로 중간 지점에 있습니다.

**유형:** 학습
**언어:** Python (표준 라이브러리, 게이트웨이 라우팅 시뮬레이터 장난감 버전)
**선수 지식:** 페이즈 17 · 01 (관리형 LLM 플랫폼), 페이즈 17 · 16 (모델 라우팅)
**시간:** 약 60분

## 학습 목표

- 게이트웨이의 핵심 기능들을 나열할 수 있습니다 (라우팅, 폴백, 재시도, 속도 제한, 시크릿, 관측, 가드레일).
- 2026년의 네 가지 게이트웨이(LiteLLM, Portkey, Kong AI, Bifrost)를 규모 상한과 사용 사례에 매핑할 수 있습니다.
- Kong 벤치마크(Portkey 대비 228%, LiteLLM 대비 859%)를 인용하고 500 RPS 초과에서 왜 중요한지 설명할 수 있습니다.
- 데이터 레지던시와 운영 예산에 따라 셀프호스팅 vs 관리형을 선택할 수 있습니다.

## 문제 상황

제품이 OpenAI, Anthropic, 셀프호스팅 Llama를 호출합니다. 프로바이더마다 SDK, 오류 모델, 속도 제한, 인증 방식이 다릅니다. 여러분이 원하는 것은 페일오버(OpenAI가 429를 내면 Anthropic 시도), 단일 자격 증명 보관소, 통합 관측, 테넌트별 속도 제한입니다.

이걸 애플리케이션 계층에서 새로 만들면 모든 서비스가 모든 프로바이더에 결합됩니다. 게이트웨이 계층은 이것을 프로바이더로 뻗어나가는 하나의 API(보통 OpenAI 호환)를 가진 하나의 프로세스로 압축합니다.

## 개념

### 여섯 가지 핵심 기능

1. **프로바이더 라우팅** — OpenAI, Anthropic, Gemini, 셀프호스팅 등을 하나의 API 뒤로.
2. **폴백** — 429, 5xx 또는 품질 실패 시 다른 곳에서 재시도.
3. **재시도** — 지수 백오프, 횟수 제한.
4. **속도 제한** — 테넌트별, 키별, 모델별.
5. **시크릿 참조** — 실행 시점에 볼트에서 자격 증명을 끌어옴(앱에 절대 두지 않음).
6. **관측** — OTel + GenAI 속성(페이즈 17 · 13) + 비용 귀속.
7. **가드레일** — PII 마스킹, 탈옥 감지, 허용 주제 필터.

### LiteLLM — MIT 오픈소스, Python

- 100개 이상 프로바이더, OpenAI 호환, 라우터 설정, 폴백, 기본 관측.
- Kong의 벤치마크에서 약 2000 RPS 부근에서 무너짐; 메모리 발자국 8 GB, 지속 부하에서 연쇄 장애.
- 가장 잘 맞는 곳: Python 앱, 500 RPS 미만, 개발/스테이징 게이트웨이, 실험적 라우팅.
- 비용: 오픈소스는 $0; 클라우드 무료 티어도 있음.

### Portkey — 컨트롤 플레인 포지셔닝

- 2026년 3월부터 Apache 2.0 오픈소스. 가드레일, PII 마스킹, 탈옥 감지, 감사 로그.
- 요청당 지연 오버헤드 20-40ms.
- 보존 기간 + SLA가 포함된 프로덕션 티어 월 $49.
- 가장 잘 맞는 곳: 가드레일 + 관측이 묶인 것을 필요로 하는 규제 산업.

### Kong AI Gateway — 대규모용 카드

- Kong Gateway(성숙한 API 게이트웨이 제품, lua+OpenResty) 위에 지어짐.
- 12 CPU 상당에서 Kong 자체 벤치마크: Portkey보다 228% 빠름, LiteLLM보다 859% 빠름.
- 가격: 모델당 월 $100, Plus 티어 최대 5개.
- 가장 잘 맞는 곳: 이미 Kong 사용 중; 1000 RPS 초과; 라이선스 비용 감수 가능.

### Bifrost (Maxim AI)

- 구성 가능한 백오프를 갖춘 자동 재시도.
- OpenAI 429 시 Anthropic 폴백은 대표 레시피입니다.
- 신생 참여자; 상용.

### Cloudflare AI Gateway / Vercel AI Gateway

- 관리형, 운영 제로. 기본 재시도와 관측.
- 가장 잘 맞는 곳: Cloudflare/Vercel 위의 엣지 서빙 JavaScript 앱.
- 가드레일과 속도 제한은 Kong/Portkey에 비해 제한적입니다.

### 셀프호스팅 vs 관리형

데이터 레지던시가 강제 함수입니다. 헬스케어와 금융은 셀프호스팅이 기본(LiteLLM, Portkey OSS, 또는 Kong). 소비자 제품은 관리형(Cloudflare AI Gateway) 또는 중간층(Portkey 관리형)이 기본입니다. 하이브리드: 규제 대상 테넌트는 셀프호스팅, 나머지는 관리형.

### 지연 시간 예산

- LiteLLM: 보통 5-15ms 오버헤드.
- Portkey: 20-40ms 오버헤드.
- Kong: 3-8ms 오버헤드.
- Cloudflare/Vercel: 1-3ms 오버헤드(엣지 이점).

게이트웨이 지연은 TTFT에 그대로 더해집니다. TTFT P99 < 100ms SLA라면 Kong 또는 Cloudflare. P99 < 500ms라면 어느 것이든.

### 속도 제한 의미론이 중요합니다

단순 토큰 버킷은 중간 규모까지만 버틱니다. 멀티테넌트에는 슬라이딩 윈도우 + 버스트 허용 + 테넌트별 등급이 필요합니다. LiteLLM은 토큰 버킷, Kong은 슬라이딩 윈도우, Portkey는 등급제를 제공합니다.

### 게이트웨이 + 관측 + 라우팅의 조합

페이즈 17 · 13(관측) + 16(모델 라우팅) + 19(게이트웨이)는 프로덕션에서 같은 계층입니다. 셋을 모두 커버하는 도구 하나를 고르거나 신중하게 연결하세요: 2026년 배포 대부분은 Helicone(관측) 또는 Portkey(가드레일)와 Kong(규모)을 역할을 나눠 결합합니다.

### 기억해야 할 숫자들

- LiteLLM: 약 2000 RPS에서 붕괴, 메모리 8 GB.
- Portkey: 20-40ms 오버헤드; 2026년 3월부터 Apache 2.0.
- Kong: Portkey보다 228% 빠름, LiteLLM보다 859% 빠름.
- Kong 가격: 모델당 월 $100, Plus 티어 최대 5개.
- Cloudflare/Vercel: 엣지에서 1-3ms 오버헤드.

```figure
mx-gateway-fallback
```

## 활용하기

`code/main.py`는 3개 프로바이더를 대상으로 429/5xx 주입 하에서 폴백이 있는 게이트웨이 라우팅을 시뮬레이션합니다. 지연 시간, 재시도율, 폴백 적중률을 보고합니다.

## 출시하기

이 레슨은 `outputs/skill-gateway-picker.md`를 산출합니다. 규모, 운영 입장, 컴플라이언스, 지연 시간 예산이 주어지면 게이트웨이를 고릅니다.

## 연습 문제

1. `code/main.py`를 실행하세요. OpenAI→Anthropic→셀프호스팅 폴백을 설정하세요. 프로바이더 오류율 5%에서 예상 적중률은 얼마인가요?
2. SLA가 300ms 베이스라인 위에서 TTFT P99 < 200ms입니다. 어느 게이트웨이가 예산 안에 남나요?
3. 헬스케어 고객이 셀프호스팅 + PII 마스킹 + 감사 로그를 요구합니다. Portkey OSS 또는 Kong을 고르세요.
4. LiteLLM vs Kong을 비교하세요: 어떤 RPS 상한에서 팀이 마이그레이션해야 하나요?
5. 멀티테넌트 SaaS의 속도 제한 정책을 설계하세요: 무료 티어, 체험 티어, 유료 티어. 토큰 버킷입니까, 슬라이딩 윈도우입니까?

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| 게이트웨이 | "API 브로커" | 앱과 프로바이더 사이에 앉는 프로세스 |
| LiteLLM | "그 MIT제" | Python 오픈소스, 100개 이상 프로바이더, 2K RPS에서 붕괴 |
| Portkey | "가드레일 게이트웨이" | 컨트롤 플레인 + 관측, Apache 2.0 |
| Kong AI Gateway | "대규모용" | Kong Gateway 기반, 벤치마크 선두 |
| Bifrost | "Maxim의 게이트웨이" | 재시도 + Anthropic 폴백 레시피 |
| Cloudflare AI Gateway | "엣지 관리형" | 엣지에 배포된 관리형 게이트웨이, 운영 제로 |
| PII 마스킹 | "데이터 세척" | 모델에 보내기 전 정규식 + NER 마스킹 |
| 탈옥 감지 | "프롬프트 인젝션 가드" | 사용자 입력에 대한 분류기 |
| 감사 로그 | "규제용 기록" | 모든 LLM 호출의 불변 기록 |
| 토큰 버킷 | "단순 속도 제한" | 리필 기반 속도 제한기 |
| 슬라이딩 윈도우 | "정밀 속도 제한" | 시간 창 기반 속도 제한기; 더 나은 공정성 |

## 더 읽을거리

- [Kong AI Gateway Benchmark](https://konghq.com/blog/engineering/ai-gateway-benchmark-kong-ai-gateway-portkey-litellm)
- [TrueFoundry — AI Gateways 2026 Comparison](https://www.truefoundry.com/blog/a-definitive-guide-to-ai-gateways-in-2026-competitive-landscape-comparison)
- [Techsy — Top LLM Gateway Tools 2026](https://techsy.io/en/blog/best-llm-gateway-tools)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Portkey GitHub](https://github.com/Portkey-AI/gateway)
- [Kong AI Gateway docs](https://docs.konghq.com/gateway/latest/ai-gateway/)
