> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 09 — 코드 마이그레이션 에이전트 (저장소 단위 언어 / 런타임 업그레이드)

> Amazon의 MigrationBench(Java 8 → 17)와 Google의 App Engine Py2→Py3 마이그레이터가 2026년의 기준선을 세웠습니다. Moderne의 OpenRewrite는 규모 있고 결정론적인 AST 재작성을 해줍니다. Grit은 같은 문제를 코드모드(codemod) 스타일 DSL로 공략합니다. 프로덕션 패턴은 둘을 결합합니다: 안전한 재작성을 위한 결정론적 기반(substrate)에, 애매한 케이스를 처리하는 에이전트 레이어, 브랜치별 빌드를 위한 샌드박스, 그리고 PR이 열리기 전에 녹색을 만드는 테스트 하니스가 그것입니다. 이 캡스톤의 목표는 실제 저장소 50개를 마이그레이션하고, 통과율과 실패 분류표(taxonomy)를 공개하는 것입니다.

**유형:** 캡스톤
**언어:** Python (에이전트), Java / Python (대상 코드), TypeScript (대시보드)
**선수 지식:** 페이즈 5 (NLP), 페이즈 7 (트랜스포머), 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구), 페이즈 14 (에이전트), 페이즈 15 (자율성), 페이즈 17 (인프라)
**활용 페이즈:** P5 · P7 · P11 · P13 · P14 · P15 · P17
**소요 시간:** 30시간

## 문제

대규모 코드 마이그레이션은 2026년 코딩 에이전트 중 가장 깔끔한 프로덕션 활용 사례 중 하나입니다. 정답이 명확하고(마이그레이션 후 테스트 스위트가 통과하는가?), 보상이 실제며(Java 8 플릿(fleet) 마이그레이션은 인원 단위 규모의 프로젝트입니다), 벤치마크도 공개되어 있습니다(MigrationBench 50저장소 서브셋). Moderne의 OpenRewrite가 결정론적인 부분을 담당합니다. 에이전트 레이어는 OpenRewrite 레시피가 못 하는 나머지 전부 — 애매한 재작성, 빌드 시스템 드리프트, 단골(long-tail) 문법, 전이(transitive) 의존성 파손 — 를 처리합니다.

여러분은 Java 8 저장소(또는 Python 2 저장소)를 받아서 CI가 녹색인 마이그레이션 브랜치를 만들어 내는 에이전트를 만들 것입니다. 통과율, 테스트 커버리지 보존율, 저장소당 비용을 측정하고 실패 분류표를 만듭니다. 결정론적 도구만 쓰는 베이스라인과 나란히 비교하면 에이전트의 가치가 실제로 어디에 있는지 알 수 있습니다.

## 개념

파이프라인은 두 레이어로 이루어져 있습니다. **결정론적 기반(substrate)**(Java는 OpenRewrite, Python은 libcst)은 기계적인 재작성 대부분을 안전하게 처리합니다: 임포트, 메서드 시그니처, null 안전성 수정, try-with-resources, 지원 종료된 API 교체가 그것입니다. 빠르고 감사 가능한 diff를 만들어 냅니다. **에이전트 레이어**(Claude Opus 4.7과 GPT-5.4-Codex 위에서 OpenAI Agents SDK 또는 LangGraph)는 레시피가 못 하는 케이스를 담당합니다: 빌드 파일 업그레이드(Maven/Gradle/pyproject), 전이 의존성 충돌, 테스트 플레이크(flake), 커스텀 어노테이션이 그것입니다.

각 저장소는 대상 런타임이 미리 설치된 Daytona 샌드박스를 받습니다. 에이전트는 반복합니다: 빌드 실행 → 실패 분류 → 수정 적용 → 재실행. 하드 리밋은 저장소당 30분, 저장소당 8달러, 에이전트 턴 20회입니다. 모든 테스트가 통과하고 커버리지 변화가 음수가 아니면 브랜치가 PR을 엽니다. 그렇지 않으면 증거와 함께 실패 클래스로 분류됩니다.

실패 분류표(taxonomy)가 산출물입니다. 50개 저장소에서 무엇이 깨졌을까요? 전이 의존성? 커스텀 어노테이션? 빌드 도구 버전? 마이그레이션과 무관한 테스트 플레이크? 각 클래스마다 개수와 대표 diff를 붙입니다. 이후에 레시피를 만드는 사람들은 상위 세 개를 노리고 만들면 됩니다.

