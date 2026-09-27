---
name: transformer-review
description: 밑바닥부터 만든 트랜스포머 구현을 페이즈 7의 13개 레슨 기준으로 검토합니다.
version: 1.0.0
phase: 7
lesson: 14
tags: [transformers, review, capstone]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-transformer-review.md](skill-transformer-review.md)

밑바닥부터 만든 트랜스포머 코드베이스(PyTorch / JAX)가 주어지면 2026년 기본값과 대조해 빠졌거나 잘못된 부분을 표시합니다:

1. 어텐션. 인과 마스크가 있는지. `sqrt(d_head)`로 스케일하는지. 멀티헤드 분할이 동작하는지. 가능하면 Flash Attention을 쓰는지. d_model ≥ 1024이면 GQA 언급.
2. 위치 인코딩. RoPE(2026년 선호) 또는 학습되는 절대 위치 임베딩(작은 모델이면 acceptable). 사인-코사인 방식은 역사적 것으로 표시.
3. 블록 배선. 프리-노름(post-norm 아님). RMSNorm(LayerNorm 아님). SwiGLU FFN(ReLU/GELU 아님). 모든 하위 레이어 주변에 잔차. 선형 레이어의 바이어스 제거(모던 기본값).
4. 학습. AdamW(또는 2026년 이후 Muon), 선형 웜업이 있는 코사인 LR 스케줄, 그래디언트 클리핑 1.0, bf16 autocast. 토큰 임베딩과 lm_head 사이 가중치 결합(tying).
5. 손실. 모든 위치에서 한 칸 밀린(shift-by-one) 교차 엔트로피. 패딩이 있으면 마스킹. 고정 간격으로 학습/검증 손실 기록.

다음 중 하나라도 있으면 코드베이스에 사인오프하지 않습니다: 명시적 사유 없는 post-norm, 정당화 없이 2026년 프로덕션 코드에 LayerNorm, 디코더 셀프 어텐션에 빠진 인과 마스크, 작은 LM에서 결합하지 않은(tied 아닌) 임베딩. 표시 항목: 검증 분할 없음, 그래디언트 클리핑 없음, 웜업 없이 LR > 1e-3, 또는 폴백 없이 위치 임베딩 범위를 초과하는 block_size. `python code/main.py`를 엔드투엔드로 실행해 nano 설정에서 tinyshakespeare의 최종 검증 손실이 2.5 미만에 도착하는지 확인할 것을 권합니다.
