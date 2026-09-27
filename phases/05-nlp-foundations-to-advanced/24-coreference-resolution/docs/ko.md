# 상호 참조 해소 (Coreference Resolution)

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> "그녀는 그에게 전화했다. 그는 받지 않았다. 의사는 점심을 먹는 중이었다." 두 사람을 가리키는 표현이 세 개인데 아무도 이름이 없습니다. 상호 참조 해소(coreference resolution)가 누가 누구인지 밝혀 줍니다.

**유형:** Learn
**사용 언어:** Python
**선수 지식:** 페이즈 5 · 06(NER), 페이즈 5 · 07(POS & 구문 분석)
**소요 시간:** 약 60분

## 문제 상황

300단어짜리 기사에서 Apple Inc.가 나온 부분을 전부 추출해 봅시다. 기사가 "Apple"이라고 쓰면 쉽습니다. 하지만 "그 회사", "그들", "쿠퍼티노의 기술 거인", "잡스의 회사"라고 쓰면 어렵습니다. 이 멘션(mention)들을 같은 개체로 묶어 주지 못하면 NER 파이프라인은 멘션의 60~80%를 놓쳐 버립니다.

상호 참조 해소는 같은 실세계 개체를 가리키는 모든 표현을 하나의 클러스터로 연결합니다. 표면 수준의 NLP(NER, 구문 분석)와 하위 의미 처리(정보 추출, QA, 요약, 지식 그래프)를 잇는 접착제입니다.

2026년에 왜 중요한가:

- 요약: "CEO는 발표했다..." vs "팀 쿡은 발표했다..." — 요약문에는 CEO의 실제 이름이 나와야 합니다.
- 질의응답: "그녀는 누구에게 전화했어?"는 "그녀"가 누구인지 풀어 내야 합니다.
- 정보 추출: "PER1이 Apple을 설립했다"와 "잡스가 Apple을 설립했다"가 별개 항목인 지식 그래프는 틀린 그래프입니다.
- 다중 문서 정보 추출: 같은 사건을 다룬 기사들에 걸친 멘션 병합은 교차 문서 상호 참조(cross-document coreference) 문제입니다.

## 개념

![상호 참조 클러스터링: 멘션 → 개체](../assets/coref.svg)

**과제 정의.** 입력: 문서 하나. 출력: 각 클러스터가 하나의 개체를 가리키는 멘션(span) 클러스터링.

**멘션 유형.**

- **고유명사 개체.** "Tim Cook"
- **일반명사.** "the CEO", "the company"
- **대명사.** "he", "she", "they", "it"
- **동격어.** "Tim Cook, Apple's CEO,"

**아키텍처.**

1. **규칙 기반(Hobbs, 1978).** 문법 규칙으로 구문 트리를 따라 대명사를 해석합니다. 훌륭한 베이스라인입니다. 대명사 처리에서는 의외로 이기기 어렵습니다.
2. **멘션 쌍 분류기.** 모든 멘션 쌍 (m_i, m_j)에 대해 상호 참조하는지 예측합니다. 추이적 폐쇄(transitive closure)로 클러스터를 만듭니다. 2016년 이전의 표준 방식.
3. **멘션 랭킹.** 각 멘션마다 후보 선행사(antecedent, "선행사 없음" 포함)의 순위를 매기고 1위를 고릅니다.
4. **Span 기반 엔드투엔드(Lee et al., 2017).** 트랜스포머 인코더. 길이 상한까지 모든 후보 span을 나열하고, 멘션 점수를 예측하고, 각 span의 선행사 확률을 예측한 뒤, 탐욕적으로 클러스터를 만듭니다. 현대의 기본값.
5. **생성형(2024+).** LLM에 프롬프트를 줍니다: "이 텍스트의 모든 대명사와 그 선행사를 나열해." 쉬운 사례는 잘 처리하지만, 긴 문서와 희귀 지시 대상에는 약합니다.

**평가 지표.** 표준 지표 다섯 개(MUC, B³, CEAF, BLANC, LEA)가 있는 이유는 하나의 지표로는 클러스터링 품질을 다 담을 수 없기 때문입니다. 앞의 세 지표 평균을 CoNLL F1로 보고합니다. 2026년 CoNLL-2012 최고 수준: 약 83 F1.

**알려진 어려운 사례.**

