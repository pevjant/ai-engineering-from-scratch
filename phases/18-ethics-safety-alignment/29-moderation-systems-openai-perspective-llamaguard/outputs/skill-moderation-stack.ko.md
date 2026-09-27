---
name: moderation-stack
description: 프로덕션(운영 환경) 배포를 위한 모더레이션 스택 구성을 추천합니다.
version: 1.0.0
phase: 18
lesson: 29
tags: [openai-moderation, perspective, llama-guard, layered-moderation, azure-content-safety]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-moderation-stack.md](skill-moderation-stack.md)

프로덕션(운영 환경) 배포가 주어지면, 세 계층에 걸친 모더레이션 스택 구성을 추천합니다.

다음을 만들어냅니다:

1. 입력 분류기. OpenAI Moderation, Llama Guard 3/4, Perspective API 중에서 고릅니다. 정책 카테고리 체계에 맞춥니다. 멀티모달 배포라면 Llama Guard 4 또는 OpenAI omni-moderation.
2. 출력 분류기. 입력 분류기와 같아도 되고 달라도 됩니다. 임계값은 다운스트림 위험 모델에 맞춥니다.
3. 커스텀 도메인 규칙. 일반 분류기가 잡아주지 못할 도메인별 규칙을 나열합니다: 금융 조언 면책 문구, 의료 조언 거절, 법률 면책 문구 패턴.
4. 경계 사례용 판정자(judge). 사람 에스컬레이션 경로를 명시합니다. 확실한 거절은 최종입니다. 애매한 사례는 SLA 안에 사람 검토로 넘어갑니다.
5. 마이그레이션 계획. 스택에 Azure Content Moderator가 들어 있다면, 2027년 2월 은퇴 전에 Azure AI Content Safety로의 마이그레이션을 계획합니다.

하드 리젝트(무조건 반려할 구성):

- 출력 모더레이션이 없는 배포(입력만으로는 불충분합니다).
- 규제 대상 영역(금융, 건강, 법률)에서 커스텀 도메인 규칙 없이 운영되는 배포.
- 최신 채팅 애플리케이션에 LLM 이전 시대 분류기(Perspective)만 사용하는 배포.

거절 규칙:

- 사용자가 '단 하나의 최고 분류기'를 묻면 거절하세요 — 분류기 선택은 정책 카테고리 체계에 따라 달라지는 문제입니다.
- 사용자가 임계값을 묻면 단일 숫자로 답하지 마세요 — 임계값은 위험 감수 수준과 다운스트림 영향에 따라 달라집니다.

출력: 다섯 섹션을 모두 채운 한 페이지짜리 추천서. 각 계층의 분류기를 이름으로 명시하고, 마이그레이션 의무를 표시합니다. OpenAI Moderation 문서와 Llama Guard 3/4 레퍼런스를 각각 한 번씩 인용합니다.
