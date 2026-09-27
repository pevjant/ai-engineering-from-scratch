---
name: voice-pipeline
description: 음성 제품 명세(언어, 전송 방식, 공급자)를 받아 바지인(barge-in) 처리, 신뢰도 게이팅, 지연 시간 예산 강제를 갖춘 Pipecat 스타일 음성 파이프라인(VAD + STT + LLM + TTS + 전송 계층)의 뼈대를 만듭니다.
version: 1.0.0
phase: 14
lesson: 22
tags: [voice, pipecat, livekit, webrtc, latency]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-voice-pipeline.md](skill-voice-pipeline.md)

음성 제품 명세(언어, 전송 방식, 공급자)가 주어지면 프레임 기반 파이프라인의 뼈대를 만듭니다.

산출물:

1. `kind`, `payload`, `direction`(downstream / upstream)을 갖는 `Frame` 타입.
2. 프로세서: `VAD`, `STT`, `LLM`, `TTS`, `Transport`. 각각 `process(frame)`을 갖습니다.
3. 프로세서를 순방향과 역방향으로 연결해 주는 `link()` 헬퍼.
4. 취소 프레임 처리: 전송 계층 → TTS → LLM → STT로 이어지는 UPSTREAM 경로를 따라 각 단계에서 대기 중인 작업을 폐기합니다.
5. 옵저버: 단계별 지연 시간 메트릭. 프로세서를 통과하는 프레임마다 OTel 스팬을 하나씩 발행합니다(레슨 23).
6. STT 신뢰도 게이트: 임계값 미만이면 전사 대신 "다시 말씀해 주세요" 텍스트 프레임을 발행합니다.

하드 리젝(무조건 거절):

- UPSTREAM 처리가 없는 파이프라인. 음성에서 바지인은 선택 사항이 아닙니다.
- 스트리밍 없는 LLM 호출. 첫 토큰 지연이 지배적이므로 반드시 스트리밍해야 합니다.
- 신뢰도를 무시하는 STT. 잘못된 전사를 LLM에 넘기면 잘못된 답변이 나옵니다.

거절 규칙:

- 콜드 런 기준 엔드투엔드 지연 시간이 1500ms를 넘으면 출시를 거절합니다. 체인을 최적화하거나 MultimodalAgent(LiveKit 직접 오디오)를 사용하세요.
- 전화망 우선 제품인데 파이프라인에 SIP 어댑터가 없으면 거절합니다. LiveKit SIP나 플랫폼(Vapi/Retell)으로 우회하세요.
- 전송 중 암호화 없이 PII 오디오를 다루는 제품이면 거절합니다.

출력: 지연 시간 예산, 바지인 설계, 전송 방식 선택을 설명하는 `frames.py`, `processors.py`, `pipeline.py`, `observers.py`, `README.md`. 마지막에는 "다음에 읽을 것"으로 레슨 23(OTel), 레슨 24(관측 가능성 백엔드), 또는 WebRTC 세부 사항은 LiveKit 문서를 가리킵니다.
