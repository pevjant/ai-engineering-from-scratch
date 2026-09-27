---
name: skill-ctc-decoder
description: 길이 정규화를 포함해서 그리디 및 빔 서치 CTC 디코더를 처음부터 작성합니다
version: 1.0.0
phase: 4
lesson: 19
tags: [ocr, ctc, decoding, sequence-models]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-ctc-decoder.md](skill-ctc-decoder.md)

# CTC 디코더

CTC 출력을 위한 두 가지 디코딩 루틴을 만들어 냅니다: 그리디(빠름)와 빔(노이즈가 많은 입력에서 더 나음).

## 사용 시점

- 커스텀 CRNN 출력에 대해 OCR 추론을 돌릴 때.
- 사전 학습된 OCR 모델을 여러 디코더로 벤치마크할 때.
- ctcdecode를 가져오지 않고 간단한 빔 서치를 구현할 때.

## 입력

- `log_probs`: (T, N, C) 어휘에 대한 log-softmax (관례상 인덱스 0 = blank).
- `vocab`: C개 문자의 목록.
- `beam_width`(빔 전용): 보통 5~10.

## 그리디 디코더

```python
def greedy_ctc_decode(log_probs, vocab, blank=0):
    preds = log_probs.argmax(dim=-1).transpose(0, 1).cpu().tolist()
    out = []
    for seq in preds:
        decoded = []
        prev = None
        for idx in seq:
            if idx != prev and idx != blank:
                decoded.append(vocab[idx])
            prev = idx
        out.append("".join(decoded))
    return out
```

## 빔 서치 디코더

```python
import heapq
import math

def beam_ctc_decode(log_probs, vocab, beam_width=5, blank=0):
    T, N, C = log_probs.shape
    lp = log_probs.cpu()
    results = []
    for n in range(N):
        beams = {("",): (0.0, -math.inf)}  # (접두사 튜플) -> (p_blank, p_nonblank)
        for t in range(T):
            logits_t = lp[t, n]
            new_beams = {}
            for prefix, (p_b, p_nb) in beams.items():
                for c in range(C):
                    p = logits_t[c].item()
                    if c == blank:
                        nb = p_b + p
                        nnb = p_nb + p
                        upd = new_beams.get(prefix, (-math.inf, -math.inf))
                        new_beams[prefix] = (
                            _logsumexp(upd[0], _logsumexp(nb, nnb)),
                            upd[1],
                        )
                    else:
                        last = prefix[-1] if prefix else ""
                        char = vocab[c]
                        if char == last:
                            # 경우 1: 같은 접두사에 머무름 (p_nb에서 병합)
                            upd = new_beams.get(prefix, (-math.inf, -math.inf))
                            new_beams[prefix] = (upd[0], _logsumexp(upd[1], p_nb + p))
                            # 경우 2: blank로 분리된 반복을 통해 접두사 확장 ("a_a" -> "aa")
                            new_prefix = prefix + (char,)
                            upd = new_beams.get(new_prefix, (-math.inf, -math.inf))
                            new_beams[new_prefix] = (upd[0], _logsumexp(upd[1], p_b + p))
                        else:
                            new_prefix = prefix + (char,)
                            upd = new_beams.get(new_prefix, (-math.inf, -math.inf))
                            nb = _logsumexp(p_b, p_nb) + p
                            new_beams[new_prefix] = (upd[0], _logsumexp(upd[1], nb))
            beams = dict(heapq.nlargest(
                beam_width,
                new_beams.items(),
                key=lambda kv: _logsumexp(kv[1][0], kv[1][1]),
            ))
        best = max(beams.items(), key=lambda kv: _logsumexp(kv[1][0], kv[1][1]))[0]
        results.append("".join(best))
    return results


def _logsumexp(a, b):
    if a == -math.inf: return b
    if b == -math.inf: return a
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))
```

## 규칙

- CTC의 blank 인덱스는 PyTorch의 `nn.CTCLoss`에서 관례상 0입니다.
- 빔 서치는 확신도가 낮은 입력에서 정확도를 끌어올립니다. 깨끗한 입력에서는 개선 폭이 CER 1% 미만입니다.
- 빔 폭을 5 미만으로 좁히지 않습니다. 그 아래로는 정확도-지연 시간 트레이드가 평평해집니다.
- 지연 시간 예산이 빠듯한 상황에서 빔 서치를 돌리고 있다면 그리디로 내려오세요. 대부분의 프로덕션 OCR 데이터에서 품질 손실은 작습니다.
- 어휘가 크다면(CJK, 3,000자 이상) 위의 순수 Python 버전 대신 `ctcdecode`(C++)으로 전환하세요. Python 빔은 금세 병목이 됩니다.
