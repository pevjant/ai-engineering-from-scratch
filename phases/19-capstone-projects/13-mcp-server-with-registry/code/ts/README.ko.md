> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 레슨 13 - 상태 비저장(stateless) MCP 서버 (TypeScript)

캡스톤의 TypeScript 쪽 절반입니다. Python 쪽(`code/main.py`)은 레지스트리와 정책 게이트를 출시하고, 이 프로젝트는 MCP 전송 계층입니다: 목(mock) 인시던트 도구 세 개를 갖추고 stdio 위에서 직접 손으로 만든(newline으로 구분된) JSON-RPC 2.0입니다. `@modelcontextprotocol/sdk` 없이 MCP `2026-07-28`을 직접 구현하므로, 회선(wire) 위의 모든 바이트를 들여다볼 수 있습니다.

목 인시던트 저장소가 데이터를 보관하기는 하지만, 프로토콜 자체는 상태 비저장(stateless)입니다. 모든 요청은 `params._meta`에 프로토콜 버전과 클라이언트 기능(capabilities)을 반복해서 담습니다. 연결, 프로세스, 이전 요청 중 무엇도 세션을 만들지 않습니다. 서버는 필수인 `server/discover`를 노출하고, 성공한 모든 결과에서 자기 자신을 식별하며, 결정론적이고 캐시 가능한 도구 목록을 공개합니다. `tools/call`은 `tools/list`가 돌려준 범위가 한정된(bounded) 스키마와 동일한 기준으로 인자를 검증합니다. 알려진 도구에 잘못된 인자가 들어오면 `isError: true`가 담긴 완전한 도구 결과를 돌려주고, 절대 실행기(executor)까지 가지 않습니다.

런타임 신원(identity)은 `com.example/internal-incidents`입니다. 검증된 `example.com` 퍼블리셔의 역방향 DNS 네임스페이스를 사용합니다. 일치하는 공개 `server.json`은 로컬 npm 패키지가 자체적인 비공개 프로젝트 이름을 갖고 있더라도 반드시 같은 이름을 써야 합니다.

## 레이아웃

```text
src/
  index.ts      진입점: 픽스처 데모(기본값) 또는 stdio 루프(--serve)
  transport.ts  stdin readline + 픽스처 리플레이
  protocol.ts   요청 검증 / server/discover / tools/list / tools/call
  tools.ts      인시던트 도구 세 개 + 실행기
  types.ts      JSON-RPC + 도구 형태
tests/
  protocol.test.ts  상태 비저장 메타데이터, 디스커버리, 도구, 오류, 왕복(roundtrip)
```

## 실행

```bash
npm install
npm run typecheck
npm test
npm start            # 스스로 종료되는 픽스처 데모
npm run serve        # 실제 stdio 루프 (stdin에서 대기)
```

데모는 스스로 종료됩니다. 실제 stdio 서버는 입력 스트림이 닫힐 때까지 살아 있습니다. MCP 셔다운(shutdown) 요청이나 초기화 핸드셰이크는 없습니다.
