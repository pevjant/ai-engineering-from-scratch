> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 트랜스포머 밑바닥부터 만들기 — 캡스톤

> 레슨 13개. 모델 하나. 지름길은 없습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 7 · 01부터 13까지. 건너뛰지 마세요.
**시간:** 약 120분

## 문제 상황

논문은 다 읽었습니다. 어텐션, 멀티헤드 분할, 위치 인코딩, 인코더와 디코더 블록, BERT와 GPT 손실, MoE, KV 캐시까지 구현했습니다. 이제 이것들을 실제 과제 하나에서 함께 작동하게 만들 차례입니다.

캡스톤 과제: 문자 단위 언어 모델링 과제에서 작은 디코더 전용 트랜스포머를 엔드투엔드로 학습시키는 것입니다. 셰익스피어를 읽고, 새로운 셰익스피어를 만들어 냅니다. 노트북에서 10분 안에 학습할 수 있을 만큼 작습니다. 더 큰 데이터셋과 더 긴 학습만 갈아 끼워도 진짜 언어 모델이 되는 수준으로 정확합니다.

이것이 이 코스의 'nanoGPT'입니다. 독창적인 것은 아닙니다 — Karpathy의 2023년 nanoGPT 튜토리얼은 학습자가 누구나 한 번쯤 써 보는 레퍼런스 구현입니다. 우리는 그 형태를 가져와 지금까지 배운 내용에 맞게 다시 무장합니다.

## 개념

![밑바닥부터 만드는 트랜스포머 블록 다이어그램](../assets/capstone.svg)

주석을 단 아키텍처:

```
input tokens (B, N)
   │
   ▼
token embedding + positional embedding  ◀── Lesson 04 (RoPE option)
   │
   ▼
┌──── block × L ────────────────────┐
│  RMSNorm                          │  ◀── Lesson 05
│  MultiHeadAttention (causal)      │  ◀── Lesson 03 + 07 (causal mask)
│  residual                         │
│  RMSNorm                          │
│  SwiGLU FFN                       │  ◀── Lesson 05
│  residual                         │
└────────────────────────────────── ┘
   │
   ▼
final RMSNorm
   │
   ▼
lm_head (tied to token embedding)
   │
   ▼
logits (B, N, V)
   │
   ▼
shift-by-one cross-entropy            ◀── Lesson 07
```

### 우리가 만드는 것

- `GPTConfig` — 모든 하이퍼파라미터를 설정하는 단 하나의 장소.
- `MultiHeadAttention` — 인과(causal) 마스크, 배치 처리, 선택적 Flash 스타일 경로(PyTorch의 `scaled_dot_product_attention`).
- `SwiGLUFFN` — 모던한 FFN.
- `Block` — 프리-노름(pre-norm), 잔차로 감싼 어텐션 + FFN.
- `GPT` — 임베딩, 쌓은 블록, LM 헤드, generate().
- AdamW, 코사인 LR, 그래디언트 클리핑이 들어간 학습 루프.
- 셰익스피어 텍스트 기반 문자 수준 토크나이저.

### 우리가 만들지 않는 것

- RoPE — 개념은 레슨 04에서 구현했습니다. 여기서는 단순함을 위해 학습되는 위치 임베딩을 씁니다. 연습 문제에서 RoPE로 바꿔 보라고 요청합니다.
- 생성 중 KV 캐시 — 생성 단계마다 접두사 전체에 대한 어텐션을 다시 계산합니다. 느리지만 단순합니다. 연습 문제에서 KV 캐시 추가를 요청합니다.
- Flash Attention — 입력 조건이 맞으면 PyTorch 2.0+가 자동으로 보내 줍니다; 우리는 `F.scaled_dot_product_attention`을 씁니다.
- MoE — 블록당 FFN 하나입니다. MoE는 레슨 11에서 봤습니다.

### 목표 지표

Mac M2 노트북에서 4층, 4헤드, d_model=128짜리 GPT를 `tinyshakespeare.txt`로 2,000 스텝 학습하면:

- 학습 손실이 약 4.2(무작위)에서 약 1.5까지 약 6분 만에 수렴합니다.
- 샘플링한 출력이 셰익스피어답게 보입니다: 고풍스러운 단어, 줄바꿈, "ROMEO:" 같은 고유명사가 나타납니다.
- 검증 손실(텍스트 마지막 10% 홀드아웃)이 학습 손실을 밀착해 따라갑니다; 이 크기/예산에서는 과적합이 없습니다.

```figure
n5-block-stack
```

## 만들어 보기

이 레슨은 PyTorch를 씁니다. `torch`를 설치하세요(CPU 빌드로 충분합니다). `code/main.py`를 보세요. 스크립트가 처리하는 것들:

- `tinyshakespeare.txt`가 없으면 다운로드(또는 로컬 사본 읽기).
- 바이트 수준 문자 토크나이저.
- 90/10 학습/검증 분할.
- 지원 하드웨어에서 bf16 autocast가 들어간 학습 루프.
- 학습 완료 후 샘플링.

### 단계 1: 데이터

```python
text = open("tinyshakespeare.txt").read()
chars = sorted(set(text))
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for c, i in stoi.items()}
encode = lambda s: [stoi[c] for c in s]
decode = lambda xs: "".join(itos[x] for x in xs)
```

고유 문자 65개. 아주 작은 어휘. vocab_size 4바이트에도 들어갑니다. BPE도, 토크나이저 골치 아픈 일도 없습니다.

