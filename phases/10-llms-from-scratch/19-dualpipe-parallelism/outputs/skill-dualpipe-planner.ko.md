---
name: dualpipe-planner
description: 학습 클러스터를 위한 파이프라인 병렬화 전략(1F1B, Zero Bubble, DualPipe, DualPipeV)을 계획한다.
version: 1.0.0
phase: 10
lesson: 19
tags: [pipeline-parallelism, dualpipe, dualpipev, zero-bubble, expert-parallelism, distributed-training]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-dualpipe-planner.md](skill-dualpipe-planner.md)

학습 클러스터 명세(총 GPU 수, 인터커넥트 토폴로지, 가속기 모델, GPU당 메모리), 모델 형상(전체 파라미터, 활성 파라미터, MoE 또는 밀집, 예상 레이어 수), 목표 학습 데이터량이 주어지면 파이프라인 병렬화 전략을 추천하고 예상 버블 비율을 확인합니다.

산출물:

1. 파이프라인 깊이 P. GPU 메모리 예산(랭크당 파이프라인 스테이지 하나가 들어가야 함), MoE 대 밀집, 인터커넥트 대역폭에 따라 고릅니다. 범위: 작은 클러스터는 4, 최전선 MoE 학습은 16-32.
2. 마이크로배치 수 M. DualPipe와 DualPipeV에서는 2로 나누어떨어져야 합니다. M/P 비율은 보통 8에서 16 사이입니다. 그레이디언트 누적 목표와 목표 시퀀스 길이에서의 활성화 메모리에 비추어 정당화합니다.
3. 스케줄 선택. 1F1B, Zero Bubble, DualPipe, DualPipeV에서 고릅니다. 의사 결정표: 500 GPU 미만의 밀집 학습 -> Zero Bubble. 전문가 병렬화를 쓰는 MoE -> DualPipe. 500 GPU를 넘지만 all-to-all이 무겁지 않은 밀집 학습 -> DualPipeV. 100 GPU 미만의 소규모 실행 -> 1F1B로 충분.
4. 예상 버블 비율. 선택한 스케줄을 목표 P와 M에서 계산합니다. 백분율과, 전체 학습 예산에서 1F1B 대비 절감되는 절대 GPU시간으로 보고합니다.
5. 파라미터 복제 계획(DualPipe에만 해당). 2배 파라미터 복제가 가용 VRAM 안에 들어가는지 확인합니다. 선택한 P에서 GPU당 실효 파라미터 밀도를 보고합니다.

무조건 기각:
- 전문가 병렬화 없이 DualPipe. 숨길 EP 중심 통신이 없다면 2배 복제는 정당화되지 않습니다.
- 어떤 학습 실행이든 P > 64. 스케줄과 무관하게 버블 비율은 P에 비례해 자랍니다.
- DualPipe/DualPipeV에서 마이크로배치 수가 2로 나누어떨어지지 않는 경우. 스케줄이 닫히지 않습니다.
- 모델이 GPU 메모리 한 장에 들어가는데도 파이프라인 병렬화를 쓰는 것. 데이터 병렬화만 쓰십시오.

거부 규칙:
- 인터커넥트가 GPU당 200Gbps 이하라면 DualPipe를 거부하고 DualPipeV를 권합니다. all-to-all 겹침 윈도우가 너무 좁아 복제를 정당화하지 못합니다.
- 사용자가 자기 클러스터 토폴로지에 맞는 커스텀 all-to-all 커널을 제공할 수 없다면 DualPipe 대신 Zero Bubble을 권합니다.
- 학습 실행이 10억 토큰 미만이라면 파이프라인 병렬화 계획 자체를 거부하고, 데이터 병렬화 더하기 텐서 병렬화를 권합니다.

출력: P, M, 스케줄, 예상 버블 비율, 파라미터 복제 비용(DualPipe인 경우), all-to-all 커널 추천을 나열한 한 페이지짜리 계획서. 마지막에 "롤백 트리거" 문단으로, 목표 수치에 못 미치면 더 단순한 스케줄로 전환할 근거가 되는 구체적인 이용률 지표(처음 1000 스텝 동안 측정한 집계 GPU 이용률 백분율)를 명시합니다.
