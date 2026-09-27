> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 코드 마이그레이션 에이전트 대시보드 (TypeScript 스켈레톤)

코드 마이그레이션 에이전트 캡스톤의 대시보드 레이어를 위한 여러 파일로 이루어진 TypeScript 스켈레톤입니다. 에이전트(Python)는 샌드박스에서 실행되고, 이 서버는 운영자에게 진행 상황을 보여줍니다.

## 레이아웃

- `src/index.ts` — 진입점. 틱(tick)을 시뮬레이션하고, 선택적으로 HTTP를 서빙합니다.
- `src/server.ts` — `/`, `/dashboard`, `/migrations`, `/migrations/:id` 라우트를 담당하는 Hono 서버.
- `src/migrations.ts` — 파일별 상태 머신과 시드(seed) 데이터.
- `src/cost.ts` — 턴 수와 달러 예산 강제.
- `src/types.ts` — 공유 타입.
- `tests/*.test.ts` — `tsx`를 통해 돌리는 `node --test` 스타일 테스트.

## 설치

```bash
npm install
```

## 실행

```bash
npm start         # 오프라인: 40틱 시뮬레이션 후 집계(rollup) 출력
npm run serve     # PORT(기본값 8009)에서 HTML 대시보드 서빙
```

## 검증

```bash
npm run typecheck
npm test
```

## 스펙 참조

- 원본 레슨: `phases/19-capstone-projects/09-code-migration-agent/docs/en.md`
- 레시피: [OpenRewrite](https://docs.openrewrite.org), libcst.
