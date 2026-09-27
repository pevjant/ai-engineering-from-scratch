---
name: audio-loader
description: 날 오디오 파일을 대상 모델의 기대와 대조해 검증하고 안전하게 리샘플링합니다.
version: 1.0.0
phase: 6
lesson: 01
tags: [audio, speech, preprocessing]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-audio-loader.md](skill-audio-loader.md)

오디오 파일(경로, 채널, 샘플 레이트, 비트 심도, 코덱)과 대상 모델(필요한 샘플 레이트와 채널 수가 정해진 ASR / TTS / 분류기)이 주어지면 다음을 출력합니다:

1. 불일치 항목. 파일이 대상과 맞지 않는 모든 차원을 나열(sr, 채널, 최소 길이, 클리핑 검사).
2. 리샘플 계획. 원본 sr, 대상 sr, 리샘플링 라이브러리(`torchaudio.transforms.Resample` 또는 `librosa.resample`), 안티에일리어싱 필터 유형.
3. 채널 계획. 모노 폴딩 전략(평균 vs 왼쪽만), 또는 모델이 지원하면 다중 채널 그대로 통과.
4. 정규화. 피크 vs RMS 정규화, dBFS 목표, 클리핑 가드.
5. 검증 스니펫. 파일을 불러오고 변환을 실행한 뒤 최종 배열이 `(target_sr, dtype, channel_count, range)`와 일치하는지 단언(assert)하는 Python 코드.

안티에일리어싱 필터 없이 다운샘플링하는 것은 거부합니다. 재구성 필터 없이 2배를 넘는 업샘플링은 거부합니다. 클리핑 피크가 ±0.999를 넘거나 DC 오프셋이 ±0.01을 넘는 입력 파일은 경고를 표시합니다.
