# 스펙트로그램, 멜 스케일, 오디오 특성 (Spectrograms, Mel Scale & Audio Features)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 신경망은 날 파형을 잘 소화하지 못합니다. 스펙트로그램은 잘 소화합니다. 멜 스펙트로그램은 더 잘 소화합니다. 2026년의 모든 ASR, TTS, 오디오 분류기는 이 단 하나의 전처리 선택에 목숨을 겁니다.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 6 · 01(오디오 기초)
**소요 시간:** 약 45분

## 문제 상황

10초짜리 16 kHz 클립을 봅시다. 실수 160,000개인데 전부 `[-1, 1]` 범위이고, "개 짖는 소리"나 "cat이라는 단어"라는 레이블과는 거의 상관이 없습니다. 날 파형에는 정보가 있지만 모델이 쉽게 뽑아 낼 수 없는 형태로 담겨 있습니다. 100 ms 간격으로 발음한 두 개의 동일한 음소는 날 샘플이 완전히 다릅니다.

스펙트로그램이 이걸 해결합니다. 인간 지각이 무시하는 시간 디테일(마이크로초 단위 흔들림)은 접어 없애고, 지각이 주목하는 구조(약 10~25 ms 윈도우 동안 어떤 주파수에 에너지가 있는지)는 보존합니다.

멜 스펙트로그램은 한 걸음 더 나아갑니다. 인간은 음높이를 로그적으로 지각합니다: 100 Hz vs 200 Hz의 차이가 1000 Hz vs 2000 Hz의 차이와 "같은 거리"로 들립니다. 멜 스케일은 주파수 축을 이에 맞게 휘어줍니다. 멜 스케일 스펙트로그램은 2010년부터 2026년까지 음성 ML에서 가장 중요한 단 하나의 특성(feature)입니다.

## 개념

![파형 → STFT → 멜 스펙트로그램 → MFCC 사다리](../assets/mel-features.svg)

**STFT(단시간 푸리에 변환).** 파형을 겹치는 프레임들로 자릅니다(전형값: 25 ms 윈도우, 10 ms 홉 = 16 kHz 기준 400 샘플 / 160 샘플). 각 프레임에 윈도우 함수를 곱합니다(Hann이 기본; Hamming은 약간 다른 트레이드오프). 프레임마다 FFT합니다. 크기 스펙트럼을 `(n_frames, n_freq_bins)` 모양의 행렬로 쌓습니다. 그것이 여러분의 스펙트로그램입니다.

**로그 크기(log-magnitude).** 날 크기는 5~6자릿수를 넘나듭니다. 동적 범위를 압축하려면 `log(|X| + 1e-6)` 또는 `20 * log10(|X|)`를 취합니다. 모든 프로덕션 파이프라인은 날 크기가 아니라 로그 크기를 씁니다.

**멜 스케일.** Hz 단위 주파수 `f`는 `m = 2595 * log10(1 + f / 700)`으로 멜 `m`에 대응합니다. 이 매핑은 1 kHz 아래에서는 대략 선형, 위에서는 대략 로그입니다. 0–8 kHz를 커버하는 멜 빈 80개가 표준 ASR 입력입니다.

**멜 필터뱅크.** 멜 스케일에서 균등한 간격으로 놓인 삼각 필터들의 집합입니다. 각 필터는 인접 FFT 빈들의 가중합입니다. STFT 크기에 필터뱅크 행렬을 곱하면 행렬 곱 한 번으로 멜 스펙트로그램이 나옵니다.

**로그-멜 스펙트로그램.** `log(mel_spec + 1e-10)`. Whisper의 입력. Parakeet의 입력. SeamlessM4T의 입력. 2026년의 만능 오디오 프런트엔드입니다.

**MFCC.** 로그-멜 스펙트로그램에 DCT(type II)를 적용하고 첫 13개 계수를 취합니다. 특성을 비상관화하고 더 압축합니다. 2015년경 날 로그-멜 위에서 동작하는 CNN/트랜스포머가 따라 잡을 때까지 지배적인 특성이었습니다. 화자 인식(x-vectors, ECAPA)에서는 여전히 쓰입니다.

**해상도 트레이드오프.** FFT가 클수록 주파수 해상도는 좋아지지만 시간 해상도는 나빠집니다. 25 ms / 10 ms가 오디오 ML 기본값; 음악은 50 ms / 12.5 ms; 과도 신호 감지(드럼 타격, 파열음)는 5 ms / 2 ms.

