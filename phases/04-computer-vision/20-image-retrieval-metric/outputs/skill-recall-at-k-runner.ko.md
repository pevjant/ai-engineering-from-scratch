> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-recall-at-k-runner.md](skill-recall-at-k-runner.md)

---
name: skill-recall-at-k-runner
description: 학습/검증/갤러리 분할과 올바른 데이터 계약으로 recall@K 평가 하네스를 깔끔하게 작성합니다
version: 1.0.0
phase: 4
lesson: 20
tags: [retrieval, evaluation, recall, faiss]
---

# Recall@K Runner

쿼리·갤러리 이미지 폴더와 레이블을 재현 가능한 recall@K 숫자로 바꿔줍니다.

## 언제 사용하나

- 새 백본의 첫 검색 벤치마크.
- 파인튜닝 에포크마다 임베딩 품질 추적.
- 같은 데이터셋에서 두 검색 시스템 비교.

## 입력

- `query_images`: 경로 목록.
- `gallery_images`: 경로 목록(쿼리와 겹칠 수도, 안 할 수도 있음).
- `query_labels`, `gallery_labels`: 클래스 또는 인스턴스 ID.
- `encoder_fn`: `image -> embedding` 콜러블(미리 계산하거나 실시간).
- `ks`: `[1, 5, 10]` 같은 목록.

## 단계

1. 갤러리 이미지를 한 번씩 인코딩합니다. numpy 배열로 저장하세요.
2. 쿼리 이미지를 인코딩합니다.
3. 두 임베딩 집합을 모두 L2 정규화합니다.
4. 각 쿼리에 대해 모든 갤러리 항목과의 유사도를 계산합니다.
5. 내림차순 정렬 후 상위 max(ks)개를 가져옵니다.
6. 각 K마다 상위 K 갤러리 항목 중 쿼리와 레이블이 같은 것이 있는지 확인합니다.
7. `recall@K = 상위 K 안에 올바른 이웃이 하나라도 있던 질의의 비율`을 보고합니다.

## 출력 템플릿

```python
import numpy as np
from sklearn.preprocessing import normalize

def encode_all(images, encoder_fn, batch=32):
    out = []
    for i in range(0, len(images), batch):
        embs = encoder_fn(images[i:i + batch])
        out.append(embs)
    return np.concatenate(out)


def recall_at_k(query_emb, gallery_emb, q_labels, g_labels,
                ks=(1, 5, 10), query_ids=None, gallery_ids=None):
    if len(query_emb) == 0 or len(gallery_emb) == 0:
        return {f"recall@{k}": 0.0 for k in ks}

    g_label_set = set(g_labels.tolist())
    keep = np.array([lbl in g_label_set for lbl in q_labels])
    if not keep.any():
        return {f"recall@{k}": 0.0 for k in ks}

    q_emb_f = query_emb[keep]
    q_lab_f = q_labels[keep]
    q_id_f = query_ids[keep] if query_ids is not None else None

    q = normalize(q_emb_f)
    g = normalize(gallery_emb)
    sims = q @ g.T

    if q_id_f is not None and gallery_ids is not None:
        self_mask = q_id_f[:, None] == gallery_ids[None, :]
        sims = np.where(self_mask, -np.inf, sims)

    top_k_max = min(max(ks), g.shape[0])
    if top_k_max <= 0:
        return {f"recall@{k}": 0.0 for k in ks}

    top = np.argpartition(-sims, top_k_max - 1, axis=1)[:, :top_k_max]
    sorted_top = np.take_along_axis(
        top, np.argsort(-sims[np.arange(len(q))[:, None], top], axis=1), axis=1
    )
    out = {}
    for k in ks:
        k_eff = min(k, top_k_max)
        hits = np.any(g_labels[sorted_top[:, :k_eff]] == q_lab_f[:, None], axis=1)
        out[f"recall@{k}"] = float(hits.mean())
    return out


def evaluate(query_images, query_labels, gallery_images, gallery_labels, encoder_fn, ks=(1, 5, 10)):
    q_emb = encode_all(query_images, encoder_fn)
    g_emb = encode_all(gallery_images, encoder_fn)
    return recall_at_k(q_emb, g_emb, np.array(query_labels), np.array(gallery_labels), ks)
```

## 보고서

```
[evaluation]
  num queries:   <int>
  num gallery:   <int>
  embedding_dim: <int>

[recall]
  recall@1:  <float>
  recall@5:  <float>
  recall@10: <float>
```

## 규칙

- 유사도를 계산하기 전에 임베딩을 정규화하세요. 정규화된 벡터에 대한 FAISS IndexFlatIP는 코사인과 같습니다.
- 쿼리의 정답 레이블이 갤러리에 없다면 그 쿼리는 제외하세요. 그렇지 않으면 recall이 사실상 1 아래로 제한됩니다.
- 쿼리와 갤러리가 겹치면 쿼리 자신을 top-K에서 제외하세요. 그렇지 않으면 검색이 아니라 자기 유사도를 측정하게 됩니다.
- `num_queries > 10,000`이면 OOM을 피하려고 유사도 행렬 곱을 배치 처리하세요.
