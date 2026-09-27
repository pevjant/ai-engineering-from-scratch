> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 스트리밍 음성 대 음성 — Moshi, Hibiki, 그리고 완전 이중 대화

> 2024-2026년은 음성 AI의 정의를 다시 썼습니다. Moshi는 듣는 것과 말하는 것을 동시에 하는 단일 모델을 200 ms 지연으로 선보였습니다. Hibiki는 음성 대 음성 번역을 청크 단위로 해냅니다. 둘 다 ASR → LLM → TTS 파이프라인을 버리고 Mimi 코덱 토큰 위의 통합된 완전 이중 아키텍처로 갔습니다. 이것이 새로운 참조 설계입니다.

**유형:** Learn
**언어:** Python
**선수 지식:** 페이즈 6 · 13 (뉴럴 오디오 코덱), 페이즈 6 · 11 (실시간 오디오), 페이즈 7 · 05 (전체 트랜스포머)
**소요 시간:** 약 75분

## 문제 상황

레슨 11 + 12로 만든 모든 음성 에이전트에는 약 300~500 ms의 근본적인 지연 하한이 있습니다. VAD가 울리고, STT가 처리하고, LLM이 생각하고, TTS가 생성하죠. 각 단계마다 자기만의 최소 지연이 있습니다. 튜닝하고 병렬화할 수 있지만, 파이프라인의 모양 자체가 상한을 만듭니다.

Moshi(Kyutai, 2024-2026)는 다른 질문을 던집니다: 파이프라인이 아예 없다면 어떨까? 모델 하나가 오디오를 받아 오디오를 내놓는 것, 그것도 끊임없이, 필수 단계가 아니라 '내면의 독백'이라는 중간 산물로서의 텍스트를 곁들인다면?

답이 바로 **완전 이중(full-duplex) 음성 대 음성**입니다. 이론 지연 160 ms (Mimi 프레임 80 ms + 음향 지연 80 ms). 실측 지연은 L4 GPU 하나에서 200 ms. 최고 수준의 직렬 파이프라인 음성 에이전트가 내는 것의 절반입니다.

## 개념

![Moshi 아키텍처: 두 개의 병렬 Mimi 스트림 + 내면의 독백 텍스트](../assets/moshi-hibiki.svg)

### Moshi 아키텍처

**입력.** Mimi 코덱 스트림 두 개, 둘 다 12.5 Hz × 8 코드북:

- 스트림 1: 사용자 오디오 (Mimi 인코딩, 계속 도착함)
- 스트림 2: Moshi 자기 오디오 (Moshi가 생성함)

**트랜스포머.** 7B 파라미터의 Temporal Transformer가 두 스트림과 텍스트 '내면의 독백' 스트림을 함께 처리합니다. 80 ms마다:

1. 가장 최근의 사용자 Mimi 토큰을 소비한다 (8개 코드북).
2. 방금 나온 Moshi Mimi 토큰을 소비한다 (8개 코드북).
3. 다음 Moshi 텍스트 토큰을 생성한다 (내면의 독백).
4. 다음 Moshi Mimi 토큰을 생성한다 (작은 Depth Transformer를 통해 8개 코드북).

세 스트림 — 사용자 오디오, Moshi 오디오, Moshi 텍스트 — 이 병렬로 흐릅니다. Moshi는 말하면서 사용자를 들을 수 있고, 사용자가 끼어들면 스스로 말을 멈출 수 있고, 주 발화를 깨지 않고서도 끼어들기 반응("음-")을 할 수 있습니다.

**depth transformer.** 한 프레임 안에서 8개 코드북은 병렬로 예측되지 않습니다 — 코드북 사이에 의존성이 있거든요. 작은 2층짜리 "depth transformer"가 그것들을 80 ms 안에서 순서대로 예측합니다. AR 코덱 LM의 표준 분해입니다 (VALL-E, VibeVoice도 이렇게 합니다).

### 내면의 독백 텍스트가 도움이 되는 이유

명시적인 텍스트가 없으면 모델이 음향 스트림 안에서 언어를 암묵적으로 모델링해야 합니다. Moshi의 통찰: 오디오와 함께 텍스트 토큰을 내놓도록 강제하자. 텍스트 스트림은 사실상 Moshi가 말하는 내용의 전사본입니다. 이것이 의미적 일관성을 높이고, 언어 모델 헤드를 갈아 끼우기 쉽게 하고, 전사본을 덤으로 얻게 해 줍니다.

### Hibiki: 스트리밍 음성 대 음성 번역

