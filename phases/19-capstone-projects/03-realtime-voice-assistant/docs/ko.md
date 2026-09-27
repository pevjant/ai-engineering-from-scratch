> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 03 — 실시간 음성 비서 (ASR에서 LLM, TTS까지)

> 느낌이 좋은 음성 에이전트는 끝에서 끝까지(end-to-end) 지연 시간이 800ms 미만이고, 당신이 말을 멈췄다는 걸 알아차리고, 끼어들기(barge-in)를 처리하고, 버벅이지 않고 도구를 호출할 수 있습니다. Retell, Vapi, LiveKit Agents, Pipecat이 2026년에 모두 이 기준을 넘습니다. 방식도 같습니다: 스트리밍 ASR, 발화 전환 검출기, 스트리밍 LLM, 스트리밍 TTS를 모두 WebRTC로 잇고, 매 홉마다 빡빡한 지연 시간 예산을 걸어 두는 것. 하나를 직접 만들고 WER과 MOS, 오차단(false-cutoff) 비율을 측정하고, 패킷 손실 아래에서 돌려 보세요.

**유형:** Capstone
**언어:** Python (에이전트 + 파이프라인), TypeScript (웹 클라이언트)
**선수 지식:** 페이즈 6 (음성과 오디오), 페이즈 7 (트랜스포머), 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구), 페이즈 14 (에이전트), 페이즈 17 (인프라)
**활용하는 페이즈:** P6 · P7 · P11 · P13 · P14 · P17
**시간:** 30시간

## 문제

음성은 2025~2026년 가장 빠르게 움직인 AI UX 카테고리였습니다. 기술적 천장이 분기마다 낮아졌습니다. OpenAI Realtime API, Gemini 2.5 Live, Cartesia Sonic-2, ElevenLabs Flash v3, LiveKit Agents 1.0, Pipecat 0.0.70이 모두 800ms 미만 첫 오디오 출력(first-audio-out)을 손에 닿는 곳으로 가져왔습니다. 기준은 지연 시간만이 아닙니다. 상호작용의 느낌입니다: 사용자 말을 끊지 않기, 끊히지 않기, 문장 한가운데 끼어듦에서 복구하기, 오디오를 멈추지 않고 대화 중에 도구 호출하기, 울퉁불퉁한 모바일 네트워크에서 버티기.

REST 호출 세 개를 이어 붙여서는 그곳에 갈 수 없습니다. 아키텍처는 끝까지 파이프라인화된 스트리밍입니다. 만들어 보면 실패 모드가 보이기 시작합니다: 전화 음성에 맞춰진 VAD가 배경의 TV 소리에 반응하기, 영원히 오지 않는 문장부호를 기다리다 멈추는 발화 전환 검출기, 출력 전에 400ms를 버퍼링하는 TTS. 이 캡스톤은 이것들을 부하 아래에서 하나씩 고치고, 지연 시간·품질 보고서를 내놓는 것입니다.

## 개념

파이프라인은 다섯 개의 스트리밍 단계를 갖습니다: **오디오 입력**(브라우저나 PSTN에서 WebRTC), **ASR**(Deepgram Nova-3 또는 faster-whisper의 스트리밍 부분 전사), **발화 전환 검출**(VAD에 더해 부분 전사를 읽고 완성 신호를 판단하는 작은 발화 전환 검출 모델), **LLM**(발화가 완료됐다고 판정되는 즉시 토큰 스트리밍), **TTS**(첫 LLM 토큰에서 약 200ms 안에 오디오 스트리밍 출력).

횡단 관심사가 셋 있습니다. **끼어들기(barge-in)**: 에이전트가 말하는 동안 사용자가 말을 시작하면 TTS를 취소하고 ASR이 즉시 받아 붙습니다. **도구 사용**: 대화 중간 함수 호출(날씨, 캘린더)은 오디오를 멈추지 않도록 사이드 채널에서 돌아야 합니다. 지연이 300ms를 넘으면 에이전트는 인지 토큰("잠시만요...")을 미리 흘려 보냅니다. **배압(backpressure)**: 패킷 손실 아래에서는 부분 전사를 보류하고, VAD는 발화 게이트 문턱을 올리고, 에이전트는 확인받지 못한 메시지 위로 말하지 않습니다.

측정 기준은 정량적입니다. 15 dB SNR의 Hamming VAD 벤치마크에서 WER 8% 미만. 측정된 100통의 통화에서 첫 오디오 출력 p50 800ms 미만. 오차단 비율 3% 미만. TTS MOS 4.2 초과. g5.xlarge 한 대에서 동시 통화 50건. 이 숫자들이 산출물입니다.

## 아키텍처

