> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캐싱, 속도 제한, 비용 최적화

> 대부분의 AI 스타트업은 나쁜 모델 때문에 죽지 않습니다. 나쁜 단위 경제학(unit economics) 때문에 죽습니다. GPT-4o 호출 한 번은 몇 센트의 일부에 불과합니다. 하지만 사용자 1만 명이 하루에 10번씩 호출하면, 단돈 한 달러를 벌기도 전에 입력 토큰만으로 $250이 듭니다. 살아남는 회사는 모든 API 호출을 함수 호출이 아니라 금융 거래처럼 다루는 회사입니다.

**유형:** Build
**언어:** Python
**선수 지식:** Phase 11 레슨 09(함수 호출)
**소요 시간:** 약 45분
**관련 문서:** Phase 11 · 15(프롬프트 캐싱) -- 이 레슨은 애플리케이션 계층 캐싱(시맨틱 캐시, 정확 해시 캐시, 모델 라우팅)을 다룹니다. 레슨 15는 프로바이더 계층 프롬프트 캐싱(Anthropic cache_control, OpenAI 자동, Gemini CachedContent)을 다룹니다. 둘을 결합하면 비용을 50-95% 줄일 수 있습니다.

## 학습 목표

- 반복되거나 비슷한 질의를 새 API 호출 대신 캐시에서 처리하는 시맨틱 캐싱 구현하기
- 프로바이더별 요청당 비용을 계산하고, 토큰 기준 속도 제한과 예산 알림 구현하기
- 프롬프트 압축, 모델 라우팅(비싼 모델 vs 싼 모델), 응답 캐싱으로 비용 최적화 계층 만들기
- 질의 유형에 따라 정확 일치, 의미 유사도, 프리픽스 캐싱을 조합한 계층형 캐싱 전략 설계하기

## 문제 상황

RAG 챗봇을 만들었습니다. 아주 멋지게 작동합니다. 사용자들도 좋아합니다.

그러다 인보이스가 도착합니다.

GPT-5는 백만 입력 토큰에 $5, 백만 출력 토큰에 $15입니다. Claude Opus 4.7은 입력 $15 / 출력 $75입니다. Gemini 3 Pro는 입력 $1.25 / 출력 $5입니다. GPT-5-mini는 $0.25/$2입니다. 아래의 가격은 예시이며, 항상 프로바이더의 최신 가격 페이지를 확인하세요.

스타트업을 죽이는 계산은 이렇습니다:

- 일일 활성 사용자 10,000명
- 사용자당 하루 10회 질의
- 질의당 입력 토큰 1,000개 (시스템 프롬프트 + 컨텍스트 + 사용자 메시지)
- 응답당 출력 토큰 500개

**일일 입력 비용:** 10,000 x 10 x 1,000 / 1,000,000 x $2.50 = **$250/일**
**일일 출력 비용:** 10,000 x 10 x 500 / 1,000,000 x $10.00 = **$500/일**
**월간 총액:** **$22,500/월**

그건 LLM 비용만입니다. 여기에 임베딩, 벡터 데이터베이스 호스팅, 인프라가 더해집니다. 챗봇 하나에 월 $30,000을 쳐다보고 있는 겁니다.

잔인한 사실은 이 질의 중 40-60%가 거의 중복이라는 점입니다. 사용자들은 같은 질문을 살짝 다른 표현으로 합니다. 모든 요청에서 동일한 여러분의 시스템 프롬프트는 요청마다 그리고 그리고 매번 과금됩니다. RAG가 검색해 오는 컨텍스트 문서도 같은 주제를 묻는 사용자들 사이에서 반복됩니다.

여러분은 중복되는 계산에 정가를 지불하고 있는 겁니다.

## 개념

### LLM 호출의 비용 해부도

모든 API 호출에는 다섯 가지 비용 구성 요소가 있습니다.

```mermaid
graph LR
    A[사용자 질의] --> B[시스템 프롬프트<br/>500-2000 토큰]
    A --> C[검색된 컨텍스트<br/>500-4000 토큰]
    A --> D[사용자 메시지<br/>50-500 토큰]
    B --> E[입력 비용<br/>$2.50/1M 토큰]
    C --> E
    D --> E
    E --> F[모델 처리]
    F --> G[출력 비용<br/>$10.00/1M 토큰]
```

시스템 프롬프트는 소리 없는 살인자입니다. 요청마다 보내는 1,500토큰짜리 시스템 프롬프트는 그 프리픽스만으로 백만 요청당 $3.75가 듭니다. 하루 10만 요청이면 $375/일 -- 월 $11,250 -- 을 절대 바뀌지 않는 텍스트에 지불하는 셈입니다.

### 프로바이더 캐싱: 기본 할인

2026년 기준 세 주요 프로바이더 모두 프로바이더 측 프롬프트 캐싱을 제공하지만, 동작 방식은 서로 다릅니다. 자세한 내용은 Phase 11 · 15를 참고하세요.

| 프로바이더 | 방식 | 할인율 | 최소 요건 | 캐시 유지 기간 |
|----------|-----------|----------|---------|----------------|
| Anthropic | 명시적 cache_control 마커 | 캐시 히트 시 90% (쓸 때 25% 추가 요금) | 1,024 토큰 (Sonnet/Opus), 2,048 (Haiku) | 기본 5분; 연장 1시간 (쓰기 프리미엄 2배) |
| OpenAI | 자동 프리픽스 매칭 | 캐시 히트 시 50% | 1,024 토큰 | 최선 노력 기준 최대 1시간 |
| Google Gemini | 명시적 CachedContent API | 약 75% 절감 (저장 비용 별도) | 4,096 (Flash) / 32,768 (Pro) | 사용자 설정 TTL |

