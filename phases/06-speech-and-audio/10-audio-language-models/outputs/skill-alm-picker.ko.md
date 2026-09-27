> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-alm-picker.md](skill-alm-picker.md)

---
name: alm-picker
description: 오디오 이해 과제를 위해 오디오 언어 모델, 벤치마크 하위 집합, 출력 모달리티(텍스트 vs 음성), 가드레일을 고른다.
version: 1.0.0
phase: 6
lesson: 10
tags: [alm, lalm, qwen-omni, audio-flamingo, gemini-audio, mmau]
---

과제(음성 / 소리 / 음악 / 멀티 오디오 / 긴 오디오, 출력 모달리티, 지연 시간, 라이선스)가 주어지면 다음을 출력한다:

1. 모델. Qwen2.5-Omni-7B · Qwen3-Omni · SALMONN · Audio Flamingo 3 · AF-Next · LTU · GAMA · Gemini 2.5 Pro (API) · GPT-4o Audio (API). 한 문장 근거.
2. 검증할 벤치마크 하위 집합. MMAU-Pro 음성 / 소리 / 음악 / 멀티 오디오 · LongAudioBench · AudioCaps · ClothoAQA. 사용자 과제에 맞는 축을 고른다.
3. 출력 모달리티. 텍스트 전용 · 텍스트 + 음성 (Qwen-Omni, GPT-4o Audio). 필요하면 음성 디코더 추가 비용을 예산에 반영한다.
4. 가드레일. 모델의 멀티 오디오 점수가 &lt; 30%(무작위에 가까움)라면 멀티 오디오 비교가 필요한 프롬프트는 거부한다. 10분을 넘는 입력에는 LALM 전에 화자 분리를 수행한다.
5. 상위 에스컬레이션. 어떤 때 이 과제를 전문 모델로 넘길지 — 전사는 Whisper, 분류는 BEATs, 화자 분리는 pyannote. LALM은 어느 하나의 최고는 아니다.

MMAU-Pro 멀티 오디오 하위 집합에서 모델 점수가 &gt; 40%인지 확인 없이 멀티 오디오 비교 과제를 배포하는 것은 거부한다. 상류 화자 분리 없이 긴 오디오(&gt; 10분)를 처리하는 것은 거부한다. 독립적 재검증 없이 벤더가 보고한 수치를 쓰는 배포는 표시(플래그)한다.

예시 입력: "컴플라이언스 감사: 10분짜리 은행 상담 녹음을 전사 + 상담원이 필수 고지 문구를 읽었는지 탐지."

예시 출력:
- 모델: 전사는 Whisper-large-v3-turbo + 전사본 위의 고지 확인 QA는 Gemini 2.5 Pro (API). 날 오디오에 LALM을 바로 쓰고 싶지만, 긴 오디오에서 LALM 정확도는 10분을 넘으면 떨어진다.
- 벤치마크 하위 집합: MMAU-Pro 음성 하위 집합 (Gemini 2.5 Pro = 73.4%) — 음성 추론 축을 커버. 자체 50건 골드 세트로도 스팟 체크.
- 출력 모달리티: 텍스트 전용. 감사 보고서에는 음성 출력이 불필요.
- 가드레일: 먼저 pyannote 3.1로 화자 분리. 화자별 세그먼트를 따로 전송. 건당 신뢰도 점수 기록.
- 에스컬레이션: 고지 확인에 통과 못한 상담은 자동 플래그 대신 사람 검토자에게 넘긴다.
