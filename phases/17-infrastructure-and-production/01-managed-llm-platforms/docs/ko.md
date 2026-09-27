> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 관리형 LLM 플랫폼 — Bedrock, Vertex AI, Azure OpenAI

> 하이퍼스케일러 셋, 서로 다른 세 가지 전략입니다. AWS Bedrock은 모델 마켓플레이스입니다 — Claude, Llama, Titan, Stability, Cohere가 하나의 API 뒤에 있습니다. Azure OpenAI는 OpenAI와의 독점 파트너십에 전용 용량을 위한 PTU(Provisioned Throughput Units)를 더한 형태입니다. Vertex AI는 Gemini를 우선하며 롱 컨텍스트와 멀티모달 스토리가 가장 강합니다. 2026년 Artificial Analysis 측정 기준으로, Llama 3.1 405B 급 배포에서 Azure OpenAI는 중앙값 약 50 ms, Bedrock은 약 75 ms입니다 — 간격은 PTU 덕분입니다. 전용 용량이 공유 온디맨드를 이기기 때문이죠. 결정 규칙은 "어느 쪽이 가장 빠른가"가 아니라 "어느 쪽의 모델 카탈로그와 FinOps 표면이 내 제품에 맞는가"입니다. 이 레슨은 감(vibes)이 아니라 적어 둔 절충점을 근거로 플랫폼을 고르는 법을 가르칩니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 비용-지연 시간 비교 장난감 구현)
**선수 지식:** 페이즈 11 (LLM Engineering), 페이즈 13 (Tools & Protocols)
**시간:** 약 60분

## 학습 목표

- 세 가지 플랫폼 전략(마켓플레이스 vs 독점 vs Gemini 우선)의 이름을 말하고 각각을 제품 사용 사례에 매핑할 수 있다.
- Azure OpenAI에서 PTU(Provisioned Throughput Units)가 무엇을 사 주는지, 그리고 405B 규모에서 온디맨드 Bedrock이 대체로 약 25 ms 느리게 읽히는 이유를 설명할 수 있다.
- 각 플랫폼의 FinOps 귀속(attribution) 표면을 도식화할 수 있다(Bedrock Application Inference Profiles vs Vertex의 팀별 프로젝트 vs Azure의 스코프 + PTU 예약).
- "최소 두 개 제공자" 정책을 적고, 왜 단일 벤더 종속이 2026년에 비싼 실수인지 설명할 수 있다.

## 문제

제품에 Claude 3.7 Sonnet을 골랐습니다. 이제 이걸 서빙해야 하죠. Anthropic API를 직접 호출할 수도 있고, AWS Bedrock을 통해서 호출할 수도 있고, 게이트웨이를 거칠 수도 있습니다. 직접 API가 가장 단순합니다. Bedrock은 BAA, VPC 엔드포인트, IAM, CloudWatch 귀속을 더합니다. 게이트웨이는 페일오버, 통합 청구, 제공자 간 레이트 리밋을 더합니다.

더 깊은 문제는 카탈로그입니다. 같은 제품에서 Claude와 Llama와 Gemini를 모두 써야 한다면, 한 곳에서 전부 살 수는 없습니다. 그 한 곳이 Bedrock과 Vertex와 Azure OpenAI를 동시에 다 쓰는 곳일 경우를 제외하면요. 하이퍼스케일러는 서로 바꿔 쓸 수 없습니다 — 각자 모델 계층의 소유권에 대해 다른 베팅을 했습니다.

이 레슨은 세 가지 베팅, 지연 시간 격차, FinOps 격차, 그리고 종속(lock-in) 위험을 지도화합니다.

## 개념

### 세 가지 전략

**AWS Bedrock** — 마켓플레이스입니다. Claude(Anthropic), Llama(Meta), Titan(AWS 자체), Stability(이미지), Cohere(임베딩), Mistral, 그리고 이미지와 임베딩 하위 카탈로그. API 하나, IAM 표면 하나, CloudWatch 내보내기 하나. Bedrock의 베팅은 고객이 단일 모델보다 선택권을 더 원한다는 것입니다.

**Azure OpenAI** — 독점 파트너십입니다. GPT-4 / 4o / 5 / o-시리즈, DALL·E, Whisper, 그리고 Azure 데이터센터에서의 OpenAI 모델 파인튜닝을 제공합니다. "Azure OpenAI Service" 카탈로그에는 OpenAI가 아닌 모델이 없습니다 — 그런 모델은 Azure AI Foundry(별도 제품)로 갑니다. Azure의 베팅은 OpenAI가 여전히 프론티어라는 것과, 고객이 그 특정 관계에 대해 엔터프라이즈 통제를 원한다는 것입니다.

**Vertex AI** — Gemini가 먼저고 나머지는 차선입니다. Gemini 1.5 / 2.0 / 2.5 Flash와 Pro, 그리고 Model Garden(서드파티). Vertex의 베팅은 멀티모달 롱 컨텍스트 — 100만 토큰 Gemini 컨텍스트가 차별화 요소입니다.

