---
name: skill-frame-sampler-auditor
description: 비디오 파이프라인의 프레임 샘플러를 검사해 인덱스 어긋남, 짧은 클립 처리, 크롭 일관성 문제를 진단
version: 1.0.0
phase: 4
lesson: 12
tags: [computer-vision, video, sampling, debugging]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-frame-sampler-auditor.md](skill-frame-sampler-auditor.md)

# 프레임 샘플러 감사기

비디오 파이프라인이 무너지는 지점은 바로 프레임 샘플링입니다. 여기의 버그는 그 아래 모든 지표로 번져 나갑니다.

## 언제 사용하나

- 새 비디오 데이터 로더를 작성할 때
- 논문의 수치를 재현하는데 학습 정확도가 보고된 값보다 낮을 때
- 실행할 때마다 평가 정확도가 들쭉날쭉한 비디오 모델을 디버깅할 때

## 입력

- `sampler_code`: (num_frames_total, T)를 받아 T개 인덱스를 반환하는 Python 함수.
- `T`: 목표 클립 길이.
- 선택 테스트 케이스: 시험해 볼 `num_frames_total` 값들 (예: `[3, T-1, T, T+1, 30, 300, 3000]`).

## 검사 항목

### 1. 짧은 클립 처리
`num_frames_total < T`를 넣어 보세요. 반환되는 모든 인덱스는 `[0, num_frames_total - 1]` 안에 있어야 합니다. 표준 패딩 정책은 남는 자리를 마지막 프레임으로 반복 채우는 것입니다.

### 2. 경계 인덱스
`num_frames_total == T`를 넣어 보세요. 반환 인덱스는 정확히 `[0, 1, ..., T-1]`이어야 합니다.

### 3. 균등 분포
`num_frames_total == 10 * T`를 넣어 보세요. 반환 인덱스는 단조 증가하고 대략 고르게 간격이 벌어져 있어야 합니다.

### 4. 밀집 윈도우 경계
밀집 샘플링에서 `num_frames_total == 3 * T`를 넣어 보세요. 반환 인덱스는 연속된 윈도우를 이루고, 클립 끝을 넘어서면 안 됩니다.

### 5. 결정론성
같은 입력과(결정론적 샘플러라면) 같은 RNG로 샘플러를 두 번 호출해 보세요. 인덱스가 일치해야 합니다.

### 6. 크롭 일관성
파이프라인이 프레임별 공간 크롭도 함께 반환한다면, 같은 시드로 같은 클립에 대해 샘플러를 두 번 돌려서 모든 프레임이 같은 크롭 박스(같은 `(x, y, w, h)`)를 쓰는지 확인하세요. 한 클립 안에서 프레임마다 크롭이 다르면 시간적 일관성이 파괴됩니다. 대표적인 조용한 버그입니다. 허용되는 변형: 증강이 *클립 단위*로 적용되고 클립 안에서는 일관된 경우.

## 보고

```
[sampler audit]
  name: <function name>
  T:    <int>

[short-clip handling]
  passed | failed (<details>)

[boundary]
  passed | failed

[uniform spacing]
  passed | failed (<stddev of gaps>)

[dense window]
  passed | failed (<details>)

[determinism]
  passed | failed

[crop consistency]
  passed | failed (<per-frame crop varies: yes/no>)

[verdict]
  ok | fix required
```

## 규칙

- 짧은 클립 처리에서 범위를 벗어난 인덱스를 반환하는 샘플러는 절대 "ok"로 표시하지 마세요.
- 밀집 샘플러는 `num_frames_total - 1`을 넘어서는 윈도우를 절대 반환하면 안 됩니다.
- 샘플러가 확률적(밀집)이라면 결정론성은 명시적으로 시드를 준 RNG로만 테스트하세요.
- 표준 정책들(마지막 프레임으로 패딩, 윈도우를 끝에 맞춰 clamp, 반열린 구간 반올림)은 제안하되 조용히 고치지는 마세요.
