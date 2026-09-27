---
name: devops-agent
description: 클러스터 지식 그래프를 걷고, 원인의 순위를 매기고, 모든 복구를 Slack 관문으로 통과시키는 쿠버네티스 문제 해결 에이전트를 만듭니다.
version: 1.0.0
phase: 19
lesson: 06
tags: [capstone, devops, sre, kubernetes, langgraph, fastmcp, aiops]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-devops-agent.md](skill-devops-agent.md)

K8s 클러스터와 알림 소스(PagerDuty 또는 Alertmanager)가 주어지면, 5분 안에 순위 매겨진 원인 가설을 만들어 내고 모든 복구를 Slack 승인 카드 관문으로 통과시키는 에이전트를 만듭니다.

만들기 계획:

1. kube-state-metrics를 30초마다 Neo4j 또는 kuzu로 수집합니다. Pod, Deployment, Service, Node, PVC, HPA의 그래프와 함께 Prometheus, Loki, Tempo 소스로 가는 텔레메트리 오버레이 에지를 만듭니다.
2. PagerDuty와 Alertmanager를 위한 FastAPI 웹훅 수신기를 세웁니다.
3. 읽기 전용 도구를 StreamableHTTP 전송의 FastMCP로 노출합니다: kubectl get/describe, promql, logql, traceql.
4. 노드 셋을 가진 LangGraph 원인 분석 에이전트를 만듭니다: `sample`(15분 텔레메트리 당겨 오기), `walk`(그래프 이웃 순회), `hypothesize`(최신성 × 구체성 × 인용 수로 후보 순위 매기기).
5. 상위 3개 순위 가설을 그래프 경로 시각화와 함께 승인 버튼을 붙여 Slack에 올립니다.
6. 파괴적 도구(스케일, 롤백, 삭제)는 에이전트가 Slack 서명 후에만 얻는 승인 토큰 뒤의 별도 FastMCP 서버에 둡니다.
7. 추가 전용 감사 로그를 유지합니다: *검토된* 모든 명령, 승인 여부, 실행 여부, 승인자.
8. 합성 장애 시나리오 20개를 만듭니다(OOMKill, DNS 흔들림, HPA 스래싱, PVC 꽉 참, 시끄러운 이웃, 고장난 사이드카, ConfigMap 잘못된 롤아웃, 인증서 순환, 이미지 풀 백오프, 프로브 실패, 그리고 10개 더). 에이전트를 RCA 정확도와 가설 도달 시간으로 채점합니다.

채점 기준:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | 시나리오 모음에서 RCA 정확도 | 20개 합성 장애에서 올바른 원인 최소 80% |
| 20 | 안전 | 감사 로그에 Slack 승인 없이 파괴적 동작 가드가 발사된 적 없음 |
| 20 | 가설 도달 시간 | 알림부터 Slack 요약까지 p50 5분 미만 |
| 20 | 설명 가능성 | 모든 가설에 그래프 경로와 텔레메트리 인용이 있음 |
| 15 | 통합 완전성 | PagerDuty, Slack, ArgoCD, Prometheus가 끝까지 동작 |

하드 리젝트(무조건 반려):

- 읽기 전용 도구와 파괴적 도구를 한 MCP 서버에 섞어 놓은 에이전트.
- 텔레메트리 인용 없이 만들어진 어떤 RCA든. 인용 없는 가설은 반려해야 합니다.
- 실행만 기록하는 감사 로그. 검토한 모든 명령을 기록해야 합니다.
- 시드를 적용한 20개 시나리오 모음으로 에이전트를 돌리지 않고 정확도를 주장하는 것.

거절 규칙:

- 온콜 담당자의 Slack 승인 없이 복구하는 것을 거절하세요. 가설이 명백해 보여도요.
- 읽기 전용 MCP를 통해 `kubectl exec`, `kubectl port-forward`, 또는 어떤 대화형 도구든 노출하는 것을 거절하세요. 효과 면에서 파괴적입니다.
- 배포별 승인 카드 없이 여러 배포에 복구를 일괄 적용하는 것을 거절하세요.

출력: FastAPI 수신기, LangGraph 에이전트, 읽기 전용 및 파괴적 MCP 서버, Slack 통합, 20개 시나리오 테스트 모음, 세 개의 공유 장애에서 AWS DevOps Agent와의 나란히 비교, 그리고 1주간 관찰 윈도우의 near-miss 명령(에이전트가 *검토했지만 실행하지 않은 것들*)에 대한 보고서가 담긴 저장소.
