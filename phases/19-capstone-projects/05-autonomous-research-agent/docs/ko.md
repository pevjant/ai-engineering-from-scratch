> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 05 — 자율 연구 에이전트 (AI-Scientist급)

> Sakana의 AI-Scientist-v2는 완성된 논문을 내놓았습니다. Agent Laboratory는 실험을 돌렸습니다. Allen AI는 트레이스를 공유했습니다. 2026년의 형태는 실험 위의 플랜-실행-검증 트리 탐색, 예산이 묶인 비용, 샌드박스 처리된 코드 실행, 비전 피드백 LaTeX 작성자, 자동화된 NeurIPS식 리뷰어 앙상블입니다. 이 캡스톤은 하나를 만들어 논문당 $30 안에서 끝까지 돌리고, Sakana가 문서화한 샌드박스 탈출 레드팀을 통과하게 만드는 것입니다.

**유형:** Capstone
**언어:** Python (에이전트 + 샌드박스), LaTeX (산출물)
**선수 지식:** 페이즈 2 (ML), 페이즈 3 (딥러닝), 페이즈 7 (트랜스포머), 페이즈 10 (스크래치 LLM), 페이즈 14 (에이전트), 페이즈 15 (자율 시스템), 페이즈 16 (멀티 에이전트), 페이즈 18 (안전)
**활용하는 페이즈:** P0 · P2 · P3 · P7 · P10 · P14 · P15 · P16 · P18
**시간:** 40시간

## 문제

자율 연구 에이전트는 2026년에 문턱을 넘었습니다. Sakana AI의 AI-Scientist-v2는 워크숍 동료 평가를 통과한 생성 논문과 함께 Nature에 실렸습니다. ShinkaEvolve(ICLR 2026)는 이 흐름을 진화하는 가설로 확장했습니다. AMD의 Agent Laboratory는 재현 가능한 트레이스를 출시했습니다. 이 에이전트들은 마법이 아닙니다. 후보 실험의 트리 위에서 돌아가는 플랜-실행-검증 루프에, 비용 상한과 시드가 고정된 샌드박스, 자동화된 리뷰를 얹은 것입니다. 기술의 핵심은 루프와 예산, 그리고 안전 이야기에 있습니다.

좁은 도메인의 시드 아이디어 하나를 상대로(예: 100M 파라미터 트랜스포머의 어텐션 희소성 소거 실험) 루프를 직접 구현하면서 배우게 됩니다. 첫 실행에서 새로운 것을 발견하는 게 가치가 아닙니다. 가치는 인프라에 있습니다: 트리 탐색, 실험 샌드박스, 작성자-리뷰어 루프, 레드팀 보고서. Sakana 팀은 샌드박스 탈출 실패를 문서화했고, 당신의 에이전트는 같은 레드팀을 통과해야 합니다.

## 개념

에이전트는 최적 우선(best-first) 트리 탐색입니다. 노드는 실험 명세입니다: (가설, 설정, 코드, 예상 결과). 확장(expand) 단계는 작은 수정으로 자식을 제안합니다(옵티마이저 교체, 배치 크기 이동, 구성 요소 소거). 각 자식은 하드 자원 상한이 걸린 새 샌드박스에서 돌아갑니다. 결과는 노드를 (신선도 × 품질 × 남은 예산)으로 순위 매기는 점수 함수로 되먹입니다. 트리는 예산이 닳을 때까지 자라고, 이후 최선의 가지가 논문으로 작성됩니다.

작성자는 멀티모달입니다. LaTeX 초안을 만들고, 컴파일하고, 그림을 렌더링하고, 렌더링된 PDF를 Claude Opus 4.7의 비전 모드에 넣어 레이아웃·그림 가독성·주장-증거 정렬에 대한 비평을 받습니다. 다섯 LLM 판정자로 이뤄진 리뷰어 앙상블이 NeurIPS식 점수(신선도, 엄밀성, 명료성, 재현성, 임팩트)를 내놓습니다. 평균이 문턱 아래로 떨어지면 논문은 비평과 함께 작성자에게 돌아갑니다.

안전이 하중을 떠받칩니다. 모든 실험은 네트워크 이그레스(외부 송신)가 없고, 실행 시간이 묶이고, 자원 한도가 고정된 E2B 또는 Daytona 샌드박스에서 돌아갑니다. 에이전트의 코드 생성 단계는 샌드박스를 탈출하는 시스템콜을 막는 정책 계층을 통과합니다. 레드팀 보고서는 Sakana가 문서화한 공격 표면(포크 폭탄, 파일시스템 탈출, LLM이 작성한 네트워크 호출)을 재현합니다.

## 아키텍처

