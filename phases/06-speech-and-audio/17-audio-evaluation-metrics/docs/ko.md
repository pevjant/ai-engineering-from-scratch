# 오디오 평가 — WER, MOS, UTMOS, MMAU, FAD, 그리고 공개 리더보드

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 측정할 수 없는 것은 출시할 수도 없습니다. 이 레슨에서는 2026년 기준 오디오 작업마다 어떤 지표를 쓰는지 짚어 줍니다: ASR(WER, CER, RTFx), TTS(MOS, UTMOS, SECS, ASR 왕복 WER), 오디오 언어(MMAU, LongAudioBench), 음악(FAD, CLAP), 화자(EER). 그리고 비교에 쓰이는 리더보드까지 소개합니다.

**유형:** 학습(Learn)
**언어:** Python
**선수 지식:** 페이즈 6 · 04, 06, 07, 09, 10; 페이즈 2 · 09 (모델 평가)
**시간:** 약 60분

## 문제 상황

오디오 작업마다 여러 지표가 쓰이고, 각 지표는 서로 다른 축을 측정합니다. 잘못된 지표를 쓰면 대시보드에서는 멋져 보이지만 프로덕션(운영 환경)에서는 형편없는 모델을 출시하게 됩니다. 2026년의 표준 목록:

| 작업 | 1차 지표 | 2차 지표 |
|------|---------|-----------|
| ASR | WER | CER · RTFx · 첫 토큰 지연 시간 |
| TTS | MOS / UTMOS | SECS · ASR 왕복 WER · CER · TTFA |
| 음성 복제 | SECS (ECAPA 코사인) | MOS · CER |
| 화자 검증 | EER | 운영 지점에서의 minDCF · FAR / FRR |
| 화자 분리(diarization) | DER | JER · 화자 혼동 |
| 오디오 분류 | top-1 · mAP | macro F1 · 클래스별 재현율 |
| 음악 생성 | FAD | CLAP · 청취 패널 MOS |
| 오디오 언어 모델 | MMAU-Pro | LongAudioBench · AudioCaps FENSE |
| 스트리밍 S2S | 지연 시간 P50/P95 | WER · MOS |

## 핵심 개념

![오디오 평가 매트릭스 — 지표 vs 작업 vs 2026 리더보드](../assets/eval-landscape.svg)

### ASR 지표

**WER (Word Error Rate, 단어 오류율).** `(S + D + I) / N`. 채점 전에 소문자로 바꾸고, 구두점을 제거하고, 숫자를 정규화합니다. `jiwer`나 OpenAI의 `whisper_normalizer`를 쓰세요. 5% 미만이면 읽기 음성 기준 사람과 맞먹는 수준입니다.

**CER (Character Error Rate, 문자 오류율).** 같은 공식을 문자 단위로 적용합니다. 단어 경계를 나누기 애매한 성조 언어(중국어, 광둥어)에서 사용합니다.

**RTFx (역실시간 배수).** 벽시계 시간 1초당 처리한 오디오의 초 수. 높을수록 좋습니다. Parakeet-TDT는 3380배를 기록합니다. Whisper-large-v3는 약 30배입니다.

**첫 토큰 지연 시간.** 오디오 입력부터 첫 전사(transcript) 토큰까지의 벽시계 시간. 스트리밍에서는 결정적입니다. Deepgram Nova-3: 약 150 ms.

### TTS 지표

**MOS (Mean Opinion Score, 평균 의견 점수).** 사람이 매기는 1-5점 척도. 금본위제 표준이지만 느립니다. 샘플당 청취자 20명 이상, 모델당 샘플 100개 이상을 모읍니다.

**UTMOS (2022-2026).** 학습된 MOS 예측기. 표준 벤치마크에서 사람의 MOS와 약 0.9의 상관관계를 보입니다. F5-TTS: UTMOS 3.95; 실제 정답(ground truth): 4.08.

