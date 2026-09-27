# 위치 인코딩 — 사인 계열, RoPE, ALiBi

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 어텐션은 순서를 구분하지 못합니다. "The cat sat on the mat"과 "mat the on sat cat the"은 위치 신호가 없으면 같은 출력을 냅니다. 이걸 고치는 알고리즘이 세 가지 있고, 각자 "위치"라는 말이 무엇을 뜻하는지에 대해 서로 다른 내기를 합니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 7 · 02 (셀프 어텐션), 페이즈 7 · 03 (멀티 헤드 어텐션)
**시간:** 약 45분

## 문제 상황

스케일드 닷프로덕트 어텐션은 순서에 눈이 없습니다. 어텐션 행렬 `softmax(Q K^T / √d) V`는 쌍별 유사도로 계산됩니다. `X`의 행들을 섞으면 출력의 행들도 똑같이 섞여 나옵니다. 어텐션 내부 어디에도 위치를 신경 쓰는 부분이 없습니다.

단어 모음(bag-of-words) 모델이라면 이건 버그가 아닙니다. 하지만 언어, 코드, 오디오, 비디오처럼 순서가 의미를 지니는 모든 것에서 이건 치명적입니다.

해법은 위치를 임베딩에 어떻게든 주입하는 것입니다. 세 시대의 답:

1. **절대 사인 기반** (Vaswani 2017). 위치의 `sin/cos` 값을 임베딩에 더합니다. 단순하고, 학습이 필요 없지만, 학습 길이를 넘어서는 외삽이 잘 안 됩니다.
2. **RoPE — Rotary Position Embeddings** (Su 2021). Q와 K 벡터를 위치에 비례하는 각도로 회전시킵니다. 닷프로덕트 안에 *상대* 위치를 직접 인코딩합니다. 2026년의 지배적 선택입니다.
3. **ALiBi — Attention with Linear Biases** (Press 2022). 임베딩을 아예 건드리지 않고, 거리에 비례하는 헤드별 선형 패널티를 어텐션 점수에 더합니다. 길이 외삽이 훌륭합니다.

2026년 기준으로 사실상 모든 프론티어 오픈 모델이 RoPE를 씁니다: Llama 2/3/4, Qwen 2/3, Mistral, Mixtral, DeepSeek-V3, Kimi. 일부 장기 컨텍스트 모델이 ALiBi나 그 현대 변형을 씁니다. 절대 사인 기반은 역사 속으로 갔습니다.

## 핵심 개념

![절대 사인 vs RoPE 회전 vs ALiBi 거리 편향](../assets/positional-encoding.svg)

### 절대 사인 기반

`(max_len, d_model)` 모양의 고정 행렬 `PE`를 미리 계산합니다:

```
PE[pos, 2i]   = sin(pos / 10000^(2i / d_model))
PE[pos, 2i+1] = cos(pos / 10000^(2i / d_model))
```

그다음 어텐션 전에 `X' = X + PE[:N]`을 계산합니다. 각 차원은 서로 다른 주파수의 사인파입니다. 모델은 위상 패턴에서 위치를 읽어 내는 법을 배웁니다. `max_len`을 넘으면 실패합니다. 0~2047 위치만 본 모델에게 2048 위치에서 무슨 일이 일어나는지 알려 준 적이 없으니까요.

### RoPE

Q와 K 벡터(임베딩이 아님)를 회전시킵니다. 차원 쌍 `(2i, 2i+1)`에 대해:

```
[q'_2i    ]   [ cos(pos·θ_i)  -sin(pos·θ_i) ] [q_2i   ]
[q'_2i+1  ] = [ sin(pos·θ_i)   cos(pos·θ_i) ] [q_2i+1 ]

θ_i = base^(-2i / d_head),  base = 10000 by default
```

위치 `pos_k`인 키에도 같은 회전을 적용합니다. 그러면 닷프로덕트 `q'_m · k'_n`이 `(m - n)`만의 함수가 됩니다. 즉 **어텐션 점수가 오직 상대 거리에만 의존합니다.** 회전은 절대 위치를 기준으로 하면서도 말이죠. 아름다운 트릭입니다.

RoPE 확장: `base`를 조절하면(NTK-aware, YaRN, LongRoPE) 재학습 없이 더 긴 컨텍스트로 외삽할 수 있습니다. Llama 3가 이 방식으로 8K에서 128K 컨텍스트로 늘렸습니다.

### ALiBi

임베딩 트릭을 건너뛰고 어텐션 점수에 직접 편향을 더합니다:

