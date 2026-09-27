> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [spec-reading-guide.md](spec-reading-guide.md)

# 명세 읽기 가이드

MCP 2026-07-28 명세를 시험 출제자의 눈으로 읽기 위한 한 페이지 참고 자료입니다.

## 어디서부터 시작할까

- 명세 인덱스: 모든 구현체가 반드시(MUST) 지원해야 하는 것(기본 프로토콜, 버전 관리, 메시지 패턴)과 추가해도 되는(MAY) 것(인가, 서버 기능, 클라이언트 기능, 유틸리티)을 구분해 보여 줍니다.
- schema.ts가 모든 메시지와 구조의 진짜 원본(source of truth)입니다. schema.json은 도구용으로 여기서 생성된 것일 뿐, 스스로 어떤 권위도 갖지 않습니다.
- 현재 리비전은 2026-07-28입니다. 리비전 상태는 Draft, Current, Final 셋 중 하나이며, 동시에 Current인 리비전은 하나뿐입니다.

## MUST, SHOULD, MAY 읽는 법

| 키워드(전부 대문자일 때만) | 강도 |
|---|---|
| MUST, SHALL, REQUIRED | 필수 |
| MUST NOT, SHALL NOT | 금지 |
| SHOULD, RECOMMENDED | 권장 |
| SHOULD NOT, NOT RECOMMENDED | 권장하지 않음 |
| MAY, OPTIONAL | 선택 |

BCP 14(RFC 2119, RFC 8174)에 따르면 일반 문장 속 소문자 "must", "should", "may"에는 아무런 규범적 효력이 없습니다. 명세가 쓴 그대로, 전부 대문자인 형태만이 효력을 가집니다.

## 기능 상태 vs 리비전 상태

리비전(날짜가 찍힌 문서 전체)은 Draft, Current, Final 중 하나입니다. 기능(메시지 하나, 기능(capability) 하나, 전송 방식(transport) 하나)은 Active, Deprecated, Removed 중 하나인데, 이는 리비전 자체 상태와는 별개로 deprecated features 레지스트리에서 관리됩니다. 리비전 상태가 그대로인 상태에서도 그 안의 특정 기능만 Deprecated가 될 수 있습니다.

## 폐기(deprecation) 시점

- 폐기 최소 기간은 12개월인데, 이 기간은 해당 기능이 처음 Deprecated로 표시된 리비전이 출시된 시점부터 잽니다. 그 기능을 폐기한 SEP가 Final에 도달한 시점이 아닙니다.
- 가장 이른 제거 시점은 그 기간이 지난 뒤 Current로 출시되는 첫 번째 리비전입니다. 실제 제거는 출시 시점에 Core Maintainer의 결정이 있어야 이뤄집니다. 즉, 기능이 최소 기간보다 훨씬 오래 Deprecated로 남을 수도 있습니다.
- Deprecated 기능은 이를 대체하는(superseding) SEP에 의해 Active로 되돌아올 수 있습니다.

## SEP와 체인지로그 항목 읽기

- SEP는 seps 디렉터리의 마크다운 파일로 존재하며, draft → in review → accepted → final 순서로 진행됩니다(이 외의 결과로 rejected, withdrawn, dormant, superseded가 있습니다).
- SEP 유형은 넷입니다: Standards Track, Informational, Process, Extensions Track.
- 체인지로그 항목에는 자신을 만든 SEP의 이름이 적혀 있습니다. 한 줄 요약을 믿기 전에 SEP 파일 자체를 열어 정확한 명세 텍스트, 근거(rationale), 실제로 Final에 도달했는지를 확인하세요.

## 시험을 위해 기억하기

- Deprecated는 Removed가 아닙니다. Roots, Sampling, Logging, Dynamic Client Registration은 2026-07-28에서 Deprecated 상태이지 사라진 게 아닙니다. 명세대로 여전히 동작합니다.
- JSON-RPC 배칭(batching)은 2025-03-26에 출시된 리비전에서 추가됐다가 한 릴리스 뒤인 2025-06-18에 폐기 기간 없이 제거됐습니다. 이 공백이 바로 기능 수명 주기 정책이 존재하는 이유입니다.
- schema.ts와 schema.json이 서로 다를 때는 schema.ts가 정답입니다.

출처: `certifications/mcpa/research/mcp-2026-07-28-brief.md`, 1절과 15절.
