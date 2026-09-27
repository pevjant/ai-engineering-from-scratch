---
name: actor-runtime
description: 개인 상태, 액터별 수신함, 메시지 전용 IPC, 결함 격리, 데드레터 큐를 갖춘 AutoGen v0.4 스타일 액터 런타임을 만듭니다.
version: 1.0.0
phase: 14
lesson: 14
tags: [autogen, actor-model, messaging, fault-isolation, dead-letter]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-actor-runtime.md](skill-actor-runtime.md)

멀티 에이전트 태스크가 주어지면, 액터 런타임과 필요한 에이전트 액터들을 만들어 냅니다.

만들 것:

1. `sender`, `recipient`, `topic`, `body`, `mid`를 가진 `Message` 타입.
2. `receive(message, runtime)`을 가진 `Actor` 베이스 클래스. 액터 상태는 비공개입니다.
3. 공유 큐, `send()`, `run_until_idle()`, 데드레터 큐를 가진 `Runtime`. 핸들러의 예외는 DLQ로 가고, 전파되지 않습니다.
4. 토폴로지 헬퍼 하나: RoundRobin(고정 순번), Selector(LLM이 다음을 지정), 또는 커스텀 브로드캐스트.
5. 메시지별 관측 훅: 레슨 23에 따라 `gen_ai.agent.name`과 `gen_ai.operation.name`을 담은 OTel 스팬을 내보냅니다.

절대 반려 사항:

- 받는 쪽이 돌아올 때까지 보내는 쪽을 막아 두는 동기 메시지 전달. 그건 v0.2 모델이며 결함 격리를 깨뜨립니다.
- 액터들에 걸친 공유 가변 상태. 액터는 메시지로 상태를 읽거나 아예 읽지 않습니다.
- 핸들러 예외를 전파하는 런타임. 실패는 DLQ로 가야 하고, 다른 액터는 계속 돌게 두세요.

거절 규칙:

- 태스크가 고정된 주고받기만 하는 두 액터뿐이라면, 액터 프레이밍을 거절하고 프롬프트 체인(레슨 12)을 제안하세요. 액터는 액터가 셋 이상이거나 비동기 동시성이 있을 때 비용을 정당합니다.
- "디버깅이 쉬워지니까" 동기 모드를 원하면 거절하세요. 대신 로깅 + 추적(레슨 23)을 제안합니다.
- 도메인이 전문가 하나짜리 순수 요청/응답이라면, 액터 팀 대신 라우팅(레슨 12)을 제안하세요.

출력: `message.py`, `actor.py`, `runtime.py`, `teams.py`, DLQ 정책·토폴로지 선택·OTel 스팬 연결 방식을 설명하는 `README.md`. 마지막은 "다음에 읽을 것"으로 끝냅니다 — 액터들이 협상한다면 레슨 25(멀티 에이전트 토론), 추적이 필요하면 레슨 23(OTel), 미래지향적인 런타임을 원하면 Microsoft Agent Framework를 가리킵니다.
