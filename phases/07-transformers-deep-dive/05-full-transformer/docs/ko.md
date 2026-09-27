# 완전한 트랜스포머 — 인코더 + 디코더

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 어텐션이 주인공입니다. 나머지 — 잔차 연결(residual), 정규화, 피드포워드, 크로스 어텐션 — 은 어텐션을 깊게 쌓을 수 있게 돕는 비계입니다.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 7 · 02 (셀프 어텐션), 페이즈 7 · 03 (멀티 헤드 어텐션), 페이즈 7 · 04 (위치 인코딩)
**시간:** 약 75분

## 문제 상황

어텐션 층 하나는 모델이 아니라 특성(feature) 추출기입니다. 층마다 행렬 곱셈 한 번으로는 언어를 담기에 용량이 부족합니다. 깊이가 필요한데, 올바른 설비가 없으면 깊이는 곧바로 무너집니다.

2017년 Vaswani 논문은 어텐션 층 하나를 쌓을 수 있는 블록으로 바꿔 주는 여섯 가지 설계 결정을 묶어 발표했습니다. 그 이후의 모든 트랜스포머 — 인코더 전용(BERT), 디코더 전용(GPT), 인코더-디코더(T5) — 는 같은 골격을 물려받습니다. 2026년에는 블록이 정교해졌지만(RMSNorm, SwiGLU, pre-norm, RoPE) 골격은 완전히 같습니다.

이 레슨이 그 골격입니다. 다음 레슨들이 각자의 방향으로 특화합니다 — 06은 인코더, 07은 디코더, 08은 인코더-디코더입니다.

## 핵심 개념

![인코더와 디코더 블록 내부, 배선도](../assets/full-transformer.svg)

### 여섯 조각

1. **임베딩 + 위치 신호.** 토큰 → 벡터. 위치는 RoPE(현대) 또는 사인 기반(고전)으로 주입합니다.
2. **셀프 어텐션.** 모든 위치가 모든 위치를 주시합니다. 디코더에서는 마스킹됩니다.
3. **피드포워드 신경망(FFN).** 위치별 두 층 MLP: `W_2 · activation(W_1 · x)`. 확장 비율은 기본 4배입니다.
4. **잔차 연결(residual connection).** `x + sublayer(x)`. 이게 없으면 약 6층을 넘어서 기울기가 사라집니다.
5. **층 정규화.** `LayerNorm` 또는 `RMSNorm`(현대). 잔차 스트림을 안정화합니다.
6. **크로스 어텐션(디코더 전용).** 쿼리는 디코더에서, 키와 값은 인코더 출력에서 옵니다.

벡터 하나가 블록 하나를 통과하는 모습을 지켜 보세요: 어텐션이 위치들 사이에서 섞고, 잔차가 그것을 앞으로 전달하고, FFN이 변형하고, 정규화가 스트림을 안정적으로 유지합니다.

```figure
transformer-block
```

### 인코더 블록 (BERT, T5 인코더가 사용)

```
x → LN → MHA(self) → + → LN → FFN → + → out
                     ^              ^
                     |              |
                     └── residual ──┘
```

인코더는 양방향입니다. 마스킹이 없습니다. 모든 위치가 모든 위치를 봅니다.

### 디코더 블록 (GPT, T5 디코더가 사용)

```
x → LN → MHA(masked self) → + → LN → MHA(cross to encoder) → + → LN → FFN → + → out
```

디코더는 블록당 세 개의 하위 층을 갖습니다. 가운데 것 — 크로스 어텐션 — 이 정보가 인코더에서 디코더로 흐르는 유일한 통로입니다. 순수 디코더 전용 아키텍처(GPT)에서는 크로스 어텐션이 빠지고, 마스킹된 셀프 어텐션 + FFN만 남습니다.

### Pre-norm vs post-norm

원래 논문은 `x + sublayer(LN(x))` vs `LN(x + sublayer(x))` 두 가지를 다뤘습니다. Post-norm은 2019년 무렵 외면받기 시작했습니다 — 신중한 워밍업 없이 깊게 학습하기 어렵기 때문입니다. Pre-norm(하위 층 *앞에* `LN`)이 2026년의 기본값입니다: Llama, Qwen, GPT-3+, Mistral이 모두 씁니다.

### 2026년의 현대화된 블록

