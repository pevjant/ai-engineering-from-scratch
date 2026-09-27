> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 에이전트 워크벤치 팩

안정적인 에이전트 작업을 원하는 어떤 저장소에나 넣을 수 있는 드롭인 워크벤치입니다.

## 들어있는 것

- `AGENTS.md` — 팩의 나머지 부분으로 연결되는 짧은 라우터.
- `docs/` — 규칙, 신뢰성 정책, 핸드오프 프로토콜, 리뷰어 루브릭.
- `schemas/` — 상태, 보드, 범위 계약을 위한 JSON 스키마.
- `scripts/` — 초기화, 피드백 러너, 검증 게이트, 핸드오프 생성기.
- `bin/install.sh` — 멱등 설치기.

## 빠른 시작

```
bin/install.sh
$EDITOR task_board.json
python3 scripts/init_agent.py
```

## 버저닝

`VERSION` 파일이 곧 계약입니다. 메이저 올림에는 상태 마이그레이션이 필요합니다.
