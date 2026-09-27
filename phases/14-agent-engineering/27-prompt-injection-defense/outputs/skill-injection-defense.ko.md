---
name: injection-defense
description: 출처 태그가 붙은 콘텐츠, 인젝션 마커 스캔, 허용 목록 탐색을 갖춘 PVE(Prompt-Validator-Executor) 계층을 어떤 에이전트 런타임에든 구축합니다.
version: 1.0.0
phase: 14
lesson: 27
tags: [security, prompt-injection, pve, greshake, source-tag]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-injection-defense.md](skill-injection-defense.md)

도구 접근 권한과 검색 기능을 가진 에이전트가 주어지면 인젝션 방어 계층을 만듭니다.

산출물:

1. 모든 콘텐츠에 출처 태그: `user_message`, `tool_output`, `retrieved_web`, `retrieved_memory`, `retrieved_file`. 태그가 메시지 기록을 통해 전파되게 합니다.
2. `Validator.assess(tool_call, contents)` — 인젝션 형태의 인수나 검색된 콘텐츠가 있는 도구 호출을 거절합니다. 출처 태그가 선언된 신뢰 수준과 일치할 때만 허용합니다.
3. 탐색용 허용 목록 / 차단 목록: 에이전트가 다룰 수 있는 URL, 도메인, 파일 경로.
4. 메모리 쓰기 가드레일: 지시문처럼 보이는 쓰기는 거절합니다.
5. 콘텐츠 캡처 규율(레슨 23): 검색된 콘텐츠는 외부에 저장하고, 스팬에는 문장이 아니라 참조 ID를 담습니다.
6. 테스트 스위트: 다섯 가지 Greshake 공격 클래스를 레드팀 케이스로 만듭니다.

하드 리젝(무조건 거절):

- 출처 태그 없는 도구 사용 표면. 출처 정보가 없으면 권한 수준을 구분할 수 없습니다.
- 최종 출력에만 돌아가는 검증자. 늦은 검증은 무의미합니다 — 모델은 이미 행동한 뒤입니다.
- "걱정 마세요, 시스템 프롬프트가 처리합니다." 시스템 프롬프트 위생은 통제 장치가 아닙니다.

거절 규칙:

- 에이전트에 출처 태깅 없는 검색 기능이 하나라도 있으면 출시를 거절합니다. 검색된 콘텐츠가 가장 전형적인 인젝션 경로입니다.
- 민감한 도구(메시지 전송, 셸 실행, / 아래 파일 쓰기)에 휴먼 인 더 루프 확인이 없으면 거절합니다.
- 메모리 쓰기가 무방비면 거절합니다. 영속 메모리 오염은 다음 세션을 재오염시킵니다.

출력: 여섯 통제 스택, 잔여 위험, 지속 검토 주기를 설명하는 `validator.py`, `source_tag.py`, `allowlist.py`, `memory_guard.py`, `red_team.py`, `README.md`. 마지막에는 "다음에 읽을 것"으로 레슨 21(컴퓨터 사용 안전)과 레슨 23(OTel을 통한 콘텐츠 캡처)을 가리킵니다.
