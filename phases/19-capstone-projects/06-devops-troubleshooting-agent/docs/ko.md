> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 06 — 쿠버네티스용 DevOps 문제 해결 에이전트

> AWS의 DevOps Agent가 GA(정식 출시)를 맞았고, Resolve AI는 K8s 플레이북을 공개했고, NeuBird는 시맨틱 모니터링을 시연했고, Metoro는 AI SRE를 서비스별 SLO에 묶었습니다. 프로덕션(운영 환경) 형태는 정형화되어 있습니다: 알림 웹훅이 발사되면, 에이전트가 텔레메트리를 읽고, K8s 객체 그래프를 걸어 다니고, 원인(root-cause) 가설의 순위를 매기고, 승인 버튼이 달린 Slack 요약을 올립니다. 기본값은 읽기 전용. 모든 복구 작업에는 사람의 승인이 필요합니다. 이 캡스톤이 바로 그 에이전트입니다. 20개의 합성 장애로 평가하고, 세 개의 공유 사례에서 AWS의 Agent와 비교합니다.

**유형:** Capstone
**언어:** Python (에이전트), TypeScript (Slack 통합)
**선수 지식:** 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구와 MCP), 페이즈 14 (에이전트), 페이즈 15 (자율 시스템), 페이즈 17 (인프라), 페이즈 18 (안전)
**활용하는 페이즈:** P11 · P13 · P14 · P15 · P17 · P18
**시간:** 30시간

## 문제

2025~2026년 SRE 서사는 이렇게 굳어졌습니다: "AI 에이전트가 장애를 분류하고, 사람이 복구를 승인한다." AWS DevOps Agent, Resolve AI, NeuBird, Metoro, PagerDuty AIOps가 모두 이 형태를 프로덕션으로 내놓습니다. 에이전트는 Prometheus 지표, Loki 로그, Tempo 트레이스, kube-state-metrics, 그리고 K8s 객체 지식 그래프를 읽습니다. 5분 안에 텔레메트리 인용이 붙은 순위 매겨진 원인 가설을 만들어 냅니다. Slack을 통한 명시적 사람 승인 없이는 파괴적 명령을 절대 실행하지 않습니다.

어려운 작업 대부분은 추론이 아니라 범위 설정과 안전입니다. 에이전트는 읽기 전용 기본값의 RBAC 표면, 강화된 MCP 도구 서버, 검토한 명령과 실행한 명령 모두의 감사 로그가 필요합니다. 자기 능력 밖임을 알아차리고 에스컬레이션할 줄도 알아야 합니다. 그리고 OOM 킬 연쇄가 $5k짜리 에이전트 청구서를 만들지 않을 만큼 싸게 돌아가야 합니다.

## 개념

에이전트는 지식 그래프 위에서 동작합니다. 노드는 K8s 객체(Pod, Deployment, Service, Node, HPA, PVC)와 텔레메트리 소스(Prometheus 시계열, Loki 스트림, Tempo 트레이스)입니다. 에지는 소유 관계(Pod -> ReplicaSet -> Deployment), 스케줄링(Pod -> Node), 관찰 관계(Pod -> Prometheus 시계열)를 인코딩합니다. 그래프는 kube-state-metrics 동기화로 신선하게 유지되고, 알림이 올 때마다 다시 샘플링됩니다.

알림이 발사되면 에이전트는 영향받은 객체에서 원인을 추적합니다. 에지를 따라 걷고, 관련 텔레메트리 조각(최근 15분)을 당겨 오고, 가설 초안을 만듭니다. 가설은 증거로 순위가 매겨집니다: 얼마나 많은 텔레메트리 인용이 뒷받침하는지, 얼마나 최근인지, 얼마나 구체적인지. 상위 3개 가설은 그래프 경로 시각화와 복구 작업 승인 버튼과 함께 Slack으로 갑니다.

복구는 관문을 통과합니다. 기본 허용 동작은 읽기 전용입니다. 파괴적 동작(스케일 다운, 롤백, Pod 삭제)에는 Slack 승인이 필요하고, ArgoCD 롤백 훅에는 에이전트가 절대 쥐지 않는 인증 토큰이 필요합니다. 감사 로그는 에이전트가 *검토한* 모든 명령을 기록합니다 — 실행한 것만이 아니라요 — 그래야 검토 과정이 아슬아슬하게 빗나간 사례(near-miss)를 잡아냅니다.

## 아키텍처

