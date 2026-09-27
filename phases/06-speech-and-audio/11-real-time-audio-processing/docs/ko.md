> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 실시간 오디오 처리

> 배치 파이프라인은 파일 하나를 처리합니다. 실시간 파이프라인은 다음 20밀리초가 도착하기 전에 지금의 20밀리초를 처리해야 합니다. 모든 대화형 AI, 방송 스튜디오, 전화 봇의 생사가 이 지연 시간 예산에 달려 있습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 02 (스펙트로그램), 페이즈 6 · 04 (ASR), 페이즈 6 · 07 (TTS)
**소요 시간:** 약 75분

## 문제 상황

살아 있는 것처럼 느껴지는 음성 비서를 만들고 싶습니다. 사람 대화의 교대(turn-taking) 지연은 약 230 ms입니다(침묵이 끝나서 응답이 시작될 때까지). 500 ms를 넘으면 로봇처럼 느껴지고, 1500 ms를 넘으면 고장 났다고 느껴집니다. 2026년의 **듣기 → 이해 → 응답 준비 → 말하기** 전체 루프 예산은 이렇습니다:

| 단계 | 예산 |
|-------|--------|
| 마이크 → 버퍼 | 20 ms |
| VAD | 10 ms |
| ASR (스트리밍) | 150 ms |
| LLM (첫 토큰) | 100 ms |
| TTS (첫 청크) | 100 ms |
| 렌더 → 스피커 | 20 ms |
| **합계** | **약 400 ms** |

Moshi(Kyutai, 2024)는 완전 이중(full-duplex) 200 ms를 기록했습니다. GPT-4o-realtime (2024)은 약 320 ms입니다. 2022년의 직렬(cascaded) 파이프라인은 2500 ms에 그쳤죠. 10배 개선은 세 가지 기술에서 나왔습니다: (1) 어디서나 스트리밍, (2) 부분 결과를 내놓는 비동기 파이프라이닝, (3) 끼어들기 가능한 생성.

## 개념

![링 버퍼, VAD 게이트, 끼어들기를 갖춘 스트리밍 오디오 파이프라인](../assets/real-time.svg)

**프레임 / 청크 / 윈도우.** 실시간 오디오는 고정 크기 블록으로 흐릅니다. 흔한 선택은 20 ms(16 kHz에서 320 샘플)입니다. 이 흐름 속도를 다운스트림 전부가 따라가야 합니다.

**링 버퍼.** 고정 크기의 원형 버퍼. 생산자 스레드가 새 프레임을 쓰고, 소비자 스레드가 읽습니다. 핫 패스(hot path)에서의 메모리 할당을 막아 줍니다. 크기 ≈ 최대 지연 시간 × 샘플레이트. 16 kHz 2초짜리 링은 32,000 샘플입니다.

**VAD (음성 활동 탐지).** 아무도 말하지 않을 때는 다운스트림 작업을 막아 줍니다. Silero VAD 4.0 (2024)은 CPU에서 30 ms 프레임당 1 ms 미만으로 돕니다. `webrtcvad`는 더 오래된 대안입니다.

**스트리밍 ASR.** 오디오가 도착하는 대로 부분 전사본을 내놓는 모델입니다. 스트리밍 모드의 Parakeet-CTC-0.6B (NeMo, 2024)는 320 ms 지연으로 WER 2~5%를 냅니다. Whisper-Streaming (Macháček 외, 2023)은 Whisper를 청크 단위로 잘라 약 2초 지연의 준(準)스트리밍을 만듭니다.

**끼어들기(interruption).** 사용자가 비서가 말하는 도중에 말을 하면, (a) 바지 인(barge-in)을 감지하고, (b) TTS를 멈추고, (c) 남은 LLM 출력을 버려야 합니다. 모든 것을 100 ms 안에 해내지 못하면 사용자는 귀 먼 비서를 경험합니다.