```
attn_score[i, j] = (q_i · k_j) / √d  -  m_h · |i - j|
```

여기서 `m_h`는 헤드별 기울기입니다(예: `1 / 2^(8·h/H)`). 가까운 토큰은 점수가 올라가고 먼 토큰은 깎입니다. 학습 시점 비용이 없습니다. 논문은 길이 외삽이 사인 기반을 이기고, 원래 학습 길이에서는 RoPE에 필적한다고 보여 줍니다.

### 2026년에 뭘 고를까

| 변형 | 외삽 | 학습 비용 | 사용처 |
|---------|---------------|---------------|---------|
| 절대 사인 기반 | 나쁨 | 없음 | 원조 트랜스포머, 초기 BERT |
| 학습형 절대 | 없음 | 아주 작음 | GPT-2, GPT-3 |
| RoPE | 스케일링과 함께면 좋음 | 없음 | Llama 2/3/4, Qwen 2/3, Mistral, DeepSeek-V3, Kimi |
| RoPE + YaRN | 훌륭함 | 파인튜닝 단계 | Qwen2-1M, Llama 3.1 128K |
| ALiBi | 훌륭함 | 없음 | BLOOM, MPT, Baichuan |

RoPE가 이긴 이유는 아키텍처를 바꾸지 않고도 어텐션에 끼워 넣어지고, 상대 위치를 인코딩하며, `base` 하이퍼파라미터가 장기 컨텍스트 파인튜닝에 깔끔한 조절 손잡이를 주기 때문입니다.

```figure
rope-explorer
```

## 만들어 보기

### 단계 1: 사인 기반 인코딩

`code/main.py`를 보세요. 4줄짜리 계산입니다:

```python
def sinusoidal(N, d):
    pe = [[0.0] * d for _ in range(N)]
    for pos in range(N):
        for i in range(d // 2):
            theta = pos / (10000 ** (2 * i / d))
            pe[pos][2 * i]     = math.sin(theta)
            pe[pos][2 * i + 1] = math.cos(theta)
    return pe
```

이 값을 첫 어텐션 층 전에 임베딩 행렬에 더합니다.

### 단계 2: Q, K에 RoPE 적용

RoPE는 Q와 K를 제자리에서 다룹니다. 각 차원 쌍에 대해:

```python
def apply_rope(x, pos, base=10000):
    d = len(x)
    out = list(x)
    for i in range(d // 2):
        theta = pos / (base ** (2 * i / d))
        c, s = math.cos(theta), math.sin(theta)
        a, b = x[2 * i], x[2 * i + 1]
        out[2 * i]     = a * c - b * s
        out[2 * i + 1] = a * s + b * c
    return out
```

핵심: 위치 `m`의 Q와 위치 `n`의 K에 같은 함수를 적용해야 합니다. 그러면 두 벡터의 닷프로덕트가 모든 좌표 쌍에 걸쳐 `cos((m-n)·θ_i)` 인자를 얻습니다. 어텐션이 상대 위치를 공짜로 배우게 됩니다.

### 단계 3: ALiBi 기울기와 편향

```python
def alibi_bias(n_heads, seq_len):
    # slope_h = 2 ** (-8 * h / n_heads) for h = 1..n_heads
    slopes = [2 ** (-8 * (h + 1) / n_heads) for h in range(n_heads)]
    bias = []
    for m in slopes:
        row = [[-m * abs(i - j) for j in range(seq_len)] for i in range(seq_len)]
        bias.append(row)
    return bias  # 소프트맥스 전에 어텐션 점수에 더한다
```

헤드 `h`의 `(seq_len, seq_len)` 어텐션 점수 행렬에 `bias[h]`를 더한 뒤 소프트맥스를 씁니다.

### 단계 4: RoPE의 상대 거리 성질 검증하기

무작위 벡터 `a, b`를 고릅니다. `(pos_a, pos_b)`로 회전한 다음, `(pos_a + k, pos_b + k)`로 회전합니다. 두 닷프로덕트는 부동소수점 오차 이내로 일치해야 합니다. 이 성질이 RoPE의 전부입니다 — 절대 오프셋에는 불변이고 상대 간격만 중요합니다.

## 활용하기

PyTorch 2.5+는 `torch.nn.functional`에 RoPE 유틸리티를 싣고 있습니다. 대부분의 프로덕션 코드는 `flash_attn`이나 `xformers`를 쓰며, 거기서는 RoPE가 어텐션 커널 안쪽에서 적용됩니다.

