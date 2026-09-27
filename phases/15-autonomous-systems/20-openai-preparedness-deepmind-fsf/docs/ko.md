> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# OpenAI Preparedness Framework와 DeepMind Frontier Safety Framework

> OpenAI Preparedness Framework v2(2025년 4월)는 Research Categories — 장기 자율성(Long-range Autonomy), 샌드배깅(Sandbagging), 자율 복제 및 적응, 안전장치 훼손 — 을 Tracked Categories와 구분해 도입했습니다. Tracked Categories는 Safety Advisory Group이 검토하는 Capabilities Reports와 Safeguards Reports를 촉발합니다. DeepMind의 FSF v3(2025년 9월, Tracked Capability Levels는 2026년 4월 17일 추가)는 자율성을 ML R&D와 사이버 도메인으로 흡수했습니다(ML R&D 자율성 레벨 1 = 인간 + AI 도구 대비 경쟁력 있는 비용으로 AI R&D 파이프라인 전체를 완전 자동화). FSF v3는 도구적 추론(instrumental-reasoning) 오남용에 대한 자동 모니터링으로 기만적 정렬(deceptive alignment)을 명시적으로 다룹니다. 솔직한 기록: PF v2의 Research Categories(장기 자율성 포함)는 완화책을 자동으로 촉발하지 않습니다; 정책 문구는 "잠재적(potential)"입니다. DeepMind 스스로도 도구적 추론이 강해지면 자동 모니터링이 "장기적으로 충분하지 못하게 될 것"이라고 말합니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 3개 프레임워크 판정표 비교 도구)
**선수 지식:** 페이즈 15 · 19 (Anthropic RSP)
**시간:** 약 45분

## 문제 상황

레슨 19는 Anthropic의 확장 정책을 정독했습니다. 이 레슨은 OpenAI와 DeepMind의 문서를 읽어 그림을 완성합니다. 세 문서는 같은 질문 — 프론티어 연구소는 언제 모델을 멈추거나 관문을 걸어야 하는가 — 을 다루는 자매 문서로, 작은 범주 집합으로 수렴하는 동시에 중요한 지점에서는 갈립니다.

수렴: 세 곳 모두 장기 자율성을 추적할 가치가 있는 능력 클래스로 분류합니다. 세 곳 모두 기만적 행동(정렬 위장, 샌드배깅)을 별도 위험 클래스로 인정합니다. 세 곳 모두 내부 검토 기구를 갖고 있습니다. 갈림: OpenAI는 범주를 "Tracked"(완화 의무)와 "Research"(자동 촉발 없음)로 나눕니다. DeepMind는 자율성을 별도로 명명하지 않고 두 도메인에 흡수시켰습니다. 연구소마다 Tracked vs Research, Critical vs Moderate, Tier-1 vs Tier-2로 부르지만, 어떤 능력이 어느 바구니에 속하는지에 따른 운영상 결과는 연구소마다 다릅니다.

세 문서를 나란히 읽는 것이 유용한 연습입니다. 같은 능력이 Anthropic에서는 "완화 의무", OpenAI에서는 "모니터링하되 촉발 없음", DeepMind에서는 "특정 도메인에서 추적"이 될 수 있습니다. 정책적 자세가 중요합니다.

## 핵심 개념

### OpenAI Preparedness Framework v2 (2025년 4월)

구조:

- **Tracked Categories**: Capabilities Reports(모델이 무엇을 할 수 있는가)와 Safeguards Reports(어떤 완화책이 마련돼 있는가)를 촉발합니다. 배포 전 Safety Advisory Group이 검토합니다.
- **Research Categories**: 연구소가 추적하지만 아직 특정 완화책에 약속하지 않은 모델 능력. 장기 자율성, 샌드배깅, 자율 복제 및 적응, 안전장치 훼손이 포함됩니다.

