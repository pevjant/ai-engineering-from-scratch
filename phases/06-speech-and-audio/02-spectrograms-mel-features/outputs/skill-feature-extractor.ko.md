---
name: feature-extractor
description: 하류 오디오 모델에 맞춰 특성 유형, 멜 개수, 프레임/홉, 정규화를 선택합니다.
version: 1.0.0
phase: 6
lesson: 02
tags: [audio, features, spectrogram, mel]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-feature-extractor.md](skill-feature-extractor.md)

대상 모델(ASR / TTS / 분류기 / 화자 / 음악)과 입력 오디오(샘플 레이트, 도메인)가 주어지면 다음을 출력합니다:

1. 특성 유형. 로그-멜, 멜, MFCC, 날 파형, 또는 이산 코덱(EnCodec, SoundStream). 한 문장 근거.
2. 멜 개수와 주파수 범위. `n_mels`, `fmin`, `fmax`. 도메인(음성 vs 음악)과 대상 모델에 근거를 둡니다.
3. 프레임과 홉. `frame_len`, `hop_len`, 윈도우 유형. 필요한 시간 해상도에 근거를 둡니다.
4. 정규화. 발화별 평균/분산, 전역 통계, 또는 고정 기준 dB; 특성화 이전 또는 이후.
5. 검증 스니펫. 1초짜리 레퍼런스 클립에서 결과의 shape, min/max, mean/std를 출력하고 학습 설정과 일치하는지 단언(assert)하는 Python 코드.

프레임/홉/멜 개수가 대상 모델의 공개된 학습 설정과 어긋나는 특성 파이프라인은 출시를 거부합니다. Whisper나 Parakeet에 MFCC 기반 설정을 쓰면 틀렸다고 경고합니다 — 그 모델들은 로그-멜을 받습니다. 정규화 단언이 없는 특성 추출기는 경고를 표시합니다.
