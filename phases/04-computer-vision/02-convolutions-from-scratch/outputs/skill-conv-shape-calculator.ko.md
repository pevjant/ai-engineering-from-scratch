---
name: skill-conv-shape-calculator
description: CNN 명세를 레이어별로 훑어 모든 블록의 출력 모양, 수용 영역, 파라미터 수를 보고하기
version: 1.0.0
phase: 4
lesson: 2
tags: [computer-vision, cnn, architecture, debugging]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-conv-shape-calculator.md](skill-conv-shape-calculator.md)

# 합성곱 모양 계산기

CNN을 설계하거나 디버깅할 때 쓰는 결정론적 도우미입니다. 입력 모양과 레이어 명세 목록이 주어지면, 모델을 실행하지 않고 모양, 수용 영역, 파라미터 수를 추적합니다.

## 언제 쓰나

- 새 CNN을 설계하면서 모든 다운샘플이 깔끔한 크기에 떨어지는지 확인하고 싶을 때.
- 논문을 읽으면서 그 아키텍처 표를 코드로 옮길 때.
- 사전 학습된 백본이 분류기 헤드에서 모양 불일치로 죽고, 어느 레이어가 공간 크기를 바꿨는지 알아야 할 때.
- 학습하기 전에 두 백본의 파라미터 효율을 비교할 때.

## 입력

- `input_shape`: `(C, H, W)`.
- `layers`: 레이어 딕셔너리의 순서 있는 목록. 각 항목은 다음을 지원합니다:
  - `{type: "conv", c_out, k, s, p, groups=1, bias=true}`
  - `{type: "pool", mode: "max"|"avg", k, s, p=0}`
  - `{type: "adaptive_pool", out_h, out_w}`
  - `{type: "flatten"}`
  - `{type: "linear", out_features, bias=true}`

## 단계

1. **추적 초기화** — `(C, H, W)`, 수용 영역 `1`, 실효 스트라이드 `1`, 누적 파라미터 `0`으로 시작합니다.

2. **각 레이어마다** 다음 순서로 갱신합니다:
   - `C_out`을 계산하거나(conv/linear), 풀링이라면 `C_in`을 그대로 통과시킵니다.
   - 공간 출력을 계산합니다. conv와 pool에는 `(H + 2P - K) / S + 1`을, adaptive pool에는 `out_h/out_w`를, flatten에는 (linear 앞에서 출력 모양이 `(C * H * W, 1, 1)`이 되도록) `(1, 1)`을, linear에는 스칼라 `1x1`을 사용합니다.
   - 수용 영역과 실효 스트라이드를 갱신합니다:
     - Conv/pool: `RF_new = RF_old + (K - 1) * effective_stride`, `effective_stride *= S`.
     - Adaptive pool: 실효 `S = H_in / out_h`(내림)인 풀링으로 취급합니다. `RF_new = RF_old + (H_in - 1) * effective_stride_old`; `effective_stride *= S`. adaptive pool의 RF는 이전 공간 범위 전체와 같다는 점에 유의하세요.
     - Flatten / linear: RF와 실효 스트라이드는 더 이상 의미가 없습니다. flatten 이전 값으로 고정하고 이후 행에서는 생략합니다.
   - 파라미터를 계산합니다:
     - Conv: `C_out * (C_in / groups) * K * K + (C_out if bias else 0)`.
     - Linear: `out_features * in_features + (out_features if bias else 0)`.
     - Pool과 flatten: 0.

3. **문제를 감지**하고 표시합니다:
   - 정수가 아닌 출력 크기(어긋난 스트라이드/패딩).
   - 스택이 끝나기 전에 `H_out <= 0`.
   - 수용 영역이 입력 크기를 초과(그 지점 이후 연산 낭비 가능).
   - 레이어별 파라미터의 급격한 10배 점프. 채널 설계가 틀렸다는 신호.

4. **보고** — 표 하나로:

```
idx  layer                C_in  C_out  K  S  P  H_out  W_out  RF    params     cum_params
1    conv 3x3 s=1 p=1     3     32     3  1  1  224    224    3     896        896
2    conv 3x3 s=2 p=1     32    64     3  2  1  112    112    7     18,496     19,392
3    pool max 2x2         64    64     2  2  0  56     56     11    0          19,392
...
```

5. **요약 줄**: 최종 `(C, H, W)`, 최종 수용 영역, 총 파라미터, 경고.

## 규칙

- 공간 크기는 항상 정수로 돌려줍니다. 공식이 비정수를 내면 오류로 표시하고 조용히 버림(floor)하지 마세요.
- `groups > 1`이면 `C_in % groups == 0`과 `C_out % groups == 0`을 검증하고, 아니면 오류를 냅니다.
- depthwise 합성곱(`groups == C_in`)이라면 `layer` 열에 표시해서 파라미터가 적은 이유가 보이게 하세요.
- 사용자가 BatchNorm이나 활성화 레이어를 넣으면 모양 계산에서는 무시하되 파라미터는 계속 누적합니다(BatchNorm당 `2 * C`).
- 빠진 필드의 기본값을 지어내지 마세요. 모든 conv와 pool에 `k`, `s`, `p`를 요구합니다.
