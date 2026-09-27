> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 스킬 호출과 라우팅

> 호출은 '권한이 있는가'를 묻는 결정 다음에 '관련이 있는가'를 묻는 결정입니다. 좋은 description은 모델이 선택하게 돕고, 좋은 정책은 그 선택이 허용되는지를 결정합니다.

**유형:** 빌드(Build)
**언어:** Python(표준 라이브러리)
**선수 지식:** 페이즈 13 · 24(스킬 발견과 점진적 공개)
**시간:** 약 105분

## 학습 목표

- 사용자 명시적 호출, 모델 암시적 호출, 애플리케이션 호출, 스킬-스킬 호출을 구분합니다.
- 사람 가시성과 모델 자격을 독립적인 정책 차원으로 모델링합니다.
- 긍정 트리거와 근접 실패(near-miss) 경계를 갖춘 라우팅 description을 작성합니다.
- 자격, 선택, 활성화, 인자 바인딩, 실행을 트레이스와 테스트에서 분리합니다.
- 런타임 전용 호출 필드를, 이식 가능한 프론트매터인 것처럼 보이지 않게 흡수합니다.

## 문제 상황

`database-migration` 스킬을 설치했다고 합시다. 사용자는 이름으로 실행할 수 있지만, 모델도 description을 보고 있어서 누군가 일반적인 데이터베이스 질문을 던지면 이 스킬을 골라 버립니다. 스킬은 설명만 필요한 작업에 스키마 변경을 제안합니다.

사람이 수동으로 실행하지 못하게 하려고 `user-invocable: false`를 추가합니다. 다른 런타임에서는 이 필드가 무시됩니다. 스킬이 완전히 사라지길 바라며 `disable-model-invocation: true`를 추가합니다. 이 필드를 이해하는 런타임에서는 사용자가 여전히 명시적으로 호출할 수 있습니다.

필드 이름이 잘못된 게 아닙니다. 모델(사고방식)이 잘못된 겁니다. "사용자가 볼 수 있다", "모델이 선택할 수 있다", "애플리케이션이 미리 로드할 수 있다", "그 안의 도구가 실행될 수 있다"는 별개의 사실입니다. `invocable`이라는 불리언 하나로는 표현할 수 없습니다.

라우팅에는 두 번째 실패 모드도 있습니다. description이 모호하면 여러 스킬이 그럴듯해집니다. description에 키워드를 잔뜩 채우면 무관한 작업이 스킬을 발동시킵니다. 카탈로그는 확률적 인터페이스입니다. 담길 만큼 요약되고, 라우팅될 만큼 구체적이어야 합니다.

## 개념

### 다섯 개의 통로가 생명주기를 시작할 수 있다

| 행위자 | 호출 형태 | 전형적인 용도 | 주요 위험 |
|---|---|---|---|
| 사람 사용자 | UI나 프롬프트에서 스킬 이름을 지정 | 의도적인 워크플로 선택 | 호스트가 부여하지 않은 가용성이나 권한을 사용자가 기대함 |
| 모델 또는 자율 에이전트 | 작업 컨텍스트에서 카탈로그 항목 선택 | 자동 전문가 절차 | 거짓 양성 라우팅 |
| 애플리케이션 | 런타임 코드를 통해 스킬을 활성화하거나 미리 로드 | 고정된 제품 워크플로 | 특정 호스트에 숨은 결합 |
| 다른 스킬이나 서브에이전트 | 워크플로 의존성으로 특정 스킬 요청 | 조합 | 순환, 누락된 의존성, 컨텍스트 오염 |
| 평가 하네스 | 고정된 시나리오에서 특정 스킬 활성화 | 반복 가능한 측정 | 연구 대상인 프로덕션 정책을 실수로 우회한 채 스킬을 테스트함 |

이식 가능한 Agent Skills 규격은 패키지를 정의합니다. 만능 슬래시 명령 UI, 암시적 라우팅 플래그, 애플리케이션 API, 서브에이전트 생명주기를 표준화하지는 않습니다.

### 다섯 단계의 호출

```figure
skill-invocation-stages
```

이 단어들은 정확하게 쓰세요:

