> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 프리필/디코드 분리(Disaggregation) — NVIDIA Dynamo와 llm-d

> 프리필은 연산 병목이고, 디코드는 메모리 병목입니다. 둘을 같은 GPU에서 돌리면 자원 하나를 낭비합니다. 분리(disaggregation)는 둘을 별도의 풀로 나누고 NIXL(RDMA/InfiniBand, 없으면 TCP 폴백)을 통해 KV 캐시를 전송합니다. NVIDIA Dynamo(GTC 2025 발표, 1.0 GA)는 vLLM/SGLang/TRT-LLM 위에 얹히는 스택으로 — Planner Profiler + SLA Planner가 SLO를 맞추기 위해 프리필:디코드 비율을 자동으로 맞춰 줍니다. NVIDIA는 이 정도 범위의 처리량 개선을 공개합니다 — developer.nvidia.com(2025-06)은 중간 지연 구간에서 GB200 NVL72 + Dynamo의 DeepSeek-R1 MoE가 약 6배 개선됐다고 보여주고, Dynamo 제품 페이지(developer.nvidia.com, 날짜 미기재)는 Hopper 대비 GB300 NVL72 + Dynamo에서 최대 50배 MoE 처리량을 내세웁니다. "30배"라는 수치는 풀스택 Blackwell + Dynamo + DeepSeek-R1 보고들을 모은 커뮤니티 집계값입니다; 정확히 30배라고 명시한 단일 1차 출처는 발견하지 못했으므로 방향성 주장으로 취급하세요. llm-d(Red Hat + AWS)는 Kubernetes 네이티브입니다: 프리필 / 디코드 / 라우터가 역할별 HPA를 가진 독립 Service로 동작합니다. llm-d 0.5는 계층형 KV 오프로딩, 캐시 인지 LoRA 라우팅, UCCL 네트워킹, 스케일 투 제로를 추가했습니다. 경제성: 여러 고객 공개 발표를 묶은 내부 집계에 따르면 동일 SLA 조건에서 동거(colocated) 서빙에서 Dynamo 기반 분리 서빙으로 전환 시 $2M급 추론 지출에서 30-40% 절감(연간 $600-800K)이 나옵니다; 다만 $2M→$600-800K라는 구체적 수치는 단일 공개 사례가 아니라 내부 합성치이므로 인용 근거가 아니라 자릿수 감각용 기준점으로 쓰세요. 짧은 프롬프트(512 토큰 미만, 짧은 출력)는 전송 비용을 정당화하지 못합니다.

**유형:** 학습
**언어:** Python (표준 라이브러리, 분리 vs 동거 시뮬레이터 장난감 버전)
**선수 지식:** 페이즈 17 · 04 (서빙 엔진 내부 구조), 페이즈 17 · 08 (추론 메트릭)
**시간:** 약 75분

## 학습 목표

- 프리필과 디코드의 최적 GPU 배분이 왜 다른지 설명하고, 동거(co-location)에서의 낭비를 수치화할 수 있습니다.
- 분리 아키텍처를 그림으로 그릴 수 있습니다: 프리필 풀, 디코드 풀, NIXL을 통한 KV 전송, 라우터.
- 분리가 값을 내지 못하는 조건(짧은 프롬프트, 짧은 출력)의 이름을 말할 수 있습니다.
- NVIDIA Dynamo(스택 위 오케스트레이터)와 llm-d(Kubernetes 네이티브)를 구분하고 각각에 맞는 운영 환경을 짝지을 수 있습니다.

## 문제 상황

H100 8장에서 Llama 3.3 70B를 돌립니다. 혼합 워크로드(긴 프롬프트 + 짧은 출력)에서는 대부분의 연산이 프리필에 쓰이기 때문에 디코드 동안 GPU가 놉니다. 다른 워크로드(짧은 프롬프트 + 긴 출력)에서는 반대가 일어납니다. 프리필 + 디코드를 동거시키면 둘 다 과잉 프로비저닝하게 됩니다.

예산 영향: GPU 시간의 20-40%가 잘못된 자원에 낭비됩니다. 메모리 병목인 디코드를 돌리려고 H100 연산을 사거나, 연산 병목인 프리필을 돌리려고 H100 HBM 대역폭을 사는 셈입니다. 둘 다 비싼 낭비입니다.

분리는 프리필과 디코드를 각자의 병목에 맞게 크기를 잡은 별도 풀로 나눕니다. KV 캐시는 고대역폭 인터커넥트를 통해 프리필 풀에서 디코드 풀로 옮겨갑니다.

## 개념

### 병목이 왜 다른가

**프리필** — 전체 입력 프롬프트를 한 번의 포워드로 트랜스포머에 통과시킵니다. 행렬 곱이 지배적; 연산 병목. H100 FP8은 유효 처리량 약 2000 TFLOPS를 냅니다. 배치 효율이 좋습니다 — 포워드 한 번이 많은 토큰을 처리합니다.

