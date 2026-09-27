> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [official-academy-parity.md](official-academy-parity.md)

# 공식 Anthropic Academy 동등성(패리티) 지도

> 패리티란 자격증과 관련된 모든 학습 목표에 이 저장소만의 설명, 결정 연습, 산출물, 검증 경로가 있다는 뜻입니다. Academy 카탈로그를 베끼라는 의미가 아닙니다.

**검증일:** 2026-08-09

## 공식 프렙(예비 학습) 스냅샷

현재 파트너 프렙 페이지는 다음처럼 안내합니다:

- Associate Foundations: 8개 모듈, 표기된 총 389분.
- Developer Foundations: 5개 모듈, 표기된 총 774분.
- Architect Foundations: 기존 Academy 과목 7개의 묶음.
- Architect Professional: 5개 모듈, 표기된 총 733분.

이 합계는 날짜가 표시된 카탈로그 스냅샷일 뿐, 시험 시간이나 요구 학습 시간이
아닙니다. Academy는 공개 시험 가이드를 바꾸지 않고도 과목을 추가, 삭제, 재편할
수 있습니다.

출처: [Associate 프렙 경로](https://anthropic-partners.skilljar.com/path/claude-certified-associate-foundations),
[Developer 프렙 경로](https://anthropic-partners.skilljar.com/path/claude-certified-developer-foundations),
[Architect Foundations 프렙 묶음](https://anthropic-partners.skilljar.com/page/claude-certified-architect-foundations-prep-courses), 그리고
[Architect Professional 프렙 경로](https://anthropic-partners.skilljar.com/path/claude-certified-architect-professional).

## 학습 표면 지도

| 공식 Academy 표면 | 자격증 관련 목표 | 로컬(이 저장소) 커버리지 |
|---|---|---|
| [AI Fluency: Framework and Foundations](https://anthropic.skilljar.com/ai-fluency-framework-foundations) | 위임(Delegation), 묘사(Description), 판별(Discernment), 성실(Diligence) | 레슨 00, 05, 06, 07은 4D를 학습 계획, 기능 진단, 통제 지도, 사람 인수인계로 바꿔 놓는다 |
| [AI Capabilities and Limitations](https://anthropic.skilljar.com/ai-capabilities-and-limitations) | 다음 토큰 예측, 지식, 작업 메모리, 조종 가능성(steerability) 진단 | 레슨 04와 05는 컨텍스트 결정과 검증된 네 속성 실패 진단법을 제공한다 |
| [Claude 101](https://anthropic.skilljar.com/claude-101) | Claude 제품 표면, Projects, 지식, 커넥터, 리서치, 안전한 일상 워크플로 | 레슨 01, 04, 07과 Associate 캡스톤 |
| [Product Foundations](https://anthropic-partners.skilljar.com/product-foundations) | 비즈니스·통제 요구 사항에서 직접 Claude, Amazon Bedrock, Google Vertex AI, Microsoft Foundry 중 고르기 | 레슨 01의 배포 ADR; 레슨 22, 23, 25가 조달, 아키텍처, 신원, 데이터 경계 결정을 확장한다 |
| [Claude Platform 101](https://anthropic.skilljar.com/claude-platform-101) | 날것의 Messages 루프, SDK Tool Runner, 퍼스트파티 도구, 관리형 에이전트, 이벤트 스트림, 워크스페이스, 지출 통제 | 레슨 08, 10, 12, 13, 26이 오프라인 상태 기계, 실행 표면, 보안, 운영 연습을 제공한다 |
| [Building with the Claude API](https://anthropic.skilljar.com/claude-with-the-anthropic-api) | API 수명 주기, 스트리밍, 도구, 구조화된 출력, 캐싱, 배치, RAG, 평가(eval), Computer Use, 에이전트 | 레슨 08~14, 20, 24, 26; 기존 페이즈 레슨이 스크래치부터 쌓는 RAG와 평가 깊이를 제공한다 |
| [Introduction to MCP](https://anthropic.skilljar.com/introduction-to-model-context-protocol) | 클라이언트, 서버, 도구, 리소스, 프롬프트, 전송, MIME, 정리 | 레슨 11의 계약 랩과 페이즈 13의 MCP 서버·클라이언트 구축 |
| [MCP Advanced Topics](https://anthropic.skilljar.com/model-context-protocol-advanced-topics) | 샘플링, 루트(roots), 알림, JSON-RPC, Streamable HTTP, 세션, 확장 | 레슨 11의 결정·배포 랩과 페이즈 13의 샘플링, 루트/일루시테이션(elicitation) 구축 |
| [Claude Code 101](https://anthropic.skilljar.com/claude-code-101) | 권한, 계획 모드(Plan Mode), 컨텍스트 복구, CLAUDE.md, 서브에이전트, 스킬, MCP, 훅 | 레슨 15, 19와 기존 Claude Code 권한 모드 레슨 |
| [Claude Code in Action](https://anthropic.skilljar.com/claude-code-in-action) | 압축(compaction), 되감기(rewind), 목표와 루프, 워크트리, 헤드리스 자동화, 검토, 루틴, 배포 | 레슨 15, 19의 운영 패킷과 CI 검증기 |
| [Introduction to Agent Skills](https://anthropic.skilljar.com/introduction-to-agent-skills) | SKILL.md 작성, 설명을 통한 트리거, 도구 제한, 스크립트 패키징, 배포, 디버깅 | 레슨 19가 실제 멀티 파일 스킬을 출시하고 검증한다; 저장소 튜터가 이식 가능한 배포를 보여 준다 |
| [Introduction to Subagents](https://anthropic.skilljar.com/introduction-to-subagents) | 격리된 컨텍스트, 제한된 도구, 구조화된 보고서, 장애물, 시간 제한, 위임 한도 | 레슨 16, 17, 19 |
| [Introduction to Claude Cowork](https://anthropic.skilljar.com/introduction-to-claude-cowork) | 안내된 작업 루프, 상시 컨텍스트, 스킬/플러그인, 파일 워크플로, 책임 있는 조종 | 제품 풍경과 워크플로 선택에 대한 짧은 커버리지뿐; 공개 시험 목표로는 채택되지 않음 |
| Claude on Amazon Bedrock and Google Vertex AI | 프로바이더별 배포와 운영 | 레슨 01이 아키텍처 결정을 가르친다; 프로바이더 콘솔 실습은 선택적인 공식 보조 자료로 남는다 |

## 로컬 패리티가 더하는 것

지도에 올라온 각 레슨은 공식 목표를 언급하는 것으로 끝나면 안 됩니다:

1. 메커니즘과 그 실패 경계를 설명한다.
2. 학습자가 시나리오나 결정을 직접 조작해 보게 한다.
3. 학습자 소유의 산출물을 만들어 내게 한다.
4. 결정론적 검증기나 시뮬레이터를 실행한다.
5. 독창적인 문제와 역할별 캡스톤으로 전이를 시험한다.

개념 레슨이라도 실행 가능한 표면이 정책, 위협 모델, ADR, 승인 흐름, 증거 패킷을
채점합니다. 레슨이 기술적으로 보이게 하려고 가짜 프로바이더 코드를 넣는 일은
결코 없습니다.

## 의도적인 비(非)패리티

- 커리큘럼은 Academy의 해설, 슬라이드, 연습 문제, 퀴즈 문구를 베끼지 않는다.
- Academy 과목 총수를 고정해 두지 않는다.
- 파트너 영업 지원 자료를 기술 시험 요구 사항으로 만들지 않는다.
- stdlib 우선인 이 저장소에서 Pydantic을 요구하지 않는다; 레슨 09는 Pydantic의
  검증 역할이 어떻게 기반 계약에 대응되는지 가르친다.
- 공개 블루프린트가 콘솔 내비게이션이 아니라 아키텍처 결정을 요구할 때
  프로바이더 콘솔 튜토리얼을 복제하지 않는다.
- 튜터 상태, 랩, 그림(figure), 평가가 필수 학습 표면이므로 자격증 레슨을
  북(book) 워크플로로 흘려 보내지 않는다.
