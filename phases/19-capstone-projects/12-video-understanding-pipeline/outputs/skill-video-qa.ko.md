---
name: video-qa
description: 장면 분할, 멀티 벡터 인덱싱, 시간적 정합, 타임스탬프 인용을 갖춘 비디오 이해 파이프라인을 만듭니다.
version: 1.0.0
phase: 19
lesson: 12
tags: [capstone, video, multimodal, gemini, qwen-vl, molmo, transnet, qdrant]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-video-qa.md](skill-video-qa.md)

100시간 분량의 비디오가 주어지면, 흡수(ingestion) 파이프라인과 자연어 질문에 (시작, 끝) 타임스탬프와 프레임 미리보기를 붙여 답하는 질의 시스템을 만듭니다.

만들기 계획:

1. 비디오를 흡수합니다(YouTube URL 또는 MP4); 필요하면 720p로 다운스케일합니다.
2. TransNetV2 또는 PySceneDetect로 장면 분할; `[{scene_id, start_ms, end_ms, keyframe_path}]`를 내보냅니다.
3. Whisper-v3-turbo(faster-whisper)로 ASR을 돌려 단어 수준 타임스탬프를 만들고; 장면별로 자릅니다.
4. Gemini 2.5 Pro 또는 Qwen3-VL-Max 또는 Molmo 2로 VLM 캡셔닝; 캡션 + 프레임 임베딩을 내보냅니다.
5. 장면마다 이름 붙은 벡터 세 개(caption_emb, frame_emb, transcript_emb)와 페이로드 {video_id, scene_id, start_ms, end_ms, keyframe_url}를 가진 Qdrant 멀티 벡터 인덱스.
6. 질의: 세 개의 병렬 밀집(dense) 질의; 상호 순위 융합으로 병합; 상위 k=5 장면.
7. 시간적 정합(TimeLens 어댑터 또는 VideoITG)이 상위 장면 안에서 (시작, 끝)을 다듬습니다.
8. 질문 + 상위 3개 장면 클립 + 전사를 갖춘 VLM 종합(Gemini 2.5 Pro); `(video_id, start_ms, end_ms)` 인용을 요구합니다.
9. ActivityNet-QA, NeXT-GQA, 그리고 수작업 레이블 100문항 커스텀 셋으로 평가합니다. 전체 정확도와 질문 클래스별(묘사, 세기, 동작 유형) 정확도를 보고합니다.

평가 루브릭:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | 시간적 정합 IoU | 홀드아웃 정합 셋에서의 IoU |
| 20 | QA 정확도 | NeXT-GQA와 100문항 커스텀 셋 |
| 20 | 흡수 처리량 | 달러당 인덱싱한 비디오 시간 |
| 20 | UI와 인용 UX | 타임스탬프 링크, 썸네일 스트립, 프레임으로 이동 |
| 15 | 환각 비율 | 세기·동작 유형 정확도를 따로따로 보고 |

즉각 탈락(Hard rejects):

- 장면마다 단일 벡터로 풀링하는 파이프라인. 클래스 구분이 드러나려면 멀티 벡터가 필요합니다.
- (시작, 끝) 인용이 없는 답변.
- 세기/동작 서브셋 분해 없이 전체 정확도 하나만 보고하는 경우.
- 장면 프레임을 직접 받지 않는 VLM 종합(텍스트만 넣으면 시각적 근거가 사라집니다).

거절 규칙(Refusal rules):

- 라이선스 출처가 불분명한 비디오를 서빙하는 일을 거절합니다; 모든 video_id에 라이선스 태그를 요구합니다.
- 측정된 처리량을 넘는 흡수율에서 "실시간" 응답을 주장하는 일을 거절합니다.
- 세기/동작 환각 수치를 전체 정확도 숫자 안에 숨기는 일을 거절합니다.

산출물: 장면 분할 + ASR + 캡셔닝 파이프라인, 멀티 벡터 Qdrant 컬렉션, 시간적 정합 어댑터, 타임스탬프 딥링크가 있는 Next.js 15 뷰어, 세 벤치마크 평가 결과(ActivityNet-QA, NeXT-GQA, 커스텀), 그리고 관찰한 세기·동작 유형 실패 클래스 세 가지와 각각을 줄인 검색·종합 변경점을 적은 보고서를 담은 저장소.
