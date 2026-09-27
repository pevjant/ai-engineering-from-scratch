> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 텍스트 음성 변환(TTS) — Tacotron에서 F5와 Kokoro까지

> ASR이 음성을 텍스트로 뒤집는다면, TTS는 텍스트를 음성으로 뒤집습니다. 2026년 스택은 세 부분으로 이루어집니다: 텍스트 → 토큰, 토큰 → 멜, 멜 → 파형. 각 부분마다 노트북 안에 들어가는 기본 모델이 있습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 02 (스펙트로그램과 멜), 페이즈 5 · 09 (Seq2Seq), 페이즈 7 · 05 (전체 트랜스포머)
**소요 시간:** 약 75분

## 문제 상황

여러분에게 문자열이 하나 있습니다: "Please remind me to water the plants at 6 pm." 이것을 자연스럽게 들리고, 운율(쉼, 강세)이 맞고, "plants"의 모음을 제대로 발음하고, 살아 있는 음성 비서를 위해 CPU에서 300 ms 안에 처리되는 3초짜리 오디오 클립으로 만들어야 합니다. 목소리를 갈아 끼우고, 코드 스위칭 입력도 처리하고("remind me at 6 pm, daijoubu?"), 사람 이름에서 망신도 당하지 않아야 합니다.

현대의 TTS 파이프라인은 이렇게 생겼습니다:

1. **텍스트 프런트엔드.** 텍스트를 정규화하고(날짜, 숫자, 이메일), 음소 또는 서브워드 토큰으로 바꾸고, 운율 특성을 예측합니다.
2. **어쿠스틱 모델.** 텍스트 → 멜 스펙트로그램. Tacotron 2 (2017), FastSpeech 2 (2020), VITS (2021), F5-TTS (2024), Kokoro (2024).
3. **보코더.** 멜 → 파형. WaveNet (2016), WaveRNN, HiFi-GAN (2020), BigVGAN (2022), 그리고 2024년 이후의 뉴럴 코덱 보코더.

2026년에는 엔드투엔드 확산(diffusion) 모델과 플로우 매칭(flow-matching) 모델이 등장하면서 어쿠스틱 + 보코더 경계가 흐려지고 있습니다. 하지만 디버깅할 때는 이 세 부분이라는 그림이 여전히 통합니다.

## 개념

![Tacotron, FastSpeech, VITS, F5/Kokoro 나란히 비교](../assets/tts.svg)

**Tacotron 2 (2017).** Seq2seq 방식: 문자 임베딩 → BiLSTM 인코더 → 위치 인식(location-sensitive) 어텐션 → 자기회귀(autoregressive) LSTM 디코더가 멜 프레임을 내놓습니다. 느리고(자기회귀), 긴 텍스트에서 잘 흔들립니다. 여전히 베이스라인으로 인용됩니다.

**FastSpeech 2 (2020).** 비자기회귀(non-autoregressive) 방식. 길이 예측기(duration predictor)가 각 음소에 배정될 멜 프레임 수를 내놓습니다. 한 번의 패스로 끝나며 Tacotron보다 10배 빠릅니다. 자연스러움은 조금 손해 봅니다(단조 정렬)만 어디에나 배포됩니다.

**VITS (2021).** 인코더 + 플로우 기반 길이 예측 + HiFi-GAN 보코더를 변분 추론(variational inference)으로 엔드투엔드 함께 학습합니다. 품질이 높은 단일 모델입니다. 2022~2024년 오픈소스 TTS의 강자였습니다. 변형: YourTTS (멀티스피커 제로샷), XTTS v2 (2024, Coqui).

**F5-TTS (2024).** 플로우 매칭 위의 확산 트랜스포머. 자연스러운 운율, 5초짜리 참조 오디오만으로 제로샷 음성 복제가 됩니다. 2026년 오픈소스 TTS 리더보드 정상입니다. 335M 파라미터.

**Kokoro (2024).** 작습니다(82M). CPU에서 돌아가고, 실시간 용도로는 최고 수준의 영어 TTS입니다. 어휘가 정해진 영어 전용이며 apache-2.0 라이선스입니다.

**OpenAI TTS-1-HD, ElevenLabs v2.5, Google Chirp-3.** 상용 최고 수준입니다. ElevenLabs v2.5의 감정 태그("[whispered]", "[laughing]")와 캐릭터 보이스는 2026년 오디오북 제작을 지배하고 있습니다.

### 보코더의 진화