**Anthropic 방식**은 명시적입니다. 프롬프트의 특정 구간에 `cache_control: {"type": "ephemeral"}` 마커를 붙입니다. 첫 요청은 25% 쓰기 프리미엄을 내고, 같은 프리픽스를 가진 이후 요청은 90% 할인을 받습니다. 평소 $0.005가 드는 2,000토큰 시스템 프롬프트는 캐시 히트 시 $0.000625입니다. 10만 요청이면 하루 $437.50을 아낍니다.

**OpenAI 방식**은 자동입니다. 이전 요청과 일치하는 프롬프트 프리픽스는 50% 할인을 받습니다. 마커가 필요 없습니다. 절충점은 할인율이 낮고 제어가 약한 대신, 구현 노력이 제로라는 것입니다.

### 시맨틱 캐싱: 직접 만드는 캐시 계층

프로바이더 캐싱은 동일한 프리픽스에만 작동합니다. 시맨틱 캐싱은 더 어려운 경우, 즉 의미는 같지만 표현이 다른 질의를 처리합니다.

"반품 정책이 어떻게 되나요?"와 "상품을 어떻게 반품하나요?"는 다른 문자열이지만 의도는 동일합니다. 시맨틱 캐시는 두 질의를 임베딩하고 코사인 유사도를 계산해서, 유사도가 임계값(보통 0.92-0.95)을 넘으면 캐시된 응답을 돌려줍니다.

```mermaid
flowchart TD
    A[사용자 질의] --> B[질의 임베딩]
    B --> C{캐시에 비슷한 질의<br/>가 있는가?}
    C -->|sim > 0.95| D[캐시된 응답 반환]
    C -->|sim < 0.95| E[LLM API 호출]
    E --> F[응답 캐시에 저장<br/>임베딩과 함께]
    F --> G[응답 반환]
    D --> G
```

임베딩 비용은 무시할 수준입니다. OpenAI의 text-embedding-3-small은 백만 토큰에 $0.02입니다. 캐시 확인 비용은 LLM 호출 전체 비용에 비하면 거의 없는 셈입니다.

### 정확 캐싱: 해시해서 찾기

결정론적 호출(temperature=0, 같은 모델, 같은 프롬프트)에는 정확 캐싱이 더 단순하고 빠릅니다. 전체 프롬프트를 해시하고, 캐시를 확인하고, 있으면 돌려줍니다.

이 방식이 완벽하게 작동하는 경우:
- 시스템 프롬프트 + 고정 컨텍스트 + 동일한 사용자 질의
- 동일한 도구 정의를 쓰는 함수 호출
- 같은 문서를 여러 번 처리하는 배치 처리

### 속도 제한: 예산 지키기

속도 제한은 공정함만의 문제가 아닙니다. 생존의 문제입니다.

**토큰 버킷 알고리즘:** 사용자마다 N개 토큰이 담긴 버킷을 주고, 초당 R 비율로 다시 채웁니다. 요청은 버킷에서 토큰을 소비합니다. 버킷이 비어 있으면 요청을 거부합니다. 이렇게 하면 평균 속도를 강제하면서도 버스트(버킷을 한 번에 몰아 쓰기)는 허용됩니다.

**사용자별 할당량:** 티어별로 일일/월간 토큰 한도를 설정합니다.

| 티어 | 일일 토큰 한도 | 분당 최대 요청 | 모델 접근 |
|------|------------------|------------------|-------------|
| Free | 50,000 | 10 | GPT-4o-mini만 |
| Pro | 500,000 | 60 | GPT-4o, Claude Sonnet |
| Enterprise | 5,000,000 | 300 | 전체 모델 |

### 모델 라우팅: 알맞은 일에 알맞은 모델

모든 질의가 GPT-4o를 필요로 하지는 않습니다.

"가게 문 몇 시에 닫아요?"라는 질문에 백만 출력 토큰 $10짜리 모델은 필요 없습니다. 백만 출력 토큰 $0.60의 GPT-4o-mini로도 완벽히 처리합니다. 백만 출력 토큰 $1.25의 Claude Haiku도 처리합니다. 간단한 분류기가 싼 질의는 싼 모델로, 복잡한 질의는 비싼 모델로 보내 주면 됩니다.

```mermaid
flowchart TD
    A[사용자 질의] --> B[복잡도 분류기]
    B -->|단순: 조회, FAQ| C[GPT-4o-mini<br/>1M당 $0.15/$0.60]
    B -->|보통: 분석, 요약| D[Claude Sonnet<br/>1M당 $3.00/$15.00]
    B -->|복잡: 추론, 코드| E[GPT-4o / Claude Opus<br/>$2.50/$10.00+]
```

잘 튜닝된 라우터는 모델 비용만 40-70% 아낍니다.

### 비용 추적: 돈이 어디로 가는지 알기

측정하지 않는 것은 최적화할 수 없습니다. 모든 API 호출을 다음 항목과 함께 기록하세요:

- 타임스탬프
- 모델 이름
- 입력 토큰
- 출력 토큰
- 지연 시간 (ms)
- 계산된 비용 ($)
- 사용자 ID
- 캐시 히트/미스
- 요청 카테고리

이 데이터는 어떤 기능이 비싼지, 어떤 사용자가 많이 쓰는지, 캐싱이 어디에 가장 큰 효과를 주는지 보여 줍니다.

### 배칭: 대량 할인

OpenAI의 Batch API는 요청을 비동기로 처리하고 50% 할인을 줍니다. 최대 50,000개 요청을 묶음으로 제출하면 24시간 안에 결과가 돌아옵니다.

배칭에 적합한 작업:
- 야간 문서 처리
- 대량 분류
- 평가 실행
- 데이터 보강 파이프라인

적합하지 않은 작업: 실시간 사용자 대면 질의 (지연 시간이 중요합니다).

### 예산 알림과 서킷 브레이커

서킷 브레이커는 한도에 도달하면 지출을 멈춥니다. 없으면 버그나 어뷰징이 몇 시간 만에 월간 예산을 태워 버릴 수 있습니다.

