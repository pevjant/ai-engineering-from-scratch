---
name: classifier-designer
description: 오디오 분류 작업에 맞는 아키텍처, 증강, 클래스 균형 전략, 평가 지표를 선택합니다.
version: 1.0.0
phase: 6
lesson: 03
tags: [audio, classification, beats, ast]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-classifier-designer.md](skill-classifier-designer.md)

오디오 분류 작업(도메인, 레이블 수, 클립당 레이블 밀도, 데이터 양, 배포 대상)이 주어지면 다음을 출력합니다:

1. 아키텍처. k-NN-MFCC / 2D CNN / AST / BEATs / Whisper-인코더. 한 문장 근거.
2. 증강. SpecAugment 파라미터(시간 마스크, 주파수 마스크 개수), mixup α, 배경 소음 혼합 수준.
3. 클래스 균형. 균형 샘플러 vs focal loss vs 클래스 가중치. 꼬리-머리 비율에 고정.
4. 손실 + 지표. CE / BCE / focal; 주 지표(top-1 / mAP / 매크로-F1)와 부 지표.
5. 분할 + 평가 계획. 층화 k-fold, 음성이라면 화자 분리(speaker-disjoint) 분할, 스트리밍 데이터라면 시간 분할.

top-1 정확도만으로 채점하는 다중 레이블 작업은 거부합니다; mAP를 요구합니다. 화자 분리 분할 없이 화자 조건 작업을 평가하는 것은 거부합니다. 레이블 클립 1만 개 미만에서 처음부터 아키텍처를 만드는 것은 경고를 표시합니다 — SSL 사전학습 백본으로 시작하세요.