- **자격 있음(Eligible)**: 정책이 이 행위자의 스킬 요청을 허용한다는 뜻.
- **선택됨(Selected)**: 사용자가 이름을 불렀거나 라우터가 관련 있다고 판단했다는 뜻.
- **활성화됨(Activated)**: 지침이 작업 컨텍스트에 들어왔다는 뜻.
- **실행 중(Executing)**: 에이전트가 그 지침 아래에서 모델 또는 도구 작업을 시작했다는 뜻.
- **완료됨(Completed)**: 출력이 독립적인 성공 검사를 통과했다는 뜻.

`skill_used=true`만 기록하는 트레이스는 실패가 어느 경계에서 일어났는지 가려 버립니다.

### 사람·모델 호출은 2x2 매트릭스가 된다

| 사람이 호출 가능 | 모델이 호출 가능 | 모드 | 적합한 예 |
|:---:|:---:|---|---|
| 예 | 예 | 공유 | 코드 설명, 테스트 계획, 문서 리뷰 |
| 예 | 아니요 | 사람 전용 | 출시 준비, 청구 내보내기, 파괴적인 정리 계획 |
| 아니요 | 예 | 모델 전용 | 내부 스타일 가이드, 도메인 참조, 자동 지원 절차 |
| 아니요 | 아니요 | 비활성 또는 애플리케이션 전용 | 단계적 출시(rollout), 지원 중단된 패키지, 프로그래밍 방식 미리 로드 |

이 매트릭스는 정책 모델이지 표준 YAML이 아닙니다.

한 현재 호스트는 '사람 전용' 행에 `disable-model-invocation: true`를, '모델 전용' 행에 `user-invocable: false`를 씁니다. 기본값은 둘 다 허용입니다. 또 다른 호스트는 `agents/openai.yaml`에서 `allow_implicit_invocation: false`로 명시적 호출은 유지하면서 암시적 선택을 끕니다. 이것들은 런타임 어댑터입니다. 모르는 호스트는 무시할 수 있습니다.

헷갈리는 세부 사항이 중요합니다. `user-invocable: false`는 "모델이 이것을 쓸 수 없다"는 뜻이 아닙니다. 이 필드를 정의한 호스트에서 사용자 직접 호출을 제거할 뿐입니다. `disable-model-invocation: true`도 "스킬이 비활성화됐다"는 뜻이 아닙니다. 모델이 주도하는 선택을 제거하면서 사용자의 명시적 접근은 유지합니다.

### 명시적 호출은 정체성이 먼저다

명시적 호출은 정체성을 직접 공급합니다:

```text
/release-readiness v2.4.0
```

또는:

```text
release-readiness check v2.4.0 without publishing
```

현재 Codex 인터페이스는 선택을 위한 `/skills`와, 명시적 호출을 위한 요청 속 평범한 스킬 이름을 문서화하고 있습니다. Claude Code는 `/skill-name`과 호스트 전용 인자 확장을 문서화합니다. 정확한 문법, 메뉴 가시성, 따옴표 규칙, 변수 확장은 호스트의 몫입니다.

명시적 요청도 정책을 통과해야 합니다. 스킬 이름을 부른다고 해서 없는 권한, 작업 공간 제약, 승인 게이트, 런타임 격리를 건너뛰어서는 안 됩니다.

### 암시적 호출은 description이 먼저다

암시적 라우팅에서는 모델이 처음에 전체 본문이 아니라 카탈로그 메타데이터를 봅니다. 따라서 description이 곧 스킬의 라우팅 인터페이스입니다.

약한 예:

```yaml
description: Helps with releases.
```

너무 넓은 예:

```yaml
description: Use for release, version, package, build, deploy, publish, tag, changelog, GitHub, CI, or software tasks.
```

경계가 분명한 예:

```yaml
description: Inspect an already prepared release candidate and produce a readiness report. Use when the user asks whether a version, tag, package, or image is ready to publish; do not use for ordinary build failures or feature development.
```

경계가 분명한 버전에는 다음이 들어 있습니다:

1. **능력**: 준비된 후보를 검사한다.
2. **출력**: 준비 완료 보고서.
3. **긍정 경계**: 릴리스 산출물이 준비됐는지 물을 때.
4. **부정 경계**: 평범한 빌드 실패와 기능 개발은 범위 밖.

