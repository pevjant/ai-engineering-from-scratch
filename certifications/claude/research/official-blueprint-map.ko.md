> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [official-blueprint-map.md](official-blueprint-map.md)

# 공식 Claude 자격증 블루프린트 지도

> 커리큘럼 관리자를 위한 원본 기준(source-of-truth) 메모입니다. 출시 전에 반드시 다시 검증하세요.

**검증일:** 2026-08-09
**시험 가이드 버전:** 1.0
**시행:** 2026년 7월

## 공식 가이드

- [CCAO-F 시험 가이드](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542847%2FClaude+Certified+Associate+%E2%80%93+Foundations+Exam+Guide.pdf)
- [CCDV-F 시험 가이드](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542875%2FClaude+Certified+Developer+%E2%80%93+Foundations+Exam+Guide.pdf)
- [CCAR-F 시험 가이드](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542750%2FClaude+Certified+Architect+%E2%80%93+Foundations+Exam+Guide.pdf)
- [CCAR-P 시험 가이드](https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542810%2FClaude+Certified+Architect+%E2%80%93+Professional+Exam+Guide.pdf)

## 커버리지 전략

이 저장소에는 프롬프팅, 구조화된 출력, 컨텍스트 엔지니어링, 평가, 에이전트, 도구
설계, MCP, 보안, RAG, 관측 가능성(옵저버빌리티), 프로덕션 운영을 위한 튼튼한
기반이 이미 있습니다. 자격증 섹션은 페이즈 커리큘럼이 하지 말아야 할 세 가지 일을
합니다:

1. 각 주제를 시험 스타일 제약 아래의 블루프린트 결정으로 프레임한다.
2. Claude 고유의 제품, API, 구성, 라이프사이클 빈틈을 메운다.
3. 역할별 캡스톤과 가중 평가를 조립한다.

기존 과정에서 발견된 가장 중요한 빈틈은 다음과 같습니다:

- Claude 채팅, 리서치, Projects, Artifacts, 프로젝트 지식 관리.
- 콘텐츠 블록, stop reason, 도구 계속 진행, 스트리밍, 사고(thinking), 캐싱,
  배치 트레이드오프를 아우르는 일관된 Messages API 상태 기계.
- Claude Code 구성 우선순위, Rules, 스킬, 커맨드, 에이전트, 메모리, 헤드리스
  실행, CI 워크플로.
- 비즈니스 디스커버리, 이해관계자 커뮤니케이션, 아키텍처 방어, 구현 인수인계,
  운영 담당 체계.

현재 Anthropic Academy 카탈로그를 대조한 두 번째 점검은 공개 블루프린트를
바꾸지 않으면서 제품 표면 깊이를 더했습니다:

- 직접 Claude, Amazon Bedrock, Google Vertex AI, Microsoft Foundry 배포 결정.
- SDK, REST, 스트리밍, 비동기, 멀티모달, Files API, Tool Runner, 관리형
  에이전트 접근 패턴.
- 고급 MCP 샘플링, 루트(roots), 알림, Inspector, Streamable HTTP, 상태 유형 대
  무상태(stateful vs stateless) 배포 결정.
- 현재 Claude Code 운영 통제, 실제 스킬 작성, 서브에이전트 계약, 팀 배포.
- 다음 토큰 예측, 지식, 작업 메모리, 조종 가능성(steerability)을 위한 네 속성
  진단법.

## 기존 심화 자료

이 자료들의 스크래치부터 가르치기를 복제하지 말고 그대로 활용하세요:

| 기능 | 기존 레슨 경로 |
|------------|-----------------------|
| 프롬프팅과 few-shot 추론 | `phases/11-llm-engineering/01-prompt-engineering`, `phases/11-llm-engineering/02-few-shot-cot` |
| 구조화된 출력 | `phases/11-llm-engineering/03-structured-outputs`, `phases/13-tools-and-protocols/04-structured-output` |
| 컨텍스트와 캐싱 | `phases/11-llm-engineering/05-context-engineering`, `phases/11-llm-engineering/11-caching-cost`, `phases/11-llm-engineering/15-prompt-caching` |
| 평가 | `phases/11-llm-engineering/10-evaluation`, `phases/14-agent-engineering/30-eval-driven-agent-development` |
| 에이전트 루프와 오케스트레이션 | `phases/14-agent-engineering/01-the-agent-loop`, `phases/14-agent-engineering/12-anthropic-workflow-patterns`, `phases/14-agent-engineering/28-orchestration-patterns` |
| Claude Agent SDK | `phases/14-agent-engineering/17-claude-agent-sdk` |
| 도구와 MCP 설계 | `phases/13-tools-and-protocols/01-the-tool-interface`, `phases/13-tools-and-protocols/05-tool-schema-design`, `phases/13-tools-and-protocols/06-mcp-fundamentals`, `phases/13-tools-and-protocols/07-building-an-mcp-server`, `phases/13-tools-and-protocols/11-mcp-sampling`, `phases/13-tools-and-protocols/12-mcp-roots-and-elicitation` |
| 보안과 승인 | `phases/14-agent-engineering/27-prompt-injection-defense`, `phases/15-autonomous-systems/10-claude-code-permission-modes`, `phases/17-infrastructure-and-production/25-security-secrets-audit` |
| RAG와 검색 | `phases/11-llm-engineering/06-rag`, `phases/11-llm-engineering/07-advanced-rag`, `phases/19-capstone-projects/65-hybrid-retrieval-bm25-dense` |
| 관측 가능성과 운영 | `phases/17-infrastructure-and-production/13-llm-observability`, `phases/17-infrastructure-and-production/23-sre-for-ai`, `phases/17-infrastructure-and-production/27-finops-llms` |

## 트랙별 강조

### CCAO-F

가중치가 가장 높은 도메인은 21%를 차지하는 출력 평가와 검증입니다. 그래서 이
루트는 프롬프트 문법보다 사실 검증, 편향 점검, 청자 적합성, 적절한 형식, 사람
검토에 더 많은 시간을 씁니다.

### CCDV-F

애플리케이션과 통합이 33.1%입니다. 이 루트는 프로토콜 먼저입니다: Messages API
상태, 애플리케이션 경계, SDK와 REST 동작, 세션 위생, 구성, 도구, 프로덕션 실패
격리.

### CCAR-F

시험은 현실적인 시나리오를 중심으로 구성됩니다. 이 루트는 공개된 여섯 시나리오
컨텍스트를 관통하는 반복 가능한 결정 방법을 가르치며, 27%를 차지하는 에이전트형
아키텍처와 오케스트레이션에 가장 많은 시간을 씁니다.

### CCAR-P

통합이 19%로 가장 큰 단일 도메인이지만, Professional은 전체 라이프사이클
시험입니다. 이 과정은 디스커버리, 아키텍처, 프롬프팅, RAG, 평가, 안전,
이해관계자 커뮤니케이션, Claude Code 도입, 운영 담당 체계를 따로 떨어진 사실로
다루지 않고 서로 연결해서 가르칩니다.