**WebRTC Opus 전송.** 20 ms 프레임, 48 kHz, 8~128 kbps 적응형 비트레이트. 브라우저와 모바일의 표준입니다. LiveKit, Daily.co, Pion이 2026년 음성 앱 구축 스택입니다.

**지터 버퍼.** 네트워크 패킷은 순서가 어긋나거나 늦게 도착합니다. 지터 버퍼가 재정렬하고 매끈하게 만들어 줍니다. 너무 작으면 들리는 공백이 생기고, 너무 크면 지연이 커집니다. 보통 60~80 ms입니다.

### 자주 겪는 골칫거리

- **스레드 경쟁.** Python의 GIL + 무거운 모델 조합은 오디오 스레드를 굶길 수 있습니다. C 콜백 기반 오디오 라이브러리(sounddevice, PortAudio)를 쓰고, 핫 패스에서 Python을 치워 두세요.
- **샘플레이트 변환 지연.** 파이프라인 안에서 리샘플링하면 5~20 ms가 더 듭니다. 처음부터 리샘플하거나 무지연 리샘플러(PolyPhase, `soxr_hq`)를 쓰세요.
- **TTS 예열.** Kokoro처럼 빠른 TTS조차 첫 요청에는 100~200 ms의 워밍업이 듭니다. 모델을 캐시하고, 실제 첫 턴 전에 더미 실행으로 예열해 두세요.
- **에코 제거.** AEC가 없으면 TTS 출력이 다시 마이크로 들어와 봇 자기 목소리로 ASR을 켜 버립니다. WebRTC AEC3가 오픈소스 기본 선택입니다.

```figure
nyquist-aliasing
```

## 직접 만들어 보기

### 단계 1: 링 버퍼

```python
import collections

class RingBuffer:
    def __init__(self, capacity):
        self.buf = collections.deque(maxlen=capacity)
    def write(self, frame):
        self.buf.extend(frame)
    def read(self, n):
        return [self.buf.popleft() for _ in range(min(n, len(self.buf)))]
    def level(self):
        return len(self.buf)
```

용량이 최대 버퍼링 지연을 정합니다. 16 kHz에서 32,000 샘플 = 2초.

### 단계 2: VAD 게이트

```python
def simple_energy_vad(frame, threshold=0.01):
    return sum(x * x for x in frame) / len(frame) > threshold ** 2
```

프로덕션에서는 Silero VAD로 교체하세요:

```python
import torch
vad, _ = torch.hub.load("snakers4/silero-vad", "silero_vad")
is_speech = vad(torch.tensor(frame), 16000).item() > 0.5
```

### 단계 3: 스트리밍 ASR

```python
# NeMo를 통한 Parakeet-CTC-0.6B 스트리밍
from nemo.collections.asr.models import EncDecCTCModelBPE
asr = EncDecCTCModelBPE.from_pretrained("nvidia/parakeet-ctc-0.6b")
# chunk_ms=320 ms, look_ahead_ms=80 ms
for chunk in audio_stream():
    partial_text = asr.transcribe_streaming(chunk)
    print(partial_text, end="\r")
```

### 단계 4: 끼어들기 처리기

```python
class Dialog:
    def __init__(self):
        self.tts_task = None

    def on_user_speech(self, frame):
        if self.tts_task and not self.tts_task.done():
            self.tts_task.cancel()   # 바지 인
        # 그다음 스트리밍 ASR로 넘긴다

    def on_final_user_utterance(self, text):
        self.tts_task = asyncio.create_task(self.reply(text))

    async def reply(self, text):
        async for tts_chunk in llm_then_tts(text):
            speaker.write(tts_chunk)
```

비동기 I/O와 취소 가능한 TTS 스트리밍에 달려 있습니다. 오디오 트랙에서 WebRTC peerconnection.stop()을 부르는 것이 정석적인 방법입니다.

## 사용해 보기

2026년 스택:

