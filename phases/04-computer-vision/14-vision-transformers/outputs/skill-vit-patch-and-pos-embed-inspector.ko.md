---
name: skill-vit-patch-and-pos-embed-inspector
description: ViT의 패치 임베딩과 위치 임베딩 모양이 모델이 기대하는 시퀀스 길이와 일치하는지 검증합니다
version: 1.0.0
phase: 4
lesson: 14
tags: [vision-transformer, debugging, pytorch]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-vit-patch-and-pos-embed-inspector.md](skill-vit-patch-and-pos-embed-inspector.md)

# ViT 패치 및 위치 임베딩 검사기

가장 흔한 ViT 포팅 버그는 이것입니다. 224x224로 사전 학습된 체크포인트를 384x384용으로 설정된 모델에 불러오는 경우(혹은 그 반대). 위치 임베딩의 시퀀스 길이가 어긋나고, 모델은 아무 소리 없이 쓰레기 같은 결과를 냅니다.

## 사용 시점

- 사전 학습된 ViT를 기본값이 아닌 해상도로 파인튜닝할 때.
- ViT-B/16과 ViT-B/32 사이의 가중치 포팅이 실패하는 원인을 점검할 때. 검사기가 패치 크기 불일치를 표시해 주므로, 호출자가 억지로 포팅하지 말고 아키텍처를 바꿔야 한다는 것을 알 수 있습니다.
- 오류 없이 불러와지는데 학습이 잘 안 되는 ViT를 디버깅할 때.

## 입력

- `model`: 인스턴스화된 ViT `nn.Module`.
- `expected_image_size`: 프로덕션(운영 환경)에서 모델이 보게 될 H x W.
- `patch_size`: 기대하는 패치 크기.

## 단계

1. 모델 안에서 패치 임베딩 합성곱을 찾습니다. `kernel_size`, `stride`, `in_channels`, `out_channels`를 보고합니다.
2. 기대되는 패치 수를 계산합니다. 정사각형 이미지: `(image_size / patch_size)^2`. 직사각형: `(H / patch_size) * (W / patch_size)`. `H % patch_size == 0`이고 `W % patch_size == 0`이어야 하며, 그렇지 않으면 표시하고 중단합니다.
3. 학습된 위치 임베딩을 찾습니다. 모양 `(1, N, dim)`을 보고합니다.
4. `N`을 `num_patches + 1`(CLS 포함) 또는 `num_patches`(CLS 없음)와 비교합니다. 불일치하면 체크포인트가 다른 해상도나 패치 크기로 사전 학습됐다는 뜻입니다.
5. 패치 합성곱의 `out_channels`가 위치 임베딩의 `dim`과 같은지 확인합니다.
6. 모델이 새 해상도에 맞게 위치 임베딩을 보간(interpolate)하기로 되어 있다면, 보간 유틸리티가 존재하는지 확인합니다(대부분의 `timm` ViT는 `resize_pos_embed`로 자동 처리합니다).

## 보고서

```
[vit-inspector]
  image_size:         HxW
  patch_size:         <정수>
  num_patches (computed): <정수>
  patch_conv:         k=<정수>  s=<정수>  in=<정수>  out=<정수>
  pos_embed shape:    (1, N, dim)
  has CLS token:      yes | no
  pos_embed N:        <정수>    expected: <정수>
  verdict:            ok | mismatch

[if mismatch]
  action:  새 시퀀스 길이에 맞게 pos_embed 재초기화
  tool:    timm.models.vision_transformer.resize_pos_embed
```

## 규칙

- 경고 없이 조용히 보간하지 않습니다. 사전 학습된 위치 구조가 어긋났을 수 있음을 사용자가 알 수 있도록 조치 내용을 드러냅니다.
- patch_size가 일치하지 않으면 보간을 추천하지 않고 거부합니다 — 올바른 아키텍처로 교체하세요.
- 모델을 직접 고치려 들지 않습니다. 보고하고 제안만 합니다.
