> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 08 — 규제 산업(Regulated Vertical)용 프로덕션(운영 환경) RAG 챗봇

> Harvey, Glean, Mendable, LlamaCloud는 모두 2026년에 같은 프로덕션 형태로 운영됩니다. 문서는 docling이나 Unstructured로 흡수(ingestion)하고, 시각 자료는 ColPali로 처리합니다. 하이브리드 검색을 하고, bge-reranker-v2-gemma로 재순위화(re-rank)합니다. Claude Sonnet 4.7로 프롬프트 캐싱(히트율 60~80%)을 활용해 종합 응답을 만듭니다. Llama Guard 4와 NeMo Guardrails로 지키고, Langfuse와 Phoenix로 지켜보고(모니터링), 200문항 골든 셋으로 RAGAS로 채점합니다. 규제 도메인(법률, 임상, 보험) 중 하나를 골라 직접 만들어 보세요. 이 캡스톤의 합격 기준은 골든 셋 통과, 레드 팀 공격 방어, 드리프트 대시보드 구축입니다.

**유형:** 캡스톤
**언어:** Python (파이프라인 + API), TypeScript (채팅 UI)
**선수 지식:** 페이즈 5 (NLP), 페이즈 7 (트랜스포머), 페이즈 11 (LLM 엔지니어링), 페이즈 12 (멀티모달), 페이즈 17 (인프라), 페이즈 18 (안전성)
**활용 페이즈:** P5 · P7 · P11 · P12 · P17 · P18
**소요 시간:** 30시간

## 문제

규제 도메인 RAG(검색 증강 생성) — 법률 계약서, 임상 시험 프로토콜, 보험 약관 같은 — 는 2026년에 가장 많이 출시된 프로덕션 형태입니다. 투자 대비 효과(ROI)가 분명하고, 잘못됐을 때 결과도 뚜렷하기 때문입니다. Harvey(Allen & Overy)는 법률용으로 만들었습니다. Mendable은 개발자 문서 버전을 출시하고 있고, Glean은 엔터프라이즈 검색을 담당합니다. 패턴은 이렇습니다: 문서를 고정밀도로 흡수하고, 재순위화가 붙은 하이브리드 검색을 하고, 인용 강제와 프롬프트 캐싱으로 응답을 종합하고, 여러 겹의 안전 장치로 지키고, 드리프트를 끊임없이 감시합니다.

어려운 부분은 모델이 아닙니다. 진짜 어려운 것은 관할권(jurisdiction)을 인식하는 컴플라이언스(HIPAA, GDPR, SOC2), 인용 단위의 감사 가능성, 비용 관리(캐시 히트율이 높으면 프롬프트 캐싱이 60~90% 할인을 해줍니다), RAGAS 충실도를 통한 환각 탐지, 그리고 원본 문서가 갱신됐는데 인덱스가 따라가지 못할 때의 드리프트 탐지입니다. 이 캡스톤은 여러분에게 이 모든 것을 200문항 골든 셋 위에서, 레드 팀 스위트를 곁들여 출시하라고 요구합니다.

## 개념

파이프라인은 두 부분으로 이루어져 있습니다. **흡수(Ingestion)**: docling이나 Unstructured가 구조화된 문서를 파싱하고, ColPali가 시각적으로 풍부한 문서를 처리합니다. 청크에는 요약, 태그, 역할 기반 접근 레이블이 붙습니다. 벡터는 pgvector + pgvectorscale(벡터 5천만 개 미만) 또는 Qdrant Cloud로 들어가고, 희소(sparse) BM25가 나란히 돕니다. **대화**: LangGraph가 메모리와 멀티턴을 담당합니다. 각 질의는 하이브리드 검색을 수행하고, bge-reranker-v2-gemma-2b로 재순위화하고, Claude Sonnet 4.7(프롬프트 캐시 적용)으로 종합한 뒤, Llama Guard 4와 NeMo Guardrails를 통과시켜, 인용이 붙은 응답을 내보냅니다.

평가 스택은 네 겹입니다. **골든 셋**(인용이 붙은 레이블된 Q/A 200개)은 정확성을 재습니다. **레드 팀**(탈옥 공격, PII 추출 시도, 도메인 밖 질문)은 안전성을 재습니다. **RAGAS**는 충실도 / 답변 관련성 / 컨텍스트 정밀도를 턴마다 자동으로 채점합니다. **드리프트 대시보드**(Arize Phoenix)는 검색 품질과 환각 점수를 매주 지켜봅니다.

프롬프트 캐싱이 비용 지렛대입니다. Claude 4.5+와 GPT-5+는 시스템 프롬프트 + 검색된 컨텍스트 캐싱을 지원합니다. 히트율이 60~80%면 질의당 비용이 3~5배 떨어집니다. 높은 캐시 히트율을 얻으려면 파이프라인이 안정적인 접두사(시스템 프롬프트 + 재순위화된 컨텍스트를 앞쪽에 배치)를 갖도록 설계해야 합니다.

