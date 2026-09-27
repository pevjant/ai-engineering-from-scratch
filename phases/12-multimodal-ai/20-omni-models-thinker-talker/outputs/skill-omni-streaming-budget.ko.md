---
name: omni-streaming-budget
description: 목표 TTFAB와 기능 세트에 맞춰 Thinker-Talker 스트리밍 음성 파이프라인(Qwen-Omni / Moshi / Mini-Omni)의 크기를 잡습니다.
version: 1.0.0
phase: 12
lesson: 20
tags: [qwen-omni, moshi, mini-omni, streaming, ttfab, thinker-talker]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-omni-streaming-budget.md](skill-omni-streaming-budget.md)

음성 우선 제품 사양(목표 TTFAB, 마이크 샘플 레이트, 비전 입력 여부, 이중 언어, 전이중)과 컴퓨트 제약(GPU 등급, 예산)이 주어지면, Thinker-Talker 파이프라인의 크기를 잡습니다.

산출물:

1. 모델 계열 선택. Moshi(최고 지연 시간), Qwen2.5-Omni(최고 오픈 기능), Qwen3-Omni(프런티어 품질), Mini-Omni(가장 단순).
2. Thinker와 Talker 크기. 400ms 미만 TTFAB에는 7B Thinker + 200~300M Talker. 품질을 위해 70B 이상 Thinker를 쓴다면 더 큰 TTFAB를 감수.
3. TTFAB 분해. 구성 요소별 지연 시간 추정.
4. 이중 모드. 기본은 VAD 말번대가 있는 반이중; 제품이 끼어들기(backchannel)를 요구하면 전이중.
5. 비전 통합. 인터리브된 비디오 프레임을 위해 절대 타임스탬프를 쓰는 TMRoPE.
6. 배포 형태. 처리량 요구에 따라 단일 GPU vs 분할(Thinker는 A, Talker는 B).

하드 리젝(무조건 거부):

- 70B Talker를 제안하는 것. Talker는 음성 토큰 속도를 따라가려면 작아야 합니다.
- 비스트리밍 음성 디코더를 쓰는 것. TTFAB가 폭발합니다.
- 전이중이 플러그 앤 플레이라고 주장하는 것. 특화된 학습 데이터가 필요합니다.

거부 규칙:

- 목표 TTFAB가 200ms 미만이라면 단일 A100에서 Moshi급(7B 융합)보다 큰 것은 모두 거부합니다.
- 제품이 스트림 도중 음악 생성을 요구한다면 이 아키텍처를 거부하고 별도의 음악 파이프라인을 추천합니다.
- 마이크 샘플 레이트가 48kHz에 품질 요구가 엄격하다면 더 강한 음성 인코더가 필요하다고 표시할 것; 무작정 다운샘플링하지 말 것.

출력: 모델 선택, 크기, TTFAB 분해, 이중 모드, 비전 전략, 배포를 담은 한 페이지짜리 스트리밍 계획서. 마지막에 arXiv 2503.20215 (Qwen2.5-Omni), 2410.00037 (Moshi)를 인용할 것.
