> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 04 — 멀티모달 문서 QA (비전 우선 PDF, 표, 차트)

> 2026년 문서 QA의 프론티어는 'OCR 먼저, 그다음 텍스트'에서 벗어나 비전 우선 늦은 상호작용(late interaction)으로 이동했습니다. ColPali, ColQwen2.5, ColQwen3-omni는 PDF 페이지 각각을 이미지로 다루고, 멀티 벡터 늦은 상호작용으로 임베딩하고, 질의가 패치에 직접 어텐션하게 합니다. 금융 10-K, 과학 논문, 손글씨 메모에서 이 패턴은 OCR 우선 방식을 큰 격차로 이깁니다. 1만 페이지에서 파이프라인을 끝까지 만들고, 'OCR 먼저, 그다음 텍스트'와의 나란히 비교를 내놓으세요.

**유형:** Capstone
**언어:** Python (파이프라인), TypeScript (뷰어 UI)
**선수 지식:** 페이즈 4 (컴퓨터 비전), 페이즈 5 (NLP), 페이즈 7 (트랜스포머), 페이즈 11 (LLM 엔지니어링), 페이즈 12 (멀티모달), 페이즈 17 (인프라)
**활용하는 페이즈:** P4 · P5 · P7 · P11 · P12 · P17
**시간:** 30시간

## 문제

기업들은 OCR 파이프라인이 엉망으로 만드는 PDF를 쌓아 두고 있습니다: 회전된 표가 있는 스캔 10-K, 수식으로 빼곡한 과학 논문, 이미지로 봐야만 이해되는 차트, 손글씨 주석. 이것들을 텍스트 우선으로 다루면 신호의 절반을 잃습니다. 2026년의 답은 날것 페이지 이미지 위의 늦은 상호작용 멀티 벡터 검색입니다. ColPali(Illuin Tech)가 도입했고, ColQwen2.5-v0.2와 ColQwen3-omni가 정확도를 밀어 올렸습니다. ViDoRe v3에서 비전 우선 검색은 'OCR 먼저, 그다음 텍스트'를 의미 있는 격차로 앞서며 — 차트, 표, 손글씨에서 격차는 더 벌어집니다.

트레이드오프는 저장소와 지연 시간입니다. ColQwen 임베딩은 페이지당 단일 1024차원 벡터가 아니라 약 2048개 패치 벡터입니다. 날것 저장소는 불어납니다. DocPruner(2026)는 측정 가능한 정확도 손실 없이 50% 가지치기를 가져옵니다. 당신은 1만 페이지를 색인하고, ViDoRe v3 nDCG@5를 측정하고, 2초 안에 답을 서빙하고, 'OCR 먼저, 그다음 텍스트' 베이스라인과 정면으로 비교하게 됩니다.

## 개념

늦은 상호작용(late interaction)은 모든 질의 토큰이 모든 패치 토큰과 점수를 매기고, 질의 토큰별 최대 점수를 합산하는 방식입니다. 하나의 풀링된 벡터 없이도 세밀한(fine-grained) 매칭을 얻습니다. 멀티 벡터 인덱스(Vespa, Qdrant 멀티 벡터, 또는 AstraDB)는 패치별 임베딩을 저장하고 검색 시점에 MaxSim을 돌립니다.

답변자는 질의와 상위 k 검색 페이지를 이미지로 받아 증거 영역(바운딩 박스나 페이지 참조)을 붙인 답을 쓰는 비전-언어 모델입니다. Qwen3-VL-30B, Gemini 2.5 Pro, InternVL3가 2026년 프론티어 선택지입니다. 수식과 과학 표기법에는 OCR 폴백(Nougat, dots.ocr)을 선택적 텍스트 채널로 접어 넣습니다.

평가는 2차원 행렬입니다. 한 축: 콘텐츠 유형(일반 텍스트 문단, 빽빽한 표, 막대/선 차트, 손글씨 메모, 수식). 다른 축: 검색 접근(비전 우선 늦은 상호작용 vs OCR-텍스트 vs 하이브리드). 각 칸에 nDCG@5와 답변 정확도를 매깁니다. 이 보고서가 산출물입니다.

## 아키텍처