### 규모에서의 지연 시간 격차

Artificial Analysis는 지속적으로 벤치마크를 돌립니다. 동등한 Llama 3.1 405B 배포(공유 온디맨드)에서 Azure OpenAI의 첫 토큰까지 중앙 지연 시간은 약 50 ms, Bedrock은 약 75 ms입니다. 이 격차는 AWS의 실패가 아니라 용량 모델의 차이입니다. Azure는 PTU(Provisioned Throughput Units)를 팝니다. 이것은 테넌트를 위해 GPU 용량을 예약합니다. Bedrock의 대응물(Provisioned Throughput)도 있지만 단위당 시간 약 $21부터 시작하고, 대부분의 고객은 공유 온디맨드에 머뭅니다.

온디맨드 공유 용량은 다른 모든 고객의 트래픽과 경쟁합니다. 전용 용량은 경쟁하지 않습니다. 제품 SLA가 P99에서 TTFT < 100 ms라면, Azure에서 PTU를 사거나, Bedrock Provisioned Throughput을 사거나, 기본 분산을 감수해야 합니다.

### Provisioned Throughput 경제학

Azure PTU: 추론 컴퓨팅의 예약 블록입니다. 예측 가능한 워크로드에서는 온디맨드 대비 최대 약 70% 절약. 트래픽과 무관하게 시간당 고정 비용 — 놀고 있어도 예약 비용을 냅니다. 손익분기점은 보통 지속 이용률 40~60% 근처입니다.

Bedrock Provisioned Throughput: 모델과 리전에 따라 시간당 $21~$50. 비슷한 산수 — 손익분기는 대략 피크 이용률의 절반. 월간 약정이 필요합니다.

Vertex의 프로비저닝 용량은 Gemini SKU별로 판매되며, 가격은 모델과 리전에 따라 다르고 공개적으로 덜 알려져 있습니다.

### FinOps 표면 — 진짜 차별화 요소

**Bedrock Application Inference Profiles**는 마켓플레이스 중 가장 깔끔한 귀속 방식입니다. 프로필에 `team`, `product`, `feature` 태그를 붙이고, 모든 모델 호출을 그 프로필로 라우팅하면, CloudWatch가 후처리 없이 프로필별 비용을 분류해 냅니다. 2025년에 추가되었고 여전히 하이퍼스케일러 네이티브 중 가장 세밀합니다.

**Vertex**의 귀속은 팀별 프로젝트 + 라벨 everywhere 방식입니다. 각 팀을 GCP 프로젝트로 모델링하고, 모든 리소스에 라벨을 붙이고, BigQuery Billing Export + DataStudio로 롤업합니다. 더 번거롭지만 BigQuery가 비용 데이터에 임의의 SQL을 허용합니다.

**Azure**는 구독/리소스 그룹 스코프 + 태그에 의존하고, PTU 예약이 일급 비용 객체입니다. 태그는 요청이 아니라 리소스 그룹에서 상속되므로, 요청별 귀속에는 Application Insights 커스텀 메트릭이나 헤더를 찍어 주는 게이트웨이가 필요합니다.

패턴을 요약하면: Bedrock이 가장 깔끔한 네이티브, Vertex가 BigQuery 덕에 가장 유연, Azure는 계측하지 않는 한 가장 불투명합니다.

### 종속은 2026년의 리스크

하나의 모델이 지배하던 때에는 단일 하이퍼스케일러 약정도 괜찮았습니다. 2026년에는 프론티어가 매달 움직입니다 — 어느 분기는 Claude 3.7, 다음은 Gemini 2.5, 그다음은 GPT-5. 한 플랫폼에 고정되면 프론티어의 3분의 2에서 배제됩니다.

잘 나가는 팀들이 채택하는 패턴: 제품에 중요한 모든 LLM 호출에는 최소 두 개 제공자. Bedrock + Azure OpenAI가 흔한 조합입니다 — 한쪽에서 Claude, 다른 쪽에서 GPT, 그 사이 페일오버, 같은 게이트웨이. 비용 상승은 무시할 수준입니다(게이트웨이가 최적 경로로 라우팅하기 때문). 장애 시의 가용성 향상(2025년 1월 Azure OpenAI 장애, AWS us-east-1 장애 같은)은 결정적입니다.

### 데이터 레지던시, BAA, 규제 산업

Bedrock: 대부분의 리전에서 BAA; VPC 엔드포인트; 가드레일. 핀테크의 흔한 기본 선택.
Azure OpenAI: HIPAA, SOC 2, ISO 27001; EU 데이터 레지던시; 규제 엔터프라이즈의 기본 선택.
Vertex: HIPAA, GDPR, 리전별 데이터 레지던시; Google Cloud의 컴플라이언스 스택.

세 가지 모두 기본 체크박스는 충족합니다. 차이는 데이터 보존 정책, 로그 처리 방식, 그리고 남용 모니터링이 당신 트래픽을 읽는지 여부(대부분 기본 옵트인; 엔터프라이즈에서는 옵트아웃 가능)에 있습니다.

