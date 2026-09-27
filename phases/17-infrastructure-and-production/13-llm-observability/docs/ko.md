> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# LLM 관측 가능성(옵저버빌리티) 스택 선택

> 2026년 관측 가능성 시장은 두 부류로 나뉩니다. 개발 플랫폼(LangSmith, Langfuse, Comet Opik)은 모니터링에 평가(eval), 프롬프트 관리, 세션 리플레이까지 묶어 팝니다. 게이트웨이/계측 도구(Helicone, SigNoz, OpenLLMetry, Phoenix)는 텔레메트리에 집중합니다. Langfuse는 MIT 라이선스 코어에 오픈소스 균형점이 좋습니다(클라우드 무료 월 5만 이벤트). Phoenix는 Elastic License 2.0 아래 OpenTelemetry 네이티브입니다 — 드리프트/RAG 시각화에는 탁월하지만 영구 프로덕션(운영 환경) 백엔드로는 부적합합니다. Arize AX는 제로 카피 Iceberg/Parquet 통합을 내세우며, 모놀리식 관측 도구보다 100배 저렴하다고 주장합니다. LangSmith는 LangChain/LangGraph에서 선두이며, 사용자당 월 $39, 셀프호스팅은 Enterprise 플랜에서만 가능합니다. Helicone은 프록시 기반으로 15-30분이면 세팅되고 월 10만 요청까지 무료이지만, 에이전트 트레이스 깊이는 얕습니다. 흔한 프로덕션 패턴: 게이트웨이(Helicone/Portkey) + 평가 플랫폼(Phoenix/TruLens)을 OpenTelemetry로 이어 붙이는 것입니다.

**유형:** 학습
**언어:** Python (표준 라이브러리, 트레이스 샘플링 시뮬레이터 장난감 버전)
**선수 지식:** 페이즈 17 · 08 (추론 메트릭), 페이즈 14 (에이전트 엔지니어링)
**시간:** 약 60분

## 학습 목표

- 개발 플랫폼(평가 + 프롬프트 + 세션 묶음)과 게이트웨이/텔레메트리 도구(트레이스 + 메트릭만 제공)를 구분할 수 있습니다.
- 여섯 가지 주요 도구(Langfuse, LangSmith, Phoenix, Arize AX, Helicone, Opik)를 라이선스, 가격, 가장 빛나는 사용 사례별로 매핑할 수 있습니다.
- 게이트웨이 도구와 별도의 평가 플랫폼을 결합하게 해주는 OpenTelemetry 접착 패턴을 설명할 수 있습니다.
- 2026년의 비용 결정 요소(Arize AX의 제로 카피 방식 vs 모놀리식 수집)를 언급하고 대략 100배라는 배수를 말할 수 있습니다.

## 문제 상황

LLM 기능을 출시했습니다. 잘 동작합니다. 하지만 프롬프트 실패, 도구 루프, 지연 시간 악화, 비용 폭증, 프롬프트 캐시 적중률을 볼 수가 없습니다. "LLM observability"를 검색하면 여덟 개 도구가 쏟아지는데, 전부 같은 문제를 해결한다면서 서로 다른 세 가지 가격표를 들고 있습니다.

실은 같은 문제를 풀지 않습니다. LangSmith는 "이 LangGraph 실행은 왜 실패했나?"에 답합니다. Phoenix는 "내 RAG 파이프라인이 드리프트 중인가?"에 답합니다. Helicone은 "어느 앱이 토큰을 태우고 있나?"에 답합니다. Langfuse는 "이걸 통째로 셀프호스팅할 수 있나?"에 답합니다. 도구가 다르면 청중도 다릅니다.

선택의 축은 네 가지입니다. 스택(LangChain? 순수 SDK? 멀티 벤더?), 라이선스 허용도(MIT만? Elastic도 OK? 상용 무관?), 예산(무료 티어? 월 $100? 월 $1000?), 셀프호스팅(필수? 있으면 좋음? 절대 안 함?).

## 개념

### 두 부류

**개발 플랫폼**은 관측 가능성에 평가, 프롬프트 관리, 데이터셋 버전 관리, 세션 리플레이를 묶습니다. 실험을 돌리고, 어떤 프롬프트가 통했는지 보고, 새 프롬프트를 기존 우승 프롬프트와 비교해 회귀를 잡습니다. LangSmith, Langfuse, Comet Opik.