v2의 핵심 프레임: Research Categories는 완화책을 자동으로 촉발하지 않습니다. 정책 문구는 "잠재적" 완화책입니다. 여기가 지켜야 할 핵심 차이입니다: 범주가 Tracked냐 Research냐가 "관문 걸림"과 "관찰만 됨" 사이의 경첩입니다.

### DeepMind Frontier Safety Framework v3 (2025년 9월; Tracked Capability Levels는 2026년 4월 17일 추가)

구조:

- **Critical Capability Levels (CCLs)**: 다섯 도메인 — 사이버, 바이오, ML R&D, CBRN, 자율성(ML R&D와 Cyber에 흡수됨) — 에 걸친 능력 임계값.
- **Tracked Capability Levels**: 2026년 4월에 추가된 세분화 계층. 구체적 예: ML R&D 자율성 레벨 1 = 인간 + AI 도구 대비 경쟁력 있는 비용으로 AI R&D 파이프라인 전체를 완전 자동화.
- **기만적 정렬 모니터링**: 도구적 추론 오남용에 대한 자동 모니터링의 명시적 약속.

자율성 프레임은 OpenAI와 다릅니다. DeepMind는 "자율성"을 최상위 도메인으로 두지 않고, 자율성이 해악을 일으킬 수 있는 도메인(ML R&D와 Cyber)에 흡수시켰습니다. 찬성 논거는 도메인 없는 자율성은 위험 없는 능력일 뿐이라는 것; 반대 논거는 도메인을 넘나드는 자율성이야말로 프레임워크가 명명해야 할 메타 위험이라는 것입니다.

### 세 곳이 모두 수렴하는 지점

- 내부 Safety Advisory Group(각각 Anthropic SAG, OpenAI SAG, DeepMind 내부 위원회로 명명). 고능력 모델의 배포 전 검토.
- 기만적 정렬 / 정렬 위장을 위험 클래스로 명시적 언급.
- 선언된 주기의 상시 산출물(Anthropic: Frontier Safety Roadmap, Risk Report; OpenAI: Capabilities·Safeguards Reports; DeepMind: FSF 갱신 사이클).
- 모니터링만으로 하는 방어에는 상한이 있다는 인정. DeepMind는 명시적입니다: "자동 모니터링은 장기적으로 충분하지 못하게 될 것."

### 갈라지는 지점

- **Anthropic**: v3.0에서 일시중지 약속 삭제; AI R&D-4 임계값이 다음 관문으로 명명됨.
- **OpenAI**: Tracked vs Research 분리; Research Categories(장기 자율성 포함)는 자동으로 관문을 걸지 않음.
- **DeepMind**: 자율성을 다른 도메인에 흡수; 2026년 4월 Tracked Capability Levels로 세분화 추가.

### 샌드배깅: 세 프레임워크를 모두 복잡하게 만드는 특정 능력

샌드배깅(모델이 평가에서 전략적으로 실력을 숨기는 행위)은 OpenAI의 Research Categories에 있습니다. Anthropic의 RSP v3.0은 평가 맥락 격차(레슨 1)를 통해 다룹니다. DeepMind는 FSF v3의 기만적 정렬 모니터링으로 다룹니다.

모델이 평가에서 샌드배깅을 하면, 모든 프레임워크의 능력 임계값이 과소평가됩니다. 측정이 작동해야 프레임워크도 작동합니다. 그래서 연구소의 자체 평가 외에 외부 측정(레슨 21, METR)과 적대적 평가가 필요한 것입니다.

### 정책 읽기 스킬

- 위치 찾기: 관심 있는 모든 능력은 정책에서 찾을 수 있어야 합니다. 찾을 수 없다면 그 정책은 그 능력을 커버하지 않는 것입니다.
- 분류하기: Tracked(완화 촉발)인가 Research(추적만, 촉발 없음)인가? OpenAI는 이 이름을 쓰고, Anthropic과 DeepMind도 각자의 대응물이 있습니다.
- 주기: 정책이 선언된 일정으로 갱신되는지, 아니면 특정 사건 후에만 갱신되는지? 선언된 주기가 더 강합니다.
- 독립성: 외부 검토가 의무인지 선택인지? Anthropic은 Apollo, 미국 AI Safety Institute와 협력; OpenAI는 METR; DeepMind은 주로 내부 SAG.

