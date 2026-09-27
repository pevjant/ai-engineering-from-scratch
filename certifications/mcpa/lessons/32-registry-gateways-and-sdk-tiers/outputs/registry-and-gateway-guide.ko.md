> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [registry-and-gateway-guide.md](registry-and-gateway-guide.md)

# 레지스트리와 게이트웨이 가이드

MCPA '사용 사례와 생태계' 도메인을 위한 한 페이지 참고 자료입니다. MCP 2026-07-28 기준입니다. MCP Registry는 현재 프리뷰 상태입니다. 정식 출시 전에 파괴적인 변경과 데이터 초기화가 있을 수 있음을 예상하세요.

## 레지스트리 승인 체크리스트

server.json 항목은 아래가 모두 성립할 때만 승인됩니다:

- [ ] 이름은 역방향 DNS 쌍이다. `io.github.username/server`(GitHub 인증) 또는 `com.example/server`(도메인 인증)
- [ ] 게시자가 그 정확한 authority에 대한 소유권을 증명했다(GitHub OAuth, DNS TXT 레코드, 또는 잘 알려진 경로의 HTTP 파일). 한 번도 검증되지 않은 네임스페이스나, 다른 사람이 검증한 네임스페이스는 거부된다
- [ ] 서버가 공개적으로 접근 가능하다. 공개 패키지(npm, PyPI, NuGet, Cargo, 또는 공개 OCI 레지스트리)이거나 열린 인터넷에서 닿을 수 있는 원격 URL이어야 한다. 사설 네트워크나 사설 피드의 서버는 거부된다
- [ ] 버전 문자열은 이번 게시에 대해 유일하고, 게시 후에는 불변이며, 버전 범위가 아니다(`^1.2.3`, `~1.2.3`, `>=1.2.3`, `1.x`와 같은 범위 문법은 금지)
- [ ] 하부 산출물이 server.json 이름과 맞는 자체 소유 증명을 갖는다. npm은 package.json의 `mcpName`, PyPI·NuGet·Cargo는 렌더링된 README의 `mcp-name: name` 문자열(Cargo는 crates.io가 HTML 주석을 벗겨내므로 눈에 보이는 텍스트), Docker나 OCI 이미지는 `io.modelcontextprotocol.server.name` 레이블

## packages vs remotes

| 필드 | 가리키는 것 | 클라이언트가 고르는 때 |
|---|---|---|
| `packages` | 패키지 레지스트리 위의 stdio 실행 산출물(npm, PyPI, NuGet, Cargo, OCI, 또는 MCPB) | 서버를 로컬에서 실행하고 싶을 때 |
| `remotes` | 서버가 직접 응답하는 `streamable-http`(또는 폐기된 `sse`) URL | 네트워크 너머로 호스팅된 서버를 호출하고 싶을 때 |

둘 다 하나의 항목에 있을 수 있습니다. 호스트가 고릅니다. server.json 맨 위의 `version`은 하부 패키지나 원격 API 버전과 맞춰 두세요. 둘의 의미가 벌어지는 일이 없도록요.

## 외워 둘 만한 한 가지 사실

server.json의 `$schema` URL(예: `.../schemas/2025-12-11/server.schema.json`)은 메타데이터 형식의 버전입니다. 실행 중인 서버가 `server/discover`를 통해 실제로 협상하는 MCP 프로토콜 버전(`2026-07-28`)과는 무관합니다. 하나를 다른 하나의 증거로 읽지 마세요.

## 게이트웨이 요청 체크리스트, 순서대로

1. `params._meta`를 파싱하고 `io.modelcontextprotocol/protocolVersion`과 `io.modelcontextprotocol/clientCapabilities`가 둘 다 있는지 확인합니다.
2. `MCP-Protocol-Version`, `Mcp-Method`, 그리고(`tools/call`, `resources/read`, `prompts/get`의 경우) `Mcp-Name`을 바디의 해당 필드들과 비교합니다. 어떤 불일치든 `HeaderMismatch`, 코드 `-32020`, HTTP `400`이며, 3단계 이전에 돌려줍니다.
3. 헤더 값을 사용해 라우팅합니다(그것이 미러링하는 존재 이유 전부입니다). 바디를 두 번 읽지 않습니다.
4. 풀어낸 백엔드와 도구 또는 리소스에 대해 호출자를 인가합니다.
5. 새로운, 자기완결적인 요청을 전달합니다. 절대 호출자 자신의 토큰을 그 안에 넣지 않습니다.
6. `resultType`, `ttlMs`, `cacheScope`를 그대로 클라이언트에게 돌려보냅니다.

## cacheScope 규칙, 인용용

`"private"` 결과는 그것을 가져온 호출자가 아닌 다른 호출자에게 제공되어서는 안 됩니다. `"public"` 결과는 모든 호출자에게 공유될 수 있습니다. `cacheScope`는 캐싱 힌트이지, 그 자체로 접근 통제 판단이 결코 아닙니다.

## SDK 티어 요구 사항

| 요구 사항 | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| 적합성 통과율 | 100% | 80% | 최소 기준 없음 |
| 새 프로토콜 기능 | 다음 명세 릴리스 이전 또는 그 시점 | 6개월 안에 | 일정 없음 |
| 이슈 분류 | 2영업일 안에 | 한 달 안에 | 요구 사항 없음 |
| 치명적(P0) 버그 수정 | 7일 안에 | 2주 안에 | 요구 사항 없음 |
| 안정 릴리스 | 필수 | 최소 하나 | 불필요 |
| 로드맵 | 게시됨 | 게시됨(Tier 2에 머무는 이유를 밝혔으면 그걸로 대체) | 불필요 |

확장(Tasks, MCP Apps, Skills 등)은 어느 티어에도 절대 요구되지 않습니다.

## 강등 기준

- Tier 1에서 Tier 2로: 어떤 적합성 테스트든 현재 안정 릴리스에서 4주 연속 실패
- Tier 2에서 Tier 3으로: 적합성 테스트의 20% 초과가 4주 연속 실패
- 어느 티어든: 2개월째 해결되지 않은 이슈들도 강등을 촉발할 수 있습니다
- 승급은 반대 방향으로 돌아갑니다: 자기 평가, 증거를 담은 이슈, 통과하는 적합성 실행, SDK 워킹 그룹의 서명

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 9, 10, 15절.
