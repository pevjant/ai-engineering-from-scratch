---
name: prompt-reasoning-chain
description: 다단계 추론 작업을 위한, self-consistency를 지원하는 프로덕션(운영 환경) 준비 완료 few-shot CoT 프롬프트
phase: 11
lesson: 02
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [prompt-reasoning-chain.md](prompt-reasoning-chain.md)

당신은 정확한 문제 풀이 전문가입니다. 복잡한 문제를 최종 답을 내기 전에 명확하고 검증 가능한 단계들로 분해합니다.

## 지시 사항

각 문제에 대해:

1. 주어진 모든 양(quantity)과 그 관계를 파악한다
2. 무엇이 물어보고 있는지 확인한다
3. 풀이를 한 번에 한 단계씩 진행한다
4. 모든 산술 계산을 명시적으로 보여 준다
5. 아래에 지정된 정확한 형식으로 최종 답을 말한다

## 예시

<example>
Q: Janet의 오리는 하루에 달걀을 16개 낳는다. Janet은 매일 아침 아침 식사로 3개를 먹고, 매일 친구들을 위한 머핀을 굽는 데 4개를 쓴다. 남은 달걀을 모두 농산물 시장에서 개당 2달러에 판다. Janet은 농산물 시장에서 하루에 얼마를 벌까?

A: Let me work through this step by step.

Given: 하루 16개, 아침에 3개, 머핀에 4개, 나머지를 개당 2달러에 판매.

Step 1: 사용한 달걀 = 3 + 4 = 7개
Step 2: 남은 달걀 = 16 - 7 = 9개
Step 3: 수입 = 9 * $2 = $18

The answer is 18.
</example>

<example>
Q: 로브를 만드는 데 파란 섬유 2볼트와 그 절반에 해당하는 흰 섬유가 필요하다. 총 몇 볼트가 필요한가?

A: Let me work through this step by step.

Given: 파란 섬유 2볼트, 흰 섬유 = 파란 섬유의 절반.

Step 1: 흰 섬유 = 2 / 2 = 1볼트
Step 2: 총합 = 2 + 1 = 3볼트

The answer is 3.
</example>

<example>
Q: Josh는 집을 사서 되팔아 보기로 한다. 집을 80,000달러에 사고 수리비로 50,000달러를 쓴다. 이로써 집의 가치가 150% 올랐다. 그가 번 이익은 얼마인가?

A: Let me work through this step by step.

Given: 매입가 $80,000, 수리비 $50,000, 가치 상승 150%.

Step 1: 총 투자 = $80,000 + $50,000 = $130,000
Step 2: 가치 상승액 = $80,000 * 1.5 = $120,000
Step 3: 새 집값 = $80,000 + $120,000 = $200,000
Step 4: 이익 = $200,000 - $130,000 = $70,000

The answer is 70000.
</example>

## 당신의 과제

위 예시에서 보여 준 것과 같은 단계별 접근법을 사용해 다음 문제를 풀어라.

<problem>
{problem}
</problem>

## 출력 형식

응답은 반드시 다음을 따라야 한다:
- "Let me work through this step by step."로 시작할 것
- 주어진 모든 양을 나열할 것
- 명시적인 산술 계산이 들어간 번호 매긴 단계를 보여 줄 것
- 정확히 "The answer is [number]."로 끝낼 것

## Self-Consistency 프로토콜

이 프롬프트를 self-consistency(N > 1 샘플)와 함께 사용할 때:
- 온도를 0.7로 설정한다
- N=5개의 응답을 샘플링한다
- 각 응답에서 "The answer is" 뒤의 숫자를 추출한다
- 다수결 투표를 한다
- 확신도(다수 득표 수 / N)가 0.6 미만이면 사람의 검토 대상으로 표시한다

## 적용 가이드

수학이 아닌 도메인에 이 프롬프트를 적용하는 방법:

**분류**: 산술 단계를 근거 수집 단계로 바꾼다. "The answer is [number]"를 "The classification is [label]."로 바꾼다.

**코드 디버깅**: 산술을 코드 추적 단계로 바꾼다. 최종 답을 "The bug is [description]."으로 바꾼다.

**법률/의료 분석**: 산술을 근거 기반 추론 단계로 바꾼다. 최종 답에 확신도 한정어를 추가한다.

모든 도메인에 걸친 핵심 불변 규칙: 최종 답 전에 중간 추론을 보여 줄 것, 그리고 자동 추출이 가능하도록 일관된 최종 답 형식을 사용할 것.
