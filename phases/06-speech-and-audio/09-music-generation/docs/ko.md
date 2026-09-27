> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 음악 생성 — MusicGen, Stable Audio, Suno, 그리고 라이선스 대지진

> 2026년 음악 생성 시장: 상용은 Suno v5와 Udio v4가 지배하고, 오픈소스는 MusicGen, Stable Audio Open, ACE-Step이 이끕니다. 기술적 문제는 거의 해결됐습니다. 법적 문제(워너 뮤직 5억 달러 합의, UMG 합의)가 2025~2026년 이 분야를 다시 만들었죠.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 02 (스펙트로그램), 페이즈 4 · 10 (확산 모델)
**소요 시간:** 약 75분

## 문제 상황

텍스트 → 가사와 보컬, 구조까지 갖춘 30초에서 4분짜리 음악 클립. 세 개의 하위 문제로 나뉩니다:

1. **반주(instrumental) 생성.** "따뜻한 키보드 소리가 깔린 로파이 힙합 드럼" 같은 텍스트 → 오디오. MusicGen, Stable Audio, AudioLDM.
2. **노래 생성 (보컬 + 가사 포함).** "비 내리는 텍사스 밤에 관한 컨트리 노래" → 완성된 노래. Suno, Udio, YuE, ACE-Step.
3. **조건부 / 제어 가능한 생성.** 기존 클립 이어 만들기, 브리지 부분 다시 만들기, 장르 바꾸기, 스템 분리, 인페인팅. Udio의 인페인팅 + 스템 분리가 2026년 따라잡아야 할 기능입니다.

## 개념

![음악 생성: 토큰-LM vs 확산 모델, 2026년 모델 지도](../assets/music-generation.svg)

### 뉴럴 코덱 토큰 위의 토큰 LM

Meta의 **MusicGen** (2023, MIT)과 수많은 파생 모델: 텍스트/멜로디 임베딩을 조건으로 삼아 EnCodec 토큰(32 kHz, 4개 코드북)을 자기회귀적으로 예측하고, EnCodec으로 디코딩합니다. 3억~33억(300M~3.3B) 파라미터. 든든한 베이스라인이지만 30초를 넘기면 버벅입니다.

**ACE-Step** (오픈소스, 2026년 4월 4B XL 공개)은 이 방식을 가사 조건부 풀노래 생성으로 확장합니다. 오픈 커뮤니티가 가진 Suno와 가장 가까운 존재입니다.

### 멜 또는 잠재 공간 위의 확산 모델

**Stable Audio (2023)**와 **Stable Audio Open (2024)**: 압축된 오디오 잠재 공간 위의 잠재 확산(latent diffusion). 루프, 사운드 디자인, 앰비언트 텍스처에 강합니다. 구조가 잡힌 풀노래에는 약합니다.

**AudioLDM / AudioLDM2**: T2I 스타일 잠재 확산을 텍스트-투-오디오로 일반화한 것. 음악, 효과음, 음성까지 다룹니다.

### 하이브리드 (프로덕션용) — Suno, Udio, Lyria

가중치 비공개. 자기회귀 코덱 LM + 확산 기반 보코더에 전용 보컬 / 드럼 / 멜로디 헤드를 얹은 구조로 추정됩니다. Suno v5 (2026)는 ELO 1293의 품질 리더입니다. Udio v4는 인페인팅 + 스템 분리(베이스, 드럼, 보컬을 따로 내려받기)를 더했습니다.

### 평가

- **FAD (Fréchet Audio Distance).** VGGish 또는 PANNs 특성을 써서 생성 오디오 분포와 실제 오디오 분포 사이의 임베딩 수준 거리. 낮을수록 좋습니다. MusicGen small은 MusicCaps에서 FAD 4.5, SOTA는 약 3.0입니다.
- **음악성 (주관).** 사람의 선호도. Suno v5의 ELO 1293이 선두입니다.
- **텍스트-오디오 정렬.** 프롬프트와 출력 사이의 CLAP 점수.
- **음악성 아티팩트.** 박자에서 어긋나는 전환, 보컬 프레이즈 흐름, 30초 넘으면 무너지는 구조.

