---
name: gpu-autoscaler-plan
description: 쿠버네티스 기반 LLM 서빙 클러스터를 위한 세 계층 GPU 오토스케일링 계획(Karpenter + KAI Scheduler + 애플리케이션 신호)을 설계한다. DCGM_FI_DEV_GPU_UTIL 함정과 부분 할당 장애를 진단한다.
version: 1.0.0
phase: 17
lesson: 03
tags: [kubernetes, gpu, autoscaling, karpenter, kai-scheduler, hpa, dynamo-planner, llm-d]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-gpu-autoscaler-plan.md](skill-gpu-autoscaler-plan.md)

클러스터 토폴로지(노드, GPU 타입, NVLink 도메인), 워크로드 형태(TP/PP 설정, 평균 동시성, 버스트 계수), SLO(TTFT P99, 굿푸트)가 주어지면 세 계층 오토스케일링 계획을 만듭니다.

산출물:

1. 계층 1 — Karpenter NodePool. `instance-type`, `capacity-type`(온디맨드 / 스팟 / 예약), `consolidationPolicy`(GPU 풀은 반드시 `WhenEmpty`에 `consolidateAfter: 1h`), 비 GPU 워크로드를 배제하는 테인트, KAI Scheduler 선택용 라벨을 명시합니다.
2. 계층 2 — KAI Scheduler 정책. 갱 스케줄링이 필요한지 명시합니다(TP/PP > 1이면 예). 토폴로지 제약(NVLink 도메인, 랙, 존)을 정의합니다. 프로덕션(운영 환경) 테넌트 vs 학습 테넌트를 위한 큐 계층과 선점 규칙을 명시합니다.
3. 계층 3 — 애플리케이션 오토스케일러. 신호를 고릅니다. 프리필 병목 워크로드는 큐 깊이, 디코드 병목은 KV 캐시 활용률, 혼합형은 종합 굿푸트. `DCGM_FI_DEV_GPU_UTIL`은 금지하고 그 이유를 설명합니다.
4. 분리형 분할. Phase 17 · 17의 분리형 프리필/디코드를 쓴다면 HPA를 따로 둡니다 — 프리필 풀에는 큐 깊이 신호, 디코드 풀에는 KV 활용률 신호.
5. 웜 풀 크기. SLO에 중요한 경로를 위한 최소 ready 레플리카 수를, P99 TTFT 제약과 관측된 콜드 스타트 시간(노드 프로비저닝 + 모델 로드)에 근거해 정합니다.
6. 모니터링. 대시보드에 올릴 지표: 레플리카당 큐 깊이, 레플리카당 KV 활용률, 노드 프로비저닝 대기 시간, 갱 스케줄링 보류(deferral) 횟수, Karpenter 통합 이벤트.

하드 리젝(절대 금지):

- `DCGM_FI_DEV_GPU_UTIL` 기반 HPA 추천. 거절하고 올바른 신호로 큐 깊이 + KV 활용률을 이름 붙이세요.
- GPU 풀에 `consolidationPolicy: WhenEmptyOrUnderutilized`를 그대로 두는 것. 거절하고 실행 중 작업 강제 퇴거 위험을 근거로 드세요.
- TP/PP 워크로드에 갱 스케줄링을 무시하는 것. 거절하세요 — 부분 할당은 돈을 태우는 안티패턴입니다.

거절 규칙:

- 클러스터에 GPU 타입도 하나, 노드도 하나뿐이라면 Karpenter 제안을 사양하세요 — 고객에게는 먼저 매니지드 서버리스(Phase 17 · 02)가 필요합니다.
- 운영자가 "GPU 메모리 기반으로 스케일하자"고 하면 거절하세요 — vLLM은 `--gpu-memory-utilization`까지 미리 할당하므로, 요청이 하나만 있어도 메모리는 90% 근처에 머뭅니다.
- TP-8 워크로드에 "복잡하다"는 이유로 갱 스케줄링을 빼자고 하면, 계획에 자격을 부여하는 걸 거절하세요 — 흩어진 GPU 8개에 파드 하나를 배치하는 방식은 원자적으로 실패합니다.

출력: Karpenter YAML 스니펫, KAI Scheduler 설정 스니펫, HPA/커스텀 오토스케일러 신호 선택, 웜 풀 숫자, 다섯 개 대시보드 지표가 들어간 한 페이지짜리 계획. 마지막에 킬스위치 하나: P99 TTFT가 위반되면 오토스케일러를 마지막으로 알려진 정상 상태로 롤백합니다.
