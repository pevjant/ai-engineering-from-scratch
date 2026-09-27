# 음성 인식 (ASR) — CTC, RNN-T, 어텐션 (Speech Recognition)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 음성 인식은 모든 시간 단계에서 하는 오디오 분류에, 영어와 침묵을 아는 시퀀스 모델로 접착한 것입니다. CTC, RNN-T, 어텐션이 그 세 가지 방법입니다. 하나를 고르고 이유를 이해하세요.

**유형:** Build
**사용 언어:** Python
**선수 지식:** 페이즈 6 · 02(스펙트로그램과 멜), 페이즈 5 · 08(텍스트를 위한 CNN과 RNN), 페이즈 5 · 10(어텐션)
**소요 시간:** 약 45분

## 문제 상황

10초짜리 16 kHz 클립이 있습니다. 문자열을 원합니다: "turn on the kitchen lights". 난제는 구조적인 것입니다: 오디오 프레임은 문자와 일대일로 맞지 않습니다. "okay"라는 단어는 200 ms가 걸릴 수도, 1200 ms가 걸릴 수도 있습니다. 발화 사이사이에 침묵이 끼어 있습니다. 어떤 음소는 다른 음소보다 깁니다. 출력 토큰의 개수는 미리 알 수 없습니다.

세 가지 정식화가 이걸 풉니다:

1. **CTC(Connectionist Temporal Classification).** 특수한 *blank*를 포함한 프레임별 토큰 확률을 내놓습니다. 디코딩 시점에 반복과 blank를 접어 정리합니다. 비자기회귀적이고 빠릅니다. wav2vec 2.0, MMS가 사용합니다.
2. **RNN-T(Recurrent Neural Network Transducer).** 조인트 네트워크가 인코더 프레임과 이전 토큰을 보고 다음 토큰을 예측합니다. 스트리밍 가능합니다. Google의 온디바이스 ASR, NVIDIA Parakeet이 사용합니다.
3. **어텐션 인코더-디코더.** 인코더가 오디오를 은닉 상태로 압축하고, 디코더가 크로스 어텐션으로 자기회귀적으로 토큰을 생성합니다. Whisper, SeamlessM4T가 사용합니다.

2026년 LibriSpeech test-clean 최고 수준 WER은 1.4%(Parakeet-TDT-1.1B, NVIDIA)와 1.58%(Whisper-Large-v3-turbo)입니다. 숫자 차이는 미미하지만, 배포 차이는 어마어마합니다.

## 개념

![세 가지 ASR 정식화: CTC, RNN-T, 어텐션 인코더-디코더](../assets/asr-formulations.svg)

**CTC 직관.** 인코더가 `V+1`개 토큰(V개 문자 + blank)에 대한 `T`개의 프레임별 분포를 출력하게 합니다. 길이 `U < T`인 목표 문자열 `y`에 대해, `y`로 접어지는 모든 프레임 정렬이 후보가 됩니다. CTC 손실은 그런 정렬 전부에 걸쳐 합산합니다. 추론: 프레임별 argmax, 반복 접기, blank 제거.

장점: 비자기회귀적, 스트리밍 가능, 선행 읽기(lookahead) 불필요. 단점: *조건부 독립 가정* — 각 프레임 예측이 다른 프레임과 독립이라 내부 언어 모델이 없습니다. 빔 서치나 얕은 융합(shallow fusion)으로 외부 LM을 붙여 보완합니다.

**RNN-T 직관.** 토큰 이력을 임베딩하는 *예측기(predictor)* 네트워크와, 예측기 상태와 인코더 프레임을 `V+1`(여기서 `+1`은 null / 출력 없음)에 대한 조인트 분포로 합치는 *조이너(joiner)*가 추가됩니다. CTC가 무시한 조건부 의존성을 명시적으로 모델링합니다. 각 단계가 과거 프레임과 과거 토큰에만 의존하므로 스트리밍이 가능합니다.

장점: 스트리밍 가능 + 내부 LM. 단점: 학습이 더 복잡하고 메모리를 많이 먹습니다(3D 손실 격자); RNN-T 손실 커널은 그 자체로 한 라이브러리 카테고리입니다.