## 2026년 모델 지도

| 모델 | 파라미터 | 길이 | 보컬 | 라이선스 |
|-------|--------|--------|--------|---------|
| MusicGen-large | 3.3B | 30초 | 없음 | MIT |
| Stable Audio Open | 1.2B | 47초 | 없음 | Stability 비상용 |
| ACE-Step XL (2026년 4월) | 4B | &gt; 2분 | 있음 | Apache-2.0 |
| YuE | 7B | &gt; 2분 | 있음, 다국어 | Apache-2.0 |
| Suno v5 (비공개) | ? | 4분 | 있음, ELO 1293 | 상용 |
| Udio v4 (비공개) | ? | 4분 | 있음 + 스템 | 상용 |
| Google Lyria 3 (비공개) | ? | 실시간 | 있음 | 상용 |
| MiniMax Music 2.5 | ? | 4분 | 있음 | 상용 API |

## 법적 환경 (2025-2026)

- **워너 뮤직 vs Suno 합의.** 5억 달러. WMG가 이제 Suno에서 AI 유사성, 음악 권리, 사용자 생성 트랙에 대한 감독권을 갖습니다. Udio에도 유사한 UMG 합의가 있습니다.
- **EU AI Act** + **캘리포니아 SB 942**: AI 생성 음악은 공개(disclosure)해야 합니다.
- **Riffusion / MusicGen** (MIT)은 컴플라이언스 부담이 없지만 상용 등급 보컬도 없습니다.

안전하게 출시할 수 있는 패턴:

1. 반주만 생성하기 (MusicGen, Stable Audio Open, MIT/CC0 출력).
2. 상용 API 사용 (Suno, Udio, ElevenLabs Music), 생성 건당 라이선스.
3. 소유하거나 라이선스를 산 카탈로그로 직접 학습 (대부분의 기업이 결국 여기로 옵니다).
4. 생성물에 워터마크 + 메타데이터 태그 붙이기.

```figure
sp-codec-tokens
```

## 직접 만들어 보기

### 단계 1: MusicGen으로 생성하기

```python
from audiocraft.models import MusicGen
import torchaudio

model = MusicGen.get_pretrained("facebook/musicgen-small")
model.set_generation_params(duration=10)
wav = model.generate(["upbeat synthwave with driving drums, 128 BPM"])
torchaudio.save("out.wav", wav[0].cpu(), 32000)
```

세 가지 크기: `small` (300M, 빠름), `medium` (1.5B), `large` (3.3B). "아이디어가 통하는지" 보는 데는 small이면 충분합니다.

### 단계 2: 멜로디 조건부 생성

```python
melody, sr = torchaudio.load("humming.wav")
wav = model.generate_with_chroma(
    ["jazz piano cover"],
    melody.squeeze(),
    sr,
)
```

MusicGen-melody는 크로마그램(chromagram)을 받아 곡조는 지키고 음색만 바꿉니다. "이 멜로디를 현악 사중주로 바꿔 줘"에 딱입니다.

### 단계 3: FAD 평가

```python
from frechet_audio_distance import FrechetAudioDistance
fad = FrechetAudioDistance()

fad.get_fad_score("generated_folder/", "reference_folder/")
```

VGGish 임베딩 거리를 계산합니다. 장르 수준의 회귀 테스트에는 유용하지만, 사람 귀를 대신하지는 못합니다.

### 단계 4: LLM-음악 워크플로에 얹기

레슨 7~8의 아이디어와 결합합니다:

```python
prompt = "Write a 30-second jazz loop. Describe the drums, bass, and piano voicing."
description = llm.complete(prompt)
music = musicgen.generate([description], duration=30)
```

## 사용해 보기

| 목표 | 스택 |
|------|-------|
| 반주 사운드 디자인 | Stable Audio Open |
| 게임 / 어댑티브 음악 | Google Lyria RealTime (비공개) |
| 보컬 있는 풀노래 (상용) | 명시적 라이선스를 맺은 Suno v5 또는 Udio v4 |
| 보컬 있는 풀노래 (오픈) | ACE-Step XL 또는 YuE |
| 짧은 광고 징글 | 허밍 참조로 멜로디 조건부 MusicGen |
| 뮤직비디오 배경 | MusicGen + Stable Video Diffusion |

