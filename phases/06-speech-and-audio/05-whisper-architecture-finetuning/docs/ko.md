> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# Whisper — 아키텍처와 파인튜닝

> Whisper는 30초 윈도우 방식의 트랜스포머 인코더-디코더로, 약지도(weakly-supervised) 방식으로 모은 68만 시간 분량의 다국어 오디오-텍스트 쌍으로 학습되었습니다. 하나의 아키텍처로 여러 작업을 해내고, 99개 언어에서도 튼튼하게 동작합니다. 2026년의 표준 ASR(음성 인식)입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 04 (ASR), 페이즈 5 · 10 (어텐션), 페이즈 7 · 05 (전체 트랜스포머)
**소요 시간:** 약 75분

## 문제 상황

2022년 9월 OpenAI가 공개한 Whisper는 최초로 '완제품(commodity)'처럼 쓸 수 있는 ASR 모델이었습니다. 오디오를 붙여 넣으면 텍스트가 나오고, 99개 언어를 지원하고, 소음에도 튼튼하며, 노트북에서도 돌아갑니다. 2024년까지 OpenAI는 Large-v3와 Turbo 변형 모델을 출시했고, 2026년 현재 Whisper는 팟캐스트 전사부터 음성 비서, YouTube 자막에 이르는 모든 분야의 기본 베이스라인이 되었습니다.

하지만 Whisper를 영원히 블랙박스로 다룰 수 있는 파이프라인은 아닙니다. 도메인이 바뀌면(도메인 시프트) 성능이 무너집니다 — 전문 용어, 화자의 억양, 고유명사, 짧은 클립, 침묵이 문제를 일으키죠. 다음 세 가지는 알아야 합니다:

1. Whisper 안에 실제로 무엇이 들어 있는가.
2. 잘게 나눈(chunked) 오디오, 스트리밍 오디오, 긴(long-form) 오디오를 올바르게 넣는 방법.
3. 언제 파인튜닝해야 하는지, 그리고 어떻게 하는지.

## 개념

![Whisper 인코더-디코더, 태스크, 청크 단위 추론, 파인튜닝](../assets/whisper.svg)

**아키텍처.** 표준 트랜스포머 인코더-디코더입니다.

- 입력: 30초 길이의 로그 멜 스펙트로그램, 멜 80개, 10 ms 홉(hop) → 3000 프레임. 30초보다 짧은 클립은 0으로 채우고(제로 패딩), 긴 클립은 잘게 나눕니다.
- 인코더: 합성곱 다운샘플링(stride 2) + `N`개의 트랜스포머 블록. Large-v3 기준: 32개 레이어, 1280차원, 20개 헤드.
- 디코더: 인과적(causal) 셀프 어텐션 + 인코더 출력을 보는 크로스 어텐션을 갖춘 `N`개의 트랜스포머 블록. 크기는 인코더와 같습니다.
- 출력: 51,865개 토큰짜리 어휘집(vocab)의 BPE 토큰.

Large-v3는 파라미터가 15.5억 개(1.55B)입니다. Turbo는 디코더를 32개 레이어에서 4개로 줄여 지연 시간을 8배 단축하면서 WER(단어 오류율) 악화는 1% 미만으로 억제했습니다.

**프롬프트 형식.** Whisper는 디코더 프롬프트에 넣는 특수 토큰으로 조종하는 멀티태스크 모델입니다:

```
<|startoftranscript|><|en|><|transcribe|><|notimestamps|> Hello world.<|endoftext|>
```

- `<|en|>` — 언어 태그. 번역할지 전사할지 동작을 강제로 정합니다.
- `<|transcribe|>` 또는 `<|translate|>` — 어떤 언어 입력이든 영어로 번역하거나(translate), 입력 언어 그대로 받아 적습니다(transcribe).
- `<|notimestamps|>` — 단어 수준 타임스탬프를 건너뜁니다(더 빠름).

바로 이 프롬프트 덕분에 하나의 모델이 여러 작업을 할 수 있습니다. `<|en|>`을 `<|fr|>`로 바꾸면 프랑스어를 전사합니다.

**30초 윈도우.** 모든 것이 30초에 묶여 있습니다. 더 긴 클립은 청킹이 필요하고, 짧은 클립은 패딩됩니다. 윈도우는 기본적으로 스트리밍되지 않습니다 — WhisperX, Whisper-Streaming, faster-whisper 같은 도구가 존재하는 이유가 바로 이것입니다.

**로그 멜 정규화.** `(log_mel - mean) / std`를 적용하는데, 이 통계값은 Whisper 자체 학습 코퍼스에서 나온 것입니다. `librosa.feature.melspectrogram`이 아니라 Whisper의 전처리(`whisper.audio.log_mel_spectrogram`)를 *반드시* 그대로 써야 합니다.

