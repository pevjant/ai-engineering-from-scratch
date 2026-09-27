> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 그래디언트 체크포인팅과 활성값 재계산

> 역전파는 모든 중간 활성값(activation)을 쥐고 있습니다. 70B 파라미터에 128K 컨텍스트면 랭크당 활성값이 3 TB에 이릅니다. 체크포인팅은 FLOPs를 메모리로 바꾸는 거래입니다. 저장 대신 재계산하는 것입니다. 문제는 어느 구간을 버릴지인데, 답은 "전부 버린다"가 아닙니다.

**유형:** Build
**언어:** Python (numpy, 선택적 torch)
**선수 지식:** 페이즈 10 레슨 04 (사전학습 미니-GPT), 페이즈 10 레슨 05 (스케일링 & 분산)
**시간:** 약 70분

## 문제 상황

트랜스포머를 학습시키면, 역전파에서 미분하는 모든 연산의 입력을 레이어마다 저장해 둡니다. 어텐션 입력, Q/K/V 프로젝션, 소프트맥스 출력, FFN 입력, 정규화 출력, 잔차 스트림까지입니다. 은닉 크기 `d`, 시퀀스 길이 `L`, 배치 `B`인 레이어의 경우 레이어당 `12 * B * L * d` 부동소수점 값 정도입니다.

`d=8192, L=8192, B=1`이면 BF16 기준 레이어당 800 MB입니다. 64레이어 모델은 활성값만 51 GB입니다. 미니배치 크기를 곱하기 전이고, 어텐션-소프트맥스 중간값(헤드당 `L^2`)을 더하기 전이고, 텐서 병렬의 부분 복사본까지 고려하기 전의 숫자입니다.

양쪽에서 오는 청구서: BF16 가중치와 옵티마이저 상태는 80GB에 들어갈 수 있지만 활성값이 한계를 넘깁니다. 그래디언트 체크포인팅(활성값 재계산이라고도 함)이 표준 해법입니다. 활성값 대부분을 버리고, 역전파 때 순전파를 다시 돌려 되찾는 것입니다. 비용은 추가 FLOPs이고, 이득은 체크포인트 구간 수 대비 전체 레이어 수의 비율만큼 메모리가 줄어드는 것입니다.

순진하게 하면 한 단계당 순전파 FLOPs가 대략 33% 더 듭니다. 잘 하면 — Korthikanti 외의 "스마트 선택" 방식의 선택적 체크포인팅 — FLOP 오버헤드 5% 미만으로 메모리를 5배 아낄 수 있습니다. FP8 행렬 곱, FSDP 오프로드, 전문가 병렬 MoE까지 얹히면 이 차이가 정말 중요해집니다. 메모리도, 낭비되는 연산도 감당할 수 없으니까요.

## 개념

### 역전파가 실제로 필요한 것

`output = layer(input)`이라 합시다. 역전파는 `grad_input`과 `grad_params`를 원합니다. 이를 계산하려면:

- `input`(선형 레이어에서 `grad_params = input.T @ grad_output`를 계산하는 데 필요)
- 일부 활성값 도함수 중간값(ReLU/GELU/소프트맥스의 도함수는 활성값 자체에 의존)

순전파는 이것들을 자동으로 오토그래드 그래프에 저장합니다. 모든 `tensor.retain_grad()`와 입력을 필요로 하는 모든 연산이 참조를 유지합니다.

### 순진한 전체 체크포인팅

네트워크를 `N`개 구간으로 나눕니다. 순전파 때는 각 구간의 *입력*만 저장합니다. 역전파가 중간값을 필요로 하면 해당 구간의 순전파를 다시 돌려 중간값을 만들고, 그다음 미분합니다.

예: 32레이어 트랜스포머를 레이어 1개짜리 구간 32개로 분할.

- 메모리: 32개 레이어 입력(작음) vs 32 * (레이어당 활성값 부피)(거대함).
- 추가 연산: 구간당 순전파 1회 추가. 즉 순전파 FLOPs가 총 약 33% 증가(역전파가 순전파의 2배이므로, 전체 단계가 1 + 2 = 3 단위 대신 1 + 1 + 2 = 4 단위가 됨).

이것이 Chen 외 2016의 원조 레시피입니다. 메모리와 연산의 균형을 위해 `sqrt(L)`레이어마다 체크포인트 하나를 두는 것입니다. L=64면 체크포인트 8개입니다.

### 선택적 체크포인팅 (Korthikanti 2022)

모든 활성값이 같은 비용을 치르는 것은 아닙니다. 어텐션 소프트맥스 출력은 `B*L*L*heads`로 시퀀스 길이에 대해 *2차(quadratic)*로 늘어납니다. FFN 은닉 활성값은 `B*L*4d`로 선형으로 늘어납니다. 긴 시퀀스에서는 소프트맥스가 지배합니다.

