> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 15 — 헌법적 안전 하니스(Constitutional Safety Harness) + 레드 팀 레인지(Red-Team Range)

> Anthropic의 Constitutional Classifiers, Meta의 Llama Guard 4, Google의 ShieldGemma-2, NVIDIA의 Nemotron 3 Content Safety, 다국어 커버리지를 위한 X-Guard가 2026년 안전 분류기 스택을 정의했습니다. garak, PyRIT, NVIDIA Aegis, promptfoo가 표준 적대적 평가 도구가 됐습니다. NeMo Guardrails v0.12가 이것들을 프로덕션(운영 환경) 파이프라인으로 묶어 줍니다. 이 캡스톤은 이 모든 것을 엮습니다: 대상 앱을 감싸는 계층화된 안전 하니스, 6개 이상 공격 계열을 돌리는 자율 레드 팀 에이전트, 그리고 측정 가능한 무해성(harmlessness) 변화를 만들어 내는 헌법적 자기 비판(self-critique) 실행.

**유형:** 캡스톤
**언어:** Python (안전 파이프라인, 레드 팀), YAML (정책 설정)
**선수 지식:** 페이즈 10 (스크래치 LLM), 페이즈 11 (LLM 엔지니어링), 페이즈 13 (도구), 페이즈 14 (에이전트), 페이즈 18 (윤리, 안전, 정렬(alignment))
**활용 페이즈:** P10 · P11 · P13 · P14 · P18
**소요 시간:** 25시간

## 문제

2026년 LLM 안전의 최전선은 분류기가 작동하느냐(대략 작동합니다)가 아니라, 과잉 거절(over-refusing) 없이도 그리고 뻔한 구멍을 남기지 않으면서도 프로덕션 앱 주위에 어떻게 올바르게 조립하느냐입니다. Llama Guard 4는 영어 정책 위반을 다룹니다. X-Guard(132개 언어)는 다국어 탈옥을 다룹니다. ShieldGemma-2는 이미지 기반 프롬프트 주입을 잡습니다. NVIDIA Nemotron 3 Content Safety는 엔터프라이즈 범주를 커버합니다. Anthropic의 Constitutional Classifiers는 서빙이 아니라 학습 중에 쓰는 별개의 접근법입니다.

공격의 진화도 중요합니다. PAIR와 TAP은 탈옥 발견을 자동화합니다. GCG는 그래디언트 기반 접미사(suffix) 공격을 돌립니다. 멀티턴과 코드 전환(code-switch) 공격은 에이전트 메모리를 악용합니다. 배포되는 모든 LLM에는 레드 팀 레인지 — garak과 PyRIT이 표준 드라이버입니다 — 와 문서화된 완화책, CVSS 점수가 붙은 발견 사항이 필요합니다.

여러분은 대상 애플리케이션(8B 명령 튜닝 모델 또는 다른 캡스톤의 RAG 챗봇 중 하나)을 강화하고, 6개 이상 공격 계열을 그 위에 돌리고, 이전/이후 무해성 측정치를 만들어 냅니다.

## 개념

안전 파이프라인은 다섯 레이어입니다. **입력 정화(sanitize)**: 폭 없는 너비 문자 제거, base64/rot13 디코딩, 유니코드 정규화. **정책 레이어**: NeMo Guardrails v0.12 레일(도메인 밖, 독성, PII 추출). **분류기 게이트**: 입력엔 Llama Guard 4, 비영어엔 X-Guard, 이미지 입력엔 ShieldGemma-2. **모델**: 대상 LLM. **출력 필터**: 출력에 Llama Guard 4, Presidio PII 스크럽, 해당하면 인용 강제. **HITL 단계**: 고위험으로 표시된 출력은 Slack 큐로 갑니다.

레드 팀 레인지는 스케줄러 위에서 돕니다. PAIR와 TAP은 자율적으로 탈옥을 발견합니다. GCG는 그래디언트 기반 접미사 공격을 돌립니다. ASCII / base64 / rot13 인코딩 공격. 멀티턴 공격(페르소나 채택, 메모리 악용). 코드 전환 공격(영어에 스와힐리어나 태국어를 섞음). 각 실행은 CVSS 점수와 공개(disclosure) 타임라인을 담은 구조화된 발견 사항 파일을 만들어 냅니다.

