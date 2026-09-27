> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# GPU 설정과 클라우드 (GPU Setup & Cloud)

> 배우는 동안은 CPU 학습으로 충분합니다. 진짜 학습(훈련)엔 GPU가 필요하죠.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 0, 레슨 01
**소요 시간:** 약 45분

## 학습 목표

- `nvidia-smi`와 PyTorch의 CUDA API로 로컬 GPU 사용 가능 여부 확인하기
- Google Colab에 T4 GPU를 설정해 무료 클라우드 실험 환경 갖추기
- CPU 대비 GPU 행렬 곱셈을 벤치마크하고 속도 향상 폭 측정하기
- fp16 경험 법칙으로 내 VRAM에 들어가는 최대 모델 크기 추정하기

## 문제 상황

페이즈 1~3의 대부분 레슨은 CPU에서도 잘 돌아갑니다. 하지만 CNN, 트랜스포머, LLM 학습이 시작되는 페이즈 4부터는 GPU 가속이 필요합니다. CPU에서 8시간 걸리는 학습이 GPU에서는 10분이면 끝납니다.

선택지는 세 가지입니다: 로컬 GPU, 클라우드 GPU, 그리고 Google Colab(무료).

## 개념

```
선택할 수 있는 옵션:

1. 로컬 NVIDIA GPU
   비용: $0 (이미 갖고 있음)
   설정: CUDA + cuDNN 설치
   적합한 경우: 꾸준한 사용, 대용량 데이터셋

2. Google Colab (무료 티어)
   비용: $0
   설정: 없음
   적합한 경우: 빠른 실험, 집에 GPU가 없을 때

3. 클라우드 GPU (Lambda, RunPod, Vast.ai)
   비용: 시간당 $0.20-2.00
   설정: SSH 접속 + 설치
   적합한 경우: 본격적인 학습, 대형 모델
```

```figure
s0-gpu-dispatch
```

## 직접 만들어 보기

### 옵션 1: 로컬 NVIDIA GPU

GPU가 있는지 확인:

```bash
nvidia-smi
```

CUDA 지원 PyTorch 설치:

```python
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

### 옵션 2: Google Colab

1. [colab.research.google.com](https://colab.research.google.com) 접속
2. 런타임 > 런타임 유형 변경 > T4 GPU
3. `!nvidia-smi` 실행으로 확인

이 코스의 노트북은 그대로 Colab에 올려 사용할 수 있습니다.

### 옵션 3: 클라우드 GPU

Lambda Labs, RunPod, Vast.ai의 경우:

```bash
ssh user@your-gpu-instance

pip install torch torchvision torchaudio
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### GPU가 없다? 문제없습니다.

대부분의 레슨은 CPU에서 동작합니다. GPU가 필요한 레슨은 그 사실을 명시하고 Colab 링크를 함께 제공합니다.

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using: {device}")
```

## 직접 만들어 보기: GPU vs CPU 벤치마크

```python
import torch
import time

size = 5000

a_cpu = torch.randn(size, size)
b_cpu = torch.randn(size, size)

start = time.time()
c_cpu = a_cpu @ b_cpu
cpu_time = time.time() - start
print(f"CPU: {cpu_time:.3f}s")

if torch.cuda.is_available():
    a_gpu = a_cpu.to("cuda")
    b_gpu = b_cpu.to("cuda")

    torch.cuda.synchronize()
    start = time.time()
    c_gpu = a_gpu @ b_gpu
    torch.cuda.synchronize()
    gpu_time = time.time() - start
    print(f"GPU: {gpu_time:.3f}s")
    print(f"Speedup: {cpu_time / gpu_time:.0f}x")
```

## 연습 문제

1. 위 벤치마크를 실행해 CPU와 GPU 시간을 비교하기
2. GPU가 없다면 Google Colab에서 실행해 비교해 보기
3. GPU 메모리 용량을 확인하고 들어갈 수 있는 최대 모델 크기를 추정해 보기 (경험 법칙: fp16 기준 파라미터당 2바이트)

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| CUDA | "GPU 프로그래밍" | GPU 위에서 코드를 실행할 수 있게 해 주는 NVIDIA의 병렬 컴퓨팅 플랫폼 |
| VRAM | "GPU 메모리" | GPU에 달린 비디오 RAM으로 시스템 RAM과는 별개. 모델 크기를 제한한다 |
| fp16 | "반정밀도" | 16비트 부동소수점. fp32의 절반 메모리를 쓰면서 정확도 손실은 미미하다 |
| Tensor Core | "빠른 행렬 전용 하드웨어" | 행렬 곱셈 전문 GPU 코어. 일반 코어보다 4~8배 빠르다 |
