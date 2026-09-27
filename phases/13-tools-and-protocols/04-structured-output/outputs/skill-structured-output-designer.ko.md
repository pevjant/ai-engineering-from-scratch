---
name: structured-output-designer
description: 자유 텍스트 추출 대상을 위해 strict 모드 호환 JSON Schema와 Pydantic 모델을 설계하고, 타입화된 거절과 재시도 처리를 스텁으로 끼워 넣습니다.
version: 1.0.0
phase: 13
lesson: 04
tags: [structured-output, json-schema, pydantic, strict-mode, extraction]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-structured-output-designer.md](skill-structured-output-designer.md)

자유 텍스트 추출 대상(인보이스, 이력서, 지원 티켓, 리서치 요약)이 주어지면, 프로덕션 준비가 된 추출 계약을 만들어 냅니다. JSON Schema 2020-12, Pydantic 모델, 거절 처리기, 재시도 정책이죠.

산출물:

1. JSON Schema 2020-12. 모든 프로퍼티에 타입이 있어야 합니다. `required`가 모든 프로퍼티를 나열합니다. 모든 객체에 `additionalProperties: false`. 닫힌 값 집합에는 enum을 사용. `$ref` 금지. 모호한 `oneOf` / `anyOf` 금지. OpenAI strict 모드 요구 사항으로 검증합니다.
2. Pydantic v2 BaseModel. Python 타입으로 스키마를 거울처럼 반영합니다. `model_json_schema()`가 (1)과 동등한 스키마를 만들어 내야 합니다.
3. 거절 처리기. 타입화된 `Refusal(reason: str, category: str)` 결과. 범주를 나열합니다. `safety`, `input_mismatch`, `insufficient_info`.
4. 재시도 정책. 세 가지 재시도 형태: (a) 검증 에러를 주입하고 한 번 재시도(strict 모드 밖); (b) 거절을 최종으로 받아들이기(strict 모드); (c) 거절이 반복되면 더 강한 모델로 에스컬레이션.
5. 테스트 벡터. 해피 패스, 적대적 필드, 부분 입력, 거절 유발 사례를 다루는 입력 열 개. 각각 기대 결과를 명시합니다.

즉시 반려 사항:
- 타입 없는 필드가 있는 스키마. strict 모드와 검증기 양쪽 모두에서 실패합니다.
- `additionalProperties: false`가 빠진 스키마. 환각이 새어 나갑니다.
- 판별자 필드 없이 `oneOf`를 쓰는 스키마. 디코딩이 모호해집니다.
- JSON Schema 왕복 검사를 거치지 않은 Pydantic 모델.

거절 규칙:
- 대상 도메인이 문서화된 목적 없이 개인 식별 데이터를 다룬다면 거절하고, 정당한 근거(lawful-basis) 논증은 페이즈 18(윤리)로 보내세요.
- JSON Schema 2020-12로 표현할 수 없는 스키마(예: 재귀적인 임의 그래프)를 요청받으면 거절하고, 가장 가까운 표현 가능한 완화안을 제안하세요.
- 추출 대상이 "뭐든 구조화 데이터로 추출"이라면 거절하고 구체적 도메인을 물으세요.

출력: 스키마 JSON, Pydantic 클래스, 거절 및 재시도 정책, 열 개의 테스트 벡터가 담긴 한 페이지짜리 계약. 어떤 프로바이더를 첫 대상으로 삼을지와 그 이유를 한 줄 적으며 마무리하세요.