부정 경계는 가까운 스킬 둘이 어휘를 공유할 때 유용합니다. 하지만 근접 실패 평가(eval)를 대신하지는 못합니다.

### 라우팅은 '기권' 옵션 있는 분류다

스킬 `s`와 요청 `x`에 대해 라우터 점수를 상상해 봅시다:

```text
score(s, x) = capability_match + trigger_match + context_match - exclusion_match - ambiguity_penalty
```

실제 점수 계산은 산술이 아니라 LLM 판단일 수 있습니다. 그래도 엔지니어링 원칙은 유효합니다. 선택은 임계값과 경쟁 스킬을 이겨야 하고, 증거가 약하면 기권해야 합니다.

```figure
skill-routing-abstention
```

영향이 큰 스킬은 description이 아무리 좋아도 암시적 라우팅이 부적절할 수 있습니다. 거짓 양성의 비용이 자동 선택의 편의를 넘는다면 사람 전용 정책을 쓰세요.

### 자격 확인이 순위 매기기보다 앞서야 한다

발견된 모든 스킬에 점수를 매기고 가장 강한 매치를 골라, 그 스킬의 정책을 나중에 확인하는 식으로 하지 마세요. 차단된 최상위 매치 하나가, 자격이 있는 더 낮은 점수의 후보까지 고려되지 못하게 막아 버립니다.

암시적 라우팅은 이 순서를 쓰세요:

1. 요청 행위자와 활성 호스트 어댑터로 발견된 스킬을 걸러냅니다.
2. 자격이 있는 후보에만 점수를 매깁니다.
3. 임계값과 모호성 규칙을 통과한 가장 강한 자격 매치를 선택합니다.
4. 자격이 있는 후보가 없거나 자격 점수가 충분히 강하지 않으면 기권합니다.

`incident-triage`가 `0.80`점인데 호스트 확장이 모델 호출을 막고 있고, `incident-review`가 `0.55`점에 모델 호출을 허용한다고 합시다. 라우터는 `incident-review`를 최고의 자격 후보로 평가해야 합니다. `incident-triage`를 골랐다가 거부하고 끝내면 안 됩니다.

이 순서 덕분에 정책 변경이 관련성 점수의 의미를 바꾸는 일도 막을 수 있습니다. 자격이 선택 집합을 정의하고, 관련성이 그 집합의 순위를 매깁니다.

### 라우팅 평가에는 근접 실패가 필요하다

긍정 사례는 재현율(recall)을 증명합니다:

```json
{"prompt":"Is version 2.4.0 ready to publish?","expected":"release-readiness"}
```

명확한 부정 사례는 기본 정밀도를 증명합니다:

```json
{"prompt":"Explain rotary position embeddings.","expected":null}
```

근접 실패는 경계 품질을 드러냅니다:

```json
{"prompt":"Why did today's package build fail?","expected":"build-diagnostics"}
```

근접 실패는 릴리스 스킬과 `package`, `build` 어휘를 공유하지만 소속은 다른 곳입니다. 자명한 긍정 사례와 무관한 부정 사례로만 이뤄진 라우팅 평가 세트는 품질을 과장합니다.

### 인자는 세 가지 표현을 거친다

호출 인자는 여러 경계를 넘습니다:

```figure
skill-argument-boundaries
```

각 경계에서 텍스트를 코드처럼 다루지 않으면서 의도를 보존하세요.

- 호스트 파서가 명령 문법과 따옴표 규칙을 결정합니다.
- 스킬은 호스트 규칙에 따라 바인딩된 텍스트나 변수를 받습니다.
- 지침이 필수 값과 기본값을 검증합니다.
- 도구 호출이 값을 타입이 정의된 스키마로 바꾸고 다시 검증합니다.

날 인자를 셸 명령에 그대로 끼워 넣지 마세요. 인자 벡터로 호출되는 스크립트나 타입이 정의된 MCP 도구를 선호하세요.

### 애플리케이션 호출은 명시적 오케스트레이션이다

제품은 워크플로가 이미 작업 유형을 알고 있다면 스킬을 활성화할 수 있습니다. 예를 들어 풀 리퀘스트 리뷰 서비스는 사용자가 Review 버튼을 누르면 `pull-request-risk-review`를 미리 로드할 수 있습니다.

