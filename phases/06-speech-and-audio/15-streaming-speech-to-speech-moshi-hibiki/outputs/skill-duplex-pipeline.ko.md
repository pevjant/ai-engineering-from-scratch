> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-duplex-pipeline.md](skill-duplex-pipeline.md)

---
name: duplex-pipeline
description: 음성 에이전트 워크로드에 대해 완전 이중(Moshi) vs 파이프라인(VAD + STT + LLM + TTS) 아키텍처를 고른다.
version: 1.0.0
phase: 6
lesson: 15
tags: [moshi, hibiki, full-duplex, voice-agent, streaming]
---

워크로드(지연 시간 목표, 도구 호출 필요성, 언어 커버리지, 하드웨어 예산, 클라우드 vs 엣지)가 주어지면 다음을 출력한다:

1. 아키텍처. 완전 이중 (Moshi / GPT-4o Realtime / Gemini Live) vs 파이프라인 (LiveKit + STT + LLM + TTS, 레슨 12). 한 문장 근거.
2. 모델. Moshi · Hibiki · Hibiki-Zero · Sesame CSM · GPT-4o Realtime · Gemini 2.5 Live · 전통 파이프라인. 이유.
3. 규모. 세션당 GPU 비용 (Moshi는 슬롯을 점유), 최대 동시 세션, 콜드 스타트 영향.
4. 도구 호출 경로. 필요하다면 — 하이브리드 파이프라인 (이중화 + 도구 호출용 외부 LLM) 또는 순수 파이프라인. 트레이드오프를 설명한다.
5. 언어 커버리지. 완전 이중 모델은 언어 지원이 좁다. 파이프라인은 LLM의 다국어 능력을 물려받는다.

도구 호출 / 검색이 필요한 기업용 에이전트에 완전 이중 전용 아키텍처는 거부한다 — Moshi는 대화 모델이지 에이전트 프레임워크가 아니다. 250 ms 미만 대화형 에이전트에 파이프라인 전용은 거부한다 — 단계들이 누적된다. GPU 하나에서 동시 세션 4개를 넘기는 Moshi 배포는 거부한다 — 경합(contention)에 걸린다.

예시 입력: "언어 학습용 음성 컴패니언 — 회화 유창성 연습. 영어 + 프랑스어. 반응성 &lt; 250 ms. 일일 활성 사용자 1만 명."

예시 출력:
- 아키텍처: 완전 이중 (Moshi). 250 ms 미만 지연 요건 + 회화 유창성이 Moshi의 강점과 맞물린다.
- 모델: Moshi. EN + FR 모두 잘 지원. CC-BY 4.0 라이선스.
- 규모: L4 GPU 하나당 동시 세션 4~6개 → 동시 접속 10% 가정의 DAU 1만 명이면 피크 시 GPU 약 1,500장. 조용한 경로는 Kyutai Pocket TTS + 로컬 Whisper를 쓰는 온디바이스 라이트 모드로 계획.
- 도구 호출: 최소한 — "문법 힌트 보여 줘"와 "이 문구 번역해 줘"는 작은 LLM 사이드카로 라우팅 가능. 대부분의 상호작용은 Moshi가 빛나는 열린 대화다.
- 언어 커버리지: EN + FR (네이티브). ES / DE / JP는 Hibiki-Zero 어댑테이션으로 (새 언어마다 오디오 1,000시간 필요).
