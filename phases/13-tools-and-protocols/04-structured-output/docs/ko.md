> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 구조화된 출력 — JSON Schema, Pydantic, Zod, 제약 디코딩

> "모델에게 정중히 JSON을 부탁하기"는 5~15퍼센트 확률로 실패합니다. 프론티어 모델에서도요. 구조화된 출력은 제약 디코딩으로 이 간격을 메웁니다. 스키마를 어기는 토큰을 모델이 아예 내보내지 못하게 막아 버리는 것이죠. OpenAI의 strict 모드, Anthropic의 스키마 타입 도구 사용, Gemini의 `responseSchema`, Pydantic AI의 `output_type`, Zod의 `.parse`는 모두 같은 아이디어를 다섯 가지 모습으로 드러낸 것입니다. 이 레슨은 학습자가 모든 프로덕션 추출 파이프라인에서 쓰게 될 스키마 검증기와 strict 모드 계약을 만듭니다.

**유형:** Build(빌드)
**언어:** Python(표준 라이브러리, JSON Schema 2020-12 서브셋)
**선수 지식:** 페이즈 13 · 02(함수 호출 심층 탐구)
**시간:** 약 75분

## 학습 목표

- 추출 대상에 대해 올바른 제약(enum, min/max, required, pattern)으로 JSON Schema 2020-12를 작성할 수 있습니다.
- strict 모드와 제약 디코딩이 "생성 후 검증"과는 다른 보장을 주는 이유를 설명할 수 있습니다.
- 세 실패 모드(파싱 에러, 스키마 위반, 모델 거절)를 구분할 수 있습니다.
- 타입화된 복구와 타입화된 거절 처리를 갖춘 추출 파이프라인을 출시할 수 있습니다.

## 문제

구매 주문 이메일을 읽는 에이전트는 자유 텍스트를 `{customer, line_items, total_usd}`로 바꿔야 합니다. 접근 방식은 세 가지입니다.

**방법 하나: JSON으로 프롬프트하기.** "customer, line_items, total_usd 필드를 가진 JSON으로 답하세요." 프론티어 모델에서 85~95퍼센트 성공합니다. 실패 방식은 여섯 가지입니다. 중괄호 누락, 마지막 쉼표, 잘못된 타입, 환각된 필드, 토큰 한도에서 잘림, "여기 JSON이 있습니다:" 같은 산문 누출.

**방법 둘: 생성 후 검증.** 자유롭게 생성하고, 파싱하고, 스키마로 검증하고, 실패 시 재시도합니다. 믿을 수 있지만 비쌉니다. 재시도마다 돈을 내고, 잘림 버그는 발생할 때마다 턴 하나씩을 추가로 치릅니다.

**방법 셋: 제약 디코딩.** 프로바이더가 디코드 시점에 스키마를 강제합니다. 잘못된 토큰은 샘플링 분포에서 마스킹됩니다. 출력은 파싱이 보장되고 검증도 보장됩니다. 실패가 한 가지 모드로 정리됩니다. 거절(모델이 입력이 스키마에 맞지 않는다고 판단)이죠.

2026년의 모든 프론티어 프로바이더는 방법 셋의 어떤 형태를 탑재합니다.

- **OpenAI.** `response_format: {type: "json_schema", strict: true}`와, 모델이 사양할 경우 응답의 `refusal`.
- **Anthropic.** `tool_use` 입력에 스키마 강제. `stop_reason: "refusal"` 같은 건 없고, 도구 호출 없는 `end_turn`이 신호입니다.
- **Gemini.** 요청 수준의 `responseSchema`. 2026년 Gemini는 선택된 타입에 대해 토큰 수준 문법 제약을 탑재합니다.
- **Pydantic AI.** `output_type=InvoiceModel`이 `InvoiceModel`로 타입화된 구조화된 `RunResult`를 내보냅니다.
- **Zod(TypeScript).** 프로바이더 출력을 Zod 스키마로 검증하는 런타임 파서. OpenAI의 `beta.chat.completions.parse`와 짝을 이룹니다.

공통 실마리: 스키마를 한 번 선언하면 엔드투엔드로 강제한다.

## 개념

### JSON Schema 2020-12 — 공용어

모든 프로바이더가 JSON Schema 2020-12를 받아들입니다. 가장 많이 쓰게 될 구성:

- `type`: `object`, `array`, `string`, `number`, `integer`, `boolean`, `null` 중 하나.
- `properties`: 필드 이름에서 하위 스키마로의 사전(mapping).
- `required`: 반드시 나타나야 하는 필드 이름 목록.
- `enum`: 허용 값의 닫힌 집합.
- `minimum` / `maximum`(숫자), `minLength` / `maxLength` / `pattern`(문자열).
- `items`: 모든 배열 요소에 적용되는 하위 스키마.
- `additionalProperties`: `false`면 추가 필드를 금지(기본값은 모드에 따라 다름).