이렇게 하면 라우팅 불확실성이 사라지지만 런타임 API 의존성이 생깁니다. 그 어댑터는 이식 가능한 본문 밖에 두세요:

```figure
skill-host-adapter
```

스킬은 다른 준수 클라이언트가 열어도 이해할 수 있게 남아야 합니다.

### 스킬-스킬 호출은 도구 같은 간선이다

`release-readiness`가 의존성 파일이 바뀌었을 때 `security-change-review`를 요청한다고 합시다.

호출자는 다음을 제공해야 합니다:

- 대상 스킬 정체성
- 한정된 작업과 산출물 경로
- 기대하는 응답 계약
- 호출 이유
- 사용할 수 없을 때의 대체 방안
- 최대 깊이 또는 순환 규칙

```json
{
  "target_skill": "security-change-review",
  "task": "Review dependency changes in the candidate diff",
  "inputs": ["artifacts/release.diff"],
  "expected": "risk-report.json",
  "max_depth": 2
}
```

두 번째 스킬이 첫 번째 스킬에 무작정 붙여 넣어지는 것이 아닙니다. 활성화 방법, 컨텍스트 공유 여부, 포크에서 실행 여부, 도구 결과로 반환 여부는 호스트가 결정합니다.

### 컨텍스트 생명주기는 호스트마다 다르다

활성화 후 스킬 본문은 대화에 남을 수도, 컴팩션 중 요약될 수도, 위임된 컨텍스트에서 실행될 수도 있습니다. 도구 허용은 한 턴만 유지되는데 지침은 더 오래 남을 수 있습니다. 서브에이전트는 부모의 전체 이력 없이 스킬만 받을 수도 있습니다.

보이지 않는 수명 가정에 의존하는 스킬을 쓰지 마세요. 오래 남는 출력은 파일이나 타입이 정의된 상태에 넣고, 재진입이 안전하게 만들고, 중단 후 무엇을 다시 로드해야 하는지 밝히세요.

```markdown
On resume, read `artifacts/release-readiness.json` if it exists.
Revalidate the candidate commit before continuing.
Do not repeat an external write whose idempotency key is already recorded.
```

## 만들어 보기

`code/main.py`는 정책과 라우팅을 별개의 어댑터로 구현합니다.

모델에는 다음이 있습니다:

- 사람, 모델, 자율 에이전트, 애플리케이션, 스킬, 하네스 호출자를 위한 `Actor`
- 라우팅 정체성을 위한 `SkillMetadata`
- 사람/모델 매트릭스를 위한 `InvocationPolicy`
- 추적 가능한 입력과 결과를 위한 `InvocationRequest`와 `InvocationDecision`
- 호스트 확장 없는 이식 가능 동작을 위한 `CorePolicyAdapter`
- 인식된 런타임 필드를 위한 `ExtensionPolicyAdapter`
- 2x2 뷰를 위한 `build_invocation_matrix(policy)`
- 관련성 순위, 선택, 거부보다 자격 필터링이 먼저 오게 하는 `route_request(skills, request, adapter)`

실행합니다:

```bash
cd phases/13-tools-and-protocols/25-skill-invocation-and-routing
python3 code/main.py
python3 -m unittest discover -s code/tests -v
```

데모는 매트릭스 하나와, 명시적 사람·암시적 모델·자율 에이전트·애플리케이션·스킬 조합·하네스 통로에 대한 결정을 출력합니다. 확장 어댑터 결과에서는 어휘상 최상위 매치가 차단되어, 자격이 있는 대안이 순위가 매겨지기 전에 제거되는 모습을 볼 수 있습니다. 정확한 이름 허용 목록도 포함됩니다. 모델 API는 필요 없습니다. 이 결정론적 라우터는 정책 경계를 들여다볼 수 있게 하기 위한 것이지, 어휘 매칭이 프로덕션 모델 라우팅을 재현한다는 주장이 아닙니다.

### 코어 어댑터와 확장 어댑터가 분리된 이유

하나의 파서가 관찰된 모든 프론트매터 필드에 의미를 부여하면, 런타임 관례가 조용히 가짜 표준으로 승격됩니다. 어댑터를 분리하면 호출자가 어떤 호스트 의미론이 활성인지 이름 붙이도록 강제됩니다.

