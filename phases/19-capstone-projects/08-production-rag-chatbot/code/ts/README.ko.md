> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 캡스톤 08 - 프로덕션(운영 환경) RAG 챗봇 (TypeScript)

Server-Sent Events(SSE)로 출처 인용(citation)을 붙인 응답을 스트리밍하는 채팅 UI 스켈레톤입니다. `../main.py`에 있는 Python 파이프라인과 짝을 이룹니다. 대화 상태는 `sessionId`를 키로 하는 프로세스 내부 Map에 저장되므로, 같은 세션 아이디로 여러 턴에 걸친 대화를 이어갈 수 있습니다.

## 레이아웃

```text
ts/
  package.json
  tsconfig.json
  src/
    index.ts        # 진입점, 데모 + HTTP 서버
    server.ts      # hono 앱, /, /chat/stream (SSE), /sessions, /health
    session.ts     # SessionStore (Map<sessionId, Session>)
    stream.ts      # SSE 프레임 인코더 + 파서 + 목(모크) 검색 + 토크나이저
    types.ts        # Session, Turn, Citation, KbEntry, SseEvent
  tests/
    session.test.ts
    stream.test.ts
    server.test.ts
```

## 실행 방법

```bash
npm install
npm run typecheck
npm test
npm start          # 셀프 체크 1회 실행 후, 코드 0으로 종료
npm run serve      # 127.0.0.1:<포트>에서 대화형 HTTP 서버 실행
```

대화형 서버는 `PORT`가 설정되어 있지 않으면 사용 가능한 포트를 골라 쓰고, `/` 경로에 채팅 HTML 클라이언트를 붙입니다. 스트리밍은 `GET /chat/stream?sessionId=...&q=...`로 이루어집니다. 데모 클라이언트는 `EventSource`를 사용해 `session`, `citations`, `token`, `done` 이벤트를 기다립니다.

## 테스트

tsx를 통해 `node --test` 러너를 사용합니다. 커버리지:

- SessionStore: 생성, 조회, 추가(append), 목록 조회, 없는 아이디일 때 아무 일도 하지 않음.
- SSE 인코더 + 파서 왕복(round-trip) 테스트; 관할(jurisdiction) 태그에 따른 검색 부스트; 토크나이저 폴백(fallback) + "참고" 꼬리 문장.
- 서버: `/`, `/health`, `/chat/stream` 정상 경로(세션 + citations + token + done), q가 없을 때 400, 여러 턴에 걸친 세션 유지, `/sessions` 목록 조회.