임계값 세 개를 설정하세요:
1. **경고** (예산의 70%): 알림 전송
2. **스로틀** (예산의 85%): 싼 모델만 사용하도록 전환
3. **정지** (예산의 95%): 새 요청 거부, 캐시된 응답만 제공

### 최적화 스택

아래 기법을 순서대로 적용하세요. 각 계층은 이전 계층 위에 효과가 누적됩니다.

| 계층 | 기법 | 일반적인 절감 | 구현 노력 |
|-------|-----------|----------------|----------------------|
| 1 | 프로바이더 프롬프트 캐싱 | 30-50% | 낮음 (캐시 마커 추가) |
| 2 | 정확 캐싱 | 10-20% | 낮음 (해시 + 딕셔너리) |
| 3 | 시맨틱 캐싱 | 15-30% | 중간 (임베딩 + 유사도) |
| 4 | 모델 라우팅 | 40-70% | 중간 (분류기) |
| 5 | 속도 제한 | 예산 보호 | 낮음 (토큰 버킷) |
| 6 | 프롬프트 압축 | 10-30% | 중간 (프롬프트 재작성) |
| 7 | 배칭 | 해당 작업 50% | 낮음 (배치 API) |

1-5 계층을 적용한 RAG 앱은 보통 월 $22,500에서 월 $4,000-6,000으로 비용을 줄입니다. 런웨이를 태우는 것과 사업을 만드는 것의 차이입니다.

### 실제 절감 효과: 최적화 전후

일일 활성 사용자 1만 명인 RAG 챗봇의 실제 세부 내역입니다.

| 지표 | 최적화 전 | 최적화 후 | 절감 |
|--------|--------------------|--------------------|---------|
| 월간 LLM 비용 | $22,500 | $5,200 | 77% |
| 질의당 평균 비용 | $0.0075 | $0.0017 | 77% |
| 캐시 히트율 | 0% | 52% | -- |
| mini로 라우팅된 질의 | 0% | 65% | -- |
| P95 지연 시간 | 2,800ms | 900ms (캐시 히트: 50ms) | 68% |
| 월간 임베딩 비용 | $0 | $180 | (신규 비용) |
| 월간 총 비용 | $22,500 | $5,380 | 76% |

시맨틱 캐싱의 임베딩 비용(월 $180)은 캐시 히트가 시작되면 한 시간 안에 본전을 뽑습니다.

```figure
semantic-cache
```

## 직접 만들기

### 단계 1: 비용 계산기

주요 모델의 현재 가격을 알고 있는 토큰 비용 계산기를 만듭니다.

```python
import hashlib
import time
import json
import math
from dataclasses import dataclass, field


MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00, "cached_input": 1.25},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "cached_input": 0.075},
    "gpt-4.1": {"input": 2.00, "output": 8.00, "cached_input": 0.50},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60, "cached_input": 0.10},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40, "cached_input": 0.025},
    "o3": {"input": 2.00, "output": 8.00, "cached_input": 0.50},
    "o3-mini": {"input": 1.10, "output": 4.40, "cached_input": 0.55},
    "o4-mini": {"input": 1.10, "output": 4.40, "cached_input": 0.275},
    "claude-opus-4": {"input": 15.00, "output": 75.00, "cached_input": 1.50},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00, "cached_input": 0.30},
    "claude-haiku-3.5": {"input": 0.80, "output": 4.00, "cached_input": 0.08},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00, "cached_input": 0.3125},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "cached_input": 0.0375},
}


def calculate_cost(model, input_tokens, output_tokens, cached_input_tokens=0):
    if model not in MODEL_PRICING:
        return {"error": f"Unknown model: {model}"}
    pricing = MODEL_PRICING[model]
    non_cached = input_tokens - cached_input_tokens
    input_cost = (non_cached / 1_000_000) * pricing["input"]
    cached_cost = (cached_input_tokens / 1_000_000) * pricing["cached_input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total = input_cost + cached_cost + output_cost
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_input_tokens,
        "input_cost": round(input_cost, 6),
        "cached_input_cost": round(cached_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total, 6),
    }
```

### 단계 2: 정확 캐시

전체 프롬프트를 해시해서 동일한 요청에는 캐시된 응답을 돌려줍니다.

```python
class ExactCache:
    def __init__(self, max_size=1000, ttl_seconds=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _hash(self, model, messages, temperature):
        key_data = json.dumps({"model": model, "messages": messages, "temperature": temperature}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, model, messages, temperature=0.0):
        if temperature > 0:
            self.misses += 1
            return None
        key = self._hash(model, messages, temperature)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                self.hits += 1
                entry["access_count"] += 1
                return entry["response"]
            del self.cache[key]
        self.misses += 1
        return None

    def put(self, model, messages, temperature, response):
        if temperature > 0:
            return
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        key = self._hash(model, messages, temperature)
        self.cache[key] = {
            "response": response,
            "timestamp": time.time(),
            "access_count": 1,
        }

    def stats(self):
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total > 0 else 0,
            "cache_size": len(self.cache),
        }
```

### 단계 3: 시맨틱 캐시

질의를 임베딩하고, 유사도가 임계값을 넘으면 캐시된 응답을 돌려줍니다.