```
seed idea + domain
      |
      v
  literature search (Semantic Scholar + OpenAlex + FAISS cache)
      |
      v
  LangGraph plan-execute-verify tree
      |
      v
  +--- expand node ----+      per-node sandbox
  |                    |      (E2B / Daytona)
  v                    v      resource caps
  child_1           child_k   no network egress
  |                    |      deterministic seeds
  v                    v
  run experiment       run experiment
  |                    |
  v                    v
  score nodes by (novelty, quality, budget)
      |
      v
  best branch -> LaTeX writer
      |
      v
  compile + vision critique (Opus 4.7 vision)
      |
      v
  reviewer ensemble (5 LLM judges, NeurIPS rubric)
      |
      v
  paper.pdf + review.md + trace.json
```

## 스택

- 오케스트레이션: 체크포인팅과 사람 승인 게이트를 갖춘 LangGraph
- 트리 탐색: 실험 노드 위의 자체 최적 우선 탐색(Sakana v2의 AB-MCTS 방식)
- 샌드박스: 실험마다 E2B, 예비로 Docker-in-Docker; cgroups로 자원 상한
- 문헌: Semantic Scholar Graph API + OpenAlex + 초록의 로컬 FAISS 캐시
- 작성자: LaTeX 템플릿 + 그림 비평과 레이아웃용 Claude Opus 4.7 (비전 모드)
- 리뷰어: 판정자 5명(Opus 4.7, GPT-5.4, Gemini 3 Pro, DeepSeek R1, Qwen3-Max)의 앙상블, 가중 집계
- 실험 프레임워크: 실제 실험용 PyTorch 2.5, 로깅용 W&B
- 관측 가능성: 에이전트 트레이스용 Langfuse, 논문당 $30 하드 예산

```figure
ce-experiment-tree
```

## 만들기

1. **시드와 도메인 범위 잡기.** 시드 아이디어를 고릅니다(예: "1B 미만 트랜스포머의 어텐션 맵 희소성 패턴 조사"). 탐색 공간을 정의합니다: 모델, 데이터셋, 컴퓨팅 예산.

2. **문헌 패스.** 가장 많이 인용된 관련 논문 50편을 Semantic Scholar + OpenAlex에서 찾습니다. 초록을 로컬에 캐싱하고, 1페이지짜리 도메인 다이제스트를 생성합니다.

3. **트리 뼈대.** 시드 가설로 루트를 초기화합니다. 작은 수정 제안을 내는 `expand(node) -> children`(자식당 설정 변경 하나)을 구현합니다. `score(node)`를 가중된 신선도 × 품질 × 예산 항으로 구현합니다.

4. **샌드박스 감싸기.** 모든 실험은 `docker run --network=none --memory=8g --cpus=2 --pids-limit=256 --read-only`(또는 동등한 E2B 정책)로 돕니다. 시드는 샌드박스 안에 쓰이고, 출력물은 읽기 전용으로 다시 마운트됩니다.

5. **플랜-실행-검증 루프.** `plan`은 자식을 제안합니다. `execute`는 샌드박스를 돌리고 로그와 지표를 받습니다. `verify`는 지표에 단위 검사를 돌립니다(손실이 줄었는가? 소거 실험이 효과를 고립했는가?). 실패한 노드에는 실패 이유가 트리에 저장됩니다.

6. **작성자.** 예산이 닳으면 최선의 가지를 고릅니다. matplotlib로 그림을 그립니다. 가지 트레이스를 컨텍스트에 넣어 Claude Opus 4.7로 LaTeX 초안을 생성합니다. 컴파일합니다. 컴파일된 PDF를 Opus 4.7 비전에 넣어 비평을 받습니다. 반복합니다.

7. **리뷰어 앙상블.** 다섯 판정자가 NeurIPS식 루브릭으로 초안에 (신선도, 엄밀성, 명료성, 재현성, 임팩트) 점수를 매깁니다. 평균 < 4.0/5이면 비평과 함께 작성자에게 돌려보냅니다. 3회 재작성 후 하드 정지.

8. **레드팀.** 샌드박스를 겨냥한 적대적 과제 모음을 만들거나 통합합니다: 포크 폭탄, 네트워크 유출 시도, 파일시스템 탈출, LLM이 작성한 셸 메타문자. 전부 막히는지 확인합니다. 발견 사항을 정리해 씁니다.

9. **재현성.** 모든 논문에는 트리 탐색 트레이스 JSON, 시드, W&B 실행 링크, 샌드박스 설정, 그리고 끝까지 재현하는 README가 함께 나갑니다.

## 사용해 보기