### 2026년 변형 모델들

| 변형 모델 | 파라미터 | 지연 시간 (A100) | WER (LibriSpeech-clean) |
|---------|--------|----------------|------------------------|
| Tiny | 39M | 1배속 실시간 | 5.4% |
| Base | 74M | 1배속 | 4.1% |
| Small | 244M | 1배속 | 3.0% |
| Medium | 769M | 1배속 | 2.7% |
| Large-v3 | 1.55B | 2배속 | 1.8% |
| Large-v3-turbo | 809M | 8배속 | 1.58% |
| Whisper-Streaming (2024) | 1.55B | 스트리밍 | 2.0% |

### 파인튜닝

2026년 표준 워크플로:

1. 정렬된 전사 텍스트가 붙은 목표 도메인 오디오를 10~100시간 모읍니다.
2. `generate_with_loss` 콜백과 함께 `transformers.Seq2SeqTrainer`를 실행합니다.
3. 파라미터 효율 방식: 어텐션 레이어의 `q_proj`, `k_proj`, `v_proj`에 LoRA를 적용하면 GPU 메모리를 4배 아끼고 WER 손해는 0.3 미만입니다.
4. 데이터가 10시간 미만이면 인코더를 얼려 두고(학습 금지) 디코더만 조정합니다.
5. Whisper 고유의 토크나이저와 프롬프트 형식을 그대로 씁니다. 토크나이저를 바꾸는 일은 절대 없어야 합니다.

커뮤니티 결과: Medium 모델을 의료 받아쓰기 20시간으로 파인튜닝하면 의료 용어에 대한 WER이 12%에서 4.5%로 떨어집니다. Turbo를 아이슬란드어 4시간으로 파인튜닝하면 WER이 18%에서 6%로 떨어집니다.

```figure
sp-asr-attention
```

## 직접 만들어 보기

### 단계 1: Whisper를 기본 상태로 돌려 보기

```python
import whisper
model = whisper.load_model("large-v3-turbo")
result = model.transcribe(
    "clip.wav",
    language="en",
    task="transcribe",
    temperature=0.0,
    condition_on_previous_text=False,  # 무한 반복에 빠지는 것을 막아 줍니다
)
print(result["text"])
for seg in result["segments"]:
    print(f"[{seg['start']:.2f}–{seg['end']:.2f}] {seg['text']}")
```

항상 기본값에서 바꿔 줘야 하는 핵심 옵션: `temperature=0.0`(기본은 0.0 → 0.2 → 0.4 … 순으로 올려 가는 폴백 체인), `condition_on_previous_text=False`(누적되는 환각 문제를 예방), `no_speech_threshold=0.6`(침묵 감지).

### 단계 2: 긴 오디오 청크 처리

```python
# whisperx는 2026년 기준, 단어 수준 타임스탬프를 제공하는 긴 오디오 처리의 표준입니다
import whisperx
model = whisperx.load_model("large-v3-turbo", device="cuda", compute_type="float16")
segments = model.transcribe("1hour.mp3", batch_size=16, chunk_size=30)
```

WhisperX는 (1) Silero VAD 게이팅, (2) wav2vec 2.0을 이용한 단어 수준 정렬, (3) `pyannote.audio`를 이용한 화자 분리(diarization)를 더합니다. 2026년 프로덕션(운영 환경) 전사의 주력 도구입니다.

### 단계 3: LoRA로 파인튜닝하기

```python
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from peft import LoraConfig, get_peft_model

model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v3-turbo")
lora = LoraConfig(
    r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1, bias="none", task_type="SEQ_2_SEQ_LM",
)
model = get_peft_model(model, lora)
# model.print_trainable_parameters()  -> 학습 대상 약 300만 개 / 전체 809M
```

이후에는 표준 Trainer 루프를 돌면 됩니다. 1000단계(step)마다 체크포인트를 저장하고, 홀드아웃(held-out, 따로 떼어 둔) 데이터로 WER을 평가합니다.

### 단계 4: 각 레이어가 무엇을 배우는지 들여다보기

```python
# 디코딩 중 크로스 어텐션 가중치를 꺼내면 디코더가 어디를 보고 있는지 알 수 있습니다.
with torch.inference_mode():
    out = model.generate(
        input_features=features,
        return_dict_in_generate=True,
        output_attentions=True,
    )
# out.cross_attentions: 레이어 × 헤드 × 스텝 × 소스 길이
```

히트맵으로 시각화해 보세요. 디코더 스텝이 인코더 프레임을 훑어 갈 때 대각선 방향의 정렬 무늬가 보일 겁니다. 바로 그 대각선이 Whisper가 이해하는 '단어 타임스탬프'입니다.

