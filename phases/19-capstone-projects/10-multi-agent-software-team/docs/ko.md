> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 10 — 멀티 에이전트 소프트웨어 엔지니어링 팀

> 2026년 멀티 에이전트 엔지니어링 팀의 모습은 하나로 수렴했습니다: 아키텍트가 계획하고, N명의 코더가 병렬 워크트리에서 일하고, 리뷰어가 관문을 지키고, 테스터가 검증합니다. SWE-AF의 팩토리 아키텍처, MetaGPT의 역할 기반 프롬프팅, AutoGen 0.4의 타입화된 액터 그래프, Cognition의 Devin, Factory의 Droids가 모두 독자적으로 이 모습에 도달했습니다. 병렬 워크트리는 벽시계 시간을 처리량으로 바꿔 줍니다. 공유 상태와 핸드오프(handoff) 프로토콜이 실패가 몰리는 지점이 됩니다. 이 캡스톤은 팀을 직접 만들고, SWE-bench Pro로 평가하고, 어떤 핸드오프가 어떤 빈도로 깨지는지 보고하는 것입니다.

**유형:** 캡스톤
**언어:** Python / TypeScript (에이전트), Shell (워크트리 스크립트)
**선수 지식:** 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구), 페이즈 14 (에이전트), 페이즈 15 (자율성), 페이즈 16 (멀티 에이전트), 페이즈 17 (인프라)
**활용 페이즈:** P11 · P13 · P14 · P15 · P16 · P17
**소요 시간:** 40시간

## 문제

단일 에이전트 코딩 하니스는 큰 작업에서 천장에 부딪힙니다. 개별 에이전트가 약해서가 아닙니다. 200k 토큰 컨텍스트 윈도우로는 아키텍처 계획 + 병렬 코드베이스 조각 4개 + 리뷰어 코멘트 + 테스트 출력을 다 담을 수 없기 때문입니다. 멀티 에이전트 팩토리는 문제를 쪼갭니다: 아키텍트가 계획을 담당하고, 코더들이 병렬 워크트리에서 구현을 맡고, 리뷰어가 관문을 지키고, 테스터가 검증합니다. SWE-AF의 "팩토리" 아키텍처, MetaGPT의 역할, AutoGen의 타입화된 액터 그래프 — 세 관점 모두 같은 모습을 묘사합니다.

실패 지점은 핸드오프입니다. 아키텍트가 코더가 구현할 수 없는 것을 계획합니다. 코더들이 서로 충돌하는 diff를 만들어 냅니다. 리뷰어가 환각으로 가득한 수정을 승인합니다. 테스터가 아직 코드를 쓰고 있는 코더와 경쟁합니다. 여러분은 이런 팀을 하나 만들어, 50개 SWE-bench Pro 이슈에서 돌리고, 모든 핸드오프를 추적하고, 사후 분석(post-mortem)을 공개할 것입니다.

## 개념

역할은 타입화된 에이전트입니다. **아키텍트**(Claude Opus 4.7)는 이슈를 읽고, 계획을 쓰고, 명시적인 인터페이스를 갖춘 하위 작업으로 쪼갭니다. **코더**(Claude Sonnet 4.7, 병렬 N개 인스턴스, 각각 `git worktree` + Daytona 샌드박스)는 하위 작업을 독립적으로 구현합니다. **리뷰어**(GPT-5.4)는 병합된 diff를 읽고 승인하거나 구체적인 수정을 요청합니다. **테스터**(Gemini 2.5 Pro)는 격리된 환경에서 테스트 스위트를 돌리고 산출물과 함께 통과/실패를 보고합니다.

의사소통은 공유 작업 보드(파일 기반 또는 Redis)를 통해 이루어집니다. 각 역할은 자신이 처리할 수 있도록 허용된 작업만 소비합니다. 핸드오프는 A2A 프로토콜로 타입화된 메시지입니다. 조율 이슈는 세 가지입니다: 병합 충돌 해소(코디네이터 역할 또는 자동 3-way 병합), 공유 상태 동기화(코더가 시작하면 계획은 고정; 재계획은 별도 이벤트), 리뷰어 관문(리뷰어는 자신이 만든 변경이나 자신이 제안한 변경을 승인할 수 없음).

토큰 증폭이 숨은 비용입니다. 역할 경계를 넘을 때마다 요약 프롬프트와 핸드오프 컨텍스트가 추가됩니다. 40턴짜리 단일 에이전트 실행이 네 역할에 걸쳐 총 160턴이 됩니다. 루브릭은 토큰 효율을 단일 에이전트 베이스라인 대비 특별히 반영합니다. 질문이 "멀티 에이전트가 되긴 하는가"가 아니라 "달러당 이기는가"이기 때문입니다.

