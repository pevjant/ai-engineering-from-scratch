---
name: tokenizer-vs-adapter-picker
description: VLM 프로젝트에서 Chameleon 스타일 얼리 퓨전(공유 어휘 토크나이저)과 LLaVA 스타일 레이트 퓨전(고정 LLM의 어댑터) 중 하나를 고른다.
version: 1.0.0
phase: 12
lesson: 11
tags: [chameleon, early-fusion, vq-vae, late-fusion, adapter]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-tokenizer-vs-adapter-picker.md](skill-tokenizer-vs-adapter-picker.md)

제품 사양(이해 전용 또는 이해 + 생성), 목표 이미지 품질(소셜 게시물 / 잡지 / 인쇄 / 방송), 비용 예산(학습 + 추론)이 주어지면, 구체적인 아키텍처 개요와 함께 Chameleon 계열 또는 LLaVA 계열을 권합니다.

산출물:

1. 판정. 얼리 퓨전(Chameleon / Emu3 / AnyGPT) 또는 레이트 퓨전(LLaVA / BLIP-2 / Qwen-VL) 계열.
2. 토크나이저 선택(얼리 퓨전 판정인 경우). VQ-VAE(Chameleon), MAGVIT-v2, IBQ, 또는 SBER-MoVQGAN; PSNR 기준 예상 재구성 천장을 인용.
3. 학습 안정성 계획. 대규모 얼리 퓨전을 위한 QK-Norm, 드롭아웃 배치, LayerNorm 순서.
4. 비용 추정. 레이트 퓨전 대안 대비 학습 GPU시간과 이미지당 추론 지연 시간.
5. 생성 품질 천장. 기대할 수 있는 PSNR / FID 범위; 제품의 품질 기준이 이산 토큰으로 도달 가능한지, 아니면 연속(Transfusion 스타일) 생성이 필요한지.
6. 마이그레이션 경로. 사용자가 성장해서 레이트 퓨전이 한계에 부딪히면(이미지 출력이 필요해지면), 마이그레이션이 어떤 모습인지.

하드 리젝(거절 사항):
- 이해 전용 제품에 Chameleon 스타일을 권하는 것. 순수 이해에는 레이트 퓨전이 더 단순하고, 저렴하고, 천장도 높습니다.
- 프로덕션 이미지 생성에 K<4096인 VQ-VAE를 제안하는 것. 코드북이 너무 작아 아티팩트가 보입니다.
- 얼리 퓨전 추론이 공짜라고 주장하는 것. VQ 디코더가 생성 이미지당 50-200ms를 추가하며, 종종 LLM 출력 시간보다 깁니다.

거절 규칙:
- 프런티어급 이미지 생성(FID < 15, 인쇄 준비 완료)을 원하면 이산 토큰은 거절하고 Transfusion / Stable Diffusion 3 / MMDiT(레슨 12.13)를 가리켜 주세요.
- 제품이 이미지 출력을 전혀 필요로 하지 않으면 얼리 퓨전은 거절 — 복잡도를 감낼 이유가 없습니다.
- 기존 Llama / Qwen LLM 가중치를 끼워 넣으려 하면 얼리 퓨전은 거절 — 새 모델 사전학습이 필요합니다.

출력: 판정, 토크나이저 선택, 안정성 체크리스트, 비용 추정, 품질 천장, 마이그레이션 경로가 담긴 한 페이지짜리 계획. 마지막에 비교 읽기용으로 arXiv 2405.09818 (Chameleon)과 2408.11039 (Transfusion)를 안내.
