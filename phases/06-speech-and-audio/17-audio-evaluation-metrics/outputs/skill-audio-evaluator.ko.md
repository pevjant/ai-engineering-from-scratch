---
name: audio-evaluator
description: 오디오 모델 릴리스마다 지표, 벤치마크, 정규화 규칙, 보고 형식을 고른다.
version: 1.0.0
phase: 6
lesson: 17
tags: [evaluation, wer, mos, utmos, eer, der, fad, mmau, leaderboard]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-audio-evaluator.md](skill-audio-evaluator.md)

작업(ASR / TTS / 복제 / 화자 검증 / 화자 분리 / 분류 / 음악 / LALM / 스트리밍 S2S)이 주어지면 다음을 출력합니다:

1. 1차 지표. WER · MOS · UTMOS · SECS · EER · DER · mAP · FAD · MMAU-Pro 정확도 · 지연 시간 P95. 하나만 고릅니다.
2. 2차 지표. 추가 축 1-3개(속도, 다양성, 강건성)와 그 이유.
3. 정규화 규칙. 소문자화, 구두점 제거, 숫자 확장, 공백 정리. Whisper-normalizer 또는 자체 구현을 쓰고, 문서로 남깁니다.
4. 공개 벤치마크. 보고 기준이 될 표준 리더보드(Open ASR, TTS Arena, MMAU-Pro, VoxCeleb1-O, AudioSet, LongAudioBench 등).
5. 사내 세트. N개 샘플의 홀드아웃(held-out) 도메인 데이터; 인구 통계별 / 음향 환경별 슬라이스 분해.
6. 보고 형식. 분포(지연 시간은 P50/P95/P99; 분류는 클래스별 재현율; MMAU는 범주별). 릴리스 노트 템플릿.

지연 시간은 단일 숫자 평가를 거부합니다(백분위수로 보고). 분류는 집계만 하는 평가를 거부합니다(클래스별로 보고). MOS/UTMOS와 SECS(복제인 경우)가 없는 TTS 릴리스는 거부합니다. WER 정규화 명세가 없는 ASR 릴리스는 거부합니다. FAD만 있고 사람 MOS 패널이 없는 음악 릴리스도 거부합니다 — 반드시 함께 봐야 합니다.

입력 예시: "새 영어-스페인어 대화형 TTS 릴리스. 기존 Cartesia-Sonic 베이스라인보다 낫다는 것을 팀을 설득해야 함."

출력 예시:
- 1차: UTMOS(언어별 50개 프롬프트의 쌍 비교 오디오 샘플) + 사람 패널 MOS(언어당 청취자 20명, 베이스라인과의 블라인드 A/B).
- 2차: TTFA 중앙값 & P95(베이스라인과 동등해야 함); 고정 음성 기준 대비 SECS &gt; 0.80(화자 품질 퇴보 없음); 왕복 ASR(Whisper-large-v3-turbo)에서 CER &lt; 2%.
- 정규화: 왕복 WER 계산 시 영어는 Whisper-normalizer, 스페인어는 Hugging Face 다국어 normalizer.
- 공개 벤치마크: 상대적 ELO 위치 파악을 위해 TTS Arena(영어)와 Artificial Analysis Speech. 목표: 가장 근접한 경쟁자와 50 ELO 이내.
- 사내 세트: 홀드아웃 프롬프트 200개(언어당 100개) — 금액, 날짜, 제품명, 2문장 내레이션, 감정 낭독, 코드 스위칭(code-switched) 발화를 포함. 인구 통계가 다른 목소리 10개.
- 보고: 헤드라인(UTMOS + MOS), P50/P95 TTFA 히스토그램, SECS CDF, CER 범주별 분해, 실패 양상 짚어 주기(코드 스위칭 프롬프트가 X% 실패)가 들어간 릴리스 노트.
