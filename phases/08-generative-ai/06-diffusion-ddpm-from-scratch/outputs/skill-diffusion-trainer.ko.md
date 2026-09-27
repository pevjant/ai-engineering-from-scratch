---
name: diffusion-trainer
description: 확산 학습 런을 구성합니다: 스케줄, 예측 타깃, 샘플러, 평가 계획.
version: 1.0.0
phase: 8
lesson: 06
tags: [diffusion, ddpm, training]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-diffusion-trainer.md](skill-diffusion-trainer.md)

데이터셋 프로필(모달리티, 해상도, 데이터셋 크기), 계산 예산(GPU 시간, VRAM 하한), 품질 기준(FID 목표 또는 다운스트림 용도)이 주어지면 다음을 출력합니다:

1. 스케줄. 선형, 코사인(Nichol), 또는 시그모이드. 스텝 수 T(DDPM 베이스라인은 1000; 더 빠른 변형은 256).
2. 예측 타깃. epsilon, v-예측, 또는 x_0. 해상도와 스케줄 전반의 신호 대 잡음비에 근거한 이유를 붙입니다.
3. 아키텍처. 픽셀 확산에는 U-Net 깊이 + 채널 폭, 잠재 확산에는 DiT, 비디오에는 3D U-Net / DiT. 시간 임베딩 방식(사인파 + MLP, FiLM, 또는 AdaLN)을 포함합니다.
4. 샘플러. DDIM(20-50스텝), DPM-Solver++(10-20), Euler-A(창의적), 또는 증류된 1-4스텝. 가이던스 스케일(CFG w) 추천을 포함합니다.
5. 평가 계획. FID / KID / CLIP-score / 인간 선호도, 샘플 수(FID는 10k 이상), CFG w 스윕 프로토콜을 함께 제시합니다.

잠재 확산이 1/16 FLOPs로 같은 품질을 내는 데도 256x256 이상 픽셀 공간 확산 학습을 추천하는 일은 없습니다. 조건부 생성 모델에 CFG 없이 출시하자는 제안도 거절합니다 - 조건부 모델의 제로샷 무조건부 샘플은 보통 퇴화되어 있습니다. beta_T &gt; 0.1인 스케줄은 포화되거나 불안정한 학습을 일으키기 쉽다고 표시합니다.