**게이트웨이/텔레메트리 도구**는 추론 호출을 계측합니다 — 프롬프트, 응답, 토큰, 지연 시간, 모델, 비용. Helicone, SigNoz, OpenLLMetry, Phoenix. 미니멀리스트 접근이며, OpenTelemetry를 통해 별도의 평가 도구와 결합할 수 있습니다.

### Langfuse — 오픈소스 균형점

- 코어는 Apache / MIT 라이선스, Docker로 셀프호스팅.
- 클라우드 무료 티어: 월 5만 이벤트. 유료: 팀용 월 $29.
- 평가, 프롬프트 관리, 트레이스, 데이터셋. 개발 플랫폼의 네 가지 기능을 모두 무난하게 커버합니다.
- 가장 빛나는 지점: LangSmith급 기능이 필요한데 셀프호스팅이 필수이거나 오픈소스 라이선스를 유지해야 할 때.

### Phoenix (Arize) — 텔레메트리 우선, OpenTelemetry 네이티브

- Elastic License 2.0, 셀프호스팅이 아주 쉽습니다.
- RAG와 드리프트 시각화에 탁월합니다. 임베딩 공간 산점도가 일급 기능으로 제공됩니다.
- 영구 프로덕션 백엔드로 설계되지 않았습니다 — 기본적으로 개발 시점의 관측 도구입니다.
- 가장 빛나는 지점: RAG 파이프라인 개발, 드리프트 디버깅. 프로덕션용으로는 별도 게이트웨이와 짝을 이룹니다.

### Arize AX — 대규모용 카드

- 상용. Iceberg/Parquet를 통한 제로 카피 데이터 레이크 통합.
- 대규모에서 모놀리식 관측 도구(Datadog급)보다 약 100배 저렴하다고 주장합니다. 계산 근거: 트레이스를 여러분의 S3 위 Parquet에 저장하고 Arize가 직접 읽는 구조입니다.
- 가장 빛나는 지점: 하루 1천만 트레이스 초과, 기존 데이터 레이크 보유, Datadog 가격표 없이 LLM 전용 대시보드가 필요할 때.

### LangSmith — LangChain/LangGraph 최우선

- 상용, 사용자당 월 $39. 셀프호스팅은 Enterprise에서만.
- LangChain과 LangGraph 스택에서는 최고 수준입니다. 둘 다 쓰지 않는다면 매력이 떨어집니다.
- 가장 빛나는 지점: LangChain에 올인한 팀, 비용 지불 의사가 있는 팀.

### Helicone — 프록시 기반 미니멀 출발점

- `OPENAI_API_BASE`를 Helicone 프록시로 바꾸는 것만으로 15-30분이면 세팅됩니다.
- MIT 라이선스, 월 10만 요청까지 무료, 유료는 월 $20부터.
- 페일오버, 캐싱, 속도 제한까지 포함 — 게이트웨이 역할도 합니다.
- 에이전트 / 멀티스텝 트레이스의 깊이는 얕습니다.
- 가장 빛나는 지점: 빠른 시작, 단일 스택 앱, 게이트웨이 + 관측을 하나로 해결하고 싶을 때.

### Opik (Comet) — 오픈소스 개발 플랫폼

- Apache 2.0, 완전 오픈소스.
- Comet의 유산이 담긴, Langfuse와 비슷한 기능 세트.
- 가장 빛나는 지점: 이미 Comet을 쓰는 ML 팀이 같은 화면에서 LLM 관측까지 하고 싶을 때.

### SigNoz — OpenTelemetry 우선 풀 APM

- Apache 2.0. 범용 APM에 OpenTelemetry를 통해 LLM까지 처리합니다.
- 가장 빛나는 지점: 여러 서비스와 LLM 호출을 하나의 관측 체계로 묶고 싶을 때.

### 접착제: OpenTelemetry + GenAI 시맨틱 컨벤션

OpenTelemetry는 2025년 말 GenAI 시맨틱 컨벤션(`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`)을 발표했습니다. OTel을 소비하는 도구들은 서로 호환됩니다. 형성되고 있는 프로덕션 패턴은 다음과 같습니다.

1. 모든 LLM 호출에서 GenAI 컨벤션을 적용한 OTel을 내보냅니다.
2. 일상 운영용으로는 게이트웨이(Helicone / Portkey)로 라우팅합니다.
3. 회귀 감지용으로는 평가 플랫폼(Phoenix / Langfuse)에 이중 전송합니다.
4. 장기 분석용으로는 데이터 레이크(Iceberg)에 보관하고 Arize AX나 DuckDB로 조회합니다.

