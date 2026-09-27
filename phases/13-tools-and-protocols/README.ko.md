> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# Phase 13: 도구 & 프로토콜

> AI와 실제 세계 사이의 인터페이스.

이 페이즈는 함수 호출과 도구 스키마에서 시작해 상호 운용 가능한
프로토콜, 에이전트 스킬, 보안, 프로덕션(운영 환경) 거버넌스로 나아갑니다.
번호 순서는 훑어 보기에 유용합니다. 아래의 집중 경로가 확실한
학습 순서입니다.

## 이 페이즈를 GitHub에서 시작하기

**선수 지식:** Phase 11 LLM 완성 API. MCP나 에이전트 스킬은 번호 순서를
가정하지 말고 아래의 집중 경로를 이용하세요.

**첫 전체 페이즈 레슨:** [The Tool Interface](01-the-tool-interface/)

저장소 루트에서 이 명령을 실행하세요:

```bash
python3 phases/13-tools-and-protocols/01-the-tool-interface/code/main.py
```

명령과 종료 코드, describe-decide-execute-observe 추적, 거부된 입력 증거,
턴 한도를 설명하는 한 문장을 남겨 두세요.

**다음 행동:** [Function Calling Deep Dive](02-function-calling-deep-dive/)로
이어 가거나, 아래의 Model Context Protocol(MCP) 또는 에이전트 스킬 경로를
선택하세요.

