---
name: document-ai-stack-picker
description: 도메인, 규모, 규제 요구에 따라 문서-AI 프로젝트에 OCR 파이프라인, OCR-free 전문 모델, VLM 네이티브 중 하나를 고릅니다.
version: 1.0.0
phase: 12
lesson: 22
tags: [document-ai, ocr, donut, nougat, paligemma, vlm-native]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-document-ai-stack-picker.md](skill-document-ai-stack-picker.md)

문서-AI 프로젝트(도메인: 청구서 / 학술 논문 / 양식 / 혼합; 규모: 일일 페이지 수; 품질 기준; 규제 요구)가 주어지면, 스택을 골라 참조 구성을 산출합니다.

산출물:

1. 스택 선택. 시대 1(OCR 파이프라인 + LayoutLMv3), 시대 2(Donut / Nougat OCR-free), 시대 3(VLM 네이티브), 또는 하이브리드.
2. 페이지당 비용 추정. 선택한 스택의 토큰 수와 지연 시간.
3. 정확도 기대치. DocVQA + ChartQA + 도메인 특화 벤치마크.
4. 손글씨 전략. 비용에 둔감하면 VLM 네이티브; 대규모라면 전용 TrOCR + 라우팅.
5. 수학 / LaTeX 출력. 학술 논문은 Nougat; 그 외는 VLM.
6. 규제 대체책. 교차 검증 감사 로그가 있는 하이브리드.

하드 리젝(무조건 거부):

- 비용 분석 없이 하루 100만 페이지 이상에 VLM 네이티브를 제안하는 것. 2576px 페이지당 토큰 비용이 상당합니다.
- 감사 경로 없이 규제 워크플로에 단일 모델 솔루션을 추천하는 것.
- Nougat이 스캔 청구서를 처리한다고 주장하는 것. 아닙니다 — 학술 논문 전문 모델입니다.

거부 규칙:

- 규모가 하루 1,000만 페이지를 넘으면 시대 3을 거부하고, 시대 3을 샘플링 검증기로 쓰는 시대 1을 추천합니다.
- 도메인이 손글씨 위주라면 OCR 파이프라인을 거부하고 VLM 네이티브 + 손글씨 전문 모델(TrOCR)을 추천합니다.
- 수식의 LaTeX 충실도가 필요하다면 파이프라인에 Nougat을 요구합니다.

출력: 스택, 비용, 정확도, 손글씨, 수학, 규제를 담은 한 페이지짜리 계획서. 마지막에 arXiv 2308.13418 (Nougat), 2204.08387 (LayoutLMv3), 2111.15664 (Donut)를 인용할 것.
