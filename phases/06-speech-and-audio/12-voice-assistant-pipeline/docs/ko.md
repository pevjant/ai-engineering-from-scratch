> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 음성 비서 파이프라인 만들기 — 페이즈 6 캡스톤

> 레슨 01~11의 모든 것을 하나로 잇습니다. 듣고, 생각하고, 대답하는 음성 비서를 만듭니다. 2026년 이것은 연구 과제가 아니라 해결된 엔지니어링 과제입니다 — 하지만 통합 디테일이 출시 성패를 가릅니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 04, 05, 06, 07, 11; 페이즈 11 · 09 (함수 호출); 페이즈 14 · 01 (에이전트 루프)
**소요 시간:** 약 120분

## 문제 상황

엔드투엔드 비서를 만듭니다:

1. 마이크 입력을 받는다 (16 kHz 모노).
2. 사용자 발화의 시작/끝을 감지한다.
3. 스트리밍으로 전사한다.
4. 전사본을 도구를 호출할 수 있는 LLM(타이머, 날씨, 캘린더)에 넘긴다.
5. LLM 텍스트를 TTS로 스트리밍한다.
6. 오디오를 사용자에게 재생한다.
7. 사용자가 응답 도중 끼어들면 멈춘다.

지연 시간 목표: 노트북 CPU 기준, 사용자 발화가 끝난 뒤 800 ms 안에 첫 TTS 오디오 바이트. 품질 목표: 놓친 단어 없음, 침묵에서의 환각 자막 없음, 음성 복제 유출 없음, 프롬프트 인젝션 성공 없음.

## 개념

![음성 비서 파이프라인: 마이크 → VAD → STT → LLM+도구 → TTS → 스피커](../assets/voice-assistant.svg)

### 일곱 구성 요소

1. **오디오 캡처.** 마이크 → 16 kHz 모노 → 20 ms 청크. Python에서는 보통 `sounddevice`, 프로덕션에서는 네이티브 AudioUnit/ALSA/WASAPI.
2. **VAD (레슨 11).** Silero VAD, 임계값 0.5, 최소 발화 250 ms, 침묵 행오버 500 ms. "시작"과 "끝" 신호를 낸다.
3. **스트리밍 STT (레슨 4-5).** Whisper-streaming, Parakeet-TDT, 또는 Deepgram Nova-3 (API). 부분 + 최종 전사본.
4. **도구 호출이 되는 LLM.** GPT-4o / Claude 3.5 / Gemini 2.5 Flash. 도구는 JSON 스키마로 정의. 토큰을 스트리밍한다.
5. **스트리밍 TTS (레슨 7).** Kokoro-82M (오픈 최속) 또는 Cartesia Sonic (상용). LLM 토큰 20개가 모이면 TTS를 시작한다.
6. **재생.** 스피커 출력. 저대역폭 네트워크를 위해 opus 인코딩.
7. **끼어들기 처리기.** TTS 재생 중 VAD가 울리면 재생을 멈추고, LLM을 취소하고, STT를 다시 시작한다.

### 반드시 부딪히는 세 가지 실패 모드

1. **첫 단어 잘림.** VAD가 한 박자 늦게 켜져 사용자의 "저기"가 사라집니다. 시작 임계값을 0.5가 아니라 0.3으로 두세요.
2. **응답 도중 끼어들기 혼란.** 사용자가 끼어들어도 LLM이 계속 생성해서 비서가 사용자 말을 덮어씁니다. VAD → LLM 취소로 연결하세요.
3. **침묵 환각.** Whisper가 조용한 예열 프레임에서 "Thanks for watching"을 내놓습니다. 항상 VAD 게이트를 거치세요.

### 2026년 프로덕션 참조 스택

| 스택 | 지연 시간 | 라이선스 | 비고 |
|-------|---------|---------|-------|
| LiveKit + Deepgram + GPT-4o + Cartesia | 350-500 ms | 상용 API | 2026년 업계 기본값 |
| Pipecat + Whisper-streaming + GPT-4o + Kokoro | 500-800 ms | 대부분 오픈 | DIY에 적합 |
| Moshi (완전 이중) | 200-300 ms | CC-BY 4.0 | 단일 모델. 다른 아키텍처, 레슨 15 |
| Vapi / Retell (관리형) | 300-500 ms | 상용 | 가장 빨리 시작. 커스터마이징은 제한적 |
| Whisper.cpp + llama.cpp + Kokoro-ONNX | 오프라인 | 오픈 | 프라이버시 / 엣지 |

```figure
v4-voice-latency
```

## 직접 만들어 보기

### 단계 1: 청킹을 곁들인 마이크 캡처 (의사코드)

```python
import sounddevice as sd

def mic_stream(chunk_ms=20, sr=16000):
    q = queue.Queue()
    def cb(indata, frames, time, status):
        q.put(indata.copy().flatten())
    with sd.InputStream(channels=1, samplerate=sr, blocksize=int(sr * chunk_ms/1000), callback=cb):
        while True:
            yield q.get()
```

### 단계 2: VAD 게이트를 통과한 턴 캡처

```python
def capture_turn(stream, vad, pre_roll_ms=300, silence_ms=500):
    buf, pre, triggered = [], collections.deque(maxlen=pre_roll_ms // 20), False
    silent = 0
    for chunk in stream:
        pre.append(chunk)
        if vad(chunk):
            if not triggered:
                buf = list(pre)
                triggered = True
            buf.append(chunk)
            silent = 0
        elif triggered:
            silent += 20
            buf.append(chunk)
            if silent >= silence_ms:
                return b"".join(buf)
```