## 아키텍처

```
target repo
      |
      v
OpenRewrite / libcst deterministic recipes
   (safe, fast, auditable, ~70-80% of fixes)
      |
      v
Daytona sandbox per branch
      |
      v
agent loop (Claude Opus 4.7 / GPT-5.4-Codex):
   - run build -> capture failures
   - classify failures (build, test, lint)
   - apply fix (patch or retry recipe)
   - rerun
   - budget: 30 min, $8, 20 turns
      |
      v
test + coverage delta gate
      |
      v (passed)
open PR
      |
      v (failed)
file under failure class + attach repro
```

## 스택

- 결정론적 기반: OpenRewrite (Java) 또는 libcst (Python)
- 에이전트: Claude Opus 4.7 + GPT-5.4-Codex 위에서 OpenAI Agents SDK 또는 LangGraph
- 샌드박스: 브랜치별 Daytona devcontainer, 대상 런타임(Java 17 / Python 3.12) 미리 설치
- 빌드 시스템: Maven, Gradle, uv (Python)
- 벤치마크: Amazon MigrationBench 50저장소 서브셋 (Java 8 → 17), Google App Engine Py2→Py3 저장소
- 테스트 하니스: 병렬 러너, 커버리지는 Java는 Jacoco, Python은 coverage.py
- 관측 가능성(옵저버빌리티): 저장소마다 모든 diff 청크가 담긴 Langfuse + 트레이스 번들
- 대시보드: 클래스별 개수와 대표 diff를 보여주는 실패 분류표 대시보드

```figure
ce-migration-funnel
```

## 직접 만들기

1. **레시피 통과.** 먼저 OpenRewrite(Java) 또는 libcst(Python) 레시피를 돌립니다. 기계적인 마이그레이션 70~80%를 여기서 잡습니다. "recipe" 커밋으로 커밋합니다.

2. **빌드 시험.** Daytona 샌드박스: 대상 런타임을 설치하고 빌드를 돌립니다. 녹색이면 테스트로 건너뜁니다. 빨간색이면 에이전트에게 넘깁니다.

3. **에이전트 루프.** 도구를 갖춘 LangGraph: `run_build`, `read_file`, `edit_file`, `run_test`, `git_diff`. 에이전트가 실패를 분류하고(의존성, 문법, 테스트, 빌드 도구) 표적화된 수정을 적용합니다. 재실행합니다.

4. **예산 상한.** 저장소당 벽시계 시간 30분, 비용 8달러, 에이전트 턴 20회. 하나라도 넘기면 중단하고 현재 diff와 함께 "budget_exhausted"로 분류합니다.

5. **테스트 + 커버리지 게이트.** 빌드가 녹색이 되면 테스트 스위트를 돌립니다. 베이스 저장소와 커버리지를 비교합니다. 커버리지가 2% 이상 떨어지면 "coverage_regression"으로 분류합니다.

6. **PR 열기.** 성공하면 브랜치를 푸시하고, diff와 함께 어떤 레시피가 적용됐는지, 어떤 커밋이 에이전트가 작성했는지 요약을 담아 PR을 엽니다.

7. **실패 분류표.** 실패한 저장소마다 클래스 태그를 붙입니다: `dep_upgrade_required`, `build_tool_drift`, `custom_annotation`, `test_flake`, `syntax_edge_case`, `budget_exhausted`. 대시보드를 만듭니다.

8. **50저장소 실행.** MigrationBench 서브셋 전체에서 실행합니다. 클래스별 통과율, 저장소당 비용, 커버리지 보존율, 그리고 결정론적 도구만 쓴 베이스라인과의 비교를 보고합니다.

## 사용해 보기

```
$ migrate legacy-java-service --target java17
[recipe]   27 rewrites applied (JUnit 4->5, HashMap initializer, try-with-resources)
[build]    FAIL: cannot find symbol sun.misc.BASE64Encoder
[agent]    turn 1 classify: removed_jdk_api
[agent]    turn 2 apply: sun.misc.BASE64Encoder -> java.util.Base64
[build]    OK
[tests]    412/412 passing; coverage 84.1% -> 84.3%
[pr]       opened #1841  cost=$3.20  turns=4
```