```python
def simple_embed(text):
    words = text.lower().split()
    vocab = {}
    for w in words:
        vocab[w] = vocab.get(w, 0) + 1
    norm = math.sqrt(sum(v * v for v in vocab.values()))
    if norm == 0:
        return {}
    return {k: v / norm for k, v in vocab.items()}


def cosine_similarity(a, b):
    if not a or not b:
        return 0.0
    all_keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in all_keys)
    return dot


class SemanticCache:
    def __init__(self, similarity_threshold=0.85, max_size=500, ttl_seconds=3600):
        self.entries = []
        self.threshold = similarity_threshold
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def get(self, query):
        query_embedding = simple_embed(query)
        now = time.time()
        best_match = None
        best_sim = 0.0
        for entry in self.entries:
            if now - entry["timestamp"] > self.ttl:
                continue
            sim = cosine_similarity(query_embedding, entry["embedding"])
            if sim > best_sim:
                best_sim = sim
                best_match = entry
        if best_match and best_sim >= self.threshold:
            self.hits += 1
            best_match["access_count"] += 1
            return {"response": best_match["response"], "similarity": round(best_sim, 4), "original_query": best_match["query"]}
        self.misses += 1
        return None

    def put(self, query, response):
        if len(self.entries) >= self.max_size:
            self.entries.sort(key=lambda e: e["timestamp"])
            self.entries.pop(0)
        self.entries.append({
            "query": query,
            "embedding": simple_embed(query),
            "response": response,
            "timestamp": time.time(),
            "access_count": 1,
        })

    def stats(self):
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total > 0 else 0,
            "cache_size": len(self.entries),
        }
```

### 단계 4: 속도 제한기

사용자별 할당량이 있는 토큰 버킷 속도 제한기입니다.

```python
class TokenBucketRateLimiter:
    def __init__(self):
        self.buckets = {}
        self.tiers = {
            "free": {"capacity": 50_000, "refill_rate": 500, "max_requests_per_min": 10},
            "pro": {"capacity": 500_000, "refill_rate": 5_000, "max_requests_per_min": 60},
            "enterprise": {"capacity": 5_000_000, "refill_rate": 50_000, "max_requests_per_min": 300},
        }

    def _get_bucket(self, user_id, tier="free"):
        if user_id not in self.buckets:
            tier_config = self.tiers.get(tier, self.tiers["free"])
            self.buckets[user_id] = {
                "tokens": tier_config["capacity"],
                "capacity": tier_config["capacity"],
                "refill_rate": tier_config["refill_rate"],
                "last_refill": time.time(),
                "request_timestamps": [],
                "max_rpm": tier_config["max_requests_per_min"],
                "tier": tier,
                "total_tokens_used": 0,
            }
        return self.buckets[user_id]

    def _refill(self, bucket):
        now = time.time()
        elapsed = now - bucket["last_refill"]
        refill = int(elapsed * bucket["refill_rate"])
        if refill > 0:
            bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + refill)
            bucket["last_refill"] = now

    def check(self, user_id, tokens_needed, tier="free"):
        bucket = self._get_bucket(user_id, tier)
        self._refill(bucket)
        now = time.time()
        bucket["request_timestamps"] = [t for t in bucket["request_timestamps"] if now - t < 60]
        if len(bucket["request_timestamps"]) >= bucket["max_rpm"]:
            return {"allowed": False, "reason": "rate_limit", "retry_after_seconds": 60 - (now - bucket["request_timestamps"][0])}
        if bucket["tokens"] < tokens_needed:
            deficit = tokens_needed - bucket["tokens"]
            wait = deficit / bucket["refill_rate"]
            return {"allowed": False, "reason": "token_limit", "tokens_available": bucket["tokens"], "retry_after_seconds": round(wait, 1)}
        return {"allowed": True, "tokens_available": bucket["tokens"]}

    def consume(self, user_id, tokens_used, tier="free"):
        bucket = self._get_bucket(user_id, tier)
        bucket["tokens"] -= tokens_used
        bucket["request_timestamps"].append(time.time())
        bucket["total_tokens_used"] += tokens_used

    def get_usage(self, user_id):
        if user_id not in self.buckets:
            return {"error": "User not found"}
        b = self.buckets[user_id]
        return {
            "user_id": user_id,
            "tier": b["tier"],
            "tokens_remaining": b["tokens"],
            "capacity": b["capacity"],
            "total_tokens_used": b["total_tokens_used"],
            "utilization": round(b["total_tokens_used"] / b["capacity"], 4) if b["capacity"] else 0,
        }
```

### 단계 5: 비용 추적기

모든 호출을 기록하고 누적 합계를 계산합니다.

```python
class CostTracker:
    def __init__(self, monthly_budget=1000.0):
        self.logs = []
        self.monthly_budget = monthly_budget
        self.alerts = []

    def log_call(self, model, input_tokens, output_tokens, cached_input_tokens=0, latency_ms=0, user_id="anonymous", cache_status="miss"):
        cost = calculate_cost(model, input_tokens, output_tokens, cached_input_tokens)
        entry = {
            "timestamp": time.time(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_input_tokens": cached_input_tokens,
            "latency_ms": latency_ms,
            "cost": cost["total_cost"],
            "user_id": user_id,
            "cache_status": cache_status,
        }
        self.logs.append(entry)
        self._check_budget()
        return entry

    def _check_budget(self):
        total = self.total_cost()
        pct = total / self.monthly_budget if self.monthly_budget > 0 else 0
        if pct >= 0.95 and not any(a["level"] == "stop" for a in self.alerts):
            self.alerts.append({"level": "stop", "message": f"Budget 95% consumed: ${total:.2f}/${self.monthly_budget:.2f}", "timestamp": time.time()})
        elif pct >= 0.85 and not any(a["level"] == "throttle" for a in self.alerts):
            self.alerts.append({"level": "throttle", "message": f"Budget 85% consumed: ${total:.2f}/${self.monthly_budget:.2f}", "timestamp": time.time()})
        elif pct >= 0.70 and not any(a["level"] == "warning" for a in self.alerts):
            self.alerts.append({"level": "warning", "message": f"Budget 70% consumed: ${total:.2f}/${self.monthly_budget:.2f}", "timestamp": time.time()})

    def total_cost(self):
        return round(sum(e["cost"] for e in self.logs), 6)

    def cost_by_model(self):
        by_model = {}
        for e in self.logs:
            m = e["model"]
            if m not in by_model:
                by_model[m] = {"calls": 0, "cost": 0, "input_tokens": 0, "output_tokens": 0}
            by_model[m]["calls"] += 1
            by_model[m]["cost"] = round(by_model[m]["cost"] + e["cost"], 6)
            by_model[m]["input_tokens"] += e["input_tokens"]
            by_model[m]["output_tokens"] += e["output_tokens"]
        return by_model

    def cache_savings(self):
        cache_hits = [e for e in self.logs if e["cache_status"] == "hit"]
        if not cache_hits:
            return {"saved": 0, "cache_hits": 0}
        saved = 0
        for e in cache_hits:
            full_cost = calculate_cost(e["model"], e["input_tokens"], e["output_tokens"])
            saved += full_cost["total_cost"]
        return {"saved": round(saved, 4), "cache_hits": len(cache_hits)}

    def summary(self):
        if not self.logs:
            return {"total_calls": 0, "total_cost": 0}
        total_latency = sum(e["latency_ms"] for e in self.logs)
        cache_hits = sum(1 for e in self.logs if e["cache_status"] == "hit")
        return {
            "total_calls": len(self.logs),
            "total_cost": self.total_cost(),
            "avg_cost_per_call": round(self.total_cost() / len(self.logs), 6),
            "avg_latency_ms": round(total_latency / len(self.logs), 1),
            "cache_hit_rate": round(cache_hits / len(self.logs), 4),
            "cost_by_model": self.cost_by_model(),
            "cache_savings": self.cache_savings(),
            "budget_remaining": round(self.monthly_budget - self.total_cost(), 2),
            "budget_utilization": round(self.total_cost() / self.monthly_budget, 4) if self.monthly_budget > 0 else 0,
            "alerts": self.alerts,
        }
```

