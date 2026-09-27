> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 02 — 코드베이스 RAG (교차 저장소 의미 검색)

> 2026년 제대로 된 엔지니어링 조직이라면 문자열이 아니라 의미를 이해하는 내부 코드 검색을 운영합니다. Sourcegraph Amp, Cursor의 코드베이스 답변, Augment의 엔터프라이즈 그래프, Aider의 repomap, Pinterest의 내부 MCP — 모두 같은 형태입니다. 여러 저장소를 받아들이고, tree-sitter로 파싱하고, 함수/클래스 수준 청크를 임베딩하고, 하이브리드 검색하고, 재순위화하고, 인용을 붙여 답합니다. 이 캡스톤은 10개 저장소에 걸쳐 200만 줄의 코드를 다루고, git push마다 증분 재색인을 견뎌내는 검색 시스템을 만들게 합니다.

**유형:** Capstone
**언어:** Python (수집), TypeScript (API + UI)
**선수 지식:** 페이즈 5 (NLP 기초), 페이즈 7 (트랜스포머), 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구), 페이즈 17 (인프라)
**활용하는 페이즈:** P5 · P7 · P11 · P13 · P17
**시간:** 30시간

## 문제

2026년까지 모든 프론티어 코딩 에이전트는 코드베이스 검색 계층을 기본으로 깔고 나옵니다. 컨텍스트 윈도우만으로는 교차 저장소 질문을 해결할 수 없기 때문입니다. Claude의 1M 토큰 컨텍스트가 도움은 되지만, 순위가 매겨진 검색의 필요를 없애 주지는 않습니다. 날것 청크 위의 순진한 코사인 검색은 생성된 코드에서, 모노레포의 코드 중복에서, 자주 임포트되지 않는 심볼의 긴 꼬리에서 결과를 오염시킵니다. 프로덕션(운영 환경)의 답은 재순위화기(re-ranker)를 얹은, AST를 인식하는 청크 위의 하이브리드(dense + BM25) 검색, 그리고 심볼 참조 그래프로 떠받치는 구성입니다.

이것은 튜토리얼용 저장소 하나가 아니라 실제 저장소 무리를 색인하고, MRR@10과 인용 충실도, 증분 신선도를 측정하면서 배우는 것입니다. 실패 모드는 인프라적입니다: 10만 파일짜리 모노레포, 파일 절반을 다시 건드리는 푸시, 정답을 내려면 네 저장소를 넘나들어야 하는 질의.

## 개념

AST 인식 수집 파이프라인은 각 파일을 tree-sitter로 파싱하고, 함수/클래스 노드를 뽑아내며, 고정 토큰 윈도우가 아니라 노드 경계에서 청크를 자릅니다. 각 청크는 세 가지 표현을 갖습니다: dense 임베딩(Voyage-code-3 또는 nomic-embed-code), 희소(sparse) BM25 용어, 그리고 짧은 자연어 요약. 요약은 세 번째 검색 가능 매체를 더합니다. 사용자는 "X는 어떻게 권한 검사를 하나"라고 묻는데, 코드에는 `check_permission`만 있어도 요약에는 "authz"가 언급되어 검색에 걸릴 수 있는 것입니다.

검색은 하이브리드입니다. 질의가 dense 검색과 BM25 검색을 동시에 발사하고, 상위 k를 병합한 뒤, 그 합집합을 크로스 인코더 재순위화기(Cohere rerank-3 또는 bge-reranker-v2-gemma-2b)에 넘깁니다. 재순위화된 목록은 긴 컨텍스트 합성기(프롬프트 캐싱을 켠 Claude Sonnet 4.7, 또는 셀프 호스팅 Llama 3.3 70B)로 가며, 모든 주장을 파일과 줄 범위로 인용하라는 지시를 받습니다. 인용 없는 답변은 후처리 필터가 거부합니다.

증분 신선도가 인프라 문제입니다. git push가 diff를 유발합니다: 어떤 파일이 바뀌었고, 어떤 심볼이 바뀌었는지. 영향을 받은 청크만 다시 임베딩합니다. 영향을 받은 파일 간 심볼 에지(임포트, 메서드 호출)는 재계산합니다. 커밋마다 200만 줄을 다 처리하지 않고도 인덱스는 일관성을 유지합니다.

## 아키텍처

```
git push --> webhook --> ingest worker (LlamaIndex Workflow)
                           |
                           v
             tree-sitter parse + AST chunk
                           |
            +--------------+----------------+
            v              v                v
          dense        BM25 index       summary (LLM)
        (Voyage / bge)  (Tantivy)        (Haiku 4.5)
            |              |                |
            +------> Qdrant / pgvector <----+
                            |
                            v
                      symbol graph (Neo4j / kuzu)
                            |
  query --> LangGraph agent (retrieve -> rerank -> synth)
                            |
                            v
                 Claude Sonnet 4.7 1M context
                            |
                            v
                 answer + file:line citations
```