**SECS (Speaker Encoder Cosine Similarity).** 음성 복제용. 기준 음성과 복제 결과의 ECAPA 임베딩 코사인 유사도입니다. 0.75 초과면 알아볼 수 있는 복제본입니다.

**ASR 왕복 WER (WER-on-ASR-round-trip).** TTS 출력물에 Whisper를 돌리고, 입력 텍스트와 비교해 WER을 계산합니다. 알아듣기 어려워진 부분(지능성 퇴보)을 잡아 냅니다. 2026년 SOTA: CER 2% 미만.

**TTFA (time-to-first-audio, 첫 오디오까지의 시간).** 벽시계 기준 지연 시간입니다. Kokoro-82M: 약 100 ms; F5-TTS: 약 1초.

### 음성 복제 전용 지표

**SECS + MOS + CER** 세트로 봅니다. SECS는 높지만 MOS가 낮다면 음색은 맞는데 부자연스럽다는 뜻이고, 반대라면 자연스럽지만 다른 사람의 목소리라는 뜻입니다.

### 화자 검증

**EER (Equal Error Rate, 등오류율).** 오수용률(False Accept Rate)과 오거부률(False Reject Rate)이 같아지는 임계값입니다. VoxCeleb1-O에서 ECAPA는 0.87%입니다.

**minDCF (최소 탐지 비용, min Detection Cost).** 선택한 운영 지점(보통 FAR=0.01)에서의 가중 비용입니다. EER보다 프로덕션과 더 관련이 깊습니다.

### 화자 분리(diarization)

**DER (Diarization Error Rate).** `(FA + Miss + Confusion) / total_speaker_time`. 놓친 발화 + 허위 경보 발화 + 화자 혼동을 각각 비율로 더한 값입니다. AMI 회의 데이터에서 DER 10-20%가 현실적인 수준입니다. pyannote 3.1 + Precision-2 상용 조합은 잘 녹음된 오디오에서 DER 10% 미만입니다.

**JER (Jaccard Error Rate).** DER의 대안으로, 짧은 구간 편향에 강합니다.

### 오디오 분류

다중 레이블: 모든 클래스에 걸쳐 **mAP (mean Average Precision)**. AudioSet에서 BEATs-iter3는 0.548 mAP입니다.

단일 선택 다중 클래스: **top-1, top-5 정확도**. Speech Commands v2: 99.0% top-1 (Audio-MAE).

불균형 데이터: **macro F1** + **클래스별 재현율**. 반드시 클래스별로 보고하세요 — 집계 정확도는 어떤 클래스가 실패하는지 숨겨 버립니다.

### 음악 생성

**FAD (Fréchet Audio Distance).** 진짜 오디오와 생성 오디오의 VGGish 임베딩 분포 사이 거리. MusicCaps에서 MusicGen-small은 4.5. MusicLM은 4.0. 낮을수록 좋습니다.

**CLAP 점수.** CLAP 임베딩으로 계산한 텍스트-오디오 정렬 점수입니다. 0.3 초과면 그럭저럭 정렬이 잘 된 것입니다.

**청취 패널 MOS.** 소비자용 음악의 최종 판정은 여전히 이것입니다. Suno v5는 TTS Arena에서 ELO 1293(사람의 쌍 비교 선호도 기반)입니다.

### 오디오 언어 벤치마크

**MMAU (Massive Multi-Audio Understanding).** 1만 개의 오디오-질문 쌍.

**MMAU-Pro.** 어려운 문항 1800개, 네 범주: 음성 / 소리 / 음악 / 다중 오디오. 4지선다 랜덤 확률은 25%. Gemini 2.5 Pro 전체 약 60%; 다중 오디오는 모든 모델에서 약 22%.

**LongAudioBench.** 수 분 길이 클립에 의미 기반 질의를 던지는 벤치마크. Audio Flamingo Next가 Gemini 2.5 Pro를 앞섭니다.

**AudioCaps / Clotho.** 캡셔닝 벤치마크. SPICE, CIDEr, FENSE 지표를 씁니다.

