# RAG를 위한 청킹 전략 (Chunking Strategies for RAG)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 청킹 설정은 임베딩 모델 선택만큼이나 검색 품질에 큰 영향을 미칩니다(Vectara, NAACL 2025). 청킹을 잘못하면 리랭킹(reranking)을 아무리 해도 소용이 없습니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 14(정보 검색), 페이즈 5 · 22(임베딩 모델)
**소요 시간:** 약 60분

## 문제 상황

50페이지짜리 계약서를 RAG 시스템에 넣었다고 해 봅시다. 사용자가 "해지 조항이 뭐야?"라고 물으면, 검색기는 표지를 돌려줍니다. 왜 그럴까요? 모델이 512토큰 크기의 청크로 학습되어 있는데, 해지 조항은 20페이지쯤 뒤에 있고, 페이지 나눔 지점에서 잘려 있으며, 질의와 연결해 줄 키워드도 주변에 없기 때문입니다.

해결책은 "더 좋은 임베딩 모델을 사자"가 아닙니다. 해결책은 청킹입니다. 얼마나 크게? 얼마나 겹치게(overlap)? 어디를 기준으로 자를까? 주변 맥락을 붙일까?

2026년 2월 벤치마크는 놀라운 결과를 보여 줍니다:

- Vectara의 2026년 연구: 재귀적(recursive) 512토큰 청킹이 시맨틱 청킹을 정확도 69% 대 54%로 이겼습니다.
- Natural Questions에서 SPLADE + Mistral-8B 조합: 오버랩(청크 겹침)은 측정 가능한 이득이 전혀 없었습니다.
- 컨텍스트 절벽(context cliff): 컨텍스트가 약 2,500토큰을 넘어서면 응답 품질이 급격히 떨어집니다.

"당연해 보이는" 답(시맨틱 청킹, 20% 오버랩, 1000토큰)은 자주 틀린 답입니다. 이 레슨에서는 여섯 가지 전략에 대한 감각을 기르고, 언제 어떤 전략을 써야 하는지 알려 드립니다.

## 개념

![하나의 문단에 여섯 가지 청킹 전략을 시각화](../assets/chunking.svg)

**고정 청킹(Fixed chunking).** N자 또는 N토큰마다 자릅니다. 가장 단순한 베이스라인입니다. 문장 중간에서 잘리기 쉽습니다. 압축률은 좋지만 문맥 일관성은 나쁩니다.

**재귀적 청킹(Recursive).** LangChain의 `RecursiveCharacterTextSplitter`입니다. 먼저 `\n\n`으로 나눠 보고, 안 되면 `\n`, 그다음 `.`, 마지막으로 공백 순서로 시도합니다. 깔끔하게 단계적으로 폴백(fallback)합니다. 2026년의 기본값입니다.

**시맨틱 청킹(Semantic).** 문장마다 임베딩을 만들고, 인접한 문장끼리 코사인 유사도를 계산합니다. 유사도가 임계값 아래로 떨어지는 지점에서 자릅니다. 주제 일관성은 잘 보존됩니다. 대신 느리고, 때로는 검색에 해가 되는 40토큰짜리 자잘한 조각이 만들어지기도 합니다.

**문장 단위 청킹(Sentence).** 문장 경계에서 자릅니다. 청크당 문장 하나이거나 N문장짜리 윈도우입니다. 비용은 훨씬 적게 들면서 약 5천 토큰까지는 시맨틱 청킹과 비슷한 성능을 냅니다.

**부모-문서 청킹(Parent-document).** 검색용 작은 자식 청크와 맥락 제공용 큰 부모 청크를 *둘 다* 저장합니다. 자식으로 검색하고, 부모를 돌려줍니다. 우아하게 성능이 저하됩니다: 자식 청크가 나빠도 그럭저럭 괜찮은 부모가 반환됩니다.

