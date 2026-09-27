---
name: prompt-gpt-architecture-analyzer
description: GPT 계열 트랜스포머 모델의 아키텍처 선택을 분석합니다
version: 1.0.0
phase: 10
lesson: 4
tags: [gpt, transformer, architecture, attention, kv-cache, scaling, pre-training]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [prompt-gpt-architecture-analyzer.md](prompt-gpt-architecture-analyzer.md)

# GPT 아키텍처 분석기

기술 보고서, 모델 카드, 학습 로그에서 GPT 계열 모델을 평가할 때는 이 프레임워크를 써서 아키텍처를 뜯어보고 설계상 트레이드오프를 짚어 내세요.

## 분석 절차

### 1. 파라미터 배분 분석

각 구성 요소의 정확한 파라미터 수를 계산합니다:

- **토큰 임베딩**: vocab_size x embed_dim
- **위치 임베딩**: max_seq_len x embed_dim
- **블록당 어텐션**: 4 x embed_dim x embed_dim (Q, K, V, 출력 투영)
- **블록당 FFN**: 2 x embed_dim x ff_dim + embed_dim + ff_dim (선형 레이어 2개 + 편향)
- **블록당 LayerNorm**: 4 x embed_dim (정규화 2개, 각각 스케일 + 편향)
- **최종 LayerNorm**: 2 x embed_dim
- **출력 헤드**: vocab_size x embed_dim (토큰 임베딩과 웨이트 타이잉되어 있으면 0)

어떤 구성 요소 하나가 전체 파라미터의 40%를 넘으면 표시하세요. 작은 모델에서는 임베딩 행렬이 지배적입니다. 큰 모델에서는 어텐션과 FFN이 지배적입니다.

### 2. 어텐션 설계 분석

어텐션 구성을 평가합니다:

- **헤드 차원**: embed_dim / num_heads. 표준은 64(GPT-2) 또는 128(Llama 3)입니다. 32 미만이면 헤드 하나의 표현력이 제한됩니다. 128 초과면 이득은 거의 없이 계산만 낭비합니다.
- **레이어당 헤드 수**: 헤드가 많을수록 어텐션 패턴은 다양해지지만, KV 캐시에 쓰이는 메모리도 더 커집니다.
- **그룹 쿼리 어텐션(GQA, Grouped Query Attention)**: 모델이 K/V 헤드를 여러 Q 헤드가 공유하는가? Llama 3는 Q 헤드 32개에 KV 헤드 8개로 GQA를 씁니다. KV 캐시가 4분의 1로 줄어듭니다.
- **컨텍스트 길이**: 위치 임베딩의 최대 개수. RoPE는 학습 길이를 넘어서도 외삽할 수 있습니다. 절대 위치 임베딩은 안 됩니다.

### 3. 메모리 예산

모델의 최대 컨텍스트 길이로 추론할 때:

- **가중치(FP16)**: total_params x 2바이트
- **KV 캐시(FP16)**: 2 x num_layers x num_kv_heads x head_dim x max_seq_len x 2바이트
- **활성값(activations)**: batch_size x seq_len x embed_dim x 2바이트 x num_layers (근사치)

KV 캐시가 가중치 메모리를 넘으면 표시하세요. 이는 긴 컨텍스트 모델(128K 이상)에서 일어나며, 디코드 중에 메모리 병목이라는 뜻입니다.

### 4. 연산 프로파일

- **토큰당 프리필 FLOPS**: 대략 2 x total_params (파라미터당 행렬 곱셈 하나, 순전파 기준)
- **토큰당 디코드 FLOPS**: 프리필과 같지만 토큰 하나에 대해 계산
- **프리필 병목**: 연산 병목(compute-bound, GPU TFLOPS)
- **디코드 병목**: 메모리 병목(memory-bound, GPU 메모리 대역폭)
- **산술 강도(arithmetic intensity)**: 읽고 쓰는 메모리 1바이트당 FLOPS. 100 미만이면 메모리 병목입니다.

### 5. 스케일링 결정

알려진 스케일링 법칙과 비교해 평가합니다:

- **친칠라 최적점(Chinchilla optimal)**: 연산 예산 C가 주어지면, 최적 모델 크기 N과 토큰 수 D는 N ~ D(대략 비슷한 비율로 함께 늘어남)를 만족합니다. 7B 모델에는 약 1,400억(140B) 토큰이 필요합니다.
- **Llama 3의 과학습(overtrained)**: Meta는 Llama 3 8B를 15조(15T) 토큰으로 학습했습니다(친칠라 최적점의 100배). 작은 모델을 더 많은 데이터로 과학습하면 토큰당 추론 비용이 더 유리해집니다.
- **너비 vs 깊이**: 같은 파라미터 수라면, 더 깊은 모델(레이어가 많음)이 일반적으로 더 넓은 모델(embed_dim이 큼)보다 데이터를 효율적으로 씁니다.

## 위험 신호

- **FFN 비율이 4배가 아님**: 표준은 ff_dim = 4 x embed_dim입니다. Llama는 SwiGLU와 함께 8/3 x embed_dim을 씁니다. 표준에서 벗어났다면 그 이유가 설명되어야 합니다.
- **웨이트 타이잉 없음**: vocab_size가 embed_dim에 비해 아주 큰 경우가 아니라면, 출력 헤드는 토큰 임베딩과 가중치를 공유해야 합니다.
- **13B를 넘는데 GQA가 없음**: 13B가 넘는 모델에 그룹 쿼리 어텐션이 없으면 KV 캐시가 지나치게 커집니다.
- **긴 컨텍스트인데 RoPE가 없음**: 절대 위치 임베딩은 학습 길이를 넘어 외삽하지 못합니다. 32K 이상 컨텍스트를 지향하는 모델은 로터리 임베딩(rotary embeddings)을 써야 합니다.
- **모델 크기에 비해 학습률이 너무 높음**: 모델이 클수록 최대 학습률은 낮아야 합니다. GPT-2 Small은 6e-4를, Llama 3 405B는 8e-5를 씁니다.

## 출력 형식

1. **파라미터 표**: 구성 요소별 파라미터 수와 비율
2. **메모리 예산**: 최대 컨텍스트 길이에서의 가중치, KV 캐시, 활성값 메모리
3. **연산 프로파일**: A100/H100 기준 프리필·디코드 처리량 추정치
4. **설계 평가**: 모델이 잘한 점과 표준에서 벗어난 점
5. **스케일링 판정**: 학습 데이터에 비해 모델 크기가 적절했는지
