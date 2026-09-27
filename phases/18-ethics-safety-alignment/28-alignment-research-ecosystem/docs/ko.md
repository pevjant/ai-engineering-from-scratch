> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 정렬(alignment) 연구 생태계 — MATS, Redwood, Apollo, METR

> 다섯 조직이 2026년 비연구실(non-lab) 정렬 연구 계층을 정의합니다. MATS(ML Alignment & Theory Scholars): 2021년 말 이후 527명 이상의 연구자, 180편 이상의 논문, 1만 회 이상의 인용, h지수 47. 2024년 여름 기수는 약 90명의 학자와 40명의 멘토로 501(c)(3) 법인으로 통합되었습니다. 2025년 이전 동문의 80%가 안전/보안 분야에서 일하며, 200명 이상이 Anthropic, DeepMind, OpenAI, 영국 AISI, RAND, Redwood, METR, Apollo에 있습니다. Redwood Research: Buck Shlegeris가 창립한 응용 정렬 연구실. AI Control을 도입했습니다(레슨 10). 영국 AISI와 통제(control) 안전 사례에서 협력합니다. Apollo Research: 프론티어 연구실을 위한 배포 전 음모(scheming) 평가. In-Context Scheming(레슨 8)과 Towards Safety Cases for AI Scheming을 집필했습니다. METR(Model Evaluation and Threat Research): 과제 기반 능력 평가, 자율 과제 수행 시간 지평(time-horizon) 연구. "Common Elements of Frontier AI Safety Policies"로 연구실 프레임워크들을 비교합니다. Eleos AI Research: 모델 복지 배포 전 평가(레슨 19). Claude Opus 4 복지 평가를 수행했습니다.

**유형:** Learn
**언어:** 없음
**선수 지식:** 페이즈 18 · 01-27(페이즈 18의 이전 레슨들)
**시간:** 약 45분

## 학습 목표

- 비연구실 정렬 연구 생태계의 다섯 조직과 각자의 핵심 산출물을 식별할 수 있습니다.
- MATS의 규모(학자 수, 논문 수, h지수)와 인재 파이프라인으로서의 역할을 설명할 수 있습니다.
- Redwood의 AI Control 어젠다와 영국 AISI와의 파트너십을 설명할 수 있습니다.
- METR의 과제 기반 평가 방법론을 설명할 수 있습니다.

## 해결할 문제

프론티어 연구실(레슨 18)은 안전 평가를 내부에서 수행하고 선별된 결과만 공개합니다. 연구실 밖의 생태계는 평가가 검증되는 곳이고, 새로운 실패 모드가 처음 발견되는 곳이며, 인재가 양성되는 곳입니다. 생태계를 이해하면 어떤 연구 결과를 누가 신뢰하는지 해석하는 데 도움이 됩니다.

## 핵심 개념

### MATS (ML Alignment & Theory Scholars)

2021년 말 시작. 연구 멘토십 프로그램으로, 학자(scholar)가 선임 연구자와 함께 10-12주 동안 특정 정렬 문제를 연구합니다.

규모(2026):
- 창설 이후 527명 이상의 연구자.
- 180편 이상의 논문 게재.
- 1만 회 이상의 인용.
- h지수 47.
- 2024년 여름: 학자 90명 + 멘토 40명. 501(c)(3) 법인으로 통합.

커리어 결과: 2025년 이전 동문의 약 80%가 안전/보안 분야에서 일하고 있습니다. 200명 이상이 Anthropic, DeepMind, OpenAI, 영국 AISI, RAND, Redwood, METR, Apollo에 있습니다.

### Redwood Research

응용 정렬 연구실입니다. Buck Shlegeris가 창립했습니다. AI Control 어젠다를 도입했습니다(레슨 10). 영국 AISI와 통제 안전 사례에서 협력하고, DeepMind와 Anthropic에 평가 설계를 자문합니다.

대표 논문: Greenblatt, Shlegeris 등, "AI Control"(arXiv:2312.06942, ICML 2024). Alignment Faking(Greenblatt, Denison, Wright 등, arXiv:2412.14093, Anthropic과 공동).

스타일: 구체적인 위협 모델, 최악의 적대자, 스트레스 테스트 가능한 구체적 프로토콜.

### Apollo Research

프론티어 연구실을 위한 배포 전 음모(scheming) 평가입니다. In-Context Scheming(레슨 8, arXiv:2412.04984)을 집필했고, 2025년 OpenAI의 반(反)음모 학습 협업 파트너입니다. Towards Safety Cases for AI Scheming(2024)을 만들어 냈습니다.

스타일: 기만이 생겨날 수 있는 에이전트 설정 평가. 세 기둥 분해(정렬 실패, 목표 지향성, 상황 인식).

### METR (Model Evaluation and Threat Research)

과제 기반 능력 평가입니다. 자율 과제 완수의 시간 지평 연구를 합니다. "Common Elements of Frontier AI Safety Policies"(metr.org/common-elements, 2025)로 연구실 프레임워크들을 비교합니다.