- 여러 페이지 앞에서 소개된 개체를 가리키는 정관사 정의구.
- 가교(anaphora, "the wheels" → 앞서 언급된 자동차).
- 중국어·일본어 같은 언어의 무시어(zero anaphora, 생략된 주어).
- 후행 지시(cataphora, 대명사가 지시 대상보다 먼저 나옴): "When **she** walked in, Mary smiled."

```figure
coref-links
```

## 직접 만들기

### 단계 1: 사전 학습된 신경망 상호 참조(AllenNLP / spaCy-experimental)

```python
import spacy
nlp = spacy.load("en_coreference_web_trf")   # 실험 단계 모델
doc = nlp("Apple announced new products. The company said they would ship soon.")
for cluster in doc._.coref_clusters:
    print(cluster, "->", [m.text for m in cluster])
```

더 긴 문서에서는 대략 이런 결과를 얻습니다:
- 클러스터 1: [Apple, The company, they]
- 클러스터 2: [new products]

### 단계 2: 규칙 기반 대명사 해석기(학습용)

`code/main.py`에 표준 라이브러리만으로 구현한 코드가 있습니다:

1. 멘션 추출: 고유명사 개체(대문자로 시작하는 span), 대명사(사전 조회), 정관사 정의구("the X").
2. 각 대명사에 대해 앞의 K개 멘션을 보고 다음 기준으로 점수를 매깁니다:
   - 성별/수 일치(휴리스틱)
   - 근접성(가까울수록 유리)
   - 통사적 역할(주어가 유리)
3. 가장 점수가 높은 선행사를 연결합니다.

신경망 모델과 경쟁할 수준은 아닙니다. 하지만 엔드투엔드 모델이 반드시 내려야 하는 결정들과 탐색 공간을 보여 줍니다.

### 단계 3: LLM으로 상호 참조 처리하기

```python
prompt = f"""Text: {text}

List every pronoun and noun phrase that refers to a person or company.
Cluster them by what they refer to. Output JSON:
[{{"entity": "Apple", "mentions": ["Apple", "the company", "it"]}}, ...]
"""
```

주의할 두 가지 실패 모드가 있습니다. 첫째, LLM은 과도하게 병합합니다("him"과 "her"가 실제로는 다른 두 사람인데 하나로 묶음). 둘째, LLM은 긴 문서에서 멘션을 조용히 누락시킵니다. 항상 span 오프셋 검사로 검증하세요.

### 단계 4: 평가

표준 conll-2012 스크립트는 MUC, B³, CEAF-φ4를 계산해 평균을 보고합니다. 사내 평가를 만든다면 먼저 직접 레이블을 단 테스트셋에서 span 수준 정밀도와 재현율을 측정하고, 그다음 멘션 연결 F1을 추가하세요.

## 흔한 실수

- **싱글턴 폭발.** 일부 시스템은 모든 멘션을 각자 별개 클러스터로 보고합니다. B³는 관대하지만 MUC는 이를 벌줍니다. 항상 세 지표를 모두 확인하세요.
- **긴 컨텍스트 속 대명사.** 2,000토큰이 넘는 문서에서는 성능이 약 15 F1 떨어집니다. 청킹에 신중하세요.
- **성별 가정.** 하드코딩된 성별 규칙은 논바이너리 지시 대상, 조직, 동물에서 깨집니다. 학습된 모델이나 중립적 점수 체계를 사용하세요.
- **긴 문서에서의 LLM 드리프트.** API 호출 한 번으로 50개가 넘는 문단에 걸친 멘션을 안정적으로 클러스터링할 수 없습니다. 슬라이딩 윈도우 + 병합을 사용하세요.

## 활용하기

2026년의 표준 스택:

| 상황 | 선택지 |
|-----------|------|
| 영어, 단일 문서 | `en_coreference_web_trf`(spaCy-experimental) 또는 AllenNLP 신경망 coref |
| 다국어 | OntoNotes 또는 Multilingual CoNLL로 학습한 SpanBERT / XLM-R |
| 교차 문서 사건 coref | 특화 엔드투엔드 모델(2025–26 SOTA) |
| 빠른 LLM 베이스라인 | 구조화 출력 coref 프롬프트를 쓴 GPT-4o / Claude |
| 프로덕션(운영 환경) 대화 시스템 | 규칙 기반 폴백 + 신경망 주력 + 중요 슬롯은 수동 검토 |

