---
name: skill-inference-optimization
description: LLM 추론 서빙의 처리량, 지연 시간, 비용을 진단하고 최적화합니다
version: 1.0.0
phase: 10
lesson: 12
tags: [inference, kv-cache, batching, speculative-decoding, vllm, optimization]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-inference-optimization.md](skill-inference-optimization.md)

# LLM 추론 최적화 패턴

두 페이즈가 있습니다: 프리필드(prefill, 연산 병목, 병렬)와 디코드(decode, 메모리 병목, 순차).
모든 최적화는 이 둘 중 하나 또는 둘 다를 겨냥합니다.

```
Request -> Prefill (process prompt) -> Decode (generate tokens) -> Response
              |                            |
         Compute-bound               Memory-bound
         Optimize: fusion,           Optimize: batching,
         prefix caching              quantization, speculation
```

## 의사결정 프레임워크

### 단계 1: 병목 찾기

여러분의 워크로드에 대한 ops:byte 비율을 측정하세요:

| ops:byte | 병목 | 최적화 대상 |
|----------|-------|-----------------|
| < 50 | 메모리 | KV 캐시 양자화, 배치 크기 증가 |
| 50-200 | 전환 구간 | 둘 다 중요, 배칭부터 시작 |
| > 200 | 연산 | 커널 퓨전, 텐서 병렬화, FP8 |

### 단계 2: 엔진 고르기

- **기본값**: vLLM (가장 넓은 모델 지원, PagedAttention, OpenAI 호환 API)
- **멀티턴 / 구조화된 출력**: SGLang (RadixAttention 프리픽스 캐싱, 제약 디코딩)
- **최대 NVIDIA 처리량**: TensorRT-LLM (커널 퓨전, H100에서 FP8)

### 단계 3: 순서대로 최적화 적용

1. **KV 캐시** -- 항상 켜기, 단점 없음
2. **연속 배칭** -- 항상 켜기, 단점 없음 (vLLM/SGLang은 기본으로 해 줌)
3. **프리픽스 캐싱** -- 공유 시스템 프롬프트가 있으면 켜기 (대부분의 챗봇이 그렇습니다)
4. **양자화** -- KV 캐시를 INT8/FP8로 하면 품질 손실을 최소화하면서 메모리 2-4배 절감
5. **스페큘레이티브 디코딩** -- 처리량보다 지연 시간이 중요할 때 추가
6. **텐서 병렬화** -- 모델이 GPU 한 장에 안 들어갈 때 여러 장으로 나누기

## KV 캐시 메모리 공식

```
per_token = 2 * num_layers * num_kv_heads * head_dim * bytes_per_param
total = per_token * sequence_length * num_concurrent_users
```

자주 쓰는 모델용 빠른 참조표 (BF16):

| 모델 | 토큰당 | 100명 @ 4K |
|-------|-----------|----------------|
| Llama 3 8B | 32 KB | 12.5 GB |
| Llama 3 70B | 320 KB | 125 GB |
| Llama 3 405B | 504 KB | 197 GB |

## 스페큘레이티브 디코딩 체크리스트

- 초안 모델은 타깃보다 5-10배 작아야 함 (예: 70B의 초안은 8B)
- 의미 있는 가속을 위해서는 수용률 > 70%
- 예측 가능한 텍스트에서 가장 좋음 (코드, 구조화된 출력, 자연어)
- 창의적/샘플링 의존적인 과제에서는 가장 나쁨 (낮은 temperature가 도움 됨)
- 대부분의 워크로드에서 EAGLE > 초안-타깃 > n-gram

## 흔한 실수

- 배치=1로 디코드 돌리기 (메모리 병목, GPU 연산은 95%가 놂)
- 연속된 KV 캐시 블록 할당하기 (PagedAttention을 쓰면 낭비가 거의 0)
- 요청의 80%가 같은 시스템 프롬프트를 공유하는데도 프리픽스 캐싱 무시하기
- 모델 가중치로 GPU 메모리를 다 써버려 KV 캐시에는 아무것도 남기지 않기
- 지연 시간 측정 없이 처리량만 측정하기 (TTFT 10초짜리 높은 처리량은 쓸모없음)
- 높은 temperature에서 스페큘레이티브 디코딩 쓰기 (수용률이 50% 아래로 떨어짐)

## 모니터링 체크리스트

- 첫 토큰까지 시간 (TTFT): 프리필드 지연 시간, 대화형 용도의 목표는 < 500ms
- 토큰 간 지연 시간 (ITL): 디코드 속도, 스트리밍의 목표는 < 50ms
- 처리량 (초당 토큰 수): 모든 동시 사용자를 합친 총량
- KV 캐시 활용도: 할당된 캐시 중 사용 중인 비율
- 배치 활용도: 반복(iteration)당 채워진 배치 슬롯 비율
- 큐 깊이: 배치 슬롯을 기다리는 요청 수