**레이트 청킹(Late chunking, 2024).** 문서 전체를 먼저 토큰 수준에서 임베딩한 다음, 토큰 임베딩을 풀링(pooling)해서 청크 임베딩을 만듭니다. 청크 사이의 문맥을 보존합니다. 롱 컨텍스트 임베더(BGE-M3, Jina v3)와 함께 동작합니다. 연산 비용은 더 큽니다.

**컨텍스추얼 검색(Contextual retrieval, Anthropic 2024).** 각 청크 앞에, 그 청크가 문서에서 어디에 있는지를 설명하는 LLM 생성 요약을 붙입니다("이 청크는 해지 조항 중 3.2절입니다..."). Anthropic 자체 벤치마크에서 검색 성능이 35~50% 향상됐습니다. 인덱싱 비용이 비쌉니다.

### 모든 기본값을 이기는 규칙

청크 크기를 질의 유형에 맞추세요:

| 질의 유형 | 청크 크기 |
|------------|-----------|
| 단순 사실형("CEO 이름이 뭐야?") | 256-512토큰 |
| 분석형 / 멀티홉(multi-hop) | 512-1024토큰 |
| 섹션 전체 이해 | 1024-2048토큰 |

NVIDIA의 2026년 벤치마크입니다. 청크는 정답과 그 주변 맥락을 담을 만큼은 충분히 커야 하고, 검색기의 top-K 결과가 맥락 노이즈가 아니라 정답에 집중할 만큼은 작아야 합니다.

```figure
n5-chunk-cuts
```

## 직접 만들기

### 단계 1: 고정 청킹과 재귀적 청킹

```python
def chunk_fixed(text, size=512, overlap=0):
    step = size - overlap
    return [text[i:i + size] for i in range(0, len(text), step)]


def chunk_recursive(text, size=512, seps=("\n\n", "\n", ". ", " ")):
    if len(text) <= size:
        return [text]
    for sep in seps:
        if sep not in text:
            continue
        parts = text.split(sep)
        chunks = []
        buf = ""
        for p in parts:
            if len(p) > size:
                if buf:
                    chunks.append(buf)
                    buf = ""
                chunks.extend(chunk_recursive(p, size=size, seps=seps[1:] or (" ",)))
                continue
            candidate = buf + sep + p if buf else p
            if len(candidate) <= size:
                buf = candidate
            else:
                if buf:
                    chunks.append(buf)
                buf = p
        if buf:
            chunks.append(buf)
        return [c for c in chunks if c.strip()]
    return chunk_fixed(text, size)
```

### 단계 2: 시맨틱 청킹

```python
def chunk_semantic(text, encoder, threshold=0.6, min_chars=200, max_chars=2048):
    sentences = split_sentences(text)
    if not sentences:
        return []
    embs = encoder.encode(sentences, normalize_embeddings=True)
    chunks = [[sentences[0]]]
    for i in range(1, len(sentences)):
        sim = float(embs[i] @ embs[i - 1])
        current_len = sum(len(s) for s in chunks[-1])
        if sim < threshold and current_len >= min_chars:
            chunks.append([sentences[i]])
        else:
            chunks[-1].append(sentences[i])

    result = []
    for group in chunks:
        text_group = " ".join(group)
        if len(text_group) > max_chars:
            result.extend(chunk_recursive(text_group, size=max_chars))
        else:
            result.append(text_group)
    return result
```

`threshold`는 여러분이 다루는 도메인에 맞게 조정하세요. 너무 높으면 조각나고, 너무 낮으면 청크 하나가 거대해집니다.

### 단계 3: 부모-문서 청킹

