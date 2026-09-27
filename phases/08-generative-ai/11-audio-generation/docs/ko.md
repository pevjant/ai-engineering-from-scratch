> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 오디오 생성

> 오디오는 16-48 kHz의 1차원 신호입니다. 5초짜리 클립은 8만~24만 개 샘플입니다. 그 시퀀스를 직접 어텐션하는 트랜스포머는 없습니다. 2026년 모든 프로덕션 오디오 모델의 해법은 같습니다: 신경 코덱(Encodec, SoundStream, DAC)이 오디오를 50-75 Hz의 이산 토큰으로 압축하고, 트랜스포머나 확산 모델이 그 토큰을 생성합니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 02(오디오 특성), 페이즈 6 · 04(ASR), 페이즈 8 · 06(DDPM)
**시간:** 약 45분

## 문제 상황

세 가지 오디오 생성 과제:

1. **텍스트-음성(TTS).** 텍스트가 주어지면 음성을 만듭니다. 깨끗한 음성은 협대역이고 강한 음운 구조가 있어 토큰 위의 트랜스포머로 잘 풀립니다. VALL-E(Microsoft), NaturalSpeech 3, ElevenLabs, OpenAI TTS.
2. **음악 생성.** 프롬프트(텍스트, 멜로디, 코드 진행, 장르)가 주어지면 음악을 만듭니다. 훨씬 넓은 분포입니다. MusicGen(Meta), Stable Audio 2.5, Suno v4, Udio, Riffusion.
3. **음향 효과 / 사운드 디자인.** 프롬프트가 주어지면 배경음이나 폴리(Foley)를 만듭니다. AudioGen, AudioLDM 2, Stable Audio Open.

세 가지 모두 같은 기반 위에서 돌아갑니다: 신경 오디오 코덱 + 토큰-AR 또는 확산 생성기.

## 개념

![오디오 생성: 코덱 토큰 + 트랜스포머 또는 확산](../assets/audio-generation.svg)

### 신경 오디오 코덱

Encodec(Meta, 2022), SoundStream(Google, 2021), Descript Audio Codec(DAC, 2023). 합성곱 인코더가 파형을 타임스텝별 벡터로 압축하고, 잔차 벡터 양자화(RVQ)가 각 벡터를 K개 코드북 인덱스의 계단식 배열로 바꿉니다. 디코더는 그 역을 합니다. 24 kHz 오디오를 75 Hz의 8개 RVQ 코드북으로 2 kbps = 초당 600 토큰.

```
waveform (16000 samples/sec)
    └─ encoder conv ─┐
                     ├─ RVQ layer 1 → indices at 75 Hz
                     ├─ RVQ layer 2 → indices at 75 Hz
                     ├─ ...
                     └─ RVQ layer 8
```

### 그 위에 얹히는 두 생성 패러다임

**토큰-자기회귀.** RVQ 토큰을 시퀀스로 펼쳐 디코더 전용 트랜스포머를 돌립니다. MusicGen은 "지연 병렬(delayed parallel)" 방식으로 스트림별 오프셋을 두고 K개 코드북 스트림을 병렬로 내놓습니다. VALL-E는 텍스트 프롬프트 + 3초 음성 샘플에서 음성 토큰을 생성합니다.

**잠재 확산.** 코덱 토큰을 연속 잠재로 묶거나 범주형 확산으로 모델링합니다. Stable Audio 2.5는 연속 오디오 잠재 위의 플로우 매칭을 씁니다. AudioLDM 2는 텍스트-멜-오디오 확산을 씁니다.

2024~2026년 흐름: 음악은 플로우 매칭이 이기고 있고(더 빠른 추론, 더 깨끗한 샘플), 음성은 본질적으로 인과적이고 스트리밍에 유리해서 토큰-AR이 여전히 지배합니다.

## 프로덕션 지형

| 시스템 | 과제 | 백본 | 지연 시간 |
|--------|------|----------|---------|
| ElevenLabs V3 | TTS | 토큰-AR + 신경 보코더 | 첫 토큰 약 300ms |
| OpenAI GPT-4o audio | 전이중 음성 | 엔드투엔드 멀티모달 AR | 약 200ms |
| NaturalSpeech 3 | TTS | 잠재 플로우 매칭 | 논스트리밍 |
| Stable Audio 2.5 | 음악 / SFX | 오디오 잠재 위의 DiT + 플로우 매칭 | 1분 클립에 약 10s |
| Suno v4 | 완곡 | 비공개; 토큰-AR 추정 | 곡당 약 30s |
| Udio v1.5 | 완곡 | 비공개 | 곡당 약 30s |
| MusicGen 3.3B | 음악 | Encodec 32kHz 위의 토큰-AR | 실시간 |
| AudioCraft 2 | 음악 + SFX | 플로우 매칭 | 5s 클립에 약 5s |
| Riffusion v2 | 음악 | 스펙트로그램 확산 | 약 10s |

