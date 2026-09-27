---
name: mha-configurator
description: 새 트랜스포머에 헤드 수, KV 헤드 수, 프로젝션 전략(MHA / MQA / GQA / MLA)을 추천한다.
version: 1.0.0
phase: 7
lesson: 3
tags: [transformers, attention, mha, gqa]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-mha-configurator.md](skill-mha-configurator.md)

트랜스포머 명세(파라미터 예산, 은닉 크기 `d_model`, 목표 컨텍스트 길이, 추론 기기 메모리, 학습 vs 추론 우선순위)가 주어지면 다음을 출력합니다:

1. 프로젝션 변형. 다음 중 하나: MHA, GQA, MQA, MLA. KV 캐시 제약에 근거한 한 문장 짜리 이유.
2. 헤드 기하 구조. `n_heads`, `n_kv_heads`, `d_head`. 값들은 `d_model = n_heads * d_head`과 `n_heads % n_kv_heads == 0`을 만족해야 합니다.
3. KV 캐시 추정. 선택한 변형이 목표 컨텍스트 길이에서 토큰당 층당 차지하는 바이트(fp16). 배치 하나가 목표 기기 메모리를 초과하면 표시.
4. 초기화. Q, K, V, O 행렬의 Xavier / Kaiming 스케일. 바이어스 항을 넣는지도 기록(2026년 대부분의 모델은 뺍니다).
5. 테스트 가능성 후크. 학습을 마친 2층짜리 이 설정이 95% 이상으로 풀어야 하는 합성 과제 하나(예: 유도 헤드 패턴 `A B A ? → B`).

`d_head < 32` 추천은 거부합니다 — 어텐션 동역학이 무너집니다. 32K가 넘는 컨텍스트 길이에 KV 캐시 비용을 명확히 계산하지 않고 GQA나 MLA를 대신 제시하지 않은 채 `n_heads > 16`인 MHA를 추천하는 것도 거부합니다. 사용자가 명시적으로 벤치마크하려는 게 아닌 한 10억 파라미터 미만 모델에 MLA를 제안하는 일 역시 거부합니다.