```python
def chunk_parent_child(text, parent_size=2048, child_size=256):
    parents = chunk_recursive(text, size=parent_size)
    mapping = []
    for p_idx, parent in enumerate(parents):
        children = chunk_recursive(parent, size=child_size)
        for child in children:
            mapping.append({"child": child, "parent_idx": p_idx, "parent": parent})
    return mapping


def retrieve_parent(child_query, mapping, encoder, top_k=3):
    child_embs = encoder.encode([m["child"] for m in mapping], normalize_embeddings=True)
    q_emb = encoder.encode([child_query], normalize_embeddings=True)[0]
    scores = child_embs @ q_emb
    top = np.argsort(-scores)[:top_k]
    seen, parents = set(), []
    for i in top:
        if mapping[i]["parent_idx"] not in seen:
            parents.append(mapping[i]["parent"])
            seen.add(mapping[i]["parent_idx"])
    return parents
```

핵심 통찰: 부모를 중복 제거(dedupe)해야 합니다. 여러 자식이 같은 부모를 가리킬 수 있는데, 전부 반환하면 컨텍스트가 낭비됩니다.

### 단계 4: 컨텍스추얼 검색(Anthropic 패턴)

```python
def contextualize_chunks(document, chunks, llm):
    context_prompts = [
        f"""<document>{document}</document>
Here is the chunk to situate: <chunk>{c}</chunk>
Write 50-100 words placing this chunk in the document's context."""
        for c in chunks
    ]
    contexts = llm.batch(context_prompts)
    return [f"{ctx}\n\n{c}" for ctx, c in zip(contexts, chunks)]
```

컨텍스트가 붙은 청크를 인덱싱하세요. 질의 시점에 검색이 주변 신호의 도움을 받습니다.

### 단계 5: 평가

```python
def recall_at_k(queries, corpus_chunks, encoder, k=5):
    chunk_embs = encoder.encode(corpus_chunks, normalize_embeddings=True)
    hits = 0
    for q_text, gold_idxs in queries:
        q_emb = encoder.encode([q_text], normalize_embeddings=True)[0]
        top = np.argsort(-(chunk_embs @ q_emb))[:k]
        if any(i in gold_idxs for i in top):
            hits += 1
    return hits / len(queries)
```

항상 벤치마크를 돌리세요. 여러분의 코퍼스에 "가장 좋은" 전략은 어느 블로그 글과도 다를 수 있습니다.

## 흔한 실수

- **단순 사실형(factoid) 질의로만 청킹을 평가하는 경우.** 멀티홉 질의에서는 승자가 완전히 달라집니다. 질의 유형별로 층을 나눈(stratified) 평가셋을 사용하세요.
- **최소 크기 없이 시맨틱 청킹을 쓰는 경우.** 검색에 해가 되는 40토큰짜리 조각이 생깁니다. 항상 `min_tokens`를 강제하세요.
- **습관처럼 오버랩을 넣는 경우.** 2026년 연구들은 오버랩이 종종 아무 이득도 없으면서 인덱스 비용만 두 배로 만든다는 것을 발견했습니다. 가정하지 말고 측정하세요.
- **최소/최대 크기를 강제하지 않는 경우.** 5토큰짜리 청크도 5000토큰짜리 청크도 검색을 망칩니다. 상하한(clamp)을 두세요.
- **문서 경계를 넘는 청킹.** 하나의 청크가 두 문서에 걸치게 두지 마세요. 항상 문서별로 잘라서, 그다음에 합치세요.

## 활용하기

2026년의 표준 스택:

| 상황 | 전략 |
|-----------|----------|
| 첫 빌드, 코퍼스 특성 불명 | 재귀적, 512토큰, 오버랩 없음 |
| 단순 사실형 QA | 재귀적, 256-512토큰 |
| 분석형 / 멀티홉 | 재귀적, 512-1024토큰 + 부모-문서 |
| 교차 참조가 많은 문서(계약서, 논문) | 레이트 청킹 또는 컨텍스추얼 검색 |
| 대화형 / 다이얼로그 코퍼스 | 턴(turn) 단위 청크 + 발화자 메타데이터 |
| 아주 짧은 텍스트(트윗, 리뷰) | 문서 1개 = 청크 1개 |

재귀적 512토큰으로 시작하세요. 50개 질의 평가셋에서 recall@5를 측정하고, 거기서부터 튜닝하세요.