2026년에 실제로 출시되는 통합 패턴: 먼저 NER을 돌리고, coref를 돌린 뒤, coref 클러스터를 NER 개체에 병합합니다. 하위 작업은 멘션마다 개체 하나가 아니라 클러스터마다 개체 하나를 보게 됩니다.

## 출시하기

`outputs/skill-coref-picker.md`로 저장하세요:

```markdown
---
name: coref-picker
description: Pick a coreference approach, evaluation plan, and integration strategy.
version: 1.0.0
phase: 5
lesson: 24
tags: [nlp, coref, information-extraction]
---

사용 사례(단일 문서 / 다중 문서, 도메인, 언어)가 주어지면 다음을 출력합니다:

1. 접근 방식. 규칙 기반 / 신경망 span 기반 / LLM 프롬프트 / 하이브리드. 한 문장 근거.
2. 모델. 신경망 방식이라면 체크포인트 이름을 명시.
3. 통합. 처리 순서: 토큰화(tokenize) → NER → 상호 참조 해소(coref) → 하위 작업.
4. 평가. 홀드아웃 셋에서 CoNLL F1 (MUC + B³ + CEAF-φ4 평균) + 문서 20개 수동 클러스터 검토.

슬라이딩 윈도우 병합 없이 2,000토큰을 넘는 문서에 LLM 전용 coref를 쓰는 것은 거부합니다. 멘션(mention) 수준 정밀도-재현율 보고서 없이 coref를 돌리는 파이프라인은 거부합니다. 인구 통계적으로 다양한 텍스트에 배포되는 성별 휴리스틱 시스템은 경고를 표시합니다.
```

## 연습 문제

1. **쉬움.** `code/main.py`의 규칙 기반 해석기를 직접 만든 문단 5개에 실행해 보세요. 정답 대비 멘션 연결 정확도를 측정하세요.
2. **보통.** 뉴스 기사에 사전 학습된 신경망 coref 모델을 적용해 보세요. 결과 클러스터를 여러분의 수동 어노테이션과 비교하세요. 어디에서 실패했나요?
3. **어려움.** coref 강화 NER 파이프라인을 만들어 보세요: NER을 먼저 돌리고 coref 클러스터로 병합합니다. 기사 100개에서 NER 단독 대비 개체 커버리지 개선을 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 의미 | 실제 의미 |
|------|-----------------|-----------------------|
| 멘션(Mention) | 지시 표현 | 개체를 가리키는 텍스트 구간(이름, 대명사, 명사구). |
| 선행사(Antecedent) | "it"이 가리키는 것 | 나중 멘션이 상호 참조하는 앞선 멘션. |
| 클러스터(Cluster) | 한 개체의 멘션들 | 같은 실세계 개체를 가리키는 멘션들의 집합. |
| 전방 지시(Anaphora) | 뒤돌아보는 지시 | 나중 멘션이 앞선 멘션을 가리킴("he" → "John"). |
| 후행 지시(Cataphora) | 앞질러 가리키기 | 앞선 멘션이 나중 멘션을 가리킴("When he arrived, John..."). |
| 가교 지시(Bridging) | 함축적 지시 | "I bought a car. The wheels were bad." (그 차의 바퀴.) |
| CoNLL F1 | 리더보드에 나오는 숫자 | MUC, B³, CEAF-φ4 F1 점수의 평균. |

## 더 읽을거리

- [Jurafsky & Martin, SLP3 Ch. 26 — Coreference Resolution and Entity Linking](https://web.stanford.edu/~jurafsky/slp3/26.pdf) — 표준 교과서 챕터.
- [Lee et al. (2017). End-to-end Neural Coreference Resolution](https://arxiv.org/abs/1707.07045) — span 기반 엔드투엔드.
- [Joshi et al. (2020). SpanBERT](https://arxiv.org/abs/1907.10529) — coref 성능을 끌어올리는 사전 학습.
- [Pradhan et al. (2012). CoNLL-2012 Shared Task](https://aclanthology.org/W12-4501/) — 벤치마크.
- [Hobbs (1978). Resolving Pronoun References](https://www.sciencedirect.com/science/article/pii/0024384178900064) — 규칙 기반의 고전.