Vaswani 2017은 LayerNorm + ReLU를 실었습니다. 현대 스택은 둘 다 바꿨습니다. 프로덕션 블록의 실제 모습:

| 구성 요소 | 2017 | 2026 |
|-----------|------|------|
| 정규화 | LayerNorm | RMSNorm |
| FFN 활성화 | ReLU | SwiGLU |
| FFN 확장 비율 | 4배 | 2.6배 (SwiGLU는 행렬 세 개를 쓰므로 총 파라미터가 맞춰짐) |
| 위치 | 절대 사인 기반 | RoPE |
| 어텐션 | 풀 MHA | GQA (또는 MLA) |
| 바이어스 항 | 있음 | 없음 |

RMSNorm은 LayerNorm의 평균 중심화를 뺀 것입니다(뺄셈 하나 절약) — 연산을 아끼고, 경험적으로 최소한만큼은 안정적입니다. SwiGLU(`Swish(W1 x) ⊙ W3 x`)는 Llama, PaLM, Qwen 논문들에서 ReLU/GELU FFN보다 꾸준히 약 0.5포인트 좋은 ppl을 보였습니다.

### 파라미터 수 세기

`d_model = d`, FFN 확장 비율 `r`인 블록 하나:

- MHA: `4 · d²` (Q, K, V, O 프로젝션)
- FFN (SwiGLU): `3 · d · (r · d)` ≈ `3rd²`
- 정규화: 무시할 수준

`d = 4096, r = 2.6, layers = 32` (대략 Llama 3 8B)이면 전체: `32 · (4·4096² + 3·2.6·4096²) ≈ 32 · (16 + 32) M = ~1.5B parameters per layer × 32 ≈ 7B` (임베딩과 출력 헤드는 별도). 공개된 수치와 맞습니다.

## 만들어 보기

### 단계 1: 빌딩 블록들

레슨 03의 작은 `Matrix` 클래스를 사용합니다(독립성을 위해 이 파일에 복사됨):

- `layer_norm(x, eps=1e-5)` — 평균을 빼고 표준편차로 나눕니다.
- `rms_norm(x, eps=1e-6)` — RMS로 나눕니다. 평균 빼기 없음.
- `gelu(x)`와 `silu(x) * W3 x` (SwiGLU).
- `ffn_swiglu(x, W1, W2, W3)`.
- `encoder_block(x, params)`과 `decoder_block(x, enc_out, params)`.

전체 배선은 `code/main.py`를 보세요.

### 단계 2: 2층 인코더와 2층 디코더 배선하기

쌓아 올립니다. 인코더 출력을 디코더의 모든 크로스 어텐션에 넘깁니다. 출력 프로젝션 전에 마지막 LN을 하나 더합니다.

```python
def encode(tokens, params):
    x = embed(tokens, params.emb) + sinusoidal(len(tokens), params.d)
    for block in params.encoder_blocks:
        x = encoder_block(x, block)
    return x

def decode(target_tokens, encoder_out, params):
    x = embed(target_tokens, params.emb) + sinusoidal(len(target_tokens), params.d)
    for block in params.decoder_blocks:
        x = decoder_block(x, encoder_out, block)
    return x
```

### 단계 3: 장난감 예제로 순전파 돌리기

6토큰 소스와 5토큰 타깃을 통과시킵니다. 출력 모양이 `(5, vocab)`인지 확인합니다. 학습은 없습니다 — 이 레슨은 손실이 아니라 아키텍처에 관한 것이니까요.

### 단계 4: RMSNorm + SwiGLU로 교체하기

LayerNorm과 ReLU FFN을 RMSNorm과 SwiGLU로 바꿉니다. 모양이 여전히 맞는지 확인합니다. 함수 두 개만 바꾸면 끝나는 2026년의 현대화입니다.

## 활용하기

PyTorch/TF 기준 구현: `nn.TransformerEncoderLayer`, `nn.TransformerDecoderLayer`. 하지만 2026년 대부분의 프로덕션 코드는 자기 블록을 직접 만듭니다. 이유는:

- Flash Attention은 `nn.MultiheadAttention` 경유가 아니라 어텐션 안쪽에서 호출됩니다.
- GQA / MLA는 표준 라이브러리 기준 구현에 없습니다.
- RoPE, RMSNorm, SwiGLU는 PyTorch 기본값이 아닙니다.