## 아키텍처

```
documents (contracts, protocols, policies)
      |
      v
docling / Unstructured parse + ColPali for visuals
      |
      v
chunks + summaries + role-labels + jurisdiction tags
      |
      v
pgvector + pgvectorscale  +  BM25 (Tantivy)
      |
query + role + jurisdiction
      |
      v
LangGraph conversational agent
   +--- retrieve (hybrid)
   +--- filter by role + jurisdiction
   +--- rerank (bge-reranker-v2-gemma-2b or Voyage rerank-2)
   +--- synthesize (Claude Sonnet 4.7, prompt cached)
   +--- guard (Llama Guard 4 + NeMo Guardrails + Presidio output PII scrub)
   +--- cite + return
      |
      v
eval:
  RAGAS faithfulness / answer_relevance / context_precision (online)
  Langfuse annotation queue (sampled)
  Arize Phoenix drift (weekly)
  red team suite (pre-release)
```

## 스택

- 흡수: 구조화된 문서는 Unstructured.io 또는 docling; 시각적으로 풍부한 PDF는 ColPali
- 벡터 DB: 벡터 5천만 개 미만이면 pgvector + pgvectorscale; 그 외에는 Qdrant Cloud
- 희소 검색: 필드 가중치를 적용한 Tantivy BM25
- 오케스트레이션: LlamaIndex Workflows (흡수) + LangGraph (대화)
- 재순위기(re-ranker): bge-reranker-v2-gemma-2b 셀프 호스팅 또는 Voyage rerank-2 호스팅
- LLM: 프롬프트 캐싱을 적용한 Claude Sonnet 4.7; 폴백으로 셀프 호스팅 Llama 3.3 70B
- 평가: RAGAS 0.2 온라인, 환각·탈옥 스위트용 DeepEval
- 관측 가능성(옵저버빌리티): 어노테이션 큐를 갖춘 셀프 호스팅 Langfuse; 드리프트용 Arize Phoenix
- 가드레일: Llama Guard 4 입력/출력 분류기, NeMo Guardrails v0.12 정책, Presidio PII 스크럽
- 컴플라이언스: 청크에 붙은 역할 기반 접근 레이블; GDPR/HIPAA용 관할권 태그

```figure
canary-rollout
```

## 직접 만들기

1. **흡수(Ingestion).** 코퍼스(제대로 만들려면 문서 1,000~10,000개)를 Unstructured나 docling으로 파싱합니다. 스캔본이거나 시각 요소가 많은 페이지는 ColPali로 보냅니다. 요약, 역할 레이블, 관할권 태그가 붙은 청크를 만듭니다.

2. **인덱싱.** 밀집(dense) 임베딩(Voyage-3 또는 Nomic-embed-v2)을 pgvector + pgvectorscale에 넣습니다. Tantivy로 BM25 보조 인덱스를 만듭니다. 역할과 관할권 필터는 페이로드로 저장합니다.

3. **하이브리드 검색.** 먼저 역할+관할권으로 필터링하고, 그다음 밀집 검색과 BM25를 병렬로 수행합니다. 상호 순위 융합(reciprocal rank fusion)으로 합치고, 상위 20개를 재순위기로, 상위 5개를 종합 단계로 보냅니다.

4. **프롬프트 캐싱으로 종합.** 시스템 프롬프트 + 고정 정책은 캐시 헤더에 넣고, 재순위화된 컨텍스트는 캐시 확장 부분에, 사용자 질문은 캐시 밖 접미사로 둡니다. 안정 상태에서 캐시 히트율 60~80%를 목표로 합니다.

5. **가드레일.** 입력에는 Llama Guard 4를 적용합니다. NeMo Guardrails 레일이 도메인 밖 질문이나 정책 금지 주제를 막아줍니다. Presidio가 출력에 섞인 실수로 인한 PII를 제거하고, 인용 강제 필터가 마지막으로 검사합니다.

6. **골든 셋.** 도메인 전문가가 (답변, 인용)과 함께 레이블을 붙인 Q/A 쌍 200개를 만듭니다. 정확한 인용 일치, 답변 정확성, 충실도(RAGAS)로 에이전트를 채점합니다.

7. **레드 팀.** 50개의 적대적 프롬프트: 탈옥 공격(PAIR, TAP), PII 유출 시도, 도메인 밖 질문, 관할권 간 누출. 합격/불합격과 심각도로 채점합니다.

8. **드리프트 대시보드.** Arize Phoenix가 검색 품질(nDCG, 인용 충실도)을 매주 추적합니다. 5% 하락 시 알림을 울립니다.

9. **비용 보고서.** Langfuse: 프롬프트 캐시 히트율, 질의당 토큰 수, 단계별 질의당 달러($/query) 분해.