```
PDFs -> page renderer (PyMuPDF, 180 DPI)
           |
           v
  ColQwen2.5-v0.2 embed (multi-vector per page, ~2048 patches)
           |
           +------> DocPruner 50% compression
           |
           v
   multi-vector index (Vespa or Qdrant multi-vector)
           |
query ----+----> retrieve top-k pages (MaxSim)
           |
           v
  VLM answerer: Qwen3-VL-30B | Gemini 2.5 Pro | InternVL3
    inputs: query + top-k page images + optional OCR text
           |
           v
  answer with cited page numbers + evidence regions
           |
           v
  Streamlit / Next.js viewer: highlighted boxes on source page
```

## 스택

- 페이지 렌더링: 180 DPI의 PyMuPDF (fitz), 세로 방향 정규화
- 늦은 상호작용 모델: ColQwen2.5-v0.2 또는 ColQwen3-omni (Hugging Face의 vidore 팀)
- 인덱스: 멀티 벡터 필드를 갖춘 Vespa, 또는 Qdrant 멀티 벡터, 또는 MaxSim을 지원하는 AstraDB
- 가지치기: DocPruner 2026 정책(고분산 패치 유지, 0.5% 미만 정확도 손실에서 50% 압축)
- OCR 폴백(수식 / 빽빽한 표): dots.ocr 또는 Nougat
- VLM 답변자: 셀프 호스팅 Qwen3-VL-30B 또는 호스티드 Gemini 2.5 Pro; 예비로 InternVL3
- 평가: ViDoRe v3 벤치마크, 다중 페이지 추론용 M3DocVQA
- 뷰어 UI: 증거 영역 캔버스 오버레이를 갖춘 Next.js 15

```figure
ce-late-interaction
```

## 만들기

1. **수집.** 10-K, 과학 논문, 스캔 문서에 걸친 1만 PDF 페이지 코퍼스를 순회합니다. 각 페이지를 1536x2048 PNG로 렌더링합니다. `{doc_id, page_num, image_path}`를 저장합니다.

2. **임베딩.** 각 페이지 이미지에 ColQwen2.5-v0.2를 돌립니다. 출력 형태는 차원 128의 패치 임베딩 약 2048개입니다. DocPruner를 적용해 신호가 가장 센 절반을 남깁니다. Vespa 멀티 벡터 필드나 Qdrant 멀티 벡터에 씁니다.

3. **질의.** 들어오는 질의마다 질의 타워로 임베딩합니다(토큰 수준 임베딩). 인덱스에 MaxSim을 돌립니다: 질의 토큰마다 페이지 패치 임베딩에 대한 최대 내적을 취해 합산합니다. 상위 k 페이지를 돌려줍니다.

4. **합성.** 질의와 상위 5페이지 이미지를 넣어 Qwen3-VL-30B를 호출합니다. 프롬프트: "제공된 페이지만 사용해 답하라. 각 주장을 (doc_id, page)로 인용하고 영역(그림, 표, 문단)을 밝혀라."

5. **증거 영역.** 답변을 후처리해 인용된 영역을 뽑아냅니다. VLM이 바운딩 박스를 내놓으면(Qwen3-VL이 그렇습니다) 뷰어에 오버레이로 그립니다.

6. **OCR 폴백.** 수식이 빽빽하다고 판정된 페이지(이미지 분산 휴리스틱)에는 Nougat이나 dots.ocr를 돌리고, OCR 텍스트를 이미지 옆 추가 채널로 넘깁니다.

7. **평가.** ViDoRe v3(검색 nDCG@5)와 M3DocVQA(다중 페이지 QA 정확도)를 돌립니다. 같은 코퍼스에 같은 합성기로 'OCR 먼저, 그다음 텍스트' 파이프라인도 돌립니다. 콘텐츠 유형 × 접근 행렬을 만듭니다.

8. **UI.** 먼저 Streamlit 프로토타입; 다음으로 페이지별 증거 영역 오버레이를 갖춘 Next.js 15 프로덕션 뷰어.

## 사용해 보기

```
$ doc-qa ask "what was the 2024 operating margin change for segment EMEA?"
[retrieve]   top-5 pages in 320ms (ColQwen2.5, MaxSim, Vespa)
[synth]      qwen3-vl-30b, 1.4s, cited (form-10k-2024, p. 88) + (..., p. 92)
answer:
  EMEA operating margin moved from 18.2% to 16.8%, a 140bp decline.
  cited: 10-K-2024.pdf p.88 (Table 4, Segment Operating Margin)
         10-K-2024.pdf p.92 (MD&A, Operating Performance)
[viewer]     open with highlighted bounding boxes overlaid on p.88 Table 4
```

