---
name: chunker
description: 주어진 코퍼스와 질의 분포에 맞는 청킹 전략, 청크 크기, 오버랩을 선택합니다.
version: 1.0.0
phase: 5
lesson: 23
tags: [nlp, rag, chunking]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-chunker.md](skill-chunker.md)

코퍼스 정보(문서 유형, 평균 길이, 도메인)와 질의 분포(단순 사실형 / 분석형 / 멀티홉)가 주어지면 다음을 출력합니다:

1. 전략. Recursive / sentence / semantic / parent-document / late / contextual 중 선택. 근거를 제시합니다.
2. 청크 크기. 토큰 수. 질의 유형에 근거를 둡니다.
3. 오버랩. 기본값 0; 0보다 크면 근거를 제시합니다.
4. 최소/최대 강제. `min_tokens`, `max_tokens` 가드.
5. 평가 계획. 50개 질의 층화 평가셋(단순 사실형, 분석형, 멀티홉)에서 recall@5 측정.

최소/최대 청크 크기 강제가 없는 청킹 전략은 거부합니다. 도움이 된다는 소거 실험(ablation) 없이 20%를 넘는 오버랩은 거부합니다. 최소 토큰 하한 없이 시맨틱 청킹을 추천하면 경고를 표시합니다.
