> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 모더레이션(Moderation, 유해 콘텐츠 걸러내기) 시스템 — OpenAI, Perspective, Llama Guard

> 프로덕션(운영 환경) 모더레이션 시스템은 레슨 12~16에서 정의한 안전 정책을 실제 동작으로 구현합니다. OpenAI Moderation API: `omni-moderation-latest`(2024)는 GPT-4o급 모델을 기반으로 텍스트 + 이미지를 한 번의 호출로 분류하고, 이전 버전보다 다국어 테스트 셋에서 42% 더 좋습니다. 응답 스키마는 13개 카테고리 불리언 값을 돌려줍니다 — harassment, harassment/threatening, hate, hate/threatening, illicit, illicit/violent, self-harm, self-harm/intent, self-harm/instructions, sexual, sexual/minors, violence, violence/graphic. 대부분의 개발자에게 무료입니다. 계층화 패턴: 입력 모더레이션(생성 전), 출력 모더레이션(생성 후), 커스텀 모더레이션(도메인 규칙). 비동기 병렬 호출로 지연 시간을 숨기고, 걸리면 플레이스홀더 응답을 보여줍니다. Llama Guard 3/4(레슨 16): MLCommons 14개 유해성 항목, Code Interpreter Abuse, 8개 언어(v3), 멀티 이미지(v4). Perspective API(Google Jigsaw): LLM을 모더레이터로 쓰는 물결 이전부터 있던 유해성(toxicity) 점수 시스템. 주로 단일 차원의 유해성 점수이며 severe-toxicity/insult/profanity 변형이 있습니다. 콘텐츠 모더레이션 연구의 베이스라인입니다. 지원 중단: Azure Content Moderator는 2024년 2월에 지원이 중단(deprecated)되었고 2027년 2월에 완전히 은퇴하며, Azure AI Content Safety로 대체됩니다.

**유형:** Build
**언어:** Python (표준 라이브러리, 3계층 모더레이션 하니스)
**선수 지식:** 페이즈 18 · 16 (Llama Guard / Garak / PyRIT)
**시간:** 약 60분

## 학습 목표

- OpenAI Moderation API의 카테고리 체계를 설명하고, Llama Guard 3의 MLCommons 집합과 어떻게 다른지 서술하기.
- 3계층 모더레이션 패턴(입력, 출력, 커스텀)을 설명하고 각 계층의 고장 모드를 하나씩 꼽기.
- Perspective API가 'LLM 이전 시대' 베이스라인으로서 어떤 위치에 있는지, 그리고 왜 연구에서 아직도 쓰이는지 설명하기.
- Azure 지원 중단 타임라인을 말하기.

## 문제 상황

레슨 12~16은 공격과 방어 도구를 다룹니다. 레슨 29는 사용자가 제품과 접촉하는 최전면에서 그 방어를 실제로 작동시키는, 배포된 모더레이션 시스템을 다룹니다. 3계층 패턴이 2026년의 기본 구성입니다.

## 개념

### OpenAI Moderation API

`omni-moderation-latest`(2024). GPT-4o 기반. 텍스트 + 이미지를 한 번의 호출로 분류합니다. 대부분의 개발자에게 무료입니다.

카테고리(응답 스키마의 13개 불리언):
- harassment, harassment/threatening
- hate, hate/threatening
- self-harm, self-harm/intent, self-harm/instructions
- sexual, sexual/minors
- violence, violence/graphic
- illicit, illicit/violent

멀티모달 지원은 `violence`, `self-harm`, `sexual`에 적용되고 `sexual/minors`에는 적용되지 않으며, 나머지는 텍스트 전용입니다.

`code/main.py`의 코드 하니스에서는 가르치기 쉽게 만들려고 `/threatening`, `/intent`, `/instructions`, `/graphic` 하위 카테고리를 상위 카테고리에 합쳐서 처리합니다. 실제 프로덕션 코드는 13개 카테고리 전체 스키마를 사용해야 합니다.

이전 세대 모더레이션 엔드포인트보다 다국어 테스트 셋에서 42% 더 좋습니다. 카테고리별 점수를 돌려주며, 임계값은 애플리케이션이 정합니다.

### Llama Guard 3/4

레슨 16에서 다뤘습니다. MLCommons 유해성 14개 카테고리(OpenAI의 13개 응답 스키마 불리언과는 구성 방식이 다릅니다). 8개 언어 지원(v3). Llama Guard 4(2025년 4월)는 네이티브 멀티모달, 12B 모델입니다.

OpenAI와 Llama Guard의 카테고리 체계는 겹치지만 서로 갈라집니다. OpenAI에는 광범위한 "illicit" 카테고리가 있는 반면, Llama Guard는 "violent crimes"와 "non-violent crimes"를 따로 둡니다. 배포할 때는 자기 정책 카테고리 체계와 얼마나 잘 맞는지로 고릅니다.

### Perspective API (Google Jigsaw)

LLM을 모더레이터로 쓰는 물결 이전(2020년 이전)부터 있던 유해성(toxicity) 점수 시스템입니다. 카테고리: TOXICITY, SEVERE_TOXICITY, INSULT, PROFANITY, THREAT, IDENTITY_ATTACK. 주 점수는 단일 차원(TOXICITY)이고 하위 차원 변형이 붙는 구조입니다.

API가 안정적이고 문서화가 잘 되어 있으며 수년간의 보정 데이터가 쌓여 있어서, 콘텐츠 모더레이션 연구의 베이스라인으로 널리 쓰입니다. 최신 LLM 인접 용도에는 Llama Guard나 OpenAI Moderation이 보통 더 잘 맞습니다.

### 3계층 패턴