| 시대 | 보코더 | 지연 시간 | 품질 |
|-----|---------|---------|---------|
| 2016 | WaveNet | 오프라인 전용 | 발표 당시 SOTA |
| 2018 | WaveRNN | 실시간 수준 | 좋음 |
| 2020 | HiFi-GAN | 100배 실시간 | 인간에 근접 |
| 2022 | BigVGAN | 50배 실시간 | 화자/언어를 가리지 않고 일반화 |
| 2024 | SNAC, DAC (뉴럴 코덱) | AR 모델과 통합 | 이산 토큰, 비트 효율적 |

2026년이 되면 대부분의 "TTS" 모델은 텍스트에서 파형까지 엔드투엔드로 갑니다. 멜 스펙트로그램은 내부 표현일 뿐입니다.

### 평가

- **MOS (Mean Opinion Score).** 1~5점 척도, 크라우드소싱으로 수집. 여전히 금본위제 표준이지만 고통스럽게 느립니다.
- **CMOS (Comparative MOS).** A vs B 선호도 비교. 주석 한 건당 더 좁은 신뢰 구간을 얻습니다.
- **UTMOS, DNSMOS.** 참조 음성이 필요 없는 뉴럴 MOS 예측기. 리더보드에 쓰입니다.
- **ASR을 통한 CER (Character Error Rate, 글자 오류율).** TTS 출력을 Whisper에 넣고, 입력 텍스트와 비교해 CER을 계산합니다. 알아듣기 쉬운 정도의 대리 지표입니다.
- **SECS (Speaker Embedding Cosine Similarity).** 음성 복제 품질 지표.

2026년 LibriTTS test-clean 수치:

| 모델 | UTMOS | CER (Whisper 기준) | 크기 |
|-------|-------|-------------------|------|
| Ground truth | 4.08 | 1.2% | — |
| F5-TTS | 3.95 | 2.1% | 335M |
| XTTS v2 | 3.81 | 3.5% | 470M |
| VITS | 3.62 | 3.1% | 25M |
| Kokoro v0.19 | 3.87 | 1.8% | 82M |
| Parler-TTS Large | 3.76 | 2.8% | 2.3B |

```figure
sp-tts-stack
```

## 직접 만들어 보기

### 단계 1: 입력을 음소로 바꾸기

```python
from phonemizer import phonemize
ph = phonemize("Hello world", language="en-us", backend="espeak")
# 'həloʊ wɜːld'
```

음소(phoneme)는 만능 다리입니다. VITS 수준 이하의 모델에는 날 텍스트를 그대로 먹이지 마세요.

### 단계 2: Kokoro 실행 (2026년 CPU 기본 선택)

```python
from kokoro import KPipeline
tts = KPipeline(lang_code="a")  # "a" = 미국 영어
audio, sr = tts("Please remind me to water the plants at 6 pm.", voice="af_bella")
# audio: float32 텐서, sr=24000
```

오프라인으로 돌고, 파일 하나짜리 모델이며, 82M 파라미터입니다.

### 단계 3: 음성 복제와 함께 F5-TTS 실행

```python
from f5_tts.api import F5TTS
tts = F5TTS()
wav = tts.infer(
    ref_file="my_voice_5s.wav",
    ref_text="The quick brown fox jumps over the lazy dog.",
    gen_text="Please remind me to water the plants.",
)
```

5초짜리 참조 클립과 그 전사 텍스트를 넘기면, F5가 운율과 음색을 복제합니다.

### 단계 4: HiFi-GAN 보코더를 밑바닥부터

튜토리얼 스크립트에 담기엔 너무 크지만, 뼈대는 이렇습니다:

```python
class HiFiGAN(nn.Module):
    def __init__(self, mel_channels=80, upsample_rates=[8, 8, 2, 2]):
        super().__init__()
        # 업샘플 블록 4개, 총 256배로 멜 속도에서 오디오 속도로 올린다
        ...
    def forward(self, mel):
        return self.blocks(mel)  # -> 파형
```

학습: 적대적 학습(짧은 윈도우 위의 판별자) + 멜 스펙트로그램 재구성 손실 + 피처 매칭 손실. 이미 상용화된 영역입니다 — `hifi-gan` 저장소나 nvidia-NeMo의 사전학습 체크포인트를 쓰세요.

### 단계 5: 전체 파이프라인 (의사코드)

```python
text = "Please remind me at 6 pm."
phones = phonemize(text)
mel = acoustic_model(phones, speaker=alice)      # [T, 80]
wav = vocoder(mel)                                # [T * 256]
soundfile.write("out.wav", wav, 24000)
```

