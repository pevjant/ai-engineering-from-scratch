> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 프론티어 안전 프레임워크 — RSP, PF, FSF

> 세 대형 연구실의 프레임워크가 2026년 프론티어 능력의 업계 거버넌스를 정의합니다. Anthropic의 책임 있는 확장 정책(Responsible Scaling Policy) v3.0(2026년 2월)은 생물 안전 등급을 본떠 단계별 AI 안전 레벨(AI Safety Levels, ASL-1부터 ASL-5+)을 도입했으며, ASL-3는 2025년 5월에 CBRN(화학·생물·방사선·핵) 관련 모델을 위해 활성화되었습니다. OpenAI의 Preparedness Framework v2(2025년 4월)는 추적 대상 능력을 가리는 다섯 가지 기준을 정의하고 Capabilities Report(능력 보고서)와 Safeguards Report(안전장치 보고서)를 분리했습니다. DeepMind의 Frontier Safety Framework v3.0(2025년 9월)은 위험 능력 레벨(Critical Capability Levels)을 도입했고, 여기에 새로운 유해한 조작(Harmful Manipulation) CCL이 포함됩니다. 이제 세 프레임워크 모두 경쟁사 조정 조항을 포함합니다. 즉, 경쟁 연구실이 비슷한 안전장치 없이 출시하면 요구 사항 적용을 미룰 수 있습니다. 연구실 간 정합성은 구조적일 뿐 용어는 아닙니다. "Capability Thresholds", "High Capability thresholds", "Critical Capability Levels"은 서로 비슷한 구조를 가리키는 이름들입니다.

**유형:** Learn
**언어:** 없음
**선수 지식:** 페이즈 18 · 17(WMDP), 페이즈 18 · 07-09(기만 실패 사례)
**시간:** 약 75분

## 학습 목표

- Anthropic의 ASL 등급 구조와 ASL-3를 활성화시킨 계기가 무엇인지 설명할 수 있습니다.
- OpenAI Preparedness Framework v2의 추적 대상 능력 다섯 가지 기준을 말할 수 있습니다.
- DeepMind의 위험 능력 레벨(CCL) 구조와 유해한 조작(Harmful Manipulation) CCL을 설명할 수 있습니다.
- 경쟁사 조정 조항이 무엇이고, 왜 경쟁 구도에서 중요한지 설명할 수 있습니다.
- 안전 사례(safety case)를 정의하고 세 기둥 구조(모니터링, 해독 불가능성, 무능력화)를 설명할 수 있습니다.

## 해결할 문제

레슨 7-17은 기만(deception)이 가능하다는 점, 이중 사용 능력이 존재한다는 점, 그리고 평가에는 한계가 있다는 점을 확인했습니다. 프론티어급 모델을 가진 연구실에는 다음을 담당할 내부 거버넌스 구조가 필요합니다:
- 새로운 안전장치가 언제 필요해지는지 임계값을 정의합니다.
- 확장(scaling) 전에 어떤 평가가 필요한지 정의합니다.
- 안전 사례가 어떤 모습인지 기술합니다.
- 경쟁 구도의 문제를 다룹니다 (경쟁사가 안전장치 없이 출시하면 어떻게 할 것인가?).

2025-2026년의 세 프레임워크가 그 최전선입니다. 불완전하고, 계속 진화하고 있으며, 연구실 간 충분히 정렬되어 있어서 이제 거버넌스 질문은 "프레임워크가 존재하는가"가 아니라 "프레임워크가 충분한가"입니다.

## 핵심 개념

### Anthropic 책임 있는 확장 정책 v3.0 (2026년 2월)

ASL 구조:
- ASL-1: 프론티어 모델이 아님 (프론티어 미달 베이스라인에 흡수됨).
- ASL-2: 현재 프론티어 베이스라인. 평상시의 안전장치와 함께 배포됨.
- ASL-3: 치명적 오남용 위험이 실질적으로 높음. CBRN 관련 능력. 2025년 5월 활성화.
- ASL-4: AI R&D-2 임계값 초과. 초급 AI 연구를 자동화할 수 있는 모델.
- ASL-5+: 고급 AI R&D. 실효적인 확장을 극적으로 가속하는 모델.

