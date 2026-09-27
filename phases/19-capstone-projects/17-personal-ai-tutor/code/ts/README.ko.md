> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 레슨 17 - 개인 AI 튜터 (TypeScript 웹 앱)

캡스톤의 TypeScript 쪽 절반입니다. Python 쪽은 학습자 모델과 튜터 정책을 담당하고, 이 프로젝트는 웹 앱 표면을 담당합니다: 커리큘럼 DAG 탐색기, BKT 스타일 학습자 모델, FSRS 라이트 간격 반복(spaced repetition) 스케줄러가 두 개의 HTTP 라우트 뒤에 놓여 있습니다.

## 구성

```text
src/
  index.ts       진입점: demo (기본값) 또는 HTTP 서버 (--serve)
  server.ts      Hono 라우트 (GET /lesson/next, POST /lesson/:id/submit)
  curriculum.ts  DAG 픽스처 + Kahn 위상 정렬 + 다음 레슨 선택기
  mastery.ts     MasteryStore (레슨별 BKT식 업데이트)
  repetition.ts  scheduleNextDue (간격 두 배/절반 조정, 범위 제한)
  types.ts       Lesson, Mastery, Pick
tests/
  curriculum.test.ts  위상 정렬 순서, BKT 업데이트, FSRS 스케줄링
```

## 실행 방법

```bash
npm install
npm run typecheck
npm test
npm start            # 스스로 종료되는 커리큘럼 워크스루
npm run serve        # :8090에서 HTTP 서버 실행
```
