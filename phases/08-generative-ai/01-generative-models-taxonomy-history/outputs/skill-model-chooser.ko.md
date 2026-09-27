---
name: generative-model-chooser
description: 주어진 과제와 예산에 대해 생성 모델 계열, 백본, 호스팅형 대안을 고릅니다.
version: 1.0.0
phase: 8
lesson: 01
tags: [generative, taxonomy]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-model-chooser.md](skill-model-chooser.md)

과제 설명(모달리티, 도메인, 지연 시간 예산, 연산 예산, 조건화 신호)이 주어지면 다음을 출력합니다:

1. 계열. 명시적-계산가능, 명시적-근사(VAE / 확산), 암시적(GAN), 점수 / 플로우 매칭, 또는 토큰-AR. 모달리티 + 지연 시간과 연결 지은 한 문장 분량의 근거를 붙입니다.
2. 백본 + 오픈 레퍼런스. 사용자가 오늘 바로 파인튜닝할 수 있는 사전학습 오픈 웨이트 모델 하나(예: Stable Diffusion 3, Flux.1-dev, AudioCraft 2, StyleGAN3, 3D Gaussian Splatting).
3. 호스팅형 대안. 품질 / 비용 / 지연 시간 트레이드오프 기준으로 순위를 매긴 프로덕션 API 세 개(fal.ai, Replicate, Stability, Runway, Veo, Kling, ElevenLabs 등).
4. 실패 모드. 선택한 계열의 알려진 병리(모드 붕괴, 노출 편향(exposure bias), 샘플러 표류, 토크나이저 아티팩트, CLIP 점수 부정행위).
5. 예산. A100 한 대 기준 대략적인 학습 시간, 샘플당 추론 비용, 최소 VRAM.

과제가 우도 점수 계산을 요구하는데 GAN을 추천하는 일은 없습니다. 고해상도 실시간 용도에 픽셀 위의 자기회귀를 추천하는 일은 없습니다. 나열된 오픈 백본이 이미 그 도메인을 커버하는데 '처음부터 학습'을 추천하는 경우는 표시합니다.
