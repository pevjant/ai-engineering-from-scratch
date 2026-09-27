> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 캡스톤 19/02 — 코드베이스 RAG (TypeScript)

`../docs/en.md`에서 설명하는 하이브리드 검색 파이프라인을 구현한 멀티 파일
TypeScript 코드 검색 API입니다. 오프라인으로 동작하고, 결정론적이며, 6청크 샘플 코퍼스를 쓰고,
hono fetch 핸들러 뒤에 node:http를 얹었습니다.

## 구성

```text
src/
  index.ts        진입점; node:http 기동 + 자기 점검(probe) + 0으로 종료
  server.ts       hono 라우트 (/healthz, /query), zod로 POST 본문 검증
  retrieval.ts    runQuery + dense와 BM25에 걸친 RRF 병합
  index_store.ts  FNV-1a 해시 임베더, 코사인, 필드 가중 BM25
  corpus.ts       6청크 샘플 (uploader / auth / client / catalog)
  types.ts        Chunk, RankedChunk, QueryResponse, anchor()
tests/
  index_store.test.ts
  retrieval.test.ts
  server.test.ts
```

## 실행

```bash
npm install
npm start                # API 기동, 세 개 질의 점검, 0으로 종료
npm start -- --serve     # 서버를 계속 띄워 둠; ctrl-c로 정지
npm test                 # tsx를 통한 node --test 러너
npm run typecheck        # tsc --noEmit
```

비대화형 `npm start` 경로는 `/healthz`가 200을 돌려주는지, 그리고
모든 점검 질의가 인용(citation)을 최소 하나씩 돌려주는지 검증합니다. 라우트:

- `GET /healthz` — `{ok, corpus}`를 돌려줍니다.
- `GET /query?q=...` — 하이브리드 질의를 실행합니다.
- `POST /query` — JSON `{q, topK?}`, zod로 검증(`topK`는 50으로 상한).
