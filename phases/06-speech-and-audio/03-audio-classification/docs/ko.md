# 오디오 분류 — MFCC k-NN부터 AST와 BEATs까지 (Audio Classification)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> "개 짖는 소리 vs 사이렌"부터 "이게 무슨 언어인가"까지 전부 오디오 분류입니다. 특성은 멜입니다. 아키텍처는 10년마다 바뀝니다. 평가는 AUC, F1, 클래스별 재현율로 그대로입니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 6 · 02(스펙트로그램과 멜), 페이즈 3 · 06(CNN), 페이즈 5 · 08(텍스트를 위한 CNN과 RNN)
**소요 시간:** 약 75분

## 문제 상황

10초짜리 클립을 받았습니다. 알고 싶은 것: "이게 뭘까?" 도시 소리(사이렌, 드릴, 개 짖는 소리), 음성 명령(yes/no/stop), 언어 식별(en/es/ar), 화자 감정(화남/중립), 환경음(실내/실외, 웅얼거림). 이 모두 *오디오 분류*이고, 2026년 베이스라인 아키텍처는 성숙했습니다: 로그-멜 → CNN 또는 트랜스포머 → softmax.

핵심 난제는 네트워크가 아닙니다. 데이터입니다. 오디오 데이터셋은 극심한 클래스 불균형, 강한 도메인 시프트(깨끗한 소리 vs 시끄러운 소리), 레이블 노이즈("도시의 웅얼거림"과 "식당 소음"을 누가 구분했나?)을 안고 있습니다. 문제의 80%는 큐레이션, 증강, 평가이지 CNN을 트랜스포머로 바꾸는 일이 아닙니다.

## 개념

![오디오 분류 사다리: MFCC k-NN → AST → BEATs](../assets/audio-classification.svg)

**MFCC 위의 k-NN(1990년대 베이스라인).** 클립마다 MFCC를 펼치고(flatten), 레이블이 달린 은행과 코사인 유사도를 계산한 뒤, top K의 다수결을 반환합니다. 깨끗하고 작은 데이터셋(Speech Commands, ESC-50)에서 의외로 강력합니다. GPU 없이 돌아갑니다.

**로그-멜 위의 2D CNN (2015-2019).** `(T, n_mels)` 로그-멜을 이미지처럼 다룹니다. ResNet-18이나 VGG 스타일을 적용하고, 시간 축을 전역 평균 풀링하고, 클래스 위에서 softmax를 돌립니다. 여전히 2026년 대부분의 캐글 대회 베이스라인입니다.

**Audio Spectrogram Transformer, AST (2021-2024).** 로그-멜을 패치로 자르고(예: 16×16 패치), 위치 임베딩을 더하고, ViT에 넣습니다. AudioSet에서 지도 학습 기준 최고 수준(mAP 0.485)입니다.

**BEATs와 WavLM-base (2024-2026).** 수백만 시간 규모의 자기 지도 사전학습입니다. 원래 필요했을 지도 데이터의 1~10%만으로 여러분의 작업에 파인튜닝합니다. 2026년에 비음성 오디오의 기본 출발점입니다. BEATs-iter3는 AST보다 연산을 1/4만 쓰면서 AudioSet에서 1~2 mAP 앞섭니다.

**고정 백본으로서의 Whisper 인코더(2024).** Whisper의 인코더를 가져오고 디코더를 떼고, 선형 분류기를 붙입니다. 오디오 증강 없이 언어 식별과 단순 이벤트 분류에서 최고 수준에 근접합니다. "공짜 점심" 베이스라인입니다.

### 클래스 불균형이 진짜 과제입니다

ESC-50: 50개 클래스, 클래스당 40개 클립 — 균형 잡혀 있고 쉽습니다. UrbanSound8K: 10개 클래스, 10:1 불균형. AudioSet: 632개 클래스, 100,000:1의 긴 꼬리. 통하는 기법들:

- 학습 중 균형 잡힌 샘플링(평가에서는 하지 않습니다).
- Mixup: 두 클립(과 레이블)을 선형 보간해 증강합니다.
- SpecAugment: 무작위 시간/주파수 대역을 가립니다. 단순하지만 결정적입니다.

### 평가

- 단일 레이블 다중 클래스(Speech Commands): top-1 정확도, top-5 정확도.
- 다중 레이블 다중 클래스(AudioSet, UrbanSound 스타일): mean average precision(mAP).
- 극심한 불균형: 클래스별 재현율 + 매크로 F1.

2026년 알아 둘 숫자:

| 벤치마크 | 베이스라인 | SOTA 2026 | 출처 |
|-----------|----------|-----------|--------|
| ESC-50 | 82% (AST) | 97.0% (BEATs-iter3) | BEATs 논문 (2024) |
| AudioSet mAP | 0.485 (AST) | 0.548 (BEATs-iter3) | HEAR 리더보드 2026 |
| Speech Commands v2 | 98% (CNN) | 99.0% (Audio-MAE) | HEAR v2 결과 |

```figure
mfcc-pipeline
```

## 직접 만들기

### 단계 1: 특성화

```python
def featurize_mfcc(signal, sr, n_mfcc=13, n_mels=40, frame_len=400, hop=160):
    mag = stft_magnitude(signal, frame_len, hop)
    fb = mel_filterbank(n_mels, frame_len, sr)
    mels = apply_filterbank(mag, fb)
    log = log_transform(mels)
    return [dct_ii(frame, n_mfcc) for frame in log]
```

### 단계 2: 고정 길이 요약

```python
def summarize(mfcc_frames):
    n = len(mfcc_frames[0])
    mean = [sum(f[i] for f in mfcc_frames) / len(mfcc_frames) for i in range(n)]
    var = [
        sum((f[i] - mean[i]) ** 2 for f in mfcc_frames) / len(mfcc_frames) for i in range(n)
    ]
    return mean + var
```

