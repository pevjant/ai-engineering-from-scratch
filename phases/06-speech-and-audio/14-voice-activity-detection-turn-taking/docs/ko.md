> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 음성 활동 탐지와 턴 교대 — Silero, Cobra, 그리고 플러시 트릭

> 모든 음성 에이전트의 명운은 두 가지 판정에 달려 있습니다: 사용자가 지금 말하고 있는가, 그리고 말을 끝냈는가. VAD가 첫 번째에 답합니다. 턴 탐지(VAD + 침묵 행오버 + 의미적 엔드포인트 모델)가 두 번째에 답합니다. 하나만 틀려도 에이전트는 사용자 말을 끊거나, 말을 멈추지 못하거나 둘 중 하나입니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 11 (실시간 오디오), 페이즈 6 · 12 (음성 비서)
**소요 시간:** 약 45분

## 문제 상황

음성 에이전트는 20 ms 청크 하나하나에 대해 서로 다른 세 가지 판정을 합니다:

1. **이 프레임은 음성인가?** — VAD. 프레임별 이진 판정.
2. **사용자가 새 발화를 시작했나?** — 시작(onset) 탐지.
3. **사용자가 말을 끝냈나?** — 엔드포인팅(end-pointing, 턴 종료).

천진난만한 답(에너지 임계값)은 소음이 있으면 무너집니다 — 차 소리, 키보드 소리, 군중 웅성거림. 2026년의 답: Silero VAD(오픈, 딥러닝 기반) + 턴 탐지 모델(의미적 엔드포인팅) + VAD로 보정한 침묵 행오버.

## 개념

![VAD 폭포: 에너지 → Silero → 턴 탐지기 → 플러시 트릭](../assets/vad-turn-taking.svg)

### 3단계 VAD 폭포

**1단계: 에너지 게이트.** 가장 싸다. RMS를 -40 dBFS에서 임계값 판정합니다. 명백한 침묵은 걸러 주지만 임계값을 넘는 소음엔 전부 반응합니다.

**2단계: Silero VAD** (2020-2026, MIT). 파라미터 100만 개. 6,000개 이상의 언어로 학습. CPU 스레드 하나에서 30 ms 청크당 약 1 ms로 돕니다. FPR 5%에서 TPR 87.7%. 오픈소스 기본 선택입니다.

**3단계: 의미적 턴 탐지기.** LiveKit의 턴 탐지 모델(2024-2026) 또는 자체 소형 분류기. "문장 중간의 멈춤"과 "말 끝남"을 구분합니다. 침묵만 보지 않고 언어적 맥락(억양 + 최근 단어들)을 봅니다.

### 핵심 파라미터와 기본값

- **임계값.** Silero는 확률을 내놓습니다. &gt; 0.5(기본) 또는 &gt; 0.3(민감)에서 음성으로 판정합니다. 임계값을 낮추면 첫 단어 잘림은 줄지만 오탐이 늘어납니다.
- **최소 발화 길이.** 250 ms 미만의 짧은 '발화'는 버립니다 — 보통 기침이나 의자 소음입니다.
- **침묵 행오버 (엔드포인팅).** VAD가 0으로 떨어진 뒤에도 500~800 ms 기다렸다가 턴 종료를 선언합니다. 너무 짧으면 사용자 말을 끊고, 너무 길면 답답하게 느껴집니다.
- **프리롤 버퍼.** VAD가 울리기 전 300~500 ms의 오디오를 보관합니다. "저기"가 잘리는 것을 막아 줍니다.

### 플러시 트릭 (Kyutai 2025)

스트리밍 STT 모델에는 룩어헤드(look-ahead) 지연이 있습니다(Kyutai STT-1B는 500 ms, STT-2.6B는 2.5초). 평소라면 발화가 끝난 뒤 그만큼 기다려야 전사본이 나옵니다. 플러시 트릭: VAD가 발화 종료를 울리면 STT에 **플러시 신호**를 보내 즉시 출력을 강제합니다. STT는 실시간의 약 4배로 처리하므로, 500 ms짜리 버퍼는 약 125 ms에 끝납니다.

엔드투엔드: VAD 125 ms + 플러시 STT = 대화 지연 시간.

### 2026년 VAD 비교

| VAD | FPR 5%에서의 TPR | 지연 시간 | 라이선스 |
|-----|--------------|---------|---------|
| WebRTC VAD (Google, 2013) | 50.0% | 30 ms | BSD |
| Silero VAD (2020-2026) | 87.7% | ~1 ms | MIT |
| Cobra VAD (Picovoice) | 98.9% | ~1 ms | 상용 |
| pyannote segmentation | 95% | ~10 ms | MIT 비슷함 |

기본값으로는 Silero가 맞습니다. 컴플라이언스 / 정확도 업그레이드는 Cobra입니다. 에너지 전용 VAD가 2026년 프로덕션에 있을 자리는 없습니다.

```figure
sp-vad-cascade
```

## 직접 만들어 보기

### 단계 1: 에너지 게이트

```python
def energy_vad(chunk, threshold_dbfs=-40.0):
    rms = (sum(x * x for x in chunk) / len(chunk)) ** 0.5
    dbfs = 20.0 * math.log10(max(rms, 1e-10))
    return dbfs > threshold_dbfs
```

### 단계 2: Python에서 Silero VAD

```python
from silero_vad import load_silero_vad, get_speech_timestamps

vad = load_silero_vad()
audio = torch.tensor(waveform_16k, dtype=torch.float32)
segments = get_speech_timestamps(
    audio, vad, sampling_rate=16000,
    threshold=0.5,
    min_speech_duration_ms=250,
    min_silence_duration_ms=500,
    speech_pad_ms=300,
)
for s in segments:
    print(f"{s['start']/16000:.2f}s - {s['end']/16000:.2f}s")
```

