> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 쿠버네티스 GPU 오토스케일링 — Karpenter, KAI Scheduler, 갱 스케줄링

> 계층은 셋입니다, 하나가 아닙니다. Karpenter는 노드를 동적으로 프로비저닝합니다(1분 미만, Cluster Autoscaler보다 40% 빠름). KAI Scheduler는 갱(gang) 스케줄링, 토폴로지 인식, 계층형 큐를 담당합니다 — 8개 중 7개만 배정되어 8번째 GPU 하나를 기다리며 일곱 노드가 돈을 태우는 '7-of-8 부분 할당 함정'을 막아 줍니다. 애플리케이션 레벨 오토스케일러(NVIDIA Dynamo Planner, llm-d Workload Variant Autoscaler)는 CPU/DCGM 듀티 사이클이 아니라 큐 깊이, KV 캐시 활용률 같은 추론 특화 신호로 확장합니다. 전형적인 HPA 함정은 이것입니다. `DCGM_FI_DEV_GPU_UTIL`은 듀티 사이클 측정값이라는 점입니다. 100%가 10개 요청일 수도 있고 100개 요청일 수도 있죠. 게다가 vLLM은 KV 캐시 메모리를 미리 할당해 두기 때문에, 메모리 기반으로는 절대 스케일다운이 일어나지 않습니다. 이 레슨은 세 계층을 조립하는 법과, 실행 중인 GPU 작업을 추론 도중에 강제 종료해 버리는 Karpenter 기본 정책 `WhenEmptyOrUnderutilized`를 피하는 법을 가르칩니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 장난감 수준 큐 깊이 오토스케일러 시뮬레이터)
**선수 지식:** Phase 17 · 02 (추론 플랫폼 경제학), Phase 17 · 04 (서빙 엔진 내부 구조)
**시간:** 약 75분

## 학습 목표

- 세 개의 오토스케일링 계층(노드 프로비저닝, 갱 스케줄링, 애플리케이션 레벨)을 그림으로 그리고, 각 계층에서 쓰는 도구의 이름을 말할 수 있다.
- vLLM에서 `DCGM_FI_DEV_GPU_UTIL`이 잘못된 HPA 신호인 이유를 설명하고, 대체 신호 두 가지(큐 깊이, KV 캐시 활용률)를 말할 수 있다.
- 갱 스케줄링이 무엇인지, 그리고 KAI Scheduler가 막아 주는 부분 할당 장애(8개 중 7개 GPU가 놂)가 어떤 것인지 설명할 수 있다.
- 실행 중인 GPU 작업을 종료해 버리는 Karpenter 통합(consolidation) 정책(`WhenEmptyOrUnderutilized`)의 이름을 말하고, 2026년 기준 안전한 대안을 제시할 수 있다.

## 문제 상황

여러분 팀이 쿠버네티스 위에 LLM 서빙 서비스를 올렸습니다. HPA의 신호로 `DCGM_FI_DEV_GPU_UTIL`을 설정했습니다. 업무 시간에는 활용률이 100%에 고정됩니다. 그런데 HPA는 절대 스케일업하지 않습니다 — 이미 "꽉 찼다"고 판단하고 있으니까요. 레플리카를 수동으로 하나 늘리면 TTFT가 떨어집니다. 그래도 HPA는 움직이지 않습니다. 신호가 여러분에게 거짓말을 하고 있는 겁니다.

따로 따로 또 문제가 생깁니다. 노드에는 Cluster Autoscaler를 씁니다. 새벽 2시에 100만 토큰짜리 프롬프트가 도착하면, 클러스터는 노드 하나를 띄우는 데 3분을 쓰고 요청은 타임아웃됩니다.

또 따로, 2개 노드에 걸쳐 GPU 8개가 필요한 70B 모델을 배포합니다. 클러스터에는 GPU가 7개 남아 있고, 나머지 1개는 3개 노드에 흩어져 있습니다. Cluster Autoscaler는 부족한 1개 GPU를 위해 노드를 프로비저닝합니다. 그 사이 일곱 노드는 4분 동안 돈을 태우며 마지막 GPU가 뜨기를 기다립니다.

세 개의 계층, 세 가지의 서로 다른 장애 양상입니다. 2026년의 GPU 인식 오토스케일링은 "HPA 켜기"가 아닙니다. 노드 프로비저닝, 갱 스케줄링, 애플리케이션 신호 기반 오토스케일링을 조립하는 일입니다.

## 개념

### 계층 1 — 노드 프로비저닝 (Karpenter)

Karpenter는 pending 상태의 파드를 지켜보다가 약 45~60초 안에 노드를 프로비저닝합니다(Cluster Autoscaler는 GPU 노드 기준 보통 90~120초). `NodePool` 제약에 따라 인스턴스 타입을 동적으로 고릅니다 — 파드가 H100 8개를 필요로 하는데 클러스터에 맞는 노드가 없으면, 기존 그룹을 늘리는 게 아니라 Karpenter가 노드를 직접 프로비저닝합니다.

