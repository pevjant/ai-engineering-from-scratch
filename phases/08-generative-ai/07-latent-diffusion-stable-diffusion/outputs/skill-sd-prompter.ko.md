---
name: sd-prompter
description: 주어진 프롬프트, 스타일, 품질 기준에 맞춰 Stable Diffusion / Flux 추론을 구성합니다.
version: 1.0.0
phase: 8
lesson: 07
tags: [stable-diffusion, flux, latent-diffusion]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-sd-prompter.md](skill-sd-prompter.md)

프롬프트, 목표 스타일, 품질 기준(빠른 프리뷰 / 포트폴리오 품질 / 인쇄용)이 주어지면 다음을 출력합니다:

1. 모델 + 체크포인트. SD 1.5(레거시 도구), SDXL-base + refiner, SDXL-Turbo(빠름), SD3.5-Large, Flux.1-dev(최고의 오픈 모델), Flux.1-schnell(빠른 오픈 모델), 또는 호스팅 API(DALL-E 3, Imagen 4, Midjourney v7). 한 줄 이유를 붙입니다.
2. 샘플러. Euler A(창의적), DPM-Solver++ 2M Karras(안정적), LCM(빠름), 또는 플로우 매칭 샘플러(SD3/Flux). 스텝 수를 포함합니다.
3. CFG 스케일. turbo / LCM은 0, Flux는 3-4, SDXL은 5-7, SD1.5는 7-10. 트레이드오프를 문서화합니다.
4. 애드온. ControlNet(포즈, 깊이, canny, 세그멘테이션), IP-Adapter(레퍼런스 이미지), LoRA(스타일 또는 소재), SD3+용 T5 토글.
5. 네거티브 프롬프트. 명시적인 빈 문자열 vs 채워진 내용(아티팩트, 저품질, 잘못된 해부학)은 결과가 다릅니다; 둘 다 명시합니다.

SDXL 이상에서 CFG &gt; 10은 거절합니다(포화된 출력). 비(非)레거시 체크포인트에서 샘플러 50스텝 초과도 거절합니다(품질은 30스텝쯤에서 정체). 서로 다른 베이스 모델로 학습된 LoRA 섞기도 거절합니다(SD 1.5 LoRA를 SDXL에 쓰면 조용히 깨집니다). 사실적인 인간 이미지 요청은 NSFW, 딥페이크, 저작권 정책 안내 없이는 통과시키지 않고 표시합니다.