`CorePolicyAdapter`는 애플리케이션이 공급한 정책만 씁니다. `ExtensionPolicyAdapter`는 명시적인 호스트 필드 집합을 인식하고, 어떤 필드가 결정을 바꿨는지 기록합니다.

## 사용해 보기

스킬을 출시하기 전에 호출 계약을 작성하세요:

```yaml
actors:
  human: allow
  model: deny
  application: allow
  skill: deny
explicit_name: release-readiness
arguments:
  candidate: required
  publish: fixed_false
ambiguity: ask_user
missing_dependency: stop
context:
  durable_state: artifacts/release-readiness.json
  max_composition_depth: 2
```

이 계약은 어댑터와 테스트를 위한 설계 문서입니다. 표준이 명시적으로 채택하지 않는 한 이식 가능한 `SKILL.md` 프론트매터가 아닙니다.

## 출시하기

이 레슨은 `skill-invocation-router` 번들을 만듭니다. 호출 모델 참조, 호스트 정책 예시, 그리고 사람·모델·자율 에이전트·애플리케이션·스킬 조합·하네스 요청 하나를 평가해 통로, 어댑터, 점수, 이유가 담긴 JSON 결정을 돌려주는 실행되지 않는 CLI가 포함됩니다.

단일 요청 CLI는 정책 탐침(probe)이지 전체 트리거 평가가 아닙니다. 혼동 개수, 정밀도, 재현율, 반복 실행 안정성을 계산할 때는 레슨 27의 레이블된 긍정·근접 실패 설계를 사용하세요.

## 연습 문제

1. 사람/모델 매트릭스의 네 행을 모두 만들고 각각 정당한 사용 사례를 하나 쓰세요.
2. `CorePolicyAdapter`에 애플리케이션 전용 활성화를 추가하세요. 사람과 모델 호출자가 여전히 거부됨을 증명하세요.
3. 배포 스킬을 위한 근접 실패 열 개를 작성하세요. 각 프롬프트는 스킬과 어휘를 공유하면서 다른 워크플로에 속해야 합니다.
4. 상위 두 라우팅 점수 사이에 모호성 마진을 추가하세요. 마진이 너무 작으면 `ask`를 돌려주세요.
5. 스킬-스킬 요청에 최대 조합 깊이를 추가하고 두 스킬 순환을 탐지하세요.
6. 같은 레이블 세트를 코어 어댑터와 확장 어댑터로 실행하세요. 바뀐 결정마다 이유를 설명하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|---|---|---|
| 명시적 호출 | "슬래시 명령" | 행위자가 정책의 구속을 받으며 스킬 정체성을 직접 공급하는 것 |
| 암시적 호출 | "모델이 알아서 고른다" | 라우터가 작업 컨텍스트를 근거로 자격 있는 카탈로그 메타데이터에서 선택하는 것 |
| User-invocable | "사람이 쓸 수 있다" | 호스트 전용 메뉴 또는 직접 호출 속성이지 핵심 필드가 아님 |
| Model-invocable | "에이전트가 쓸 수 있다" | 호스트 정책 아래에서 암시적 모델 선택의 자격 |
| 호출 어댑터 | "프론트매터 파서" | 호스트의 필드와 API를 선언된 정책 모델로 옮기는 코드 |
| 근접 실패 | "어려운 부정 사례(hard negative)" | 스킬이 의도한 입력을 닮았지만 발동하면 안 되는 요청 |
| 기권 | "선택된 스킬 없음" | 증거가 없거나 모호할 때의 의도적인 라우팅 결과 |

## 더 읽을거리

- [스킬 description 최적화](https://agentskills.io/skill-creation/optimizing-descriptions): 긍정 트리거, 구체성, 평가.
- [스킬 평가하기](https://agentskills.io/skill-creation/evaluating-skills): 트리거·출력 평가 설계.
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills): 현재 Codex의 명시적·암시적 호출 통제.
- [Claude Code skills](https://code.claude.com/docs/en/skills): 한 호스트의 `user-invocable`, `disable-model-invocation`, 인자, 위임 컨텍스트.
