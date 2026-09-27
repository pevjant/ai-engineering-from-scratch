---
name: distributed-fsdp-ddp
description: 밑바닥부터 만든 DDP 래퍼와 FSDP 파라미터 샤딩 개요로 멀티 랭크 학습을 구성한다. gloo 또는 nccl 백엔드 사용.
version: 1.0.0
phase: 19
lesson: 48
tags: [distributed, ddp, fsdp, collectives]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-distributed-fsdp-ddp.md](skill-distributed-fsdp-ddp.md)

## 언제 사용하나

모델은 디바이스 하나에 들어가지만 더 큰 처리량이 필요한 경우(DDP). 모델이 디바이스 하나에 들어가지 않는 경우(FSDP). 어느 쪽이든 같은 코드 경로를 사용하는 멀티 랭크 학습 환경을 만듭니다.

## 프로세스 그룹 띄우기

```python
os.environ["MASTER_ADDR"] = "127.0.0.1"
os.environ["MASTER_PORT"] = str(port)
dist.init_process_group(backend="gloo", rank=rank, world_size=world_size)
```

`gloo`는 CPU 백엔드이고, `nccl`은 GPU 백엔드입니다. 둘 다 같은 집합 통신 표면을 구현합니다.

## 모델 감싸기

1. 랭크 0에서 자기 시드로 모델을 만듭니다.
2. DDP 껍데기로 감쌉니다.
3. 껍데기의 `__init__`은 모든 파라미터와 버퍼에 대해 `dist.broadcast(p.data, src=0)`를 호출합니다.
4. 모든 `loss.backward()` 이후 트레이너가 `sync_grads()`를 호출합니다.
5. `sync_grads()`는 `dist.all_reduce(p.grad, op=SUM)`과 `p.grad.div_(world_size)`를 호출합니다.
6. 모든 랭크가 같은 평균 그래디언트로 옵티마이저를 스텝합니다.

## 파라미터 샤딩(FSDP 개요)

1. 각 파라미터를 평탄화하고 `world_size`의 배수로 패딩합니다.
2. 자기 샤드는 로컬에 두고 나머지는 놓아 줍니다.
3. 순전파 전에 `dist.all_gather(...)`로 모든 랭크에서 전체 텐서를 재조립합니다.
4. 순전파 후에는 전체 텐서를 버립니다.

## 실패 모드

- 브로드캐스트를 건너뛰는 경우: 랭크들이 서로 다른 초기값에서 출발해 조용히 갈라집니다.
- 합산 후 나누기를 잊는 경우: 그래디언트가 world_size배가 되어 옵티마이저 스텝이 과하게 커집니다.
- 체크포인트에 디바이스를 넘나드는 rename을 쓰는 경우: 원자적이지 않습니다. 레슨 47의 같은 함정입니다.
- 같은 집합 통신에서 CPU 텐서와 CUDA 텐서를 섞는 경우: 백엔드 불일치로 실행이 멈춥니다(hang).
