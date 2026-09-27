> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 페이즈 8: 생성형 AI

> 이미지, 비디오, 오디오, 3D 등을 만들어 냅니다.

## 이 페이즈를 GitHub에서 시작하기

**선수 지식:** 페이즈 2 ML 기초, 페이즈 3 딥러닝 핵심, 그리고
페이즈 7 레슨 14(트랜스포머 밑바닥부터 만들기).

**첫 레슨:** [생성 모델: 분류와 역사](01-generative-models-taxonomy-history/)

저장소 루트에서 다음 명령을 실행하세요:

```bash
python3 phases/08-generative-ai/01-generative-models-taxonomy-history/code/main.py
```

명령, 종료 코드, 밀도 추정치, 생성된 샘플, 그리고 암시적 생성기(implicit generator)가
`p(x)`에 대해 답할 수 없는 것을 설명하는 한 문장을 기록해 두세요.

**다음 행동:** 무작위 시드를 바꿔 밀도 추정치를 비교한 뒤,
[오토인코더와 VAE](02-autoencoders-vae/)로 계속 진행하세요.

[페이즈 8 전체 레슨 목록](../../README.md#phase-8)이나
[페이즈 간 로드맵](../../ROADMAP.md)을 둘러보세요.

레슨 15개, 총 약 15시간. 각 레슨은 상세 문서, 실행 가능한 Python 데모,
다이어그램, 그리고 여러분의 에이전트를 위한 이름 있는 스킬을 함께 제공합니다.

| # | 레슨 | 시간 |
|---|--------|------|
| 01 | [생성 모델: 분류와 역사](01-generative-models-taxonomy-history/) | ~45분 |
| 02 | [오토인코더 & VAE](02-autoencoders-vae/) | ~75분 |
| 03 | [GAN: 생성자 vs 판별자](03-gans-generator-discriminator/) | ~75분 |
| 04 | [조건부 GAN & Pix2Pix](04-conditional-gans-pix2pix/) | ~75분 |
| 05 | [StyleGAN](05-stylegan/) | ~45분 |
| 06 | [확산 모델: 밑바닥부터 만드는 DDPM](06-diffusion-ddpm-from-scratch/) | ~75분 |
| 07 | [잠재 확산 & Stable Diffusion](07-latent-diffusion-stable-diffusion/) | ~75분 |
| 08 | [ControlNet, LoRA & 조건화](08-controlnet-lora-conditioning/) | ~75분 |
| 09 | [인페인팅, 아웃페인팅 & 편집](09-inpainting-outpainting-editing/) | ~75분 |
| 10 | [비디오 생성](10-video-generation/) | ~45분 |
| 11 | [오디오 생성](11-audio-generation/) | ~45분 |
| 12 | [3D 생성](12-3d-generation/) | ~45분 |
| 13 | [플로우 매칭 & 정류 플로우](13-flow-matching-rectified-flows/) | ~45분 |
| 14 | [평가: FID, CLIP 점수, 인간 선호도](14-evaluation-fid-clip-score/) | ~45분 |
| 19 | [시각 자기회귀 모델링](19-visual-autoregressive-var/) | ~60분 |
