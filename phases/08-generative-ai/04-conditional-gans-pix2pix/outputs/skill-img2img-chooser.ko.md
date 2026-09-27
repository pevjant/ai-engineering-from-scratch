---
name: img2img-chooser
description: 페어 여부, 도메인 특수성, 지연 시간 예산을 고려해 이미지-이미지 접근 방식을 고릅니다.
version: 1.0.0
phase: 8
lesson: 04
tags: [pix2pix, img2img, conditional]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-img2img-chooser.md](skill-img2img-chooser.md)

과제 설명(소스 도메인, 타깃 도메인, 데이터 가용성 - 페어/비페어/샘플 수 N, 지연 시간 예산, 품질 기준)이 주어지면 다음을 출력합니다:

1. 접근 방식. Pix2Pix(페어, 좁은 도메인), Pix2PixHD(페어, 고해상도), CycleGAN(페어 없음), SPADE(세그멘테이션-이미지), 또는 SD3 / Flux.1 위의 ControlNet 변형(범용, 오픈 도메인).
2. 학습 데이터 스펙. 최소 페어 수, 해상도, 증강 기법, 라이선스 고려사항.
3. 아키텍처. G(U-Net 깊이, 채널 폭), D(PatchGAN 수용 영역, 스펙트럼 정규화), 손실 가중치(적대적, L1, VGG-지각).
4. 추론 지연 시간. 소비자용 GPU 한 장(RTX 4090, M3 Max) 기준 이미지당 목표 ms, 해상도 트레이드오프.
5. 평가. 홀드아웃 페어 데이터에 대한 LPIPS, 5k 샘플 FID, 과제별 지표(세그멘테이션 과제는 mIoU, 초해상도는 PSNR), 인간 선호도.

데이터가 페어가 아니면 Pix2Pix 추천을 거절합니다 - 대신 CycleGAN이나 ControlNet을 처방합니다. 증강 / 사전학습 조언 없이 500개 미만의 페어로 페어 모델을 학습시키자는 요청도 거절합니다. "임의 텍스트 프롬프트"를 언급하는 요청은 모두 표시합니다 - 이런 것에는 페어 GAN이 아니라 확산 + ControlNet이 필요합니다.