## 스택

- 파싱: 17개 언어 문법(Python, TS, Rust, Go, Java, C++ 등)을 갖춘 tree-sitter
- dense 임베딩: Voyage-code-3(호스티드) 또는 nomic-embed-code-v1.5(셀프 호스팅), 예비로 bge-code-v1
- 희소 인덱스: BM25F를 쓰는 Tantivy(Rust), 심볼 이름 vs 본문에 필드 가중
- 벡터 DB: 하이브리드 검색을 지원하는 Qdrant 1.12, 또는 5천만 벡터 미만 팀을 위한 pgvector + pgvectorscale
- 청크 요약 모델: Claude Haiku 4.5 또는 Gemini 2.5 Flash, 프롬프트 캐싱 적용
- 재순위화기: Cohere rerank-3 또는 셀프 호스팅 bge-reranker-v2-gemma-2b
- 오케스트레이션: 수집은 LlamaIndex Workflows, 질의 에이전트는 LangGraph
- 합성기: 프롬프트 캐싱을 켠 Claude Sonnet 4.7 (1M 컨텍스트)
- 심볼 그래프: 임포트/호출 에지를 위한 Neo4j(매니지드) 또는 kuzu(임베디드)
- 관측 가능성: 검색 + 합성 단계마다 Langfuse 스팬

```figure
ce-hybrid-retrieval
```

## 만들기

1. **수집 워커.** 푸시 훅마다 git 히스토리를 순회합니다. 바뀐 파일을 모읍니다. 파일마다 tree-sitter로 파싱하고, 전체 소스 범위와 함께 함수/클래스 노드를 추출합니다. 청크 레코드 `{repo, path, start_line, end_line, symbol, body}`를 발행합니다.

2. **청크 요약기.** 청크를 묶어 Haiku 4.5 호출로 보내되 시스템 전문에 프롬프트 캐싱을 켭니다. 프롬프트: "이 함수를 한 문장으로 요약하되 공개 계약(public contract)과 부수 효과를 이름으로 적어라." 요약을 청크 옆에 저장합니다.

3. **임베딩 풀.** 두 개의 병렬 큐: dense(Voyage-code-3 배치 128)와 요약(같은 모델이되 요약 문자열 대상). 벡터를 페이로드 `{repo, path, start_line, end_line, symbol, kind}`와 함께 Qdrant에 씁니다.

4. **BM25 인덱스.** 필드 가중 Tantivy 인덱스: 심볼 이름 가중치 4, 심볼 본문 가중치 1, 요약 가중치 2. "X를 하는 함수를 찾아줘" 질의와 함께 "이름이 X인 함수를 찾아줘" 질의도 가능해집니다.

5. **심볼 그래프.** 청크마다 에지를 기록합니다: 임포트(이 파일이 저장소 Z의 심볼 Y를 사용), 호출(이 함수가 클래스 C의 메서드 M을 호출), 상속. kuzu에 저장합니다. 질의 시점에 저장소 경계를 넘어 검색을 확장하는 데 씁니다.

6. **질의 에이전트.** 노드 세 개를 가진 LangGraph. `retrieve`는 dense + BM25를 병렬 발사하고 (repo, path, symbol)로 중복을 제거합니다. `rerank`는 크로스 인코더를 상위 50에 돌리고 상위 10을 남깁니다. `synth`는 재순위화된 청크를 컨텍스트에 넣어 Claude Sonnet 4.7을 호출하고, 시스템 프롬프트를 캐싱하며, file:line 인용을 요구합니다.

7. **인용 강제.** 모델 출력을 파싱합니다. `(repo/path:start-end)` 앵커 없는 주장은 재질문(re-ask) 표시를 하거나 버립니다. 인용된 것만 담은 답변을 사용자에게 돌려줍니다.

8. **증분 재색인.** 웹훅마다 심볼 수준 diff를 계산합니다. 텍스트가 바뀐 청크만 다시 임베딩합니다. 임포트가 바뀐 청크의 심볼 에지는 재계산합니다. 목표치: 200만 LOC 규모에서 50파일 푸시를 60초 안에 재색인.

9. **평가.** 교차 저장소 질문 100개에 정답 file:line을 라벨로 붙입니다. MRR@10, nDCG@10, 인용 충실도(검증 가능한 앵커를 가진 주장의 비율), p50/p99 지연 시간을 측정합니다.

## 사용해 보기

