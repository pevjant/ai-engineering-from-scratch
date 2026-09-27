---
name: skill-library
description: 유사도 기반 검색, 조합 실행, 실패 기반 정제를 갖춘 Voyager 스타일 스킬 라이브러리를 생성합니다.
version: 1.0.0
phase: 14
lesson: 10
tags: [voyager, skills, library, composition, refinement]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-skill-library.md](skill-skill-library.md)

대상 런타임과 도메인이 주어지면, Voyager의 세 구성 요소 — 커리큘럼 훅, 검색 가능한 스킬 저장소, 반복 정제 — 를 지원하는 스킬 라이브러리를 만들어 냅니다.

만들 것:

1. `name`, `description`, `code`, `version`, `tags`, `depends_on`, `history`를 가진 `Skill` 타입. 쓸 때마다 이전 코드를 기록합니다.
2. `register(skill, dedup=True)`(새로 등록하거나 버전을 올림), `search(query, top_k, tag_filter)`, `get(name)`, `topo_order(name)`(의존성 해결), `execute(name, context)`(위상 정렬 실행)을 갖춘 `SkillLibrary`.
3. 검색은 반드시(MUST) 임베딩 유사도나 BM25를 써야 하며, 라이브러리 전체를 대상으로 한 LLM 스코어링을 쓰면 안 됩니다. 상위 k 후보 목록에 한해 LLM 재정렬은 허용됩니다.
4. 실행은 반드시(MUST) 스킬별로 예외를 잡아, 정제 루프가 소비할 수 있는 피드백 형태로 추적 기록에 드러내야 합니다.
5. 정제 훅: `execute`가 실패하면 런타임이 (task, skill_name, error, env_state)를 모아 모델에 넘기고, 다시 쓴 스킬로 `register`를 호출합니다. 버전은 올라가고, history에는 기존 코드가 남습니다.

절대 반려 사항:

- 스킬이 코드가 아니라 산문 문자열인 라이브러리. 스킬은 실행 가능해야 합니다. 산문은 `description`에 들어갑니다.
- 위상 정렬 없는 조합. 순환 감지 없는 깊이 우선 탐색은 스킬 DAG에서 깨집니다.
- 조용한 버전 덮어쓰기. 모든 정제는 반드시(MUST) `version`을 올리고, 감사를 위해 기존 코드를 `history`로 밀어 넣어야 합니다.

거절 규칙:

- 대상 런타임에 스킬 실행용 샌드박스가 없다면, 스킬이 프로덕션(운영 환경) 시스템을 건드리는 도메인에 대해서는 거절하세요. 출시 전에 샌드박스(레슨 09 원칙)를 요구합니다.
- 사용자가 "정제 없이 실패마다 자동 재시도"를 요구하면 거절하세요. 정제 없는 재시도는 버그를 고치는 게 아니라 증폭합니다.
- 평면 검색 상태로 라이브러리가 약 200개 스킬을 넘어섰다면 "프로덕션 준비 완료"라고 부르는 것을 거절하세요. 먼저 태그 필터와 계층적 네임스페이스를 추가합니다.

출력: `skill.py`, `library.py`, `execute.py`, `refine.py`, 그리고 중복 제거 규칙·검색 백엔드·정제 프롬프트·버전 정책을 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — Claude Agent SDK 통합은 레슨 17, OpenAI Agents SDK 도구 번역은 레슨 16, 스킬 라이브러리 품질 평가는 레슨 30을 가리킵니다.
