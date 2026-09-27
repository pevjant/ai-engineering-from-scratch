---
name: audio-llm-pipeline-picker
description: 오디오 과제에 캐스케이드(Whisper + LLM) 또는 엔드투엔드(AF3 / Qwen-Audio)를 고르고, 인코더와 브리지 구성을 잡습니다.
version: 1.0.0
phase: 12
lesson: 19
tags: [whisper, audio-flamingo-3, qwen-audio, cascaded, end-to-end]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-audio-llm-pipeline-picker.md](skill-audio-llm-pipeline-picker.md)

오디오 과제(전사, 요약, 화자 분리, 감정, 음악, 환경음, 딥페이크, 시간적 그라운딩)와 배포 제약이 주어지면, 파이프라인을 고르고 구성을 산출합니다.

산출물:

1. 파이프라인 선택. 깨끗한 음성의 전사 전용 또는 요약 전용이라면 캐스케이드; 음향 과제라면 무조건 엔드투엔드(AF3 / Qwen-Audio).
2. 인코더 스택. Whisper-large-v3(음성에 강함), BEATs(음악에 강함), AF-Whisper concat(균형).
3. 브리지 구성. 비스트리밍에는 32~64쿼리 Q-former; 스트리밍에는 RVQ 토큰.
4. LLM 선택. 비용은 Qwen2.5-7B, 품질은 Qwen2.5-72B 또는 AF3의 백본.
5. 온디맨드 CoT. MMAU 같은 추론 과제에는 켜기; 전사 처리량이 중요하면 끄기.
6. MMAU 기대 정확도. 캐스케이드 ~0.50, Qwen-Audio ~0.60, AF3 ~0.72, Gemini 2.5 Pro ~0.78.

하드 리젝(무조건 거부):

- 음악이나 감정 과제에 캐스케이드를 추천하는 것. 음향 신호가 사라집니다.
- 다중 과제 오디오에 32개 미만 쿼리의 Q-former를 쓰는 것. 추론에 토큰이 부족합니다.
- Whisper만으로 음악을 처리한다고 주장하는 것. 음성 위주 데이터로 학습된 모델입니다.

거부 규칙:

- 실시간 스트리밍 대화 오디오(실시간 음성 입출력)가 필요하다면 Q-former 기반 AF3를 거부하고 Moshi 또는 Qwen-Omni(레슨 12.20)를 추천합니다.
- 지연 시간 예산이 500ms 미만이고 목표가 단순 전사라면 스트리밍 Whisper를 쓴 캐스케이드를 추천합니다.
- 새로운 유형의 오디오 과제(딥페이크, 압축 아티팩트 탐지)라면 기성품을 거부하고 AF3를 합성 데이터로 파인튜닝하는 방안을 제안합니다.

출력: 파이프라인 선택, 인코더 스택, 브리지 구성, LLM 선택, CoT 플래그, 기대 정확도를 담은 한 페이지짜리 계획서. 더 깊은 읽기용으로 마지막에 arXiv 2212.04356 (Whisper)과 2507.08128 (AF3)를 인용할 것.
