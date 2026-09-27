> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# MCP 사양 읽는 법

> 사양(specification)은 튜토리얼이 아니라 규범적(normative) 문서입니다. MUST는 구현을 결정짓고, SHOULD는 판단의 여지를 남기며, 기능의 Deprecated 상태는 그 기능을 얼마나 더 의지할 수 있는지를 정확히 알려 줍니다.

**유형:** 레퍼런스
**언어:** Python
**선수 지식:** 레슨 00
**시간:** 약 45분

## 학습 목표

- 사양의 구조를 헤매지 않고 찾아다니기: 어느 부분이 모든 구현이 반드시(MUST) 지원해야 하는 것이고 어느 부분이 필요할 때 추가되는 것인지
- RFC 2119와 RFC 8174의 키워드 강도를 정확히 읽기. 소문자로 쓰인 단어에는 규범적 효력이 없다는 규칙까지 포함해서
- schema.ts와 schema.json의 관계, 그리고 TypeScript 파일이 진짜 원천(source of truth)인 이유 설명하기
- 사양 개정(revision)의 Draft, Current, Final 상태와 개별 기능의 Active, Deprecated, Removed 상태를 구분하기
- 체인지로그(changelog) 항목을 그것을 만들어 낸 SEP까지 거슬러 올라가 보고, Deprecated 기능의 최조 제거 시점을 그 윈도우(대기 기간)로부터 계산하기

## 문제 상황

이 커리큘럼의 모든 사실은 결국 한 문서로 거슬러 올라갑니다. TypeScript 스키마로부터 만들어진 modelcontextprotocol.io의 사양입니다. 블로그 글에서, 현재 개정판보다 오래된 데이터로 학습된 교육 자료에서, 아니면 이전 릴리스에 대한 기억에서 MCP를 배운 팀은 사양이 실제로 요구하는 것에서 점점 벗어나게 됩니다. 그리고 시험은 "과거에 사실이던 것"이 아니라 사양을 기준으로 출제됩니다. 2025-06-18 개정판을 정확히 기억하고 있지만 현행 문서를 다시 읽지 않은 구현이라면 2026-07-28은 여전히 틀리게 알고 있을 것입니다. 이전 개정판의 MUST는 다른 규칙으로 대체될 수 있고, 한때 프로토콜의 중심에 있던 기능은 마이그레이션 경로가 붙은 채 Deprecated로 이동하면서도 지금까지와 똑같이 계속 동작할 수 있기 때문입니다.

사양을 읽는 것 자체가 하나의 스킬입니다. 규범적 텍스트가 어디에 있는지, 그 키워드들이 구현에 무엇을 강제하는지, 문서 전체의 성숙도가 개별 기능의 상태와 어떻게 다른지, 그리고 요약 글을 믿는 대신 어떤 주장을 그것을 만들어 낸 제안(proposal)까지 거슬러 올라가 확인하는지 알아야 합니다.

## 개념

사양은 소수의 파트로 구성됩니다. 아키텍처, 베이스 프로토콜, 버저닝과 호환성, 메시지 패턴, 인가(authorization), 서버 기능, 클라이언트 기능, 유틸리티이며, 그 위에 선택적 확장(extensions)이 얹힙니다. 개요 페이지는 이 중 무엇이 필수인지 분명히 밝힙니다. 모든 구현은 베이스 프로토콜, 버저닝, 메시지 패턴을 반드시(MUST) 지원해야 합니다. 인가, 서버 기능, 클라이언트 기능, 유틸리티를 포함한 나머지 전부는 애플리케이션이 실제로 필요로 하는 것에 따라 구현해도 됩니다(MAY). 이 한 문장은 그 자체로 기억할 가치가 있습니다. 바닥선(최소 요건)을 표시하기 때문입니다. 리소스도 프롬프트도 없이 stdio 위에서 툴만 제공하고 인가는 전혀 없는 서버라도, 베이스 프로토콜, 버저닝, 메시지 패턴만 바르게 지키면 여전히 규격에 맞는(conformant) MCP 서버입니다.

이 커리큘럼의 모든 메시지 형태, 그리고 시험이 물어볼 수 있는 모든 메시지 형태는 결국 한 파일에서 나옵니다. 사양 저장소의 TypeScript 스키마인 schema.ts입니다. 산문 페이지들은 그 스키마를 읽기 쉽게 설명한 것일 뿐 독립적인 진짜 원천이 아닙니다. 산문과 스키마가 서로 어긋나 보이는 곳에서는 schema.ts가 이깁니다. schema.json은 TypeScript를 파싱하지 못하는 도구들을 위해 schema.ts에서 자동 생성된 것이며, 그 자체로는 어떤 권위도 갖지 않습니다. 어떤 결과나 오류의 정확한 형태가 문제가 될 때, 답이 실제로 있는 곳은 스키마입니다.