### 단계 6: 모델 라우터

질의를 처리할 수 있는 가장 싼 모델로 보냅니다.

```python
SIMPLE_KEYWORDS = ["what time", "hours", "address", "phone", "price", "return policy", "hello", "hi", "thanks", "yes", "no"]
COMPLEX_KEYWORDS = ["analyze", "compare", "explain why", "write code", "debug", "architect", "design", "trade-off", "evaluate"]


def classify_complexity(query):
    q = query.lower()
    if len(q.split()) <= 5 or any(kw in q for kw in SIMPLE_KEYWORDS):
        return "simple"
    if any(kw in q for kw in COMPLEX_KEYWORDS):
        return "complex"
    return "medium"


def route_model(query, tier="pro"):
    complexity = classify_complexity(query)
    routing_table = {
        "simple": {"free": "gpt-4.1-nano", "pro": "gpt-4o-mini", "enterprise": "gpt-4o-mini"},
        "medium": {"free": "gpt-4o-mini", "pro": "claude-sonnet-4", "enterprise": "claude-sonnet-4"},
        "complex": {"free": "gpt-4o-mini", "pro": "gpt-4o", "enterprise": "claude-opus-4"},
    }
    model = routing_table[complexity].get(tier, "gpt-4o-mini")
    return {"query": query, "complexity": complexity, "model": model, "tier": tier}
```

### 단계 7: 데모 실행

