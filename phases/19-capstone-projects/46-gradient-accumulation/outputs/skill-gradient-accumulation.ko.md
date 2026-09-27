---
name: gradient-accumulation
description: 마이크로 배치 손실을 스케일링하고 윈도우당 옵티마이저를 한 번만 스텝시켜, 디바이스 메모리보다 큰 유효 배치로 학습한다.
version: 1.0.0
phase: 19
lesson: 46
tags: [training, batch-size, distributed, scaling]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-gradient-accumulation.md](skill-gradient-accumulation.md)

## 언제 사용하나

유효 배치(effective batch)는 그래디언트를 매끄럽게 만들고 학습률 스케줄과 맞춰 주는 레버입니다. 순전파 한 번에 감당할 수 없을 때 쓰는 레시피가 바로 이것입니다.

## 레시피

1. 메모리에 들어가면서 가속기를 꽉 채우는 가장 큰 크기를 `micro_batch`로 고릅니다.
2. 학습률 스케줄에 맞춰 `effective_batch`를 고릅니다.
3. `accum_steps = effective_batch // (micro_batch * world_size)`로 설정하고, 나누어 떨어지는지 단언(assert)합니다.
4. 마이크로 배치마다: `loss = criterion(model(x), y) / accum_steps; loss.backward()`.
5. 마지막이 아닌 마이크로 배치에서는 `model.no_sync()`에 들어가 DDP의 그래디언트 all-reduce를 건너뜁니다.
6. 마지막 마이크로 배치 이후 `optimizer.step()`을 한 번 실행합니다. 다음 윈도우 전에 그래디언트를 0으로 초기화합니다.
7. 옵티마이저 상태는 유효 배치당 한 번 전진하고, 학습률 스케줄도 유효 배치당 한 번 갱신됩니다.

## 로깅

유효 스텝마다 `samples_per_sec`, `median_step_ms`, `sync_calls`, `accum_steps`, `effective_batch`를 담은 작은 JSON 레코드를 남깁니다. 이게 없으면 비용 트레이드오프가 보이지 않습니다.

## 실패 모드

- `/ accum_steps` 스케일링을 잊는 경우: 그래디언트가 N배로 폭발합니다.
- 윈도우 중간에 스텝하는 경우: 파라미터가 어긋납니다(drift).
- 모든 마이크로 배치마다 동기화하는 경우: 통계적으로 얻는 것 없이 네트워크 병목만 생깁니다.
- 혼합 정밀도(mixed precision) 언스케일링과 섞는 경우: 언스케일링한 손실에만 스케일링을 적용해야 합니다.
