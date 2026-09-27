---
name: sampling-tuner
description: 주어진 생성 과제에 디코딩 전략(greedy / temperature / top-k / top-p / min-p / speculative)을 고른다.
version: 1.0.0
phase: 7
lesson: 7
tags: [gpt, sampling, decoding, inference]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-sampling-tuner.md](skill-sampling-tuner.md)

생성 과제(코드, 창작, 추론, 대화, 구조화된 출력)와 지연 시간/품질 목표가 주어지면 다음을 출력합니다:

1. 샘플링 방법. 다음 중 하나: greedy, temperature 전용, top-k, top-p, min-p, beam-k, speculative. 한 문장 짜리 이유.
2. 파라미터 값. Temperature, top-k, top-p, min-p, 반복 패널티 — 과제 유형에 근거한 구체적 수치. (예: 코드는 temperature 0.2 + top-p 1.0; 채팅은 min-p 0.1 + temperature 0.7.)
3. 중단 조건. `max_new_tokens`, 중단 토큰 목록, 패턴 기반 중단(예: 닫는 `</tool_call>`).
4. 결정론성 토글. 재현성을 위한 고정 시드; 사용 사례(평가, 법률)가 이를 요구하는지 표시.
5. 품질 점검. 과제 목표에 대한 한 줄 테스트(컴파일/단위 테스트 통과, 사실성, 형식 유효성 등).

구조화된 출력이나 코드 완성에 temperature > 1.0을 추천하는 일은 거부합니다 — 환각 위험이 급격히 올라갑니다. 열린 대화에 순수 greedy를 추천하는 것도 거부합니다 — 모델이 같은 말만 반복하게 됩니다. 모델이 템플릿이나 도구를 생성할 수 있는데 중단 토큰 목록이 명시되지 않은 샘플링 설정을 출시하는 일 역시 거부합니다.