1. **입력 모더레이션.** 생성 전에 사용자 프롬프트를 분류합니다. 걸리면 거절합니다. 지연 시간: 분류기 호출 한 번.
2. **출력 모더레이션.** 전달 전에 모델 출력을 분류합니다. 걸리면 거절 응답으로 바꿉니다. 지연 시간: 생성 후 분류기 호출 한 번.
3. **커스텀 모더레이션.** 도메인별 규칙(정규식, 허용 목록, 비즈니스 정책). 입력이나 출력 어느 쪽에서든 돌릴 수 있습니다.

세 계층은 설계상 순차적입니다. 입력 모더레이션은 생성 전에 끝나야 하고, 출력 모더레이션은 생성 후에 돌아갑니다. 병렬화는 계층 '안에서' 적용합니다 — 같은 텍스트에 여러 분류기(예: OpenAI Moderation + Llama Guard + Perspective)를 동시에 돌리면 분류기별 지연 시간을 숨길 수 있습니다. 선택 최적화로, 입력 모더레이션이 끝날 때까지 "잠시만요, 확인 중입니다..." 같은 플레이스홀더 응답을 보여주고 첫 토큰 스트리밍을 늦출 수도 있습니다. 걸렸을 때의 동작은 설정할 수 있습니다: 거절, 정화(sanitize), 사람 검토로 에스컬레이션.

### 고장 모드

- **입력만.** 출력의 환각은 못 잡습니다(레슨 12~14의 인코딩 공격은 입력 분류기를 우회합니다).
- **출력만.** 어떤 입력이든 모델까지 도달합니다. 비용이 늘어나고, 내부 추론을 공격자에게 노출합니다.
- **커스텀만.** 카테고리 전반에 걸쳐 튼튼하지 않습니다. 정규식은 깨지기 쉽습니다.

계층화가 기본입니다. 이중 삼중의 안전장치(belt-and-suspenders)입니다.

### Azure 지원 중단

Azure Content Moderator: 2024년 2월 지원 중단(deprecated), 2027년 2월 완전 은퇴. 대체품은 Azure AI Content Safety이며, LLM 기반이고 Azure OpenAI와 통합됩니다. 이 마이그레이션은 2024~2027년에 걸친 Azure 배포 현장의 프로젝트입니다.

### 페이즈 18에서의 위치

레슨 16은 레드팀 맥락에서 모더레이션 도구를 다룹니다. 레슨 29는 운영에 배포된 모더레이션을 다룹니다. 레슨 30은 현재의 이중 사용(dual-use) 능력 증거로 마무리합니다.

```figure
an-moderation-layers
```

## 사용해 보기

`code/main.py`는 3계층 모더레이션 하니스를 만듭니다: 입력 모더레이터(키워드 + 카테고리 점수), 출력 모더레이터(출력에 같은 분류기 적용), 커스텀 모더레이터(도메인 규칙). 입력을 넣어 보면 어떤 계층이 무엇을 잡는지 관찰할 수 있습니다.

## 출시하기

이 레슨은 `outputs/skill-moderation-stack.md`를 산출물로 만듭니다. 배포 환경이 주어지면 모더레이션 스택 구성을 추천해 줍니다: 입력에는 어떤 분류기, 출력에는 어떤 분류기, 어떤 커스텀 규칙, 경계 사례를 판정할 판정자(judge)는 무엇인지.

## 연습 문제

1. `code/main.py`를 실행합니다. 무해한 입력, 애매한 경계의 입력, 유해한 입력을 세 계층 모두에 통과시켜 보세요. 각각 어떤 계층이 걸렸는지 보고하세요.

2. 하니스에 Perspective API 스타일의 특정 카테고리 유해성 점수를 추가해 보세요. 그 임계값 동작을 카테고리 점수와 비교하세요.

3. OpenAI Moderation API 문서와 Llama Guard 3 카테고리 목록을 읽습니다. OpenAI 카테고리 각각을 가장 가까운 Llama Guard 카테고리에 대응시켜 보세요. 깔끔하게 대응되지 않는 카테고리 세 개를 찾아보세요.

4. 코드 어시스턴트 배포(예: GitHub Copilot)를 위한 모더레이션 스택을 설계해 보세요. 가장 관련 있는 카테고리와 가장 관련 없는 카테고리를 찾고, 커스텀 규칙을 제안하세요.

5. Azure Content Moderator는 2027년 2월에 은퇴합니다. Azure AI Content Safety로의 마이그레이션을 계획해 보세요. 마이그레이션에서 가장 위험한 요소를 짚어보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| OpenAI Moderation | "omni-moderation-latest" | GPT-4o 기반 13카테고리(텍스트) 분류기, 부분적 멀티모달 지원 |
| Perspective API | "Google Jigsaw toxicity" | LLM 이전 시대의 유해성 점수 베이스라인 |
| Llama Guard | "MLCommons 14-category" | Meta의 유해성 분류기 (v3: 8B 텍스트, 8개 언어; v4: 12B 멀티모달) |
| 입력 모더레이션 | "pre-generation filter" | 모델 호출 전에 사용자 프롬프트를 검사하는 분류기 |
| 출력 모더레이션 | "post-generation filter" | 전달 전에 모델 출력을 검사하는 분류기 |
| 커스텀 모더레이션 | "domain rules" | 배포별 규칙(정규식, 허용 목록, 정책) |
| 계층화 모더레이션 | "all three layers" | 표준 프로덕션 배포 패턴 |

## 더 읽을거리

- [OpenAI Moderation API 문서](https://platform.openai.com/docs/api-reference/moderations) — omni-moderation 엔드포인트
- [Meta PurpleLlama + Llama Guard](https://github.com/meta-llama/PurpleLlama) — Llama Guard 저장소
- [Google Jigsaw Perspective API](https://perspectiveapi.com/) — 유해성 점수
- [Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/) — Azure 대체품
