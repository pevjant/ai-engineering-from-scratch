> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 오디오 트랜스포머 — Whisper 아키텍처

> 오디오는 시간 위에 펼쳐진 주파수의 그림입니다. Whisper는 멜 스펙트로그램을 먹고 그 내용을 말로 되돌려 주는 ViT입니다.

**유형:** Learn
**언어:** Python
**선수 지식:** 페이즈 7 · 05(풀 트랜스포머), 페이즈 7 · 08(인코더-디코더), 페이즈 7 · 09(ViT)
**시간:** 약 45분

## 문제 상황

Whisper(OpenAI, Radford 외, 2022)가 나오기 전까지 최고 수준의 자동 음성 인식(ASR)이라 하면 wav2vec 2.0과 HuBERT, 즉 자기 지도 학습 기반 특성 추출기에 파인튜닝한 헤드를 얹은 구조였습니다. 품질은 높았지만 데이터 파이프라인 비용이 비쌌고, 도메인이 바뀌면 성능이 쉽게 무너졌습니다. 다국어 음성 인식을 하려면 언어군마다 별도의 모델이 필요했습니다.

Whisper는 세 가지에 베팅했습니다:

1. **전부 다 모아서 학습시킨다.** 인터넷에서 긁어 모은 97개 언어의 약한 레이블(weakly-labeled) 오디오 680,000시간. 깨끗한 학술 코퍼스도 없고, 음소 레이블도 없습니다.
2. **하나의 모델로 여러 작업을 수행한다.** 하나의 디코더를 전사(transcription), 번역, 발화 감지, 언어 식별, 타임스탬프 찍기를 작업 토큰으로 구분해 한꺼번에 학습시킵니다.
3. **표준 인코더-디코더 트랜스포머를 쓴다.** 인코더는 로그-멜 스펙트로그램을 받고, 디코더는 텍스트 토큰을 자기회귀 방식으로 만들어 냅니다. 보코더도, CTC도, HMM도 없습니다.

그 결과, Whisper large-v3는 억양이든 잡음이든, 아니면 깨끗한 레이블 데이터가 하나도 없는 언어든 튼튼하게 버텨 냅니다. 2026년 현재 오픈소스 음성 비서는 물론이고 상용 음성 비서 대부분이 기본 음성 프런트엔드로 쓰는 모델입니다.

## 개념

![Whisper 파이프라인: 오디오 → 멜 → 인코더 → 디코더 → 텍스트](../assets/whisper.svg)

### 단계 1 — 리샘플링 + 윈도잉

오디오는 16 kHz로 다룹니다. 30초로 자르거나 모자란 만큼 채워(패딩) 맞춥니다. 로그-멜 스펙트로그램을 계산합니다: 멜 빈 80개, 10 ms 간격 → 약 3,000프레임 × 80개 특성(feature). 이것이 Whisper가 보는 '입력 이미지'입니다.

### 단계 2 — 합성곱 스템(stem)

커널 크기 3, 스트라이드 2인 Conv1D 레이어 두 개가 3,000프레임을 1,500프레임으로 줄입니다. 파라미터를 크게 늘리지 않고도 시퀀스 길이를 절반으로 만드는 셈이죠.

### 단계 3 — 인코더

1,500개 타임스텝 위에서 동작하는 24층(large 기준) 트랜스포머 인코더입니다. 사인-코사인(sinusoidal) 위치 인코딩, 셀프 어텐션, GELU FFN을 씁니다. 1,500 × 1,280 크기의 은닉 상태를 만들어 냅니다.

### 단계 4 — 디코더

24층 트랜스포머 디코더입니다. GPT-2 어휘의 상위 집합에 오디오 전용 특수 토큰 몇 개를 얹은 BPE 어휘에서 토큰을 자기회귀 방식으로 만들어 냅니다.

### 단계 5 — 작업 토큰

디코더 프롬프트는 모델에게 무슨 일을 할지 알려 주는 제어 토큰으로 시작합니다:

```
<|startoftranscript|>  <|en|>  <|transcribe|>  <|0.00|>
```

또는

```
<|startoftranscript|>  <|fr|>  <|translate|>   <|0.00|>
```

모델은 이 관례를 보고 학습됐습니다. 접두어만 바꾸면 작업이 바뀝니다. 명령어 튜닝(instruction-tuning)의 2026년판이라고 할 수 있는데, 음성에 적용한 것입니다.

### 단계 6 — 출력

로그 확률 임계값과 함께 빔 서치(폭 5)를 씁니다. `<|notimestamps|>` 토큰이 없을 때는 0.02초 간격으로 타임스탬프를 예측합니다.

### Whisper 크기별 사양

