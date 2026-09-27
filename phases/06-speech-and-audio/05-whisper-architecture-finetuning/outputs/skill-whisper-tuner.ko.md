> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-whisper-tuner.md](skill-whisper-tuner.md)

---
name: whisper-tuner
description: 주어진 언어, 도메인, 지연 시간 예산에 맞춰 Whisper 파인튜닝 또는 추론 파이프라인을 설계한다.
version: 1.0.0
phase: 6
lesson: 05
tags: [audio, whisper, asr, fine-tuning, lora]
---

목표(언어 집합, 도메인, 클립 길이 분포, 지연 시간 예산, 하드웨어)와 데이터(확보 가능한 시간, 품질)가 주어지면 다음을 출력한다:

1. 변형 모델. Tiny / Base / Small / Medium / Large-v3 / Turbo. 이유.
2. 런타임. vanilla / faster-whisper / whisperx / whisper-streaming. 이유.
3. 파인튜닝 계획. 전체 파인튜닝(Full-FT) vs LoRA (r, target_modules), 인코더 동결 정책, 에포크 수.
4. 추론 가드레일. VAD (Silero 또는 Whisper 자체), `temperature=0`, `condition_on_previous_text=False`, `no_speech_threshold`.
5. 평가. 도메인 WER 목표, 텍스트 정규화 규칙, 침묵 클립에 대한 환각 발생률 점검.

VAD 없이 임의의 오디오에 Whisper를 배포하는 것을 거부한다. 폭주 방지 장치 없이 다중 청크 작업에 `condition_on_previous_text=True`로 설정하는 것을 거부한다. Whisper의 토크나이저나 멜 파이프라인을 교체하는 파인튜닝은 표시(플래그)한다.