### 기억해 둘 숫자들

- Llama 3.1 405B 급에서 Azure OpenAI 중앙 TTFT: 약 50 ms (PTU 사용 시).
- Bedrock 온디맨드 중앙 TTFT: 약 75 ms.
- Bedrock Provisioned Throughput: 단위당 시간 $21~$50.
- Azure PTU 손익분기: 지속 이용률 약 40~60%.
- 높은 이용률에서 PTU의 온디맨드 대비 절감: 최대 70%.

```figure
i4-platform-lanes
```

## 활용하기

`code/main.py`는 합성 워크로드에서 세 플랫폼을 비교합니다 — 온디맨드 vs PTU 경제학, TTFT 분산, 비용 귀속 정확도를 모델링합니다. 실행해 보면 PTU가 빛나는 지점과, 마켓플레이스의 모델 폭이 TTFT 격차를 능가하는 지점을 볼 수 있습니다.

## 출시하기

이 레슨은 `outputs/skill-managed-platform-picker.md`를 산출합니다. 워크로드 프로필(필요한 모델, TTFT SLA, 일일 볼륨, 컴플라이언스 요건)이 주어지면, 주 플랫폼, 폴백, FinOps 계측 계획을 추천합니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 70B급 모델에서 Azure PTU가 온디맨드를 이기는 지속 이용률은 얼마인가요? 손익분기를 계산하고 공표된 40~60% 범위와 비교하세요.
2. 당신의 제품에는 Claude 3.7 Sonnet과 GPT-4o가 필요합니다. 두 제공자 배포를 설계하세요 — 어느 쪽을 어느 하이퍼스케일러에 둘지, 앞에 어떤 게이트웨이를 둘지, 페일오버 정책은 무엇인지요?
3. 규제 대상 의료 고객이 BAA, US-East 데이터 레지던시, 100 ms 미만 P99 TTFT를 요구합니다. 플랫폼을 고르고 세 가지 구체적 기능으로 정당화하세요.
4. 이번 달 Bedrock 청구서가 트래픽 변화 없이 4배 올랐다는 걸 발견했습니다. Application Inference Profiles가 없다면 범인을 어떻게 찾겠습니까? 프로필이 있다면 얼마나 걸리나요?
5. Azure OpenAI와 Bedrock 가격 페이지를 읽으세요. 월 1억 토큰 Claude 워크로드에서 어느 쪽이 쌀까요 — 직접 Anthropic API, Bedrock 온디맨드, 아니면 Bedrock Provisioned Throughput?

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| Bedrock | "AWS LLM 서비스" | Claude, Llama, Titan, Mistral, Cohere를 아우르는 모델 마켓플레이스 |
| Azure OpenAI | "Azure의 ChatGPT" | Azure 데이터센터에서 엔터프라이즈 통제를 곁들인 독점적 OpenAI 모델 |
| Vertex AI | "Google의 LLM" | Gemini 우선 플랫폼, 서드파티 모델용 Model Garden |
| PTU | "전용 용량" | Provisioned Throughput Unit — 예약된 추론 GPU, 시간당 가격 |
| Application Inference Profile | "Bedrock 태깅" | 태그가 붙은 제품별 비용/사용량 프로필, CloudWatch 네이티브 |
| Model Garden | "Vertex 카탈로그" | Gemini와 별도인 Vertex AI의 서드파티 모델 섹션 |
| 최소 두 제공자 | "LLM 이중화" | 중요한 모든 LLM 경로를 2개 이상의 하이퍼스케일러에 걸치는 정책 |
| BAA | "HIPAA 서류" | Business Associate Agreement; PHI에 필요; 셋 모두 제공 |
| 남용 모니터링 | "로그 감시자" | 제공자 측에서 프롬프트/출력을 검사하는 안전 기능; 엔터프라이즈는 옵트아웃 가능 |

## 더 읽을거리

- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) — 공식 요금표와 Provisioned Throughput 가격.
- [Azure OpenAI Service Pricing](https://azure.microsoft.com/en-us/pricing/details/azure-openai/) — PTU 경제학과 요금표.
- [Vertex AI Generative AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) — Gemini 등급과 Model Garden 추가 요금.
- [Artificial Analysis LLM Leaderboard](https://artificialanalysis.ai/) — 제공자 간 지속 지연 시간·처리량 벤치마크.
- [The AI Journal — AWS Bedrock vs Azure OpenAI CTO Guide 2026](https://theaijournal.co/2026/03/aws-bedrock-vs-azure-openai/) — 엔터프라이즈 의사결정 프레임워크.
- [Finout — Bedrock vs Vertex vs Azure FinOps](https://www.finout.io/blog/bedrock-vs.-vertex-vs.-azure-cognitive-a-finops-comparison-for-ai-spend) — 귀속 메커니즘의 나란히 비교.
