> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 텍스트를 위한 CNN과 RNN (CNNs and RNNs for Text)

> 합성곱은 n-gram을 배우고, 순환 구조는 기억합니다. 둘 다 어텐션에게 자리를 내주었지만, 제약 걸린 하드웨어 위에서는 둘 다 여전히 유효합니다.

**유형:** 빌드 (Build)
**언어:** Python
**선수 지식:** 페이즈 3 · 11(PyTorch 입문), 페이즈 5 · 03(단어 임베딩), 페이즈 4 · 02(직접 구현하는 합성곱)
**소요 시간:** 약 75분

## 해결할 문제

TF-IDF와 Word2Vec은 단어 순서를 무시하는 평평한 벡터를 만들어 냈습니다. 이 위에 세운 분류기는 `dog bites man`과 `man bites dog`을 구분하지 못합니다. 그런데 단어 순서가 신호를 담고 있을 때가 있죠.

트랜스포머가 오기 전까지 그 간격을 메운 아키텍처 계열이 둘 있었습니다.

**텍스트용 합성곱 신경망(TextCNN).** 단어 임베딩 시퀀스 위에 1차원 합성곱을 적용합니다. 너비 3짜리 필터는 학습 가능한 트라이그램(trigram) 탐지기입니다. 세 단어에 걸쳐 점수 하나를 뱉죠. 서로 다른 너비(2, 3, 4, 5)를 쌓아 멀티스케일 패턴을 잡고, 맥스 풀링으로 고정 크기 표현을 만듭니다. 평평하고, 병렬적이고, 빠릅니다.

**순환 신경망(RNN, LSTM, GRU).** 토큰을 한 번에 하나씩 처리하면서, 정보를 앞으로 나르는 은닉 상태를 유지합니다. 순차적이고, 기억을 담고, 입력 길이가 유연합니다. 2014년부터 2017년까지 시퀀스 모델링을 지배하다가, 어텐션이 나타났습니다.

이 레슨은 둘 다 직접 만들고, 나서 어텐션을 낳게 된 그 실패의 이름을 붙입니다.

## 핵심 개념

**TextCNN**(Kim, 2014). 토큰을 임베딩합니다. 너비 `k`짜리 1차원 합성곱은 연속한 `k`개 임베딩 위를 필터로 미끄러지며 특성 맵(feature map)을 만듭니다. 그 맵 위의 전역 맥스 풀링이 가장 강한 활성화를 고릅니다. 여러 필터 너비에서 나온 맥스 풀링 출력을 이어 붙여 분류 헤드로 흘려보냅니다.

왜 되는 걸까요. 필터는 곧 학습 가능한 n-gram입니다. 맥스 풀링은 위치 불변이기 때문에, "not good"은 리뷰의 시작에서든 중간에서든 같은 특성을 발화합니다. 필터 너비 세 가지에 각 100개씩이면 학습된 n-gram 탐지기 300개를 얻습니다. 학습은 병렬입니다. 순차 의존이 없거든요.

**RNN.** 각 시점 `t`에서 은닉 상태는 `h_t = f(W * x_t + U * h_{t-1} + b)`입니다. `W`, `U`, `b`는 시점들에 걸쳐 공유됩니다. 시점 `T`의 은닉 상태는 전체 접두부(prefix)의 요약입니다. 분류에는 `h_1 ... h_T`를 풀링합니다(맥스, 평균, 또는 마지막 값).

단순 RNN은 그래디언트 소실에 시달립니다. **LSTM**은 무엇을 잊고, 무엇을 저장하고, 무엇을 출력할지 결정하는 게이트를 더해서 긴 시퀀스에서도 그래디언트를 안정시킵니다. **GRU**는 LSTM을 두 개 게이트로 단순화한 것으로, 파라미터가 더 적으면서 비슷한 성능을 냅니다.

**양방향 RNN**은 한 RNN은 순방향으로, 다른 RNN은 역방향으로 돌리고 은닉 상태를 이어 붙입니다. 모든 토큰의 표현이 왼쪽 맥락과 오른쪽 맥락을 모두 봅니다. 태깅 과제에는 필수입니다.

```figure
rnn-unroll
```

## 만들어 보기

### 단계 1: PyTorch로 TextCNN 만들기

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


class TextCNN(nn.Module):
    def __init__(self, vocab_size, embed_dim, n_classes, filter_widths=(2, 3, 4), n_filters=64, dropout=0.3):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, n_filters, kernel_size=k)
            for k in filter_widths
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(n_filters * len(filter_widths), n_classes)

    def forward(self, token_ids):
        x = self.embed(token_ids).transpose(1, 2)
        pooled = []
        for conv in self.convs:
            c = F.relu(conv(x))
            p = F.max_pool1d(c, c.size(2)).squeeze(2)
            pooled.append(p)
        h = torch.cat(pooled, dim=1)
        return self.fc(self.dropout(h))
