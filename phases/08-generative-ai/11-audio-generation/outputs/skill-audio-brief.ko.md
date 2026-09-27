---
name: audio-brief
description: 오디오 브리프를 TTS, 음악, SFX에 맞는 모델 + 프롬프트 + 평가 계획으로 바꿉니다.
version: 1.0.0
phase: 8
lesson: 11
tags: [audio, tts, music, sfx, codec]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-audio-brief.md](skill-audio-brief.md)

오디오 브리프(과제: TTS / 음악 / SFX / 목소리 복제, 길이, 스타일, 목소리 또는 장르, 라이선스 제약, 실시간 또는 오프라인, 품질 기준)가 주어지면 다음을 출력합니다:

1. 모델 + 호스팅. ElevenLabs V3, OpenAI TTS, XTTS v2, Suno v4, Udio, Stable Audio 2.5, MusicGen 3.3B, AudioCraft 2, 또는 GPT-4o realtime. 한 줄 이유를 붙입니다.
2. 프롬프트 형식. TTS: 텍스트 + 보이스 프롬프트(3-10초 샘플 또는 음성 ID) + 감정 / 속도 태그. 음악: 장르 + 편성 + 무드 + BPM + 구조 표식. SFX: 의성어 + 소리의 근원 + 길이 힌트.
3. 코덱 + 생성기 + 보코더 체인. 구체적인 코덱(Encodec 32 kHz, DAC 44 kHz, 커스텀)과 생성기 선택(토큰-AR vs 플로우 매칭)을 명시합니다.
4. 시드 + 재현성. 시드 고정, 버전 고정, 프롬프트 해시.
5. 평가. TTS는 MOS(평균 의견 점수) 또는 A/B, 음악은 CLAP score, TTS 전사는 CER, SFX는 사용자 청취 테스트.
6. 가드레일. 목소리 복제 동의 + 워터마크(PerTh / SynthID-audio), 음악 산출물의 저작권 검사, 학습 데이터 정책 확인.

소유자의 검증된 동의 없이는 어떤 목소리도 복제하지 않습니다(카세트 시대의 "3초 프롬프트"는 동의가 아닙니다). 라이선스 없는 참조 소재가 들어간 음악은 출시하지 않습니다. 스트리밍 토큰-AR 모델을 쓰지 않으면서 200 ms 미만의 실시간 목표를 잡은 요청은 표시합니다 - 확산 기반 오디오는 2026년 기준 300 ms 미만 TTFB를 맞출 수 없습니다.
