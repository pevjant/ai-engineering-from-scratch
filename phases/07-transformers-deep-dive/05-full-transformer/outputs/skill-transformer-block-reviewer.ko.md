---
name: transformer-block-reviewer
description: 트랜스포머 블록 구현을 2026년 기본값과 비교해 검토하고 이탈(drift)을 표시한다.
version: 1.0.0
phase: 7
lesson: 5
tags: [transformers, architecture, review]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-transformer-block-reviewer.md](skill-transformer-block-reviewer.md)

트랜스포머 블록 소스(PyTorch / JAX / numpy / 의사 코드)와 의도된 역할(인코더 / 디코더 / 인코더-디코더)이 주어지면 다음을 출력합니다:

1. 배선 검사. Pre-norm인지 post-norm인지. 각 하위 층을 감싸는 잔차 연결. 작성자가 이유를 명시하지 않는 한 post-norm은 2026년 기본값이 아니라고 표시.
2. 정규화. LayerNorm vs RMSNorm. RMSNorm 선호. Q/K/V/O 프로젝션에 바이어스 항이 있으면 표시 — 2026년 대부분의 모델은 뺍니다.
3. 어텐션 모양. MHA / GQA / MQA / MLA. 디코더 블록이라면: 인과 마스크가 적용되는지 확인. 크로스 어텐션이라면: Q는 디코더에서, K/V는 인코더에서 오는지 확인.
4. FFN. 활성화 함수(ReLU / GELU / SwiGLU / GeGLU). 확장 비율. 약 2.67배 SwiGLU가 현대 기본값; 4배 ReLU/GELU는 고전.
5. 위치 신호. RoPE / ALiBi / 절대 인코딩이 기대되는 자리에 적용되는지 확인(RoPE는 보통 Q, K 프로젝션).

Post-norm에 워밍업 스케줄 없이 12층을 넘게 쌓은 블록에는 승인 도장을 찍지 않습니다 — 학습이 발산합니다. 인과 마스킹 없는 디코더 블록은 거부합니다. FFN 확장 비율이 2배 아래로 떨어진 블록은 용량 부족 가능성이 높다고 표시합니다. 설정(config) 필드 없이 `d_model`을 하드코딩해 크기 교체가 불가능한 블록이면 경고합니다.