| 모델 | 파라미터 | 레이어 수 | d_model | 헤드 수 | VRAM(fp16) |
|-------|--------|--------|---------|-------|-------------|
| Tiny | 39M | 4 | 384 | 6 | ~1 GB |
| Base | 74M | 6 | 512 | 8 | ~1 GB |
| Small | 244M | 12 | 768 | 12 | ~2 GB |
| Medium | 769M | 24 | 1024 | 16 | ~5 GB |
| Large | 1550M | 32 | 1280 | 20 | ~10 GB |
| Large-v3 | 1550M | 32 | 1280 | 20 | ~10 GB |
| Large-v3-turbo | 809M | 32 | 1280 | 20 | ~6 GB (4층 디코더) |

Large-v3-turbo(2024)는 디코더를 32층에서 4층으로 줄였습니다. 디코딩은 8배 빨라지고 WER(단어 오류율) 상승은 1포인트 미만입니다. 이 디코딩 속도 덕분에 2026년 현재 실시간 음성 에이전트의 기본값은 Whisper-turbo입니다.

### Whisper가 하지 않는 것

- 화자 분리(diarization, 누가 말하고 있는지 구분)는 하지 않습니다. 이건 pyannote와 함께 써야 합니다.
- 자체적으로는 실시간 스트리밍을 지원하지 않습니다 — 30초 윈도우가 고정되어 있기 때문입니다. 최신 래퍼(`faster-whisper`, `WhisperX`)는 VAD + 오버랩으로 스트리밍을 얹어서 해결합니다.
- 외부 청킹(chunking) 없이는 30초를 넘는 긴 오디오를 다루지 못합니다. 다만 사람 발화는 전사에 긴 범위의 문맥을 거의 필요로 하지 않아서, 실전에서는 잘 동작합니다.

### 2026년 생태계 현황

| 작업 | 모델 | 비고 |
|------|-------|-------|
| 영어 ASR | Whisper-turbo, Moonshine | Moonshine은 엣지에서 4배 빠름 |
| 다국어 ASR | Whisper-large-v3 | 97개 언어 |
| 스트리밍 ASR | faster-whisper + VAD | 150 ms 지연 시간 목표 달성 가능 |
| TTS | Piper, XTTS-v2, Kokoro | 인코더-디코더 패턴이지만 Whisper와 비슷한 구조 |
| 오디오 + 언어 | AudioLM, SeamlessM4T | 하나의 트랜스포머 안에서 텍스트 토큰 + 오디오 토큰 |

```figure
n5-mel-decode
```

## 만들어 보기

`code/main.py`를 보세요. 여기서는 Whisper를 학습시키지 않습니다 — 로그-멜 스펙트로그램 파이프라인과 작업 토큰 프롬프트 포맷터를 만들어 봅니다. 프로덕션(운영 환경)에서 실제로 손대는 부분이 바로 이것들입니다.

### 단계 1: 오디오 합성

440 Hz 사인파를 16 kHz로 샘플링해 1초 분량을 만듭니다. 샘플 16,000개죠.

### 단계 2: 로그-멜 스펙트로그램(간략화 버전)

제대로 된 멜 스펙트로그램은 FFT가 필요합니다. 여기서는 `librosa` 없이도 파이프라인을 보여 줄 수 있게, 프레임 나누기 + 프레임별 에너지로 단순화한 버전을 씁니다:

```python
def frame_signal(x, frame_size=400, hop=160):
    frames = []
    for start in range(0, len(x) - frame_size + 1, hop):
        frames.append(x[start:start + frame_size])
    return frames
```

프레임은 25 ms, 홉은 10 ms입니다. Whisper의 윈도잉과 같습니다. 프레임별 에너지는 교육용으로 멜 빈을 대신하는 것입니다.

### 단계 3: 30초로 패딩

Whisper는 항상 30초 단위 청크를 처리합니다. 스펙트로그램을 3,000프레임으로 패딩(또는 잘라내기)합니다.

### 단계 4: 프롬프트 토큰 만들기

```python
def whisper_prompt(lang="en", task="transcribe", timestamps=True):
    tokens = ["<|startoftranscript|>", f"<|{lang}|>", f"<|{task}|>"]
    if not timestamps:
        tokens.append("<|notimestamps|>")
    return tokens
```

작업을 제어하는 인터페이스는 이게 전부입니다. 토큰 4개짜리 접두어 하나죠.

## 사용해 보기

```python
import whisper
model = whisper.load_model("large-v3-turbo")
result = model.transcribe("meeting.wav", language="en", task="transcribe")
print(result["text"])
print(result["segments"][0]["start"], result["segments"][0]["end"])
```

더 빠른, OpenAI 호환 방식:

```python
from faster_whisper import WhisperModel
model = WhisperModel("large-v3-turbo", compute_type="int8_float16")
segments, info = model.transcribe("meeting.wav", vad_filter=True)
for s in segments:
    print(f"{s.start:.2f} - {s.end:.2f}: {s.text}")
```

**2026년에 Whisper를 고르면 좋은 경우:**