| 계층 | 선택 |
|-------|------|
| 전송 | LiveKit (WebRTC) 또는 Pion (Go) |
| VAD | Silero VAD 4.0 |
| 스트리밍 ASR | Parakeet-CTC-0.6B 또는 Whisper-Streaming |
| LLM 첫 토큰 | Groq, Cerebras, vLLM 스트리밍 |
| 스트리밍 TTS | Kokoro 또는 ElevenLabs Turbo v2.5 |
| 에코 제거 | WebRTC AEC3 |
| 엔드투엔드 네이티브 | OpenAI Realtime API 또는 Moshi |

## 함정들

- **안전을 부르는 500 ms 버퍼링.** 버퍼 자체가 지연 시간의 바닥입니다. 줄이세요.
- **스레드 고정(affinity) 안 함.** UI보다 우선순위가 낮은 스레드에서 오디오 콜백을 돌리면 부하 시 끊김이 생깁니다.
- **너무 작은 TTS 청크.** 200 ms 미만 청크는 보코더 아티팩트가 들려 보입니다. 320 ms 청크가 적당합니다.
- **지터 버퍼 없음.** 실제 네트워크는 출렁입니다. 스무딩이 없으면 탁탁 소리가 납니다.
- **한 번 실패로 끝나는 오류 처리.** 오디오 파이프라인은 충격 방지가 필수입니다. 예외 하나가 세션을 통째로 죽입니다.

## 출시해 보기

`outputs/skill-realtime-designer.md`로 저장하세요. 단계별 구체적인 지연 시간 예산을 담은 실시간 오디오 파이프라인을 설계합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 링 버퍼 + 에너지 VAD를 시뮬레이션하고, 가짜 10초 스트림의 단계별 지연 시간을 출력합니다.
2. **보통.** `sounddevice`로 20 ms 프레임 단위로 마이크를 처리하고 프레임마다 VAD 상태를 출력하는 패스스루 루프를 만들어 보세요.
3. **어려움.** `aiortc`로 완전 이중 에코 테스트를 만들어 보세요: 브라우저 → WebRTC → Python → WebRTC → 브라우저. 1 kHz 펄스로 유리 끝에서 유리 끝까지(glass-to-glass) 지연을 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 링 버퍼 | 원형 큐 | 오디오 프레임을 담는 고정 크기, 잠금 없는(또는 SPSC 잠금) FIFO. |
| VAD | 침묵 게이트 | 음성 vs 비음성을 표시하는 모델 또는 휴리스틱. |
| 스트리밍 ASR | 실시간 STT | 오디오가 도착하는 대로 부분 텍스트를 내놓는다. 제한된 룩어헤드(lookahead). |
| 지터 버퍼 | 네트워크 스무더 | 순서가 어긋난 패킷을 재정렬하는 큐. 보통 60~80 ms. |
| AEC | 에코 제거 | 스피커→마이크 피드백 경로를 뺀다. |
| 바지 인 (Barge-in) | 사용자 끼어들기 | TTS 도중 사용자 발화를 감지하면 재생을 반드시 취소해야 한다. |
| 완전 이중 (Full duplex) | 양쪽 동시 | 사용자와 봇이 동시에 말할 수 있다. Moshi가 완전 이중이다. |

## 더 읽을거리

- [Macháček 외 (2023). Whisper-Streaming](https://arxiv.org/abs/2307.14743) — 청크 기반 준스트리밍 Whisper.
- [Kyutai (2024). Moshi](https://kyutai.org/Moshi.pdf) — 완전 이중 200 ms 지연.
- [LiveKit Agents 프레임워크 (2024)](https://docs.livekit.io/agents/) — 프로덕션 오디오 에이전트 오케스트레이션.
- [Silero VAD 저장소](https://github.com/snakers4/silero-vad) — 1 ms 미만 VAD, Apache 2.0.
- [WebRTC AEC3 논문](https://webrtc.googlesource.com/src/+/main/modules/audio_processing/aec3/) — 오픈소스 속 에코 제거.
