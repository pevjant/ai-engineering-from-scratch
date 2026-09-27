---
name: skill-mot-evaluator
description: 정답 트랙 대비 MOTA / IDF1 / HOTA 평가 하네스 전체를 작성한다
version: 1.0.0
phase: 4
lesson: 27
tags: [mot, evaluation, tracking, metrics]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mot-evaluator.md](skill-mot-evaluator.md)

# MOT 평가기 (MOT Evaluator)

트래커의 출력을 표준 MOTA/IDF1/HOTA 파이프라인에 넣어, 논문의 수치와 공정하게 비교할 수 있게 만듭니다.

## 사용 시점

- MOT17 / MOT20 / DanceTrack / SportsMOT에서 새 트래커 벤치마킹.
- 직접 촬영한 영상에서 ByteTrack과 BoT-SORT, SAM 2 비교.
- 논문이나 PR 설명에 넣을 재현 가능한 숫자 만들기.

## 입력

- `predictions`: 프레임별 `(track_id, x, y, w, h, confidence)` 튜플 목록.
- `ground_truth`: 프레임별 `(gt_id, x, y, w, h)` 튜플 목록.
- `iou_threshold`: MOTA에는 보통 0.5. HOTA는 스윕(sweep)을 사용.
- `evaluator`: `py-motmetrics` (MOTA, IDF1) 또는 `TrackEval` (HOTA).

## 출력 형식 계약(contract)

`py-motmetrics`와 `TrackEval` 모두 디스크 상의 특정 형식을 기대합니다:

```
# predictions.txt
<frame>,<track_id>,<x>,<y>,<w>,<h>,<confidence>,-1,-1,-1

# ground_truth.txt
<frame>,<gt_id>,<x>,<y>,<w>,<h>,1,-1,-1,-1
```

프레임은 1부터 시작하고, 박스는 (x1, y1, x2, y2)가 아니라 (x, y, w, h)입니다. 통합 버그는 대부분 이 형식 변환에서 나옵니다.

## 단계

1. 트래커의 출력을 MOT Challenge 텍스트 형식으로 변환한다.
2. 두 파일 모두에 `py-motmetrics.io.loadtxt`를 실행한다.
3. `mm.metrics.create().compute()`로 MOTA + IDF1을 계산한다.
4. HOTA는 같은 파일로 `TrackEval`을 호출하되 `Metrics: HOTA`로 지정한다.
5. 결과를 JSON으로 저장해 대시보드에 쓴다.

## 구현 스케치

```python
import motmetrics as mm

def evaluate_mota_idf1(pred_path, gt_path):
    gt = mm.io.loadtxt(gt_path, fmt="mot15-2D")
    pred = mm.io.loadtxt(pred_path, fmt="mot15-2D")
    acc = mm.utils.compare_to_groundtruth(gt, pred, dist="iou", distth=0.5)
    metrics = mm.metrics.create().compute(
        acc, metrics=["num_frames", "mota", "motp", "idf1", "idp", "idr", "num_switches"]
    )
    return metrics


def write_mot_txt(predictions, path):
    with open(path, "w") as f:
        for frame_idx, detections in enumerate(predictions, start=1):
            for tid, x, y, w, h, conf in detections:
                f.write(f"{frame_idx},{tid},{x:.2f},{y:.2f},{w:.2f},{h:.2f},{conf:.3f},-1,-1,-1\n")
```

## 보고서

```
[mot evaluation]
  frames:     <int>
  gt tracks:  <int>
  pred tracks: <int>

[metrics]
  MOTA:       <float>
  MOTP:       <float>
  IDF1:       <float>
  IDP/IDR:    <float/float>
  ID switches: <int>
  HOTA:       <float>  (from TrackEval)
```

## 규칙

- 출력 텍스트 파일의 프레임 번호는 반드시 1부터 시작한다. MOT 도구들이 이를 기대한다.
- 쓰기 전에 (x1, y1, x2, y2)를 (x, y, w, h)로 변환한다.
- 현대적 비교에서 MOTA 하나만 보고하지 않는다. IDF1과 HOTA를 함께 넣는다.
- MOT17의 private vs public 검출 구분을 주의한다 — 두 경우는 따로 평가되며, 섞으면 점수가 부풀려진다.
- 시퀀스별 점수를 기록한다. 집계 평균은 어려운 시퀀스 하나에서의 실패를 감춰 버린다.
