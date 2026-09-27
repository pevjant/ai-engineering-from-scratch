> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-concept-prompt-designer.md](skill-concept-prompt-designer.md)

---
name: skill-concept-prompt-designer
description: 사용자 발화를 분할, 중의성 해소, 폴백을 거쳐 잘 만들어진 SAM 3 컨셉 프롬프트로 바꿉니다
version: 1.0.0
phase: 4
lesson: 24
tags: [sam3, open-vocab, prompt-engineering, segmentation]
---

# Concept Prompt Designer

SAM 3의 정확도는 컨셉 프롬프트를 어떻게 표현했는지에 크게 좌우됩니다. 이 스킬은 자유 형식의 사용자 발화를 SAM 3가 잘 처리하는 프롬프트로 정규화합니다.

## 언제 사용하나

- 자연어 객체 질의를 받는 UI를 만들 때.
- 업스트림 호출자가 문장을 보내는 API로 SAM 3를 노출할 때.
- SAM 3 매칭이 나빠서 디버깅할 때 — 흔히 모델이 아니라 프롬프트가 잘못된 형태입니다.

## 입력

- `utterance`: 원시 사용자 문자열.
- `context`: 선택적 도메인 힌트(예: "surveillance", "medical", "retail").
- `max_concepts`: 발화당 뽑아낼 최대 컨셉 수; 기본 5.

## SAM 3가 선호하는 규칙

- **문장이 아니라 짧은 명사구.** `"there is a cat"`보다 `"cat"`이 이깁니다.
- **구체적인 명사.** `"thing to ride on"`보다 `"skateboard"`가 이깁니다.
- **수식어는 명사 바로 앞에.** `"car that is red"`보다 `"red car"`가 이깁니다.
- **소문자.** SAM 3는 강건하지만 경험상 소문자 입력이 약간 더 낫습니다.
- **단수 또는 복수.** 둘 다 됩니다; 여러 인스턴스가 예상될 때는 복수가 도움이 됩니다.

## 단계

1. **흔한 구분자로 토크나이즈** — 쉼표, 세미콜론, "and", "or", "&".
2. **군더더기 접두사 제거** — "find", "show me", "segment", "detect", "locate", "a", "an", "the".
3. **전치사 수식어는 시각적일 때만 유지** — `"striped red umbrella"`는 OK, `"umbrella from yesterday"`는 안 됨(`"from yesterday"`는 이미지 안에 없음).
4. 선택적 `context`로 **중의성 해소**:
   - 감시(surveillance) 맥락의 `"window"` -> `"building window"`.
   - 의료 맥락의 `"window"` -> 보통 오류; 사용자에게 명확히 하라고 제안.
5. 분할 결과가 0개이고 발화에 구체적 명사가 하나 이상 있다면 원래 문자열로 **폴백**합니다. 구체적 명사를 뽑아낼 수 없으면 컨셉을 내보내지 말고, 경고만 돌려주고 사용자에게 명확히 하라고 요청하세요(규칙 참조).
6. **`max_concepts`로 상한.** 호출자가 요청한 것보다 많은 컨셉이 나오면 발화 순서대로 첫 `max_concepts`개를 유지하고, 나머지는 `"exceeded max_concepts"` 사유와 함께 `dropped`로 내보냅니다. 사용자가 긴 열거를 붙여넣어도 지연 시간이 제한됩니다.

## 출력 형식

```
[designed prompts]
  utterance:    <원본>
  concepts:     ["concept_1", "concept_2", ...]
  dropped:      ["filler_1", ...]
  warnings:     ["concept too abstract", "may match many classes", ...]

[sam3 calls]
  각 컨셉에 대해 실행: sam3.detect(image, concept)
  검출마다 고유한 컨셉 태그를 붙여 출력을 병합.
```

## 예시

```
in:  "can you find me a cat or two dogs?"
out: ["cat", "dogs"]
dropped: ["can you find me", "a", "or two", "?"]
note: 발화가 "two dogs"라고 말했기 때문에 "dogs"를 복수로 유지 — 복수 힌트를 보존합니다.

in:  "segment the big red truck and the blue sedan"
out: ["big red truck", "blue sedan"]
dropped: ["segment", "the", "and"]

in:  "thing near the door"
out: ["door"]
warnings: ["'thing' is too abstract for SAM 3; fell back to 'door'"]

in:  "striped red umbrella, green hat, pink balloon"
out: ["striped red umbrella", "green hat", "pink balloon"]
```

## 규칙

- 8단어보다 긴 문장을 SAM 3에 넘기지 마세요 — 그 이상이면 정확도가 떨어집니다.
- 발화에서 뽑아낼 수 있는 구체적 명사가 없으면 SAM 3를 실행하지 말고, 경고를 돌려주고 명확히 하라고 요청하세요.
- 따옴표 안의 구두점으로 자르지 마세요; 따옴표에 들어 있으면 `"black and white cat"`을 컨셉 하나로 유지하세요.
- 프로덕션 디버깅을 위해 원본 발화와 파생 컨셉을 항상 로그하세요.
