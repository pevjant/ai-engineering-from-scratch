---
name: skill-pipeline-budget-planner
description: 목표 지연 시간과 처리량이 주어지면 모든 파이프라인 단계에 시간 예산을 배정하고, 예산을 가장 먼저 넘길 단계를 표시합니다
version: 1.0.0
phase: 4
lesson: 16
tags: [vision, pipeline, performance, deployment]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-pipeline-budget-planner.md](skill-pipeline-budget-planner.md)

# 파이프라인 예산 플래너

지연 시간/처리량 목표를 단계별 예산으로 바꿔 줍니다. 그래야 모든 팀원이 자기가 향해 나아가야 할 숫자를 알 수 있으니까요.

## 사용 시점

- 새 비전 서비스를 만들기 전에, 각 단계의 기대치를 정하려고.
- 첫 벤치마크 후에, 어느 단계가 예산에서 가장 멀리 떨어져 있는지 보려고.
- SLA가 바뀌어서 예산을 다시 조정해야 할 때.

## 입력

- `p95_latency_target_ms`: 요청당 예산.
- `target_qps`: 레플리카당 처리량.
- `stages`: `{ name: str, current_ms: float }` 목록.

## 배분 규칙

현재 측정값이 주어지지 않았을 때의 일곱 표준 단계 기본 배분:

| 단계 | 비중 |
|-------|-------|
| decode + preprocess | 15% |
| detector forward | 55% |
| postprocess detections (NMS, clamp) | 5% |
| crop + resize for classifier | 5% |
| classifier forward | 15% |
| schema validation | <1% |
| response serialisation | 4% |

GPU 바운드 파이프라인(클라우드)에서는 검출기 비중이 보통 70%까지 올라갑니다. CPU에서는 전처리와 분류기 배칭이 더 많이 잡아먹습니다.

## 보고서

```
[budget plan]
  p95 target:  <ms>
  throughput:  <replica당 qps>

| stage               | target_ms | current_ms | headroom | gate |
|---------------------|-----------|------------|----------|------|
| decode+preprocess   | ...       | ...        | ...      | ok|X |
| detector            | ...       | ...        | ...      | ok|X |
| ...                 | ...       | ...        | ...      |      |

[bottleneck]
  stage:  <이름>
  miss:   <예산 초과 ms>
  lever:  <구체적인 조치>

[levers]
  decode+preprocess:   Pillow-SIMD, libjpeg-turbo, NVJPEG로 GPU 디코딩
  detector:            더 작은 백본, 더 낮은 입력 해상도, INT8, TensorRT
  postprocess:         GPU 측 NMS (torchvision.ops), 융합된 마스크
  crop+resize:         grid_sample을 쓰는 GPU 크롭, 배치 interpolate
  classifier:          더 작은 백본, INT8, 웜 캐시, 배치
  schema:              핫패스에서는 검증 생략, 경계에서만 검증
  response:            orjson, protobuf 스트리밍
```

## 규칙

- 프로덕션 경로에서 스키마 검증을 빼 버리는 방향은 절대 추천하지 않습니다. 대신 경계로 옮기는 방안을 제안하세요.
- 전처리가 예산을 넘겼다면 모델을 바꾸기 전에 항상 Pillow-SIMD나 NVJPEG를 먼저 시도하세요.
- 검출기의 초과분이 목표의 30%를 넘으면 현재 모델을 최적화하는 대신 모델을 교체하세요.
- current_ms > 1.1 * target_ms이면 게이트를 `X`로 표시하고, 예산의 10% 이내면 `ok`로 표시하세요.