```
PagerDuty / Alertmanager webhook
           |
           v
     FastAPI receiver
           |
           v
   LangGraph root-cause agent
           |
           +---- read-only MCP tools ----+
           |                             |
           v                             v
   K8s knowledge graph              telemetry slices
     (Neo4j / kuzu)              Prometheus, Loki, Tempo
   ownership + scheduling          last 15m, scoped
           |
           v
   hypothesis ranking (evidence weight)
           |
           v
   Slack brief + approval buttons
           |
           v (approved)
   ArgoCD rollback hook / PagerDuty escalate
           |
           v
   audit log: considered vs executed, every command
```

## 스택

- 관측 가능성 소스: Prometheus, Loki, Tempo, kube-state-metrics
- 지식 그래프: K8s 객체 + 텔레메트리 에지를 담은 Neo4j(매니지드) 또는 kuzu(임베디드)
- 에이전트: 도구별 허용 목록을 갖춘 LangGraph, 기본값은 읽기 전용
- 도구 전송: StreamableHTTP 위의 FastMCP; 파괴적 도구는 승인 게이트 뒤 별도 서버로
- 모델: 원인 추론용 Claude Sonnet 4.7, 로그 요약용 Gemini 2.5 Flash
- 복구: ArgoCD 롤백 웹훅, PagerDuty 에스컬레이션, Slack 승인 카드
- 감사: 추가 전용(append-only) 구조화 로그(검토됨, 실행됨, 승인됨, 결과)
- 배포: 자체 좁은 RBAC 역할을 가진 K8s 배포; 별도 네임스페이스

```figure
ce-rootcause-walk
```

## 만들기

1. **그래프 수집.** kube-state-metrics를 30초마다 Neo4j/kuzu로 동기화합니다. 노드: Pod, Deployment, Node, Service, PVC, HPA. 에지: OWNED_BY, SCHEDULED_ON, EXPOSES, MOUNTS, SCALES. 텔레메트리 오버레이 에지: OBSERVED_BY(Pod가 Prometheus 시계열에 의해 관찰됨).

2. **알림 수신기.** PagerDuty 또는 Alertmanager 웹훅을 받는 FastAPI 엔드포인트. 영향받은 객체와 SLO 위반을 추출합니다.

3. **읽기 전용 도구 표면.** kubectl, Prometheus 쿼리, Loki logql, Tempo traceql을 FastMCP로 감쌉니다. 모든 도구는 좁은 RBAC 동사("get", "list", "describe")만 가집니다. 기본 서버에는 "delete", "exec", "scale"이 없습니다.

4. **원인 분석 에이전트.** 노드 셋을 가진 LangGraph: `sample`은 최근 15분 텔레메트리 조각을 당겨 오고, `walk`는 그래프에서 인접 객체를 찾고, `hypothesize`는 텔레메트리 인용이 붙은 순위 매겨진 원인 후보 초안을 만듭니다.

5. **증거 점수.** 각 가설의 점수 = 최신성 * 구체성 * 그래프 경로 길이의 역수 * 인용 수. 상위 3개를 돌려줍니다.

6. **Slack 요약.** 가설, 그래프 경로 시각화(서버 쪽에서 렌더링한 서브그래프 이미지), 그리고 최대 하나의 복구 작업 승인 버튼을 담은 첨부를 올립니다.

7. **복구 관문.** 파괴적 도구(스케일 다운, 롤백, 삭제)는 승인 토큰 뒤의 두 번째 MCP 서버에 삽니다. 에이전트는 Slack 카드가 사람에게 승인된 후에만 호출할 수 있습니다.

8. **감사 로그.** 추가 전용 JSONL: 후보 명령마다 검토되었는지, 실행되었는지, 누가 승인했는지 기록합니다. 매일 S3로 보냅니다.

9. **합성 장애 모음.** 시나리오 20개를 만듭니다: OOMKill 연쇄, DNS 흔들림, HPA 스래싱, PVC 꽉 참, 시끄러운 이웃, 고장난 사이드카, 잘못된 ConfigMap 롤아웃, 인증서 순환, 이미지 풀 백오프 등. 에이전트를 원인 분석 정확도와 가설 도달 시간으로 채점합니다.

## 사용해 보기