## 출시하기

`outputs/skill-migration-agent.md`가 산출물입니다. 저장소가 주어지면 결정론적 레시피를 실행한 뒤 에이전트 루프를 돌려 녹색 마이그레이션 브랜치를 만들어 내거나, 저장소를 분류표 클래스로 기록합니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | MigrationBench 통과율 | 50저장소 서브셋 pass@1 |
| 20 | 테스트 커버리지 보존 | 베이스 대비 평균 커버리지 변화량 |
| 20 | 마이그레이션 저장소당 비용 | 통과한 실행 기준 저장소당 달러($/repo) |
| 20 | 에이전트 / 결정론적 도구 통합 | OpenRewrite가 처리한 수정 대비 에이전트가 작성한 수정의 비율 |
| 15 | 실패 분석 보고서 | 대표 사례를 갖춘 분류표의 완성도 |
| **100** | | |

## 연습 문제

1. 에이전트 없이 OpenRewrite만으로 마이그레이션 파이프라인을 돌려 봅니다. 전체 파이프라인과 통과율을 비교합니다. 에이전트만이 만들어 내는 차이가 어디에 있는지 찾아냅니다.

2. "린트 클린" 검사를 구현합니다: 마이그레이션 후 스타일 린터(Java는 spotless, Python은 ruff)를 돌립니다. 새 린트 오류가 나오면 PR을 실패 처리합니다. 커버리지는 지켰는데 스타일이 퇴보한 비율을 측정합니다.

3. "최소 diff" 옵티마이저를 추가합니다: 에이전트 브랜치가 테스트를 통과하면 2차 패스로 불필요한 변경을 잘라냅니다. diff 크기가 얼마나 줄었는지 보고합니다.

4. 세 번째 마이그레이션으로 확장합니다: Node 18 → Node 22. 샌드박스 감싸기는 재사용하고, 레시피 레이어는 커스텀 코드모드(codemod)로 바꿉니다.

5. 첫 녹색 빌드까지의 시간(TTFGB, time-to-first-green-build)을 UX 지표로 측정합니다. 목표: p50 10분 미만.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| 결정론적 기반(substrate) | "레시피 엔진" | OpenRewrite / libcst: 안전성 보장이 붙은 선언형 AST 재작성 |
| 코드모드(codemod) | "코드 수정 프로그램" | 소스 코드를 기계적으로 바꾸는 재작성 규칙 |
| 빌드 드리프트 | "도구 버전 어긋남" | 메이저 버전 사이에서 벌어지는 미묘한 Maven / Gradle / uv 동작 변화 |
| 실패 클래스 | "분류 통(taxonomy bucket)" | 저장소가 마이그레이션에 실패한 레이블된 이유: 의존성, 문법, 테스트, 빌드 도구, 예산 |
| 커버리지 델타 | "커버리지 보존" | 베이스부터 마이그레이션 브랜치까지의 테스트 커버리지 % 변화 |
| 에이전트 턴 | "도구 호출 라운드" | 에이전트 루프에서 한 번의 계획 -> 실행 -> 관찰 주기 |
| 예산 소진 | "천장에 도달" | 저장소가 통과하지 못한 채 30분 / 8달러 / 20턴 한도를 모두 씀 |

## 더 읽을거리

- [Amazon MigrationBench](https://aws.amazon.com/blogs/devops/amazon-introduces-two-benchmark-datasets-for-evaluating-ai-agents-ability-on-code-migration/) — 2026년의 표준 벤치마크
- [Moderne.io OpenRewrite 플랫폼](https://www.moderne.io) — 결정론적 기반의 참고 사례
- [OpenRewrite 문서](https://docs.openrewrite.org) — 레시피 작성법
- [Grit.io](https://www.grit.io) — 대안 코드모드 DSL
- [OpenAI 샌드박스 마이그레이션 쿡북](https://developers.openai.com/cookbook/examples/agents_sdk/sandboxed-code-migration/sandboxed_code_migration_agent) — Agents SDK 참고 자료
- [Google App Engine Py2 → Py3 마이그레이터](https://cloud.google.com/appengine) — 대안 마이그레이션 벤치마크
- [libcst](https://github.com/Instagram/LibCST) — Python 결정론적 기반
- [Daytona 샌드박스](https://daytona.io) — 브랜치별 샌드박스의 참고 사례
