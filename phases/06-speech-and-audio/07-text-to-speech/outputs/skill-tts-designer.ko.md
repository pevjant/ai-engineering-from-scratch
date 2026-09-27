> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-tts-designer.md](skill-tts-designer.md)

---
name: tts-designer
description: 주어진 언어, 스타일, 지연 시간 목표에 맞춰 TTS 모델, 보이스, 텍스트 정규화 범위, 평가 계획을 고른다.
version: 1.0.0
phase: 6
lesson: 07
tags: [audio, tts, speech-synthesis]
---

목표(언어, 보이스 스타일, 지연 시간 예산, CPU vs GPU, 라이선스 제약)와 콘텐츠(도메인, OOV 밀도, 문장부호 풍부도)가 주어지면 다음을 출력한다:

1. 모델. Kokoro / XTTS v2 / F5-TTS / VITS / StyleTTS 2 / 상용 API. 한 문장 근거.
2. 텍스트 프런트엔드. 정규화 범위(숫자, 날짜, URL), 음소 변환기(espeak-ng vs g2p-en), OOV 폴백.
3. 보이스. 프리셋 이름 또는 참조 클립 사양(초, 노이즈 플로어, 억양 일치도).
4. 품질 목표. 목표 UTMOS, Whisper 기준 CER, 복제 시 SECS.
5. 평가 계획. 숫자, 다의어(homograph), 고유명사, 긴 문장을 모두 담은 20문장 테스트 세트.

텍스트 정규화기 없이 상용 TTS를 배포하는 것은 거부한다. 사용자 동의와 워터마킹 없이 음성 복제를 진행하는 것은 거부한다. Kokoro에게 영어가 아닌 다른 언어를 말하게 요청하는 배포는 표시(플래그)한다.
