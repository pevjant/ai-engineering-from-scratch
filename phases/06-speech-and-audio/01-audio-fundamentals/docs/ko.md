# 오디오 기초 — 파형, 샘플링, 푸리에 변환 (Audio Fundamentals)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 파형은 날신호입니다. 스펙트로그램은 표현 방식입니다. 멜 특성은 ML 친화적 형태입니다. 모든 현대 ASR과 TTS 파이프라인이 이 사다리를 오르고, 그 첫 번째 단은 샘플링과 푸리에를 이해하는 것입니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 1 · 06(벡터와 행렬), 페이즈 1 · 14(확률 분포)
**소요 시간:** 약 45분

## 문제 상황

마이크는 압력-시간 신호를 만들어 냅니다. 신경망은 텐서를 먹습니다. 그 사이에는 관례(convention)의 스택이 있는데, 이를 어기면 조용한 버그가 생깁니다: 모델은 잘 학습되는데 WER이 두 배가 되거나, TTS가 지직거림을 내보내거나, 음성 복제 시스템이 화자가 아니라 마이크를 기억해 버립니다.

음성 시스템의 모든 버그는 세 가지 질문 중 하나로 거슬러 올라갑니다:

1. 데이터는 몇 Hz로 녹음됐고, 모델은 무엇을 기대하는가?
2. 신호에 에일리어싱이 일어났는가?
3. 날 샘플을 다루는가, 주파수 표현을 다루는가?

이것들을 맞히면 페이즈 6의 나머지는 다룰 만해집니다. 틀리면 Whisper-Large-v4조차 쓰레기를 내놓습니다.

## 개념

![파형, 샘플링, DFT, 주파수 빈 시각화](../assets/audio-fundamentals.svg)

**파형.** `[-1.0, 1.0]` 범위의 실수(float) 1차원 배열입니다. 샘플 번호로 인덱싱합니다. 초 단위로 바꾸려면 샘플 레이트로 나눕니다: `t = n / sr`. 16 kHz의 10초 클립은 실수 160,000개짜리 배열입니다.

**샘플링 레이트(sr).** 초당 샘플 수입니다. 2026년의 흔한 레이트:

| 레이트 | 용도 |
|------|-----|
| 8 kHz | 전화, 구형 VOIP. 나이퀴스트 4 kHz가 자음을 죽입니다. ASR에는 비추천. |
| 16 kHz | ASR 표준. Whisper, Parakeet, SeamlessM4T v2 모두 16 kHz를 받습니다. |
| 22.05 kHz | 구형 모델의 TTS 보코더 학습. |
| 24 kHz | 현대 TTS (Kokoro, F5-TTS, xTTS v2). |
| 44.1 kHz | CD 오디오, 음악. |
| 48 kHz | 영화, 전문 오디오, 고충실도 TTS (VALL-E 2, NaturalSpeech 3). |

**나이퀴스트-샤논 정리.** 샘플 레이트 `sr`은 최대 `sr/2`까지의 주파수를 모호함 없이 표현할 수 있습니다. `sr/2` 경계가 *나이퀴스트 주파수*입니다. 나이퀴스트를 넘는 에너지는 *에일리어싱*됩니다 — 더 낮은 주파수로 접혀 내려와 신호를 오염시킵니다. 다운샘플링 전에는 항상 저역 통과 필터를 거치세요.

**비트 심도.** 16비트 PCM(부호 있는 int16, 범위 ±32,767)이 만능 교환 포맷입니다. 음악은 24비트, 내부 DSP는 32비트 float를 씁니다. `soundfile` 같은 라이브러리는 int16으로 읽지만 `[-1, 1]` 범위의 float32 배열로 내어 줍니다.

**푸리에 변환.** 모든 유한 신호는 서로 다른 주파수의 사인파들의 합입니다. 이산 푸리에 변환(DFT)은 `N`개 샘플에 대해 주파수 빈(bin)마다 하나씩, `N`개의 복소수 계수를 계산합니다. `bin k`는 주파수 `k · sr / N` Hz에 대응합니다. 크기(magnitude)는 그 주파수의 진폭이고, 각도는 위상입니다.