사양의 규범적 언어는 RFC 2119와 RFC 8174의 조합인 BCP 14를 따릅니다. MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, OPTIONAL이라는 단어들은 여기에 표시된 것처럼 모두 대문자일 때에만 정의된 강도를 갖습니다. "클라이언트는 요청을 배치(batch)해서는 안 된다"고 쓰인 문장이 소문자라면 규범적 효력이 전혀 없는 평범한 산문입니다. 똑같은 단어가 MUST NOT으로 쓰이면 단호한 금지가 됩니다. 강도를 올바르게 읽는다는 것은 어휘가 아니라 대소문자를 보는 것입니다. MUST와 MUST NOT은 구현이 밑으로 내려갈 수 없는 바닥을 정합니다. SHOULD와 SHOULD NOT은 구체적이고 이해된 사유로 무시할 수 있는 강한 기본값을 묘사합니다. MAY와 OPTIONAL은 어느 쪽 기본값도 없는 진짜 선택지를 묘사합니다.

사양 개정판(날짜가 찍힌 문서 전체)은 세 상태 중 하나입니다. Draft 개정판은 진행 중이며 아직 사용할 준비가 되지 않았습니다. Current는 현재 활발히 쓰이는 유일한 개정판입니다. 오늘날 2026-07-28이 Current이며, 하위 호환(backwards-compatible) 변경은 아직 받을 수 있습니다. 식별자 자체는 YYYY-MM-DD 형식의 날짜로, 하위 비호환(backwards incompatible) 변경이 마지막으로 이루어진 날을 표시합니다. 그래서 Current 개정판은 이름을 바꾸지 않고도 호환되는 수정사항을 흡수할 수 있는 것이죠. Final 개정판은 지나간, 완결된 개정판입니다. 다시는 바뀌지 않습니다. 프로토콜이 상태 비저장이기 때문에, 서버가 실제로 어떤 개정판을 말하는지 알고 싶은 클라이언트는 문서를 추측으로 읽을 필요가 없습니다. 사양의 진입점인 server/discover를 호출해서 와이어 위에서 답을 직접 읽으면 됩니다.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "server/discover",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resultType": "complete",
    "supportedVersions": ["2026-07-28"],
    "capabilities": {"tools": {"listChanged": false}},
    "ttlMs": 300000,
    "cacheScope": "public"
  }
}
```

Current 개정판 안의 개별 기능 — 메시지 하나, 기능(capability) 하나, 전송 계층 하나 — 에는 개정판의 Draft, Current, Final 라벨과 별개로 자기만의 상태가 있습니다. Active는 규범적 요구사항 그대로 구현하며 예정된 제거가 없는 상태입니다. Deprecated는 기능이 여전히 온전히 명세되고 동작하지만, 마이그레이션 경로가 문서화되어 있고 제거 예정이라는 뜻이며, 새 구현은 채택하지 말아야 합니다. Removed는 초안 사양에서 삭제되어 다음 Current 개정판에는 등장하지 않을 상태입니다. Roots, Sampling, Logging, Dynamic Client Registration은 모두 2026-07-28에서 제거(removed)가 아니라 Deprecated입니다. 명세된 대로 지금 이 순간에도 정확히 동작하고, 이를 지원하는 서버나 클라이언트는 내일도 계속 동작합니다. Deprecated 기능 레지스트리는 현재 Deprecated 또는 Removed 상태인 모든 기능을 한 페이지에 나열하는 곳이라, 흩어진 체인지로그 항목들을 조합해 그 그림을 재구성할 필요가 없습니다.

폐기(deprecation) 정책은 고정 일정이 아니라 바닥선을 정합니다. 기능은 제거 후보가 되기 위해서라도 최소 12개월 동안 Deprecated 상태를 유지해야 하고, 이 윈도우는 폐기되기 전 제안이 Final에 도달한 때가 아니라 폐기를 처음 표시한 개정판의 릴리스 시점부터 셉니다. 이 윈도우가 끝나는 날이 그 기능의 최조 제거 가능 시점이며, 그 시점과 같거나 이후에 릴리스되는 첫 Current 개정판이 해당됩니다. 그 개정판에서 실제로 제거될지, 더 나중 개정판에서 제거될지, 아니면 훨씬 오래 Deprecated로 남을지는 릴리스 준비 과정에서 Core Maintainer가 내리는 결정입니다. Roots, Sampling, Logging, Dynamic Client Registration은 모두 2026-07-28에 릴리스된 개정판에서 Deprecated로 표시되었기 때문에, 공통 최조 제거 가능 시점은 2027-07-28과 같거나 이후에 릴리스되는 첫 개정판입니다. 어떤 개별 제안의 일정이 아니라 그 릴리스 날짜로부터 계산됩니다.

사양에 대한 모든 실질적 변경 — 새 기능, 파괴적(breaking) 변경, 거버넌스 변경 — 은 SEP(Specification Enhancement Proposal, 사양 개선 제안)를 거칩니다. seps 디렉터리의 마크다운 파일로, 동기(motivation), 정확한 사양 텍스트, 근거(rationale), 하위 호환성, 보안 영향을 명시합니다. SEP는 draft와 in-review 상태를 지나 승인되거나 기각되며, 참조 구현(reference implementation)과, 관찰 가능한 동작이 있는 표준 트랙 변경의 경우 적합성(conformance) 시나리오까지 존재해야만 final에 도달합니다. Extensions 트랙 SEP도 동일한 절차를 따르지만 핵심 프로토콜 추가가 아니라 선택적 확장을 묘사합니다. 사양의 모든 체인지로그 항목은 자신을 만들어 낸 SEP를 이름으로 밝힙니다. 그 SEP를 읽는 것이야말로 신중한 구현자, 그리고 신중한 시험 수험생이 한 줄 요약을 믿는 대신 주장을 확증하는 방법입니다. 이 레슨이 Active, Deprecated, Removed의 근거로 삼는 그 기능 라이프사이클과 폐기 정책 자체는 SEP-2596으로, 위에 설명한 메커니즘을 정확히 문서화하여 Final 상태에 도달한 Process SEP입니다.

JSON-RPC 배치 처리(batching)는 라이프사이클 정책이 막고자 만들어진 반면교사 같은 사례입니다. 2025-03-26 릴리스 개정판에서 추가되었고 단 한 릴리스 뒤인 2025-06-18에 폐기 기간 없이 그대로 제거되었습니다. 2026-07-28 체제에서는 이런 종류의 변경이 최소 12개월의 Deprecated 상태와 문서화된 마이그레이션 경로 없이는 다시 일어나지 않아야 합니다.

```figure
mcpa-01-spec-map
```

## 인터랙티브 랩

그림은 하나의 루트를 중심으로 사양을 지도화합니다. 베이스 프로토콜, 버저닝, 메시지 패턴을 반드시(MUST) 지원한다고 표시된 박스 세 개, 그리고 인가, 서버 기능, 클라이언트 기능, 유틸리티를 구현해도 된다(MAY)고 표시된 박스 네 개입니다. 그 아래 칩(chip) 세 개는 개별 기능의 라이프사이클인 Active에서 Deprecated로, 다시 Removed로 이어지는 상태를 추적합니다. 이 상태는 개정판이 아니라 기능을 따라다닙니다. 박스가 MUST일 수 있으면서도, 그 아래의 모든 것 — 예컨대 특정 서버가 어떤 툴이나 리소스를 노출할지 — 은 전적으로 구현의 선택으로 남습니다.

## 연습 랩

`code/main.py`를 열어 보세요. 네트워크 호출이 전혀 없고, 실제 서버와 통신하는 대신 사양을 데이터로 모델링합니다. 폐기된 기능 레지스트리, SEP 번호로 색인된 작은 체인지로그, 그리고 키워드 분류기가 들어 있습니다.

```bash
python3 code/main.py
```

출력물을 위의 개념 절과 대조하며 읽으세요. `classify_requirement`는 문장을 읽고 그 강도를 반환하는데, 대소문자만 다른 동일 단어가 `forbidden`이 아니라 `unspecified`로 분류되는 모습을 보여 줍니다. `feature_state`는 특정 개정판 기준으로 roots, sampling, JSON-RPC 배치 처리가 active, deprecated, removed 중 어디에 속하는지 답하고, `earliest_removal`은 2027-07-28 날짜를 어디에도 하드코딩하지 않고 폐기 윈도우로부터 직접 계산합니다. `changelog_lookup`은 SEP 번호를 받아 그것을 인용한 항목을 반환합니다. 마지막에 데모는 `server/discover` 요청을 보내고 그 교환을 출력하는데, 일부러 잘못되게 만든 것도 함께 보여 줍니다. 필수 `_meta` 블록이 빠진 요청으로, 규격에 맞는 서버는 이를 추측으로 넘기지 않고 반드시 거부해야 합니다. 자기만의 윈도우를 가진 새 항목을 `DEPRECATED_REGISTRY`에 추가하거나, `include-context-this-server-all-servers`가 따르는 기능을 바꾼 뒤 다시 실행해 보세요. 다른 코드는 하나도 건드리지 않은 채 `earliest_removal`과 `feature_state`가 변화를 반영하는 모습을 확인할 수 있습니다.

## 제공되는 산출물

`outputs/spec-reading-guide.md`는 실제 사양을 읽는 동안 옆에 펼쳐 둘 수 있는 한 페이지짜리 참조 자료입니다. MUST 지원 목록, 키워드 강도 표, 개정판 상태와 기능 상태의 차이, 정확한 기준 시점이 표시된 폐기 시점 규칙이 담겨 있습니다. 팀원에게 뭔가가 아직 현행인지 말해 주기 전에, 또는 시험 문제에 답하기 전에 체크리스트로 활용하세요.

## 검증하기

레슨 디렉터리에서 테스트를 실행하세요.

```bash
python3 -m unittest discover code/tests
```

테스트는 이 레슨의 주장들을 확인합니다. MUST와 MUST NOT은 required와 forbidden으로 분류되는지. 동일한 소문자 단어는 unspecified로 분류되는지. SHOULD와 MAY는 recommended와 optional로 분류되는지. SHOULD NOT과 NOT RECOMMENDED는 둘 다 not recommended로 분류되는지. 기능이 자기 폐기 개정판 이전에는 active로, 그 개정판과 같거나 이후에는 deprecated로 표시되는지. 제거 날짜만 있고 Deprecated 상태가 전혀 없는 기능은 결코 현행(current)으로 보고되지 않는지. 최조 제거 가능 시점이 하드코딩이 아니라 12개월 윈도우로부터 계산되는지. 다른 기능의 일정을 따르는 기능이 그 기능의 최조 제거 가능 시점을 공유하는지. 인식할 수 없는 기능 이름이 예외를 일으키지 않고 처리되는지. 체인지로그 항목을 SEP 번호로 찾을 수 있고 알 수 없는 SEP는 아무것도 반환하지 않는지. 조회한 개정판이 Current, Final, unknown을 올바르게 보고하는지. 저장소의 와이어 체커도 이 레슨의 전송 기록을 2026-07-28 규칙에 맞춰 검증합니다:

```bash
python3 scripts/check_mcpa_wire.py certifications/mcpa/lessons/01-reading-the-specification
```

## 캡스톤 연결

캡스톤은 2026-07-28 교환 하나를 처음부터 끝까지 조립하며, 아무것도 찾아보지 않고도 어떤 메시지 형태, 오류 코드, 사용된 기능이 아직 현행인지 판별할 수 있다고 가정합니다. 이 트랙의 이후 모든 레슨은 이 레슨이 여러분에게 가르친 방식으로, 즉 키워드 강도, 기능 상태, 그리고 실제로 그 규칙을 만들어 낸 SEP를 근거로 특정 페이지나 SEP를 인용합니다. 캡스톤이든 시험 문제든, 어떤 것이 MUST인지 SHOULD인지, 어떤 기능이 Removed가 아니라 Deprecated인지에 걸려 있다면, 여러분은 이 레슨이 데이터로 모델링한 바로 그 레지스트리와 키워드를 읽고 있는 것입니다.

## 핵심 용어

| 용어 | 의미 |
|------|---------|
| 베이스 프로토콜 | 모든 구현이 반드시(MUST) 지원해야 하는 JSON-RPC 메시지 형태 |
| BCP 14 | MUST, SHOULD, MAY가 대문자일 때에만 규범적 효력을 가진다는 RFC 2119와 RFC 8174의 규칙 |
| schema.ts | 모든 MCP 메시지와 구조의 진짜 원천(source of truth)인 TypeScript 파일 |
| Current 개정판 | 현재 활발히 사용 중인 유일한 사양 개정판. 오늘날의 2026-07-28 |
| Draft, Current, Final | 사양 개정판이 지나가는 세 가지 상태 |
| Active | 규범적 요구사항대로 구현되며 예정된 제거가 없는 기능의 상태 |
| Deprecated | 여전히 명세되고 동작하지만 마이그레이션 경로와 함께 제거 예정인 기능의 상태 |
| Removed | 초안 사양에서 삭제된 뒤의 기능 상태 |
| 최조 제거 가능 시점(earliest removal) | Deprecated 기능의 최소 윈도우가 끝난 시점과 같거나 이후에 릴리스되는 첫 Current 개정판 |
| SEP | Specification Enhancement Proposal(사양 개선 제안). 사양 변경을 제안하고 기록하는 마크다운 문서 |

## 더 읽기

- [MCP 사양 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [MCP 사양 2026-07-28, 베이스 프로토콜](https://modelcontextprotocol.io/specification/2026-07-28/basic)
- [MCP 사양 2026-07-28, 체인지로그](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [MCP 사양 2026-07-28, 폐기된 기능들](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)
- [기능 라이프사이클과 폐기 정책](https://modelcontextprotocol.io/community/feature-lifecycle)
- [SEP 가이드라인](https://modelcontextprotocol.io/community/sep-guidelines)
- `certifications/mcpa/research/mcp-2026-07-28-brief.md` 1절과 15절
- `phases/13-tools-and-protocols/31-mcp-conformance-versioning-and-operations` — 이 버전-시대 규칙들 위에 적합성 하네스(harness)를 구축하는 레슨입니다.