```
webhook: alert.pagerduty.com -> checkout-api SLO breach, error rate 14%
[graph]   affected: Deployment checkout-api (3 Pods, Node ip-10-2-3-4)
[walk]    neighbors: ReplicaSet checkout-api-abc, Service checkout-api,
           recent rollout 14m ago
[sample]  prometheus error_rate 14%, up-trend; loki 500s on /api/v2/pay
[hypo]    #1 bad rollout: latest image checkout-api:v2.41 fails /healthz
          citations: deploy.yaml (rev 42), prometheus errorRate, loki 500 stack
[slack]   [ROLL BACK to v2.40]  [ESCALATE]  [IGNORE]
          (approval required; agent does not roll back unilaterally)
```

## 출시하기

`outputs/skill-devops-agent.md`가 산출물입니다. K8s 클러스터와 알림 소스가 주어지면 에이전트는 순위 매겨진 원인 가설과 Slack 승인 복구 흐름을 만들어 냅니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 시나리오 모음에서 RCA 정확도 | 20개 합성 장애에서 올바른 원인 ≥80% |
| 20 | 안전 | 감사 로그에 Slack 승인 없이 파괴적 동작 가드가 발사된 적 없음 |
| 20 | 가설 도달 시간 | 알림부터 Slack 요약까지 p50 5분 미만 |
| 20 | 설명 가능성 | 모든 가설에 그래프 경로와 텔레메트리 인용이 있음 |
| 15 | 통합 완전성 | PagerDuty, Slack, ArgoCD, Prometheus가 끝까지 동작 |
| **100** | | |

## 연습 문제

1. AWS DevOps Agent가 데모되는 같은 세 장애에 당신의 에이전트를 돌려 보세요. 나란히 비교를 공개하고, 어디서 갈라지는지 보고하세요.

2. "아슬아슬하게 빗나간(near-miss)" 감사를 추가하세요. 승인 없이는 파괴적이었을 명령 중 에이전트가 *검토한* 것을 표시합니다. 한 주간의 near-miss 비율을 측정하세요.

3. 가설 모델을 Claude Sonnet 4.7에서 셀프 호스팅 Llama 3.3 70B로 바꿔 보세요. RCA 정확도 변화와 장애당 비용을 측정하세요.

4. 인과 필터를 만들어 보세요: 상관된 텔레메트리 스파이크와 진짜 원인을 구분합니다. 20개 시나리오 라벨로 작은 분류기를 학습시키세요.

5. 롤백 드라이런을 추가하세요: 같은 매니페스트로 스테이징 클러스터에 ArgoCD 롤백을 돌립니다. Slack 승인 버튼 전에 실제 클러스터의 롤백 계획을 검증합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| K8s 지식 그래프 | "클러스터 그래프" | 노드 = K8s 객체 + 텔레메트리 시계열. 에지 = 소유, 스케줄링, 관찰 |
| 읽기 전용 기본값 | "범위가 좁은 RBAC" | 에이전트의 서비스 계정은 get/list/describe 동사만 가짐. 파괴적 동사는 승인 뒤 별도 서버에 |
| 감사 로그 | "검토 vs 실행" | 모든 후보 명령, 실행 여부, 승인자의 추가 전용 기록 |
| 가설 순위 | "증거 점수" | 최신성 × 구체성 × 그래프 경로 길이의 역수 × 인용 수 |
| Slack 승인 카드 | "HITL 관문" | 복구 버튼이 달린 대화형 Slack 메시지. 사람이 클릭하기 전까지 에이전트는 진행 불가 |
| 텔레메트리 인용 | "증거 포인터" | 주장을 뒷받침하는 Prometheus 쿼리, Loki 셀렉터, 또는 Tempo 트레이스 URL |
| MTTR | "해결까지 시간" | 알림 발사부터 SLO 회복까지의 실제 시간 |

## 더 읽을거리

- [AWS DevOps Agent GA](https://aws.amazon.com/blogs/aws/aws-devops-agent-helps-you-accelerate-incident-response-and-improve-system-reliability-preview/) — 2026년의 표준 참고자료
- [Resolve AI K8s 문제 해결](https://resolve.ai/blog/kubernetes-troubleshooting-in-resolve-ai) — 경쟁사 참고자료
- [NeuBird 시맨틱 모니터링](https://www.neubird.ai) — 시맨틱 그래프 접근
- [Metoro AI SRE](https://metoro.io) — SLO 우선 프로덕션 프레이밍
- [kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) — 클러스터 상태 소스
- [LangGraph](https://langchain-ai.github.io/langgraph/) — 참고용 에이전트 오케스트레이터
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP 서버 프레임워크
- [ArgoCD 롤백](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd_app_rollback/) — 관문을 거치는 복구 대상