### 단계 3: 턴 종료 상태 머신

```python
class TurnDetector:
    def __init__(self, silence_hangover_ms=500, min_speech_ms=250):
        self.state = "idle"
        self.speech_ms = 0
        self.silence_ms = 0
        self.silence_hangover_ms = silence_hangover_ms
        self.min_speech_ms = min_speech_ms

    def update(self, is_speech, chunk_ms=20):
        if is_speech:
            self.speech_ms += chunk_ms
            self.silence_ms = 0
            if self.state == "idle" and self.speech_ms >= self.min_speech_ms:
                self.state = "speaking"
                return "START"
        else:
            self.silence_ms += chunk_ms
            if self.state == "speaking" and self.silence_ms >= self.silence_hangover_ms:
                self.state = "idle"
                self.speech_ms = 0
                return "END"
        return None
```

### 단계 4: 플러시 트릭 뼈대

```python
def flush_on_end(stt_client, audio_buffer):
    stt_client.send_audio(audio_buffer)
    stt_client.send_flush()
    return stt_client.recv_transcript(timeout_ms=150)
```

이 방법이 되려면 STT(Kyutai, Deepgram, AssemblyAI)가 플러시를 지원해야 합니다. Whisper 스트리밍은 안 됩니다 — 블록 기반이라 항상 청크를 기다립니다.

## 사용해 보기

| 상황 | VAD 선택 |
|-----------|-----------|
| 오픈, 빠름, 범용 | Silero VAD |
| 상용 콜센터 | Cobra VAD |
| 온디바이스 (폰) | Silero VAD ONNX |
| 연구 / 화자 분리 | pyannote segmentation |
| 의존성 없는 폴백 | WebRTC VAD (레거시) |
| 턴 종료 품질이 필요할 때 | Silero + LiveKit turn-detector 겹쳐 쓰기 |

경험칙: 정말로 다른 선택지가 없는 게 아니라면 에너지 전용 VAD를 출시하지 마세요.

## 함정들

- **고정 임계값.** 조용한 곳에선 되고 시끄러운 곳에선 실패합니다. 온디바이스에서 보정하거나 Silero로 갈아타세요.
- **너무 짧은 침묵 행오버.** 에이전트가 문장 중간에 끼어듭니다. 대화 음성에는 500~800 ms가 적당합니다.
- **너무 긴 행오버.** 답답하게 느껴집니다. 대상 사용자와 A/B 테스트하세요.
- **프리롤 버퍼 없음.** 사용자 오디오의 처음 200~300 ms가 사라집니다. 항상 굴러가는(rolling) 프리롤을 유지하세요.
- **의미적 엔드포인팅 무시.** "음, 잠깐만 생각 좀 해볼게..."에는 긴 멈춤이 섞여 있습니다. 사용자는 생각하다 끊기는 걸 미워합니다. LiveKit turn-detector 같은 것을 쓰세요.

## 출시해 보기

`outputs/skill-vad-tuner.md`로 저장하세요. 워크로드에 맞는 VAD 모델, 임계값, 행오버, 프리롤, 턴 탐지 전략을 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 발화 + 침묵 + 발화 + 기침 시퀀스를 시뮬레이션하고 세 단계 VAD를 모두 시험합니다.
2. **보통.** `silero-vad`를 설치해 5분짜리 녹음을 처리하고, 첫 단어 잘림과 오탐을 동시에 최소화하도록 임계값을 튜닝합니다. 정밀도/재현율을 보고합니다.
3. **어려움.** 미니 턴 탐지기를 만들어 보세요: Silero VAD + 마지막 10개 단어의 임베딩 위의 3층 MLP(sentence-transformers 사용). 손으로 레이블링한 턴 종료 데이터셋으로 학습합니다. Silero 단독 대비 F1을 10% 높입니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| VAD | 음성 탐지기 | 프레임별 이진 판정: 이것이 음성인가? |
| 턴 탐지 | 엔드포인팅 | VAD + 침묵 행오버 + 의미적 엔드포인트. |
| 침묵 행오버 | 발화 후 대기 | 턴 종료를 선언하기 전 기다리는 시간. 500~800 ms. |
| 프리롤 | 발화 이전 버퍼 | VAD가 울리기 전 300~500 ms의 오디오를 보관한다. |
| 플러시 트릭 | Kyutai 해법 | VAD → STT 플러시 → 500 ms 대신 125 ms. |
| 의미적 엔드포인트 | "끝낼 생각이었나?" | 침묵만이 아니라 단어를 보는 ML 분류기. |
| FPR 5%에서의 TPR | ROC 지점 | 표준 VAD 벤치마크. Silero 87.7%, WebRTC 50%. |

## 더 읽을거리

- [Silero VAD](https://github.com/snakers4/silero-vad) — 참조 오픈 VAD.
- [Picovoice Cobra VAD](https://picovoice.ai/products/cobra/) — 상용 정확도 리더.
- [Kyutai — Unmute + 플러시 트릭](https://kyutai.org/stt) — 200 ms 미만의 엔지니어링 기술.
- [LiveKit — 턴 탐지](https://docs.livekit.io/agents/logic/turns/) — 프로덕션 속 의미적 엔드포인팅.
- [WebRTC VAD](https://webrtc.googlesource.com/src/) — 레거시 베이스라인.
- [pyannote segmentation](https://github.com/pyannote/pyannote-audio) — 화자 분리 등급의 분할.