```figure
spectrogram-window
```

## 직접 만들기

### 단계 1: 파형을 프레임으로 자르기

```python
def frame(signal, frame_len, hop):
    n = 1 + (len(signal) - frame_len) // hop
    return [signal[i * hop : i * hop + frame_len] for i in range(n)]
```

10초짜리 16 kHz 클립을 `frame_len=400, hop=160`으로 자르면 998개 프레임이 나옵니다.

### 단계 2: Hann 윈도우

```python
import math

def hann(N):
    return [0.5 * (1 - math.cos(2 * math.pi * n / (N - 1))) for n in range(N)]
```

FFT 전에 요소별로 곱합니다. 0이 아닌 끝점에서 잘려 나오며 생기는 스펙트럼 누설을 제거합니다.

### 단계 3: STFT 크기

```python
def stft_magnitude(signal, frame_len=400, hop=160):
    win = hann(frame_len)
    frames = frame(signal, frame_len, hop)
    return [magnitudes(dft([w * s for w, s in zip(win, f)])) for f in frames]
```

프로덕션은 `torch.stft`나 `librosa.stft`(FFT 기반, 벡터화)를 씁니다. 여기의 루프는 교육용이며, `code/main.py`에서 짧은 클립에 돌아갑니다.

### 단계 4: 멜 필터뱅크

```python
def hz_to_mel(f):
    return 2595.0 * math.log10(1.0 + f / 700.0)

def mel_to_hz(m):
    return 700.0 * (10 ** (m / 2595.0) - 1)

def mel_filterbank(n_mels, n_fft, sr, fmin=0, fmax=None):
    fmax = fmax or sr / 2
    mels = [hz_to_mel(fmin) + (hz_to_mel(fmax) - hz_to_mel(fmin)) * i / (n_mels + 1)
            for i in range(n_mels + 2)]
    hzs = [mel_to_hz(m) for m in mels]
    bins = [int(h * n_fft / sr) for h in hzs]
    fb = [[0.0] * (n_fft // 2 + 1) for _ in range(n_mels)]
    for m in range(n_mels):
        for k in range(bins[m], bins[m + 1]):
            fb[m][k] = (k - bins[m]) / max(1, bins[m + 1] - bins[m])
        for k in range(bins[m + 1], bins[m + 2]):
            fb[m][k] = (bins[m + 2] - k) / max(1, bins[m + 2] - bins[m + 1])
    return fb
```

`n_fft=400`으로 0–8 kHz를 커버하는 80개 멜은 `(80, 201)` 행렬을 줍니다. `(n_frames, 201)` STFT 크기에 전치 행렬을 곱하면 `(n_frames, 80)` 멜 스펙트로그램이 나옵니다.

### 단계 5: 로그-멜

```python
def log_mel(mel_spec, eps=1e-10):
    return [[math.log(max(v, eps)) for v in frame] for frame in mel_spec]
```

흔한 대안들: `librosa.power_to_db`(기준 정규화 dB), `10 * log10(power + eps)`. Whisper는 더 복잡한 클립 + 정규화 절차를 씁니다(Whisper의 `log_mel_spectrogram` 참조).

### 단계 6: MFCC

```python
def dct_ii(x, n_coeffs):
    N = len(x)
    return [
        sum(x[n] * math.cos(math.pi * k * (2 * n + 1) / (2 * N)) for n in range(N))
        for k in range(n_coeffs)
    ]
```

각 로그-멜 프레임에 DCT를 적용하고 첫 13개 계수를 취합니다. 그것이 MFCC 행렬입니다. 첫 계수는 보통 버립니다(전체 에너지를 인코딩합니다).

## 활용하기

2026년의 표준 스택:

| 작업 | 특성 |
|------|----------|
| ASR (Whisper, Parakeet, SeamlessM4T) | 로그-멜 80개, 10 ms 홉, 25 ms 윈도우 |
| TTS 어쿠스틱 모델 (VITS, F5-TTS, Kokoro) | 멜 80개, 세밀한 시간 제어를 위한 5–12 ms 홉 |
| 오디오 분류 (AST, PANNs, BEATs) | 로그-멜 128개, 10 ms 홉 |
| 화자 임베딩 (ECAPA-TDNN, WavLM) | 로그-멜 80개 또는 날 파형 SSL |
| 음악 (MusicGen, Stable Audio 2) | EnCodec 이산 토큰 (멜이 아님) |
| 키워드 스포팅 | 초소형 기기용 MFCC 40개 |