## 출시하기

`outputs/skill-chunker.md`로 저장하세요:

```markdown
---
name: chunker
description: Pick a chunking strategy, size, and overlap for a given corpus and query distribution.
version: 1.0.0
phase: 5
lesson: 23
tags: [nlp, rag, chunking]
---

코퍼스 정보(문서 유형, 평균 길이, 도메인)와 질의 분포(단순 사실형 / 분석형 / 멀티홉)가 주어지면 다음을 출력합니다:

1. 전략. Recursive / sentence / semantic / parent-document / late / contextual 중 선택. 근거를 제시합니다.
2. 청크 크기. 토큰 수. 질의 유형에 근거를 둡니다.
3. 오버랩. 기본값 0; 0보다 크면 근거를 제시합니다.
4. 최소/최대 강제. `min_tokens`, `max_tokens` 가드.
5. 평가 계획. 50개 질의 층화 평가셋(단순 사실형, 분석형, 멀티홉)에서 recall@5 측정.

최소/최대 청크 크기 강제가 없는 청킹 전략은 거부합니다. 도움이 된다는 소거 실험(ablation) 없이 20%를 넘는 오버랩은 거부합니다. 최소 토큰 하한 없이 시맨틱 청킹을 추천하면 경고를 표시합니다.
```

## 연습 문제

1. **쉬움.** 20페이지짜리 문서 하나를 fixed(512, 0), recursive(512, 0), recursive(512, 100)로 잘라 보세요. 청크 개수와 경계 품질을 비교하세요.
2. **보통.** 문서 5개에 대해 30개 질의 평가셋을 만드세요. recursive, semantic, parent-document의 recall@5를 측정하세요. 무엇이 이기나요? 블로그 글의 주장과 일치하나요?
3. **어려움.** 컨텍스추얼 검색을 구현하세요. 베이스라인인 recursive 대비 MRR 향상을 측정하고, 인덱스 비용(LLM 호출 횟수) 대 정확도 이득을 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| 청크(Chunk) | 문서의 한 조각 | 임베딩하고, 인덱싱하고, 검색하는 문서 하위 단위. |
| 오버랩(Overlap) | 안전 여유분 | 인접 청크가 공유하는 N토큰; 2026년 벤치마크에서는 종종 무용지물. |
| 시맨틱 청킹 | 똑똑한 청킹 | 인접 문장 임베딩 유사도가 떨어지는 지점에서 자름. |
| 부모-문서 | 2단계 검색 | 작은 자식으로 검색하고, 더 큰 부모를 반환. |
| 레이트 청킹 | 임베딩 후에 자르기 | 문서 전체를 토큰 수준에서 임베딩한 뒤 청크 벡터로 풀링. |
| 컨텍스추얼 검색 | Anthropic의 비법 | 인덱싱 전에 각 청크 앞에 LLM 생성 요약을 붙임. |
| 컨텍스트 절벽 | 2500토큰의 벽 | RAG에서 컨텍스트 약 2.5천 토큰 지점에서 관찰되는 품질 저하(2026년 1월). |

## 더 읽을거리

- [Yepes et al. / LangChain — Recursive Character Splitting 문서](https://python.langchain.com/docs/how_to/recursive_text_splitter/) — 프로덕션(운영 환경)의 기본값.
- [Vectara (2024, NAACL 2025). Chunking configurations analysis](https://arxiv.org/abs/2410.13070) — 청킹이 임베딩 선택만큼 중요하다는 연구.
- [Jina AI — Late Chunking in Long-Context Embedding Models (2024)](https://jina.ai/news/late-chunking-in-long-context-embedding-models/) — 레이트 청킹 원 논문.
- [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) — LLM 생성 컨텍스트 접두어로 검색 성능 35~50% 향상.
- [NVIDIA 2026 chunk-size benchmark — Premai 요약](https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/) — 질의 유형별 청크 크기.
