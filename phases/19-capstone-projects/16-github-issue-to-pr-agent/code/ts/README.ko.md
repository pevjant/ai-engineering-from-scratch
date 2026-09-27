> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 레슨 16 - GitHub 이슈→PR 에이전트 (TypeScript 웹훅 수신기)

캡스톤의 TypeScript 쪽 절반입니다. Python 쪽은 에이전트 루프와 디스패처를 담당하고, YAML 쪽은 Actions 워크플로를 담당합니다. 이 프로젝트는 GitHub App 웹훅 수신기 역할을 합니다: 원본 바디(raw body)의 HMAC 서명을 검증하고, 이벤트 타입별로 라우팅하며, `issues.opened` 이벤트가 오면 스텁(stub) 에이전트를 실행합니다.

## 구성

```text
src/
  index.ts    진입점: demo (기본값) 또는 HTTP 서버 (--serve)
  server.ts   Hono 웹훅 수신기 (POST /webhook)
  verify.ts   X-Hub-Signature-256 HMAC, 타이밍 안전(timing-safe) 비교
  router.ts   이벤트 타입 라우팅 (ping, issues, pull_request)
  agent.ts    스텁 에이전트 + 감사 로그
  types.ts    페이로드 + 감사(audit) 자료구조
tests/
  verify.test.ts  서명 통과, 변조 케이스, 라우터 분기
```

## 실행 방법

```bash
npm install
npm run typecheck
npm test
npm start            # 스스로 종료되는 데모 (인프로세스 리플레이)
npm run serve        # :8081 에서 HTTP 서버 실행
```

HMAC 시크릿은 `GH_WEBHOOK_SECRET`에서 읽어 옵니다(데모에서는 기본값 `demo-shared-secret`을 사용합니다).