같은 아키텍처를 번역 쌍으로 학습한 것입니다. 원본 오디오가 들어가면 목표 언어 오디오가 계속 나옵니다. Hibiki-Zero (2026년 2월)는 단어 수준으로 정렬된 학습 데이터의 필요를 없앴습니다 — 문장 수준 데이터 + 지연 최적화를 위한 GRPO 강화 학습을 사용합니다.

처음에 네 개의 언어 쌍을 지원하고, 약 1,000시간 데이터로 새 언어에 맞출 수 있습니다.

### 더 넓은 Kyutai 스택 (2026)

- **Moshi** — 완전 이중 대화 (프랑스어 우선, 영어도 잘 지원)
- **Hibiki / Hibiki-Zero** — 동시 음성 번역
- **Kyutai STT** — 스트리밍 ASR (500 ms 또는 2.5 s 룩어헤드)
- **Kyutai Pocket TTS** — CPU에서 도는 100M 파라미터 TTS (2026년 1월)
- **Unmute** — 이것들을 공개 서버에서 조합한 풀 파이프라인

L40S GPU의 처리량: 3배속 실시간으로 동시 세션 64개.

### Sesame CSM — 사촌 격

Sesame CSM (2025)은 비슷한 아이디어를 씁니다 — Llama-3 백본에 Mimi 코덱 헤드를 얹은 것이죠. 하지만 CSM은 완전 이중이 아니라 단방향입니다(컨텍스트 + 텍스트를 받아 음성을 만듦). 시장에서 최고의 '목소리 존재감(voice presence)' TTS이지만, Moshi의 완전 이중 능력과는 정확히 같지는 않습니다.

### 2026년 성능 수치

| 모델 | 지연 시간 | 용도 | 라이선스 |
|-------|---------|----------|---------|
| Moshi | 200 ms (L4) | 완전 이중 영어 / 프랑스어 대화 | CC-BY 4.0 |
| Hibiki | 12.5 Hz 프레임레이트 | 프랑스어 ↔ 영어 스트리밍 번역 | CC-BY 4.0 |
| Hibiki-Zero | 동일 | 5개 언어 쌍, 정렬 데이터 불필요 | CC-BY 4.0 |
| Sesame CSM-1B | 200 ms TTFA | 컨텍스트 조건부 TTS | Apache-2.0 |
| GPT-4o Realtime | ~300 ms | 비공개, OpenAI API | 상용 |
| Gemini 2.5 Live | ~350 ms | 비공개, Google API | 상용 |

```figure
sp-fullduplex
```

## 직접 만들어 보기

### 단계 1: 인터페이스

Moshi는 80 ms짜리 Mimi 인코딩 오디오 청크를 받아서 80 ms짜리 Mimi 인코딩 오디오 청크를 돌려주는 WebSocket 서버를 제공합니다. 양방향으로. 끊임없이.

```python
import asyncio
import websockets
from moshi.client_utils import encode_audio_mimi, decode_audio_mimi

async def moshi_chat():
    async with websockets.connect("ws://localhost:8998/api/chat") as ws:
        mic_task = asyncio.create_task(stream_mic_to(ws))
        spk_task = asyncio.create_task(stream_from_to_speaker(ws))
        await asyncio.gather(mic_task, spk_task)
```

### 단계 2: 완전 이중 루프

```python
async def stream_mic_to(ws):
    async for chunk_80ms in mic_stream_at_12_5_hz():
        mimi_tokens = encode_audio_mimi(chunk_80ms)
        await ws.send(serialize(mimi_tokens))

async def stream_from_to_speaker(ws):
    async for msg in ws:
        mimi_tokens, text_token = deserialize(msg)
        audio = decode_audio_mimi(mimi_tokens)
        await play(audio)
```

양방향이 동시에 돕니다. Python asyncio 또는 Rust futures가 표준 전송 계층입니다.

### 단계 3: 학습 목적 함수 (개념)

모든 80 ms 프레임 `t`에 대해:

- 입력: `user_mimi[0..t]`, `moshi_mimi[0..t-1]`, `moshi_text[0..t-1]`
- 예측: `moshi_text[t]`, 이어서 `moshi_mimi[t, codebook_0..7]`

텍스트가 오디오보다 먼저 예측되고(내면의 독백), 오디오는 depth transformer 안에서 코드북 순서대로 예측됩니다.

### 단계 4: Moshi가 이기는 곳과 지는 곳

Moshi가 이기는 곳:

