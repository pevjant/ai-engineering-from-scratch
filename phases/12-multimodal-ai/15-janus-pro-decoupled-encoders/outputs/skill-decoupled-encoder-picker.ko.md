---
name: decoupled-encoder-picker
description: 통합 VLM이 시각 인코더를 분리할지 판단하고 Janus-Pro, JanusFlow, InternVL-U 중 하나를 고릅니다.
version: 1.0.0
phase: 12
lesson: 15
tags: [janus-pro, janusflow, internvl-u, decoupled-encoders, unified-model]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-decoupled-encoder-picker.md](skill-decoupled-encoder-picker.md)

통합 모델 사양(이해 + 생성, 선택적으로 편집 / 인페인팅), 컴퓨트 예산, 오픈 웨이트 제약이 주어지면, 분리형 인코더 아키텍처와 구체적인 구성을 추천합니다.

산출물:

1. 아키텍처 선택. Janus-Pro(VQ 생성), JanusFlow(정정 흐름 생성), InternVL-U(네이티브 사전학습 + 분리형) 중 하나.
2. 인코더 조합. 이해에는 SigLIP-SO400m; 이산 생성에는 MAGVIT-v2 / IBQ VQ; 연속 생성에는 SD3 스타일 VAE.
3. 데이터 단계 계획. 1단계 정렬(5천만~1억 쌍), 2단계 통합(7천만 쌍 이상), 3단계 지시문(100만 샘플 이상). Janus-Pro의 5.4배 모델 + 2.8배 데이터 스케일링 결과를 인용할 것.
4. 라우팅 전략. 프롬프트 태그 기반(명시적 `<understand>` / `<generate>`) 또는 작업 분류기 기반.
5. 공유 본체 초기화. 밑바닥부터가 아니라 사전학습된 LLM(DeepSeek, Qwen, Llama)으로 초기화.
6. 품질 상한. 기대치 MMMU(7B에서 ~60)와 GenEval(7B 기준 Janus-Pro ~0.80 / InternVL-U ~0.85+).

하드 리젝(무조건 거부):

- 양쪽 모두에서 프런티어 경쟁력 있는 품질을 요구하는데 단일 인코더 통합 모델(Show-o / Transfusion)을 제안하는 것. 분리형 접근이 유일한 길입니다.
- 10B 미만 모델에 밑바닥부터의 사전학습을 권하는 것. 사전학습된 LLM 본체를 재사용하세요.
- 새 프로젝트에 Janus-Pro 대신 Janus(원조)를 제안하는 것. Janus-Pro가 후속작입니다.

거부 규칙:

- 이해만 필요하다면 분리형을 거부하고 LLaVA 계열을 추천합니다. 인코더 하나로 충분합니다.
- 생성만 필요하다면 거부하고 Stable Diffusion 3 / Flux를 추천합니다 — T2I 품질에서는 여전히 전문 모델이 이깁니다.
- 컴퓨트가 5만 GPU시간 미만이라면 InternVL-U를 거부(네이티브 사전학습 필요)하고 Janus-Pro를 추천합니다(사전학습 LLM 재사용).

출력: 아키텍처 선택, 인코더 조합, 단계 계획, 라우팅, 공유 본체 초기화, 품질 상한을 담은 한 페이지짜리 계획서. 마지막에 arXiv 2501.17811 (Janus-Pro), 2411.07975 (JanusFlow), 2603.09877 (InternVL-U)를 인용할 것.
