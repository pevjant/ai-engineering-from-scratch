> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-cmer-monitor.md](skill-cmer-monitor.md)

---
name: skill-cmer-monitor
description: 프로덕션 VLM 엔드포인트에 Cross-Modal Error Rate 모니터링, 대시보드, 알림을 계측합니다
version: 1.0.0
phase: 4
lesson: 25
tags: [vlm, production, monitoring, hallucination]
---

# CMER Monitor

크로스 모달 정렬을 1급 프로덕션(운영 환경) KPI로 다루세요.

## 언제 사용하나

- 이미지에 근거한 텍스트를 생성하는 어떤 VLM 엔드포인트든 배포할 때.
- 환각 응답 보고를 조사할 때.
- 입력 분포 변화가 모델 그라운딩을 악화시키는지 추적할 때.

## 입력

- `vlm_output`: 생성된 텍스트.
- `text_confidence`: 소프트맥스 후 토큰별 평균 확률, `[0, 1]` 범위. `exp(mean(log_probs))`로 계산합니다. 원시 로짓을 넘기지 마세요. 원시 로짓은 경계가 없고 `conf_threshold`는 확률을 가정합니다.
- `image_embedding`: 이미지의 CLIP 계열 임베딩(DINOv3, SigLIP, CLIP).
- `text_embedding`: 생성 텍스트의 CLIP 계열 임베딩.
- 선택적 `prompt_type`: 그룹핑용 레이블(vqa / ocr / captioning / agent).

## 요청별 계산

```python
import torch

def cmer_flag(image_emb, text_emb, text_conf, sim_thr=0.25, conf_thr=0.8):
    if image_emb.shape != text_emb.shape:
        raise ValueError(f"emb shape mismatch: {image_emb.shape} vs {text_emb.shape}")
    image_emb = image_emb / (image_emb.norm() + 1e-8)
    text_emb = text_emb / (text_emb.norm() + 1e-8)
    sim = float((image_emb * text_emb).sum())
    flagged = (text_conf > conf_thr) and (sim < sim_thr)
    return {"sim": sim, "flagged": flagged}
```

임베딩은 독립된 CLIP 계열 인코더에서 나온 1차원 PyTorch 텐서(`torch.float32`)입니다. NumPy 배열을 쓴다면 `.norm()`을 `np.linalg.norm(...)`으로 바꾸고 출력을 맞게 캐스팅하세요.

`sim`, `text_conf`, `flagged`, `prompt_type`, `timestamp`, `model_version`, `request_id`를 모니터링 파이프라인(Prometheus, DataDog, OpenTelemetry)에 저장하세요.

## 집계 지표

```
CMER = (윈도우 안 flagged 요청 수) / (윈도우 안 전체 요청 수)
```

엔드포인트별, prompt_type별, 모델 버전별로 보고하세요.

## 알림 임계값

- 베이스라인 CMER: 정상 트래픽 7일치로 확립합니다.
- 경고: CMER가 1시간 동안 베이스라인의 1.5배 이상.
- 심각: CMER가 30분 동안 베이스라인의 2배 이상, 또는 어떤 윈도우에서든 절대값 15% 초과.

## 대시보드 패널

1. 시간에 따른 CMER (5분 버킷, 7일 윈도우).
2. prompt_type별 CMER (누적 막대 그래프).
3. 시간별 `sim` 분포 (히스토그램).
4. 최다 환각 출력 (하루에 flagged 응답 20개를 샘플해 사람 검토).

## CMER 급등 시 행동

1. flagged 요청을 샘플링합니다.
2. 모델 버전이 실수로 바뀌지 않았는지 확인합니다.
3. 입력 분포를 점검합니다(새 파일 형식? 새 이미지 소스? 다르게 압축?).
4. 급등이 해소될 때까지 영향받는 트래픽을 사람 검토로 라우팅합니다.
5. 급등이 지속되면 모델을 파인튜닝하거나 교체합니다; 알림을 억제하지 마세요.

## 규칙

- CMER를 VLM 자신의 임베딩으로 계산하지 마세요. 독립 인코더(DINOv3, SigLIP, 또는 CLIP-L/14)를 쓰세요. 그렇지 않으면 정렬이 아니라 모델의 자기 일관성을 측정하는 셈입니다.
- `flagged` 비트만이 아니라 원시 `sim` 값을 항상 로그하세요. 분포 변화는 flag 비율이 바뀌기 전에 하위 사분위수에 먼저 나타납니다.
- CMER 모니터링 없이 VLM 엔드포인트를 출시하지 마세요. 환각은 지배적인 프로덕션 실패 모드이고, 이 지표 없이는 조용히 지나갑니다.
- 민감 도메인(의료, 법률, 금융)에서는 `sim_threshold`를 0.35 이상으로 올리세요. flag 조건은 `sim < sim_threshold`라서 임계값이 높을수록 더 많은 출력을 근거 없을 가능성이 있는 것으로 잡습니다 — 고위험 용도에 맞는 올바른 기본값입니다.