```figure
score-matching
```

## 만들어 보기

`code/main.py`는 핵심 아이디어를 시뮬레이션합니다: 서로 다른 두 "스타일"(스타일 A는 낮은 토큰과 높은 토큰의 교대, 스타일 B는 단조 상승)에서 만든 합성 "오디오 토큰" 시퀀스로 작은 다음 토큰 트랜스포머를 학습시킵니다. 스타일로 조건화하고 샘플링합니다.

### 단계 1: 합성 오디오 토큰

```python
def make_tokens(style, length, vocab_size, rng):
    if style == 0:  # "음성스러움": 교대
        return [i % vocab_size for i in range(length)]
    # "음악스러움": 상승 램프
    return [(i * 3) % vocab_size for i in range(length)]
```

### 단계 2: 작은 토큰 예측기 학습

스타일로 조건화된 바이그램 스타일 예측기입니다. 요점은 패턴입니다: 코덱 토큰 → 교차 엔트로피 학습 → 자기회귀 샘플링.

### 단계 3: 조건부 샘플링

스타일 토큰과 시작 토큰이 주어지면 예측 분포에서 다음 토큰을 샘플링합니다. 20-40 토큰을 이어 갑니다.

## 함정들

- **코덱 품질이 출력 품질의 상한입니다.** 코덱이 소리를 충실히 표현하지 못하면 생성기가 아무리 좋아도 소용이 없습니다. 현재 오픈 최고는 DAC입니다.
- **RVQ 오차 누적.** 각 RVQ 층은 이전 층의 잔차를 모델링합니다. 1층의 오차가 전파됩니다. 상위 층에서는 온도 0 샘플링이 도움이 됩니다.
- **음악적 구조.** 30초의 토큰은 75 Hz 기준 2만 토크 이상입니다. 트랜스포머에게 어렵습니다. MusicGen은 슬라이딩 윈도우 + 프롬프트 연속을, Stable Audio는 더 짧은 클립 + 크로스페이드를 씁니다.
- **경계에서의 아티팩트.** 생성된 클립 사이의 크로스페이드는 신중한 overlap-add가 필요합니다.
- **깨끗한 데이터에 대한 식욕.** 음악 생성기는 수만 시간의 라이선스 음악이 필요합니다. Suno / Udio RIAA 소송(2024)이 이를 수면 위로 끌어올렸습니다.
- **목소리 복제 윤리.** 3초 샘플 하나와 텍스트 프롬프트면 VALL-E / XTTS / ElevenLabs가 목소리를 복제하기에 충분합니다. 모든 프로덕션 모델에는 악용 감지 + 옵트아웃 목록이 필요합니다.

## 사용해 보기

| 과제 | 2026년 스택 |
|------|------------|
| 상업용 TTS | ElevenLabs, OpenAI TTS, 또는 Azure Neural |
| 목소리 복제(동의 확인됨) | XTTS v2(오픈) 또는 ElevenLabs Pro |
| 배경 음악, 빠르게 | Stable Audio 2.5 API, Suno, 또는 Udio |
| 가사 있는 음악 | Suno v4 또는 Udio v1.5 |
| 음향 효과 / 폴리 | AudioCraft 2, ElevenLabs SFX, 또는 Stable Audio Open |
| 실시간 음성 에이전트 | GPT-4o realtime 또는 Gemini Live |
| 오픈 가중치 음악 연구 | MusicGen 3.3B, Stable Audio Open 1.0, AudioLDM 2 |
| 더빙 / 번역 | HeyGen, ElevenLabs Dubbing |

## 출시하기

