---
name: skill-invocation-router
description: 에이전트 스킬 카탈로그를 위해 명시적 사람, 암시적 모델·에이전트, 프로그래밍 방식 애플리케이션, 한정된 스킬 조합, 하네스 활성화 정책을 설계하고 테스트합니다.
license: MIT
metadata:
  lesson: "25"
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

# 스킬 호출 라우터

호스트가 하나의 획일적인 `invocable` 플래그가 아니라 감사 가능한 활성화 정책이 필요할 때 이 스킬을 사용하세요.

1. `references/invocation-model.md`를 읽고 요청된 통로를 분류합니다.
2. `assets/host-policy.json`을 이식 가능한 표준이 아니라 어댑터 설정 예시로 살펴봅니다.
3. `python3 scripts/simulate_invocation.py --policy assets/host-policy.json --actor ACTOR --name NAME --description DESCRIPTION --query QUERY [--explicit-name NAME] [--caller-name NAME] [--depth N] [--user-invocable true|false] [--disable-model-invocation true|false]`를 실행합니다.
4. 사람, 애플리케이션, 스킬, 하네스 요청에는 정확히 발견된 이름과 그 통로 전용 허용 목록을 요구합니다.
5. 스킬 호출자에게는 호출자 신원, 순환 없는 대상, 한정된 조합 깊이도 요구합니다.
6. 모델이나 자율 에이전트 요청에는 행위자 또는 인식된 호스트 확장이 자격을 잃게 만드는 후보를 제거합니다.
7. 남은 description에만 점수를 매깁니다. 가장 강한 자격 매치를 선택하거나, 임계값을 넘는 자격 후보가 없으면 기권합니다.
8. 어댑터, 통로, 점수, 정책 이유가 담긴 JSON 결정을 돌려줍니다.

활성화는 지침을 로드할 뿐입니다. 도구, 파일시스템 변경, 네트워크 접근, 시크릿 사용, 번들 스크립트를 승인하지 않습니다.
