> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 레슨 12 - 비디오 이해 파이프라인 (TypeScript UI)

캡스톤의 TypeScript 쪽 절반입니다. Python 쪽(`code/main.py`)은 멀티 벡터 인덱스와 시간적 정합(템포럴 그라운딩)을 담당합니다. 이 프로젝트는 대시보드 절반을 출시합니다: 네 파이프라인 단계(청킹, 임베딩, 인덱싱, 질의응답) 위에서 돌아가는 Hono 앱입니다.

## 레이아웃

```text
src/
  index.ts     진입점: 데모(기본값) 또는 HTTP 서버(--serve)
  server.ts    Hono 라우트 (/, /jobs, /job/:id) + HTML 인덱스
  jobs.ts     JobStore + 픽스처 시더
  stages.ts    단계 진행 + 전체 상태
  types.ts     Stage, StageState, Job
tests/
  stages.test.ts  작업 상태 전이 + 저장소
```

## 실행

```bash
npm install
npm run typecheck
npm test
npm start              # 스스로 종료되는 데모
npm run serve          # :8123에서 HTTP 서버
```