HF `transformers`에는 읽어 볼 만한 깔끔한 기준 블록이 있습니다: `modeling_llama.py`는 2026년 디코더 전용 블록의 표준입니다. 약 500줄이고 한 번 훑어 볼 가치가 있습니다.

**인코더 vs 디코더 vs 인코더-디코더 — 언제 뭘 고르나:**

| 필요 | 선택 | 예시 |
|------|------|---------|
| 분류, 임베딩, 텍스트 기반 질의응답 | 인코더 전용 | BERT, DeBERTa, ModernBERT |
| 텍스트 생성, 채팅, 코드, 추론 | 디코더 전용 | GPT, Llama, Claude, Qwen |
| 구조화된 입력 → 구조화된 출력 (번역, 요약) | 인코더-디코더 | T5, BART, Whisper |

디코더 전용이 언어를 지배한 이유는 가장 깔끔하게 확장되고 이해와 생성을 모두 처리하기 때문입니다. 인코더-디코더는 입력에 명확한 "소스 시퀀스" 정체성이 있을 때(번역, 음성 인식, 구조화된 과제) 여전히 가장 좋습니다.

## 출시하기

`outputs/skill-transformer-block-reviewer.md`를 보세요. 이 스킬은 새 트랜스포머 블록 구현을 2026년 기본값과 비교해 검토하고 빠진 조각들(pre-norm, RoPE, RMSNorm, GQA, FFN 확장 비율)에 표시를 붙입니다.

## 연습 문제

1. **쉬움.** `d_model=512, n_heads=8, ffn_expansion=4, swiglu=True`에서 encoder_block의 파라미터 수를 세어 보세요. 블록을 직접 구현하고 `sum(p.numel() for p in block.parameters())`으로 검증합니다.
2. **보통.** Post-norm을 pre-norm으로 바꿔 봅니다. 둘 다 초기화한 뒤 무작위 입력을 12층에 통과시켜 활성화 노름을 측정합니다. Post-norm의 활성화는 폭발해야 하고, pre-norm은 유한해야 합니다.
3. **어려움.** 장난감 복사 과제(`x`를 뒤집어 복사)에서 4층 인코더-디코더를 구현합니다. 100스텝 학습하고 손실을 보고합니다. RMSNorm + SwiGLU + RoPE로 바꾸면 손실이 떨어지나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 블록 (Block) | "트랜스포머 층 하나" | 정규화 + 어텐션 + 정규화 + FFN을 잔차 연결로 감싼 묶음. |
| 잔차 (Residual) | "스킵 연결" | `x + f(x)` 출력; 깊은 스택을 통과하는 기울기 흐름을 가능하게 한다. |
| Pre-norm | "뒤가 아니라 앞에서 정규화" | 현대식: `x + sublayer(LN(x))`. 워밍업 요술 없이도 더 깊이 학습된다. |
| RMSNorm | "평균을 뺀 LayerNorm" | RMS로 나눈다; 연산 하나 덜 하되 경험적 안정성은 같다. |
| SwiGLU | "모두가 갈아탄 FFN" | `Swish(W1 x) ⊙ W3 x → W2`. LM ppl에서 ReLU/GELU를 이긴다. |
| 크로스 어텐션 | "디코더가 인코더를 보는 방법" | Q는 디코더에서, K/V는 인코더 출력에서 오는 MHA. |
| FFN 확장 비율 | "가운데 MLP가 얼마나 넓은가" | 은닉 크기와 d_model의 비율. 보통 4(LayerNorm) 또는 2.6(SwiGLU). |
| 바이어스 제거 | "+b 항을 뺀다" | 현대 스택은 선형 층의 바이어스를 뺀다; ppl이 약간 좋아지고 모델도 작아진다. |

## 더 읽을거리

- [Vaswani et al. (2017). Attention Is All You Need](https://arxiv.org/abs/1706.03762) — 원조 블록 명세.
- [Xiong et al. (2020). On Layer Normalization in the Transformer Architecture](https://arxiv.org/abs/2002.04745) — 깊게 쌓으면 pre-norm이 post-norm을 이기는 이유.
- [Zhang, Sennrich (2019). Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467) — RMSNorm.
- [Shazeer (2020). GLU Variants Improve Transformer](https://arxiv.org/abs/2002.05202) — SwiGLU 논문.
- [HuggingFace `modeling_llama.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py) — 2026년 디코더 전용 블록의 표준.