[Phase 13 전체 레슨 목록](../../README.md#phase-13)이나
[크로스 페이즈 로드맵](../../ROADMAP.md)을 훑어 볼 수도 있습니다.

## Model Context Protocol (MCP) 경로

집중 MCP 경로는 17개 레슨, 약 23시간 15분입니다. 하나의 자기 기술적
(self-describing) JSON-RPC 요청부터 운영 가능한 적합성 게이트까지
MCP `2026-07-28`을 따라 갑니다.

| 단계 | 레슨 | 증명하는 것 | 시간 |
|---|---|---|---:|
| 코어 | [06](06-mcp-fundamentals/), [07](07-building-an-mcp-server/), [08](08-building-an-mcp-client/), [09](09-mcp-transports/), [10](10-mcp-resources-and-prompts/) | 봉투(envelope), 탐색(discovery), 클라이언트와 서버 동작, 전송(transport), 리소스, 프롬프트. | 5시간 50분 |
| 양방향 | [11](11-mcp-sampling/), [12](12-mcp-roots-and-elicitation/), [13](13-mcp-async-tasks/), [14](14-mcp-apps/) | 서버가 먼저 요청을 보내지 않으면서 MRTR 입력, 명시적 스코프, 영속 태스크, 앱 경계를 다룸. | 5시간 |
| 보안 | [15](15-mcp-security-tool-poisoning/), [16](16-mcp-security-oauth-2-1/), [18](18-mcp-auth-production/), [17](17-mcp-gateways-and-registries/) | 포이즈닝 방어, 인가, 프로덕션 토큰, 게이트웨이 라우팅, 레지스트리 승인. | 5시간 15분 |
| 고급 | [28](28-mcp-tool-contracts-and-content/), [29](29-mcp-reliability-cancellation-and-flow-control/), [30](30-mcp-registry-supply-chain-and-drift/), [31](31-mcp-conformance-versioning-and-operations/) | 계약 충실도, 취소 경쟁 상황, 공급망 드리프트, 릴리스 증거. | 7시간 10분 |

정확한 순서는 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 18, 17, 28,
29, 30, 31입니다.
[`learning-paths/model-context-protocol.json`](../../learning-paths/model-context-protocol.json)에
정의되어 있습니다. 튜터는 `MCP-LEARNING.md`를 만들고, 호출마다 한 레슨을
가르치며, 각 체크포인트가 요구하는 요청, 응답, 명령, 작업 디렉터리, 종료
코드, 마스킹된 경계 증거를 기록합니다.

사용 중인 호스트가 지원하는 호출로 시작하세요:

| 호스트 | 호출 |
|---|---|
| Codex | `learn-mcp`, 또는 `/skills`에서 선택 |
| Claude Code | `/learn-mcp` |
| 기타 호환 호스트 | `Use learn-mcp to start or resume the Model Context Protocol (MCP) path.` |

### 처음 10분

저장소 루트에서 레슨 06의 상태 비저장(stateless) 트랜스크립트를 실행하세요:

```bash
python3 phases/13-tools-and-protocols/06-mcp-fundamentals/code/main.py
```

출력에서 네 가지를 찾아 보세요: 반복되는 요청 메타데이터, 완전한
`server/discover` 결과, 지원하지 않는 버전에 대한 `-32022` 오류, 그리고
MCP 프로토콜 세션을 만들거나 종료하지 않는 전송 종료(transport close).
그 트랜스크립트는 단순한 데모가 아니라 첫 번째 체크포인트입니다.

저장소나 Python 3를 쓸 수 없다면 [레슨 06](06-mcp-fundamentals/)을 읽고
요청과 응답 하나를 손으로 추적해 보세요. 그 체크포인트는 개념 학습으로
표시하고, 런타임, 전송, 인가, 배포 증거는 보류로 남겨 두세요.

루프백이 아닌 바인드, 공유 인그레스, 호스팅 엔드포인트, 레지스트리
게시 전에 반드시 레슨 15의 실행 가능한 보안 체크포인트를 완료하세요.
외부 대상과 요청된 권한을 검토한 뒤 배포 행위를 명시적으로 확인해야
합니다. 튜토리얼을 끝냈다는 사실이 배포 권한을 부여하지는 않습니다.

구형 `initialize`, `Mcp-Session-Id`, 독립 SSE `GET`, 세션 `DELETE`,
서버 주도 요청 흐름은 명시적인 호환성 노트에만 등장합니다. 현대의
요청은 `params._meta`에서 프로토콜 버전과 클라이언트 기능을 선언하고,
`server/discover`를 사용하며, 검증·인가·라우팅·재시도에 충분한 정보를
독립적으로 담고 있습니다.

[레슨 23](23-capstone-tool-ecosystem/)이 MCP 경로의 유일한 선택
캡스톤입니다. 시작하기 전에 요구되는 17개 레슨과 [레슨 19](19-a2a-protocol/),
[레슨 20](20-opentelemetry-genai/)을 완료하세요.

## 에이전트 스킬 고속 경로

집중 경로는 5개 레슨, 약 9시간 30분입니다:

| 단계 | 레슨 | 성과 | 시간 |
|---:|---|---|---:|
| 1 | [22: Portable Contract and Runtime Boundary](22-skills-and-agent-sdks/) | 완전한 스킬 번들을 만들고, 설치하고, 호출하고, 검증하고, 제거합니다. | 90분 |
| 2 | [24: Discovery and Progressive Disclosure](24-skill-discovery-and-progressive-disclosure/) | 탐색, 카탈로그화, 활성화, 리소스 로딩을 추적합니다. | 105분 |
| 3 | [25: Invocation and Routing](25-skill-invocation-and-routing/) | 명시적, 암시적, 사람, 모델, 거부(abstention) 경로를 제어합니다. | 105분 |
| 4 | [26: Permissions, Sandboxes, and Trust](26-skill-permissions-sandboxes-and-trust/) | 지시, 권한, 격리(containment), 검증을 분리합니다. | 120분 |
| 5 | [27: Evals, Packaging, and Portability](27-skill-evals-packaging-and-portability/) | 릴리스 게이트를 만들고 실제 호스트에서 동작을 증명합니다. | 150분 |

사용 중인 호스트가 지원하는 호출로 시작하세요:

| 호스트 | 호출 |
|---|---|
| Codex | `learn-agent-skills`, 또는 `/skills`에서 선택 |
| Claude Code | `/learn-agent-skills` |
| 기타 호환 호스트 | `Use learn-agent-skills to start or resume the Agent Skills Engineering path.` |

튜터는 `AGENT-SKILLS-LEARNING.md`를 만들거나 재개하고, 호출마다 한 레슨을
가르치며, 각 체크포인트가 요구하는 증거를 기록합니다. 이 경로는
[`learning-paths/agent-skills.json`](../../learning-paths/agent-skills.json)에
정의되어 있습니다.

먼저 읽고 싶다면 [레슨 22](22-skills-and-agent-sdks/)부터 시작하세요.
첫 실습에서 약 10분 만에 실제 호스트에 스킬을 넣을 수 있습니다.

### 선수 지식 고속 차선

- 실제 실습을 위해서는 `node`, `npx`, `python3`, 선택한 스킬 지원
  호스트 하나, 그리고 선택한 프로젝트 또는 사용자 스킬 스코프에 대한
  쓰기 권한이 필요합니다. 설치 전에 `node --version`, `npx --version`,
  `python3 --version`으로 세 명령을 확인하세요.
- 이 사전 점검이 불가능하다면 웹사이트를 이용하거나 각 `docs/en.md`를
  직접 읽으세요. 개념 학습은 완료할 수 있지만, 탐색, 호출, 스크립트,
  업데이트, 제거 증거는 보류 표시로 남겨 두어야 합니다.
- 도구 계약이 처음이라면 [레슨 01](01-the-tool-interface/)과
  [레슨 05](05-tool-schema-design/)를 훑어 보세요.
- 레슨 26 전에 도구 포이즈닝과 신뢰할 수 없는 지시를 설명할 수 있는지
  확인하세요. [레슨 15](15-mcp-security-tool-poisoning/)는 그 사전
  점검용 선택 복습이지 이 경로의 여섯 번째 필수 레슨이 아닙니다.
- [레슨 23](23-capstone-tool-ecosystem/)은 선택 시스템 캡스톤이지
  22 다음의 에이전트 스킬 레슨이 아닙니다. 도전하기 전에 레슨 06부터
  20까지를 완료하세요.

## 전체 페이즈

전체 레슨 계획은 [ROADMAP.md](../../ROADMAP.md)를 참고하세요.
