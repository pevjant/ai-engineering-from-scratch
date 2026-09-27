---
name: skill-linear-probe-runner
description: 어떤 얼린 인코더와 레이블된 데이터셋 조합이든 선형 프로브 평가 전체를 작성합니다
version: 1.0.0
phase: 4
lesson: 17
tags: [self-supervised, evaluation, linear-probe, pytorch]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-linear-probe-runner.md](skill-linear-probe-runner.md)

# 선형 프로브 러너

얼려 둔 인코더의 특성을, 그 위에 선형 분류기 하나만 학습시켜서 평가합니다. 모든 자기지도 학습 논문이 쓰는 표준 평가입니다.

## 사용 시점

- 자기지도 학습 체크포인트들을 비교할 때.
- 사전 학습 에포크가 진행됨에 따라 특성 품질을 추적할 때.
- 파인튜닝 없이도 사전 학습된 인코더가 다운스트림 작업에 충분한지 판단할 때.

## 입력

- `encoder`: 이미지당 고정 차원의 특성을 돌려주는 얼려 둔 `nn.Module`.
- `feature_dim`: 인코더 출력의 차원.
- `train_dataset`: 레이블된 데이터셋 (image, class_id).
- `val_dataset`: 홀드아웃(held-out) 세트.
- `num_classes`: 작업의 클래스 수.
- `epochs`: ImageNet 규모면 보통 100, 더 작은 데이터셋이면 50.

## 단계

1. 인코더를 eval 모드로 두고 모든 파라미터에 `requires_grad=False`를 설정합니다.
2. train과 val 세트의 특성을 한 번씩 추출합니다. numpy 배열이나 메모리 매핑 파일로 저장합니다.
3. 캐시한 특성 위에서 `nn.Linear(feature_dim, num_classes)`를 SGD + 코사인 스케줄로 학습합니다.
4. 표준 하이퍼파라미터: `lr=0.1`, `momentum=0.9`, `weight_decay=0`, `batch_size=1024`. 선형 프로브는 `lr`에 의외로 민감합니다 — 정확도가 나쁘면 스윕하세요.
5. 학습이 끝나면 val에 대한 top-1 정확도를 보고합니다.

## 출력 템플릿

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.optim import SGD
from torch.optim.lr_scheduler import CosineAnnealingLR

def extract(encoder, loader, device="cpu"):
    encoder.eval()
    feats, labels = [], []
    with torch.no_grad():
        for x, y in loader:
            f = encoder(x.to(device)).cpu()
            feats.append(f)
            labels.append(y)
    return torch.cat(feats), torch.cat(labels)


def linear_probe(encoder, feature_dim, train_loader, val_loader,
                 num_classes, epochs=50, lr=0.1, device="cpu"):
    for p in encoder.parameters():
        p.requires_grad = False

    f_train, y_train = extract(encoder, train_loader, device)
    f_val, y_val = extract(encoder, val_loader, device)

    head = nn.Linear(feature_dim, num_classes).to(device)
    opt = SGD(head.parameters(), lr=lr, momentum=0.9, weight_decay=0)
    sched = CosineAnnealingLR(opt, T_max=epochs)

    ds = torch.utils.data.TensorDataset(f_train, y_train)
    train_iter = DataLoader(ds, batch_size=1024, shuffle=True)

    best_val = 0.0
    for ep in range(epochs):
        head.train()
        for x, y in train_iter:
            x, y = x.to(device), y.to(device)
            loss = F.cross_entropy(head(x), y)
            opt.zero_grad(); loss.backward(); opt.step()
        sched.step()

        head.eval()
        with torch.no_grad():
            acc = (head(f_val.to(device)).argmax(-1).cpu() == y_val).float().mean().item()
        best_val = max(best_val, acc)
    return best_val
```

## 보고서

```
[linear probe]
  encoder:     <이름 + 사전 학습 체크포인트>
  feature_dim: <정수>
  epochs:      <정수>
  best_val_top1: <실수>
```

## 규칙

- 선형 프로브 중에 인코더 가중치를 절대 업데이트하지 않습니다. 그건 프로브가 아니라 파인튜닝입니다.
- 특성은 한 번만 미리 계산합니다. 에포크마다 인코더를 다시 돌리면 100배의 컴퓨팅을 낭비합니다.
- 코사인 스케줄과 가중치 감쇠 없는 SGD를 사용하세요. Adam은 여기서 종종 성능이 떨어집니다.
- 인코더 계열마다 학습률을 최소 한 번은 스윕하세요. 최적값은 SSL 방법마다 다릅니다.