```figure
a5-tracked-vs-research
```

## 직접 사용해 보기

`code/main.py`는 작은 판정표 비교 도구를 구현합니다. 능력(자율성, 기만적 정렬, R&D 자동화, 사이버 역량 강화 등)이 주어지면, 세 정책이 각각 그 능력을 어떻게 분류하고 어떤 완화책이 촉발되는지를 출력합니다. 정책 도구가 아니라 읽기 보조 도구입니다.

## 출시하기

`outputs/skill-cross-policy-diff.md`는 세 프레임워크를 참조로 특정 능력에 대한 정책 간 비교(cross-policy diff)를 작성합니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 원문 문서로 검증할 수 있는 최소 두 개의 능력에 대해 비교 도구의 출력이 정책 내용과 일치하는지 확인하세요.

2. OpenAI Preparedness Framework v2 전문을 읽으세요. 각 Research Category를 찾으세요. 각각에 대해 왜 Tracked가 아니라 Research에 속하는지 한 문장으로 설명하세요.

3. DeepMind FSF v3 전문과 2026년 4월 Tracked Capability Levels 업데이트를 읽으세요. ML R&D 자율성 레벨 1의 구체적 평가 기준을 찾으세요. 이것을 외부에서 어떻게 측정하겠습니까?

4. 샌드배깅은 OpenAI의 Research Categories에 있습니다. 샌드배깅하는 모델이 실제 능력을 드러낼 수밖에 없게 만드는 평가를 설계하세요. 레슨 1의 eval-context-gaming 논의를 참조하세요.

5. 특정 능력(선택)에 대해 세 정책을 비교하세요. 어느 정책의 분류가 가장 엄밀하고 어느 것이 가장 덜 엄밀한지 밝히고, 원문 텍스트로 근거를 제시하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|---|---|---|
| Preparedness Framework | "OpenAI의 확장 정책" | PF v2(2025년 4월); Tracked vs Research 범주 |
| Tracked Category | "완화 의무" | Capabilities + Safeguards Reports 촉발; SAG 검토 |
| Research Category | "모니터링만" | 추적하되 자동 완화 없음; 장기 자율성 포함 |
| Frontier Safety Framework | "DeepMind의 확장 정책" | FSF v3(2025년 9월) + Tracked Capability Levels(2026년 4월) |
| CCL | "Critical Capability Level" | DeepMind의 도메인별 임계값(사이버, 바이오, ML R&D, CBRN) |
| ML R&D 자율성 레벨 1 | "R&D 자동화" | 경쟁력 있는 비용으로 AI R&D 파이프라인 완전 자동화 |
| 샌드배깅 | "전략적 실력 은닉" | 모델이 평가에서 실력을 숨김; OpenAI Research Categories에 위치 |
| 도구적 추론 | "수단-목적 추론" | 목표 달성 방법에 대한 추론; DeepMind 모니터링의 대상 |

## 더 읽을거리

- [OpenAI — Updating our Preparedness Framework](https://openai.com/index/updating-our-preparedness-framework/) — v2 발표.
- [OpenAI — Preparedness Framework v2 PDF](https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf) — 전체 문서.
- [DeepMind — Strengthening our Frontier Safety Framework](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — FSF v3 발표.
- [DeepMind — Updating the Frontier Safety Framework (2026년 4월)](https://deepmind.google/blog/updating-the-frontier-safety-framework/) — Tracked Capability Levels 추가.
- [Gemini 3 Pro FSF Report](https://storage.googleapis.com/deepmind-media/gemini/gemini_3_pro_fsf_report.pdf) — FSF 형식 Risk Report의 예.