## 사용해 보기

2026년 스택:

| 상황 | 선택 |
|-----------|------|
| 영어 일반 용도, 오프라인 | `whisperx`로 Large-v3-turbo |
| 모바일 / 엣지 | 양자화된(int8) Whisper-Tiny 또는 Moonshine |
| 다국어 긴 오디오 | `whisperx`로 Large-v3 + 화자 분리 |
| 저자원 언어 | Medium 또는 Turbo를 LoRA로 파인튜닝 |
| 스트리밍 (지연 시간 2초) | Whisper-Streaming 또는 Parakeet-TDT |
| 단어 수준 타임스탬프 | WhisperX (wav2vec 2.0 강제 정렬) |

`faster-whisper`(CTranslate2 백엔드)는 2026년 기준 CPU+GPU 추론 런타임 중 가장 빠릅니다 — 원조(vanilla) Whisper보다 4배 빠르고 결과물은 동일합니다.

## 2026년에도 여전히 출시되는 함정들

- **침묵에서 나오는 환각 텍스트.** Whisper는 자막 데이터로 학습했기 때문에 "Thanks for watching!", "Subscribe!", 노래 가사 같은 문장을 지어냅니다. 호출하기 전에 반드시 VAD 게이트를 거치세요.
- **`condition_on_previous_text` 연쇄 오염.** 환각이 한 번 일어나면 이후 윈도우까지 오염됩니다. 청크 사이의 흐름이 꼭 필요하지 않다면 `False`로 두세요.
- **짧은 클립 패딩.** 2초짜리 클립을 30초로 채우면 뒤따르는 침묵 구간에서 환각이 일어날 수 있습니다. `pad=False`를 쓰거나 VAD 게이트를 거치세요.
- **잘못된 멜 통계.** Whisper 것 대신 librosa의 멜을 쓰면 거의 무작위에 가까운 결과가 나옵니다. `whisper.audio.log_mel_spectrogram`을 쓰세요.

## 출시해 보기

`outputs/skill-whisper-tuner.md`로 저장하세요. 주어진 도메인에 맞는 Whisper 파인튜닝 또는 추론 파이프라인을 설계합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. Whisper 스타일 프롬프트를 토큰화하고, 디코딩 형태(shape) 예산을 계산하고, 10분짜리 클립의 청크 일정을 출력합니다.
2. **보통.** `faster-whisper`를 설치해 10분짜리 팟캐스트를 전사하고, 사람이 만든 전사본과 WER을 비교해 보세요. `language="auto"`와 `language="en"` 강제 지정도 비교해 보세요.
3. **어려움.** HF `datasets`를 이용해 Whisper가 유난히 못하는 언어(예: 우르두어)를 골라, 2시간 데이터로 2 에포크 동안 Medium을 LoRA로 파인튜닝하고 WER 변화를 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 30초 윈도우 | Whisper의 한계 | 입력 길이의 딱딱한 상한. 더 긴 오디오는 청크로 쪼갠다. |
| SOT | 전사 시작(Start-of-transcript) | `<\|startoftranscript\|>`가 디코더 프롬프트를 연다. |
| 타임스탬프 토큰 | 시간 정렬 | 0.02초 간격의 시점 하나하나가 5만1천 개 어휘집 안의 특수 토큰이다. |
| Turbo | 빠른 변형 모델 | 디코더 레이어 4개, 8배 빠름, WER 악화는 1% 미만. |
| WhisperX | 긴 오디오용 래퍼 | VAD + Whisper + wav2vec 정렬 + 화자 분리. |
| LoRA 파인튜닝 | 효율적인 튜닝 | 어텐션에 저랭크 어댑터를 붙여 파라미터의 약 0.3%만 학습한다. |
| 환각 | 조용히 벌어지는 실패 | Whisper가 소음/침묵에서 유창한 영어를 지어낸다. |

## 더 읽을거리

- [Radford 외 (2022). Whisper 논문](https://arxiv.org/abs/2212.04356) — 최초의 아키텍처와 학습 레시피.
- [OpenAI (2024). Whisper Large-v3-turbo 출시](https://github.com/openai/whisper/discussions/2363) — 4개 레이어 디코더, 8배 속도 향상.
- [Bain 외 (2023). WhisperX](https://arxiv.org/abs/2303.00747) — 긴 오디오, 단어 정렬, 화자 분리까지 한 번에.
- [Systran — faster-whisper 저장소](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 기반, 4배 빠름.
- [HuggingFace — Whisper 파인튜닝 튜토리얼](https://huggingface.co/blog/fine-tune-whisper) — 표준 LoRA / 전체 파인튜닝 워크스루.
