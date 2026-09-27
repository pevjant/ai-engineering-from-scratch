> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 시퀀스-투-시퀀스 모델 (Sequence-to-Sequence Models)

> 번역기인 척하는 RNN 둘입니다. 이들이 부딪힌 병목이 바로 어텐션이 존재하는 이유입니다.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 5 · 08(텍스트를 위한 CNN + RNN), 페이즈 3 · 11(PyTorch 입문)
**소요 시간:** 약 75분

## 해결할 문제

분류는 길이가 가변적인 시퀀스를 레이블 하나로 바꿉니다. 번역은 길이가 가변적인 시퀀스를 또 다른 길이 가변 시퀀스로 바꿉니다. 입력과 출력은 서로 다른 어휘집(vocabulary), 어쩌면 서로 다른 언어에 살고 있고, 길이가 같다는 보장도 없습니다.

seq2seq 아키텍처(Sutskever, Vinyals, Le, 2014)는 일부러 단순하게 만든 레시피로 이 문제를 해부했습니다. RNN 둘. 하나는 원문 문장을 읽어 고정 크기 컨텍스트 벡터를 만들고, 다른 하나는 그 벡터를 읽어 대상 문장을 토큰 단위로 생성합니다. 레슨 08에서 짠 바로 그 코드를 다른 방식으로 접착한 것입니다.

이것을 공부할 가치가 있는 이유는 둘입니다. 첫째, 컨텍스트 벡터 병목은 NLP에서 가장 가르침이 깊은 실패입니다. 어텐션과 트랜스포머가 잘하는 모든 것의 동기를 부여합니다. 둘째, 학습 레시피(교사 강제, 스케줄 샘플링, 추론 시 빔 서치)는 LLM을 포함한 모든 현대 생성 시스템에 여전히 적용됩니다.

## 핵심 개념

**인코더.** 원문 문장을 읽는 RNN입니다. 최종 은닉 상태가 **컨텍스트 벡터**입니다. 입력 전체를 고정 크기로 요약한 것이죠. 원문을 잊는 대신 이것 하나만 남는다고 볼 수 있습니다.

**디코더.** 컨텍스트 벡터로 초기화되는 또 다른 RNN입니다. 매 단계에서 이전에 생성한 토큰을 입력으로 받고 대상 어휘집 위의 확률 분포를 만들어 냅니다. 샘플링이나 argmax로 다음 토큰을 고르고, 다시 입력으로 넣습니다. `<EOS>` 토큰이 나오거나 최대 길이에 닿을 때까지 반복합니다.

**학습:** 디코더의 매 단계에서 교차 엔트로피 손실을 계산해 시퀀스 전체에 걸쳐 더합니다. 두 네트워크를 관통하는 표준적인 시간편차 역전파(backprop through time)를 씁니다.

**교사 강제(teacher forcing).** 학습 중 디코더의 `t` 단계 입력은 디코더 자신의 이전 예측이 아니라 `t-1` 위치의 *정답* 토큰입니다. 이렇게 해야 학습이 안정됩니다. 없으면 초기 실수가 눈덩이처럼 불어나 모델이 끝내 배우지 못하죠. 추론 때는 모델 자신의 예측을 쓸 수밖에 없으므로 학습/추론 분포 사이 간극이 언제나 존재합니다. 이 간극을 **노출 편향(exposure bias)**이라고 부릅니다.

**병목.** 인코더가 원문에 대해 배운 모든 것이 그 하나의 컨텍스트 벡터에 짜여 들어가야 합니다. 긴 문장은 디테일을 잃고, 희귀 단어는 흐려지고, 어순 재배열(chat noir vs. black cat)은 계산이 아니라 암기로 처리해야 합니다.

어텐션(레슨 10)은 디코더가 마지막 상태만이 아니라 인코더의 *모든* 은닉 상태를 볼 수 있게 해서 이것을 고칩니다. 어필 포인트는 그게 전부입니다.

```figure
lstm-gates
```

## 만들어 보기

### 단계 1: 인코더

```python
import torch
import torch.nn as nn


class Encoder(nn.Module):
    def __init__(self, src_vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embed = nn.Embedding(src_vocab_size, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)

    def forward(self, src):
        e = self.embed(src)
        outputs, hidden = self.gru(e)
        return outputs, hidden
```

`outputs`의 모양은 `[batch, seq_len, hidden_dim]`입니다. 입력 위치마다 은닉 상태가 하나씩 있는 것이죠. `hidden`의 모양은 `[1, batch, hidden_dim]`입니다. 마지막 단계입니다. 레슨 08에서는 "분류를 위해 outputs 위에서 풀링하라"고 했죠. 여기서는 마지막 은닉 상태를 컨텍스트 벡터로 쓰고 단계별 출력은 무시합니다.

### 단계 2: 디코더

```python
class Decoder(nn.Module):
    def __init__(self, tgt_vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embed = nn.Embedding(tgt_vocab_size, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, tgt_vocab_size)

    def forward(self, token, hidden):
        e = self.embed(token)
        out, hidden = self.gru(e, hidden)
        logits = self.fc(out)
        return logits, hidden
```