Apollo와 함께 AI Scheming 안전 사례 스케치의 공동 저자입니다.

스타일: 긴 지평의 과제 평가, 실증적 능력 측정, 프레임워크 종합.

### Eleos AI Research

모델 복지 배포 전 평가 기관입니다. 시스템 카드 5.3절에 문서화된 Claude Opus 4 복지 평가를 수행했습니다. 레슨 19의 복지 관련 주장에 대한 외부 방법론 점검 역할을 합니다.

### 흐름

MATS가 연구자를 양성합니다. 졸업생들은 Anthropic, DeepMind, OpenAI(연구실 안전 팀)이나 Redwood, Apollo, METR, Eleos(외부 평가)로 흘러갑니다. 외부 평가자들은 연구실 및 영국 AISI / CAISI와 파트너가 됩니다. 논문 발표는 생태계를 다시 MATS로 되돌려 다음 기수를 먹입니다.

### 이 계층이 중요한 이유

단일 출처 평가는 신뢰하기 어렵습니다. 자기 모델을 평가하는 연구실에는 구조적 이해 상충이 있습니다. 외부 평가자는 연구실이 과소 보고할 수 있는 실패 모드를 제기하고 검증할 수 있습니다. 2024년 Sleeper Agents 논문(레슨 7)은 Anthropic + Redwood였고, Alignment Faking은 Anthropic + Redwood였고, In-Context Scheming은 Apollo였으며, Anti-Scheming은 Apollo + OpenAI였습니다. 다중 조직 구조가 바로 품질 관리입니다.

### 페이즈 18에서의 위치

레슨 7-11은 Redwood와 Apollo의 작업을 인용합니다. 레슨 18은 METR의 프레임워크 비교를 인용하고, 레슨 19는 Eleos를 인용합니다. 레슨 28은 페이즈 나머지가 의존하는 생태계의 명시적인 조직 지도입니다.

```figure
sae-features
```

## 사용해 보기

코드는 없습니다. METR의 "Common Elements of Frontier AI Safety Policies"를, 외부 종합이 연구실 내부 정책 작업에 어떻게 가치를 더하는지 보여 주는 예로 읽습니다.

## 출시하기

이 레슨은 `outputs/skill-ecosystem-map.md`를 산출물로 만듭니다. 정렬 주장이나 평가가 주어지면 조직, 게재처, 방법론적 스타일을 식별하고 알려진 대응 조직과 교차 점검합니다.

## 연습 문제

1. 레슨 7-15에서 논문 하나를 골라 관련 조직을 식별합니다. 저자들을 MATS 동문 및 현재 생태계 소속과 교차 점검합니다.

2. METR의 "Common Elements of Frontier AI Safety Policies"를 읽습니다. 그들이 강조하는 세 가지 연구실 간 수렴과 가장 큰 두 가지 분기를 찾습니다.

3. MATS의 커리어 결과는 약 80%가 안전/보안입니다. 이 선택 압박이 적응적인가(분야를 양성한다) 편향인가(이단적 입장을 걸러낸다)를 논증합니다.

4. Redwood와 Apollo는 둘 다 통제/음모 연구를 하지만 스타일이 다릅니다. 실패 모드 하나를 골라 각 조직이 어떻게 조사할지 기술합니다.

5. Eleos AI는 유일한 순수 모델 복지 조직입니다. 다른 복지 인접 질문(인지적 자유, 로봇 신체화 등)에 초점을 둔 가상의 두 번째 조직을 설계하고 그 방법론을 진술합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|---------------------|-----------|
| MATS | "그 멘토십 프로그램" | ML Alignment & Theory Scholars. 2021년 이후 527명 이상의 연구자 |
| Redwood Research | "그 통제 연구실" | 응용 정렬. AI Control 저자. 영국 AISI 파트너 |
| Apollo Research | "음모 평가 기관" | 프론티어 연구실을 위한 배포 전 음모(scheming) 평가 |
| METR | "과제 지평 평가 기관" | 과제 기반 능력 평가. 프레임워크 종합 |
| Eleos AI | "복지 연구실" | 모델 복지 배포 전 평가 |
| 인재 파이프라인 | "MATS → 연구실" | MATS 졸업생이 Anthropic, DM, OpenAI, Redwood, Apollo, METR로 흐름 |
| 외부 평가 | "비연구실 점검" | 모델 제작자가 아닌 주체의 평가. 신뢰도를 더함 |

## 더 읽을거리

- [MATS (ML Alignment & Theory Scholars)](https://www.matsprogram.org/) — 그 멘토십 프로그램
- [Redwood Research](https://www.redwoodresearch.org/) — AI Control 논문들
- [Apollo Research](https://www.apolloresearch.ai/) — 음모(scheming) 평가
- [METR — Common Elements of Frontier AI Safety Policies](https://metr.org/blog/2025-03-26-common-elements-of-frontier-ai-safety-policies/) — 프레임워크 비교
- [Eleos AI Research](https://www.eleosai.org/research) — 모델 복지 방법론