## 아키텍처

```
GitHub issue URL
      |
      v
Architect (Opus 4.7)
   reads issue, produces plan with subtasks + interfaces
      |
      v
Task board (file / Redis)
      |
   +-- subtask 1 ---+-- subtask 2 ---+-- subtask 3 ---+-- subtask 4 ---+
   v                v                v                v                v
Coder A          Coder B          Coder C          Coder D          (4 parallel)
 (Sonnet)         (Sonnet)         (Sonnet)         (Sonnet)
 worktree A       worktree B       worktree C       worktree D
 Daytona          Daytona          Daytona          Daytona
      |                |                |                |
      +--------+-------+-------+--------+
               v
           merge coordinator  (three-way merge + conflict resolution)
               |
               v
           Reviewer (GPT-5.4)
               |
               v
           Tester  (Gemini 2.5 Pro)  -> passes? -> open PR
                                     -> fails?  -> route back to coder
```

## 스택

- 오케스트레이션: 공유 상태 + 에이전트별 서브그래프를 갖춘 LangGraph
- 메시징: 타입화된 에이전트 간 메시지를 위한 A2A 프로토콜 (Google 2025)
- 모델: Opus 4.7 (아키텍트), Sonnet 4.7 (코더), GPT-5.4 (리뷰어), Gemini 2.5 Pro (테스터)
- 워크트리 격리: 코더마다 `git worktree add` + Daytona 샌드박스
- 병합 코디네이터: 커스텀 3-way 병합 + LLM 중재 충돌 해소
- 평가: SWE-bench Pro (50 이슈), SWE-AF 시나리오, 단위 테스트용 HumanEval++
- 관측 가능성(옵저버빌리티): 역할 태그가 붙은 스팬과 에이전트별 토큰 회계를 갖춘 Langfuse
- 배포: K8s에서 역할마다 별도 Deployment + 백로그 기준 HPA

```figure
ce-team-handoff
```

## 직접 만들기

1. **작업 보드.** 타입화된 메시지를 담은 파일 기반 JSONL: `plan_request`, `subtask`, `diff_ready`, `review_needed`, `test_needed`, `approved`, `rejected`, `replan_needed`. 에이전트는 태그를 구독합니다.

2. **아키텍트.** GitHub 이슈를 읽고, 하위 작업 인터페이스(건드리는 파일, 공개 함수, 테스트 영향)를 명시하도록 요구하는 계획 템플릿과 함께 Opus 4.7을 실행합니다. 하위 작업 DAG를 담아 `plan_request` 하나를 내보냅니다.

3. **코더.** 병렬 워커 N개가 각각 보드에서 하위 작업 하나를 가져갑니다. 각자 새로운 `git worktree add` 브랜치와 Daytona 샌드박스를 만듭니다. 하위 작업을 구현하고 패치 + 테스트 변화를 담아 `diff_ready`를 내보냅니다.

4. **병합 코디네이터.** 모든 코더가 끝나면 N개 브랜치를 스테이징 브랜치로 3-way 병합합니다. 파일 수준 겹침이 있을 때만 LLM 중재 충돌 해소를 씁니다.

5. **리뷰어.** GPT-5.4가 병합된 diff를 읽습니다. 자신이 작성한 diff는 승인할 수 없습니다. `approved`(변경 없음) 또는 구체적인 수정 요청을 담아 관련 코더에게 돌려 보내는 `review_feedback`을 내보냅니다.

6. **테스터.** Gemini 2.5 Pro가 깨끗한 샌드박스에서 테스트 스위트를 돌립니다. 산출물을 캡처하고 스택트레이스와 함께 `test_passed` 또는 `test_failed`를 내보냅니다. 실패한 테스트는 해당 하위 작업을 맡은 코더에게 되돌아갑니다.

7. **핸드오프 회계.** 역할 경계를 넘는 모든 메시지는 페이로드 크기와 사용 모델을 담아 Langfuse에 스팬으로 남습니다. 하위 작업별 토큰 증폭률(coder_tokens + reviewer_tokens + tester_tokens + architect_share / coder_tokens)을 계산합니다.

8. **평가.** 50개 SWE-bench Pro 이슈에서 실행합니다. 단일 에이전트 베이스라인(하나의 워크트리에서 도는 하나의 Sonnet 4.7)과 pass@1, 해결 이슈당 비용을 비교합니다.

9. **사후 분석.** 실패한 이슈마다 깨진 핸드오프를 찾아냅니다(계획이 너무 모호함, 병합 충돌, 리뷰어 잘못된 승인, 테스터 플레이크). 핸드오프 실패 히스토그램을 만듭니다.

## 사용해 보기