선택적 체크포인팅은 저장이 값싼 활성값(선형 프로젝션, 잔차)은 유지하고, 비싼 것(어텐션)만 재계산합니다. 재계산에 드는 FLOPs는 최소한으로 내고 O(L^2) 메모리를 아낍니다.

Megatron-Core는 이것을 "선택적(selective)" 활성값 재계산으로 구현합니다. 2024년 이후 대부분의 프론티어 학습 러닝에서 표준입니다.

### 오프로드

재계산의 대안: 순전파와 역전파 사이에 활성값을 CPU RAM으로 보내는 것입니다. PCIe 대역폭이 필요하고, 유휴 대역폭이 재구체화(rematerialization) 비용을 넘을 때 유리합니다. 혼합 전략도 흔합니다. 일부 레이어는 체크포인트, 다른 일부는 오프로드.

FSDP2는 오프로드를 1급 옵션으로 제공합니다. GPU가 메모리로 병목이지만 CPU-GPU 전송에 여유가 있을 때 오프로드가 빛을 냅니다.

### 재계산 비용 모델

`L`레이어 중 `k`레이어마다 순진하게 체크포인트를 둘 때의 단계당 FLOPs:

```
flops_fwd_normal = L * f_layer
flops_bwd_normal = 2 * L * f_layer
flops_total_normal = 3 * L * f_layer

flops_fwd_ckpt = L * f_layer
flops_recompute = L * f_layer  # segment 안의 레이어당 순전파 1회 추가
flops_bwd_ckpt = 2 * L * f_layer
flops_total_ckpt = 4 * L * f_layer
overhead = 4 / 3 - 1 = 0.33 = 33%
```

선택적 체크포인팅은 레이어 전체가 아니라 어텐션 커널만 재계산합니다:

```
flops_recompute_selective = L * f_attention ~= L * f_layer * 0.15
overhead_selective = (3 + 0.15) / 3 - 1 = 0.05 = 5%
```

### 메모리 절감 모델

레이어당 활성값 부피: `A`. `L`레이어면 총 활성값 메모리는 `L * A`.

전체 체크포인트(구간 크기 1): `L * input_volume`만 저장(표준 트랜스포머에서 약 `L * 1/10 A`). 약 `9 * L * A * 1/10` 절감.

`k`레이어마다 체크포인트: `L/k * A`를 저장하고, 활성 구간 안의 `k-1`레이어 분량을 추가로 저장.

`k = sqrt(L)`에서 메모리와 재계산 비용이 모두 `sqrt(L)`에 비례해 늘어납니다. 비용이 균일한 레이어에서 이것이 최적 트레이드오프입니다.

### 체크포인트를 두지 말아야 할 때

- 파이프라인 스테이지의 이미 진행 중인 가장 안쪽 레이어. 어차피 끝내야 합니다.
- 스테이지의 연산을 지배하는 첫/마지막 레이어(트랜스포머에서는 드묾).
- 이미 FlashAttention을 쓰는 어텐션 커널. Flash가 이미 소프트맥스 재계산을 빠르게 하므로, 레이어 수준 체크포인팅을 얹어도 얻는 게 적습니다.

### 구현 패턴

1. **함수 래퍼:** 구간을 `torch.utils.checkpoint.checkpoint(fn, input)`으로 감쌉니다. PyTorch는 `input`만 저장하고, 역전파 때 나머지를 재계산합니다.

2. **데코레이터 기반:** 레이어에 체크포인트 가능(checkpointable) 표시를 붙이고, 트레이너가 설정 시점에 어떤 구간을 감쌀지 결정합니다.

3. **수동 명시적 재계산:** 역전파를 직접 작성하고, 저장해 둔 입력으로 순전파를 복제하는 커스텀 `recompute_forward`를 호출합니다.

세 방법 모두 기능적으로 같은 결과를 냅니다. 래퍼가 표준 어법입니다.

### TP / PP / FP8과의 상호작용

- **텐서 병렬:** 체크포인트 입력은 재계산 시 다시 모으거나(gather) 재분산(rescatter)해야 합니다. 통신 비용을 처리하세요.
- **파이프라인 병렬:** 전형적인 패턴은 각 파이프라인 스테이지의 순전파를 체크포인트해서, 역순 미니배치가 활성값 메모리를 재사용할 수 있게 하는 것입니다.
- **FP8 재계산:** 재계산 중 갱신되는 amax 이력은 원래 순전파의 것과 일치해야 합니다. 그렇지 않으면 FP8 스케일이 흘러갑니다. 대부분의 프레임워크는 스케일을 스냅샷으로 저장합니다.

```figure
activation-recompute
```

## 만들어 보기

### 단계 1: 구간이 있는 간이 모델

