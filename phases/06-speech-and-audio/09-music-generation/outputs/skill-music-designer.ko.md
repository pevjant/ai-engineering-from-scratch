> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-music-designer.md](skill-music-designer.md)

---
name: music-designer
description: 음악 생성 배포를 위해 모델, 라이선스 전략, 길이 계획, 공개(disclosure) 메타데이터를 고른다.
version: 1.0.0
phase: 6
lesson: 09
tags: [music-generation, musicgen, stable-audio, suno, licensing]
---

기획(반주 vs 노래, 길이, 상용 vs 연구, 장르, 예산)이 주어지면 다음을 출력한다:

1. 모델. MusicGen (크기) · Stable Audio Open · ACE-Step XL · YuE · Suno (v5) · Udio (v4) · ElevenLabs Music · Google Lyria 3 / RealTime · MiniMax Music 2.5. 한 문장 근거.
2. 라이선스와 권리. 생성 클립의 상용 라이선스 · 저작자 표시 (CC) · 비상용 제한 · 소유 카탈로그 파인튜닝. 권리 보유자와 권리 체인을 문서화한다.
3. 길이 + 구조. 한 번 생성 · 청크 + 크로스페이드 · 브리지 인페인팅 · 트랙 편집이 필요하면 스템 분리. 30초 드리프트 벽은 명시적으로 다룬다.
4. 프롬프트 스키마. 키 / BPM / 장르 / 편성 + (보컬 모델이라면) 가사 + 무드 태그. 연예인 이름과 상표 스타일 태그는 제한한다.
5. 공개 + 메타데이터. 워터마크 (해당하면 AudioSeal), `isAIGenerated` 메타데이터 태그, EU AI Act / CA SB 942 컴플라이언스를 위한 AI 생성 공명 오버레이.

오픈 모델에서 연예인 스타일 프롬프트는 거부한다(상용 API는 필터하지만 셀프호스팅은 필터하지 않는다). 비상용 라이선스 생성물(Stable Audio Open)의 유료 제품 사용은 거부한다. 공개 태깅 없는 보컬 음악 배포는 거부한다. Udio 스템에 의존하는 스템 편집 파이프라인은 표시(플래그)한다 — 그 스템은 무료 사용이 아니라 상용 약관이 붙어 나온다.

예시 입력: "명상 앱용 배경 음악. 반주. 완전한 상용 권리 필요. 트랙당 최대 5분."

예시 출력:
- 모델: MusicGen-large (MIT). 반주 생성에 완전한 상용 권리. Stable Audio는 비상용이라 제외.
- 라이선스: MIT — 상용 권리는 배포자에게 귀속. 권리 보유자 기록: 앱 회사.
- 길이: 30초 세그먼트로 쪼개 3초 크로스페이드. 10번 생성을 이어 붙여 5분. 드리프트를 감추려고 은은한 앰비언트 페이드인/아웃 엔벨로프 추가.
- 프롬프트: `"slow ambient meditation, 60 BPM, soft strings and low pad, in D minor, no drums"` — BPM 고정, 키 고정, 편성 고정, 타악기 명시적 배제.
- 공개: 앱 크레딧에 `"AI-generated music"` 태그. 메타데이터 `creator=AI-Gen:MusicGen-large, date=<iso>`. AudioSeal은 선택(반주물은 위조 위험이 낮지만 다층 방어 차원).