디코더는 한 번에 한 단계씩 호출됩니다. 입력은 단일 토큰들로 이뤄진 배치와 현재 은닉 상태입니다. 출력은 다음 토큰을 위한 어휘집 로짓과 갱신된 은닉 상태입니다.

### 단계 3: 교사 강제를 곁들인 학습 루프

```python
def train_batch(encoder, decoder, src, tgt, bos_id, optimizer, teacher_forcing_ratio=0.9):
    optimizer.zero_grad()
    _, hidden = encoder(src)
    batch_size, tgt_len = tgt.shape
    input_token = torch.full((batch_size, 1), bos_id, dtype=torch.long)
    loss = 0.0
    loss_fn = nn.CrossEntropyLoss(ignore_index=0)

    for t in range(tgt_len):
        logits, hidden = decoder(input_token, hidden)
        step_loss = loss_fn(logits.squeeze(1), tgt[:, t])
        loss += step_loss
        use_teacher = torch.rand(1).item() < teacher_forcing_ratio
        if use_teacher:
            input_token = tgt[:, t].unsqueeze(1)
        else:
            input_token = logits.argmax(dim=-1)

    loss.backward()
    optimizer.step()
    return loss.item() / tgt_len
```

이름 붙일 가치가 있는 다이얼 두 개. `ignore_index=0`은 패딩 토큰은 손실 계산에서 건너뜁니다. `teacher_forcing_ratio`는 매 단계에서 모델 예측 대신 정답 토큰을 쓸 확률입니다. 1.0(완전 교사 강제)에서 시작해 학습이 진행되며 약 0.5까지 낮추면 노출 편향 간극을 좁힐 수 있습니다.

### 단계 4: 추론 루프(탐욕적)

```python
@torch.no_grad()
def greedy_decode(encoder, decoder, src, bos_id, eos_id, max_len=50):
    _, hidden = encoder(src)
    batch_size = src.shape[0]
    input_token = torch.full((batch_size, 1), bos_id, dtype=torch.long)
    output_ids = []
    for _ in range(max_len):
        logits, hidden = decoder(input_token, hidden)
        next_token = logits.argmax(dim=-1)
        output_ids.append(next_token)
        input_token = next_token
        if (next_token == eos_id).all():
            break
    return torch.cat(output_ids, dim=1)
```

탐욕적(greedy) 복호화는 매 단계에서 확률이 가장 높은 토큰을 고릅니다. 길을 잃을 수 있습니다. 토큰 하나를 확정하면 도로 말취소할 수는 없으니까요. **빔 서치(beam search)**는 상위 `k`개의 부분 시퀀스를 끝까지 살려 두고, 마지막에 가장 점수 높은 완성 시퀀스를 고릅니다. 빔 폭 3~5가 표준입니다.

### 단계 5: 병목, 실증 편

장난감 복사 과제로 모델을 학습시켜 보세요. 소스 `[a, b, c, d, e]`, 타깃 `[a, b, c, d, e]`. 시퀀스 길이를 늘려 가며 정확도를 관찰합니다.

```
seq_len=5   copy accuracy: 98%
seq_len=10  copy accuracy: 91%
seq_len=20  copy accuracy: 62%
seq_len=40  copy accuracy: 23%
```

GRU 은닉 상태 하나로 40토큰 입력을 무손실 암기할 수는 없습니다. 정보는 인코더의 매 단계에 살아 있지만, 디코더는 마지막 상태만 보니까요. 어텐션은 바로 이것을 직접 고칩니다.

## 활용하기

PyTorch에는 `nn.Transformer`와 `nn.LSTM` 기반 seq2seq 템플릿이 있습니다. Hugging Face의 `transformers` 라이브러리는 수십억 토큰으로 학습된 인코더-디코더 모델(BART, T5, mBART, NLLB)을 통째로 제공합니다.

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tok = AutoTokenizer.from_pretrained("facebook/bart-base")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-base")

src = tok("Translate this to French: Hello, how are you?", return_tensors="pt")
out = model.generate(**src, max_new_tokens=50, num_beams=4)
print(tok.decode(out[0], skip_special_tokens=True))
```

현대의 인코더-디코더는 RNN을 버리고 트랜스포머로 갈아탔습니다. 그러나 상위 수준의 모양(인코더, 디코더, 토큰 단위 생성)은 2014년 seq2seq 논문과 동일합니다. 각 블록 안의 메커니즘이 다를 뿐입니다.

### 아직도 RNN 기반 seq2seq를 쓸 때

새 프로젝트라면 거의 없습니다. 구체적인 예외는 다음과 같습니다.

- 입력을 토큰 단위로, 제한된 메모리로 소비하는 스트리밍 번역.
- 트랜스포머의 메모리 비용이 감당 안 되는 온디바이스 텍스트 생성.
- 교육. 인코더-디코더 병목을 이해하는 것이 트랜스포머가 왜 이겼는지 이해하는 가장 빠른 길입니다.

### 노출 편향과 그 완화책

- **스케줄 샘플링(scheduled sampling).** 학습 중 교사 강제 비율을 서서히 낮춰, 모델이 자기 실수에서 회복하는 법을 배우게 합니다.
- **최소 위험 학습(minimum risk training).** 토큰 수준 교차 엔트로피 대신 문장 수준 BLEU 점수로 학습합니다. 실제로 원하는 것에 더 가깝죠.
- **강화 학습 파인튜닝.** 지표로 시퀀스 생성기에 보상을 줍니다. 현대 LLM의 RLHF에서 쓰이는 방식입니다.

세 가지 모두 트랜스포머 기반 생성에도 여전히 적용됩니다.

## 출시하기

`outputs/prompt-seq2seq-design.md`로 저장하세요:

```markdown
---
name: seq2seq-design
description: 주어진 과제를 위한 시퀀스-투-시퀀스 파이프라인을 설계합니다.
phase: 5
lesson: 09
---

