> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 12 — 비디오 이해 파이프라인 (장면, 질의응답, 검색)

> Twelve Labs는 Marengo + Pegasus를 제품화했습니다. VideoDB는 비디오용 CRUD API를 출시했습니다. AI2의 Molmo 2는 오픈 VLM 체크포인트를 공개했습니다. Gemini 롱 컨텍스트는 몇 시간짜리 비디오를 기본으로 처리합니다. TimeLens-100K는 규모 있게 시간적 정합(temporal grounding)을 정의했습니다. 2026년 파이프라인은 정착됐습니다: 장면 분할, 장면별 캡션 + 임베딩, 전사(transcript) 정합, 멀티 벡터 인덱스, 그리고 (시작, 끝) 타임스탬프와 프레임 미리보기를 붙여 답하는 질의입니다. 이 캡스톤은 100시간을 흡수하고, 공개 벤치마크를 치고, 세기와 동작 유형 질문에서의 환각을 측정하는 것입니다.

**유형:** 캡스톤
**언어:** Python (파이프라인), TypeScript (UI)
**선수 지식:** 페이즈 4 (CV), 페이즈 6 (음성), 페이즈 7 (트랜스포머), 페이즈 11 (LLM 엔지니어링), 페이즈 12 (멀티모달), 페이즈 17 (인프라)
**활용 페이즈:** P4 · P6 · P7 · P11 · P12 · P17
**소요 시간:** 30시간

## 문제

긴 형식(long-form) 비디오 질의응답은 2026년 규모에서 가장 대역폭을 많이 먹는 멀티모달 문제입니다. Gemini 2.5 Pro는 2시간짜리 비디오를 기본으로 읽을 수 있지만, 100시간 분량의 비디오를 질의 가능한 코퍼스로 만들려면 여전히 장면 수준 인덱스가 필요합니다. 프로덕션(운영 환경) 형태는 장면 분할(TransNetV2 또는 PySceneDetect), VLM을 이용한 장면별 캡셔닝(Gemini 2.5, Qwen3-VL-Max, Molmo 2), 전사 정합(단어 타임스탬프가 있는 Whisper-v3-turbo), 그리고 캡션·프레임 임베딩·전사를 나란히 저장하는 멀티 벡터 인덱스를 결합합니다. 질의 파이프라인은 (시작, 끝) 타임스탬프와 프레임 미리보기를 붙여 답합니다.

벤치마크는 공개되어 있고(ActivityNet-QA, NeXT-GQA) 여러분 자신의 100문항 커스텀 셋도 만듭니다. 세기와 동작 유형 질문에서의 환각이 잘 알려진 난제(실패 클래스)이고, 이 캡스톤은 이를 명시적으로 측정합니다.

## 개념

흡수 단계에서 세 파이프라인이 병렬로 돕니다. **장면 분할**은 비디오를 장면 단위로 자릅니다. **VLM 캡셔닝**은 장면마다 캡션을 만들고 키프레임으로 프레임 임베딩을 만듭니다. **ASR 정합**은 단어 수준 타임스탬프를 만듭니다. 세 스트림은 (scene_id, 시간 범위)로 연결됩니다. 각 장면은 멀티 벡터 인덱스(Qdrant)에 벡터 세 종류를 갖습니다: 캡션 임베딩, 키프레임 임베딩, 전사 임베딩.

질의 시점에는 자연어 질문이 세 벡터 모두에 발사됩니다; 결과는 RRF로 병합됩니다; 시간적 정합 어댑터(TimeLens 스타일)가 상위 장면 안에서 (시작, 끝) 윈도우를 다듬습니다. VLM 종합기(Gemini 2.5 Pro 또는 Qwen3-VL-Max)는 질문 + 상위 장면 + 잘라낸 프레임을 받아 인용된 타임스탬프와 프레임 미리보기를 붙여 답합니다.

환각 측정이 중요합니다. 세기 질문("방에 몇 명이 들어오나요?")과 동작 유형 질문("셰프가 젓기 전에 붓나요?")은 악명 높게 신뢰성이 떨어집니다. 묘사형 질문과 따로따로 정확도를 보고하세요.