### 단계 2: 모델

`code/main.py`를 보세요. 블록은 레슨 05의 교과서 그대로입니다 — 프리-노름, RMSNorm, SwiGLU, 인과 MHA. 4/4/128 기준 파라미터 수: 약 80만 개.

### 단계 3: 학습 루프

길이 256짜리 토큰 윈도우를 무작위 배치로 가져옵니다. 순전파. 한 칸 밀린(shift-by-one) 교차 엔트로피. 역전파. AdamW 스텝. 로그. 반복.

```python
for step in range(max_steps):
    x, y = get_batch("train")
    logits = model(x)
    loss = F.cross_entropy(logits.view(-1, vocab_size), y.view(-1))
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    opt.zero_grad()
```

### 단계 4: 샘플링

프롬프트를 받으면 순전파를 반복하고, top-p 로짓에서 샘플링해 붙인 뒤 계속합니다. 500토큰 후에 멈춥니다.

### 단계 5: 출력 읽기

2,000 스텝 후:

```
ROMEO:
Away and mild will not thy friend, that thou shalt wit:
The chief that well shame and hath been his friends,
...
```

셰익스피어는 아니지만, 셰익스피어 같은 모양입니다. 노트북에서 약 80만 파라미터와 6분으로 낼 수 있는 확실한 승리입니다.

## 사용해 보기

이 캡스톤은 레퍼런스 아키텍처입니다. 진짜 물건으로 만들 확장 세 가지:

1. **토크나이저 교체.** BPE를 쓰세요(예: `tiktoken.get_encoding("cl100k_base")`). 어휘 크기가 65에서 약 50,000으로 뜁니다. 이를 보상하려면 모델 용량도 키워야 합니다.
2. **더 큰 코퍼스로 학습.** `OpenWebText`나 `fineweb-edu`(HuggingFace)를 쓰세요. A100 한 대에서 125M 파라미터 GPT로 10B 토큰을 학습하는 데 약 24시간 걸립니다.
3. **RoPE + KV 캐시 + Flash Attention 추가.** 아래 연습 문제가 각각을 안내합니다.

이렇게 하면 유창한 영어를 생성하는 125M 파라미터 GPT가 됩니다. 최전선 모델은 아닙니다. 하지만 같은 코드 경로를 더 크게 만든 것이 2026년 현재 Karpathy, EleutherAI, Allen 연구소가 연구용 체크포인트를 학습시키는 방법입니다.

## 출시하기

`outputs/skill-transformer-review.md`를 보세요. 이 스킬은 밑바닥부터 만든 트랜스포머 구현을 앞선 13개 레슨 전체 기준으로 정확성을 검토합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 학습한 모델의 마지막 스텝 검증 손실이 2.0 미만인지 확인합니다. `max_steps`를 2,000에서 5,000으로 바꾸면 — 검증 손실이 계속 좋아지나요?
2. **보통.** 학습되는 위치 임베딩을 RoPE로 교체하세요. `MultiHeadAttention` 안에서 Q와 K에 회전을 적용합니다. 학습 후 검증 손실이 최소한 같거나 낮은지 확인합니다.
3. **보통.** 샘플링 루프에 KV 캐시를 구현하세요. 캐시 있음/없음으로 각각 500토큰을 생성합니다. 노트북에서 벽시계 시간이 5~20배 좋아져야 합니다.
4. **어려움.** 다다음 토큰을 예측하는 두 번째 헤드를 모델에 추가하세요(DeepSeek-V3의 MTP — Multi-Token Prediction). 함께 학습시킵니다. 도움이 되나요?
5. **어려움.** 블록당 FFN 하나를 4전문가 MoE로 교체하세요. 라우터 + top-2 라우팅입니다. 활성 파라미터를 맞춘 상태에서 검증 손실이 어떻게 바뀌는지 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| nanoGPT | "Karpathy의 튜토리얼 저장소" | 최소한의 디코더 전용 트랜스포머 학습 코드, 약 300줄; 정석 레퍼런스. |
| tinyshakespeare | "표준 장난감 코퍼스" | 약 1.1 MB 텍스트; 2015년 이후 모든 문자-LM 튜토리얼이 사용합니다. |
| 결합 임베딩(Tied embeddings) | "입력/출력 행렬 공유" | LM 헤드 가중치 = 토큰 임베딩 행렬의 전치; 파라미터를 아끼고 품질을 높입니다. |
| bf16 autocast | "학습 정밀도 트릭" | 순전파/역전파는 bf16으로, 옵티마이저 상태는 fp32로 유지; 2021년 이후 표준. |
| 그래디언트 클리핑 | "스파이크를 막음" | 전역 그래디언트 노름을 1.0으로 제한; 학습 폭발을 막습니다. |
| 코사인 LR 스케줄 | "2020년 이후 기본값" | LR이 선형으로 상승(웜업)한 뒤 코사인 모양으로 감소해 피크의 10%까지 내려갑니다. |
| MFU | "Model FLOP Utilization" | 달성 FLOPs / 이론적 피크; 2026년 기준 덴스 40%, MoE 30%면 강력합니다. |
| 검증 손실(Val loss) | "홀드아웃 손실" | 모델이 한 번도 본 적 없는 데이터에 대한 교차 엔트로피; 과적합 감지기. |

## 더 읽을거리

- [The Annotated Transformer (Harvard NLP)](https://nlp.seas.harvard.edu/annotated-transformer/) — 고전적인 주석 달린 구현.