### 스트리밍 음성 대 음성(speech-to-speech)

**지연 시간 P50 / P95 / P99.** 사용자 발화 끝부터 첫 음성 응답이 들리기까지의 벽시계 시간. Moshi: 200 ms; GPT-4o Realtime: 300 ms.

출력물에 대한 **WER / MOS**.

**바지인(barge-in) 반응성.** 사용자가 끼어들어 말하기 시작한 시점부터 어시스턴트가 입을 다물 때까지의 시간. 목표는 150 ms 미만입니다.

### 2026년의 리더보드

| 리더보드 | 트랙 | URL |
|------------|--------|-----|
| Open ASR Leaderboard (HF) | 영어 + 다국어 + 장문 | `huggingface.co/spaces/hf-audio/open_asr_leaderboard` |
| TTS Arena (HF) | 영어 TTS | `huggingface.co/spaces/TTS-AGI/TTS-Arena` |
| Artificial Analysis Speech | TTS + STT, 쌍 비교 투표 기반 ELO | `artificialanalysis.ai/speech` |
| MMAU-Pro | LALM 추론 | `mmaubenchmark.github.io` |
| SpeakerBench / VoxSRC | 화자 인식 | `voxsrc.github.io` |
| MMAU 음악 서브셋 | 음악 LALM | (MMAU 내부) |
| HEAR benchmark | 자기지도 학습 오디오 | `hearbenchmark.com` |

```figure
sp-wer-align
```

## 만들어 보기

### 단계 1: 정규화를 적용한 WER

```python
from jiwer import wer, Compose, ToLowerCase, RemovePunctuation, Strip

transform = Compose([ToLowerCase(), RemovePunctuation(), Strip()])
score = wer(
    truth="Please turn on the lights.",
    hypothesis="please turn on the light",
    truth_transform=transform,
    hypothesis_transform=transform,
)
# 약 0.17
```

### 단계 2: TTS 왕복 WER

```python
def ttr_wer(tts_model, asr_model, texts):
    errors = []
    for txt in texts:
        audio = tts_model.synthesize(txt)
        recog = asr_model.transcribe(audio)
        errors.append(wer(truth=txt, hypothesis=recog))
    return sum(errors) / len(errors)
```

### 단계 3: 음성 복제를 위한 SECS

```python
from speechbrain.inference.speaker import EncoderClassifier
sv = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb")

emb_ref = sv.encode_batch(load_wav("reference.wav"))
emb_clone = sv.encode_batch(load_wav("cloned.wav"))
secs = torch.nn.functional.cosine_similarity(emb_ref, emb_clone, dim=-1).item()
```

### 단계 4: 음악 생성을 위한 FAD

```python
from frechet_audio_distance import FrechetAudioDistance
fad = FrechetAudioDistance()
score = fad.get_fad_score("generated_folder/", "reference_folder/")
```

### 단계 5: 화자 검증을 위한 EER (레슨 6과 같은 코드)

```python
def eer(same_scores, diff_scores):
    thresholds = sorted(set(same_scores + diff_scores))
    best = (1.0, 0.0)
    for t in thresholds:
        far = sum(1 for s in diff_scores if s >= t) / len(diff_scores)
        frr = sum(1 for s in same_scores if s < t) / len(same_scores)
        if abs(far - frr) < best[0]:
            best = (abs(far - frr), (far + frr) / 2)
    return best[1]
```

## 활용하기

모든 배포에는 모델을 업데이트할 때마다 돌리는 고정된 평가 하니스(eval harness)를 붙이세요. 세 가지 철칙:

1. **채점 전에 정규화한다.** 소문자화, 구두점 제거, 숫자 확장. 정규화 규칙도 함께 보고합니다.
2. **평균이 아니라 분포를 보고한다.** 지연 시간은 P50/P95/P99. 분류는 클래스별 재현율. MMAU는 범주별 결과.
3. **표준 공개 벤치마크를 하나는 반드시 돌린다.** 프로덕션 데이터와 다르더라도 Open ASR / TTS Arena / MMAU에 대한 결과를 보고하면 검토자가 조건을 같게 두고 비교할 수 있습니다.

