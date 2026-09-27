> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 음성 에이전트: Pipecat과 LiveKit

> 음성 에이전트는 2026년에 하나의 독립된 프로덕션(운영 환경) 카테고리로 자리 잡았습니다. Pipecat은 프레임 기반 파이프라인(VAD → STT → LLM → TTS → 전송 계층)을 제공하는 Python 프레임워크입니다. LiveKit Agents는 WebRTC를 통해 AI 모델을 사용자와 연결해 줍니다. 프리미엄 스택 기준으로 프로덕션 지연 시간 목표는 엔드투엔드 450~600ms 수준입니다.

**유형:** Learn(학습)
**언어:** Python (표준 라이브러리)
**선수 지식:** 페이즈 14 · 01(에이전트 루프), 페이즈 14 · 12(워크플로 패턴)
**시간:** 약 60분

## 학습 목표

- Pipecat의 프레임 기반 파이프라인을 설명할 수 있습니다. DOWNSTREAM(원천→싱크, 순방향 흐름)과 UPSTREAM(제어, 역방향 흐름)의 구분을 포함합니다.
- 표준적인 음성 파이프라인 단계들과 Pipecat이 지원하는 전송(transport) 방식들을 말할 수 있습니다.
- LiveKit Agents의 두 음성 에이전트 클래스(MultimodalAgent, VoicePipelineAgent)와 각각이 어디에 맞는지 설명할 수 있습니다.
- 2026년 프로덕션 지연 시간 기대치와 이것이 아키텍처 선택을 어떻게 좌우하는지 요약할 수 있습니다.

## 문제 상황

음성 에이전트는 텍스트 루프에 TTS를 억지로 붙인 것이 아닙니다. 지연 시간 예산은 혹독하게 타이트하고(약 600ms), 부분 오디오(partial audio)가 기본이며, 발화 턴 감지는 별도의 모델이 담당하고, 전송 계층은 전화망 SIP부터 WebRTC까지 폭넓습니다. 프레임 기반 파이프라인을 직접 만들거나(Pipecat), 플랫폼에 기대거나(LiveKit), 둘 중 하나를 택해야 합니다.

## 핵심 개념

### Pipecat (pipecat-ai/pipecat)

- Python 프레임 기반 파이프라인 프레임워크입니다.
- `Frame` → `FrameProcessor` 체인으로 동작합니다.
- 두 가지 흐름 방향이 있습니다.
  - **DOWNSTREAM** — 원천(source) → 싱크(sink, 최종 출력) 방향(오디오 입력, TTS 출력).
  - **UPSTREAM** — 피드백과 제어 방향(취소, 메트릭, 바지인(barge-in, 사용자가 에이전트 말을 끊고 끼어드는 것)).
- `PipelineTask`는 이벤트(`on_pipeline_started`, `on_pipeline_finished`, `on_idle_timeout`)와 메트릭/트레이싱/RTVI용 옵저버를 통해 생명주기를 관리합니다.

전형적인 파이프라인은 다음과 같습니다.

```
VAD (Silero) → STT → LLM (컨텍스트가 사용자/어시스턴트를 번갈아 쌓음) → TTS → 전송 계층
```

지원 전송 방식: Daily, LiveKit, SmallWebRTCTransport, FastAPI WebSocket, WhatsApp.

Pipecat Flows는 구조화된 대화(상태 머신)를 추가하고, Pipecat Cloud는 관리형 런타임입니다.

### LiveKit Agents (livekit/agents)

- WebRTC를 통해 AI 모델을 사용자와 연결합니다.
- 핵심 개념: `Agent`, `AgentSession`, `entrypoint`, `AgentServer`.
- 두 가지 음성 에이전트 클래스가 있습니다.
  - **MultimodalAgent** — OpenAI Realtime 등을 통한 직접 오디오 처리.
  - **VoicePipelineAgent** — STT → LLM → TTS 캐스케이드(직렬 연결). 텍스트 수준의 제어를 제공합니다.
- 트랜스포머 모델 기반의 시맨틱 턴 감지(semantic turn detection)를 제공합니다.
- MCP 기능을 기본 내장하고 있습니다.
- SIP를 통해 전화망 연결을 지원합니다.
- LiveKit Inference를 통해 API 키 없이 50개 이상의 모델을, 플러그인으로 200개 이상을 더 사용할 수 있습니다.

### 상용 플랫폼

Vapi(최적화된 프리미엄 스택에서 약 450~600ms)와 Retell(180건의 테스트 통화에서 엔드투엔드 약 600ms)은 이런 기술 위에 구축되어 있습니다. WebRTC 전담 팀 없이 관리형 음성 스택을 원한다면 플랫폼을 고르세요.

### 이 패턴이 잘못되기 쉬운 지점