OpenAI strict 모드는 요구 사항 세 개를 더합니다. 모든 프로퍼티가 `required`에 명시되어야 하고, 모든 곳에서 `additionalProperties: false`여야 하고, 풀리지 않은 `$ref`가 없어야 합니다. 이를 어기면 API가 요청 시점에 400을 돌려줍니다.

### Python 바인딩인 Pydantic

Pydantic v2는 데이터클래스 형태의 모델에서 `model_json_schema()`로 JSON Schema를 만들어 냅니다. Pydantic AI가 이를 감싸서 이렇게 쓰면:

```python
class Invoice(BaseModel):
    customer: str
    line_items: list[LineItem]
    total_usd: Decimal
```

에이전트 프레임워크가 스키마를 엣지에서 OpenAI strict 모드, Anthropic `input_schema`, 또는 Gemini `responseSchema`로 번역합니다. 모델 출력은 타입화된 `Invoice` 인스턴스로 돌아옵니다. 검증 에러는 타입화된 에러 경로를 담은 `ValidationError`로 발생합니다.

### TypeScript 바인딩인 Zod

Zod(`z.object({customer: z.string(), ...})`)는 TS판입니다. OpenAI의 Node SDK는 `zodResponseFormat(Invoice)`를 노출하는데, 이것이 API의 JSON Schema 페이로드로 번역됩니다.

### 거절

strict 모드도 모델에게 답을 강요할 수는 없습니다. 입력이 스키마에 맞지 않으면("그 이메일은 인보이스가 아니라 시였습니다") 모델은 이유를 담은 `refusal` 필드를 내보냅니다. 코드는 이를 실패가 아니라 1급 결과(first-class outcome)로 다뤄야 합니다. 거절은 안전 신호로도 쓸모가 있습니다. 보호 콘텐츠 이메일에서 신용카드 번호를 추출하라고 한 모델은 안전 사유를 붙여 거절을 돌려줍니다.

### 공개된 제약 디코딩

오픈 웨이트(공개 가중치) 구현은 세 가지 기법을 씁니다.

1. **문법 기반 디코딩**(`outlines`, `guidance`, `lm-format-enforcer`): 스키마에서 결정론적 유한 오토마타를 만들고, 매 단계 FSM을 어길 토큰의 로짓을 마스킹합니다.
2. **JSON 파서와 짝을 이루는 로짓 마스킹**: 스트리밍 JSON 파서를 모델과 발을 맞춰 돌리고, 매 단계 유효한 다음 토큰 집합을 계산합니다.
3. **검증기와 짝을 이루는 추측 디코딩**: 저렴한 드래프트 모델이 토큰을 제안하면, 검증기가 스키마를 강제합니다.

상업 프로바이더들은 무대 뒤에서 이 중 하나를 고릅니다. 2026년의 최신 기술은 짧은 구조화 출력에서는 일반 생성보다 빠르고, 긴 출력에서는 대략 같은 속도입니다.

### 세 실패 모드

1. **파싱 에러.** 출력이 유효한 JSON이 아닙니다. strict 모드에서는 일어날 수 없습니다. non-strict 프로바이더에서는 여전히 일어날 수 있습니다.
2. **스키마 위반.** 출력은 파싱되지만 스키마를 어깁니다. strict 모드에서는 일어날 수 없습니다. 그 밖에서는 흔합니다.
3. **거절.** 모델이 사양합니다. 타입화된 결과로 다뤄야 합니다.

### 재시도 전략

strict 모드 밖이라면(Anthropic 도구 사용, non-strict OpenAI, 구버전 Gemini) 복구 패턴은 다음과 같습니다.

```
generate -> parse -> validate -> if fail, inject error and retry, max 3x
```

재시도 한 번이면 보통 충분합니다. 세 번이면 약한 모델의 들쭉날쭉함을 잡습니다. 세 번을 넘기면 나쁜 스키마의 신호입니다. 어떤 입력에 대해서는 모델이 스키마를 만족시킬 수 없는 것이니 프롬프트나 스키마를 고쳐야 합니다.

### 소형 모델 지원

제약 디코딩은 소형 모델에서도 동작합니다. 문법 강제를 붙인 30억 파라미터 공개 모델이, 순수 프롬프팅만 한 700억 파라미터 모델을 구조화 작업에서 이깁니다. 구조화된 출력이 프로덕션에서 중요한 주된 이유가 바로 이것입니다. 신뢰성을 모델 크기에서 분리해 주니까요.

```figure
constrained-decoding
```

## 활용하기

`code/main.py`는 표준 라이브러리만으로 쓴 최소 JSON Schema 2020-12 검증기(타입, required, enum, min/max, pattern, items, additionalProperties)를 실어 옵니다. `Invoice` 스키마를 감싸고 가짜 LLM 출력을 검증기에 통과시켜 파싱 에러, 스키마 위반, 거절 경로를 보여 줍니다. 프로덕션에서는 가짜 출력을 어떤 프로바이더의 실제 응답으로 바꾸면 됩니다.