**어텐션 인코더-디코더.** 로그-멜 프레임 위의 인코더(트랜스포머 6~32층). 디코더(트랜스포머 6~32층)는 인코더 출력에 크로스 어텐션하며 자기회귀적으로 토큰을 생성합니다. 정렬 제약이 없습니다 — 어텐션은 오디오 어디든 볼 수 있습니다. 어텐션을 제한하지 않으면 스트리밍 불가입니다(chunked Whisper-Streaming, 2024).

장점: 오프라인 ASR에서 최고 품질, 표준 seq2seq 도구로 학습이 쉬움. 단점: 자기회귀 지연 시간이 출력 길이에 비례; 공학적 노력 없이는 스트리밍 불가.

### WER: 단 하나의 숫자

**Word Error Rate(단어 오류율)** = `(S + D + I) / N`. 여기서 S=대체, D=삭제, I=삽입, N=정답 단어 수입니다. 단어 수준의 레벤슈타인 편집 거리와 일치합니다. 낮을수록 좋습니다. WER이 20%를 넘으면 보통 사용 불가이고, 5% 아래면 읽기 음성 기준 사람 수준입니다. 표준 벤치마크의 2026년 숫자:

| 모델 | LibriSpeech test-clean | LibriSpeech test-other | 크기 |
|-------|------------------------|------------------------|------|
| Parakeet-TDT-1.1B | 1.40% | 2.78% | 1.1B 파라미터 |
| Whisper-Large-v3-turbo | 1.58% | 3.03% | 809M |
| Canary-1B Flash | 1.48% | 2.87% | 1B |
| Seamless M4T v2 | 1.7% | 3.5% | 2.3B |

이 모두 인코더-디코더 또는 RNN-T 기반입니다. 순수 CTC 시스템(wav2vec 2.0)은 test-clean에서 1.8~2.1% 정도입니다.

```figure
ctc-collapse
```

## 직접 만들기

### 단계 1: 탐욕적 CTC 디코딩

```python
def ctc_greedy(frame_logits, blank=0, vocab=None):
    # frame_logits: 프레임별 확률 벡터의 목록
    preds = [max(range(len(p)), key=lambda i: p[i]) for p in frame_logits]
    out = []
    prev = -1
    for p in preds:
        if p != prev and p != blank:
            out.append(p)
        prev = p
    return "".join(vocab[i] for i in out) if vocab else out
```

두 가지 규칙: 연속 반복은 접고, blank는 버립니다. 예: `a a _ _ a b b _ c` → `a a b c`.

### 단계 2: 빔 서치 CTC

```python
def ctc_beam(frame_logits, beam=8, blank=0):
    import math
    beams = [([], 0.0)]  # (tokens, log_prob)
    for p in frame_logits:
        log_p = [math.log(max(pi, 1e-10)) for pi in p]
        candidates = []
        for seq, lp in beams:
            for t, lpt in enumerate(log_p):
                new = seq[:] if t == blank else (seq + [t] if not seq or seq[-1] != t else seq)
                candidates.append((new, lp + lpt))
        candidates.sort(key=lambda x: -x[1])
        beams = candidates[:beam]
    return beams[0][0]
```

프로덕션은 LM 융합이 있는 접두사 트리(prefix tree) 빔 서치를 씁니다; 여기 있는 것은 개념적 뼈대입니다.

### 단계 3: WER

```python
def wer(ref, hyp):
    r, h = ref.split(), hyp.split()
    dp = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        dp[i][0] = i
    for j in range(len(h) + 1):
        dp[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[len(r)][len(h)] / max(1, len(r))
```

### 단계 4: Whisper로 추론하기

```python
import whisper
model = whisper.load_model("large-v3-turbo")
result = model.transcribe("clip.wav")
print(result["text"])
```

2026년 가장 강한 범용 ASR을 위한 한 줄 코드입니다. 24 GB GPU에서 실시간의 약 20배로 돌아갑니다.

### 단계 5: Parakeet 또는 wav2vec 2.0으로 스트리밍

```python
from transformers import pipeline
asr = pipeline("automatic-speech-recognition", model="nvidia/parakeet-tdt-1.1b")
for chunk in streaming_audio():
    print(asr(chunk, return_timestamps=True))
```

