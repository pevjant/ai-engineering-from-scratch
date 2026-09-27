---
name: prompt-distributed-training-planner
description: 모델 크기와 사용 가능한 하드웨어를 바탕으로 분산 학습 실행을 계획합니다
version: 1.0.0
phase: 10
lesson: 5
tags: [distributed-training, fsdp, deepspeed, tensor-parallelism, pipeline-parallelism, scaling]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [prompt-distributed-training-planner.md](prompt-distributed-training-planner.md)

# 분산 학습 플래너

대규모 언어 모델의 분산 학습 실행을 계획할 때는, 이 프레임워크로 병렬화 전략, 메모리 예산, 통신 오버헤드, 예상 처리량을 정하세요.

## 입력 요건

다음을 준비하세요:
- **모델 크기** (파라미터 수, 단위: 십억(B))
- **목표 학습 토큰 수** (단위: 조(T))
- **사용 가능한 GPU** (유형: A100/H100/H200, 장수, 상호연결: NVLink/InfiniBand)
- **GPU 메모리** (A100/H100은 80GB, H200은 141GB)
- **노드** (노드당 GPU 수, 노드 수)
- **예산 제약** (최대 비용(달러), 최대 소요 시간)

## 단계 1: 메모리 예산

구성 요소별 GPU당 메모리를 계산합니다:

| 구성 요소 | 공식 | FP16 | FP32 |
|-----------|---------|------|------|
| 가중치 | params x bytes_per_param | params x 2 | params x 4 |
| Adam 옵티마이저 (m + v) | params x 4 x 2 | 항상 8 bytes/param | 8 bytes/param |
| 그래디언트 | params x bytes_per_param | params x 2 | params x 4 |
| 활성값 (추정치) | seq_len x batch x hidden x layers x 2 | 가변 | 가변 |

합계가 GPU 메모리를 넘으면 샤딩이 필요합니다. 순서대로 시도하세요:
1. ZeRO-1 (옵티마이저만 샤딩) -- 통신 비용이 가장 저렴
2. ZeRO-2 (+ 그래디언트) -- 통신 중간
3. FSDP/ZeRO-3 (+ 가중치) -- 통신이 가장 많지만 메모리 절감은 최대
4. 그래도 활성값이 너무 크면 활성값 체크포인팅 추가
5. 레이어 하나가 GPU 한 장에 안 들어가면 텐서 병렬화 추가

## 단계 2: 병렬화 전략

### 의사 결정 트리

1. **레이어 하나가 GPU 한 장에 들어가는가?**
   - 아니오: 텐서 병렬화가 필요합니다. TP = 2, 4, 8 중 하나로 설정하세요(노드 안에서).
   - 예: 텐서 병렬화는 건너뜁니다.

2. **샤딩을 적용한 전체 모델이 한 노드 안의 GPU에 들어가는가?**
   - 아니오: 파이프라인 병렬화가 필요합니다. PP = 노드 수(그룹 수).
   - 예: 파이프라인 병렬화는 건너뜁니다.

3. **데이터 병렬화에 남는 GPU는 몇 장인가?**
   - DP = total_gpus / (TP x PP)

4. **데이터 병렬 그룹 안에서의 샤딩 수준은?**
   - FSDP(ZeRO-3)로 시작하세요. 통신이 병목이면 ZeRO-2나 ZeRO-1로 낮춥니다.

### 전형적인 구성

| 모델 크기 | 총 GPU 수 | TP | PP | DP | 샤딩 |
|-----------|-----------|----|----|-----|----------|
| 7B | 8 | 1 | 1 | 8 | FSDP |
| 13B | 16 | 2 | 1 | 8 | FSDP |
| 70B | 64 | 8 | 1 | 8 | FSDP |
| 70B | 128 | 8 | 2 | 8 | FSDP |
| 405B | 16,384 | 8 | 16 | 128 | FSDP |

## 단계 3: 통신 분석

학습 스텝 하나의 통신량을 추정합니다:

- **데이터 병렬(all-reduce)**: 스텝당 2 x 그래디언트 크기 x (N-1)/N
- **FSDP(all-gather + reduce-scatter)**: 스텝당 약 3 x 가중치 크기 x (N-1)/N (DP보다 높음)
- **텐서 병렬(레이어마다 all-reduce)**: 스텝당 2 x 활성값 크기 x num_layers (NVLink 필요)
- **파이프라인 병렬(지점 간)**: 단계 경계마다 활성값 크기 (최소)

통신 시간이 계산 시간의 20%를 넘으면 그 전략은 통신 병목입니다. 해결책:
- 그래디언트 누적(all-reduce 빈도를 줄임)
- 통신과 계산을 겹치기(FSDP는 기본으로 이렇게 함)
- 마이크로배치 크기 늘리기(계산 대비 통신 비율 개선)
- 통신 부담이 덜한 샤딩 단계로 전환

## 단계 4: 처리량과 비용 추정

**학습 스텝당 FLOPS:**
- 순전파: 약 2 x params x tokens_per_batch
- 역전파: 약 4 x params x tokens_per_batch (순전파의 2배)
- 합계: 약 6 x params x tokens_per_batch

**학습 시간:**
- total_flops = 6 x params x total_tokens
- time_seconds = total_flops / (num_gpus x gpu_tflops x 1e12 x utilization)
- 전형적인 활용률: 35~45% (통신, 파이프라인 버블, 메모리 오버헤드 반영)

**비용:**
- total_gpu_hours = num_gpus x time_seconds / 3600
- cost = total_gpu_hours x cost_per_gpu_hour

## 단계 5: 검증 체크리스트

실행 전에:

1. GPU당 메모리가 하드웨어 한도 안에 들어가는지(여유 10% 확보)
2. 실효 배치 크기가 목표와 일치하는지(per_gpu_batch x DP x gradient_accumulation_steps)
3. 통신 대비 계산 비율이 20% 미만인지
4. 파이프라인 버블 비율이 15% 미만인지(마이크로배치가 충분한지)
5. 학습률이 실효 배치 크기에 맞게 조정되었는지
6. 체크포인트 저장 주기가 실패 확률을 감안하는지(대규모 실행은 1~2시간마다 저장)
7. 그래디언트 클리핑이 설정되어 있는지(대형 모델은 보통 1.0)
8. 워밍업 스텝이 전체 스텝에 비례하는지(보통 전체의 0.1~1%)

## 위험 신호

- **TP > 8**: 노드를 넘는 텐서 병렬화(InfiniBand 경유)는 거의 항상 파이프라인 병렬화보다 느립니다
- **파이프라인 단계 > 32**: 마이크로배치를 많이 써도 버블 오버헤드가 커집니다
- **실효 배치 > 1,000만 토큰**: 효과가 점점 줄어들고 수렴을 해칠 수 있습니다
- **활용률 30% 미만**: 통신 병목 — 병렬화 전략을 다시 검토하세요
- **13B를 넘는데 활성값 체크포인팅이 없음**: 역전파 도중 메모리가 부족해집니다
- **GPU당 배치가 작은데 그래디언트 누적이 없음**: 그래디언트 잡음이 커집니다 — 실효 배치가 256개 샘플 이상이 되도록 누적하세요
