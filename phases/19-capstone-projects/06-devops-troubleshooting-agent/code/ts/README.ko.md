> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 캡스톤 06 - DevOps 문제 해결 에이전트 (TypeScript)

`../main.py`의 온콜(on-call) 에이전트를 위한 Slack 통합 뼈대입니다.
슬래시 명령 엔드포인트와 인터랙티브(버튼 클릭) 엔드포인트를 노출하며, 둘 다
Slack의 HMAC-SHA256 요청 서명과 5분 재생(replay) 윈도우로 보호됩니다.
파괴적인 복구 작업은 Slack 카드가 승인된 후에만 실행됩니다.

## 구성

```text
ts/
  package.json
  tsconfig.json
  src/
    index.ts          # 진입점, 데모 + HTTP 서버
    server.ts         # hono 앱, /slack/command + /slack/interactivity
    slack_verify.ts   # HMAC v0 검증 + 타이밍 안전 비교
    agent.ts          # 모의(mock) 가설 순위 매기기
    blocks.ts         # Block Kit 응답 빌더
    types.ts          # Hypothesis, AgentReport, SlackResponse, OutboundCall
  tests/
    slack_verify.test.ts
    agent.test.ts
    server.test.ts
```

## 실행

```bash
npm install
npm run typecheck
npm test
npm start          # 자기 점검 한 패스를 돌리고 0으로 종료
npm run serve      # 127.0.0.1:<port>에서 대화형 HTTP 서버
```

`SLACK_SIGNING_SECRET=...`을 설정하면 플레이스홀더 시크릿을 덮어씁니다.
대화형 서버는 선택된 포트를 출력합니다(`PORT`가 정해져 있지 않으면 무작위).

## 테스트

tsx를 통한 `node --test` 러너. 커버리지:

- Slack 서명 검증: 올바른 서명은 통과, 변조된 서명은 거부,
  낡은 타임스탬프(5분 넘는 편차)는 거부, 숫자가 아닌 타임스탬프는 거부,
  길이 불일치 경로는 상수 시간 비교 전에 처리.
- 모의 에이전트: OOM 키워드 경로, CrashLoop 키워드 경로, 폴백 경로.
- 서버: `/health`, `/slack/command`의 정상/변조/만료 경로,
  `/slack/interactivity` 승인 동작.
