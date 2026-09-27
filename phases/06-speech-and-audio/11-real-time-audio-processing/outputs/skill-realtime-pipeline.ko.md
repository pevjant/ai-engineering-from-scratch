> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-realtime-pipeline.md](skill-realtime-pipeline.md)

---
name: realtime-voice-pipeline
description: 목표 엔드투엔드 지연 시간에 맞춰 전송, VAD, 스트리밍 STT, LLM, 스트리밍 TTS, 오케스트레이션을 고른다.
version: 1.0.0
phase: 6
lesson: 11
tags: [voice-agent, livekit, pipecat, silero, streaming, latency]
---

목표(지연 시간 P50/P95, 언어, 채널, 오프라인 vs 클라우드, 통화량)가 주어지면 다음을 출력한다:

1. 전송. WebRTC (LiveKit / Daily) · WebSocket · SIP 트렁킹 (Twilio / Telnyx). 지터 허용도 + 용도에 근거한 이유.
2. VAD + 턴 테이킹. Silero VAD (오픈, TPR 99.5%) · Cobra (상용) · LiveKit turn-detector. 임계값, 최소 발화 길이, 침묵 행오버(hang-over).
3. 스트리밍 STT. Parakeet TDT (오픈 최속) · Kyutai STT (플러시 트릭 지원) · Deepgram Nova-3 (API, 약 150 ms) · Whisper-streaming. 이유.
4. LLM + 스트리밍. TTS가 시작되기 전 첫 20개 토큰을 고정한다. 모델 + 스트리밍 설정 + 프롬프트 인젝션 가드레일.
5. 스트리밍 TTS. Kokoro-82M (TTFA 약 100 ms) · Orpheus · Cartesia Sonic · ElevenLabs Turbo. 보이스팩 또는 복제 가드 (레슨 8).
6. 오케스트레이션. LiveKit Agents · Pipecat · Vapi · Retell · 자체 Rust. 팀 역량 + 규모에 근거한 이유.
7. 관측 가능성(옵저버빌리티). 단계별 P50/P95/P99 히스토그램. 오탐 끼어들기 비율. 통화 끊김률. 통화 샘플에 대한 WER.

STT 전에 발화 전체를 버퍼링하는 배포는 거부한다. 스트리밍하지 않는 TTS는 거부한다. 평균 지연 시간으로 평가하는 것은 거부한다 — P95를 요구한다. 직접 구축 대비 비용 비교 없이 월 100k분을 넘는 트래픽에 관리형 플랫폼(Vapi / Retell)을 쓰는 것은 거부한다.

예시 입력: "자동차 보험 견적 음성 에이전트. P95 &lt; 500 ms. 영어, 미국. 주 5만 분. 컴플라이언스: HIPAA 인젝션(로그에 PII 금지)."

예시 출력:
- 전송: LiveKit Agents + Twilio SIP. 콜센터 규모에서 검증됐고 HIPAA 모드 옵트인 가능.
- VAD: Silero VAD, 임계값 0.45, 최소 발화 220 ms, 침묵 행오버 400 ms. LiveKit turn-detector 오버레이.
- STT: Deepgram Nova-3 영어 (P95 약 150 ms). 온프레미스 감사가 필요하면 Parakeet-TDT로 폴백.
- LLM: OpenAI realtime API를 통한 GPT-4o 스트리밍. 후처리 필터로 프롬프트 인젝션 방어. 첫 20개 토큰을 TTS에 고정.
- TTS: Cartesia Sonic 2 (TTFA 약 150 ms, 보이스 복제 미사용 — 사전 정의된 목소리).
- 오케스트레이션: LiveKit Agents. 프로덕션 관측은 Hamming AI.
- 로그: 저장 전 정규식 + NER 패스로 CVV / SSN / 생년월일 제거. 30일 보관.