- **바지인 처리가 없음.** 사용자가 끼어들어도 에이전트는 계속 말합니다. Pipecat에서는 UPSTREAM 취소 프레임이, LiveKit에서는 이에 상응하는 처리가 필요합니다.
- **STT 신뢰도 무시.** 신뢰도가 낮은 전사(transcript)를 마치 정답인 양 LLM에 넘깁니다. 신뢰도로 게이팅하거나 재확인을 요청해야 합니다.
- **TTS 문장 중간 끊김.** 파이프라인이 발화 도중 취소되면 TTS가 그 사실을 알아채거나 오디오를 끊어야 합니다.
- **지연 시간 예산 무시.** 모든 구성 요소가 50~200ms씩 추가됩니다. 출시 전에 체인 전체를 합산해 보세요.

### 2026년 전형적인 지연 시간

- VAD: 20~60ms
- STT 부분 결과: 100~250ms
- LLM 첫 토큰: 150~400ms
- TTS 첫 오디오: 100~200ms
- 전송 RTT: 30~80ms

엔드투엔드 450~600ms가 프리미엄 수준입니다. 800~1200ms가 흔한 경우고, 1500ms를 넘으면 망가진 것처럼 느껴집니다.

```figure
voice-pipeline
```

## 만들어 보기

`code/main.py`는 다음을 갖춘 프레임 기반 장난감 파이프라인입니다.

- `Frame` 타입(audio, transcript, text, tts_audio, control).
- `process(frame)`를 갖는 `Processor` 인터페이스.
- 스크립트화된 프로세서로 구성한 5단계 파이프라인(VAD → STT → LLM → TTS → 전송 계층).
- 바지인을 시연하는 UPSTREAM 취소 프레임.

실행 방법:

```
python3 code/main.py
```

트레이스를 보면 정상 흐름과 함께, 발화 도중 TTS를 멈추는 바지인 취소 흐름도 확인할 수 있습니다.

## 활용하기

- **Pipecat** — 완전한 제어가 필요할 때. 커스텀 프로세서, Python 우선, 공급자 교체 가능.
- **LiveKit Agents** — WebRTC 우선 배포와 전화망 연결.
- **Vapi / Retell** — WebRTC 팀 없이 호스팅된 음성 에이전트를 쓸 때.
- **OpenAI Realtime / Gemini Live** — 오디오 입출력을 직접 처리할 때(MultimodalAgent).

## 출시하기

`outputs/skill-voice-pipeline.md`는 VAD + STT + LLM + TTS + 전송 계층과 바지인 처리를 갖춘 Pipecat 스타일 음성 파이프라인의 뼈대를 잡아 줍니다.

## 연습 문제

1. 장난감 파이프라인에 메트릭 옵저버를 추가하세요. 초당 단계별 프레임 수를 세어 보고, 지연 시간이 어디에 쌓이는지 찾아보세요.
2. 신뢰도 기반 게이팅 STT를 구현해 보세요. 임계값 미만이면 "다시 말씀해 주시겠어요?"를 요청합니다.
3. 시맨틱 턴 감지를 추가해 보세요. 간단한 규칙으로는 전사가 "?"로 끝나면 턴의 끝으로 판단하는 방식이 있습니다.
4. Pipecat의 전송 계층 문서를 읽어 보세요. 표준 라이브러리 전송을 SmallWebRTCTransport 설정(스텁)으로 바꿔 보세요.
5. 같은 질문에 대해 OpenAI Realtime과 STT+LLM+TTS 캐스케이드의 지연 시간을 측정해 비교해 보세요. 텍스트 수준 제어에는 어느 정도의 지연 시간 비용이 따르나요?

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| Frame | "이벤트" | 파이프라인에서 타입이 정해진 데이터 단위(오디오, 전사, 텍스트, 제어) |
| Processor | "파이프라인 단계" | process(frame)를 갖는 처리기 |
| DOWNSTREAM | "순방향 흐름" | 원천에서 싱크로: 오디오가 들어오고 음성이 나감 |
| UPSTREAM | "피드백 흐름" | 제어: 취소, 메트릭, 바지인 |
| VAD | "음성 활동 감지" | 사용자가 말하고 있는지 감지 |
| 시맨틱 턴 감지 | "똑똑한 발화 끝 감지" | 사용자가 말을 끝냈는지 모델이 판단 |
| MultimodalAgent | "직접 오디오 에이전트" | 오디오 입력, 오디오 출력. 중간에 텍스트가 없음 |
| VoicePipelineAgent | "캐스케이드 에이전트" | STT + LLM + TTS. 텍스트 수준의 제어 |

## 더 읽을거리

- [Pipecat 문서](https://docs.pipecat.ai/getting-started/introduction) — 프레임 기반 파이프라인, 프로세서, 전송 계층
- [LiveKit Agents 문서](https://docs.livekit.io/agents/) — WebRTC + 음성 기본 요소
- [Vapi](https://vapi.ai/) — 관리형 음성 플랫폼
- [Retell AI](https://www.retellai.com/) — 관리형 음성, 지연 시간 벤치마크 공개
