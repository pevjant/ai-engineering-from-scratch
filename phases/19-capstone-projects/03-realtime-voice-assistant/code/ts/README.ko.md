> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 캡스톤 19/03 — 실시간 음성 비서 (TypeScript)

`../docs/en.md`에서 설명하는 스트리밍 음성 파이프라인을 위한 멀티 파일 TypeScript
웹 클라이언트 하니스입니다. 오프라인 상태 머신 시뮬레이션에 더해,
`ws` 패키지로 떠받치는 실제 동작하는(live) WebSocket 서버를 얹었습니다.

## 구성

```text
src/
  index.ts        진입점; 오프라인 세션 두 개를 실행하고, 실제 ws를 점검(probe)한 뒤 0으로 종료
  server.ts       hono /healthz + WebSocketServer를 통한 ws 업그레이드
  orchestrator.ts IDLE -> LISTENING -> WAITING -> THINKING -> SPEAKING, barge-in 포함
  vad.ts          발화 종료 점수기 + 합성 20ms 프레임 생성기
  protocol.ts     zod로 검증하는 프레임 봉투(event / summary)
  types.ts        AudioChunk, Metrics, SessionOptions, SessionSummary
tests/
  vad.test.ts
  orchestrator.test.ts
  protocol.test.ts
```

## 실행

```bash
npm install
npm start                # 오프라인 세션 두 개 + ws 자기 점검을 실행하고 0으로 종료
npm start -- --serve     # ws 서버를 계속 띄워 둠; ctrl-c로 정지
npm test                 # tsx를 통한 node --test 러너
npm run typecheck        # tsc --noEmit
```

비대화형 `npm start` 경로는 깨끗한 세션이 `first_audio_out`에 도달하는지,
barge-in 세션이 barge-in 이벤트를 최소 하나 기록하는지,
그리고 실제 WebSocket 점검이 닫히기 전에 `summary` 프레임을 받는지 검증합니다.
