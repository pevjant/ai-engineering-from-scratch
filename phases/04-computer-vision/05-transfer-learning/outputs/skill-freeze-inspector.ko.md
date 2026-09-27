---
name: skill-freeze-inspector
description: 어떤 파라미터가 학습 가능한지, 어떤 BatchNorm 레이어가 eval 모드인지, 옵티마이저가 실제로 학습 가능 파라미터를 소비하는지 보고
version: 1.0.0
phase: 4
lesson: 5
tags: [computer-vision, transfer-learning, debugging, pytorch]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-freeze-inspector.md](skill-freeze-inspector.md)

# 프리즈 검사관 (Freeze Inspector)

전이 학습 버그는 세 곳에 숩니다: 프리즈돼야 하는데 안 된 파라미터, 학습돼야 하는데 안 된 파라미터, 그리고 프리즈 상태가 바뀌기 전에 만들어진 옵티마이저. 이 스킬은 세 가지를 한 번의 패스로 끌어냅니다.

## 언제 사용하나

- 파라미터 일부에 `requires_grad`를 설정한 직후.
- 파인튜닝 실행의 첫 학습 스텝 전.
- `freeze_bn_stats`나 BN 모드를 바꾸는 다른 헬퍼를 호출한 뒤.
- 검증 정확도가 무작위 수준에서 멈춰 있고, 아무것도 실제로 학습되지 않는다고 의심될 때.

## 입력

- `model`: PyTorch `nn.Module`.
- `optimizer`: 곧 학습에 쓸 옵티마이저.
- 선택 사항 `expected_frozen_prefixes`: 프리즈돼야 하는 파라미터 이름 접두어 목록(예: `["conv1", "bn1", "layer1"]`).

## 단계

1. **파라미터 순회.** 각 `(name, param)`마다:
   - `requires_grad` 기록
   - `shape`과 `numel` 기록

2. **모듈 순회.** 각 모듈마다:
   - BatchNorm이라면 eval 모드인지, affine 파라미터(`weight`, `bias`)가 학습 가능한지 기록.

3. **옵티마이저 검사.** 각 파라미터 그룹마다:
   - 그룹의 `params`를 `id(p)` 집합으로 펼칩니다.
   - `requires_grad == True`인 모든 파라미터의 `id(p)` 집합과 비교합니다.

4. **네 가지 실패 양상 탐지:**
   - `leaked_train`: 파라미터가 `requires_grad=True`인데 옵티마이저에 없음(그래디언트는 계산되지만 적용은 안 됨).
   - `ghost_train`: 파라미터가 옵티마이저에 있는데 `requires_grad=False`(옵티마이저 상태 낭비; 나중에 requires_grad를 다시 켜면 버그의 씨앗이 되기도 함).
   - `bn_mismatch`: (a) BN 레이어가 train 모드(이동 통계 누적)인데 affine 파라미터는 프리즈돼 있거나, (b) BN 레이어가 eval 모드(통계 프리즈)인데 affine 파라미터는 학습 가능. 둘 다 비일관적 상태이고 거의 항상 버그입니다.
   - `expected_vs_actual`: `expected_frozen_prefixes`에 있는 접두어 중 여전히 학습 가능한 파라미터를 가진 것.

## 리포트

```
[freeze-inspector]
  model trainable params: <N>
  model frozen params:    <N>
  batchnorm layers in eval mode: <개수>
  batchnorm layers in train mode: <개수>

[optimizer coverage]
  trainable params fed to optimizer: <N> 중 <M>
  leaked_train: <이름 목록> (학습 가능하지만 옵티마이저에 없음)
  ghost_train:  <이름 목록> (옵티마이저에는 있지만 프리즈됨)

[bn audit]
  mismatched layers: <이름 목록>

[expectations]
  expected_frozen_prefixes: <...>
  violating params:         <목록>

[verdict]
  ok | <가장 심각한 문제의 한 줄 요약>
```

## 규칙

- 파라미터 이름만 보고합니다; 가중치 자체를 절대 출력하지 않습니다.
- 모든 목록은 파라미터 이름 기준 알파벳순으로 정렬합니다.
- 옵티마이저 커버리지가 100%이고 불일치가 없으면 `ok`를 반환하고 멈춥니다.
- `leaked_train`에는 항상 "프리즈 상태가 바뀐 후 옵티마이저를 다시 만들 것"을 권합니다.
- `ghost_train`에는 파라미터 그룹을 제거하거나, 학습 의도가 있었다면 `requires_grad=True`로 설정할 것을 권합니다.