**통합(consolidation) 함정**: Karpenter의 기본값인 `consolidationPolicy: WhenEmptyOrUnderutilized`는 GPU 풀에서 위험합니다. 파드를 더 저렴한 적정 크기 인스턴스로 옮기겠다고, 실행 중인 GPU 노드를 종료해 버릴 수 있습니다. 추론 워크로드라는 건 실행 중인 요청을 쫓아내고 새 노드에 70B 모델을 다시 올리는 일이 됩니다. 잃는 것은 수 분치 용량에 요청 실패까지입니다.

GPU 풀의 안전한 설정:

```yaml
disruption:
  consolidationPolicy: WhenEmpty
  consolidateAfter: 1h
```

이렇게 하면 Karpenter가 1시간 후에 진짜 빈 노드만 통합하고, 실행 중인 작업은 절대 쫓아내지 않습니다.

### 계층 2 — 갱 스케줄링 (KAI Scheduler)

KAI Scheduler(프로젝트명이 "Karp"였다가 개명됨)는 기본 kube-scheduler가 못 해 주는 일을 처리합니다:

**갱(gang) 스케줄링** — 전부 아니면 전무(all-or-nothing)로 스케줄링합니다. GPU 8개가 필요한 분산 추론 파드는 8개가 함께 뜨거나 아예 안 뜨거나 둘 중 하나여야 합니다. 이게 없으면 부분 할당 함정에 걸립니다. 8개 중 7개가 떠서 무한히 기다리며 돈을 태우는 거죠.

**토폴로지 인식** — 어떤 GPU끼리 NVLink를 공유하는지, 어떤 것들이 같은 랙에 있는지, 누구 사이에 InfiniBand가 있는지 알고 그에 맞게 파드를 배치합니다. DeepSeek-V3 67B 텐서 병렬 워크로드는 하나의 NVLink 도메인 안에 머물러야 하는데, KAI Scheduler가 이를 지켜 줍니다.

**계층형 큐** — 여러 팀이 같은 GPU 풀을 우선순위와 쿼터로 두고 경쟁합니다. 우선순위 규칙이 허용할 때만, 팀 B의 학습 작업이 팀 A의 프로덕션(운영 환경) 급한 작업을 선점(preempt)할 수 있습니다.

KAI는 kube-scheduler 옆에 세컨더리 스케줄러로 배포하고, 워크로드에 어노테이션을 붙여 사용하게 합니다. Ray와 vLLM 프로덕션 스택 둘 다 통합되어 있습니다.

### 계층 3 — 애플리케이션 레벨 신호

**HPA 함정**: `DCGM_FI_DEV_GPU_UTIL`은 듀티 사이클 지표입니다 — 각 샘플링 구간에 GPU가 일을 했는지를 잰 값이죠. 100% 활용률은 동시 요청 10개일 수도 있고 100개일 수도 있습니다. 어느 쪽이든 GPU는 바빴을 뿐입니다. 듀티 사이클로 스케일링하는 건 눈 감고 스케일링하는 겁니다.

더 나쁜 건, vLLM 같은 엔진은 KV 캐시 메모리를 미리 할당해 둡니다(`--gpu-memory-utilization`까지). 그래서 요청이 하나만 있어도 메모리 사용량은 90% 근처에 머뭅니다. 메모리 기반 HPA는 절대 스케일다운하지 않습니다.

**2026년의 대체 신호**:

- 큐 깊이(프리필을 기다리는 요청 수).
- KV 캐시 활용률(블록 중 활성 시퀀스에 할당된 비율).
- 레플리카당 P99 TTFT(여러분의 SLA 신호).
- 굿푸트(goodput, 모든 SLO를 충족하는 초당 요청 수).

NVIDIA Dynamo Planner와 llm-d Workload Variant Autoscaler는 이 신호들을 받아 레플리카 수를 조절합니다. LLM 서빙에서는 HPA를 완전히 대체합니다.

### 무엇을 언제 쓰나

| 확장 결정 | 도구 |
|----------------|------|
| 노드 추가/제거 | Karpenter |
| 멀티 GPU 작업 스케줄링 | KAI Scheduler |
| 레플리카 추가/제거 | Dynamo Planner / llm-d WVA (또는 큐 깊이 기반 커스텀 HPA) |
| GPU 종류 선택 | Karpenter NodePool |
| 낮은 우선순위 선점 | KAI Scheduler 큐 |

### 분리형 프리필/디코드가 모든 걸 복잡하게 만든다

분리형(disaggregated) 프리필/디코드(Phase 17 · 17)를 돌린다면 스케일링 트리거가 다른 두 파드 클래스가 생깁니다. 프리필 파드는 큐 깊이로, 디코드 파드는 KV 캐시 압박으로 확장합니다. llm-d는 이를 역할별 HPA가 붙은 별개의 `Services`로 노출합니다. 둘 앞에 HPA 하나를 두려고 하지 마세요.

### 여기서도 콜드 스타트가 문제다

콜드 스타트 완화(Phase 17 · 10)는 노드 프로비저닝 시간이 사용자에게 보이게 되는 지점입니다. Karpenter의 45~60초 워밍업 + 20GB 모델 로드 + 엔진 초기화라면, 제로부터 시작한 요청 하나에 2~5분이 걸립니다. SLO에 중요한 경로에는 웜 풀(`min_workers=1`)을 유지하거나, 애플리케이션 계층에서 Modal식 체크포인팅을 쓰세요.

