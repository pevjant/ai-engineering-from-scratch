---
name: benchmark-harness
description: FAIL_TO_PASS / PASS_TO_PASS 관문, 오염 검사, 단계 수 지표를 갖춘 SWE-bench 스타일 하네스스를 코드베이스용으로 만듭니다.
version: 1.0.0
phase: 14
lesson: 19
tags: [swe-bench, gaia, agentbench, harness, evaluation]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-benchmark-harness.md](skill-benchmark-harness.md)

코드베이스와 (bug, fix) 쌍 목록이 주어지면, 진짜 유닛 테스트로 관문을 두고 운영 지표를 기록하는 벤치마크 하네스스를 만듭니다.

만들 것:

1. 태스크별 정의: `(tid, description, state_before, fail_to_pass_tests, pass_to_pass_tests, solution)`.
2. 에이전트 패치를 적용하고, 샌드박스에서 저장소 테스트 스위트를 돌리고, 다음을 기록하는 러너: FTP 통과 수, PTP 통과 수, 단계 수, 토큰, 소요 시간, 비용.
3. 오염 검사: 이슈 텍스트를 만들어진 패치와 패턴 매칭. 겹침이 30% 이상이면 깃발을 올립니다.
4. 태스크별·집계 점수를 JSON으로 내보내고 P50/P75/P95 단계·비용을 더하는 리포터.
5. 모든 PR에서 하네스스를 돌리고 5% 이상 퇴보 시 실패 처리하는 CI 잡.

절대 반려 사항:

- 단일 집계 숫자만 보고하는 하네스스. 태스크별 결과 + 분포를 요구하세요.
- 샌드박스 없이 테스트를 돌리는 하네스스. 에이전트가 제공한 패치는 신뢰할 수 없는 코드입니다.
- PASS_TO_PASS 관문 없는 하네스스. 다른 테스트를 깨뜨리는 패치는 제품을 조용히 퇴보시킵니다.

거절 규칙:

- "FAIL_TO_PASS 점수만"을 요구하면 거절하세요. PASS_TO_PASS를 더하세요. 기존 테스트를 깨뜨리는 것은 수정을 놓치는 것보다 나쁜 퇴보입니다.
- 테스트가 특정 커밋에 고정돼 있지 않으면 거절하세요. 테스트가 흐트러지면 실행 간 점수 비교가 불가능해집니다.
- 태스크가 학습 중에 본 이슈 텍스트와 겹치면 명시적으로 깃발을 올리세요.

출력: `tasks.py`, `harness.py`, `contamination.py`, `report.py`, 샌드박스·관문·오염 정책을 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 하네스스 위에서의 평가 주도 개발은 레슨 30을 가리킵니다.