## 사용해 보기

```
$ chat --role=analyst --jurisdiction=GDPR
> what is the data-retention obligation for EU user profiles under our contract?
[retrieve]  hybrid top-20 filtered to GDPR + analyst-role
[rerank]    top-5 kept
[synth]     claude-sonnet-4.7, cache hit 74%, 0.8s
answer:
  The contract (Section 12.4, Master Services Agreement dated 2024-03-11)
  obligates EU user profile deletion within 30 days of termination per GDPR
  Article 17. The DPA amendment (DPA-v2.1, Section 5) extends this to 14 days
  for "restricted" category data.
  citations: [MSA-2024-03-11 s12.4, DPA-v2.1 s5]
```

## 출시하기

`outputs/skill-production-rag.md`가 산출물을 설명합니다. 컴플라이언스 레이블을 붙여 배포하고, 루브릭을 통과하고, 실시간 드리프트 모니터링으로 관찰하는 규제 도메인 챗봇입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | RAGAS 충실도 + 답변 관련성 | 골든 셋(200 Q/A)에 대한 온라인 점수 |
| 20 | 인용 정확성 | 검증 가능한 출처 앵커가 붙은 답변의 비율 |
| 20 | 가드레일 커버리지 | Llama Guard 4 통과율 + 탈옥 스위트 결과 |
| 20 | 비용 / 지연 시간 엔지니어링 | 프롬프트 캐시 히트율, p95 지연 시간, 질의당 비용 |
| 15 | 드리프트 모니터링 대시보드 | 주간 검색 품질 추이를 보여주는 Phoenix 실시간 대시보드 |
| **100** | | |

## 연습 문제

1. 다른 관할권(예: GDPR과 나란히 HIPAA)으로 두 번째 코퍼스 조각을 만듭니다. 역할+관할권 필터링이 관할권 간 누출을 막아내는 모습을 20문항 교차 관할권 프로브로 시연합니다.

2. 1주일치 프로덕션 트래픽에 걸쳐 프롬프트 캐시 히트율을 측정합니다. 어떤 질의가 캐시 접두사를 깨는지 찾아내고 구조를 다시 잡습니다.

3. 10k 토큰 요약 버퍼를 곁들인 멀티턴 메모리를 추가합니다. 대화가 길어질수록 충실도가 떨어지는지 측정합니다.

4. Claude Sonnet 4.7을 셀프 호스팅 Llama 3.3 70B로 바꿔 봅니다. 질의당 비용과 충실도 변화를 측정합니다.

5. "확신 없음(unsure)" 모드를 추가합니다. 재순위화된 상위 점수가 임계값 아래면, 에이전트가 답변 대신 "확신할 만한 인용이 없습니다"라고 말하게 합니다. 잘못된 확신이 얼마나 줄었는지 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| 프롬프트 캐싱 | "시스템 + 컨텍스트 캐시" | Claude/OpenAI 기능: 캐시된 접두사 토큰은 히트 시 60~90% 할인 |
| RAGAS | "RAG 평가기" | 충실도, 답변 관련성, 컨텍스트 정밀도의 자동 채점 |
| 골든 셋 | "레이블된 평가" | 인용이 붙은 전문가 레이블 Q/A 200개 이상; 정답 기준(ground truth) |
| 관할권 태그 | "컴플라이언스 레이블" | 청크에 붙는 GDPR/HIPAA/SOC2 범위; 검색 필터가 강제 |
| 인용 충실도 | "근거 기반 답변 비율" | 검색 가능한 출처 구간으로 뒷받침되는 주장의 비율 |
| 드리프트 | "검색 품질 저하" | nDCG나 인용 점수의 주간 변화; 알림 임계값 5% |
| 레드 팀 | "적대적 평가" | 출시 전 수행하는 탈옥, PII 추출, 도메인 밖 프로브 |

## 더 읽을거리

- [Harvey AI](https://www.harvey.ai) — 법률 프로덕션 스택의 참고 사례
- [Glean 엔터프라이즈 검색](https://www.glean.com) — 엔터프라이즈 규모 RAG의 참고 사례
- [Mendable 문서](https://mendable.ai) — 개발자 문서 RAG 참고 사례
- [LlamaCloud Parse + Index](https://docs.cloud.llamaindex.ai/llamaparse/getting_started) — 관리형 흡수(ingestion)
- [Anthropic 프롬프트 캐싱](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — 비용 지렛대의 참고 문서
- [RAGAS 0.2 문서](https://docs.ragas.io/) — 표준 RAG 평가 프레임워크
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — 드리프트 관측 가능성의 참고 사례
- [Llama Guard 4](https://www.llama.com/docs/model-cards-and-prompt-formats/llama-guard-4/) — 2026년 안전 분류기
- [NeMo Guardrails v0.12](https://docs.nvidia.com/nemo-guardrails/) — 정책 레일 프레임워크