## 아키텍처

```
video file / URL
      |
      v
PySceneDetect / TransNetV2  (scene segmentation)
      |
      +--- per-scene keyframe --- VLM caption + frame embedding
      |                            (Gemini 2.5 Pro / Qwen3-VL-Max / Molmo 2)
      |
      +--- audio channel --- Whisper-v3-turbo ASR + word timestamps
      |
      v
multi-vector Qdrant: {caption_emb, keyframe_emb, transcript_emb}
      |
query:
  dense queries against all three -> RRF merge -> top-k scenes
      |
      v
TimeLens / VideoITG temporal grounding (refine start/end within scene)
      |
      v
VLM synth: query + top scenes + frame previews
      |
      v
answer + (start, end) timestamps + frame thumbs + citations
```

## 스택

- 장면 분할: TransNetV2 (2024~26 최고 수준) 또는 PySceneDetect
- ASR: 단어 타임스탬프가 있는 faster-whisper 기반 Whisper-v3-turbo
- VLM 캡셔너 + 답변기: Gemini 2.5 Pro 또는 Qwen3-VL-Max 또는 Molmo 2
- 시간적 정합: TimeLens-100K 학습 어댑터 또는 VideoITG
- 인덱스: 멀티 벡터 지원(캡션 / 프레임 / 전사) Qdrant
- UI: HTML5 비디오 플레이어와 장면 썸네일을 갖춘 Next.js 15
- 평가: ActivityNet-QA, NeXT-GQA, 수작업 레이블 100문항 커스텀 셋
- 환각 벤치마크: 수작업 레이블을 붙인 세기·동작 유형 서브셋

```figure
cf-scene-index
```

## 직접 만들기

1. **흡수 워커.** YouTube URL이나 로컬 MP4를 받습니다. 필요하면 720p로 다운스케일합니다. `{video_id, file_path}`를 저장합니다.

2. **장면 분할.** TransNetV2나 PySceneDetect를 돌려 `[{scene_id, start_ms, end_ms, keyframe_path}]`를 만듭니다. 100시간 목표 기준 약 6k~8k 장면입니다.

3. **ASR 패스.** 오디오에 Whisper-v3-turbo를 돌리고; 단어 수준 타임스탬프를 내보내고; 장면별 전사 조각으로 자릅니다.

4. **VLM 캡셔닝.** 장면마다 키프레임과 짧은 캡션 템플릿을 갖고 Gemini 2.5 Pro(또는 Qwen3-VL-Max)를 호출합니다. 캡션 + 프레임 임베딩을 만듭니다.

5. **멀티 벡터 인덱스.** 이름 붙은 벡터 세 개를 가진 Qdrant 컬렉션. 페이로드: `{video_id, scene_id, start_ms, end_ms, keyframe_url}`.

6. **질의.** 자연어 질문이 세 개의 밀집(dense) 질의를 발사합니다; 상호 순위 융합으로 병합합니다; 상위 k=5 장면.

7. **시간적 정합.** TimeLens 스타일 어댑터를 상위 장면에 돌려 장면 안에서 (시작, 끝) 윈도우를 다듬습니다.

8. **VLM 종합.** 질문 + 상위 3개 장면 클립(이미지 또는 짧은 클립) + 전사를 갖고 Gemini 2.5 Pro를 호출합니다. `(video_id, start_ms, end_ms)` 인용을 요구합니다.

9. **평가.** ActivityNet-QA와 NeXT-GQA를 실행합니다. 100문항 커스텀 셋을 만듭니다. 전체 정확도 + 클래스별 분해(세기, 동작, 묘사)를 보고합니다.

## 사용해 보기