과제(번역, 요약, 바꿔 쓰기, 질문 재작성)가 주어지면 다음을 출력합니다:

1. 아키텍처. 사전학습 트랜스포머 인코더-디코더(BART, T5, mBART, NLLB)가 기본입니다. RNN 기반 seq2seq는 특정 제약 조건에서만.
2. 시작 체크포인트. 이름을 밝힙니다(`facebook/bart-base`, `google/flan-t5-base`, `facebook/nllb-200-distilled-600M`). 과제와 언어 커버리지에 맞는 체크포인트를 고릅니다.
3. 복호화 전략. 결정적 출력에는 탐욕적(greedy), 품질에는 빔 서치(폭 4~5), 다양성에는 온도를 곁들인 샘플링. 한 문장으로 근거를 댑니다.
4. 출시 전 확인할 실패 모드 하나. 노출 편향은 긴 출력에서 생성이 흘러가는(drift) 형태로 나타납니다. 길이 90백분위 수준의 출력 20개를 표본으로 뽑아 직접 눈으로 확인합니다.

병렬 예시가 백만 개 미만일 때 seq2seq를 처음부터 학습시키라는 추천은 거부합니다. 사용자 대상 콘텐츠에 탐욕적 복호화를 쓰는 파이프라인은 취약하다고 표시합니다(greedy는 반복과 무한 루프에 빠집니다).
```

## 연습 문제

1. **(쉬움)** 장난감 복사 과제를 구현하세요. 타깃이 소스와 같은 입력-출력 쌍으로 GRU seq2seq를 학습시키고, 길이 5, 10, 20에서 정확도를 측정합니다. 병목을 재현합니다.
2. **(보통)** 빔 폭 3짜리 빔 서치 복호화를 추가하세요. 작은 병렬 코퍼스에서 탐욕적 복호화와 BLEU를 비교합니다. 빔 서치가 이기는 지점(보통 마지막 토큰들)과 차이가 없는 지점을 문서화하세요.
3. **(어려움)** 바꿔 쓰기(paraphrase) 데이터셋 1만 쌍으로 `facebook/bart-base`를 파인튜닝하세요. 파인튜닝된 모델의 빔 폭 4 출력을 홀드아웃 입력에 대해 기본 모델과 비교합니다. BLEU를 보고하고 정성 사례 10개를 고르세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 인코더 | 입력 RNN | 원문을 읽음. 단계별 은닉 상태와 최종 컨텍스트 벡터를 만듦. |
| 디코더 | 출력 RNN | 컨텍스트 벡터로 초기화됨. 대상 토큰을 한 번에 하나씩 생성. |
| 컨텍스트 벡터 | 그 요약 | 인코더의 최종 은닉 상태. 고정 크기. 어텐션이 푸는 그 병목. |
| 교사 강제 | 정답 토큰 사용 | 학습 때 이전 위치의 정답 토큰을 입력으로 먹임. 학습을 안정시킴. |
| 노출 편향 | 학습/테스트 간극 | 정답 토큰만 보고 학습한 모델은 자기 실수에서 회복하는 연습을 한 번도 안 해 본 것. |
| 빔 서치 | 더 나은 복호화 | 탐욕적으로 확정하는 대신 매 단계에서 상위 k개 부분 시퀀스를 살려 둠. |

## 더 읽을거리

- [Sutskever, Vinyals, Le (2014). Sequence to Sequence Learning with Neural Networks](https://arxiv.org/abs/1409.3215) — seq2seq의 원 논문. 4페이지입니다.
- [Cho et al. (2014). Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation](https://arxiv.org/abs/1406.1078) — GRU와 인코더-디코더 프레임을 소개한 논문.
- [Bahdanau, Cho, Bengio (2014). Neural Machine Translation by Jointly Learning to Align and Translate](https://arxiv.org/abs/1409.0473) — 그 어텐션 논문. 이 레슨 직후에 바로 읽으세요.
- [PyTorch NLP from Scratch 튜토리얼](https://pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html) — 따라 만들 수 있는 seq2seq + 어텐션 코드.