헌법적 자기 비판 실행은 학습 시점 개입입니다. 유해 시도 프롬프트 1천 개를 받아, 모델이 응답 초안을 쓰게 하고, 작성된 헌법(피해 금지 규칙)에 대조해 비판하게 하고, 그 비판 루프로 재학습합니다. 홀드아웃 평가에서 이전/이후 무해성 변화를 측정합니다.

## 아키텍처

```
request (text / image / multilingual)
      |
      v
input sanitize (strip zero-width, decode, normalize)
      |
      v
NeMo Guardrails v0.12 rails (off-domain, policy)
      |
      v
classifier gate:
  Llama Guard 4 (English)
  X-Guard (multilingual, 132 langs)
  ShieldGemma-2 (image prompts)
  Nemotron 3 Content Safety (enterprise)
      |
      v (allowed)
target LLM
      |
      v
output filter: Llama Guard 4 + Presidio PII + citation check
      |
      v
HITL tier for flagged outputs

parallel:
  red-team scheduler
    -> garak (classic attacks)
    -> PyRIT (orchestrated red team)
    -> autonomous jailbreak agent (PAIR + TAP)
    -> GCG suffix attacks
    -> multilingual / code-switch
    -> multi-turn persona adoption

output: CVSS-scored findings + disclosure timeline + before/after harmlessness delta
```

## 스택

- 안전 분류기: Llama Guard 4, ShieldGemma-2, NVIDIA Nemotron 3 Content Safety, X-Guard
- 가드레일 프레임워크: NeMo Guardrails v0.12 + OPA
- 레드 팀 드라이버: garak (NVIDIA), PyRIT (Microsoft Azure), NVIDIA Aegis, promptfoo
- 탈옥 에이전트: PAIR (Chao et al., 2023), Tree-of-Attacks (TAP), GCG 접미사
- 헌법적 학습: Anthropic 스타일 자기 비판 루프 + 비판에 대한 SFT
- PII 스크럽: Presidio
- 대상: 8B 명령 튜닝 모델 또는 다른 캡스톤의 RAG 챗봇 중 하나

```figure
cf-safety-stack
```

## 직접 만들기

1. **대상 설정.** vLLM 위에 8B 명령 튜닝 모델을 세웁니다(또는 다른 캡스톤의 RAG 챗봇을 재사용합니다). 이것이 테스트 대상 앱입니다.

2. **안전 파이프라인 감싸기.** 다섯 레이어 파이프라인을 대상 주위에 연결합니다. 각 레이어가 개별적으로 관찰 가능한지 확인합니다(Langfuse에 레이어별 스팬).

3. **분류기 커버리지.** Llama Guard 4, X-Guard(다국어), ShieldGemma-2(이미지)를 적재합니다. 베이스라인을 잡기 위해 작은 레이블 셋에서 각각 돌려 봅니다.

4. **레드 팀 스케줄러.** garak, PyRIT, PAIR 에이전트, TAP 에이전트, GCG 러너, 멀티턴 공격자, 코드 전환 공격자를 예약합니다. 각각 별도 큐에서 돕니다.

5. **공격 스위트.** 여섯 공격 계열: (1) PAIR 자동 탈옥, (2) TAP 공격 트리, (3) GCG 그래디언트 접미사, (4) ASCII / base64 / rot13 인코딩, (5) 멀티턴 페르소나, (6) 다국어 코드 전환. 계열별 성공률을 보고합니다.

6. **헌법적 자기 비판.** 유해 시도 프롬프트 1천 개를 엄선합니다. 각각에 대해 대상이 응답 초안을 씁니다. 비판자(critic) LLM이 작성된 헌법("피해 금지", "증거 인용", "불법 요청 거절")에 대조해 채점합니다. 비판자가 이의를 제기한 프롬프트는 다시 쓰고; 대상은 비판으로 개선된 쌍으로 파인튜닝합니다. 홀드아웃 평가에서 이전/이후 무해성을 측정합니다.

7. **과잉 거절 측정.** 무해한 프롬프트 스위트(예: XSTest)에서 거짓 양성 비율을 추적합니다. 대상은 무해한 질문에서 여전히 유용해야 합니다.

8. **CVSS 채점.** 성공한 탈옥마다 CVSS 4.0(공격 벡터, 복잡도, 영향)으로 점수를 매깁니다. 공개 타임라인과 완화 계획을 만듭니다.

9. **레인지 자동화.** 위의 모든 것은 cron으로 돕니다; 발견 사항은 큐에 기록되고; 과잉 거절 퇴보(regression) 알림이 Slack으로 발사됩니다.

## 사용해 보기

