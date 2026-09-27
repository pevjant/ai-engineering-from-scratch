---
name: checkpointing-planner
description: 학습 설정과 HBM 예산이 주어지면 레이어별 활성값 재계산 정책(없음 / 선택적 / 전체 / 오프로드)을 고릅니다.
version: 1.0.0
phase: 10
lesson: 34
tags: [gradient-checkpointing, activation-recomputation, selective-checkpoint, fsdp-offload, training-memory]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-checkpointing-planner.md](skill-checkpointing-planner.md)

학습 설정(레이어 수 L, 은닉 크기 d, 시퀀스 길이 S, 미니배치 B, 값당 dtype 바이트, 어텐션 커널, 텐서 병렬도 TP, 파이프라인 병렬도 PP, MoE라면 전문가 병렬도 EP)과 가중치 및 옵티마이저 상태를 뺀 랭크별 HBM 예산이 주어지면 다음을 출력합니다:

1. 레이어별 정책. 스택의 각 레이어 계열(임베딩, 어텐션, FFN, MoE 전문가, 정규화, 출력 헤드)에 대해 없음(none), 선택적(selective), 전체(full), 오프로드(offload) 중 하나를 고릅니다. S가 4,096을 넘으면 어텐션은 기본적으로 selective, 잔차 스트림과 정규화는 기본적으로 none. FFN은 해당 레이어 활성값의 측정된 PCIe 전송 시간이 측정된 재계산 시간보다 짧을 때만 기본적으로 offload.
2. 구간 크기 k. 전체 체크포인팅이 켜져 있으면, 비용이 균일한 레이어에서는 k = round(sqrt(L))로 고르고, 활성값 메모리가 예산을 지배하면 더 작은 k를 고릅니다. 추가 FLOP 비율을 순전파 FLOPs의 (1/k)로 보고합니다.
3. FlashAttention 상호작용. 어텐션 커널이 이미 소프트맥스를 재계산하는지 확인합니다. 그렇다면 어텐션 선택적 체크포인팅은 얻는 게 거의 없으므로 none으로 격하합니다. 커널 이름을 명시합니다(FlashAttention-2/3, xFormers memory-efficient, vanilla).
4. TP / PP 계획. TP의 경우 재계산 시 gather 또는 rescatter가 필요한 활성값과 단계당 추가 통신 바이트를 밝힙니다. PP의 경우 어떤 파이프라인 스테이지가 종단 간 체크포인트 되어, 역방향 미니배치가 되돌아가기 전에 활성값 메모리를 해제하는지 확인합니다.
5. 예산 계산. 정책 적용 전과 후의 활성값 메모리를 예측합니다(랭크당 MB). FLOP 오버헤드를 순전파+역전파 대비 퍼센트로 예측합니다. 여유 10%를 두고도 HBM 예산에 들어가지 않는 계획은 거부합니다.

어텐션만 선택적으로 해도 예산이 맞는 경우 레이어마다 전체 체크포인팅은 거부합니다. 프로파일링 결과 같은 메모리 절감에 FLOP 오버헤드가 선택적 방식보다 몇 배나 높으며, 정확한 비율은 작업 부하에 따라 달라집니다. 대상 PCIe 링크에서 해당 레이어의 측정된 활성값 전송 시간이 측정된 재계산 시간을 넘으면 오프로드는 거부합니다. 재계산이 이깁니다. 선택한 프레임워크가 amax 이력을 스냅샷으로 저장하지 않는 FP8 학습에 "모든 곳에 체크포인트"는 거부합니다. 재계산이 스케일을 흐트러뜨리고 조용히 그래디언트를 망가뜨립니다.

입력 예: "L=64, d=8192, S=8192, B=1, bf16, FlashAttention-3, TP=8, PP=4, 랭크당 HBM 예산 32 GB(가중치 제외), 전문가 8개 EP=8인 MoE."

출력 예:
- 레이어별 정책: 어텐션 selective, FFN none, MoE 전문가 full, 임베딩 none, 출력 헤드 offload.
- 구간 크기: full은 MoE에만 k=8로 적용. FLOP 오버헤드는 전문가 경로에서 12%, 그 외 0%.
- FlashAttention 상호작용: FA-3는 이미 소프트맥스를 재계산함. 선택적 체크포인트는 커널 내부가 아니라 레이어 래퍼에서.
- TP / PP 계획: TP는 재계산 시 어텐션 입력 gather, 단계당 추가 통신 0.3 GB. PP 스테이지는 각자 전체 순전파를 체크포인트. PP 스테이지 3은 최종 역전파를 위해 활성값을 유지.
- 예산 계산: 활성값은 정책 없이 38 GB, 정책 적용 시 11 GB. 총 FLOP 오버헤드는 순전파+역전파 대비 7.5%.