```
$ ai-scientist run --seed "attention sparsity in sub-1B transformers" --budget 30
[lit]    50 papers, digest in 12s
[tree]   expanded 8 nodes, budget 12/30
[exec]   node #3 sparsity=top-8, loss=2.83 (best so far)
[exec]   node #6 sparsity=top-4, loss=3.12 (worse)
[exec]   ...
[tree]   chose branch rooted at node #3 (novelty 0.62, quality 0.81)
[write]  LaTeX draft v1 complete
[vision] critique: figure 2 legend too small, claim-evidence ok
[write]  draft v2 after 3 edits
[review] mean 4.2/5 (novelty 3.9, rigor 4.3, clarity 4.1, repro 4.5, impact 4.2)
[done]   paper.pdf + review.md + trace.json     $28.40 spent
```

## 출시하기

`outputs/skill-ai-scientist.md`가 산출물입니다. 시드 아이디어 + 도메인 + $30 예산이 주어지면 전체 파이프라인을 돌리고, 검토 가능한 논문과 재현성 번들을 내놓습니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 논문 품질 | 공개된 워크숍 논문 대비 블라인드 루브릭 검토 |
| 20 | 실험 엄밀성 | 베이스라인, 시드, 소거 실험. 모든 주장이 결과 표의 칸으로 뒷받침 |
| 20 | 비용과 컴퓨팅 규율 | 논문당 $30 상한 강제, Langfuse로 추적 |
| 20 | 안전 | 샌드박스 레드팀 통과, 네트워크 정책과 킬 스위치 검증 |
| 15 | 재현성 | 같은 시드로 한 명령 재실행이 논문을 재현 |
| **100** | | |

## 연습 문제

1. 같은 도메인의 서로 다른 시드 아이디어 세 개로 파이프라인을 돌려 보세요. 트리 탐색의 어느 부분이 겹치는지 비교하고, 중복으로 낭비된 컴퓨팅을 찾아보세요.

2. $5 초과로 추정되는 노드에는 실험 실행 전에 사람 확인(human-in-the-loop) 게이트를 추가해 보세요. 총비용이 얼마나 줄어드는지 측정하세요.

3. 리뷰어 앙상블을 단일 판정자로 바꿔 보세요. 알려진 불량 논문의 홀드아웃 세트에서 오수용(false-accept) 비율을 측정하세요.

4. 네트워크 유출 레드팀 테스트를 넣어 보세요: 에이전트가 외부 주소를 `curl`하려는 코드를 작성합니다. `--network=none` 정책이 이를 막는지 확인하고, 시도를 기록하세요.

5. 당신의 트리 탐색을 평면적 무작위 베이스라인(같은 예산, 확장 전략 없음)과 비교하세요. 신선도 × 품질 이득을 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| 트리 탐색 | "AB-MCTS 방식 확장" | 신선도×품질×예산 점수로 실험 노드를 최적 우선 탐색하는 것 |
| 샌드박스 | "실험 격리" | 네트워크 없음, CPU/메모리 상한, 시드 고정, 읽기 전용 입력을 갖춘 컨테이너 |
| 비전 비평 | "렌더 후 읽기" | 논문을 PDF로 컴파일하고 그 PDF를 VLM에 넣어 레이아웃과 주장-증거를 비평하게 하는 것 |
| 리뷰어 앙상블 | "자동화된 동료 평가" | NeurIPS 루브릭으로 논문에 점수를 매기는 여러 LLM 판정자. 가중 집계가 파이프라인을 관문 제어 |
| 신선도 점수 | "새로운가?" | 50편 문헌 캐시와의 근접성에 벌점을 주는 휴리스틱 |
| 비용 상한 | "$ 예산" | 논문당 총 지출의 하드 상한. Langfuse 카운터 + 사전 추정치 |
| 레드팀 | "샌드박스 탈출 감사" | 정책이 잘못됐다면 샌드박스를 탈출했을 적대적 과제들 |

## 더 읽을거리

- [Sakana AI-Scientist-v2 저장소](https://github.com/SakanaAI/AI-Scientist-v2) — 참고용 프로덕션 연구 에이전트
- [Sakana AI-Scientist-v1 논문 (arXiv:2408.06292)](https://arxiv.org/abs/2408.06292) — 최초의 방법론
- [ShinkaEvolve (Sakana ICLR 2026)](https://sakana.ai) — 진화형 확장
- [Agent Laboratory (AMD)](https://github.com/SamuelSchmidgall/AgentLaboratory) — 다중 역할 연구소 프레임워크
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/) — 참고용 오케스트레이션 계층
- [Semantic Scholar Graph API](https://api.semanticscholar.org/) — 문헌 검색
- [E2B 샌드박스](https://e2b.dev) — 참고용 실험 격리
- [NeurIPS 리뷰어 가이드라인](https://neurips.cc/Conferences/2026/Reviewer-Guidelines) — 리뷰어 앙상블이 인코딩하는 루브릭
