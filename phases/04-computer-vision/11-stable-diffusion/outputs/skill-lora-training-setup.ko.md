---
name: skill-lora-training-setup
description: 캡션, 랭크, 배치 크기, 학습률을 포함한 LoRA 학습 설정 전체를 커스텀 데이터셋에 맞게 작성
version: 1.0.0
phase: 4
lesson: 11
tags: [computer-vision, stable-diffusion, lora, fine-tuning]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-lora-training-setup.md](skill-lora-training-setup.md)

# LoRA 학습 설정

파인튜닝 의도에 대한 설명을 `diffusers`나 `kohya_ss`에 바로 넘길 수 있는 구체적인 학습 설정으로 바꿔 줍니다.

## 언제 사용하나

- 대상(인물, 물건, 캐릭터), 스타일(작가, 브랜드), 개념(포즈, 조명)용 LoRA를 학습할 때
- 기존 LoRA에 데이터를 더해 확장할 때
- 출력이 학습 이미지에 과소적합하거나 과적합하는 LoRA 실행을 디버깅할 때

## 입력

- `purpose`: subject | style | concept
- `num_images`: 학습 이미지가 몇 장 있는지
- `base_model`: SD 1.5 | SDXL | SD3 | FLUX
- `gpu_vram_gb`: 8 | 12 | 16 | 24 | 48+
- `caption_source`: manual | BLIP2-generated | dataset-native

## 랭크 선택

| 용도 | 랭크 | 알파 |
|---------|------|-------|
| Subject | 8-16 | rank |
| Style | 16-32 | rank * 2 |
| Concept | 32-64 | rank |

랭크가 높을수록 용량이 커지고, 작은 데이터셋에서 과적합 위험도 커집니다. 알파는 LoRA 효과의 세기를 조절하며, `alpha == rank`가 안전한 기본값입니다. 스타일이 문서화된 예외입니다. `alpha == rank * 2`는 스타일을 더 강하게 밀어 주지만 스타일이 지나치게 굳어질 위험도 커집니다. 대상 충실도가 목표가 아닐 때만 사용하세요.

## 학습 스텝 목표

- 이미지 5-20장의 `subject`: 500-1500단계.
- 이미지 30-100장의 `style`: 1500-4000단계.
- 이미지 100장 이상의 `concept`: 4000-10000단계.

초과하는 건 자기 책임입니다. 학습 이미지를 통째로 외워버린 LoRA는 일반화하지 못합니다.

## 학습률

- 텍스트 인코더 LoRA: SD 1.5는 `1e-4`, SDXL은 `5e-5`.
- U-Net LoRA: SD 1.5는 `1e-4`, SDXL은 `1e-4`.
- FLUX / SD3: 트랜스포머는 `5e-5`, 텍스트 인코더는 보통 얼려 둠.
- `num_images < 15`(subject)이거나 3000단계를 넘게 학습할 때는 학습률을 절반으로. 작은 데이터셋과 긴 실행은 모두 더 부드러운 갱신이 이롭습니다.

## 스케줄러

- `cosine_with_warmup`(기본값): 처음 5-10%의 단계에서 워밍업한 뒤 코사인 감쇠. `steps >= 1000`일 때 사용하세요. 감쇠 꼬리가 마지막 샘플을 더 선명하게 만들어 줍니다.
- `constant`: 아주 짧은 실행(`steps < 500`)이나, 재어닐링 없이 현재 학습된 특징을 유지하며 이전 LoRA를 이어갈 때만 사용하세요.

## 캡션 형식

- Subject: 모든 캡션 앞에 고유한 트리거 토큰("myperson")을 붙입니다. 트리거 토큰은 희귀하게 유지해야 기존 개념을 덮어쓰지 않습니다. 실제 단어와 흔한 이름은 피하세요.
- Style: 모든 캡션 끝에 고유한 스타일 태그를 붙입니다("...in mystyle style"). 태그 자체를 희귀 트리거 토큰으로 다루세요. `impressionism`처럼 이미 실제 개념에 대응되는 단어가 아니라 `mystyle` 같은 것이어야 합니다.
- Concept: 모든 캡션에 개념을 설명합니다. 트리거 토큰은 없습니다. 개념 자체(예: "low-angle shot")가 앵커입니다.

## 출력 설정

```yaml
model:
  base: <base_model HF id>
  precision: fp16 | bf16

lora:
  rank: <int>
  alpha: <int>
  targets: unet.cross_attention  # unet.to_q, to_k, to_v, to_out도 가능

training:
  steps:          <int>
  batch_size:     <int, gpu_vram_gb에 맞게 조정>
  grad_accum:     <int, 보통 16GB 이상이면 1, 12GB 이하면 4>
  learning_rate:  <float>
  optimizer:      AdamW8bit | AdamW
  scheduler:      cosine_with_warmup | constant
  warmup_steps:   <int>
  save_every:     <int>

data:
  images_dir:     <path>
  caption_source: <manual | BLIP2 | native>
  trigger_token:   <purpose==subject이면 문자열>
  resolution:      <SD 1.5는 512, SDXL은 1024>
  aspect_ratio_bucketing: true
  augmentation:
    flip:          true
    color_jitter:  false

validation:
  prompts:
    - "<trigger> ...test prompt..."
    - "<trigger> in a different scene"
  every_steps: 250
```

## 보고

```
[lora setup]
  purpose:   <subject|style|concept>
  base:      <model>
  rank:      <int>
  steps:     <int>
  batch:     <int>   grad_accum: <int>
  lr:        <float>
  vram est.: <float> GB
```

## 규칙

- `rank > 64`는 절대 권하지 마세요. 그 이상은 LoRA가 미니 파인튜닝이 되어버려 "어댑터"라는 본질을 잃습니다.
- `num_images < 5`면 강하게 경고하세요. 이미지 1-3장의 정체성(identity) LoRA는 매번 과적합됩니다.
- `gpu_vram_gb < 12`면 AdamW8bit과 그래디언트 체크포인팅을 필수로 요구하세요.
- `base_model == FLUX`이고 `gpu_vram_gb < 24`면 `schnell` 변형으로 안내하고 학습이 더 느리다는 점을 알리세요.
- 검증 프롬프트는 절대 건너뛰지 마세요. 샘플 그리드가 없는 LoRA는 평가할 방법이 없습니다.