## 2026년에도 여전히 출시되는 함정들

- **저작권 세탁 프롬프트.** "Taylor Swift 스타일의 노래" — 상용 Suno/Udio는 이제 걸러 주지만, 오픈 모델은 걸러 주지 않습니다. 자체 필터 목록을 만드세요.
- **30초 넘으면 반복 / 흐름 이탈.** 자기회귀 모델은 같은 구간을 반복합니다. 여러 생성물을 크로스페이드로 잇거나, 구조적 일관성이 필요하면 ACE-Step을 쓰세요.
- **템포 이탈.** 모델이 BPM에서 벗어납니다. 프롬프트에 BPM 태그를 넣고, librosa의 `beat_track`으로 후처리 필터를 거세요.
- **보컬 알아듣기.** Suno는 훌륭하지만, 오픈 모델은 발음이 뭉개지는 경우가 많습니다. 가사가 중요하다면 상용 API를 쓰거나 파인튜닝하세요.
- **모노 출력.** 오픈 모델은 모노 또는 가짜 스테레오를 내놓습니다. 제대로 된 스테레오 복원(ezst, Cartesia의 스테레오 확산)으로 업그레이드하세요.

## 출시해 보기

`outputs/skill-music-designer.md`로 저장하세요. 음악 생성 배포를 위해 모델, 라이선스 전략, 길이 / 구조 계획, 공개(disclosure) 메타데이터를 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. "생성적인" 코드 진행 + 드럼 패턴을 ASCII 기호로 만들어 내는 — 음악 생성 만화입니다. 원하면 아무 MIDI 렌더러로 재생해 보세요.
2. **보통.** `audiocraft`를 설치하고, MusicGen-small로 4개 장르 프롬프트에서 10초 클립을 생성한 뒤, 참조 장르 세트 대비 FAD를 측정합니다.
3. **어려움.** ACE-Step(또는 MusicGen-melody)으로 같은 곡조를 서로 다른 음색 프롬프트로 3가지 변주해 보세요. CLAP 유사도를 계산해 프롬프트와의 정렬을 확인합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| FAD | 오디오 버전 FID | 실제 vs 생성 오디오의 임베딩 분포 사이 Fréchet 거리. |
| 크로마그램 (Chromagram) | 음높이로 본 멜로디 | 프레임별 12차원 벡터. 멜로디 조건부 생성의 입력. |
| 스템 (Stems) | 악기별 트랙 | 베이스 / 드럼 / 보컬 / 멜로디를 WAV로 분리한 것. |
| 인페인팅 (Inpainting) | 구간 다시 만들기 | 시간 구간을 마스크하면 모델이 그 부분만 다시 생성한다. |
| CLAP | 텍스트-오디오 CLIP | 대조 학습 오디오-텍스트 임베딩. 텍스트-오디오 정렬을 평가한다. |
| EnCodec | 음악 코덱 | MusicGen이 쓰는 Meta의 뉴럴 코덱. 32 kHz, 4개 코드북. |

## 더 읽을거리

- [Copet 외 (2023). MusicGen](https://arxiv.org/abs/2306.05284) — 오픈 자기회귀 벤치마크.
- [Evans 외 (2024). Stable Audio Open](https://arxiv.org/abs/2407.14358) — 사운드 디자인의 기본 선택.
- [ACE-Step](https://github.com/ace-step/ACE-Step) — 오픈 4B 풀노래 생성기, 2026년 4월.
- [Suno v5 플랫폼 문서](https://suno.com) — 상용 품질 리더.
- [AudioLDM2](https://arxiv.org/abs/2308.05734) — 음악 + 효과음을 위한 잠재 확산 모델.
- [WMG-Suno 합의 보도](https://www.musicbusinessworldwide.com/suno-warner-music-settlement/) — 2025년 11월의 선례.