```
browser / Twilio PSTN
        |
        v
   WebRTC / SIP edge
        |
        v
  LiveKit Agents 1.0  (or Pipecat 0.0.70)
        |
   +----+--------------+--------------+-----------------+
   |                   |              |                 |
   v                   v              v                 v
  ASR              VAD v5         turn-detector     side-channel
(Deepgram         (Silero)          (LiveKit)        tools
 Nova-3 /         speech-gate    completion score    (weather,
 Whisper-v3)      per 20ms        on partials        calendar)
   |                   |              |
   +--------+----------+--------------+
            v
        LLM (streaming)
     GPT-4o-realtime / Gemini 2.5 Flash /
     cascaded Claude Haiku 4.5
            |
            v
        TTS streaming
     Cartesia Sonic-2 / ElevenLabs Flash v3
            |
            v
     audio back to caller
            |
            v
   OpenTelemetry voice traces -> Langfuse
```

## 스택

- 전송: LiveKit Agents 1.0 (WebRTC) + Twilio PSTN 게이트웨이; 대안 프레임워크로 Pipecat 0.0.70
- ASR: Deepgram Nova-3 (스트리밍, 첫 부분 전사 300ms 미만) 또는 셀프 호스팅 faster-whisper Whisper-v3-turbo
- VAD: Silero VAD v5 + LiveKit 발화 전환 검출기(부분 전사를 읽는 작은 트랜스포머)
- LLM: 긴밀한 통합용 OpenAI GPT-4o-realtime, Gemini 2.5 Flash Live, 또는 캐스케이드 Claude Haiku 4.5 (스트리밍 완성, 별도 오디오 경로)
- TTS: Cartesia Sonic-2(최저 첫 바이트 지연), ElevenLabs Flash v3, 또는 셀프 호스팅용 오픈소스 Orpheus
- 도구: 날씨/캘린더/예약용 FastMCP 사이드 채널; 도구가 300ms 넘게 걸리면 에이전트가 먼저 필러를 흘려 보냄
- 관측 가능성: OpenTelemetry 음성 스팬, 오디오 재생이 가능한 Langfuse 음성 트레이스
- 배포: 셀프 호스팅 Whisper + Orpheus용 g5.xlarge 한 대(24GB VRAM); 최저 지연 시간은 호스티드 API

```figure
ce-voice-latency
```

## 만들기

1. **WebRTC 세션.** LiveKit 룸과 마이크 오디오를 스트리밍하는 웹 클라이언트를 세웁니다. 서버에서는 룸에 참여하는 에이전트 워커를 붙입니다.

2. **ASR 스트리밍.** 20ms PCM 프레임을 Deepgram Nova-3(또는 GPU의 faster-whisper)에 먹입니다. 부분 전사와 최종 전사를 구독합니다. 부분 전사별 지연 시간을 기록합니다.

3. **VAD와 발화 전환 검출기.** 프레임 스트림에 Silero VAD v5를 돌립니다. 발화 종료 이벤트가 오면 최신 부분 전사로 LiveKit 발화 전환 검출기를 발사합니다. VAD가 500ms 침묵을 말해주고 발화 전환 검출기의 완성 점수가 0.6 초과일 때만 "발화 완료"로 확정합니다.

4. **LLM 스트림.** 발화 완료 시점에 진행 중 대화와 최종 전사를 넣어 LLM 호출을 시작합니다. 토큰을 스트리밍합니다. 첫 토큰에서 TTS로 넘깁니다.

5. **TTS 스트림.** Cartesia Sonic-2가 오디오 청크를 돌려줍니다. 첫 청크는 첫 LLM 토큰에서 200ms 안에 서버를 떠나야 합니다. 청크를 LiveKit 룸으로 내보냅니다. 클라이언트는 WebRTC 지터 버퍼를 거쳐 재생합니다.

6. **끼어들기.** TTS가 재생 중일 때 VAD가 새 사용자 발화를 감지하면 TTS 스트림을 즉시 취소하고, 남은 LLM 출력을 버리고, ASR을 다시 무장합니다. `tts_canceled` 스팬을 발행합니다.

7. **도구 사이드 채널.** 날씨와 캘린더를 함수 호출 도구로 등록합니다. 호출되면 동시에 발사합니다. 300ms 안에 끝나지 않으면 LLM이 "잠시만요, 확인해 볼게요"라는 필러를 흘려 보내게 하고, 도구가 돌아오면 이어서 진행합니다.

8. **평가 하니스.** 통화 100건을 녹음합니다. WER(홀드아웃 전사 대비), 오차단 비율(사용자가 문장 중간일 때 TTS가 취소된 경우), 첫 오디오 출력 p50, TTS MOS(사람 또는 NISQA), 지터-손실 테스트(패킷 3% 드롭)를 계산합니다.

9. **부하 테스트.** 합성 발신자로 g5.xlarge 한 대에서 동시 통화 50건을 몹니다. 지속 가능한 첫 오디오 출력 p95를 측정합니다.