스트리밍 ASR에는 청크 단위 인코더 어텐션과 이월 상태(carryover state)가 필요합니다; 이를 지원하는 라이브러리를 쓰세요(Parakeet은 NeMo, `transformers` 파이프라인은 `chunk_length_s`).

## 활용하기

2026년의 표준 스택:

| 상황 | 선택지 |
|-----------|------|
| 영어, 오프라인, 최고 품질 | Whisper-large-v3-turbo |
| 다국어, 강인함 | SeamlessM4T v2 |
| 스트리밍, 저지연 | Parakeet-TDT-1.1B 또는 Riva |
| 엣지, 모바일, 지연 500 ms 미만 | 양자화된 Whisper-Tiny 또는 Moonshine (2024) |
| 장문 | VAD 기반 청킹을 얹은 Whisper (WhisperX) |
| 도메인 특화(의료, 법률) | wav2vec 2.0 파인튜닝 + 도메인 LM 융합 |

## 2026년에도 계속 출시되는 실수들

- **VAD 없음.** 침묵에 Whisper를 돌리면 환각이 나옵니다("시청해 주셔서 감사합니다!"). 항상 VAD로 게이트하세요.
- **문자 vs 단어 vs 서브워드 WER.** 정규화(소문자화, 구두점 제거)*후에* 단어 수준 WER을 보고하세요.
- **언어 식별(LID) 드리프트.** Whisper의 자동 LID는 시끄러운 클립을 일본어나 웨일스어로 잘못 라우팅합니다; 알고 있다면 `language="en"`을 강제하세요.
- **청킹 없는 긴 클립.** Whisper의 윈도우는 30초입니다. 그보다 긴 것은 `chunk_length_s=30, stride=5`를 쓰세요.

## 출시하기

`outputs/skill-asr-picker.md`로 저장하세요. 주어진 배포 대상에 맞는 모델, 디코딩 전략, 청킹, LM 융합을 선택해 줍니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 손으로 만든 CTC 출력을 탐욕적으로 디코딩하고 정답 대비 WER을 계산합니다.
2. **보통.** 단계 2의 접두사 트리 빔 서치를 제대로 구현하세요(blank 병합 규칙을 처리). 10개 예시짜리 합성 데이터셋에서 탐욕적 디코딩과 비교하세요.
3. **어려움.** [LibriSpeech test-clean](https://www.openslr.org/12)에 `whisper-large-v3-turbo`를 적용해 보세요. 첫 100개 발화의 WER을 계산하고 공개된 수치와 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| CTC | blank 토큰 손실 | 모든 프레임-토큰 정렬에 대한 주변화; 비자기회귀. |
| RNN-T | 스트리밍 손실 | CTC + 다음 토큰 예측기; 어순을 다룸. |
| 어텐션 인코더-디코더 | Whisper 스타일 | 인코더 + 크로스 어텐션 디코더; 오프라인 품질 최고. |
| WER | 보고하는 그 숫자 | 단어 수준 `(S+D+I)/N`. |
| Blank | 공백 토큰 | CTC에서 "이 프레임은 출력 없음"을 알리는 특수 토큰. |
| LM 융합 | 외부 언어 모델 | 빔 서치 중 가중치가 적용된 LM 로그 확률을 더함. |
| VAD | 침묵 게이트 | 음성 활동 탐지기; 비음성 구간을 잘라냄. |

## 더 읽을거리

- [Graves et al. (2006). Connectionist Temporal Classification](https://www.cs.toronto.edu/~graves/icml_2006.pdf) — CTC 원 논문.
- [Graves (2012). Sequence Transduction with RNNs](https://arxiv.org/abs/1211.3711) — RNN-T 원 논문.
- [Radford et al. / OpenAI (2022). Whisper: Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — 2022년 표준 논문; 2024년 v3-turbo 확장.
- [NVIDIA NeMo — Parakeet-TDT 카드](https://huggingface.co/nvidia/parakeet-tdt-1.1b) — 2026년 Open ASR 리더보드 1위.
- [Hugging Face — Open ASR 리더보드](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) — 25개 이상 모델의 실시간 벤치마크.