단순하지만 강력합니다: 시간 축의 평균 + 분산만으로 13계수 MFCC를 26차원 고정 임베딩으로 바꿉니다. 즉시 실행됩니다. 2017년까지만 해도 ESC-50에서 최신 신경망 베이스라인을 이겼습니다.

### 단계 3: k-NN

```python
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-12
    nb = math.sqrt(sum(x * x for x in b)) or 1e-12
    return dot / (na * nb)

def knn_classify(q, bank, labels, k=5):
    sims = sorted(range(len(bank)), key=lambda i: -cosine(q, bank[i]))[:k]
    votes = Counter(labels[i] for i in sims)
    return votes.most_common(1)[0][0]
```

### 단계 4: 로그-멜 위의 CNN으로 업그레이드

PyTorch에서:

```python
import torch.nn as nn

class AudioCNN(nn.Module):
    def __init__(self, n_mels=80, n_classes=50):
        super().__init__()
        self.body = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.head = nn.Linear(128, n_classes)

    def forward(self, x):  # x: (B, 1, T, n_mels)
        return self.head(self.body(x).flatten(1))
```

파라미터 300만 개. RTX 4090 한 장에서 ESC-50 학습에 약 10분. 정확도 80% 이상.

### 단계 5: 2026년의 기본값 — BEATs 파인튜닝

```python
from transformers import ASTFeatureExtractor, ASTForAudioClassification

ext = ASTFeatureExtractor.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593")
model = ASTForAudioClassification.from_pretrained(
    "MIT/ast-finetuned-audioset-10-10-0.4593",
    num_labels=50,
    ignore_mismatched_sizes=True,
)

inputs = ext(audio, sampling_rate=16000, return_tensors="pt")
logits = model(**inputs).logits
```

BEATs는 `beats` 라이브러리를 통해 `microsoft/BEATs-base`를 쓰세요; transformers API와 형태는 같습니다.

## 활용하기

2026년의 표준 스택:

| 상황 | 출발점 |
|-----------|-----------|
| 초소형 데이터셋(1,000개 미만 클립) | MFCC 평균 기반 k-NN(여러분의 베이스라인) + 오디오 증강 |
| 중간 데이터셋(1K–100K) | BEATs 또는 AST 파인튜닝 |
| 대형 데이터셋(100K 초과) | 처음부터 학습 또는 Whisper-인코더 파인튜닝 |
| 실시간, 엣지 | int8로 양자화한 40-MFCC CNN (KWS 스타일) |
| 다중 레이블(AudioSet) | BCE 손실 + mixup + SpecAugment를 얹은 BEATs-iter3 |
| 언어 식별 | MMS-LID, SpeechBrain VoxLingua107 베이스라인 |

판단 규칙: **새 모델이 아니라 고정된 백본으로 시작하세요**. BEATs 헤드를 파인튜닝하면 몇 주가 아니라 몇 시간 만에 SOTA의 95%에 도달합니다.

## 출시하기

`outputs/skill-classifier-designer.md`로 저장하세요. 주어진 오디오 분류 작업에 맞는 아키텍처, 증강, 클래스 균형 전략, 평가 지표를 선택해 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 4클래스 합성 데이터셋(서로 다른 음높이의 순수 톤)에서 k-NN MFCC 베이스라인을 학습합니다. 혼동 행렬을 보고하세요.
2. **보통.** `summarize`를 [평균, 분산, 왜도, 첨도]로 바꿔 보세요. 같은 합성 데이터셋에서 4-모멘트 풀링이 평균+분산을 이기나요?
3. **어려움.** `torchaudio`로 ESC-50 fold 1에서 2D CNN을 학습하세요. 5-fold 교차 검증 정확도를 보고하세요. SpecAugment(시간 마스크 = 20, 주파수 마스크 = 10)를 추가하고 변화량을 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| AudioSet | 오디오의 ImageNet | Google의 200만 클립, 632클래스 약한 레이블 YouTube 데이터셋. |
| ESC-50 | 소형 분류 벤치마크 | 환경음 50클래스 × 클립 40개. |
| AST | Audio Spectrogram Transformer | 로그-멜 패치 위의 ViT; 2021년 SOTA. |
| BEATs | 자기 지도 오디오 | Microsoft 모델, 2026년 기준 iter3가 AudioSet 선두. |
| Mixup | 쌍 증강 | `x = λ·x1 + (1-λ)·x2; y = λ·y1 + (1-λ)·y2`. |
| SpecAugment | 마스크 기반 증강 | 스펙트로그램의 무작위 시간/주파수 대역을 0으로 만듦. |
| mAP | 주요 다중 레이블 지표 | 클래스와 임계값에 걸친 mean average precision. |

## 더 읽을거리

- [Gong, Chung, Glass (2021). AST: Audio Spectrogram Transformer](https://arxiv.org/abs/2104.01778) — 2021~2024년의 대표 아키텍처.
- [Chen et al. (2022, 개정 2024). BEATs: Audio Pre-Training with Acoustic Tokenizers](https://arxiv.org/abs/2212.09058) — 2024년 이후의 기본값.
- [Park et al. (2019). SpecAugment](https://arxiv.org/abs/1904.08779) — 지배적인 오디오 증강 기법.
- [Piczak (2015). ESC-50 dataset](https://github.com/karolpiczak/ESC-50) — 여전히 살아 있는 50클래스 벤치마크.
- [Gemmeke et al. (2017). AudioSet](https://research.google.com/audioset/) — 632클래스 YouTube 분류 체계; 여전히 금본위 기준.