```python
from transformers import AutoModel
model = AutoModel.from_pretrained("meta-llama/Llama-3.2-3B")
# model.config.rope_scaling → {"type": "yarn", "factor": 32.0, "original_max_position_embeddings": 8192}
```

**2026년의 장기 컨텍스트 트릭:**

- **NTK-aware 보간.** 4K에서 16K 이상으로 늘릴 때 `base`를 `base * (scale_factor)^(d/(d-2))`로 다시 스케일합니다.
- **YaRN.** 장기 컨텍스트에서 어텐션 엔트로피를 보존하는 더 똑똑한 보간입니다. Llama 3.1 128K가 씁니다.
- **LongRoPE.** 진화 탐색으로 차원별 스케일 팩터를 고르는 Microsoft의 2024년 기법. Phi-3-Long이 씁니다.
- **위치 보간 + 파인튜닝.** 위치를 확장 배수만큼 줄이고 1~5B 토큰으로 파인튜닝합니다. 의외로 효과가 좋습니다.

## 출시하기

`outputs/skill-positional-encoding-picker.md`를 보세요. 이 스킬은 목표 컨텍스트 길이, 외삽 요구, 학습 예산이 주어진 새 모델에 인코딩 전략을 골라 줍니다.

## 연습 문제

1. **쉬움.** `max_len=512, d=128` 사인 `PE` 행렬을 히트맵으로 그려 보세요. "차원 인덱스가 커질수록 줄무늬가 넓어진다"는 패턴을 확인합니다.
2. **보통.** NTK-aware RoPE 스케일링을 구현합니다. 길이 256 시퀀스로 아주 작은 언어 모델을 학습한 뒤, 스케일링을 켠 경우와 끈 경우 각각 길이 1024에서 테스트합니다. 퍼플렉시티를 측정합니다.
3. **어려움.** 같은 어텐션 모듈 안에 ALiBi와 RoPE를 모두 구현합니다. 길이 512 시퀀스 복사 과제로 4층 트랜스포머를 학습하고, 테스트 때 2048로 외삽합니다. 성능 저하를 비교합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 위치 인코딩 | "어텐션에게 순서를 알려 준다" | 위치를 인코딩하기 위해 임베딩이나 어텐션에 더하는 모든 신호. |
| 사인 기반 (Sinusoidal) | "원조" | 기하급수적 주파수의 `sin/cos`를 임베딩에 더하는 방식; 외삽이 안 된다. |
| RoPE | "회전 임베딩" | Q, K를 위치 의존 각도로 회전; 닷프로덕트가 상대 거리를 인코딩한다. |
| ALiBi | "선형 편향 트릭" | 어텐션 점수에 `-m·\|i-j\|`를 더함; 임베딩이 필요 없고 외삽이 뛰어나다. |
| base | "RoPE의 손잡이" | RoPE의 주파수 스케일러; 추론 때 컨텍스트를 늘리려면 값을 올린다. |
| NTK-aware | "RoPE 스케일링 트릭" | 컨텍스트를 늘릴 때 고주파 차원이 눌리지 않도록 `base`를 다시 스케일한다. |
| YaRN | "고급스러운 것" | 어텐션 엔트로피를 보존하는 차원별 보간+외삽. |
| 외삽 (Extrapolation) | "학습 길이 너머에서도 동작" | 학습에서 본 `max_len`을 넘어서도 위치 방식이 올바른 출력을 내는가? |

## 더 읽을거리

- [Vaswani et al. (2017). Attention Is All You Need §3.5](https://arxiv.org/abs/1706.03762) — 원조 사인 기반 인코딩.
- [Su et al. (2021). RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864) — RoPE 논문.
- [Press, Smith, Lewis (2021). Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation](https://arxiv.org/abs/2108.12409) — ALiBi.
- [Peng et al. (2023). YaRN: Efficient Context Window Extension of Large Language Models](https://arxiv.org/abs/2309.00071) — RoPE 스케일링의 최고 수준.
- [Chen et al. (2023). Extending Context Window of Large Language Models via Positional Interpolation](https://arxiv.org/abs/2306.15595) — Meta의 Llama 2 장기 컨텍스트 논문.
- [Ding et al. (2024). LongRoPE: Extending LLM Context Window Beyond 2 Million Tokens](https://arxiv.org/abs/2402.13753) — Phi-3-Long이 쓰고 활용하기 섹션에서 언급된 Microsoft 기법.
- [HuggingFace Transformers — `modeling_rope_utils.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/modeling_rope_utils.py) — 모든 RoPE 스케일링 방식(default, linear, dynamic, YaRN, LongRoPE, Llama-3)의 프로덕션급 구현.
