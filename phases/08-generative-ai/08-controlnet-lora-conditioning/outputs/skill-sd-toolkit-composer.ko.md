---
name: sd-toolkit-composer
description: 주어진 입력 세트에 맞춰 SD / Flux 베이스 위에 ControlNet, LoRA, IP-Adapter를 조합합니다.
version: 1.0.0
phase: 8
lesson: 08
tags: [controlnet, lora, ip-adapter, diffusion]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-sd-toolkit-composer.md](skill-sd-toolkit-composer.md)

과제(목표 이미지), 입력(프롬프트, 레퍼런스 이미지, 포즈 / 깊이 / 낙서 / 세그멘테이션, 소재 신원), 베이스 모델(SDXL, SD3.5, Flux.1-dev)이 주어지면 다음을 출력합니다:

1. ControlNet 스택. 어떤 ControlNet(canny / openpose / depth / scribble / seg / lineart / tile)을, 어떤 가중치로, 어떤 순서로. 가중치 합 최대 &lt;= 1.5.
2. LoRA 스택. 이름이 붙은 LoRA들, 계수, 알파. 알파 &gt; 1.5이거나 여러 LoRA가 같은 개념을 겨냥할 때 경고합니다.
3. IP-Adapter. 없음, 기본형, 또는 FaceID 변형; 가중치는 보통 0.4-0.8.
4. 텍스트 프롬프트 + 네거티브 프롬프트. 키워드 순서, 토큰 예산, 네거티브 뼈대.
5. 샘플러 + CFG + 시드. Euler A / DPM-Solver++ / LCM; CFG 스케일은 베이스에 맞춥니다. 재현 가능한 시드 프로토콜.
6. QA 체크리스트. ControlNet 표류, LoRA 과포화, IP-Adapter 신원 누출, 해부학 문제의 육안 검사.

SD 1.5 LoRA를 SDXL 베이스 위에 쌓는 것(차원 불일치)은 거절합니다. 가중치 1.0짜리 ControlNet 3개 이상 실행도 거절합니다(특성 충돌). 사용자가 SDXL이나 Flux를 쓸 GPU 예산이 있는데 SD 1.5를 추천하는 것은 표시합니다. 이미지 10장 미만으로 LoRA 신원 학습을 하면 과적합되기 쉽다고 표시합니다.