- 값싼 하드웨어에서 엔드투엔드 250 ms 미만.
- 자연스러운 끼어들기 반응과 끼어들기.
- 파이프라인 접착 코드가 없음.

Moshi가 지는 곳:

- 도구 호출 (학습되지 않음; 별도 LLM 경로가 필요).
- 긴 추론 (Moshi는 8B 정도의 대화 모델이지 Claude/GPT-4가 아님).
- 틈새 주제에 대한 사실 정확도.
- 대부분의 기업 프로덕션 용도 (2026년에도 여전히 파이프라인을 씁니다).

## 사용해 보기

| 상황 | 선택 |
|-----------|------|
| 지연이 가장 짧은 음성 컴패니언 | Moshi |
| 실시간 통역 통화 | Hibiki |
| 음성 데모 / 연구 | Moshi, CSM |
| 도구를 쓰는 기업용 에이전트 | Moshi가 아니라 파이프라인 (레슨 12) |
| 문맥 속 맞춤 목소리 TTS | Sesame CSM |
| 모든 언어의 음성 대 음성 | GPT-4o Realtime 또는 Gemini 2.5 Live (상용) |

## 함정들

- **제한된 도구 호출.** Moshi는 대화 모델이지 에이전트 프레임워크가 아닙니다. 도구가 필요하면 파이프라인과 조합하세요.
- **특정 목소리 조건부 생성.** Moshi는 학습된 단일 페르소나를 씁니다. 복제는 별도의 학습 런입니다.
- **언어 커버리지.** 프랑스어 + 영어는 훌륭하지만, 다른 언어는 제한적입니다. Hibiki-Zero가 도움되지만 그래도 학습 데이터는 필요합니다.
- **자원 비용.** Moshi 세션 하나가 GPU 슬롯 하나를 점유합니다. 값싸게 여러 테넌트가 나눠 쓰는 배포 패턴이 아닙니다.

## 출시해 보기

`outputs/skill-duplex-pipeline.md`로 저장하세요. 음성 에이전트 워크로드에 대해 파이프라인 vs 완전 이중 아키텍처를 근거와 함께 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 두 스트림 + 내면의 독백 아키텍처를 기호적으로 시뮬레이션합니다.
2. **보통.** HuggingFace에서 Moshi를 받아 서버를 돌리고 대화 한 번을 시험합니다. 사용자 발화 종료부터 Moshi 응답 시작까지의 실측 지연을 측정합니다.
3. **어려움.** 레슨 12에서 만든 파이프라인 에이전트를 가져와 20개의 동일한 테스트 발화에서 P50 지연을 Moshi와 비교합니다. 어느 쪽이 구조적으로 이기는지 정리해서 씁니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 완전 이중 (Full-duplex) | 듣고 말하기 동시에 | 같은 모델 위에서 두 오디오 스트림이 동시에 활성 상태. |
| 내면의 독백 (Inner monologue) | 모델의 텍스트 스트림 | Moshi가 오디오 출력과 함께 텍스트 토큰을 내놓는다. |
| Depth transformer | 코드북 간 예측기 | 80 ms 프레임 하나 안에서 8개 코드북을 예측하는 작은 트랜스포머. |
| Mimi | Kyutai의 코덱 | 12.5 Hz × 8 코드북. 의미+음향. Moshi의 동력. |
| 스트리밍 S2S | 실시간 오디오 → 오디오 | 청크 단위 번역/대화. 파이프라인 단계 없음. |
| 끼어들기 반응 (Back-channeling) | "음-" 반응 | Moshi는 자기 턴을 깨지 않고 작은 확인 반응을 낼 수 있다. |

## 더 읽을거리

- [Défossez 외 (2024). Moshi — 음성-텍스트 파운데이션 모델](https://arxiv.org/html/2410.00037v2) — 원 논문.
- [Kyutai Labs (2026). Hibiki-Zero](https://arxiv.org/abs/2602.12345) — 정렬 데이터 없는 스트리밍 번역.
- [Sesame (2025). Crossing the uncanny valley of voice](https://www.sesame.com/research/crossing_the_uncanny_valley_of_voice) — CSM 사양.
- [Kyutai — Moshi 저장소](https://github.com/kyutai-labs/moshi) — 설치 + 서버.
- [OpenAI — Realtime API](https://platform.openai.com/docs/guides/realtime) — 비공개 상용 경쟁자.
- [Kyutai — Delayed Streams Modeling](https://github.com/kyutai-labs/delayed-streams-modeling) — 밑바닥의 STT/TTS 프레임워크.