```python
import numpy as np


def linear_forward(x, w, b):
    return x @ w + b


def relu(x):
    return np.maximum(x, 0)


def layer_forward(x, w1, b1, w2, b2):
    h = relu(linear_forward(x, w1, b1))
    return linear_forward(h, w2, b2)


def model_forward(x, params):
    activations = [x]
    h = x
    for w1, b1, w2, b2 in params:
        h = layer_forward(h, w1, b1, w2, b2)
        activations.append(h)
    return h, activations
```

### 단계 2: 모든 활성값이 필요한 순진한 역전파

```python
def model_backward(grad_output, activations, params):
    grads = [None] * len(params)
    g = grad_output
    for i in range(len(params) - 1, -1, -1):
        w1, b1, w2, b2 = params[i]
        x_in = activations[i]
        h_pre = linear_forward(x_in, w1, b1)
        h = relu(h_pre)
        gh = g @ w2.T
        gw2 = h.T @ g
        gb2 = g.sum(axis=0)
        g_pre = gh * (h_pre > 0)
        gx = g_pre @ w1.T
        gw1 = x_in.T @ g_pre
        gb1 = g_pre.sum(axis=0)
        grads[i] = (gw1, gb1, gw2, gb2)
        g = gx
    return g, grads
```

### 단계 3: k레이어마다 체크포인트

```python
def model_forward_checkpointed(x, params, k=4):
    saved_inputs = [x]
    h = x
    for i, (w1, b1, w2, b2) in enumerate(params):
        h = layer_forward(h, w1, b1, w2, b2)
        if (i + 1) % k == 0:
            saved_inputs.append(h)
    return h, saved_inputs


def model_backward_checkpointed(grad_output, saved_inputs, params, k=4):
    grads = [None] * len(params)
    g = grad_output
    segments = [(j * k, min((j + 1) * k, len(params))) for j in range(len(saved_inputs))]
    for seg_idx in range(len(saved_inputs) - 1, -1, -1):
        start, end = segments[seg_idx]
        if start >= end:
            continue
        x_in = saved_inputs[seg_idx]
        _, seg_acts = model_forward(x_in, params[start:end])
        g, seg_grads = model_backward(g, seg_acts, params[start:end])
        for j, gr in enumerate(seg_grads):
            grads[start + j] = gr
    return g, grads
```

### 단계 4: 비용 모델

```python
def checkpoint_cost(n_layers, segment_size, flops_per_layer=1.0):
    fwd = n_layers * flops_per_layer
    recompute = n_layers * flops_per_layer
    bwd = 2 * n_layers * flops_per_layer
    return {
        "fwd": fwd,
        "recompute": recompute,
        "bwd": bwd,
        "total": fwd + recompute + bwd,
        "overhead_vs_no_ckpt": (fwd + recompute + bwd) / (fwd + bwd) - 1.0,
    }


def selective_checkpoint_cost(n_layers, attention_fraction=0.15,
                              flops_per_layer=1.0):
    fwd = n_layers * flops_per_layer
    recompute = n_layers * attention_fraction * flops_per_layer
    bwd = 2 * n_layers * flops_per_layer
    return {
        "fwd": fwd,
        "recompute": recompute,
        "bwd": bwd,
        "total": fwd + recompute + bwd,
        "overhead_vs_no_ckpt": (fwd + recompute + bwd) / (fwd + bwd) - 1.0,
    }
```

### 단계 5: 메모리 추정기

```python
def activation_memory_mb(n_layers, hidden=8192, seq=8192,
                        batch=1, bytes_per_value=2):
    per_layer = 12 * batch * seq * hidden * bytes_per_value
    return n_layers * per_layer / 1e6


def memory_after_checkpoint(n_layers, segment_size, hidden=8192,
                           seq=8192, batch=1, bytes_per_value=2):
    n_seg = max(1, n_layers // segment_size)
    saved = (n_seg + segment_size) * 1 * batch * seq * hidden * bytes_per_value
    return saved / 1e6
```

### 단계 6: 최적 구간 크기

```python
def optimal_segment(n_layers):
    return int(round(np.sqrt(n_layers)))
```

### 단계 7: 선택적 체크포인트 판단

```python
def should_recompute(layer_type, activation_bytes, recompute_flops_ratio):
    if layer_type == "attention" and activation_bytes > 100 * 1e6:
        return True
    if layer_type == "ffn" and activation_bytes > 500 * 1e6:
        return recompute_flops_ratio < 0.1
    return False
```

## 사용해 보기

