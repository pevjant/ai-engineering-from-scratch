---
name: checkpoint-save-resume
description: 전체 RNG 캡처를 갖춘 원자적 샤딩 체크포인트. 강제 종료된 실행이 에포크 중간부터 같은 손실 궤적으로 재개된다.
version: 1.0.0
phase: 19
lesson: 47
tags: [training, durability, resume, sharded-state]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-checkpoint-save-resume.md](skill-checkpoint-save-resume.md)

## 언제 사용하나

클러스터 시간 제한(wallclock cap)보다 긴 모든 학습 실행, 노드 재부팅을 견뎌야 하는 모든 실행, 단일 페이로드에 담기엔 너무 큰 모든 모델에 사용합니다.

## 페이로드 구조

```python
{
  "schema": "ckpt.v1",
  "model": model.state_dict(),
  "optimizer": opt.state_dict(),
  "scheduler": sched.state_dict(),
  "state": {"step": int, "epoch": int, "batch_in_epoch": int, "losses": [float, ...]},
  "rng": {"python": ..., "numpy": ..., "torch_cpu": ..., "torch_cuda": ...},
  "wall_saved_at": time.time(),
}
```

## 원자적 저장

1. 페이로드를 대상과 같은 디렉터리의 고유한 임시 파일에 씁니다.
2. `os.replace(tmp, target)`로 원자적으로 교체합니다.
3. 대상 이름에 곧바로 쓰는 일은 절대 없어야 합니다.

## 샤딩 레이아웃

- 샤드마다 `model.shard-NNN.pt` 파일. 키 기준 라운드 로빈 또는 파라미터 그룹 기준 분할.
- `meta.pt`는 옵티마이저, 스케줄러, 학습 상태, RNG, 샤드 매니페스트를 담습니다.
- `index.json`은 모든 샤드와 `meta.pt`의 `sha256`을 담습니다.
- 로더는 병합 전에 모든 해시를 검증하고, 체크포인트 디렉터리 밖의 샤드 경로는 거부합니다.
- 모든 파일은 `torch.load(path, map_location="cpu", weights_only=True)`로 불러옵니다. RNG 상태는 평범한 리스트로 유지해서 weights-only 로더를 통과하게 만드세요.

## 에포크 중간 재개

- `step` 옆에 `(epoch, batch_in_epoch)`을 함께 저장합니다.
- 재개되는 에포크의 첫 배치 전에 RNG 상태를 복원합니다.
- 이미 소비한 배치들을 건너뛰도록 생성기를 빨리 감습니다.

## 실패 모드

- 디바이스를 넘나드는 rename: 원자적이지 않아 이전 파일을 잃습니다. 임시 파일은 같은 디렉터리에 두세요.
- RNG를 빼먹는 경우: 재개된 손실이 베이스라인에서 벗어납니다. 데모의 단언문을 실행해 확인하세요.
- 옵티마이저 상태를 빼먹는 경우: 다음 스텝이 휘청거립니다. 같은 차이가 기하급수적으로 커집니다.
- 잘못된 체크포인트를 정리(pruning)하는 경우: 마지막 K개에 최고 성능 체크포인트를 더해 보관하세요.
- `weights_only=False`로 불러오는 경우: `.pt` 파일은 피클이므로, 신뢰할 수 없는 체크포인트가 로드 시점에 코드를 실행합니다.