경험칙: **음악을 다루는 게 아니라면 로그-멜 80개로 시작하세요.** 다르게 하려면 그만큼의 근거를 제시해야 합니다.

## 2026년에도 계속 출시되는 실수들

- **멜 개수 불일치.** 80 멜로 학습하고 128 멜로 추론합니다. 조용한 실패입니다. 양쪽 끝에서 특성 모양을 로그로 남기세요.
- **상류의 샘플 레이트 불일치.** 22.05 kHz로 계산한 멜은 16 kHz 것과 다르게 보입니다. 특성화*하기 전에* 샘플 레이트를 고치세요.
- **dB vs 로그.** Whisper는 dB-멜이 아니라 로그-멜을 기대합니다. 일부 HF 파이프라인은 자동 감지하지만, 여러분의 커스텀 코드는 그렇지 않습니다.
- **정규화 드리프트.** 학습 중에는 발화별 정규화, 추론 중에는 전역 정규화. WER을 두 배로 만드는 프로덕션 버그입니다.
- **패딩에서 오는 누설.** 클립 끝을 0으로 패딩하면 뒤쪽 프레임에 평평한 스펙트럼이 생깁니다. 대칭 패딩 또는 복제 패딩을 쓰세요.

## 출시하기

`outputs/skill-feature-extractor.md`로 저장하세요. 이 스킬은 대상 모델에 맞는 특성 유형, 멜 개수, 프레임/홉, 정규화를 선택해 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 처프(주파수가 200 → 4000 Hz로 변하는 신호)를 합성하고 프레임별 argmax 멜 빈을 출력합니다. (선택) 그래프를 그려 스윕과 일치하는지 확인하세요.
2. **보통.** `n_mels`를 `{40, 80, 128}`로, `frame_len`을 `{200, 400, 800}`으로 바꿔 다시 실행하세요. 시간 축을 따라 선명한 피크의 대역폭을 측정하세요. 어느 조합이 처프를 가장 잘 해석하나요?
3. **어려움.** `power_to_db`를 구현하고, AudioMNIST의 작은 CNN 분류기에서 (a) 날 로그-멜, (b) `ref=max`인 dB-멜, (c) MFCC-13 + 델타 + 델타-델타의 ASR 정확도를 비교하세요. top-1 정확도를 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| 프레임 | 잘라낸 조각 | FFT 한 번에 들어가는 25 ms짜리 파형 덩어리. |
| 홉(Hop) | 보폭 | 연속 프레임 사이의 샘플 수; 10 ms가 ASR 기본값. |
| 윈도우 | Hann/Hamming 함수 | 프레임 가장자리를 0으로 테이퍼시키는 요소별 승수. |
| STFT | 스펙트로그램 생성기 | 프레이밍 + 윈도잉 FFT; 시간 × 주파수 행렬을 산출. |
| 멜(Mel) | 휘어진 주파수 | 로그 지각 스케일; `m = 2595·log10(1 + f/700)`. |
| 필터뱅크 | 그 행렬 | STFT를 멜 빈에 사상하는 삼각 필터들. |
| 로그-멜 | Whisper의 입력 | `log(mel_spec + eps)`; 2026년 표준. |
| MFCC | 구식 특성 | 로그-멜의 DCT; 계수 13개, 비상관화됨. |

## 더 읽을거리

- [Davis, Mermelstein (1980). Comparison of parametric representations for monosyllabic word recognition](https://ieeexplore.ieee.org/document/1163420) — MFCC 원 논문.
- [Stevens, Volkmann, Newman (1937). A Scale for the Measurement of the Psychological Magnitude Pitch](https://pubs.aip.org/asa/jasa/article-abstract/8/3/185/735757/) — 최초의 멜 스케일.
- [OpenAI — Whisper 소스, log_mel_spectrogram](https://github.com/openai/whisper/blob/main/whisper/audio.py) — 레퍼런스 구현을 직접 읽어 보세요.
- [librosa 특성 추출 문서](https://librosa.org/doc/main/feature.html) — `mfcc`, `melspectrogram`, 홉/윈도우 참고서.
- [NVIDIA NeMo — 오디오 전처리](https://docs.nvidia.com/deeplearning/nemo/user-guide/docs/en/main/asr/asr_all.html#featurizers) — Parakeet + Canary 모델용 프로덕션 규모 파이프라인.
