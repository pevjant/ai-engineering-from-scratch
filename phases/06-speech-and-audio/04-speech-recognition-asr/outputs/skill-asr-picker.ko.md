---
name: asr-picker
description: 주어진 배포 대상에 맞는 ASR 모델, 디코딩 전략, 청킹, LM 융합을 선택합니다.
version: 1.0.0
phase: 6
lesson: 04
tags: [audio, asr, speech-recognition]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-asr-picker.md](skill-asr-picker.md)

배포 대상(언어 목록, 도메인, 지연 시간 예산, 하드웨어, 오프라인 / 스트리밍, 클립 길이)이 주어지면 다음을 출력합니다:

1. 모델. Whisper-large-v3-turbo / Parakeet-TDT / Canary-Flash / wav2vec 2.0 / Moonshine. 한 문장 근거.
2. 디코딩. Greedy / 빔 폭 / 온도 폴백 / LM 융합 가중치. 품질 예산에 근거를 둡니다.
3. 청킹과 VAD. 청크 길이, 스트라이드, Silero-VAD로 게이트할지 Whisper 자체 VAD로 할지.
4. 언어 정책. 언어 강제 vs 자동 LID; 교차 언어 프레임 처리 방법.
5. 평가 계획. 도메인 테스트셋의 WER, 화자별 커버리지, 침묵 클립에서의 환각 비율.

VAD 게이트 없는 장문 Whisper 배포는 거부합니다(침묵에서 환각이 나오기 쉽습니다). 텍스트 정규화(소문자화, 구두점 제거) 없이 WER을 보고하는 것은 거부합니다. LM 없이 빔 폭 16 초과는 경고를 표시합니다; blank 위에서 날 빔을 늘려 봤자 도움이 되지 않습니다.
