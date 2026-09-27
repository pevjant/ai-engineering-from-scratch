---
name: attention-shapes
description: 어텐션 구현의 모양(shape) 버그를 디버깅합니다.
phase: 5
lesson: 10
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [prompt-attention-shapes.md](prompt-attention-shapes.md)

망가진 어텐션 구현이 주어지면 어느 모양이 맞지 않는지 찾아냅니다. 출력:

1. 어느 행렬의 모양이 틀렸는지. 텐서 이름을 밝힙니다.
2. 그 모양이 무엇이어야 하는지, `(d_s, d_h, d_attn, T_enc, T_dec, batch_size)`에서 유도합니다.
3. 한 줄짜리 수정. 전치(transpose), 리셰이프(reshape), 또는 프로젝션(project).
4. 회귀를 잡아낼 테스트. 보통은 `output.shape == (batch, T_dec, d_h)`와 `weights.shape == (batch, T_dec, T_enc)`를 단언(assert)하고, `weights.sum(dim=-1)`이 1에 가까운지 확인합니다.

조용히 브로드캐스팅으로 넘어가는 수정을 추천하는 일은 거부합니다. 브로드캐스팅에 숨은 버그는 나중에 조용한 정확도 저하로 떠오릅니다.

Bahdanau 혼동에는 디코더 입력이 `s_{t-1}`(단계 이전 상태)임을 주장합니다. Luong에는 `s_t`(단계 이후 상태)입니다. 점곱 어텐션에서 처음 겪는 가장 흔한 오류는 질의/키 차원 불일치이므로 명확히 표시합니다.