### 기억해야 할 숫자들

- Karpenter 노드 프로비저닝: 약 45~60초 vs Cluster Autoscaler 약 90~120초(GPU 노드).
- KAI Scheduler는 부분 할당 낭비 — 7-of-8 함정 — 를 막는다.
- HPA 신호로서의 `DCGM_FI_DEV_GPU_UTIL`: 깨져 있다. 큐 깊이나 KV 활용률을 써라.
- Karpenter `WhenEmptyOrUnderutilized`: 실행 중인 GPU 작업을 종료한다. 추론에는 `WhenEmpty + consolidateAfter: 1h`를 써라.

```figure
autoscaling
```

## 직접 써보기

`code/main.py`는 버스트성 GPU 워크로드에 대해 세 계층 오토스케일러를 시뮬레이션합니다. 순진한 HPA(듀티 사이클), 큐 깊이 HPA, KAI 갱 스케줄링 확장을 비교하고, 미처리 요청 수, GPU 유휴 시간(분), 종합 점수를 보고합니다.

## 산출물

이 레슨은 `outputs/skill-gpu-autoscaler-plan.md`를 만듭니다. 클러스터 토폴로지, 워크로드 형태, SLO가 주어지면 세 계층 오토스케일링 계획을 설계합니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 버스트성 워크로드에서 순진한 듀티 사이클 HPA가 놓치는 요청은 큐 깊이 HPA보다 몇 개 더 많나요? 그 차이는 어디서 오나요?
2. H100 SXM5에서 Llama 3.3 70B FP8을 서빙하는 클러스터를 위한 Karpenter NodePool을 설계하세요. `capacity-type`, `disruption.consolidationPolicy`, `consolidateAfter`, 그리고 비 GPU 워크로드가 이 노드에 못 오게 막는 테인트(taint)를 명시하세요.
3. 팀이 "GPU는 남아 있는데 파드가 스케줄이 안 된다"며 배포가 Pending에 갇혔다고 보고합니다. 진단해 보세요 — Karpenter 문제인가요, kube-scheduler인가요, KAI Scheduler인가요? 어떤 지표로 확인하나요?
4. 분리형 프리필 파드를 위한 스케일링 신호와 디코드 파드를 위한 신호를 서로 다르게 하나씩 고르세요. 둘 다 근거를 대세요.
5. P99 TTFT가 10초를 넘는 요청 유실 사건이 하루 평균 60번 일어나는 24시간 연중무휴 프로덕션(운영 환경) 서비스에서, `WhenEmptyOrUnderutilized` 통합 함정의 비용을 계산해 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| Karpenter | "노드 프로비저너" | 쿠버네티스 노드 오토스케일러. 1분 미만 프로비저닝 |
| Cluster Autoscaler | "옛날 스케일러" | 쿠버네티스 노드 오토스케일러의 전신. 더 느리고 그룹 기반 |
| KAI Scheduler | "GPU 스케줄러" | 갱 + 토폴로지 + 큐를 담당하는 세컨더리 스케줄러 |
| 갱 스케줄링 | "전부 아니면 전무" | N개 파드를 원자적으로 스케줄하거나 전부 미룸 |
| 토폴로지 인식 | "랙 인식" | NVLink/IB/랙 배치에 따라 파드 배치 |
| `DCGM_FI_DEV_GPU_UTIL` | "GPU 활용률" | 듀티 사이클 지표. LLM 스케일링 신호로는 부적합 |
| 큐 깊이 | "대기 요청" | 프리필 병목 확장에 맞는 HPA 신호 |
| KV 캐시 활용률 | "메모리 압박" | 디코드 병목 확장에 맞는 HPA 신호 |
| 통합(Consolidation) | "Karpenter 통합" | 더 저렴한 인스턴스 타입으로 바꾸려고 노드를 종료하는 것 |
| `WhenEmpty + 1h` | "안전한 통합" | 실행 중인 GPU 작업을 쫓아내지 않는 정책 |

## 더 읽을거리

- [KAI Scheduler GitHub](https://github.com/kai-scheduler/KAI-Scheduler) — 설계 문서와 설정 예제.
- [Karpenter Disruption Controls](https://karpenter.sh/docs/concepts/disruption/) — 통합 정책 의미론과 GPU 안전 기본값.
- [NVIDIA — Disaggregated LLM Inference on Kubernetes](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/) — Dynamo Planner 확장 신호.
- [Ray docs — KAI Scheduler for RayClusters](https://docs.ray.io/en/latest/cluster/kubernetes/k8s-ecosystem/kai-scheduler.html) — Ray 통합 패턴.
- [AWS EKS Compute and Autoscaling Best Practices](https://docs.aws.amazon.com/eks/latest/best-practices/aiml-compute.html) — 매니지드 쿠버네티스 특화 가이드.
- [llm-d GitHub](https://github.com/llm-d/llm-d) — Workload Variant Autoscaler 설계.