**디코드** — 토큰을 한 번에 하나씩 생성하며, 매 반복마다 가중치 전체를 읽습니다. 메모리 대역폭 병목. HBM3는 약 3 TB/s를 제공합니다. 배치 효율은 높은 동시성에서만 좋습니다 — 가중치 읽기 비용이 배치에 걸쳐 분산되기 때문입니다.

동거시키면: 둘 다에 최적화된 GPU를 삽니다. H100은 둘 다 잘하지만 어느 쪽이든 비용은 같습니다. 규모가 커지면 프리필 풀은 H100 / 연산 위주로, 디코드 풀은 H200 / 메모리 위주 또는 공격적인 양자화로 구성하고 싶어집니다.

### 아키텍처

```
            ┌──────────────┐
  Request → │    Router    │ ───────────────────────┐
            └──────┬───────┘                        │
                   │                                │
                   ▼ (prompt only)                  │
            ┌──────────────┐    KV cache    ┌───────▼──────┐
            │ Prefill pool │ ─── NIXL ────► │ Decode pool  │
            │  (compute)   │                │  (memory)    │
            └──────────────┘                └──────┬───────┘
                                                   │ tokens
                                                   ▼
                                                 Client
```

NIXL은 NVIDIA의 노드 간 전송 계층입니다. 가능하면 RDMA/InfiniBand를 쓰고, 아니면 TCP로 폴백합니다. 전송 지연은 실재합니다 — 70B FP8 기준 4K 토큰 프롬프트의 KV 캐시에 보통 20-80ms입니다. 그래서 짧은 프롬프트는 분리를 정당화하지 못합니다: 전송세가 절감액을 넘어버립니다.

### Dynamo vs llm-d

**NVIDIA Dynamo** (GTC 2025 발표, 1.0 GA):
- vLLM, SGLang, TRT-LLM 위에 오케스트레이터로 얹힙니다.
- Planner Profiler가 워크로드를 측정하고, SLA Planner가 프리필:디코드 비율을 자동 설정합니다.
- Rust 코어, Python 확장성.
- 처리량 개선: NVIDIA는 중간 지연 구간에서 GB200 NVL72 + Dynamo의 DeepSeek-R1 MoE에 대해 6배를 보고합니다(developer.nvidia.com, 2025-06); 풀 Blackwell + Dynamo + DeepSeek-R1 스택에 대한 커뮤니티의 "최대 30배" 주장은 단일 1차 출처가 없어 방향성으로 취급해야 합니다.
- GB300 NVL72 + Dynamo: Dynamo 제품 페이지(developer.nvidia.com, 날짜 미기재) 기준 Hopper 대비 최대 50배 MoE 처리량.

**llm-d** (Red Hat + AWS, Kubernetes 네이티브):
- 프리필 / 디코드 / 라우터가 독립적인 Kubernetes Service.
- 큐 깊이(프리필) / KV 사용률(디코드) 신호를 쓰는 역할별 HPA.
- `topologyConstraint packDomain: rack`으로 프리필+디코드 클리크(clique)를 같은 랙에 묶어 고대역폭 KV 전송을 확보합니다.
- llm-d 0.5 (2026): 계층형 KV 오프로딩, 캐시 인지 LoRA 라우팅, UCCL 네트워킹, 스케일 투 제로.

관리형 스택 위 오케스트레이터를 원하면 Dynamo를 쓰세요. Kubernetes 네이티브 프리미티브를 원하고 CNCF 생태계에 올인한다면 llm-d를 쓰세요.

### 경제성

내부 합성치(단일 공개 사례가 아님 — 자릿수 감각용 기준점):

- 동거 서빙으로 연간 $2M 추론 지출.
- Dynamo 기반 분리 서빙으로 전환.
- 같은 요청 볼륨, 같은 P99 지연 SLA.
- 보고된 절감: 연간 $600K-$800K (30-40% 감소).
- 새 하드웨어 없음.

이 수치는 인용 가능한 단일 사례가 아니라 여러 고객 공개 발표를 종합한 것입니다. 가장 가까운 공개 데이터 포인트는 Baseten의 Dynamo KV 라우팅으로 2배 빠른 TTFT / 61% 높은 처리량(baseten.co, 2025-10), 그리고 VAST + CoreWeave의 KV 적중률 40-60%에서 토큰/$ 60-130% 개선 전망(vastdata.com, 2025-12)입니다. 절감은 각 풀의 크기를 병목에 맞게 조정하는 데서 나옵니다; 프리필 위주 워크로드(8K 이상 프리픽스의 RAG)가 균형형보다 더 큰 혜택을 봅니다.

### 분리하면 안 되는 경우

- 프롬프트 512 토큰 미만 + 출력 200 토큰 미만: 전송세가 이득을 지배합니다.
- 작은 클러스터(GPU 4장 미만): 풀 다양성이 부족합니다.
- 역할별 스케일링이 가능한 GPU 풀 둘을 운영할 수 없는 팀: Dynamo가 도움되긴 하지만 만만치 않습니다.
- RDMA 패브릭이 없음: TCP 전송세가 더 무겁습니다.

