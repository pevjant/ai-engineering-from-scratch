---
name: skill-residual-block-reviewer
description: PyTorch 잔차 블록을 스킵 연결 정합성, BN 위치, 활성화 순서, shape 정렬 관점에서 리뷰
version: 1.0.0
phase: 4
lesson: 3
tags: [computer-vision, resnet, code-review, pytorch]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-residual-block-reviewer.md](skill-residual-block-reviewer.md)

# 잔차 블록 리뷰어 (Residual Block Reviewer)

잔차 블록을 구현했다고 주장하는 모든 PyTorch `nn.Module`을 위한 집중 리뷰어입니다. 깨진 ResNet 재작성의 거의 전부를 차지하는 네 가지 실수를 잡아냅니다.

## 언제 사용하나

- 누군가 BasicBlock이나 Bottleneck을 직접 만들었는데 손실이 NaN이거나 정확도가 멈춰 있을 때.
- 블록을 한 프레임워크에서 다른 프레임워크로 옮기면서 동등성을 확인하고 싶을 때.
- ResNet 내부를 바꾸는 PR(pre-activation, squeeze-excite, anti-alias 등)을 리뷰할 때.
- CIFAR 크기 입력에서는 멀쩡히 돌다가 ImageNet 해상도에서 shortcut이 틀려 크래시가 날 때.

## 입력

- PyTorch 클래스 정의(소스 텍스트 또는 임포트 가능한 경로).
- 선택 사항 `variant`: `basic` | `bottleneck` | `preact` | `seblock`.

## 네 가지 검사

### 1. shortcut shape 정렬

`stride != 1` 또는 `in_channels != out_channels`인 블록이라면 shortcut 경로는 **반드시** shape를 맞춰 주는 모듈 — 보통 1x1 conv + BN — 이어야 합니다. 이 상황에서 맨 `nn.Identity()`를 쓰면 forward 시점에 100% shape 불일치 오류가 납니다.

진단:
```
[shortcut]
  detected:  nn.Identity | 1x1 Conv + BN | 1x1 Conv + BN + ReLU | other
  required:  shape-matching Conv if (stride != 1 or in_c != out_c) else Identity
  verdict:   ok | wrong | unnecessarily heavy
```

### 2. 덧셈 대비 BN 위치

덧셈 `out + shortcut(x)`은 최종 ReLU **이전에** 일어나야 하고(post-activation, 원조 ResNet 방식), 또는 최종 ReLU는 아예 없어야 합니다(pre-activation ResNet v2). 메인 브랜치에 ReLU를 적용한 뒤 raw shortcut을 더하는 블록은 비대칭적인 활성 범위를 만들어 학습을 해칩니다.

진단:
```
[activation order]
  pattern:  post-act (conv-BN-ReLU-conv-BN-add-ReLU) | pre-act (BN-ReLU-conv-BN-ReLU-conv-add) | other
  verdict:  ok | suspect
```

### 3. conv 레이어의 bias

바로 뒤에 BatchNorm이 오는 conv는 `bias=False`여야 합니다. BN의 beta가 이미 편향을 담당하므로 conv bias를 추가로 두면 파라미터 낭비이고 수렴을 느리게 만들 수 있습니다.

진단:
```
[bias]
  convs with BN and bias=True: <개수>
  recommended fix: set bias=False on those layers
```

### 4. in-place ReLU와 autograd

shortcut과 더해질 텐서에 `nn.ReLU(inplace=True)`를 적용하면 잔차 덧셈에 아직 필요할 수 있는 값이 덮어써집니다. 덧셈 전에 새 텐서를 만드는 레이어가 뒤따르지 않는 `inplace=True`는 모두 표시하세요.

진단:
```
[in-place]
  risky inplace ops: <목록>
  fix: inplace=False before the residual add
```

## 리포트

```
[block-review]
  variant:       basic | bottleneck | preact | se | other
  shortcut:      ok | wrong | heavy
  activation:    ok | suspect
  bias-bn:       ok | <N>개 conv에 bias=False 필요
  in-place:      ok | <N>개 위험 연산
  summary:       한 문장
```

## 규칙

- 블록을 다시 쓰지 않습니다. 리포트만 합니다.
- 블록이 올바르면 모든 곳에 `ok`라고 쓰고 멈춥니다. 제안을 붙이지 않습니다.
- 여러 문제가 있으면 위 순서대로 나열합니다(shortcut이 크래시의 가장 흔한 원인이므로 맨 앞).
- 사용자가 명시적으로 지정한 pre-activation이나 squeeze-excite 변형을 틀렸다고 표시하지 않습니다.