볼 포인트:

- 검증기는 경로와 메시지를 담은 타입화된 `[ValidationError]` 목록을 돌려줍니다. 재시도 프롬프트에 노출하고 싶은 모양이 바로 이것입니다.
- 거절 분기는 재시도하지 않습니다. 로그를 남기고 타입화된 거절을 돌려줍니다. 페이즈 14 · 09가 거절을 안전 신호로 씁니다.
- `additionalProperties: false` 검사가 적대적 테스트 입력에서 발동해, strict 모드가 환각 필드에 문을 닫는 이유를 보여 줍니다.

## 출시하기

이 레슨은 `outputs/skill-structured-output-designer.md`를 만듭니다. 자유 텍스트 추출 대상(인보이스, 지원 티켓, 이력서 등)이 주어지면, 이 스킬이 strict 모드 호환 JSON Schema 2020-12와 그것을 거울처럼 반영하는 Pydantic 모델을 만들어 내고, 타입화된 거절과 재시도 처리를 스텁으로 끼워 넣습니다.

## 연습 문제

1. `code/main.py`를 실행하세요. `total_usd`가 음수인 네 번째 테스트 케이스를 추가하고, 검증기가 `minimum` 제약 경로로 거부하는지 확인하세요.

2. 검증기를 확장해 판별자(discriminator)가 있는 `oneOf`를 지원하세요. 흔한 사례: `line_item`이 `kind`로 태그된 제품 또는 서비스. strict 모드에는 여기서 미묘한 규칙이 있으니 OpenAI의 구조화 출력 가이드를 확인하세요.

3. 같은 Invoice 스키마를 Pydantic BaseModel로 작성하고 `model_json_schema()` 출력을 손으로 만든 스키마와 비교하세요. Pydantic이 기본으로 설정하는데 손으로 만든 버전은 빠뜨리는 필드 하나를 찾으세요.

4. 거절율을 측정하세요. 추출이 되어서는 안 되는 입력 열 개(가사 한 곡, 수학 증명, 빈 이메일)를 만들어 strict 모드의 실제 프로바이더에 돌려 보세요. 거절과 환각 출력을 세어 보세요. 이것이 거절을 인지하는 재시도의 정답 기준(ground truth)입니다.

5. OpenAI의 구조화 출력 가이드를 처음부터 끝까지 읽으세요. 일반 JSON Schema는 허용하는데 strict 모드에서 명시적으로 금지하는 구성 하나를 찾으세요. 그다음 그 금지 구성을 본질적이지 않게 쓰는 스키마를 설계하고, strict 호환으로 리팩터링하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| JSON Schema 2020-12 | "스키마 명세" | 요즘 모든 프로바이더가 쓰는 IETF 드래프트 스키마 방언 |
| Strict 모드 | "스키마 보장" | 제약 디코딩으로 스키마를 강제하는 OpenAI 플래그 |
| 제약 디코딩(Constrained decoding) | "로짓 마스킹" | 디코드 시점에 잘못된 다음 토큰을 마스킹하는 강제 방식 |
| 거절(Refusal) | "모델이 사양함" | 입력이 스키마에 맞지 않을 때의 타입화된 결과 |
| 파싱 에러(Parse error) | "잘못된 JSON" | 출력이 JSON으로 파싱되지 않음. strict에서는 불가능 |
| 스키마 위반(Schema violation) | "모양이 틀림" | 파싱은 됐지만 타입 / required / enum / 범위를 어김 |
| `additionalProperties: false` | "여분 금지" | 모르는 필드를 금지. OpenAI strict에서 필수 |
| Pydantic BaseModel | "타입화된 출력" | JSON Schema를 만들어 내고 검증하는 Python 클래스 |
| Zod 스키마 | "TypeScript 출력 타입" | 프로바이더 출력 검증을 위한 TS 런타임 스키마 |
| 문법 강제(Grammar enforcement) | "오픈 웨이트 제약 디코드" | outlines / guidance 같은 FSM 기반 로짓 마스킹 |

## 더 읽기

- [OpenAI — 구조화된 출력](https://platform.openai.com/docs/guides/structured-outputs) — strict 모드, 거절, 스키마 요구 사항
- [OpenAI — 구조화된 출력 소개](https://openai.com/index/introducing-structured-outputs-in-the-api/) — 2024년 8월 출시 포스트, 디코딩 보장 설명
- [Pydantic AI — 출력](https://ai.pydantic.dev/output/) — 각 프로바이더로 직렬화되는 타입화 output_type 바인딩
- [JSON Schema — 2020-12 릴리스 노트](https://json-schema.org/draft/2020-12/release-notes) — 정규 명세
- [Microsoft — Azure OpenAI의 구조화된 출력](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs) — 엔터프라이즈 배포 노트와 strict 모드 주의 사항
