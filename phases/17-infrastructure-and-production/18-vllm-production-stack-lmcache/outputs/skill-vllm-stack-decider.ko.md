---
name: vllm-stack-decider
description: vLLM 배포 구성을 결정합니다 — production-stack Helm 차트, KV 오프로드(네이티브 CPU 또는 LMCache), 라우터/관측 통합 — 워크로드와 플릿 크기가 주어지면.
version: 1.0.0
phase: 17
lesson: 18
tags: [vllm, production-stack, lmcache, kv-offload, connector-api]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-vllm-stack-decider.md](skill-vllm-stack-decider.md)

워크로드(프롬프트 형태, 동시성, 프리픽스 재사용 패턴), 플릿(엔진, GPU 유형), 운영 환경(Kubernetes 네이티브, 멀티테넌트, 예산)이 주어지면 vLLM 스택 계획을 만들어 냅니다.

산출물:

1. 스택. vLLM production-stack Helm 차트(신규 배포에 권장)를 쓰거나 직접 구성합니다. 어떤 오퍼레이터/CRD가 적용되는지 밝힙니다.
2. KV 오프로드. 고르세요:
   - 없음(짧은 프롬프트, 낮은 동시성 — 오버헤드가 이득을 넘음).
   - 네이티브 vLLM CPU 오프로드(단일 엔진 HBM 압박, 간단함).
   - LMCache 커넥터(멀티 엔진 프리픽스 재사용, 선점 잦음, 또는 멀티테넌트 공유 프롬프트).
3. HBM 사용률 모니터링. `--gpu-memory-utilization`을 여유를 두고 설정; 지속 92% 이상에서 알림 — 선점 전조 신호입니다.
4. 라우터 통합. 캐시 인지 라우터(페이즈 17 · 11). KV 이벤트 채널이 설정됐는지 확인합니다.
5. 관측. 엔진별 Prometheus 스크레이프, OTel GenAI 속성(페이즈 17 · 13), production-stack의 Grafana 대시보드 템플릿.
6. 예상 영향. 현재 대비 예상 처리량 증가를 수치화 — 16x H100 벤치마크 형태를 참고(KV 발자국이 HBM을 넘을 때 LMCache가 도움됩니다).

하드 리젝(무조건 거절):

- 공유 프리픽스나 선점 없이 LMCache를 배포하는 것. 거절하세요 — 오버헤드만 있고 이득이 없습니다.
- HBM 압박 모니터링 없이 vLLM을 돌리는 것. 거절하세요 — 첫 선점은 놀람으로 다가옵니다.
- Helm 차트가 용례를 커버하는데 production-stack을 손수 만드는 것. 거절하세요 — 재발명 비용입니다.

거절 규칙:

- 플릿이 엔진 2개 미만이면 LMCache를 거절 — 교차 엔진 재사용이 핵심입니다; 단일 엔진이면 네이티브를 씁니다.
- 워크로드의 프롬프트가 1K 토큰 미만이고 동시성이 100 미만이면 어떤 오프로드도 거절 — HBM 여유로 충분합니다.
- 팀에 K8s 역량이 없다면 production-stack을 거절 — 단일 엔진 vLLM + 간단한 프록시로 시작합니다.

출력: 스택, KV 오프로드 선택, HBM 모니터링, 라우터 통합, 관측, 예상 영향을 적은 한 페이지짜리 계획서. 마지막에 단 하나의 관문으로 마무리합니다: 직전 24시간의 HBM 사용률 P99.
