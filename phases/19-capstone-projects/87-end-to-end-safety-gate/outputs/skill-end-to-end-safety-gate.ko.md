---
name: skill-end-to-end-safety-gate
description: 입력 탐지기, 스트리밍 토큰 필터, 출력 분류기, 규칙 엔진을 결정적인 집계 표와 요청별 트레이스로 묶는 3체크포인트 안전 게이트
version: 1.0.0
phase: 19
lesson: 87
tags: [safety, harness, composition]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-end-to-end-safety-gate.md](skill-end-to-end-safety-gate.md)

# End-to-End Safety Gate(종단 간 안전 게이트)

## 생명주기

1. pre-gen(생성 전) - 프롬프트에 레슨 83 탐지기를 실행
   - 신뢰도 >= block_threshold이면: 거절 반환, 트레이스 내보내기, 정지
2. during-gen(생성 중) - 모델에서 스트리밍받으며 두 청크를 버퍼링하고 알려진 유해 이어쓰기를 스캔
   - 매치하면: 반복자 종료, 트레이스 표시, medium 심각도로 취급
3. post-gen(생성 후) - 조기 종료가 없었다면, 완성된 출력에 레슨 85 분류기 라우터와 레슨 86 규칙 엔진을 실행
4. aggregate(집계) - pre, during, post.classifier, post.rules 사이의 최대 심각도를 취함
5. apply(적용) - block, redact, warn, allow 중 하나로 매핑

## 집계 표

| 신호 상태 | 행동 |
|---|---|
| high 심각도가 하나라도 있음 | block |
| medium 심각도가 하나라도 있음 | redact |
| low 심각도가 하나라도 있음 | warn |
| 아무것도 없음 | allow |

## 트레이스 구조

```text
RequestTrace
  request_id: str
  prompt: str
  pre_gen: { category, confidence, fired[] }
  during_gen: { terminated_early, matched_pattern, partial_chunks }
  post_gen: { classifier_action, classifier_severity, rules_max_severity, rules_violations[] } | null
  final_action: block | redact | warn | allow
  final_output: str
  latency_ms: float
```

## 산출물

`outputs/gate_trace.json`에 요약과 요청별 트레이스가 담깁니다. 여기에는 분류 체계 픽스처 50개와 무해 프롬프트 10개가 포함됩니다.