```
$ video-qa ask --url=https://youtube.com/watch?v=X "how many cars pass the intersection in the first minute?"
[scene]    23 scenes detected
[asr]      transcript complete, 4m12s
[index]    69 vectors written (23 scenes x 3)
[query]    top scene: scene 3 [01:32-01:54], confidence 0.84
[ground]   refined window: [00:12-00:58]
[synth]    gemini 2.5 pro, 1.4s
answer:    5 cars pass the intersection between 00:12 and 00:58.
citations: [scene 3: 00:12-00:58]
          [frame preview at 00:14, 00:27, 00:44, 00:51, 00:57]
```

## 출시하기

`outputs/skill-video-qa.md`가 산출물입니다. YouTube URL이나 업로드된 비디오가 주어지면 파이프라인이 장면을 인덱싱하고 타임스탬프 인용을 붙여 질문에 답합니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 시간적 정합 IoU | 홀드아웃 정합 셋에서의 교집합/합집합(IoU) |
| 20 | QA 정확도 | NeXT-GQA와 커스텀 100문항 |
| 20 | 흡수 처리량 | 지출 달러당 처리한 비디오 시간 |
| 20 | UI와 인용 UX | 타임스탬프 링크, 썸네일 스트립, 프레임으로 이동 |
| 15 | 환각 비율 | 세기·동작 유형 정확도를 따로따로 측정 |
| **100** | | |

## 연습 문제

1. 캡셔닝 패스에서 Gemini 2.5 Pro를 Qwen3-VL-Max로 바꿔 봅니다. 사람이 평가한 50장면 샘플에서 캡션 품질 변화를 보고합니다.

2. 장면별 프레임 임베딩을 멀티 벡터 대신 하나의 풀링된 벡터로 줄여 봅니다. 검색 퇴보(regression)를 측정합니다.

3. "엄격한 세기(counting strict)" 모드를 만듭니다: 종합기가 세어 나열한 각 항목에 타임스탬프를 붙이고 사용자가 클릭해 검증합니다. 사용자 검증이 환각을 줄이는지 측정합니다.

4. 흡수 비용을 벤치마크합니다: 세 가지 VLM 선택지에서 달러당 비디오 시간을 비교하고 최적점을 고릅니다.

5. 화자 분리 전사를 추가합니다: 오디오에 pyannote 화자 분리(diarization)를 돌리고 화자별 전사를 임베딩합니다. "Alice가 X에 대해 뭐라고 했나요?" 질의를 시연합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| 장면 분할 | "샷 감지" | 샷 경계에서 비디오를 장면 단위로 자르는 것 |
| 멀티 벡터 인덱스 | "캡션 + 프레임 + 전사" | 표현(representation)마다 이름 붙은 벡터를 둔 Qdrant 컬렉션 |
| 시간적 정합 | "정확히 언제 일어났나" | 질의 답변의 (시작, 끝) 윈도우를 다듬는 것 |
| 프레임 임베딩 | "시각 표현" | 키프레임의 벡터 임베딩; 장면-시각 유사성에 사용 |
| RRF 융합 | "상호 순위 융합" | 여러 순위 목록을 병합하는 전략; 클래식한 하이브리드 검색 트릭 |
| 세기 환각 | "잘못된 개수 세기" | "X가 몇 개" 질문에서 벌어지는 알려진 VLM 실패 모드 |
| ActivityNet-QA | "비디오 QA 벤치마크" | 긴 형식 비디오 QA 정확도 벤치마크 |

## 더 읽을거리

- [AI2 Molmo 2](https://allenai.org/blog/molmo2) — 오픈 VLM 체크포인트
- [TimeLens (CVPR 2026)](https://github.com/TencentARC/TimeLens) — 규모 있는 시간적 정합
- [Gemini Video 롱 컨텍스트](https://deepmind.google/technologies/gemini) — 호스팅 참고 사례
- [VideoDB](https://videodb.io) — 비디오용 CRUD API 참고 사례
- [Twelve Labs Marengo + Pegasus](https://www.twelvelabs.io) — 상용 참고 사례
- [TransNetV2](https://github.com/soCzech/TransNetV2) — 장면 분할 모델
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) — 클래식한 오픈소스 대안
- [ActivityNet-QA](https://arxiv.org/abs/1906.02467) — 참고 평가 벤치마크
