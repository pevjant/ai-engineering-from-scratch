# LLM 평가 — RAGAS, DeepEval, G-Eval (LLM Evaluation — RAGAS, DeepEval, G-Eval)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 완전 일치(exact-match)와 F1은 의미상 동치를 놓칩니다. 사람이 검토하기에는 규모가 안 됩니다. LLM-as-judge가 프로덕션(운영 환경)의 해답입니다 — 물론 그 숫자를 믿을 수 있을 만큼 충분히 보정(calibration)한 후에야.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 13(질의응답), 페이즈 5 · 14(정보 검색)
**소요 시간:** 약 75분

## 문제 상황

여러분의 RAG 시스템이 "June 29th, 2007."이라고 답했습니다.
정답 레퍼런스는 "June 29, 2007."입니다.
완전 일치(Exact Match)는 0점. F1은 약 75%. 사람이라면 100점을 줄 점수입니다.

이제 테스트 케이스 1만 개에 곱해 보세요. 그리고 검색기, 청킹, 프롬프트, 모델이 바뀔 때마다 또 곱해 보세요. 필요한 것은 의미를 이해하고, 대규모로 저렴하게 돌고, 회귀에 대해 거짓말을 하지 않고, 올바른 실패 양상을 드러내는 평가기입니다.

2026년에는 이 문제를 책임지는 세 가지 프레임워크가 있습니다.

- **RAGAS.** Retrieval-Augmented Generation ASsessment. NLI + LLM-judge 백엔드를 갖춘 네 가지 RAG 지표(faithfulness, answer-relevance, context-precision, context-recall). 연구에 기반하고 가볍습니다.
- **DeepEval.** LLM을 위한 Pytest. G-Eval, task-completion, 환각, 편향 지표. CI/CD 네이티브.
- **G-Eval.** 하나의 방법론(그리고 DeepEval의 지표): chain-of-thought와 커스텀 기준으로 0~1 점수를 매기는 LLM-as-judge.

세 가지 모두 LLM-as-judge에 기댑니다. 이 레슨은 그 방법론과, 그 주변의 신뢰 계층에 대한 감각을 길러 줍니다.

## 개념

![네 가지 평가 차원, LLM-as-judge 아키텍처](../assets/llm-evaluation.svg)

**LLM-as-judge.** 정적 지표를, 루브릭이 주어졌을 때 출력에 점수를 매기는 LLM으로 바꿉니다. `(query, context, answer)`가 주어지면 평가자(judge) LLM에게 프롬프트를 줍니다: "faithfulness 기준으로 0~1점을 매겨." 점수가 돌아옵니다.

왜 통하는가: LLM은 인간 판단을 아주 적은 비용으로 근사합니다. 케이스당 약 $0.003인 GPT-4o-mini라면 $5 이하로 1,000 샘플 회귀 평가를 돌릴 수 있습니다.

왜 조용히 실패하는가:

1. **평가자 편향.** 평가자는 더 긴 답, 같은 모델 계열의 답, 프롬프트 스타일에 맞는 답을 선호합니다.
2. **JSON 파싱 실패.** 잘못된 JSON → NaN 점수 → 집계에서 조용히 제외. RAGAS 사용자들이 잘 아는 고통입니다. try/except + 명시적 실패 모드로 게이트를 세우세요.
3. **모델 버전에 따른 드리프트.** 평가자를 업그레이드하면 모든 지표가 바뀝니다. 평가자 모델 + 버전을 고정하세요.

**RAG의 네 가지.**

| 지표 | 질문 | 백엔드 |
|--------|----------|---------|
| Faithfulness | 답변의 각 주장이 검색된 컨텍스트에서 나왔는가? | NLI 기반 함의(entailment) 판별 |
| 답변 관련성 | 답변이 질문에 부합하는가? | 답변에서 가상 질문을 생성해 실제 질문과 비교 |
| 컨텍스트 정밀도 | 검색된 청크 중 관련 있는 비율은? | LLM-judge |
| 컨텍스트 재현율 | 검색이 필요한 것을 전부 찾았는가? | 정답과 비교하는 LLM-judge |

**G-Eval.** 커스텀 기준을 정의합니다: "답변이 올바른 출처를 인용했는가?" 프레임워크가 이를 chain-of-thought 평가 단계로 자동 확장한 뒤 0~1점을 매깁니다. RAGAS가 다루지 않는 도메인 특화 품질 차원에 적합합니다.

**보정(Calibration).** 인간 레이블과의 상관관계를 확인하기 전까지는 날것의 평가자 점수를 절대 믿지 마세요. 수작업 레이블 예시 100개를 실행하고, 평가자 점수 대 인간 점수를 그래프로 그리고, 스피어만 상관계수(Spearman rho)를 계산합니다. rho가 0.7 미만이면 평가자 루브릭을 고쳐야 합니다.

```figure
n5-judge-gauge
```