```
$ team run --issue https://github.com/acme/widget/issues/842
[architect] plan: 4 subtasks (parser, cache, api, migration)
[board]     dispatched to 4 coders in parallel worktrees
[coder-A]   subtask parser  -> 42 lines, tests pass locally
[coder-B]   subtask cache   -> 88 lines, tests pass locally
[coder-C]   subtask api     -> 31 lines, tests pass locally
[coder-D]   subtask migration -> 19 lines, tests pass locally
[merge]     3-way merge: 0 conflicts
[reviewer]  comments on cache (thread pool sizing); routed to coder-B
[coder-B]   revision: 92 lines; submits
[reviewer]  approved
[tester]    all 412 tests pass
[pr]        opened #3382   4 coders, 1 revision, $4.90, 18m
```

## 출시하기

`outputs/skill-multi-agent-team.md`가 산출물입니다. 이슈 URL과 병렬 수준이 주어지면, 역할별 토큰 회계를 갖춘 병합 준비가 된 PR을 팀이 만들어 냅니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 | 짝을 맞춘 50이슈 서브셋 pass@1 |
| 20 | 병렬 가속 | 단일 에이전트 베이스라인 대비 벽시계 시간 |
| 20 | 리뷰 품질 | 주입된 버그 프로브에서의 잘못된 승인 비율 |
| 20 | 토큰 효율 | 단일 에이전트 대비 해결 이슈당 총 토큰 |
| 15 | 조율 엔지니어링 | 병합 충돌 해소, 핸드오프 실패 히스토그램 |
| **100** | | |

## 연습 문제

1. 실행 도중 diff에 눈에 띄는 버그를 주입합니다(본문 앞에 `return None` 한 줄 추가). 리뷰어의 잘못된 승인 비율을 측정합니다. 잘못된 승인이 5% 미만이 될 때까지 리뷰어 프롬프트를 다듬습니다.

2. 코더를 둘로 줄입니다(아키텍트 + 코더 + 리뷰어 + 테스터, 코더는 하위 작업 두 개를 순차적으로 처리). 벽시계 시간과 통과율을 비교합니다.

3. 병합 코디네이터를 단일 작성자(single-writer) 제약(하위 작업들이 서로 겹치지 않는 파일 집합만 건드림)으로 바꿉니다. 아키텍트에게 돌아가는 계획 부담을 측정합니다.

4. 리뷰어를 GPT-5.4에서 Claude Opus 4.7로 바꿔 봅니다. 잘못된 승인 비율과 토큰 비용 변화를 측정합니다.

5. 다섯 번째 역할을 추가합니다: 문서화 담당(Haiku 4.5). 리뷰 후 변경 로그 항목을 만듭니다. 문서 품질이 추가 토큰 비용을 정당화하는지 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| 병렬 워크트리 | "격리된 브랜치" | 코더마다 새로운 작업 트리를 만들어 주는 `git worktree add` |
| 작업 보드 | "공유 메시지 버스" | 에이전트가 구독하는 타입화된 메시지의 파일 또는 Redis 저장소 |
| 핸드오프 | "역할 경계" | 한 역할의 컨텍스트에서 다른 역할의 컨텍스트로 넘어가는 모든 메시지 |
| 토큰 증폭 | "멀티 에이전트 오버헤드" | 같은 작업 기준, 역할 전체의 총 토큰 / 단일 에이전트 토큰 |
| A2A 프로토콜 | "에이전트 대 에이전트" | 타입화된 에이전트 간 메시지를 위한 Google의 2025 스펙 |
| 병합 코디네이터 | "통합자(integrator)" | 3-way 병합을 실행하고 충돌을 중재하는 구성 요소 |
| 잘못된 승인 | "리뷰어 환각" | 리뷰어가 알려진 버그가 있는 diff를 승인하는 것 |

## 더 읽을거리

- [SWE-AF 팩토리 아키텍처](https://github.com/Agent-Field/SWE-AF) — 2026년 멀티 에이전트 팩토리의 참고 사례
- [MetaGPT](https://github.com/FoundationAgents/MetaGPT) — 역할 기반 멀티 에이전트 프레임워크
- [AutoGen v0.4](https://github.com/microsoft/autogen) — Microsoft의 타입화된 액터 프레임워크
- [Cognition AI (Devin)](https://cognition.ai) — 참고 제품
- [Factory Droids](https://www.factory.ai) — 대안 참고 제품
- [Google A2A 프로토콜](https://a2a-protocol.org/latest/) — 에이전트 간 메시징 스펙
- [git worktree 문서](https://git-scm.com/docs/git-worktree) — 격리의 기반
- [SWE-bench Pro](https://www.swebench.com) — 평가 대상
