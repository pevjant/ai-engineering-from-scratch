---
name: unified-gen-model-picker
description: 멀티모달 이해와 생성을 모두 필요로 하고 오픈 웨이트 제약이 있는 제품에 Show-o / Transfusion / Emu3 / Janus-Pro 계열 중 하나를 고른다.
version: 1.0.0
phase: 12
lesson: 14
tags: [show-o, masked-diffusion, unified, t2i, inpainting]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-unified-gen-model-picker.md](skill-unified-gen-model-picker.md)

통합 이해 + 생성(VQA, 캡셔닝, T2I, 선택적으로 인페인팅)이 필요하고, 오픈 웨이트 제약과 지연 시간 예산이 있는 제품이 주어지면, 모델 계열을 골라 참조 설정을 내놓습니다.

산출물:

1. 계열 판정. Show-o(마스크 이산 확산), Transfusion / MMDiT(연속 확산), Emu3 / Chameleon(자기회귀 이산), 또는 Janus-Pro(분리 인코더).
2. 추론 스텝 예산. Show-o는 16, Transfusion은 20, Emu3는 1024+. 사용자의 지연 시간 예산으로 선택을 정당화한다.
3. 인페인팅 지원. Show-o는 공짜; Transfusion은 마스크 채널 추가; Emu3는 별도 파인튜닝 필요. 이 점을 사용자에게 표시한다.
4. 토크나이저 선택. 이산 계열에는 IBQ / MAGVIT-v2 / SBER 권장; 연속 계열에는 SD3의 VAE 권장.
5. 학습 안정성. 두-손실(Transfusion)은 가중치 튜닝 필요; Show-o의 단일 손실이 더 깔끔하다.
6. 성장 시 마이그레이션 경로. 품질이 한계가 되면 Show-o에서 Transfusion으로.

하드 리젝(거절 사항):
- 이미지당 추론 지연 시간이 10초 미만인데 Emu3 / Chameleon을 제안하는 것. 약 1024토큰 위의 자기회귀는 너무 느립니다.
- Show-o가 프런티어 이미지 품질에서 Transfusion에 필적한다고 주장하는 것. 그렇지 않습니다. 천장은 토크나이저입니다.
- VQA가 필요한 제품에 Stable Diffusion을 권하는 것. SD는 이미지에 대해 추론하지 못합니다.

거절 규칙:
- 이미지 생성이 2초 미만이어야 하면 Show-o를 거절하고, Stable Diffusion + 이해용 별도 VLM을 권하세요. 다중 모델 복잡도는 감수하는 걸로.
- 오픈 웨이트로 "최고 수준 품질"을 원하면 Show-o / Emu3를 거절하고 Transfusion 계열(MMDiT)이나 JanusFlow를 권하세요.
- 토크나이저 확정이 불가능하면(라이선스 우려, 품질 천장) 이산 전용 계열을 거절하고 Transfusion을 권하세요.

출력: 계열 판정, 스텝 예산, 인페인팅 지원, 토크나이저 권장, 안정성 계획, 마이그레이션 경로가 담긴 한 페이지짜리 선택 보고서. 마지막에 arXiv 2408.12528 (Show-o), 2408.11039 (Transfusion), 2501.17811 (Janus-Pro)을 안내.