```python
def simulate_llm_call(model, query):
    input_tokens = len(query.split()) * 4 + 500
    output_tokens = 150 + (len(query.split()) * 2)
    latency = 200 + (output_tokens * 2)
    return {
        "model": model,
        "response": f"[Simulated {model} response to: {query[:50]}...]",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency,
    }


def run_demo():
    print("=" * 60)
    print("  Caching, Rate Limiting & Cost Optimization Demo")
    print("=" * 60)

    print("\n--- Model Pricing ---")
    for model, pricing in list(MODEL_PRICING.items())[:6]:
        cost_1k = calculate_cost(model, 1000, 500)
        print(f"  {model}: ${cost_1k['total_cost']:.6f} per 1K in + 500 out")

    print("\n--- Cost Comparison: 100K Requests ---")
    for model in ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "claude-haiku-3.5"]:
        cost = calculate_cost(model, 1000 * 100_000, 500 * 100_000)
        print(f"  {model}: ${cost['total_cost']:.2f}")

    print("\n--- Anthropic Cache Savings ---")
    no_cache = calculate_cost("claude-sonnet-4", 2000, 500, 0)
    with_cache = calculate_cost("claude-sonnet-4", 2000, 500, 1500)
    saving = no_cache["total_cost"] - with_cache["total_cost"]
    print(f"  Without cache: ${no_cache['total_cost']:.6f}")
    print(f"  With 1500 cached tokens: ${with_cache['total_cost']:.6f}")
    print(f"  Savings per call: ${saving:.6f} ({saving/no_cache['total_cost']*100:.1f}%)")

    exact_cache = ExactCache(max_size=100, ttl_seconds=300)
    semantic_cache = SemanticCache(similarity_threshold=0.75, max_size=100)
    rate_limiter = TokenBucketRateLimiter()
    tracker = CostTracker(monthly_budget=100.0)

    print("\n--- Exact Cache ---")
    messages_1 = [{"role": "user", "content": "What is the return policy?"}]
    result = exact_cache.get("gpt-4o-mini", messages_1, 0.0)
    print(f"  First lookup: {'HIT' if result else 'MISS'}")
    exact_cache.put("gpt-4o-mini", messages_1, 0.0, "You can return items within 30 days.")
    result = exact_cache.get("gpt-4o-mini", messages_1, 0.0)
    print(f"  Second lookup: {'HIT' if result else 'MISS'} -> {result}")
    result = exact_cache.get("gpt-4o-mini", messages_1, 0.7)
    print(f"  With temp=0.7: {'HIT' if result else 'MISS (non-deterministic, skip cache)'}")
    print(f"  Stats: {exact_cache.stats()}")

    print("\n--- Semantic Cache ---")
    test_queries = [
        ("What is the return policy?", "Items can be returned within 30 days with receipt."),
        ("How do I return an item?", None),
        ("What are your store hours?", "We are open 9am-9pm Monday through Saturday."),
        ("When does the store open?", None),
        ("Tell me about quantum computing", "Quantum computers use qubits..."),
        ("Explain quantum mechanics", None),
    ]
    for query, response in test_queries:
        cached = semantic_cache.get(query)
        if cached:
            print(f"  '{query[:40]}' -> CACHE HIT (sim={cached['similarity']}, original='{cached['original_query'][:40]}')")
        elif response:
            semantic_cache.put(query, response)
            print(f"  '{query[:40]}' -> MISS (stored)")
        else:
            print(f"  '{query[:40]}' -> MISS (no match)")
    print(f"  Stats: {semantic_cache.stats()}")

    print("\n--- Rate Limiting ---")
    for i in range(12):
        check = rate_limiter.check("user_1", 1000, "free")
        if check["allowed"]:
            rate_limiter.consume("user_1", 1000, "free")
        status = "OK" if check["allowed"] else f"BLOCKED ({check['reason']})"
        if i < 5 or not check["allowed"]:
            print(f"  Request {i+1}: {status}")
    print(f"  Usage: {rate_limiter.get_usage('user_1')}")

    print("\n--- Model Routing ---")
    routing_queries = [
        "What time do you close?",
        "Summarize this quarterly earnings report",
        "Analyze the trade-offs between microservices and monoliths",
        "Hello",
        "Write code for a binary search tree with deletion",
    ]
    for q in routing_queries:
        route = route_model(q, "pro")
        print(f"  '{q[:50]}' -> {route['model']} ({route['complexity']})")

    print("\n--- Full Pipeline: Before vs After Optimization ---")
    queries = [
        "What is the return policy?",
        "How do I return something?",
        "What are your hours?",
        "When do you open?",
        "Explain the difference between TCP and UDP",
        "Compare TCP vs UDP protocols",
        "Hello",
        "What is your phone number?",
        "Write a Python function to sort a list",
        "Analyze the pros and cons of serverless architecture",
    ]

    print("\n  [Before: no caching, single model (gpt-4o)]")
    tracker_before = CostTracker(monthly_budget=1000.0)
    for q in queries:
        result = simulate_llm_call("gpt-4o", q)
        tracker_before.log_call("gpt-4o", result["input_tokens"], result["output_tokens"], latency_ms=result["latency_ms"], cache_status="miss")
    before = tracker_before.summary()
    print(f"  Total cost: ${before['total_cost']:.6f}")
    print(f"  Avg cost/call: ${before['avg_cost_per_call']:.6f}")
    print(f"  Avg latency: {before['avg_latency_ms']}ms")

    print("\n  [After: caching + routing + rate limiting]")
    exact_c = ExactCache()
    semantic_c = SemanticCache(similarity_threshold=0.75)
    tracker_after = CostTracker(monthly_budget=1000.0)

    for q in queries:
        messages = [{"role": "user", "content": q}]
        cached = exact_c.get("gpt-4o", messages, 0.0)
        if cached:
            tracker_after.log_call("gpt-4o-mini", 0, 0, latency_ms=5, cache_status="hit")
            continue
        sem_cached = semantic_c.get(q)
        if sem_cached:
            tracker_after.log_call("gpt-4o-mini", 0, 0, latency_ms=15, cache_status="hit")
            continue
        route = route_model(q)
        result = simulate_llm_call(route["model"], q)
        tracker_after.log_call(route["model"], result["input_tokens"], result["output_tokens"], latency_ms=result["latency_ms"], cache_status="miss")
        exact_c.put(route["model"], messages, 0.0, result["response"])
        semantic_c.put(q, result["response"])

    after = tracker_after.summary()
    print(f"  Total cost: ${after['total_cost']:.6f}")
    print(f"  Avg cost/call: ${after['avg_cost_per_call']:.6f}")
    print(f"  Avg latency: {after['avg_latency_ms']}ms")
    print(f"  Cache hit rate: {after['cache_hit_rate']:.0%}")

    if before["total_cost"] > 0:
        savings_pct = (1 - after["total_cost"] / before["total_cost"]) * 100
        print(f"\n  SAVINGS: {savings_pct:.1f}% cost reduction")
        print(f"  Latency improvement: {(1 - after['avg_latency_ms'] / before['avg_latency_ms']) * 100:.1f}% faster")

    print("\n--- Budget Alerts Demo ---")
    alert_tracker = CostTracker(monthly_budget=0.01)
    for i in range(5):
        alert_tracker.log_call("gpt-4o", 5000, 2000, latency_ms=500)
    print(f"  Total spent: ${alert_tracker.total_cost():.6f} / ${alert_tracker.monthly_budget}")
    for alert in alert_tracker.alerts:
        print(f"  ALERT [{alert['level'].upper()}]: {alert['message']}")

    print("\n--- Cost Breakdown by Model ---")
    multi_tracker = CostTracker(monthly_budget=500.0)
    for _ in range(50):
        multi_tracker.log_call("gpt-4o-mini", 800, 200, latency_ms=150)
    for _ in range(30):
        multi_tracker.log_call("claude-sonnet-4", 1500, 500, latency_ms=400)
    for _ in range(10):
        multi_tracker.log_call("gpt-4o", 2000, 800, latency_ms=600)
    for _ in range(10):
        multi_tracker.log_call("claude-opus-4", 3000, 1000, latency_ms=1200)
    breakdown = multi_tracker.cost_by_model()
    for model, data in sorted(breakdown.items(), key=lambda x: x[1]["cost"], reverse=True):
        print(f"  {model}: {data['calls']} calls, ${data['cost']:.6f}, {data['input_tokens']:,} in / {data['output_tokens']:,} out")
    print(f"  Total: ${multi_tracker.total_cost():.6f}")

    print("\n" + "=" * 60)
    print("  Demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
```

## 활용하기