```
$ code-rag ask "how is S3 multipart abort wired into our retry budget?"
[retrieve]  12 chunks dense + 7 chunks bm25, 16 unique after dedup
[rerank]    top-5 kept (cohere rerank-3)
[synth]     claude-sonnet-4.7, cache hit rate 68%, 2.1s
answer:
  Multipart aborts are triggered by `AbortMultipartOnFail` in
  services/uploader/retry.go:122-148, which decrements the per-bucket
  retry budget defined in config/budgets.yaml:34-51 ...
  citations: [services/uploader/retry.go:122-148, config/budgets.yaml:34-51,
              libs/s3client/multipart.ts:44-61]
```

## 출시하기

산출물 스킬은 `outputs/skill-codebase-rag.md`입니다. 저장소 코퍼스가 주어지면 수집 파이프라인, 하이브리드 인덱스, 질의 에이전트를 세우고, 어떤 교차 저장소 질문이든 인용된 답을 돌려줍니다. 채점 기준:

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 검색 품질 | 100질문 홀드아웃 세트에서 MRR@10과 nDCG@10 |
| 20 | 인용 충실도 | 검증 가능한 file:line 앵커를 가진 답변 주장의 비율 |
| 20 | 지연 시간과 규모 | 색인된 코퍼스 규모에서 10k QPS의 p95 질의 지연 시간 |
| 20 | 증분 색인 정확성 | 50파일 커밋이 git push부터 검색 가능해질 때까지 걸린 시간 |
| 15 | UX와 답변 포맷 | 인용 클릭 가능성, 스니펫 미리보기, 후속 질문 편의성 |
| **100** | | |

## 연습 문제

1. Voyage-code-3를 셀프 호스팅 nomic-embed-code로 바꿔 보세요. MRR@10 변화를 측정하고, 재순위화를 켜면 격차가 닫히는지 보고하세요.

2. 코퍼스에 생성된 코드(LLM이 만든 보일러플레이트)를 20% 섞어 넣고 다시 평가해 보세요. 검색 오염을 관찰하세요. 페이로드에 "generated" 플래그를 추가하고 그 결과물의 가중치를 낮추세요.

3. 당신의 코퍼스 규모에서 Qdrant 하이브리드 검색과 pgvector + pgvectorscale을 벤치마크하세요. 배치 크기 1의 p99를 보고하세요.

4. 표본 추출 기반 드리프트 검사를 추가하세요: 매주 100질문 평가를 다시 돌립니다. MRR@10이 5% 넘게 떨어지면 알립니다.

5. 교차 언어 심볼 해석으로 확장하세요: gRPC로 Go 서비스를 호출하는 Python 함수. 심볼 그래프를 써서 둘을 연결해 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| AST 인식 청킹 | "함수 수준 분할" | 고정 토큰 윈도우가 아니라 tree-sitter 노드 경계에서 코드를 자르는 것 |
| 하이브리드 검색 | "dense + sparse" | BM25와 벡터 검색을 병렬로 돌리고 상위 k를 병합한 뒤 재순위화 |
| 크로스 인코더 재순위화 | "2단계 랭킹" | (질의, 후보) 쌍을 함께 넣고 점수를 매기는 모델. 코사인보다 정확 |
| 프롬프트 캐싱 | "캐시된 시스템 프롬프트" | 2026년 Claude / OpenAI 기능. 반복되는 접두 토큰 비용을 최대 90% 깎아줌 |
| 심볼 그래프 | "코드 그래프" | 파일과 저장소를 넘나드는 임포트·호출·상속 에지 |
| 인용 충실도 | "근거 답변율" | 앵커를 클릭해 참조된 범위를 읽으면 검증할 수 있는 주장의 비율 |
| 증분 재색인 | "푸시-검색 가능 시간" | git push부터 바뀐 심볼이 질의 가능해질 때까지의 실제 시간 |

## 더 읽을거리

- [Sourcegraph Amp](https://ampcode.com) — 프로덕션 교차 저장소 코드 인텔리전스
- [Sourcegraph Cody RAG 아키텍처](https://sourcegraph.com/blog/how-cody-understands-your-codebase) — 이 캡스톤의 참고용 심층 해설
- [Aider repo-map](https://aider.chat/docs/repomap.html) — tree-sitter 기반 순위 매긴 저장소 뷰
- [Augment Code 엔터프라이즈 그래프](https://www.augmentcode.com) — 상용 심볼 그래프 RAG
- [Qdrant 하이브리드 검색 문서](https://qdrant.tech/documentation/concepts/hybrid-queries/) — 참고 구현
- [Voyage AI 코드 임베딩](https://docs.voyageai.com/docs/embeddings) — Voyage-code-3 상세
- [Cohere rerank-3](https://docs.cohere.com/reference/rerank) — 크로스 인코더 레퍼런스
- [Pinterest MCP 내부 검색](https://medium.com/pinterest-engineering) — 내부 플랫폼 레퍼런스