## 출시하기

`outputs/skill-doc-qa.md`가 산출물을 설명합니다: 특정 코퍼스에 맞춰 튜닝하고 ViDoRe v3에서 'OCR 먼저, 그다음 텍스트' 베이스라인과 평가한, 비전 우선 멀티모달 문서 QA 시스템입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | ViDoRe v3 / M3DocVQA 정확도 | OCR-텍스트 베이스라인과 공개 리더보드 대비 벤치마크 수치 |
| 20 | 증거 영역 근거 | 인용된 영역 중 실제로 답변 범위를 담고 있는 비율 |
| 20 | 저장소와 지연 시간 엔지니어링 | DocPruner 압축 비율, 인덱스 p95, 답변 p95 |
| 20 | 다중 페이지 추론 | 손으로 라벨을 붙인 100질문 다중 페이지 세트 정확도 |
| 15 | 원본 검수 UX | 뷰어 명확성, 오버레이 충실도, 나란히 비교 도구 |
| **100** | | |

## 연습 문제

1. 같은 코퍼스에서 ColQwen2.5-v0.2와 ColQwen3-omni를 비교 측정하세요. 한쪽은 맞히고 다른 쪽이 놓치는 페이지는 어떤 것인가요? 유형별 라우팅을 위해 인덱스에 "content class" 태그를 추가하세요.

2. 임베딩을 공격적으로 가지치기하세요(75%, 90%). 압축 낭떠러지를 찾으세요: ViDoRe nDCG@5가 OCR 베이스라인 밑으로 떨어지는 지점.

3. 하이브리드를 만들어 보세요: OCR-텍스트와 ColQwen을 병렬로 돌리고, RRF로 융합하고, 크로스 인코더로 재순위화합니다. 하이브리드가 어느 하나보다 나은가요? 어디서 가장 도움이 되나요?

4. Qwen3-VL-30B를 더 작은 VLM(Qwen2.5-VL-7B)으로 바꿔 보세요. 달러당 정확도 곡선을 측정하세요.

5. 손글씨 메모 지원을 추가하세요. 손글씨 코퍼스를 렌더링하고 ColQwen으로 임베딩해 검색을 측정합니다. 손글씨 OCR 파이프라인과 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| 늦은 상호작용 | "ColPali 방식 검색" | 질의 토큰이 페이지 패치와 독립적으로 점수를 매기고, MaxSim이 합산 |
| 멀티 벡터 | "패치별 임베딩" | 문서마다 풀링된 벡터 하나가 아니라 여러 벡터가 있음 |
| MaxSim | "늦은 상호작용 점수" | 질의 토큰마다 문서 벡터에 대한 최대 유사도를 취해 합산 |
| DocPruner | "패치 압축" | 정확도 손실은 무시할 수준으로 두고 패치 50%를 남기는 2026년 가지치기 |
| ViDoRe v3 | "문서 검색 벤치마크" | 시각 문서 검색을 측정하는 2026년 표준 |
| 증거 영역 | "인용된 바운딩 박스" | 원본 페이지에서 답변 범위의 위치를 짚어 주는 bbox |
| OCR 폴백 | "수식 채널" | 수식이나 표가 많은 페이지를 위해 비전 옆에 쓰는 텍스트 파이프라인 |

## 더 읽을거리

- [ColPali (Illuin Tech) 저장소](https://github.com/illuin-tech/colpali) — 참고용 늦은 상호작용 문서 검색
- [ColPali 논문 (arXiv:2407.01449)](https://arxiv.org/abs/2407.01449) — 기초가 되는 방법론 논문
- [Hugging Face의 ColQwen 계열](https://huggingface.co/vidore) — 프로덕션 준비된 체크포인트
- [M3DocRAG (Adobe)](https://arxiv.org/abs/2411.04952) — 다중 페이지 멀티모달 RAG 베이스라인
- [Vespa 멀티 벡터 튜토리얼](https://docs.vespa.ai/en/colpali.html) — 참고용 서빙 스택
- [Qdrant 멀티 벡터 지원](https://qdrant.tech/documentation/concepts/vectors/#multivectors) — 대안 인덱스
- [AstraDB 멀티 벡터](https://docs.datastax.com/en/astra-db-serverless/databases/vector-search.html) — 대안 매니지드 인덱스
- [Nougat OCR](https://github.com/facebookresearch/nougat) — 수식을 다루는 OCR 폴백