```

`transpose(1, 2)`는 `[batch, seq_len, embed_dim]`을 `[batch, embed_dim, seq_len]`으로 바꿔 줍니다. `nn.Conv1d`가 가운데 축을 채널로 취급하기 때문입니다. 풀링된 출력은 입력 길이와 무관하게 고정 크기입니다.

### 단계 2: LSTM 분류기

```python
class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, n_classes, bidirectional=True, dropout=0.3):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)
        factor = 2 if bidirectional else 1
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * factor, n_classes)

    def forward(self, token_ids):
        x = self.embed(token_ids)
        out, _ = self.lstm(x)
        pooled = out.max(dim=1).values
        return self.fc(self.dropout(pooled))
```

마지막 상태가 아니라 시퀀스 전체에 맥스 풀링하세요. 분류에서는 맥스 풀링이 보통 마지막 은닉 상태를 택하는 것보다 낫습니다. 긴 시퀀스 끝의 정보가 마지막 상태를 장악하는 경향이 있거든요.

### 단계 3: 그래디언트 소실 데모(직관)

게이트 없는 단순 RNN은 장거리 의존성을 배우지 못합니다. 장난감 과제를 하나 떠올려 봅시다. 시퀀스 어딘가에 토큰 `A`가 등장했는지 맞히는 것입니다. `A`가 1번 위치에 있고 시퀀스 길이가 100이면, 손실에서 온 그래디언트는 순환 가중치 곱셈 99번을 거쳐 되돌아와야 합니다. 가중치가 1보다 작으면 그래디언트는 사라지고, 1보다 크면 폭발합니다.

```python
def vanishing_gradient_sim(seq_len, recurrent_weight=0.9):
    import math
    return math.pow(recurrent_weight, seq_len)


# 가중치 0.9로 100단계를 거치면:
#   0.9 ^ 100 ≈ 2.7e-5
# 100단계에서 1단계까지 흐르는 그래디언트는 사실상 0입니다.
```

LSTM은 **셀 상태(cell state)**로 이 문제를 고칩니다. 셀 상태는 네트워크를 덧셈적 상호작용만으로 흘러갑니다(망각 게이트가 곱셈으로 크기를 조절하지만, 그래디언트는 그래도 "고속도로"를 따라 흐릅니다). GRU는 더 적은 파라미터로 비슷한 일을 합니다. 둘 다 100단계가 넘는 시퀀스에서도 안정적인 학습을 가능하게 합니다.

### 단계 4: 그런데도 왜 부족했나

LSTM이 있어도 세 가지 문제가 남았습니다.

1. **순차 처리의 병목.** 길이 1000짜리 시퀀스로 RNN을 학습하려면 직렬 순전파/역전파를 1000번 밟아야 합니다. 시간 축으로는 병렬화할 수 없습니다.
2. **인코더-디코더 구성에서 고정 크기 컨텍스트 벡터.** 디코더는 인코더의 최종 은닉 상태, 즉 입력 전체를 압축한 것만 봅니다. 긴 입력은 디테일을 잃습니다. 레슨 09가 바로 이것을 다룹니다.
3. **원거리 의존성 정확도의 천장.** LSTM은 단순 RNN보다는 낫지만, 여전히 특정 정보를 200단계 이상 전달하는 데 애를 먹습니다.

어텐션이 이 세 가지를 모두 해결했습니다. 트랜스포머는 순환 구조를 완전히 버렸죠. 레슨 10이 그 분수령입니다.

## 활용하기

PyTorch의 `nn.LSTM`, `nn.GRU`, `nn.Conv1d`는 프로덕션 수준입니다. 학습 코드도 표준적인 방식으로 충분합니다.

Hugging Face는 입력 레이어로 끼워 넣을 수 있는 사전학습 임베딩을 제공합니다.

```python
from transformers import AutoModel

encoder = AutoModel.from_pretrained("bert-base-uncased")
for param in encoder.parameters():
    param.requires_grad = False


class BertCNN(nn.Module):
    def __init__(self, n_classes, filter_widths=(2, 3, 4), n_filters=64):
        super().__init__()
        self.encoder = encoder
        self.convs = nn.ModuleList([nn.Conv1d(768, n_filters, kernel_size=k) for k in filter_widths])
        self.fc = nn.Linear(n_filters * len(filter_widths), n_classes)

    def forward(self, input_ids, attention_mask):
        with torch.no_grad():
            out = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        x = out.transpose(1, 2)
        pooled = [F.max_pool1d(F.relu(conv(x)), kernel_size=conv(x).size(2)).squeeze(2) for conv in self.convs]
        return self.fc(torch.cat(pooled, dim=1))
