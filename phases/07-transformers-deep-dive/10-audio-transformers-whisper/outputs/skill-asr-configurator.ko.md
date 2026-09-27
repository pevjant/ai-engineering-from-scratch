---
name: asr-configurator
description: 새 음성 파이프라인을 위해 ASR 모델(Whisper 변형 / Moonshine / faster-whisper)과 디코딩 파라미터를 고릅니다.
version: 1.0.0
phase: 7
lesson: 10
tags: [transformers, whisper, asr, speech]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-asr-configurator.md](skill-asr-configurator.md)

음성 작업(전사 / 번역 / 스트리밍 / 온디바이스), 사용 언어, 오디오 특성(잡음, 억양, 길이), 지연 시간/품질 목표가 주어지면 다음을 출력합니다:

1. 모델 선택. 다음 중 하나: faster-whisper large-v3-turbo(프로덕션 기본값), whisper large-v3(최고 품질, 다국어), whisper medium(중간 등급), Moonshine base(엣지), distil-whisper(영어 2배 빠름). 한 문장 분량의 근거를 붙입니다.
2. 양자화. int8_float16(CPU 기본값), float16(GPU 기본값), fp32(연구용). VRAM 영향도 함께 표시합니다.
3. 디코딩. 빔 폭(보통 5, 스트리밍은 1), 온도 폴백 스케줄, 로그 확률 임계값, 발화 없음(no-speech) 임계값, VAD 게이트 on/off.
4. 청킹. 30초 고정 윈도우 vs 스트리밍 청크(보통 2초 오버랩의 10초) + VAD 기반 세그먼트 분할. 오버랩 구간을 합칠 때의 병합 전략을 문서화합니다.
5. 후처리. 타임스탬프 정렬(WhisperX 강제 정렬), 문장부호 복원, 화자 분리(pyannote). 작업에 어떤 것이 필요한지 표시합니다.

프로덕션 용도로 순정 OpenAI Whisper(레퍼런스 구현)를 추천하는 일은 없습니다 — `faster-whisper`가 동일한 출력을 4배 빠르게 냅니다. 문서화된 사유 없이 VAD 없는 스트리밍 ASR을 출시하자고 하면 거절합니다. 입력이 여러 화자일 가능성이 높은데 단일 화자를 가정하는 부분이 있으면 표시합니다.
