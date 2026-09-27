---
name: prompt-caching-planner
description: 캐시에 친화적인 프롬프트 배치를 설계하고 올바른 제공사 캐싱 모드를 고른다
version: 1.0.0
phase: 11
lesson: 15
tags: [llm-engineering, caching, cost]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-prompt-caching-planner.md](skill-prompt-caching-planner.md)

프롬프트(시스템 + 도구 + few-shot + 검색 + 대화 기록 + 사용자)와 사용 패턴(시간당 요청 수, 필요한 TTL, 제공사)이 주어지면 다음을 출력합니다:

1. 배치. 캐시 중단점 하나를 표시해 섹션 순서를 재배치합니다. 어떤 섹션이 안정적이고 어떤 섹션이 변동적인지 설명합니다.
2. 제공사 모드. Anthropic cache_control, OpenAI 자동, 또는 Gemini CachedContent 중 고르고, TTL과 재사용 패턴을 근거로 정당화합니다.
3. 손익분기. TTL 안의 쓰기당 예상 읽기 횟수. 계산 과정과 함께 캐시 없음 대비 순비용을 제시합니다.
4. 검증 계획. 동일한 두 번째 요청에서 cache_read_input_tokens > 0임을 확인하는 CI 어설션. 캐시됨/캐시 안 됨 토큰으로 나눈 대시보드.
5. 실패 모드. 이 구성에서 캐시 미스가 날 가장 가능성 높은 세 가지 이유(동적 타임스탬프, 도구 재정렬, 근사 중복 텍스트)와 각각의 예방 방법을 나열합니다.

동적 필드를 중단점 위에 두는 캐시 계획은 출시를 거부합니다. 2배 쓰기 추가 요금을 복구할 만한 재사용 횟수 없이 1시간 TTL을 켜는 것도 거부합니다.
