---
name: stylegan-inversion
description: 사전학습된 StyleGAN에 대해 실제 사진의 인버션 및 편집 파이프라인을 선택합니다.
version: 1.0.0
phase: 8
lesson: 05
tags: [stylegan, inversion, editing]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-stylegan-inversion.md](skill-stylegan-inversion.md)

실제 사진 + 사전학습 StyleGAN 체크포인트(FFHQ-1024, StyleGAN-XL, 커스텀 파인튜닝)와 목표 편집(나이, 미소, 포즈, 머리카락, 신원 보존)이 주어지면 다음을 출력합니다:

1. 인버션 방법. e4e(빠름, 충실도 낮음), ReStyle(반복 인코더), HyperStyle(하이퍼넷), PTI(pivotal tuning), 또는 직접 W 최적화. 충실도 vs 속도에 근거한 한 줄 이유를 붙입니다.
2. 타깃 공간. W, W+, 또는 StyleSpace. 트레이드오프: W = 가장 잘 분리되지만 충실도가 가장 낮음, W+ = 레이어별 w, StyleSpace = 채널 수준.
3. 편집 방향. 이름이 붙은 방향의 출처: InterFaceGAN(SVM 기반), StyleSpace 채널, GANSpace PCA, 또는 학습된 분류기.
4. 충실도 예산. 신원이 흐트러지기 전까지의 LPIPS 임계값; 롤백 휴리스틱.
5. 평가. ID 유사도(ArcFace 코사인), 원본 대비 LPIPS, 편집 강도(목표 속성 분류기 점수).

Z 공간에서 직접 편집하는(얽혀 있는) 파이프라인은 거절합니다. 신원 검사 없이 큰 편집(W에서 &gt;1.5 시그마)도 거절합니다. 오픈 도메인 편집이 필요한 요청(예: "그를 만화 캐릭터로 바꿔 줘")은 표시합니다 - 이런 것에는 StyleGAN이 아니라 확산 + IP-Adapter가 필요합니다.