## 직접 만들기

### 단계 1: NLI로 faithfulness 측정(RAGAS 스타일)

```python
from typing import Callable
from transformers import pipeline

nli = pipeline("text-classification",
               model="MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
               top_k=None)

# `llm`은 모든 콜러블: 프롬프트 str -> 생성된 str.
# 예: llm = lambda p: client.messages.create(model="claude-haiku-4-5", ...).content[0].text
LLM = Callable[[str], str]


def atomic_claims(answer: str, llm: LLM) -> list[str]:
    prompt = f"""Break this answer into simple factual claims (one per line):
{answer}
"""
    return llm(prompt).splitlines()


def faithfulness(answer: str, context: str, llm: LLM) -> float:
    claims = atomic_claims(answer, llm)
    if not claims:
        return 0.0
    supported = 0
    for claim in claims:
        result = nli({"text": context, "text_pair": claim})[0]
        entail = next((s for s in result if s["label"] == "entailment"), None)
        if entail and entail["score"] > 0.5:
            supported += 1
    return supported / len(claims)
```

답변을 원자적 주장으로 분해합니다. 각 주장을 검색된 컨텍스트와 NLI로 검사합니다. faithfulness = 뒷받침된 주장의 비율.

### 단계 2: 답변 관련성

```python
import numpy as np
from sentence_transformers import SentenceTransformer

# encoder: .encode(texts, normalize_embeddings=True) -> ndarray 를 구현한 모든 모델
# 예: encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")

def answer_relevance(question: str, answer: str, encoder, llm: LLM, n: int = 3) -> float:
    prompt = f"Write {n} questions this answer could be the answer to:\n{answer}"
    generated = [line for line in llm(prompt).splitlines() if line.strip()][:n]
    if not generated:
        return 0.0
    q_emb = np.asarray(encoder.encode([question], normalize_embeddings=True)[0])
    g_embs = np.asarray(encoder.encode(generated, normalize_embeddings=True))
    sims = [float(q_emb @ g_emb) for g_emb in g_embs]
    return sum(sims) / len(sims)
```

답변이 실제 질문이 아니라 다른 질문들을 함의한다면 관련성 점수가 떨어집니다.

### 단계 3: G-Eval 커스텀 지표

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase

metric = GEval(
    name="Correctness",
    criteria="The answer should be factually accurate and match the expected output.",
    evaluation_steps=[
        "Read the expected output.",
        "Read the actual output.",
        "List factual claims in the actual output.",
        "For each claim, mark supported or unsupported by the expected output.",
        "Return score = fraction supported.",
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
)

test = LLMTestCase(input="When was the first iPhone released?",
                   actual_output="June 29th, 2007.",
                   expected_output="June 29, 2007.")
metric.measure(test)
print(metric.score, metric.reason)
```

평가 단계가 곧 루브릭입니다. 명시적인 단계들이 암시적인 "0~1점을 매겨" 프롬프트보다 안정적입니다.

### 단계 4: CI 게이트

```python
import deepeval
from deepeval.metrics import FaithfulnessMetric, ContextualRelevancyMetric


def test_rag_system():
    cases = load_regression_cases()
    faith = FaithfulnessMetric(threshold=0.85)
    rel = ContextualRelevancyMetric(threshold=0.7)
    for case in cases:
        faith.measure(case)
        assert faith.score >= 0.85, f"faithfulness regression on {case.id}"
        rel.measure(case)
        assert rel.score >= 0.7, f"relevancy regression on {case.id}"
```

pytest 파일로 만들어 출시하세요. 모든 PR에서 실행하고, 회귀가 있으면 병합을 막습니다.

### 단계 5: 밑바닥부터 만드는 장난감 평가

`code/main.py`를 보세요. 표준 라이브러리만으로 faithfulness(답변 주장과 컨텍스트의 중첩)와 관련성(답변 토큰과 질문 토큰의 중첩)을 근사한 코드입니다. 프로덕션용은 아닙니다. 형태를 보여 주는 용도입니다.

## 흔한 실수

- **보정 생략.** 인간 레이블과 0.3의 상관관계를 가진 평가자는 그냥 노이즈입니다. 출시 전에 보정 실행을 요구하세요.
- **자기 평가.** 같은 LLM으로 생성과 평가를 모두 하면 점수가 10~20% 부풀어 오릅니다. 평가자는 다른 모델 계열을 쓰세요.
- **쌍대 평가(pairwise)의 위치 편향.** 평가자는 먼저 제시된 선택지를 선호합니다. 항상 순서를 무작위화하고 양쪽 모두로 실행하세요.
- **평균이 실패를 가리는 문제.** 평균 0.85는 종종 5%의 치명적 실패를 숨깁니다. 항상 하위 분위(quantile)를 살펴 보세요.
- **골든 데이터셋의 부패.** 버전 관리가 안 된 평가셋은 시간이 지나며 변해서 종적 비교를 망칩니다. 데이터셋에 변경마다 태그를 다세요.
- **LLM 비용.** 규모가 커지면 평가자 호출이 비용을 지배합니다. 보정 임계값을 충족하는 가장 저렴한 모델을 쓰세요. GPT-4o-mini, Claude Haiku, Mistral-small.

## 활용하기

2026년의 표준 스택:

| 사용 사례 | 프레임워크 |
|---------|-----------|
| RAG 품질 모니터링 | RAGAS (4개 지표) |
| CI/CD 회귀 게이트 | DeepEval + pytest |
| 커스텀 도메인 기준 | DeepEval 안의 G-Eval |
| 온라인 실시간 트래픽 모니터링 | 레퍼런스 불필요(reference-free) 모드의 RAGAS |
| 사람이 개입하는 표본 검사 | 어노테이션 UI를 갖춘 LangSmith 또는 Phoenix |
| 레드팀 / 안전 평가 | Promptfoo + DeepEval |

전형적인 스택: 모니터링은 RAGAS, CI는 DeepEval, 새로운 차원은 G-Eval. 세 가지 모두 돌리세요. 서로 다른 의견을 내주기 때문에 유용합니다.

## 출시하기

`outputs/skill-eval-architect.md`로 저장하세요:

```markdown
---
name: eval-architect
description: Design an LLM evaluation plan with calibrated judge and CI gates.
version: 1.0.0
phase: 5
lesson: 27
tags: [nlp, evaluation, rag]
---

사용 사례(RAG / 에이전트 / 생성형 작업)가 주어지면 다음을 출력합니다:

1. 지표. Faithfulness / relevance / context-precision / context-recall + 기준(criteria)이 명시된 커스텀 G-Eval 지표.
2. 평가자(judge) 모델. 모델 이름 + 버전, 비용 대 정확도 근거.
3. 보정(calibration). 수작업 레이블 셋 크기, 인간 대비 목표 스피어만 상관계수(Spearman rho) > 0.7.
4. 데이터셋 버저닝. 태그 전략, 변경 로그, 층화(stratification).
5. CI 게이트. 지표별 임계값, 회귀 윈도우 로직, 하위 분위(bottom-quantile) 알림.

인간 레이블 예시 50개 이상으로 검증되지 않은 평가자에 의존하는 것은 거부합니다. 자기 평가(같은 모델이 생성 + 평가를 모두 수행)는 거부합니다. 하위 10%를 드러내지 않는 집계 전용 보고는 거부합니다. 평가자 업그레이드가 병렬 베이스라인 평가 없이 배포되는 파이프라인은 경고를 표시합니다.
```

## 연습 문제

1. **쉬움.** 환각이 있다는 것을 아는 RAG 예시 10개에 RAGAS를 적용해 보세요. faithfulness 지표가 각각을 잡아 내는지 확인하세요.
2. **보통.** QA 답변 50개의 정확성을 0~1로 직접 레이블링하세요. G-Eval로 점수를 매기고, 평가자와 인간 사이의 스피어만 상관계수를 측정하세요.
3. **어려움.** DeepEval로 pytest CI 게이트를 만들어 보세요. 일부러 검색기를 망가뜨리고 게이트가 실패하는지 확인하세요. 하위 10%에 대한 임계값 검사로 하위 분위 알림을 추가하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| LLM-as-judge | LLM으로 채점하기 | 평가자 모델에게 루브릭을 주고 출력에 0~1점을 매기게 함. |
| RAGAS | RAG 지표 라이브러리 | 레퍼런스 불필요 RAG 지표 4개를 갖춘 오픈소스 평가 프레임워크. |
| Faithfulness | 답이 근거에 충실한가? | 검색된 컨텍스트가 함의하는 답변 주장의 비율. |
| 컨텍스트 정밀도 | 검색된 청크가 관련 있었나? | top-K 청크 중 실제로 도움이 된 것의 비율. |
| 컨텍스트 재현율 | 검색이 전부 찾았나? | 검색된 청크가 뒷받침하는 정답 주장의 비율. |
| G-Eval | 커스텀 LLM 평가자 | 루브릭 + chain-of-thought 평가 단계 + 0~1 점수. |
| 보정(Calibration) | 믿되 검증하라 | 평가자 점수와 인간 점수 사이의 스피어만 상관관계. |

## 더 읽을거리

- [Es et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) — RAGAS 원 논문.
- [Liu et al. (2023). G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment](https://arxiv.org/abs/2303.16634) — G-Eval 원 논문.
- [DeepEval 문서](https://deepeval.com/docs/metrics-introduction) — 오픈소스 프로덕션 스택.
- [Zheng et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) — 편향, 보정, 한계.
- [MLflow GenAI Scorer](https://mlflow.org/blog/third-party-scorers) — RAGAS, DeepEval, Phoenix를 통합하는 프레임워크.
