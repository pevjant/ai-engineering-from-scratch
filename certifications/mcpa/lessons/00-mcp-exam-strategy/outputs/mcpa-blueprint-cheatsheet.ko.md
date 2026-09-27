> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [mcpa-blueprint-cheatsheet.md](mcpa-blueprint-cheatsheet.md)

# MCPA 블루프린트 치트 시트

한 페이지짜리 MCPA 시험 블루프린트 참고 자료입니다. 다섯 개 도메인, 공표된 가중치, 하위 역량, 무엇을 공부하든 변하지 않는 시험 사실들, 구버전(legacy) 시대 함정 선지 체크리스트, 34개 레슨 전체 로드맵을 담고 있습니다.

## 다섯 개 도메인과 가중치

| 도메인 | 가중치 | 하위 역량(공표 기준) |
|--------|--------|----------------------------------|
| MCP 기초(MCP Fundamentals) | 16% | MCP의 목적과 범위; 핵심 MCP 개념; 상호 운용성과 가치 |
| 아키텍처와 구성 요소 | 14% | 스키마와 구조화 데이터; MCP 호스트, 클라이언트, 서버; 모델 상호작용 흐름 |
| 상호작용과 실행 | 26% | 상호작용 패턴과 응답 처리; 오류 처리; 도구 호출 수명 주기; 프로토콜 프리미티브 |
| 보안과 거버넌스 | 24% | 신뢰 경계; 권한과 동의; 위험 및 안전 통제; 감사 가능성과 관측 가능성 |
| 사용 사례와 생태계 | 20% | 역할, 책임, 도입; 운영 사용 사례; 생태계와 이식성 |

가중치의 합은 100퍼센트입니다. '상호작용과 실행'과 '보안과 거버넌스' 두 도메인이 블루프린트의 절반을 차지합니다. 즉, 이 둘이 학습 시간과 연습 문제를 가장 많이 투자할 가치가 있는 도메인이라는 뜻입니다.

## 가중치를 학습 시간으로 바꾸기

학습 시간 예산이 `H`라면, 가중치가 `W`퍼센트인 도메인에는 `H * W / 100`시간을 배정합니다. 예를 들어 40시간 예산이라면:

- MCP 기초(16%): 6.4시간
- 아키텍처와 구성 요소(14%): 5.6시간
- 상호작용과 실행(26%): 10.4시간
- 보안과 거버넌스(24%): 9.6시간
- 사용 사례와 생태계(20%): 8.0시간

`code/main.py`의 `allocate_study_hours`로 자신의 시간 예산 기준으로 다시 계산해 보세요.

## 연습 점수를 준비도 추정치로 바꾸기

다섯 도메인 점수를 똑같이 평균 내지 말고, 각 도메인의 연습 문제 정답률에 블루프린트 비중을 곱해서 더하세요. 아직 풀어 본 문제가 없는 도메인은 추정치에서 0으로 계산되는데, 이건 일부러 그렇게 만든 겁니다. 학습 범위의 빈틈을 감추지 않고 드러내기 위해서입니다. 인식할 수 없는 도메인 이름은 조용히 무시하지 않고 거부합니다. `code/main.py`의 `estimate_readiness`로 자신의 연습 점수를 다시 계산해 보세요.

## 고정된 시험 사실

- 형식: 온라인, 감독 시험(proctored), 객관식.
- 기준 명세: Model Context Protocol 2026-07-28.
- 응시료: 시험만 250미국 달러.
- 유효 기간: 2년.
- 재응시: 재응시 1회 포함.
- 시험 시간: 인증 페이지는 90분, Linux Foundation의 출시 보도자료는 120분으로 적고 있습니다. 이 커리큘럼은 인증 페이지를 따르며 이 불일치를 명시해 둡니다. 어느 쪽 숫자를 근거로 삼기 전에 반드시 재확인하세요.
- 문항 수: 어느 공식 출처에도 공표되지 않았습니다.
- 합격 점수: 어느 공식 출처에도 공표되지 않았습니다.

