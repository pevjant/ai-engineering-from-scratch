> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 캡스톤 19/01 — 터미널 네이티브 코딩 에이전트 (TypeScript)

`../docs/en.md`에서 설명하는 플랜/행동/관찰 루프를 구현한 멀티 파일 TypeScript
하니스입니다. 오프라인으로 동작하고, 결정론적이며, 네트워크 호출이 전혀 없습니다.

## 구성

```text
src/
  index.ts     진입점; 스크립트로 짜인 데모와 평가(eval)를 실행한 뒤 0으로 종료
  repl.ts      대화형 명령 파서 (run / eval / help / quit)
  harness.ts   플랜-행동-관찰 루프, 훅 버스를 통해 연결
  hooks.ts     8종 이벤트 훅 버스와 파괴적 명령 가드
  model.ts     데모를 구동하는 스크립트형 오프라인 LLM
  tools.ts     zod로 인자를 검증하는 read_file + run_shell
  plan.ts     PlanState(투두 재작성) + Budget(턴 / 토큰 / 달러 상한)
  eval.ts      오프라인 과제 세 개에 대한 작은 합격/불합격 카운터
  types.ts     공유 형태(shape) 정의
tests/
  harness.test.ts
  tools.test.ts
```

## 실행

```bash
npm install
npm start                # 스크립트형 데모 + 오프라인 평가를 실행하고 0으로 종료
npm start -- --repl      # 대화형 하니스 REPL을 엽니다
npm test                 # tsx를 통한 node --test 러너
npm run typecheck        # tsc --noEmit
```

비대화형 `npm start` 경로는 평가가 `passed=3
failed=0`을 보고하는지, 그리고 스크립트 실행이 모두 완료(done)된 플랜으로 수렴하는지 검증합니다.
어긋나는 부분이 있으면 실행이 실패합니다.