- **torch.utils.checkpoint**: `from torch.utils.checkpoint import checkpoint` — PyTorch의 대표적인 래퍼. 함수를 감싸면 입력만 저장하고 역전파 때 재계산합니다.
- **Megatron-Core 활성값 재계산**: `selective`, `full`, `block` 모드를 지원합니다. 2024년 이후 프론티어 학습의 표준입니다.
- **FSDP2 오프로드**: FSDP2에서 `module.to_empty(device="cpu")`와 `offload_policy`를 쓰면 재계산 대신 활성값을 CPU로 샤딩합니다.
- **DeepSpeed ZeRO-Offload**: 옵티마이저 상태와 활성값을 CPU로 오프로드해 체크포인팅을 보완합니다.

## 출시하기

이 레슨은 `outputs/prompt-activation-recompute-policy.md`를 산출합니다. 모델 설정(레이어, 은닉, 시퀀스, 배치)과 사용 가능한 GPU 메모리를 받아 레이어별 재계산 정책(없음 / 선택적 / 전체 / 오프로드)을 내놓는 프롬프트입니다.

## 연습 문제

1. 정확성을 검증하세요. `model_forward` + `model_backward`(전체 활성값)와 `model_forward_checkpointed` + `model_backward_checkpointed`(구간 분할)를 실행해 비교하세요. 파라미터 그래디언트는 기계 정밀도까지 동일해야 합니다.

2. 구간 크기 `k`를 1부터 `L`까지 스윕하세요. FLOP 오버헤드와 메모리를 그래프로 그리고, 곡선의 무릎(knee) 지점을 찾으세요.

3. 선택적 체크포인팅을 구현하세요. 어텐션 모듈의 입력은 저장하되 중간값은 저장하지 않습니다. seq=8192인 32레이어 모델에서 레이어 전체 체크포인팅 대비 FLOP 오버헤드를 측정하세요.

4. 오프로드를 추가하세요. 구간 입력을 시뮬레이션된 "CPU 버퍼"(별도 리스트)에 저장합니다. 바이트/시간으로 "PCIe 대역폭"을 측정하고, 오프로드와 재계산의 손익분기점을 찾으세요.

5. 실제 PyTorch 트랜스포머를 `torch.utils.checkpoint` 사용/미사용으로 벤치마크하세요. 메모리(`torch.cuda.max_memory_allocated` 사용)와 단계 시간을 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| Gradient checkpointing | "순전파를 다시 해서 메모리 아끼기" | 구간 입력만 저장하고, 역전파 중 중간값을 재계산해 그래디언트 계산에 필요한 텐서를 되찾음 |
| Activation recomputation | "체크포인팅과 같은 것" | 같은 기법의 HPC(고성능 컴퓨팅)식 이름 |
| Segment size (k) | "체크포인트당 레이어 수" | 중간값을 함께 버리고 함께 다시 만드는 레이어 수 |
| Selective checkpointing | "Korthikanti의 비결" | 저장이 비싼 활성값(어텐션 소프트맥스)만 재계산하고 값싼 것은 유지 |
| Full checkpointing | "순진한 버전" | 모든 구간의 모든 레이어 중간값을 재계산 |
| Block checkpointing | "굵은 입자" | 트랜스포머 블록 전체를 체크포인트. 가장 큰 단위 |
| FLOP overhead | "연산 세금" | 단계당 추가 FLOPs = (재계산 FLOPs) / (순전파 + 역전파 FLOPs). 순진한 방식 33%, 선택적 5% |
| Activation offload | "CPU로 보내기" | 순전파->역전파 사이에 활성값을 CPU RAM으로 옮기기. 재계산의 대안 |
| sqrt-L rule | "고전적 최적해" | 비용이 균일한 레이어에서 최적 체크포인트 간격은 sqrt(L)레이어 |
| Attention-softmax volume | "O(L^2) 문제" | L^2 * heads * batch 개의 부동소수점 값. 긴 컨텍스트에서 활성값 메모리를 지배 |

## 더 읽을거리

- [Chen 외, 2016 -- "Training Deep Nets with Sublinear Memory Cost"](https://arxiv.org/abs/1604.06174) -- 그래디언트 체크포인팅을 정식화한 원조 논문
- [Korthikanti 외, 2022 -- "Reducing Activation Recomputation in Large Transformer Models"](https://arxiv.org/abs/2205.05198) -- 선택적 활성값 재계산과 공식 비용 분석
- [Pudipeddi 외, 2020 -- "Training Large Neural Networks with Constant Memory using a New Execution Algorithm"](https://arxiv.org/abs/2002.05645) -- 역방향 모드 재구체화를 통한 대안적 고정 메모리 접근법
- [Ren 외, 2021 -- "ZeRO-Offload: Democratizing Billion-Scale Model Training"](https://arxiv.org/abs/2101.06840) -- 대규모 활성값 오프로드
- [PyTorch torch.utils.checkpoint 문서](https://pytorch.org/docs/stable/checkpoint.html) -- 표준 API
- [Megatron-Core 활성값 재계산 문서](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/features/memory_optimizations.html) -- selective, full, block 모드