### 라우터는 페이즈 17 · 11과 통합됩니다

분리된 라우터는 KV 캐시를 인지합니다(페이즈 17 · 11). 요청은 자기 프리픽스를 들고 있는 디코드 풀에 착지합니다 — 매칭이 없으면 프리필 → 디코드로 흐릅니다. 적중률과 분리는 시너지를 냅니다 — 캐시 인지 라우터가 새 프리필이 필요한지조차 결정합니다.

### 진짜 숫자가 나오는 곳은 Blackwell 위의 MoE입니다

GB300 NVL72 + Dynamo는 Hopper 베이스라인 대비 50배 MoE 처리량을 보여줍니다. MoE 전문가 라우팅은 프리필에서는 연산 위주이지만 디코드에서는 메모리 위주(전문가 캐시)라서, 분리는 두 번의 승리입니다. 2026년 프론티어 모델 서빙은 MoE가 지배적입니다(DeepSeek-V3, 미래의 GPT-5 변형들).

### 기억해야 할 숫자들

벤치마크 수치는 흔듭니다 — NVIDIA와 추론 스택은 분기마다 갱신된 결과를 올립니다. 인용 전에 다시 확인하세요.

- GB200 NVL72 + Dynamo의 DeepSeek-R1: 중간 지연 구간에서 베이스라인 대비 약 6배 처리량 (developer.nvidia.com, 2025-06); 풀 Blackwell + Dynamo 스택에 대한 커뮤니티의 "최대 30배" 주장은 단일 1차 출처 없는 방향성 집계입니다.
- GB300 NVL72 + Dynamo: Hopper 대비 최대 50배 MoE 처리량 (developer.nvidia.com, 날짜 미기재).
- 절감 기준점(내부 합성치, 단일 사례 아님): 동일 SLA에서 연간 $2M 지출 대비 연간 $600-800K 절감.
- 분리 임계점: 프롬프트 512 토큰 초과 + 출력 200 토큰 초과.
- NIXL 통한 KV 전송: 70B FP8의 4K 프롬프트 KV 기준 20-80ms.

```figure
prefill-decode-split
```

## 활용하기

`code/main.py`는 동거 서빙과 분리 서빙을 시뮬레이션합니다. 처리량, 요청당 비용, 프롬프트 길이 교차점을 보고합니다.

## 출시하기

이 레슨은 `outputs/skill-disaggregation-decider.md`를 산출합니다. 워크로드와 클러스터가 주어지면 분리 여부를 결정합니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 어떤 프롬프트 길이에서 분리가 동거를 이기나요?
2. P99 프리픽스 길이 8K, 출력 300인 RAG 서비스의 프리필 풀과 디코드 풀을 설계하세요.
3. Dynamo vs llm-d: Python 런타임 선호가 없는 순수 Kubernetes 조직이라면 어느 쪽을 고르시겠습니까?
4. KV 전송 비용을 계산하세요: 70B FP8에서 4K 프리필 = KV 약 500 MB. RDMA 100 GB/s면 전송 = 5ms. TCP 10 GB/s면 = 50ms. 어느 쪽이 여러분의 SLA에 문제가 되나요?
5. MoE 전문가 라우팅은 KV 접근 패턴을 바꿉니다. 토큰마다 다른 전문가를 활성화하는 MoE에서 분리는 어떻게 동작할까요?

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| 분리 서빙 | "프리필/디코드 분리" | 페이즈별로 나눈 별도 GPU 풀 |
| NIXL | "NVIDIA 전송 계층" | Dynamo의 노드 간 KV 전송 (RDMA/TCP) |
| NVIDIA Dynamo | "그 오케스트레이터" | vLLM/SGLang/TRT-LLM 위에 얹히는 조율자 |
| llm-d | "Kubernetes 네이티브" | Red Hat + AWS의 K8s 분리 스택 |
| Planner Profiler | "Dynamo 자동 구성" | 워크로드를 측정해 풀 비율을 설정 |
| SLA Planner | "Dynamo 정책" | SLO 충족을 위해 프리필:디코드 비율을 자동 조정 |
| `packDomain: rack` | "llm-d 토폴로지" | 빠른 KV 전송을 위해 프리필+디코드를 같은 랙에 묶음 |
| UCCL | "통합 콜렉티브" | llm-d 0.5의 스케일 투 제로용 네트워킹 계층 |
| MoE 전문가 라우팅 | "토큰별 전문가" | DeepSeek-V3 패턴; 분리가 도움됨 |

## 더 읽을거리

- [NVIDIA — Introducing Dynamo](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/)
- [NVIDIA — Disaggregated LLM Inference on Kubernetes](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/)
- [TensorRT-LLM Disaggregated Serving blog](https://nvidia.github.io/TensorRT-LLM/blogs/tech_blog/blog5_Disaggregated_Serving_in_TensorRT-LLM.html)
- [llm-d GitHub](https://github.com/llm-d/llm-d)
- [llm-d 0.5 release notes](https://github.com/llm-d/llm-d/releases)