v3.0에서 새로워진 것:
- 프론티어 안전 로드맵(Frontier Safety Roadmaps, 일부 가려진 형태로 공개).
- 리스크 보고서(Risk Reports, 분기별, 일부는 외부 검토).
- AI R&D가 AI R&D-2와 AI R&D-4로 세분화됨.
- AI R&D-4를 넘으면 긍정적 안전 사례(affirmative safety case)가 필요해짐. 정렬되지 않은 목표를 추구하는 모델에서 오는 정렬 실패 위험을 명시해야 합니다.

### OpenAI Preparedness Framework v2 (2025년 4월 15일)

추적 대상 능력을 가리는 다섯 가지 기준:
- **Plausible(개연성).** 합리적인 위협 모델이 존재한다.
- **Measurable(측정 가능성).** 실증적 평가가 가능하다.
- **Severe(심각성).** 피해가 크다.
- **Net-new(새로운 위험).** 이미 있던 위험이 커진 것이 아니다.
- **Instantaneous-or-irremediable(즉발이거나 되돌릴 수 없음).** 피해가 빠르게 발생하거나 되돌릴 수 없다.

다섯 기준을 모두 만족하는 능력은 추적 대상이 됩니다. 나머지는 추적하지 않습니다.

PF v2의 다른 구조:
- Capabilities Report(모델이 무엇을 할 수 있는가)와 Safeguards Report(어떤 통제 장치가 있는가)를 분리합니다.
- 안전 자문 그룹(Safety Advisory Group) 검토가 있습니다.
- 리더십이 승인하고, 이사회의 안전·보안 위원회가 감독합니다.
- "조정 조항(adjustment clause)": 다른 연구실이 비슷한 수준의 안전장치 없이 출시하면 OpenAI도 요구 사항을 낮출 수 있습니다.

### DeepMind Frontier Safety Framework v3.0 (2025년 9월)

도메인별 위험 능력 레벨(CCL):
- 생물무기 Uplift(Bioweapon Uplift)
- 사이버 Uplift(Cyber Uplift)
- ML R&D 가속(ML R&D Acceleration)
- 유해한 조작(Harmful Manipulation, v3.0에서 신설): 고위험 상황에서 신념/행동을 실질적으로 바꿀 수 있는 모델.

v2.0(2025년 2월)에서는 기만적 정렬(Deceptive Alignment) 섹션이 추가되고 ML R&D CCL의 보안 레벨이 높아졌습니다.

### 연구실 간 정합성

- Anthropic "Capability Thresholds(능력 임계값)".
- DeepMind "Critical Capability Levels(위험 능력 레벨)".
- OpenAI "High Capability thresholds(높은 능력 임계값)".

업계 표준 용어는 없습니다. 다만 구조적으로는 정렬되어 있습니다. 공개된 평가 기준을 갖춘 프론티어 능력의 세 단계 구조입니다. 세 프레임워크 모두 경쟁사 조정 조항을 포함합니다(2025년 이후).

### 안전 사례(safety case)

안전 사례는 "최악의 가정 하에서도 이 배포는 수용 가능하게 안전하다"는 서면 논증입니다. 표준 구조는 세 기둥을 노립니다:

- **모니터링(Monitoring).** 나쁜 행동이 발생하면 탐지할 수 있는가?
- **해독 불가능성(Illegibility).** 모델에게 피해를 일으킬 일관된 계획을 실행할 능력이 없는가?
- **무능력화(Incapability).** 모델에게 문제가 되는 피해를 일으킬 능력 자체가 없는가?

안전 사례마다 노리는 기둥이 다릅니다. ASL-3 CBRN 사례는 무능력화(언러닝을 통한)가 주된 목표입니다. 기만적 정렬에는 모니터링과 해독 불가능성이 목표입니다. 사이버 uplift에는 셋 모두 관련됩니다.

### 경쟁 구도의 문제

경쟁사 조정 조항은 논란이 있습니다. 비판자들은 이것이 바닥을 향한 경쟁(race to the bottom)을 만든다고 주장합니다. 세 연구실 모두 경쟁사가 배신하면 요구를 낮출 것이라면, 균형점은 배신 쪽으로 기웁니다. 옹호자들은 대안(일방적 안전장치)이 경쟁사가 안전 의식이 덜한 연구실일 때 더 나쁜 결과를 낸다고 반박합니다.

