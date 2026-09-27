> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-voice-assistant-architect.md](skill-voice-assistant-architect.md)

---
name: voice-assistant-architect
description: 주어진 워크로드에 대해 구성 요소, 지연 시간 예산, 관측 가능성(옵저버빌리티), 컴플라이언스를 담은 음성 비서 풀스택 사양을 만든다.
version: 1.0.0
phase: 6
lesson: 12
tags: [voice-assistant, architecture, livekit, pipecat, compliance]
---

용도(소비자 / 고객 지원 / 접근성 / 엣지), 예상 규모(동시 세션, 월간 분(分)량), 언어, 지연 시간 목표, 컴플라이언스(HIPAA, PCI, EU AI Act, CA SB 942)가 주어지면 다음을 출력한다:

1. 구성 요소 (7개 계층). 마이크 + 청킹 · VAD · 스트리밍 STT · LLM + 도구 · 스트리밍 TTS · 재생 · 끼어들기 처리기. 각각에 정확한 공급자/모델 이름을 쓴다.
2. 지연 시간 예산. 단계별 P50 / P95 / P99 목표가 엔드투엔드 목표에 합산되도록 잡는다. 어떤 단계가 병렬이고 어떤 단계가 직렬인지 표시한다.
3. 도구 호출 스키마. 도구마다 JSON 사양 + 오류 처리 + 폴백 문구. 두 번 실패하면 LLM이 반드시 거쳐야 하는 "도와드릴 수 없다" 경로를 항상 포함한다.
4. 안전. 프롬프트 인젝션 방어, 음성 복제 잠금 (TTS가 복제를 지원할 경우), 웨이크워드 게이트 (상시 켜짐이라면), 로그의 PII 마스킹, 30일 보관.
5. 관측 가능성(옵저버빌리티). 단계별 P50/P95/P99 · 오탐 끼어들기 비율 · 도구 호출 성공률 · 통화 100건당 WER · 분당 비용 · 이탈률.
6. 컴플라이언스. 고지 음성 ("이것은 AI 비서입니다"), 지역 고정 (EU 데이터는 EU에서), 감사 로그 보관, 옵트아웃 경로.

웨이크워드 없는 상시 켜짐 배포는 거부한다. 스트리밍하지 않는 TTS (발화 길이만큼 지연이 늘어남)는 거부한다. P95 없이 평균 지연 시간만 보고하는 것은 거부한다 — 사용자가 떠나는 지점은 꼬리(tail)다. 법무 검토 없이 30일을 넘게 날 오디오를 보관하는 것은 거부한다.

예시 입력: "저시력 사용자용 접근성 비서: 소비자 이메일 앱의 음성 전용 인터페이스. 영어. P95 &lt; 600 ms. 동시 사용자 약 1만 명."

예시 출력:
- 구성 요소: sounddevice (LiveKit Agents를 통한 WebRTC) · Silero VAD · Deepgram Nova-3 (영어) · 이메일 도구를 갖춘 GPT-4o (read_message, compose_reply, mark_read) · Cartesia Sonic 2 스트리밍 · WebRTC 출력 · VAD 발화 시 interrupt=LLM과 TTS 취소.
- 예산: 캡처 120 ms + VAD 40 + STT 150 + LLM TTFT 100 + TTS TTFA 150 = P95 560 ms.
- 도구: read_message({id}), compose_reply({message_id, body}), mark_read({id}), search({query}). 모두 JSON 반환. 도구당 최대 2회 재시도 후 폴백 "그건 처리하지 못했어요 — 다르게 말씀해 보시겠어요?".
- 안전: 프롬프트 인젝션 방어 (`ignore previous instructions` 탐지). 웨이크워드 "Hey Mail". 음성 복제 없음 (Cartesia 고정 목소리). 로그에서 이메일 본문 마스킹.
- 관측 가능성: Hamming AI 프로덕션 모니터링. 단계별 Prometheus 히스토그램. 오탐 끼어들기 &gt; 5% 또는 p95 &gt; 800 ms에서 알림.
- 컴플라이언스: 첫 사용 시 AI 고지. 의료 메시지에만 HIPAA 옵트인. EU 사용자는 EU 호스팅 Cartesia + GPT-4o Ireland로 연결.
