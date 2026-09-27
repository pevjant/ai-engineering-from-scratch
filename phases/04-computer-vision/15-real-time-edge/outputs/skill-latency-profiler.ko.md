---
name: skill-latency-profiler
description: 워밍업, 동기화, 백분위수, 메모리 추적이 들어간 완전한 지연 시간 벤치마킹 스크립트를 작성합니다
version: 1.0.0
phase: 4
lesson: 15
tags: [edge, deployment, profiling, benchmarking]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-latency-profiler.md](skill-latency-profiler.md)

# 지연 시간 프로파일러

어떤 PyTorch 모델이든 규율 있는 지연 시간 벤치마크를 만들어 냅니다. 이후 단계의 누구도 실제로 믿을 수 있는 보고서죠.

## 사용 시점

- 배포할 백본을 고르기 전에 여러 후보를 비교할 때.
- 양자화나 가지치기 전후를 비교할 때.
- 런타임을 바꾼 뒤(eager vs ONNX vs TensorRT).
- 배포 준비 완료 보고서를 만들 때.

## 입력

- `model`: PyTorch `nn.Module`.
- `input_shape`: `(1, 3, 224, 224)` 같은 튜플.
- `device`: `cpu` | `cuda` | `mps`.
- `warmup`: 기본값 10.
- `iters`: 기본값 100.

## 점검 항목

### 1. 워밍업
시간을 재지 않고 모델을 `warmup`번 실행합니다. 첫 순전파의 JIT 컴파일과 콜드 캐시 효과를 걸러 줍니다.

### 2. 동기화
`cuda`라면 시간을 재는 순전파 각각의 앞뒤로 `torch.cuda.synchronize()`를 호출합니다.
`mps`라면 `torch.mps.synchronize()`를 호출합니다.

### 3. 타이머
실제 시간(wall-clock) 측정에는 `time.perf_counter()`를 씁니다. 밀리초로 변환합니다.

### 4. 백분위수
시간 목록 전체를 정렬합니다. `p50, p90, p95, p99, mean, std`를 보고합니다.

### 5. 메모리
`cuda`라면 실행이 끝난 뒤 `torch.cuda.max_memory_allocated()`를 호출하고 기준값을 뺍니다.
`cpu`라면 실행 전후로 `tracemalloc` 또는 `psutil.Process().memory_info().rss`를 씁니다.

### 6. 배치 크기 스윕
선택 사항. `batch_size in [1, 4, 16, 32]`에 대해 벤치마크를 반복하면 처리량 대 지연 시간 트레이드오프가 드러납니다.

## 출력 템플릿

```python
import time
import torch
import psutil, os

def profile(model, input_shape, device="cpu", warmup=10, iters=100):
    proc = psutil.Process(os.getpid())
    baseline_rss = proc.memory_info().rss / 1e6

    model = model.to(device).eval()
    x = torch.randn(input_shape, device=device)

    def sync():
        if device == "cuda":
            torch.cuda.synchronize()
        elif device == "mps":
            torch.mps.synchronize()

    with torch.no_grad():
        for _ in range(warmup):
            model(x)
        sync()
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()

        times = []
        for _ in range(iters):
            sync()
            t0 = time.perf_counter()
            model(x)
            sync()
            times.append((time.perf_counter() - t0) * 1000)

    times.sort()
    mean = sum(times) / len(times)
    std  = (sum((t - mean) ** 2 for t in times) / len(times)) ** 0.5

    def pct(p):
        idx = max(0, min(len(times) - 1, int(len(times) * p) - 1))
        return times[idx]

    report = {
        "p50_ms":  pct(0.50),
        "p90_ms":  pct(0.90),
        "p95_ms":  pct(0.95),
        "p99_ms":  pct(0.99),
        "mean_ms": mean,
        "std_ms":  std,
        "rss_mb":  proc.memory_info().rss / 1e6 - baseline_rss,
    }
    if device == "cuda":
        report["peak_cuda_mb"] = torch.cuda.max_memory_allocated() / 1e6

    return report
```

## 규칙

- 항상 워밍업을 실행합니다. 첫 순전파 시간은 절대 믿지 않습니다.
- 평균이 아니라 백분위수 — 이상치 하나가 평균은 두 배로 만들지만 p50은 거희 안 움직입니다.
- 프로덕션과 같은 input_shape를 사용하세요. 224x224의 지연 시간은 384x384의 지연 시간이 아닙니다.
- CUDA에서는 `torch.cuda.synchronize()`를 절대 빼먹지 않습니다. 없으면 숫자 자체가 무의미합니다.
- 숫자 옆에 torch 버전, CUDA 버전, 기기 이름을 함께 기록하세요. 그렇지 않으면 수치끼리 비교가 불가능해집니다.