**FFT.** 고속 푸리에 변환: `N`이 2의 거듭제곱일 때 DFT를 `O(N log N)`에 푸는 알고리즘입니다. 모든 오디오 라이브러리가 내부적으로 FFT를 씁니다. 16 kHz에서 1024 샘플 FFT는 0–8 kHz를 15.6 Hz 해상도로 커버하는 쓸만한 주파수 빈 512개를 줍니다.

**프레이밍 + 윈도잉.** 클립 전체를 FFT하지 않습니다. 겹치는 *프레임*들로 자른 다음(보통 25 ms 길이에 10 ms 홉), 각 프레임에 윈도우 함수(Hann, Hamming)를 곱해 경계 불연속을 죽이고, 프레임마다 FFT합니다. 이것이 단시간 푸리에 변환(STFT)입니다. 레슨 02가 여기서 이어집니다.

```figure
mel-scale
```

## 직접 만들기

### 단계 1: 클립을 읽고 파형 그리기

`code/main.py`는 데모를 의존성 없이 유지하려고 표준 라이브러리의 `wave` 모듈만 씁니다. 프로덕션에서는 `soundfile`이나 `torchaudio.load`를 쓰게 됩니다(둘 다 `(waveform, sr)` 튜플을 반환):

```python
import soundfile as sf
waveform, sr = sf.read("clip.wav", dtype="float32")  # shape (T,), sr=int
```

### 단계 2: 기본 원리로 사인파 합성하기

```python
import math

def sine(freq_hz, sr, seconds, amp=0.5):
    n = int(sr * seconds)
    return [amp * math.sin(2 * math.pi * freq_hz * i / sr) for i in range(n)]
```

16 kHz에서 1초짜리 440 Hz 사인파(연주음 A)는 실수 16,000개입니다. `wave.open(..., "wb")`로 16비트 PCM 인코딩으로 쓰세요.

### 단계 3: DFT를 손으로 계산하기

```python
def dft(x):
    N = len(x)
    out = []
    for k in range(N):
        re = sum(x[n] * math.cos(-2 * math.pi * k * n / N) for n in range(N))
        im = sum(x[n] * math.sin(-2 * math.pi * k * n / N) for n in range(N))
        out.append((re, im))
    return out
```

`O(N²)`입니다 — `N=256` 정도로 정확성을 확인하는 데는 괜찮지만, 실제 오디오에는 무용지물입니다. 실제 코드는 `numpy.fft.rfft`나 `torch.fft.rfft`를 호출합니다.

### 단계 4: 지배적 주파수 찾기

크기 피크 인덱스 `k_star`는 주파수 `k_star * sr / N`에 대응합니다. 이것을 440 Hz 사인파에 돌리면 `440 * N / sr` 빈에서 피크가 나와야 합니다.

### 단계 5: 에일리어싱 시연하기

10 kHz로 7 kHz 사인파를 샘플링해 봅시다(나이퀴스트 = 5 kHz). 7 kHz 톤은 나이퀴스트 위라 `10 − 7 = 3 kHz`로 접혀 내려옵니다. FFT 피크가 3 kHz에 나타납니다. 이것이 고전적인 에일리어싱 데모이며, 모든 DAC/ADC에 벽돌벽(brick-wall) 저역 통과 필터가 붙어 나오는 이유입니다.

## 활용하기

2026년에 실제로 출시하게 될 스택:

| 작업 | 라이브러리 | 이유 |
|------|---------|-----|
| WAV/FLAC/OGG 읽기/쓰기 | `soundfile` (libsndfile 래퍼) | 가장 빠르고, 안정적이고, float32 반환. |
| 리샘플 | `torchaudio.transforms.Resample` 또는 `librosa.resample` | 올바른 안티에일리어싱 내장. |
| STFT / 멜 | `torchaudio` 또는 `librosa` | GPU 친화적; PyTorch 생태계. |
| 실시간 스트리밍 | `sounddevice` 또는 `pyaudio` | 크로스 플랫폼 PortAudio 바인딩. |
| 파일 들여다보기 | `ffprobe` 또는 `soxi` | CLI, 빠름, sr/채널/코덱 보고. |

판단 규칙: **다른 무엇보다 먼저 샘플 레이트를 맞추세요**. Whisper는 16 kHz 모노 float32를 기대합니다. 44.1 kHz 스테레오를 넘기면 모델 버그처럼 보이는 쓰레기가 나옵니다.

## 출시하기

`outputs/skill-audio-loader.md`로 저장하세요. 이 스킬은 오디오 입력이 하류 모델의 기대와 일치하는지 확인하고, 일치하지 않을 때 올바르게 리샘플하도록 도와줍니다.

## 연습 문제

1. **쉬움.** 16 kHz에서 220 Hz + 440 Hz + 880 Hz를 섞은 1초짜리 신호를 합성하세요. DFT를 돌리고 예상 빈 세 곳에서 피크가 나오는지 확인하세요.
2. **보통.** 48 kHz로 자기 목소리를 3초 WAV로 녹음하세요. `torchaudio.transforms.Resample`로(안티에일리어싱 켜고) 16 kHz로 낮춘 것과, 나이브 디시메이션(3개마다 하나씩)으로 16 kHz로 낮춘 것을 준비하세요. 둘 다 FFT해 보세요. 에일리어싱이 어디에 나타나나요?
3. **어려움.** `math`와 단계 3의 DFT만으로 STFT를 밑바닥부터 만들어 보세요. 프레임 크기 400, 홉 160, Hann 윈도우. `matplotlib.pyplot.imshow`로 크기를 그리세요. 이것이 레슨 02의 스펙트로그램입니다.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| 샘플 레이트 | 초당 샘플 수 | ADC가 신호를 측정하는 Hz 빈도. |
| 나이퀴스트 | 표현 가능한 최대 주파수 | `sr/2`; 이 위의 에너지는 아래로 에일리어싱됨. |
| 비트 심도 | 샘플 하나의 해상도 | `int16` = 65,536 단계; `float32` = `[-1, 1]`에서 24비트 정밀도. |
| DFT | 신호열을 위한 푸리에 변환 | `N` 샘플 → 복소수 주파수 계수 `N`개. |
| FFT | 빠른 DFT | `N` = 2의 거듭제곱이 필요한 `O(N log N)` 알고리즘. |
| 빈(Bin) | 주파수 열 | `k · sr / N` Hz; 해상도 = `sr / N`. |
| STFT | 스펙트로그램의 내부 실체 | 시간에 걸친 프레이밍 + 윈도잉 FFT. |
| 에일리어싱(Aliasing) | 이상한 주파수 유령 | 나이퀴스트 위의 에너지가 낮은 빈으로 접혀 내려옴. |

## 더 읽을거리

- [Shannon (1949). Communication in the Presence of Noise](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf) — 샘플링 정리 뒤에 있는 논문.
- [Smith — The Scientist and Engineer's Guide to Digital Signal Processing](https://www.dspguide.com/ch8.htm) — 무료, 표준 DSP 교과서.
- [librosa 문서 — 오디오 프라이머](https://librosa.org/doc/latest/tutorial.html) — 코드와 함께 보는 실용적 안내.
- [Heinrich Kuttruff — Room Acoustics (6판)](https://www.routledge.com/Room-Acoustics/Kuttruff/p/book/9781482260434) — 실세계 오디오가 왜 깨끗한 사인파가 아닌지에 대한 참고서.
- [Steve Eddins — FFT 해석 노트북](https://blogs.mathworks.com/steve/2020/03/30/fft-spectrum-and-spectral-densities/) — 주파수 빈 직관을 10분 만에 정리해 줌.
