> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [architecture-packet.md](architecture-packet.md)

# 아키텍트 Foundations 시나리오 패킷

오리지널 시나리오 하나에 대해 이 패킷을 완성한 뒤, 나머지 다섯 공개 컨텍스트 카테고리 각각에 대해 델타(변경분)를 작성하세요. 대괄호 안의 안내 문구를 증거로 바꾸세요.

## 1. 시나리오 경계

```text
Scenario ID:
Public context category:
Decision supported:
Users and affected people:
Allowed actions:
Prohibited actions:
Input sources and sensitivity:
Latency and volume:
Failure consequence:
Human decision authority:
```

## 2. 에이전틱 아키텍처와 오케스트레이션

### 의존성 그래프

```mermaid
flowchart LR
    A["접수"] --> B["범위가 한정된 분석"]
    B --> C["검증된 후보"]
    C --> D["독립 리뷰"]
    D --> E["사람의 결정"]
```

| 작업 ID | 별도 컨텍스트로 분리하는 이유 | 선수 조건 | 허용 도구 | 완료 | 부분 | 차단 |
|---|---|---|---|---|---|---|
| [task] | [isolation, specialization, parallelism, or review] | [IDs] | [names] | [gate] | [named gaps] | [required state] |

```text
Deterministic prerequisites:
Adaptive decisions:
Parallelism limit:
Merge identity and conflict rules:
Resume, fork, and compaction policy:
```

## 3. 도구와 MCP 계약

| 도구 또는 프리미티브 | 사용하는 경우 | 사용하지 않는 경우 | 닫힌 입력 스키마 | 결과와 오류 | 인가 범위 | 부수 효과 |
|---|---|---|---|---|---|---|
| [name] | [positive rule] | [negative rule] | [object schema] | [complete, partial, blocked] | [scope] | [none or bounded write] |

각 입력 경계를 검증기 패킷에 `input_schema`로 옮겨 적으세요. 모든 속성 타입을 명시하고, 선언된 속성만 필수로 요구하며, `additionalProperties`는 `false`로 설정해야 합니다. 인수가 없는 도구도 빈 `properties`와 `required` 배열을 가진 닫힌 객체 스키마를 사용합니다.

```json
{
  "type": "object",
  "properties": {
    "case_id": {"type": "string"}
  },
  "required": ["case_id"],
  "additionalProperties": false
}
```

```text
MCP server scope:
Resources:
Tools:
Prompts:
Progressive discovery policy:
Write authorization:
Idempotency and reconciliation:
Secret provisioning:
```

## 4. Claude Code 구성과 워크플로

```text
Root project guidance:
Imported guidance:
Path-specific rules and tested globs:
Skills:
Commands:
Agents and allowed tools:
Hooks and enforced invariants:
Plan or interview boundary:
User-local configuration excluded from team policy:
```

### 헤드리스 CI

- [ ] 깨끗한 커밋과 선언된 입력에서 시작한다.
- [ ] 버전 관리되는 프로젝트 구성을 사용한다.
- [ ] 범위가 한정된 읽기 전용 리뷰 도구를 가진다.
- [ ] 안정적인 ID와 함께 구조화된 발견 항목을 출력한다.
- [ ] 결정론적 테스트와 정책 게이트를 분리해서 실행한다.
- [ ] 보완(remediation) 리뷰를 위해 이전 발견 항목 ID를 받는다.
- [ ] 현재 모델과 런타임 구성을 기록한다.

## 5. 프롬프트와 구조화 출력

```text
Evaluation criteria:
Boundary examples:
Prompt contract version:
Schema version:
Representation for unknown or unsupported values:
Tool-choice policy:
Syntax validator:
Schema validator:
Semantic validator:
Provenance validator:
Retry limit and feedback contract:
Independent reviewer inputs and output:
Batch or real-time decision:
```

## 6. 컨텍스트 관리와 신뢰성

```text
Critical fact placement:
Context budget:
Manifest location and schema:
Scratchpad lifecycle:
Subagent context boundaries:
Compaction and resume packet:
Tool-output trimming rules:
Complete, partial, and blocked propagation:
Provenance fields:
Source conflict and date rules:
Content-type extraction and rendering checks:
Confidence evidence classes:
Human review strata and random sample:
Escalation owners:
```

## 7. 실패 픽스처

| ID | 주입한 실패 | 탐지 | 봉쇄 | 재시도 또는 에스컬레이션 | 지속 증거 | 소유자 |
|---|---|---|---|---|---|---|
| [failure] | [condition] | [signal] | [safe stop] | [rule] | [artifact] | [role] |

필수 커버리지:

- [ ] 오케스트레이션 선수 조건, 부분 결과, 또는 오래된 상태에서의 재개(resume).
- [ ] 도구 검증, 인가, 충돌, 타임아웃, 또는 알 수 없는 부수 효과.
- [ ] Claude Code 규칙 범위, 퍼미션, 훅, 또는 클린 CI 실패.
- [ ] 스키마는 통과하지만 의미 또는 출처(provenance)가 실패하는 케이스.
- [ ] 사라진 사실, 충돌하는 소스, 콘텐츠 유형, 또는 에스컬레이션 실패.

## 8. 아키텍처 결정

주요 선택 하나하나마다 기록을 하나씩 완성합니다.

```text
Decision ID:
Context and forces:
Chosen option:
Alternatives rejected:
Tradeoff accepted:
Evidence:
Change trigger:
Owner:
```

## 9. 교차 시나리오 델타

기본 시나리오를 포함해 여섯 컨텍스트 모두에 대해 반복합니다.

```text
Context category:
Core invariants retained:
New source or authority boundary:
New tool or MCP requirement:
New Claude Code configuration requirement:
New output and validation requirement:
New context and escalation risk:
Control removed or added, with reason:
```

## 10. 리뷰와 인수인계

```text
Decision owner:
Implementation owner:
Independent reviewer:
Validator result:
Finding IDs and dispositions:
Evidence artifacts:
Residual risks and owners:
Fallback:
Rollout boundary:
Model, API, SDK, Claude Code, or MCP change triggers:
Next verification date:
```

릴리스 권고:

- [ ] 권한, 정책, 증거, 또는 아키텍처 교정이 끝날 때까지 차단.
- [ ] 섀도우 또는 읽기 전용 파일럿 준비 완료.
- [ ] 범위가 한정된 사람 검토 사용 준비 완료.
- [ ] 구체적으로 이름 붙은 저영향 자동화 준비 완료.

근거:

```text
[어떤 시나리오와 실패를 테스트했고, 어떤 불변식이 통과했고, 무엇이 아직 불확실한지, 결정을 누가 소유하는지 서술한다.]
```