### Anthropic 프롬프트 캐싱

```python
# import anthropic
#
# client = anthropic.Anthropic()
#
# response = client.messages.create(
#     model="claude-sonnet-5",
#     max_tokens=1024,
#     system=[
#         {
#             "type": "text",
#             "text": "You are a helpful customer support agent for Acme Corp...",
#             "cache_control": {"type": "ephemeral"},
#         }
#     ],
#     messages=[{"role": "user", "content": "What is the return policy?"}],
# )
#
# print(f"Input tokens: {response.usage.input_tokens}")
# print(f"Cache creation tokens: {response.usage.cache_creation_input_tokens}")
# print(f"Cache read tokens: {response.usage.cache_read_input_tokens}")
```

첫 호출은 캐시에 기록합니다(25% 프리미엄). 이후 같은 시스템 프롬프트 프리픽스를 쓰는 모든 호출은 캐시에서 읽습니다(90% 할인). 캐시는 5분 동안 유지되며, 히트할 때마다 타이머가 초기화됩니다.

### OpenAI 자동 캐싱

```python
# from openai import OpenAI
#
# client = OpenAI()
#
# response = client.chat.completions.create(
#     model="gpt-4o",
#     messages=[
#         {"role": "system", "content": "You are a helpful customer support agent..."},
#         {"role": "user", "content": "What is the return policy?"},
#     ],
# )
#
# print(f"Prompt tokens: {response.usage.prompt_tokens}")
# print(f"Cached tokens: {response.usage.prompt_tokens_details.cached_tokens}")
# print(f"Completion tokens: {response.usage.completion_tokens}")
```

OpenAI는 자동으로 캐싱합니다. 최근 요청과 일치하는 1,024토큰 이상의 프롬프트 프리픽스는 50% 할인을 받습니다. 코드 변경이 필요 없습니다 -- 동작 여부는 응답의 `prompt_tokens_details.cached_tokens`를 확인하면 됩니다.

### OpenAI Batch API

```python
# import json
# from openai import OpenAI
#
# client = OpenAI()
#
# requests = []
# for i, query in enumerate(queries):
#     requests.append({
#         "custom_id": f"request-{i}",
#         "method": "POST",
#         "url": "/v1/chat/completions",
#         "body": {
#             "model": "gpt-4o-mini",
#             "messages": [{"role": "user", "content": query}],
#         },
#     })
#
# with open("batch_input.jsonl", "w") as f:
#     for r in requests:
#         f.write(json.dumps(r) + "\n")
#
# batch_file = client.files.create(file=open("batch_input.jsonl", "rb"), purpose="batch")
# batch = client.batches.create(input_file_id=batch_file.id, endpoint="/v1/chat/completions", completion_window="24h")
# print(f"Batch ID: {batch.id}, Status: {batch.status}")
```

Batch API는 모든 토큰에 50% 정액 할인을 줍니다. 결과는 24시간 안에 도착합니다. 평가, 데이터 레이블링, 대량 요약 같은 실시간이 아닌 워크로드에 딱 맞습니다.

### Redis를 쓰는 프로덕션용 시맨틱 캐시

```python
# import redis
# import numpy as np
# from openai import OpenAI
#
# r = redis.Redis()
# client = OpenAI()
#
# def get_embedding(text):
#     response = client.embeddings.create(model="text-embedding-3-small", input=text)
#     return response.data[0].embedding
#
# def semantic_cache_lookup(query, threshold=0.95):
#     query_emb = np.array(get_embedding(query))
#     keys = r.keys("cache:emb:*")
#     best_sim, best_key = 0, None
#     for key in keys:
#         stored_emb = np.frombuffer(r.get(key), dtype=np.float32)
#         sim = np.dot(query_emb, stored_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(stored_emb))
#         if sim > best_sim:
#             best_sim, best_key = sim, key
#     if best_sim >= threshold and best_key:
#         response_key = best_key.decode().replace("cache:emb:", "cache:resp:")
#         return r.get(response_key).decode()
#     return None
```

프로덕션에서는 선형 스캔을 벡터 인덱스(Redis Vector Search, Pinecone, pgvector)로 바꾸세요. 선형 스캔은 엔트리 1,000개 미만에서 동작합니다. 그 이상에서는 O(log n) 조회를 위해 ANN(근사 최근접 이웃)을 쓰세요.

## 출시하기

이 레슨은 `outputs/prompt-cost-optimizer.md`를 만듭니다 -- LLM 애플리케이션을 분석하고 예상 절감액과 함께 구체적인 비용 최적화를 추천하는 재사용 가능한 프롬프트입니다.

또한 `outputs/skill-cost-patterns.md`도 만듭니다 -- 사용 사례에 맞는 캐싱 전략, 속도 제한 설정, 모델 라우팅 규칙을 고르기 위한 의사 결정 프레임워크입니다.

## 연습 문제

1. **시맨틱 캐시에 LRU 방출 구현하기.** 가장 오래된 것 먼저 버리는 방식을 LRU(최근 최소 사용)로 바꿔 보세요. 엔트리마다 마지막 접근 시간을 추적하고, 캐시가 가득 차면 접근 시간이 가장 오래된 엔트리를 버립니다. 100개 질의에 대해 두 전략의 히트율을 비교하세요.

2. **비용 예측 도구 만들기.** API 호출 로그(CostTracker 로그)가 주어지면, 최근 7일 이동평균 기준으로 월간 비용을 예측하세요. 평일/주말 패턴도 반영합니다. 예측 월간 비용이 예산을 20% 이상 초과하면 알림을 발생시키세요.

3. **계층형 시맨틱 캐싱 구현하기.** 유사도 임계값 두 개를 쓰세요. 0.98은 높은 확신 히트(즉시 반환), 0.90은 중간 확신 히트("과거의 비슷한 질문을 기준으로 하면..."이라는 안내를 붙여 반환)입니다. 각 히트가 어느 계층에서 왔는지 추적하고 사용자 만족도 차이를 측정하세요.

