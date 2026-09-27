---
name: skill-image-text-retriever
description: 어떤 CLIP 체크포인트로든 이미지 임베딩 인덱스를 구축하고, 텍스트로 찾기와 이미지로 찾기를 지원합니다
version: 1.0.0
phase: 4
lesson: 18
tags: [clip, retrieval, faiss, zero-shot]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-image-text-retriever.md](skill-image-text-retriever.md)

# 이미지-텍스트 검색기

이미지 폴더를 CLIP 임베딩으로 검색 가능한 인덱스로 바꿔 줍니다.

## 사용 시점

- 내부 카탈로그 위에 제로샷 이미지 검색을 만들 때.
- 임베딩 거리로 거의 똑같은 이미지를 중복 제거할 때.
- 레이블된 데이터셋 없이 "비슷한 것 찾기" 컴포넌트를 빠르게 만들 때.

## 입력

- `image_folder`: 이미지 파일 디렉터리.
- `clip_model`: `openai/clip-vit-base-patch32` 또는 `google/siglip-base-patch16-224` 같은 HuggingFace id.
- `index_type`: flat | IVF | HNSW.
- `embedding_dim`: 모델에서 추론합니다.

## 단계

1. CLIP 모델과 전처리기를 불러옵니다.
2. 폴더 안 모든 이미지를 배치로 인코딩합니다. 임베딩을 (N, D) float32 + 파일 이름 목록으로 저장합니다.
3. 임베딩 위에 FAISS 인덱스를 만듭니다. L2 정규화된 벡터에 내적(inner-product)을 쓰면 코사인 유사도가 됩니다.
4. 두 가지 질의 인터페이스를 제공합니다:
   - `search_by_text(text, k)` — 텍스트를 임베딩해서 검색합니다.
   - `search_by_image(image_path, k)` — 이미지를 임베딩해서 검색합니다.

## 출력 템플릿

```python
import os
import glob
import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
import faiss


class ImageTextRetriever:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.model = CLIPModel.from_pretrained(model_name).eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.dim = self.model.config.projection_dim
        self.index = None
        self.filenames = []

    @torch.no_grad()
    def _encode_images(self, paths, batch=16):
        embs = []
        for i in range(0, len(paths), batch):
            imgs = [Image.open(p).convert("RGB") for p in paths[i:i + batch]]
            inputs = self.processor(images=imgs, return_tensors="pt")
            out = self.model.get_image_features(**inputs)
            out = out / out.norm(dim=-1, keepdim=True)
            embs.append(out.cpu().numpy())
        return np.concatenate(embs).astype(np.float32)

    @torch.no_grad()
    def _encode_text(self, texts):
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        out = self.model.get_text_features(**inputs)
        out = out / out.norm(dim=-1, keepdim=True)
        return out.cpu().numpy().astype(np.float32)

    def build_index(self, folder, index_type="flat"):
        exts = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(folder, ext)))
        self.filenames = sorted(files)
        embs = self._encode_images(self.filenames)
        if index_type == "IVF":
            quantizer = faiss.IndexFlatIP(self.dim)
            nlist = min(256, max(4, len(embs) // 32))
            self.index = faiss.IndexIVFFlat(quantizer, self.dim, nlist)
            self.index.train(embs)
        elif index_type == "HNSW":
            self.index = faiss.IndexHNSWFlat(self.dim, 32, faiss.METRIC_INNER_PRODUCT)
        else:
            self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embs)

    def search_by_text(self, text, k=5):
        q = self._encode_text([text])
        dist, idx = self.index.search(q, k)
        return [(self.filenames[i], float(d)) for d, i in zip(dist[0], idx[0])]

    def search_by_image(self, image_path, k=5):
        q = self._encode_images([image_path])
        dist, idx = self.index.search(q, k)
        return [(self.filenames[i], float(d)) for d, i in zip(dist[0], idx[0])]
```

## 보고서

```
[retriever]
  model:          <이름>
  num_images:     <정수>
  dim:            <정수>
  index_type:     flat | IVF | HNSW
  index_size_mb:  <실수>
```

## 규칙

- 인덱싱 전에 항상 임베딩을 L2 정규화합니다. 정규화된 벡터에 대한 FAISS 내적은 코사인 유사도와 같습니다.
- 이미지 10만 장 미만이면 `IndexFlatIP`(정확 검색)가 가장 단순하고 빠릅니다.
- 10만~1,000만 장이면 `IndexIVFFlat`이 표준적인 트레이드오프입니다.
- 1,000만 장을 넘으면 HNSW나 곱 양자화(product-quantised) 변형을 쓰세요.
- 질의할 때마다 인덱스를 다시 만들지 않습니다. 한 번 임베딩하고 여러 번 검색합니다.