### 함정: 잘못된 계층에서 계측하기

에이전트 프레임워크 안쪽에서 계측하면(예: LangSmith 트레이스 추가) 그 프레임워크에 묶입니다. HTTP/OpenAI SDK 계층에서 계측하면(OpenLLMetry나 여러분의 게이트웨이를 통해) 어디로든 옮길 수 있습니다.

### 샘플링 — 전부 보관할 수는 없습니다

하루 백만 요청을 넘으면 전체 트레이스 보관 비용이 LLM 호출 비용보다 커집니다. 규칙 기반으로 샘플링하세요: 에러는 100%, 고비용은 100%, 성공은 5%. 집계치는 항상 유지하고, 원시 데이터는 롱테일 구간만 유지합니다.

### 기억해야 할 숫자들

- Langfuse 무료 클라우드: 월 5만 이벤트.
- LangSmith: 사용자당 월 $39.
- Helicone 무료: 월 10만 요청.
- Arize AX 주장: 대규모에서 모놀리식 대비 약 100배 저렴.
- OpenTelemetry GenAI 컨벤션: 2025년 출시, 2026년 광범위 채택.

```figure
i4-otel-glue
```

## 활용하기

`code/main.py`는 보관 전략별(100% 수집, 샘플링, 샘플링 + 에러)로 하루 100만 트레이스를 시뮬레이션합니다. 각 전략의 저장 비용과 잃게 되는 것을 보고합니다.

## 출시하기

이 레슨은 `outputs/skill-observability-stack.md`를 산출합니다. 스택, 규모, 예산, 라이선스 입장이 주어지면 도구(들)를 골라줍니다.

## 연습 문제

1. LangChain을 쓰는 팀이 오픈소스 셀프호스팅 관측 도구를 원합니다. Langfuse나 Opik 중 하나를 고르고 근거를 대세요.
2. 하루 500만 트레이스인데 Datadog 견적이 월 $150K라면, Arize AX의 손익분기점을 계산해 보세요.
3. 여러분 조직의 가이드라인이 모든 LLM 호출에 강제해야 할 OpenTelemetry GenAI 속성 집합을 설계해 보세요.
4. Phoenix 하나만으로 프로덕션에 충분한지 논증해 보세요. 언제 충분하지 않습니까?
5. Helicone의 프록시 오버헤드는 20ms입니다. P99 TTFT(첫 토큰까지의 시간)가 300ms라면 감수할 만한가요? SLA가 100ms라면요?

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| OpenLLMetry | "LLM용 OTel" | LLM을 위한 오픈소스 OpenTelemetry 계측 |
| GenAI 컨벤션 | "OTel 속성" | LLM 호출을 위한 표준 OTel 속성 이름 |
| LangSmith | "LangChain 관측 도구" | LangChain 생태계에 묶인 상용 플랫폼 |
| Langfuse | "오픈소스 LangSmith" | 비슷한 기능 세트를 가진 MIT 오픈소스 |
| Phoenix | "Arize 개발 도구" | OpenTelemetry 네이티브 개발/평가 플랫폼 |
| Arize AX | "대규모 관측" | 상용 제로 카피 Iceberg/Parquet 관측 도구 |
| Helicone | "프록시 관측" | LLM 텔레메트리를 모으는 HTTP 프록시 + 게이트웨이 기능 |
| Opik | "Comet LLM" | Comet의 Apache 2.0 오픈소스 개발 플랫폼 |
| 세션 리플레이 | "트레이스 재실행" | 도구 호출까지 포함해 에이전트 세션 전체를 재생 |
| 평가(eval) | "오프라인 테스트" | 레이블 달린 데이터셋 위에 후보 모델/프롬프트를 돌려보기 |

## 더 읽을거리

- [SigNoz — Top LLM Observability Tools 2026](https://signoz.io/comparisons/llm-observability-tools/)
- [Langfuse — Arize AX Alternative analysis](https://langfuse.com/faq/all/best-phoenix-arize-alternatives)
- [PremAI — Setting Up Langfuse, LangSmith, Helicone, Phoenix](https://blog.premai.io/llm-observability-setting-up-langfuse-langsmith-helicone-phoenix/)
- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Arize Phoenix docs](https://docs.arize.com/phoenix)
- [Helicone docs](https://docs.helicone.ai/)