```

제약 조건에 맞을 때 쓰는 체크리스트입니다.

- **엣지/온디바이스 추론.** GloVe 임베딩을 쓴 TextCNN은 트랜스포머보다 10~100배 작습니다. 배포 대상이 휴대폰이라면 이 스택이 답입니다.
- **스트리밍/온라인 분류.** RNN은 토큰을 하나씩 처리하지만 트랜스포머는 시퀀스 전체를 필요로 합니다. 실시간으로 들어오는 텍스트에는 여전히 LSTM이 이깁니다.
- **베이스라인용 초소형 모델.** 새 과제에서 빠르게 반복할 때. TextCNN은 CPU에서도 5분이면 학습됩니다.
- **데이터가 적은 시퀀스 레이블링.** BiLSTM-CRF(레슨 06)는 레이블 문장 1천~1만 개 규모에서도 여전히 프로덕션급 NER 아키텍처입니다.

나머지는 전부 트랜스포머로 갑니다.

## 출시하기

`outputs/prompt-text-encoder-picker.md`로 저장하세요:

```markdown
---
name: text-encoder-picker
description: 주어진 제약 조건 집합에 맞는 텍스트 인코더 아키텍처를 고릅니다.
phase: 5
lesson: 08
---

제약 조건(과제, 데이터 양, 지연 시간 예산, 배포 대상, 연산 예산)이 주어지면 다음을 출력합니다:

1. 인코더 아키텍처: TextCNN, BiLSTM, BiLSTM-CRF, 트랜스포머 파인튜닝, 또는 "사전학습 트랜스포머를 얼린(frozen) 인코더로 쓰고 작은 헤드를 붙이기".
2. 임베딩 입력: 무작위 초기화, GloVe/fastText를 얼려서 사용, 또는 문맥화된(contextualized) 트랜스포머 임베딩.
3. 5줄짜리 학습 레시피: 옵티마이저, 학습률, 배치 크기, 에포크, 정규화.
4. 감시할 신호 하나. RNN/CNN 모델: 어텐션 메커니즘이 없어 장거리 의존성을 놓칠 수 있으므로 길이별 정확도를 점검합니다. 트랜스포머: 학습률이 너무 높으면 파인튜닝 붕괴가 올 수 있으므로 학습 손실을 점검합니다.

레이블 예시가 약 500개 미만일 때, TextCNN/BiLSTM 베이스라인이 정체됐음을 보여 주지 않고 트랜스포머 파인튜닝을 추천하는 일은 거부합니다. 엣지 배포에는 아키텍처 결정이 모든 것보다 먼저 필요하다고 표시합니다.
```

## 연습 문제

1. **(쉬움)** 3클래스 장난감 데이터셋(데이터는 여러분이 만듭니다)에서 TextCNN을 학습시키세요. 필터 너비 (2, 3, 4)가 단일 너비 (3)보다 평균 F1이 나은지 검증합니다.
2. **(보통)** LSTM 분류기에 맥스 풀링, 평균 풀링, 마지막 상태 풀링을 구현하세요. 작은 데이터셋으로 비교하고, 어떤 풀링이 이겼는지 문서화하고 그 이유를 가설로 세워 보세요.
3. **(어려움)** BiLSTM-CRF NER 태거를 만드세요(레슨 06과 이 레슨을 결합). CoNLL-2003으로 학습하고, 레슨 06의 CRF 단독 베이스라인 및 BERT 파인튜닝과 비교하세요. 학습 시간, 메모리, F1을 보고합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| TextCNN | 텍스트용 CNN | 단어 임베딩 위의 1차원 합성곱 층들 + 전역 맥스 풀링. Kim (2014). |
| RNN | 순환 신경망 | 매 시점 갱신되는 은닉 상태: `h_t = f(W x_t + U h_{t-1})`. |
| LSTM | 게이트 달린 RNN | 입력/망각/출력 게이트 + 셀 상태를 추가. 긴 시퀀스에서도 안정적으로 학습됨. |
| GRU | 단순화된 LSTM | 게이트 셋 대신 둘. 비슷한 정확도에 더 적은 파라미터. |
| 양방향(Bidirectional) | 양쪽 방향 | 순방향 + 역방향 RNN을 이어 붙임. 모든 토큰이 양쪽 맥락을 봄. |
| 그래디언트 소실 | 학습 신호가 죽음 | 단순 RNN에서 1 미만 가중치의 반복 곱셈이 초반 단계 그래디언트를 사실상 0으로 만듦. |

## 더 읽을거리

- [Kim, Y. (2014). Convolutional Neural Networks for Sentence Classification](https://arxiv.org/abs/1408.5882) — TextCNN 논문. 8페이지. 읽을 만합니다.
- [Hochreiter, S. and Schmidhuber, J. (1997). Long Short-Term Memory](https://www.bioinf.jku.at/publications/older/2604.pdf) — LSTM 원 논문. 의외로 명쾌합니다.
- [Olah, C. (2015). Understanding LSTM Networks](https://colah.github.io/posts/2015-08-Understanding-LSTMs/) — LSTM을 모두에게 친숙하게 만들어 준 그림들.