### 단계 3: 스트리밍 STT → LLM → TTS

```python
async def turn(audio_bytes):
    transcript = await stt.transcribe(audio_bytes)
    async for token in llm.stream(transcript):
        async for audio in tts.stream(token):
            await speaker.play(audio)
```

### 단계 4: LLM 루프 안에서 도구 호출

```python
tools = [
    {"name": "get_weather", "parameters": {"location": "string"}},
    {"name": "set_timer", "parameters": {"seconds": "int"}},
]

async for chunk in llm.stream(user_text, tools=tools):
    if chunk.type == "tool_call":
        result = dispatch(chunk.name, chunk.args)
        continue_streaming(result)
    if chunk.type == "text":
        await tts.stream(chunk.text)
```

### 단계 5: 끼어들기 처리

```python
tts_task = asyncio.create_task(tts_loop())
while True:
    chunk = await mic.get()
    if vad(chunk):
        tts_task.cancel()
        await speaker.stop()
        await new_turn()
        break
```

## 사용해 보기

`code/main.py`는 일곱 구성 요소를 스텁(stub) 모델로 잇는 실행 가능한 시뮬레이션입니다. 하드웨어가 없어도 파이프라인의 형태를 볼 수 있습니다. 실제 구현에서는 스텁을 다음으로 교체하세요:

- `silero-vad` (`pip install silero-vad`)
- `deepgram-sdk` 또는 `openai-whisper`
- `openai` (`gpt-4o`) 또는 `anthropic`
- `kokoro` 또는 `cartesia`
- 입출력은 `sounddevice`

## 함정들

- **PII를 영원히 로깅.** 턴 전체 오디오는 대부분의 관할권에서 개인정보(PII)입니다. 30일 보관, 저장 시 암호화.
- **바지 인 없음.** 사용자는 반드시 끼어듭니다. 비서는 말을 멈출 수 있어야 합니다.
- **막히는(블로킹) TTS.** 동기 TTS는 이벤트 루프를 막습니다. 비동기 또는 별도 스레드를 쓰세요.
- **도구 호출 오류 처리 없음.** 도구는 실패합니다. LLM은 오류를 돌려받고 한 번 재시도한 뒤, 우아하게 성능을 낮춰야 합니다.
- **과도한 환각 필터.** 너무 세게 걸러서 비서가 "도와드릴 수 없어요"만 반복하게 됩니다. 너무 느슨하면 뭐든 지어냅니다. 홀드아웃 세트로 보정하세요.
- **웨이크워드 옵션 없음.** 상시 청취는 프라이버시 부채입니다. 웨이크워드 게이트(Porcupine 또는 openWakeWord)를 추가하세요.

## 출시해 보기

`outputs/skill-voice-assistant-architect.md`로 저장하세요. 예산 + 규모 + 언어 + 컴플라이언스 제약이 주어지면 풀스택 사양을 만듭니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 스텁 모듈로 턴 하나를 엔드투엔드 시뮬레이션하고 단계별 지연 시간을 출력합니다.
2. **보통.** STT 스텁을 미리 녹음한 `.wav` 위의 실제 Whisper 모델로 교체하세요. WER과 엔드투엔드 지연 시간을 측정합니다.
3. **어려움.** 도구 호출을 추가하세요: `get_weather`(아무 API든)와 `set_timer`를 구현합니다. LLM이 도구를 거치게 하고, 사용자가 "5분 타이머 맞춰 줘"라고 말했을 때 올바른 함수가 불리고 음성 응답이 그것을 확인하는지 검증합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 턴 (Turn) | 사용자 + 비서의 한 왕복 | VAD로 경계가 정해진 사용자 발화 한 번 + LLM-TTS 응답 한 번. |
| 바지 인 (Barge-in) | 끼어들기 | 비서가 말하는 동안 사용자가 말하면 비서가 멈춘다. |
| 웨이크워드 | "저기 비서님" | 짧은 키워드 탐지기. Porcupine, Snowboy, openWakeWord. |
| 엔드포인팅 (End-pointing) | 턴의 끝 | 사용자가 말을 마쳤다고 판단하는 VAD + 최소 침묵 판정. |
| 프리롤 (Pre-roll) | 발화 이전 버퍼 | 첫 단어 잘림을 막으려고 VAD 발화 전 200-400 ms의 오디오를 보관한다. |
| 도구 호출 | 함수 호출 | LLM이 JSON을 내놓으면 런타임이 디스패치하고 결과가 루프 안으로 돌아온다. |

## 더 읽을거리

- [LiveKit — 음성 에이전트 퀵스타트](https://docs.livekit.io/agents/) — 프로덕션급 참조.
- [Pipecat — 음성 에이전트 예제](https://github.com/pipecat-ai/pipecat) — DIY 친화적 프레임워크.
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime) — 관리형 음성 네이티브 경로.
- [Kyutai Moshi](https://github.com/kyutai-labs/moshi) — 완전 이중 참조 (레슨 15).
- [Porcupine 웨이크워드](https://picovoice.ai/products/porcupine/) — 웨이크워드 게이팅.
- [Anthropic — 도구 사용 가이드](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) — LLM 함수 호출.
