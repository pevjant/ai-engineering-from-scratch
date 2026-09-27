> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# LLM 관측 가능성(옵저버빌리티) 대시보드 (TypeScript 스켈레톤)

LLM 관측 가능성 대시보드 캡스톤을 위한 여러 파일로 이루어진 TypeScript 스켈레톤입니다. Hono 서버가 OpenTelemetry GenAI 스팬을 받아 1만 개짜리 링 버퍼에 보관하고, p50/p95/p99 지연 시간과 모델별 비용을 그려 보여줍니다.

## 레이아웃

- `src/index.ts` — 진입점. 합성 스팬을 시드하고, 선택적으로 HTTP를 서빙합니다.
- `src/server.ts` — `/trace`, `/`, `/dashboard`, `/dashboard.json`, `/healthz` 라우트를 담당하는 Hono 서버.
- `src/spans.ts` — `RingBuffer`와 `ObservabilityStore`(기본값 스팬 1만 개).
- `src/rollup.ts` — `percentile`과 `rollUpByModel`.
- `src/pricing.ts` — 2026년 모델별 가격표와 비용 헬퍼.
- `src/types.ts` — 공유 타입.
- `tests/*.test.ts` — `tsx`를 통해 돌리는 `node --test` 스타일 테스트.

## 설치

```bash
npm install
```

## 실행

```bash
npm start         # 합성 스팬 1200개를 시드하고 집계(rollup)를 출력
npm run serve     # PORT(기본값 8011)에서 HTTP 수집 + 대시보드도 함께 서빙
```

## 검증

```bash
npm run typecheck
npm test
```

## 스펙 참조

- 원본 레슨: `phases/19-capstone-projects/11-llm-observability-dashboard/docs/en.md`
- [OpenTelemetry GenAI 시맨틱 컨벤션](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