`outputs/skill-audio-brief.md`로 저장하세요. 이 스킬은 오디오 브리프(과제, 길이, 스타일, 목소리, 라이선스)를 받아 모델 + 호스팅, 프롬프트 형식(장르 태그, 스타일 묘사, 구조 표식), 코덱 + 생성기 + 보코더 체인, 시드 프로토콜, 평가 계획(MOS / CLAP score / TTS의 CER / 사용자 A/B)을 출력합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하고 스타일을 명시적으로 지정하세요. 생성된 시퀀스가 그 스타일의 패턴과 일치하는지 확인합니다.
2. **보통.** 지연 병렬 디코딩을 추가해 보세요: 1스텝 오프셋을 유지해야 하는 2개 토큰 스트림을 시뮬레이션하고, 공동 예측기를 학습시킵니다.
3. **어려움.** HuggingFace transformers로 MusicGen-small을 로컬에서 돌려 보세요. 서로 다른 프롬프트 세 개로 10초 클립을 생성하고, 스타일 순응도를 A/B 테스트합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 코덱 | "신경 압축" | 오디오용 인코더 / 디코더; 전형적인 출력은 50-75 Hz 토큰. |
| RVQ | "잔차 VQ" | K개 양자화기의 계단식 배열; 각각이 이전 것의 잔차를 모델링합니다. |
| 토큰 | "코덱 기호 하나" | 코드북을 가리키는 이산 인덱스; 보통 1024 또는 2048. |
| 지연 병렬 | "오프셋 코드북" | 시퀀스 길이를 줄이려고 K개 토큰 스트림을 어긋난 오프셋으로 출력. |
| 플로우 매칭 | "2024년 오디오의 승자" | 확산보다 곧은 경로를 그리는 대안; 더 빠른 샘플링. |
| 보이스 프롬프트 | "3초 샘플" | 복제된 목소리를 조종하는 화자 임베딩 또는 토큰 접두사. |
| 멜 스펙트로그램 | "그 그림" | 로그 크기 지각 스펙트로그램; 많은 TTS 시스템이 사용합니다. |
| 보코더 | "멜에서 파형으로" | 멜 스펙트로그램을 다시 오디오로 바꾸는 신경 부품. |

## 프로덕션 노트: 오디오는 스트리밍의 문제입니다

오디오는 사용자가 *생성되는 대로* 도착하기를 기대하는 유일한 출력 모달리티입니다. 한꺼번에 오는 게 아니죠. 프로덕션 용어로 이것은 TPOT(Time Per Output Token, 출력 토큰당 시간)가 중요하다는 뜻입니다 — 목표 처리량은 사용자의 듣는 속도이지 읽는 속도가 아니니까요. 약 75 토큰/초(Encodec)로 토큰화된 16kHz 오디오라면, 서버는 재생이 끊기지 않도록 사용자당 최소 75 토큰/초를 생성해야 합니다.

아키텍처적 귀결 두 가지:

- **플로우 매칭 오디오 모델은 간단히 스트리밍할 수 없습니다.** Stable Audio 2.5와 AudioCraft 2는 고정된 클립 길이를 한 번에 렌더링합니다. 스트리밍하려면 클립을 청크로 자르고 경계를 겹쳐야 합니다 — 슬라이딩 윈도우 확산을 떠올리면 됩니다 — 코덱 AR 모델 대비 100-300ms의 지연 오버헤드가 추가됩니다.

제품이 "라이브 음성 채팅"이나 "실시간 음악 이어 만들기"라면 코덱 AR 경로를 고르세요. "제출 시 30초 클립 렌더링"이라면 플로우 매칭이 품질과 총 지연 시간에서 이깁니다.

## 더 읽을거리

- [Défossez 외 (2022). Encodec: High Fidelity Neural Audio Compression](https://arxiv.org/abs/2210.13438) — 코덱의 표준.
- [Zeghidour 외 (2021). SoundStream](https://arxiv.org/abs/2107.03312) — 최초로 널리 쓰인 신경 오디오 코덱.
- [Kumar 외 (2023). High-Fidelity Audio Compression with Improved RVQGAN (DAC)](https://arxiv.org/abs/2306.06546) — DAC.
- [Wang 외 (2023). Neural Codec Language Models are Zero-Shot Text to Speech Synthesizers (VALL-E)](https://arxiv.org/abs/2301.02111) — VALL-E.
- [Copet 외 (2023). Simple and Controllable Music Generation (MusicGen)](https://arxiv.org/abs/2306.05284) — MusicGen.
- [Liu 외 (2023). AudioLDM 2: Learning Holistic Audio Generation with Self-supervised Pretraining](https://arxiv.org/abs/2308.05734) — AudioLDM 2.
- [Stability AI (2024). Stable Audio 2.5](https://stability.ai/news/introducing-stable-audio-2-5) — 플로우 매칭을 쓰는 2025년 텍스트-음악.