## 문제 읽기: 구버전 시대 함정 선지 잡아내기

- 첫 번째 실제 요청 전에 나오는 설정 단계, 핸드셰이크, 버전 협상 선지: 2026-07-28에는 그런 게 없습니다. 모든 요청이 자기 버전과 자신의 기능(capabilities)을 `_meta`에 실어 보냅니다.
- 호출 사이 상태를 기억하는 세션이나 고정(sticky) 연결 선지: 세션은 없습니다. 요청 간 상태는 서버가 만들어 준 명시적인 핸들(handle)이 일반 인자처럼 오가는 방식으로 전달됩니다.
- 모르는 도구에 `-32601`을 쓰는 선지: 올바른 코드는 `-32602`이고, `-32601`은 메서드 자체를 모른다는 뜻입니다.
- 스키마에 맞지 않는 인자를 프로토콜 오류로 보고하는 선지: 그건 도구 실행 오류, 즉 `isError: true`를 담은 정상 결과지 JSON-RPC 오류가 절대 아닙니다.
- 전체 함정 표는 `certifications/mcpa/research/mcp-2026-07-28-brief.md` 16절에 있습니다.

## 34개 레슨 로드맵

| 레슨 | 도메인 |
|--------|-----------|
| 00 mcp-exam-strategy | MCP 기초 |
| 01 reading-the-specification | MCP 기초 |
| 02 the-integration-problem | MCP 기초 |
| 03 json-rpc-and-meta | MCP 기초, 아키텍처와 구성 요소 |
| 04 the-stateless-core | MCP 기초 |
| 05 protocol-eras-and-compatibility | MCP 기초 |
| 06 hosts-clients-and-servers | 아키텍처와 구성 요소 |
| 07 discovery-and-capability-negotiation | 아키텍처와 구성 요소 |
| 08 tool-schemas-and-structured-content | 아키텍처와 구성 요소 |
| 09 reading-server-manifests | 아키텍처와 구성 요소 |
| 10 model-interaction-flow | 아키텍처와 구성 요소 |
| 11 the-tools-primitive | 상호작용과 실행 |
| 12 the-resources-primitive | 상호작용과 실행 |
| 13 prompts-and-completion | 상호작용과 실행 |
| 14 multi-round-trip-requests-and-elicitation | 상호작용과 실행 |
| 15 deprecated-client-features | 상호작용과 실행 |
| 16 notifications-and-subscriptions | 상호작용과 실행 |
| 17 tool-invocation-lifecycle | 상호작용과 실행 |
| 18 error-handling | 상호작용과 실행 |
| 19 transports-and-http-headers | 상호작용과 실행, 아키텍처와 구성 요소 |
| 20 caching-and-pagination | 상호작용과 실행 |
| 21 long-running-work-and-tasks | 상호작용과 실행 |
| 22 trust-boundaries | 보안과 거버넌스 |
| 23 oauth-authorization | 보안과 거버넌스 |
| 24 client-registration-and-identity | 보안과 거버넌스 |
| 25 consent-and-least-privilege | 보안과 거버넌스 |
| 26 risk-and-safety-controls | 보안과 거버넌스 |
| 27 auditability-and-observability | 보안과 거버넌스 |
| 28 roles-and-adoption | 사용 사례와 생태계 |
| 29 operational-use-cases | 사용 사례와 생태계 |
| 30 the-extensions-framework | 사용 사례와 생태계 |
| 31 mcp-apps | 사용 사례와 생태계 |
| 32 registry-gateways-and-sdk-tiers | 사용 사례와 생태계 |
| 33 mcpa-capstone-readiness | 다섯 도메인 전체 |

`code/main.py`의 `allocate_study_hours`와 `estimate_readiness`로 학습 시간·준비도 섹션을 자신의 숫자로 다시 계산하고, 같은 파일의 `route_for_domain`으로 로드맵을 프로그램으로 조회할 수 있습니다.

위 모든 사실의 출처와 확인 날짜: 이 저장소의 `certifications/mcpa/research/source-verification-ledger.md`.