## 사용해 보기

```
caller: "what is the weather in tokyo tomorrow"
[asr  ] partial @280ms: "what is the"
[asr  ] partial @540ms: "what is the weather"
[turn ] completion score 0.82 at @820ms; commit
[llm  ] first token @960ms
[tool ] weather.tokyo tomorrow -> 68/52 partly cloudy @1140ms
[tts  ] first audio-out @1040ms: "Tokyo tomorrow will be partly cloudy..."
turn latency: 1040ms user-stop -> audio-out
```

## 출시하기

`outputs/skill-voice-agent.md`가 산출물입니다. 도메인(고객 지원, 일정 관리, 키오스크)이 주어지면 측정 기준에 맞춰 튜닝한 ASR/VAD/LLM/TTS 파이프라인으로 LiveKit 에이전트를 세웁니다. 채점 기준:

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 끝까지 지연 시간 | 녹음된 100통에서 첫 오디오 출력 p50 800ms 미만 |
| 20 | 발화 전환 품질 | Hamming VAD 벤치마크에서 오차단 비율 3% 미만 |
| 20 | 도구 사용 정확성 | 오디오를 멈추지 않고 올바른 데이터를 돌려주는 대화 중 도구 호출 |
| 20 | 패킷 손실 하 신뢰성 | 패킷 3% 드롭 주입 시 WER과 발화 전환 안정성 |
| 15 | 평가 하니스 완전성 | 공개 설정으로 재현 가능한 측정 |
| **100** | | |

## 연습 문제

1. Deepgram Nova-3를 g5.xlarge의 faster-whisper v3 turbo로 바꿔 보세요. 지연 시간과 WER 격차를 측정하고, CPU 대비 GPU 선택이 어디서 중요한지 찾아보세요.

2. 끼어듦 중재 정책을 추가하세요: 도구 호출 중에 사용자가 끼어들면 에이전트는 무엇을 할까요? 세 정책(하드 취소, 도구 끝나고 정지, 다음 발화 큐잉)을 비교하세요.

3. 적대적 발화 전환 검출 테스트를 돌려 보세요: 사용자가 문장 중간에 긴 휴지를 갖게 합니다. 900ms를 넘기지 않으면서 오차단을 최소로 만드는 VAD 침묵 문턱과 발화 전환 검출기 점수 문턱을 튜닝하세요.

4. 같은 에이전트를 Twilio PSTN으로 배포해 보세요. PSTN 첫 오디오 출력과 WebRTC를 비교하고, 지터 버퍼와 코덱 차이를 설명하세요.

5. 비영어권 언어(일본어, 스페인어)용 음성 활동 검출을 추가하세요. Silero VAD v5의 오반응(false-trigger) 비율을 언어별 파인튜닝 버전과 비교해 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| 발화 전환 검출 | "발화 끝" | VAD 침묵과 부분 전사를 보고 사용자가 말을 끝냈는지 판단하는 분류기 |
| 끼어들기(barge-in) | "인터럽트 처리" | VAD가 새 사용자 발화를 감지하면 재생 중 TTS를 취소하는 것 |
| 첫 오디오 출력 | "지연 시간" | 사용자가 말을 멈춘 시점부터 첫 오디오 패킷이 서버를 떠날 때까지의 시간 |
| VAD | "발화 게이트" | 오디오 프레임을 발화 vs 침묵으로 분류하는 모델. Silero VAD v5가 2026년 기본값 |
| 지터 버퍼 | "오디오 스무딩" | 네트워크 편차를 흡수하려고 패킷을 잠깐 쥐고 있는 클라이언트 쪽 버퍼 |
| 필러 | "인지 토큰" | 도구가 느릴 때 침묵을 피하려고 에이전트가 흘려 보내는 짧은 문구 |
| MOS | "평균 의견 점수" | 지각적 음성 품질 등급. NISQA가 자동화 대체 지표 |

## 더 읽을거리

- [LiveKit Agents 1.0](https://github.com/livekit/agents) — 참고용 WebRTC 에이전트 프레임워크
- [Pipecat](https://github.com/pipecat-ai/pipecat) — 대안 Python 우선 스트리밍 에이전트 프레임워크
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime) — 통합 음성 모델 레퍼런스
- [Deepgram Nova-3 문서](https://developers.deepgram.com/docs) — 스트리밍 ASR 레퍼런스
- [Silero VAD v5](https://github.com/snakers4/silero-vad) — VAD 참고 모델
- [Cartesia Sonic-2](https://docs.cartesia.ai) — 저지연 TTS 레퍼런스
- [Retell AI 아키텍처](https://docs.retellai.com) — 프로덕션 음성 에이전트 아키텍처
- [Vapi.ai 프로덕션 스택](https://docs.vapi.ai) — 대안 프로덕션 레퍼런스
