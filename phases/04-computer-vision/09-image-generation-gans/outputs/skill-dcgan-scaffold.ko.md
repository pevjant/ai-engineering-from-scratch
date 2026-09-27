---
name: skill-dcgan-scaffold
description: z_dim, image_size, num_channels만으로 학습 루프와 샘플 저장기까지 포함한 완전한 DCGAN 스캐폴드 작성
version: 1.0.0
phase: 4
lesson: 9
tags: [computer-vision, gan, dcgan, scaffolding]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-dcgan-scaffold.md](skill-dcgan-scaffold.md)

# DCGAN 스캐폴드

매개변수 세 개가 주어지면, 목표 이미지 해상도에 맞게 아키텍처 크기가 조정된 실행 가능한 DCGAN 프로젝트 뼈대를 만들어 냅니다.

## 언제 사용하나

- 작은 데이터셋으로 새 생성 실험을 시작할 때
- 동작하는 최소 예제로 DCGAN 기초를 가르칠 때
- 조건부 GAN을 프로토타이핑할 때(레이블 주입은 같은 스캐폴드 안에서 이뤄짐)

## 입력

- `image_size`: 32, 64, 128 중 하나(2의 거듭제곱이어야 함).
- `num_channels`: 1(그레이스케일) 또는 3(RGB).
- `z_dim`: 보통 64 또는 128.
- `with_spectral_norm`: yes | no, 기본값 yes.

## 아키텍처 크기 산정

G의 transposed conv 블록 수와 D의 스트라이드 conv 블록 수는 `image_size`에 따라 달라집니다:

| image_size | G 블록 | D 블록 |
|------------|----------|----------|
| 32         | 4        | 4        |
| 64         | 5        | 5        |
| 128        | 6        | 6        |

블록이 하나 추가될 때마다 공간 차원은 두 배(G) 또는 절반(D)이 됩니다. 특징 수는 32에서 시작해 `feat_base * 2^block_index`로 늘어납니다.

## 출력 파일

- `model.py` — Generator + Discriminator 클래스
- `train.py` — 학습 루프, 손실, 옵티마이저 설정
- `sample.py` — 샘플 그리드 저장기
- `config.json` — 하이퍼파라미터
- `README.md` — 10줄짜리 퀵스타트

## 보고

```
[scaffold]
  image_size:       <int>
  num_channels:     <int>
  z_dim:            <int>
  spectral_norm:    yes | no

[arch]
  G blocks:         <N>, channels: [list]
  D blocks:         <N>, channels: [list]
  G params (est):   <N>
  D params (est):   <N>

[training defaults]
  optimizer:   Adam(lr=2e-4, betas=(0.5, 0.999))
  batch_size:  64
  epochs:      50
  sample_every: 1 epoch

[files written]
  - model.py
  - train.py
  - sample.py
  - config.json
  - README.md
```

## 규칙

- G의 출력에는 항상 `nn.Tanh()`를 쓰고, 학습 중 데이터는 [-1, 1] 범위로 스케일합니다.
- D에는 항상 `LeakyReLU(0.2)`를 씁니다.
- `with_spectral_norm == yes`이면 D의 모든 conv를 `spectral_norm()`으로 감싸고 D에서 BatchNorm을 제거합니다. G의 BatchNorm은 유지합니다.
- image_size > 128인 스캐폴드는 절대 만들지 않습니다. 그 이상에서는 DCGAN이 불안정해집니다. 사용자에게 StyleGAN이나 디퓨전 모델을 안내하세요.