- 모델 하나로 다국어 ASR을 할 때.
- 잡음이 섞이고 다양한 오디오도 튼튼하게 전사할 때.
- 연구/프로토타입용 ASR — 가장 빠른 출발점입니다.

**다른 것을 골라야 하는 경우:**

- 엣지에서의 초저지연 스트리밍 — 같은 품질 기준으로는 Moonshine이 Whisper를 이깁니다.
- 200 ms 미만이 필요한 실시간 대화형 AI — 전용 스트리밍 ASR을 쓰세요.
- 화자 분리 — Whisper는 이걸 하지 않습니다. pyannote를 붙이세요.

## 출시하기

`outputs/skill-asr-configurator.md`를 보세요. 이 스킬은 새 음성 애플리케이션을 위해 ASR 모델, 디코딩 파라미터, 전처리 파이프라인을 골라 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 16 kHz 신호 1초를 10 ms 홉으로 나누면 프레임 수가 약 100개인지 확인합니다. 30초라면 약 3,000프레임입니다.
2. **보통.** `numpy.fft`로 제대로 된 로그-멜 스펙트로그램을 만들어 보세요. 멜 빈 80개가 `librosa.feature.melspectrogram(n_mels=80)` 결과와 수치 오차 범위 안에서 일치하는지 확인합니다.
3. **어려움.** 스트리밍 추론을 구현해 보세요: 오디오를 2초 오버랩이 있는 10초 윈도우로 잘라 각 청크마다 Whisper를 돌리고, 전사 결과를 합칩니다. 5분 분량 팟캐스트 샘플에서 한 번에 처리했을 때와의 WER(단어 오류율)을 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 멜 스펙트로그램(Mel spectrogram) | "오디오 이미지" | 2차원 표현: 한 축은 주파수 빈, 다른 축은 시간 프레임, 칸마다 로그 스케일 에너지. |
| 로그-멜(Log-mel) | "Whisper가 보는 것" | 멜 스펙트로그램에 로그를 취한 것; 사람의 크기 인지를 근사합니다. |
| 프레임(Frame) | "시간 조각 하나" | 샘플 25 ms 분량의 윈도우; 10 ms 간격으로 겹칩니다. |
| 작업 토큰(Task token) | "음성용 프롬프트 접두어" | 디코더 프롬프트에 넣는 `<\|transcribe\|>` / `<\|translate\|>` 같은 특수 토큰. |
| 발화 감지(VAD, Voice activity detection) | "말하는 구간 찾기" | ASR 전에 침묵을 걸러 내는 관문; 비용을 크게 줄여 줍니다. |
| CTC | "Connectionist Temporal Classification" | 정렬 없이 학습할 수 있게 해 주는 고전적 ASR 손실; Whisper는 사용하지 않습니다. |
| Whisper-turbo | "작은 디코더, 풀 사이즈 인코더" | large-v3 인코더 + 4층 디코더; 디코딩이 8배 빠릅니다. |
| Faster-whisper | "프로덕션용 래퍼" | CTranslate2로 재구현한 버전; int8 양자화 지원, OpenAI 레퍼런스보다 4배 빠릅니다. |

## 더 읽을거리

- [Radford 외 (2022). Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — Whisper 논문.
- [OpenAI Whisper 저장소](https://github.com/openai/whisper) — 레퍼런스 코드 + 모델 가중치. `whisper/model.py`를 읽으면 Conv1D 스템 + 인코더 + 디코더를 약 400줄 안에서 처음부터 끝까지 볼 수 있습니다.
- [OpenAI Whisper — `whisper/decoding.py`](https://github.com/openai/whisper/blob/main/whisper/decoding.py) — 단계 5~6에서 설명한 빔 서치 + 작업 토큰 로직이 여기 있습니다; 500줄, 충분히 읽을 만합니다.
- [Baevski 외 (2020). wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations](https://arxiv.org/abs/2006.11477) — 선행 연구; 일부 설정에서는 여전히 최고 수준의 특성입니다.
- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) — 프로덕션용 래퍼, 레퍼런스보다 4배 빠릅니다.
- [Jia 외 (2024). Moonshine: Speech Recognition for Live Transcription and Voice Commands](https://arxiv.org/abs/2410.15608) — 2024년 엣지 친화적 ASR, Whisper와 비슷한 구조이지만 더 작습니다.
- [HuggingFace 블로그 — "Fine-Tune Whisper For Multilingual ASR with 🤗 Transformers"](https://huggingface.co/blog/fine-tune-whisper) — 멜 스펙트로그램 전처리기와 토큰-타임스탬프 처리를 포함한 표준 파인튜닝 레시피.
- [HuggingFace `modeling_whisper.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/whisper/modeling_whisper.py) — 이 레슨의 아키텍처 다이어그램과 대응되는 전체 구현(인코더, 디코더, 크로스 어텐션, 생성).