## 사용해 보기

2026년 스택:

| 상황 | 선택 |
|-----------|------|
| 실시간 영어 음성 비서 | Kokoro (CPU) 또는 XTTS v2 (GPU) |
| 5초 참조 음성으로 복제 | F5-TTS |
| 상용 캐릭터 보이스 | ElevenLabs v2.5 |
| 오디오북 낭독 | ElevenLabs v2.5 또는 XTTS v2 + 파인튜닝 |
| 저자원 언어 | 목표 언어 데이터 5~20시간으로 VITS 학습 |
| 표현력 / 감정 태그 | ElevenLabs v2.5 또는 StyleTTS 2 파인튜닝 |

2026년 기준 오픈소스 리더: **품질은 F5-TTS, 효율은 Kokoro**. 역사학자가 아니라면 Tacotron에 손대지 마세요.

## 함정들

- **텍스트 정규화기 부재.** "Dr. Smith"를 "Doctor"로 읽을까요, "Drive"로 읽을까요? "2026"은 "twenty twenty six"일까요, "two zero two six"일까요? 음소 변환기(phonemizer) 전에 반드시 정규화하세요.
- **OOV(사전에 없는) 고유명사.** "Ghumare"가 "ghyu-mair"로 읽힌다면? 모르는 토큰을 위한 폴백 그래프-음소(grapheme-to-phoneme) 모델을 준비하세요.
- **클리핑.** 보코더 출력이 클리핑되는 일은 드물지만, 추론 때 멜 스케일이 어긋나면 ±1.0을 넘을 수 있습니다. 항상 `np.clip(wav, -1, 1)`을 적용하세요.
- **샘플레이트 불일치.** Kokoro는 24 kHz로 내보냅니다. 그런데 다운스트림 파이프라인이 16 kHz를 기대한다면 → 리샘플링하지 않으면 에일리어싱(aliasing)이 생깁니다.

## 출시해 보기

`outputs/skill-tts-designer.md`로 저장하세요. 주어진 목소리, 지연 시간, 언어 목표에 맞는 TTS 파이프라인을 설계합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 장난감 어휘로 음소 사전을 만들고, 음소별 길이를 추정하고, 가짜 "멜" 일정을 출력합니다.
2. **보통.** Kokoro를 설치해 같은 문장을 `af_bella`와 `am_adam` 목소리로 합성해 보세요. 오디오 길이와 주관적 품질을 비교합니다.
3. **어려움.** 자기 목소리 5초짜리 참조 클립을 녹음하세요. F5-TTS로 복제하고, 참조 음성과 복제 출력 사이의 SECS를 측정해 보고합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 음소 (Phoneme) | 소리의 단위 | 추상적인 소리의 부류. 영어에는 39개 (ARPABet). |
| 길이 예측기 (Duration predictor) | 음소마다 얼마나 길어지나 | 비자기회귀(Non-AR) 모델의 출력. 음소당 정수 프레임 수. |
| 보코더 (Vocoder) | 멜 → 파형 | 멜 스펙트로그램을 날 샘플로 바꾸는 신경망. |
| HiFi-GAN | 표준 보코더 | GAN 기반. 2020~2024년의 강자. |
| MOS | 주관적 품질 | 사람 평가자들이 매긴 1~5점 평균 의견 점수. |
| SECS | 음성 복제 지표 | 목표 화자 임베딩과 출력 화자 임베딩 사이의 코사인 유사도. |
| F5-TTS | 2024년 오픈소스 SOTA | 플로우 매칭 확산 모델. 제로샷 복제 지원. |
| Kokoro | CPU 영어 리더 | 82M 파라미터 모델, Apache 2.0. |

## 더 읽을거리

- [Shen 외 (2017). Tacotron 2](https://arxiv.org/abs/1712.05884) — 시퀀스투시퀀스(seq2seq) 베이스라인.
- [Kim, Kong, Son (2021). VITS](https://arxiv.org/abs/2106.06103) — 엔드투엔드 플로우 기반.
- [Chen 외 (2024). F5-TTS](https://arxiv.org/abs/2410.06885) — 현재 오픈소스 SOTA.
- [Kong, Kim, Bae (2020). HiFi-GAN](https://arxiv.org/abs/2010.05646) — 2026년에도 배포되는 보코더.
- [Kokoro-82M on HuggingFace](https://huggingface.co/hexgrad/Kokoro-82M) — 2024년 CPU 친화적 영어 TTS.
