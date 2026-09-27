---
name: vision-rag-designer
description: ColPali / ColQwen2 / VisRAG로 비전 네이티브 문서 RAG를 설계하고, 저장 추정과 생성기 선택을 포함합니다.
version: 1.0.0
phase: 12
lesson: 23
tags: [colpali, colqwen2, visrag, late-interaction, vidore]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-vision-rag-designer.md](skill-vision-rag-designer.md)

문서 RAG 프로젝트(코퍼스 크기, 질의 지연 시간 목표, 저장 예산, 질의당 비용)가 주어지면, 비전 네이티브 RAG 구성을 산출합니다.

산출물:

1. 검색기 선택. ColPali(PaliGemma 베이스), ColQwen2(Qwen2-VL 베이스, 더 나은 품질), ColSmol(엣지용 1B), 또는 VisRAG(바이 인코더, 저장이 저렴).
2. 저장 추정. N_docs * N_p_per_doc * D * 4바이트 원본; PQ면 8로 나눔.
3. 지연 시간 추정.
   - 검색 SLA: 질의 임베딩 ~10ms + 상위 k 검색(MaxSim 또는 ANN), 인덱스 크기에 따라 다름.
   - 전체 답변 SLA: 검색 지연 + 200~500ms 생성기(모델과 하드웨어에 따라 다름).
4. 생성기 선택. 오픈은 Qwen2.5-VL-72B, 프런티어는 Claude Opus 4.7.
5. 압축 계획. PQ / OPQ 비율 목표 8~16배; 빠른 ANN용 HNSW 인덱스.
6. 텍스트-RAG에서의 전환 경로. A/B 방법, 전면 전환 시점.

하드 리젝(무조건 거부):

- 1만 페이지를 넘는 코퍼스에 PQ 압축 없이 ColPali를 쓰는 것. 저장이 폭발합니다.
- 문서 회상에서 바이 인코더 검색이 ColBERT MaxSim과 맞먹는다고 주장하는 것. ViDoRe에서는 아닙니다.
- 차트 + 표 워크로드에 텍스트-RAG를 추천하는 것. 텍스트-RAG는 대부분의 신호를 잃습니다.

거부 규칙:

- 코퍼스가 순수 텍스트(위키, 채팅 로그)라면 비전 네이티브 RAG를 거부하고 표준 텍스트-RAG를 추천합니다.
- 검색 SLA가 100ms 미만이라면 ColPali MaxSim보다 VisRAG(바이 인코더)를 선호합니다.
- 전체 답변 SLA가 100ms 미만이라면 생성형 RAG 전체를 거부하고 검색 전용 UX 또는 캐시된 답변을 추천합니다.
- 저장 예산이 1GB 미만이고 코퍼스가 10만 페이지를 넘는다면 풀 충실도 ColPali를 거부; 공격적인 PQ 또는 VisRAG를 제안합니다.

출력: 검색기 선택, 저장 추정, 지연 시간, 생성기, 압축, 전환 경로를 담은 한 페이지짜리 RAG 설계서. 마지막에 arXiv 2407.01449 (ColPali), 2410.10594 (VisRAG)를 인용할 것.
