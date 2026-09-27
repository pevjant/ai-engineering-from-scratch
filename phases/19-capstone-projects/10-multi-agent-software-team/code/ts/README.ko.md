> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 멀티 에이전트 소프트웨어 팀 (TypeScript 스켈레톤)

멀티 에이전트 소프트웨어 팀 캡스톤을 위한 여러 파일로 이루어진 TypeScript 스켈레톤입니다. 플래너, 코더, 리뷰어 에이전트가 하나의 워크스페이스를 공유하고 코디네이터를 돌아가며 거칩니다. 워크트리 스텁(stub)은 거부 목록(denylist)과 셸 메타문자 거부 규칙을 갖춰 `execFile`로 자식 프로세스를 실행합니다.

## 레이아웃

- `src/index.ts` — 데모 러너.
- `src/agent.ts` — 기본 `Agent` 클래스와 `PlannerAgent`, `CoderAgent`, `ReviewerAgent`.
- `src/coordinator.ts` — 라운드 로빈 루프와 로테이션 추적.
- `src/workspace.ts` — 공유 인메모리 파일시스템과 메시지 로그.
- `src/runtime.ts` — 거부 목록을 갖춘 `child_process.execFile` 워크트리 스텁.
- `src/types.ts` — 공유 타입.
- `tests/*.test.ts` — `tsx`를 통해 돌리는 `node --test` 스타일 테스트.

## 설치

```bash
npm install
```

## 실행

```bash
npm start
```

## 검증

```bash
npm run typecheck
npm test
```

## 스펙 참조

- 원본 레슨: `phases/19-capstone-projects/10-multi-agent-software-team/docs/en.md`
- [MetaGPT](https://github.com/FoundationAgents/MetaGPT) 역할 기반 멀티 에이전트 프레임워크.