## 주의할 함정

- **UTMOS 외삽 오류.** VCTK 스타일의 깨끗한 음성으로 학습했기 때문에, 시끄럽거나 복제되었거나 감정이 실린 오디오는 잘 평가하지 못합니다.
- **MOS 패널 편향.** 아마존 메커니컬 터크(Mechanical Turk) 작업자 20명은 목표 사용자 20명이 아닙니다. 판돈이 크다면 도메인 전문 패널에 돈을 쓰세요.
- **FAD는 기준 집합에 의존합니다.** 여러 모델을 비교할 때는 항상 같은 기준 분포를 사용하세요.
- **집계 WER.** 전체 WER 5%가 억양이 있는 음성에서의 WER 30%를 숨기고 있을 수 있습니다. 인구 통계별 슬라이스로 보고하세요.
- **공개 벤치마크 포화.** 대부분의 최신 프론티어 모델은 표준 벤치마크에서 천장에 가까운 점수를 냅니다. 여러분의 실제 트래픽을 반영한 사내 홀드아웃(held-out) 세트를 따로 만드세요.

## 출시하기

`outputs/skill-audio-evaluator.md`로 저장합니다. 오디오 모델 릴리스마다 지표, 벤치마크, 보고 형식을 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행합니다. 장난감 입력에 대해 WER / CER / EER / SECS / FAD 비슷한 것 / MMAU 비슷한 것을 계산합니다.
2. **보통.** TTS 왕복 WER 하니스를 만듭니다. Kokoro 또는 F5-TTS 출력물을 Whisper에 통과시키고, 50개 프롬프트에 걸쳐 WER을 계산합니다. WER이 10%를 넘는 프롬프트에 표시를 붙입니다.
3. **어려움.** 레슨 10에서 선택한 LALM을 MMAU-Pro의 speech + multi-audio 서브셋(각 50문항)으로 채점합니다. 범주별 정확도를 보고하고 공개된 수치와 비교합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| WER | ASR 점수 | 정규화 후 단어 수준의 `(S+D+I)/N`. |
| CER | 문자 단위 WER | 성조 언어나 문자 단위 시스템용. |
| MOS | 사람의 평가 점수 | 1-5점 척도; 청취자 20명 이상 × 샘플 100개. |
| UTMOS | ML 기반 MOS 예측기 | 학습된 모델; 사람 MOS와 약 0.9 상관. |
| SECS | 음성 복제 유사도 | 기준 음성과 복제본 사이 ECAPA 코사인. |
| EER | 화자 검증 점수 | FAR = FRR이 되는 임계값. |
| DER | 화자 분리 점수 | (FA + Miss + Confusion) / 전체. |
| FAD | 음악 생성 품질 | VGGish 임베딩에 대한 Fréchet 거리. |
| RTFx | 처리량 | 벽시계 시간 1초당 처리한 오디오의 초 수. |

## 더 읽을거리

- [jiwer](https://github.com/jitsi/jiwer) — 정규화 유틸리티를 갖춘 WER/CER 라이브러리.
- [UTMOS (Saeki et al. 2022)](https://arxiv.org/abs/2204.02152) — 학습된 MOS 예측기.
- [Fréchet Audio Distance (Kilgour et al. 2019)](https://arxiv.org/abs/1812.08466) — 음악 생성의 표준.
- [Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) — 2026년 실시간 순위.
- [TTS Arena](https://huggingface.co/spaces/TTS-AGI/TTS-Arena) — 사람 투표 기반 TTS 리더보드.
- [MMAU-Pro benchmark](https://mmaubenchmark.github.io/) — LALM 추론 리더보드.
- [HEAR benchmark](https://hearbenchmark.com/) — 오디오 SSL 벤치마크.
