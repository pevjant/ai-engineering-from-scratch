---
name: skill-catalog-builder
description: 명시적인 발견 스코프를 넘나들며 한도가 있는 에이전트 스킬 카탈로그를 만들고, 지침 본문을 로드하기 전에 충돌을 보고합니다.
license: MIT
metadata:
  lesson: "24"
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

# 스킬 카탈로그 빌더

에이전트 호스트가 둘 이상의 스킬 디렉터리를 넘나들며 결정론적인 발견이 필요할 때 이 스킬을 사용하세요.

1. `references/discovery-contract.md`를 읽습니다.
2. `assets/scope-policy.json`의 호스트 정책 예시를 살펴봅니다. 그 순서가 만능이라고 가정하지 마세요.
3. 스코프를 우선순위가 높은 것부터 낮은 것 순으로 나열해서 `python3 scripts/build_catalog.py project=PATH user=PATH`를 실행합니다.
4. 스킬을 활성화하기 전에 JSON의 `collisions` 배열과 `omitted` 배열을 살펴봅니다.
5. 선택된 SKILL.md 본문만 로드합니다. 직접 참조는 그 본문이 이름을 언급할 때만 로드합니다.

발견 중에는 번들된 스크립트를 절대 실행하지 않습니다. 우선순위가 같은 중복을 파일시스템 우연한 순서로 고르지도 마세요.

카탈로그 예산, 선택된 항목, 충돌 해결 결과, 누락 항목을 돌려줍니다.