4. **모델 라우팅 분류기 만들기.** 키워드 기반 분류기를 임베딩 기반으로 바꿔 보세요. 레이블된 질의 50개(simple/medium/complex)를 임베딩한 다음, 가장 가까운 레이블 예시를 찾아 새 질의를 분류합니다. 테스트 질의 20개에 대해 분류 정확도를 측정하세요.

5. **단계별 성능 저하가 있는 서킷 브레이커 구현하기.** 예산 70%에서 경고를 기록합니다. 85%에서 모든 라우팅을 자동으로 가장 싼 모델(gpt-4o-mini)로 전환합니다. 95%에서는 캐시된 응답만 제공하고 새 질의를 거부합니다. $1.00 예산으로 1,000개 요청을 시뮬레이션해서 각 임계값이 올바르게 작동하는지 확인하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|----------------------|
| 프롬프트 캐싱 | "시스템 프롬프트 캐시" | 반복되는 프롬프트 프리픽스에 할인을 주는 프로바이더 수준 캐싱 (Anthropic 90%, OpenAI 50%) -- OpenAI는 코드 변경 불필요, Anthropic은 명시적 마커 필요 |
| 시맨틱 캐싱 | "스마트 캐싱" | 질의를 임베딩하고 과거 질의와의 유사도를 계산해서, 유사도가 임계값을 넘으면 캐시된 응답을 돌려주는 것 -- 정확 매칭이 놓치는 어휘만 다른 표현을 잡아냄 |
| 정확 캐싱 | "해시 캐싱" | 전체 프롬프트(모델 + 메시지 + temperature)를 해시해서 동일한 입력에는 캐시된 응답을 돌려주는 것 -- temperature=0 결정론적 호출에서만 동작 |
| 토큰 버킷 | "속도 제한기" | 사용자마다 N개 토큰 버킷을 주고 초당 R 비율로 다시 채우는 알고리즘 -- 평균 속도 R을 강제하면서 최대 N까지 버스트 허용 |
| 모델 라우팅 | "짠 라우팅" | 분류기로 단순 질의는 싼 모델(GPT-4o-mini, Haiku)에, 복잡한 질의는 비싼 모델(GPT-4o, Opus)에 보내는 것 -- 모델 비용 40-70% 절감 |
| 비용 추적 | "미터링" | 모든 API 호출을 모델, 토큰, 지연 시간, 비용, 사용자 ID와 함께 기록해서 돈이 어디로 가는지, 어떤 기능이 비싼지 정확히 아는 것 |
| 서킷 브레이커 | "킬 스위치" | 지출이 예산 한도에 가까워지면 서비스를 자동으로 저하시키거나(싼 모델, 캐시 전용) 요청을 완전히 멈추는 것 |
| Batch API | "대량 할인" | OpenAI의 비동기 처리 50% 할인 -- 최대 50,000개 요청 제출, 24시간 내 결과 수령 |
| 프롬프트 압축 | "토큰 다이어트" | 의미를 유지하면서 시스템 프롬프트와 컨텍스트를 더 적은 토큰으로 재작성하는 것 -- 짧은 프롬프트는 비용도 덜 들고 성능이 더 나은 경우가 많음 |
| 캐시 히트율 | "캐시 효율" | LLM을 호출하는 대신 캐시에서 처리된 요청의 비율 -- 프로덕션 챗봇에서 40-60%가 일반적이며, 비용도 비례해서 절감됨 |

## 더 읽을거리

- [Anthropic 프롬프트 캐싱 가이드](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) -- Anthropic의 명시적 cache_control 마커, 가격, 캐시 수명 동작에 관한 공식 문서
- [OpenAI 프롬프트 캐싱](https://platform.openai.com/docs/guides/prompt-caching) -- OpenAI의 자동 캐싱, usage 필드로 캐시 히트 확인하는 방법, 최소 프리픽스 길이
- [OpenAI Batch API](https://platform.openai.com/docs/guides/batch) -- 비동기 처리 50% 할인, JSONL 형식, 24시간 처리 윈도우, 5만 요청 한도
- [GPTCache](https://github.com/zilliztech/GPTCache) -- 여러 임베딩 백엔드, 벡터 스토어, 방출 정책을 지원하는 오픈소스 시맨틱 캐싱 라이브러리
- [Martian Model Router](https://docs.withmartian.com) -- 각 질의를 처리할 수 있는 가장 싼 모델을 자동으로 고르는 프로덕션 모델 라우팅
- [Not Diamond](https://www.notdiamond.ai) -- 트래픽 패턴을 학습해 프로바이더 간 비용/품질 절충을 최적화하는 ML 기반 모델 라우터
- [Helicone](https://www.helicone.ai) -- 프록시 계층으로 비용 추적, 캐싱, 속도 제한, 예산 알림을 제공하는 LLM 관측 가능성(옵저버빌리티) 플랫폼
- [Dean & Barroso, "The Tail at Scale" (CACM 2013)](https://research.google/pubs/the-tail-at-scale/) -- 지연 시간, 처리량, TTFT/TPOT 백분위수, 헤지드 요청. "P95를 충족하는 한 가장 싼 모델을 고른다"는 비용 모델의 뿌리입니다.
- [Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention" (SOSP 2023)](https://arxiv.org/abs/2309.06180) -- vLLM 논문. 페이지드 KV-캐시 + 연속 배칭이 순진한 서버보다 처리량에서 24배 나은 이유. "캐싱과 비용" 아래의 인프라 계층입니다.
- [Dao et al., "FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning" (ICLR 2024)](https://arxiv.org/abs/2307.08691) -- 프롬프트 캐싱과 직교하는 커널 수준 비용 절감. 스페큘러티브 디코딩과 GQA와 함께 읽으면 전체 비용 곡선이 그려집니다.