영국 AISI, 미국 CAISI, EU AI Office(레슨 24)가 외부 거버넌스 대응 조직입니다. 연구실 프레임워크는 자율적인 것이고, 규제 프레임워크는 이제 막 만들어지고 있습니다.

### 페이즈 18에서의 위치

레슨 17-18은 기만·레드팀 분석 위에 얹히는 측정-거버넌스 계층입니다. 레슨 19-24는 모델 복지, 편향, 프라이버시, 워터마킹, 규제 구조를 다룹니다. 레슨 28은 이 평가들을 실제로 수행하는 연구 생태계(MATS, Redwood, Apollo, METR)를 지도로 보여 줍니다.

```figure
al-asl-ladder
```

## 사용해 보기

이 레슨은 코드가 없습니다. 원문 자료 세 가지(RSP v3.0, PF v2, FSF v3.0)를 직접 읽습니다. 각 연구실의 등급 구조를 서로 대응시켜 보고, 한 연구실만 정의하고 나머지는 정의하지 않는 임계값을 하나 찾아 봅니다.

## 출시하기

이 레슨은 `outputs/skill-framework-diff.md`를 산출물로 만듭니다. 안전 프레임워크나 릴리스 노트가 주어지면, 그 임계값 정의, 요구 평가, 안전 사례 구조를 RSP v3.0, PF v2, FSF v3.0과 비교하고 연구실 간 격차를 표시합니다.

## 연습 문제

1. RSP v3.0, PF v2, FSF v3.0을 읽습니다. 각 연구실의 CBRN 임계값, AI R&D 임계값, 배포 전 필수 평가를 한 표로 정리합니다.

2. 경쟁사 조정 조항은 세 프레임워크 모두에 있습니다(2025년 이후). 찬성 논거를 한 단락, 반대 논거를 한 단락 씁니다. 각 입장이 의존하는 전제를 짚습니다.

3. Anthropic의 AI R&D-4 임계값을 넘는 모델을 위한 안전 사례를 설계합니다. 세 기둥(모니터링, 해독 불가능성, 무능력화) 각각이 요구하는 증거를 말합니다.

4. DeepMind의 FSF v3.0은 유해한 조작(Harmful Manipulation) CCL을 도입했습니다. 모델이 이 임계값을 넘었음을 보여 줄 실증적 측정 세 가지를 제안합니다.

5. METR의 "Common Elements of Frontier AI Safety Policies"(2025)를 읽습니다. 가장 강한 연구실 간 수렴 세 가지와 가장 큰 분기 두 가지를 말합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|---------------------|-----------|
| RSP | "Anthropic의 프레임워크" | Responsible Scaling Policy. ASL 등급. 2026년 2월 v3.0 |
| PF | "OpenAI의 프레임워크" | Preparedness Framework. 다섯 기준. 2025년 4월 v2 |
| FSF | "DeepMind의 프레임워크" | Frontier Safety Framework. CCL. 2025년 9월 v3.0 |
| ASL-3 | "생물안전 3등급에 대응하는 등급" | Anthropic의 CBRN 관련 능력용 등급. 2025년 5월 활성화 |
| CCL | "위험 능력 레벨" | DeepMind의 임계값 구조. 도메인별 |
| 안전 사례 | "그 형식적 논증" | 최악의 상황을 가정해도 배포가 수용 가능하게 안전하다는 서면 논증 |
| 조정 조항 | "경쟁사 배신 허용 조항" | 경쟁사가 비슷한 안전장치 없이 출시하면 요구 사항을 낮출 수 있게 하는 규정 |

## 더 읽을거리

- [Anthropic — Responsible Scaling Policy v3.0 (2026년 2월)](https://www.anthropic.com/responsible-scaling-policy) — ASL 등급, 로드맵, AI R&D 세분화
- [OpenAI — Updating the Preparedness Framework (2025년 4월 15일)](https://openai.com/index/updating-our-preparedness-framework/) — 다섯 기준, 조정 조항
- [DeepMind — Strengthening our Frontier Safety Framework (2025년 9월)](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — CCL v3.0, Harmful Manipulation
- [METR — Common Elements of Frontier AI Safety Policies (2025)](https://metr.org/blog/2025-03-26-common-elements-of-frontier-ai-safety-policies/) — 연구실 간 비교