```
$ safety probe --model=target --family=PAIR --budget=50
[attacker]   PAIR agent running on target
[attack]     attempt 1/50: disguise query as academic research ... blocked
[attack]     attempt 2/50: appeal to roleplay ... blocked
[attack]     attempt 3/50: chain-of-thought coax ... SUCCEEDED
[finding]    CVSS 4.8 medium: roleplay bypass on target
[range]      7 successes out of 50 (14% success rate)
```

## 출시하기

`outputs/skill-safety-harness.md`가 산출물입니다. 프로덕션 수준의 계층화 안전 파이프라인과 이전/이후 무해성 변화를 갖춘 재현 가능한 레드 팀 레인지입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 공격 표면 커버리지 | 6개 이상 공격 계열 실행, 2개 이상 언어 |
| 20 | 참 양성 / 거짓 양성 트레이드오프 | 공격 차단률 vs XSTest 무해 통과율 |
| 20 | 자기 비판 변화량 | 홀드아웃 평가에서의 이전/이후 무해성 |
| 20 | 문서화와 공개 | 타임라인이 붙은 CVSS 점수 발견 사항 |
| 15 | 자동화와 재현성 | 전부 cron으로 돌고 알림까지 연동 |
| **100** | | |

## 연습 문제

1. RAG 챗봇에 garak의 프롬프트 주입 플러그인을 돌리고, 출력 필터 레이어의 유무에 따른 공격 성공률을 비교합니다.

2. 일곱 번째 공격 계열을 추가합니다: 검색된 문서를 통한 간접 프롬프트 주입. 추가로 필요한 방어를 측정합니다.

3. "거절하되 도움 주기(refuse-with-help)" 모드를 구현합니다: 가드레일이 막았을 때 대상이 무조건적 거절 대신 더 안전한 관련 답변을 제안하게 합니다. XSTest 변화량을 측정합니다.

4. 다국어 커버리지 공백: X-Guard가 기대에 못 미치는 언어를 찾습니다. 그 언어를 겨냥한 파인튜닝 데이터셋을 제안합니다.

5. 30B 모델에서 헌법적 자기 비판을 돌리고 변화량이 함께 확장되는지 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| 계층화 안전 | "심층 방어" | 입력, 게이트, 출력, HITL에 걸친 여러 가드레일 |
| Llama Guard 4 | "Meta의 안전 분류기" | 2026년 참고용 입력/출력 콘텐츠 분류기 |
| PAIR | "탈옥 에이전트" | LLM 주도 탈옥 발견에 관한 논문 (Chao et al.) |
| TAP | "공격 트리(Tree-of-Attacks)" | PAIR의 트리 탐색 변형 |
| GCG | "탐욕 좌표 그래디언트" | 그래디언트 기반 적대적 접미사 공격 |
| 헌법적 자기 비판 | "Anthropic 스타일 학습" | 대상 초안 작성 -> 비판자 채점 -> 재작성 -> 재학습 |
| XSTest | "무해 프로브 셋" | 과잉 거절 퇴보를 위한 벤치마크 |
| CVSS 4.0 | "심각도 점수" | 안전 발견 사항을 위한 표준 취약점 채점 체계 |

## 더 읽을거리

- [Anthropic Constitutional Classifiers](https://www.anthropic.com/research/constitutional-classifiers) — 학습 시점 참고 사례
- [Meta Llama Guard 4](https://www.llama.com/docs/model-cards-and-prompt-formats/llama-guard-4/) — 2026년 입력/출력 분류기
- [Google ShieldGemma-2](https://huggingface.co/google/shieldgemma-2b) — 이미지 + 멀티모달 안전
- [NVIDIA Nemotron 3 Content Safety](https://developer.nvidia.com/blog/building-nvidia-nemotron-3-agents-for-reasoning-multimodal-rag-voice-and-safety/) — 엔터프라이즈 참고 사례
- [X-Guard (arXiv:2504.08848)](https://arxiv.org/abs/2504.08848) — 132개 언어 다국어 안전
- [garak](https://github.com/NVIDIA/garak) — NVIDIA 레드 팀 툴킷
- [PyRIT](https://github.com/Azure/PyRIT) — Microsoft 레드 팀 프레임워크
- [NeMo Guardrails v0.12](https://docs.nvidia.com/nemo-guardrails/) — 레일 프레임워크
- [PAIR (arXiv:2310.08419)](https://arxiv.org/abs/2310.08419) — 탈옥 에이전트 논문
