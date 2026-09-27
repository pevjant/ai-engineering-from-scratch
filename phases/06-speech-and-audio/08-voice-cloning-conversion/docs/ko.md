> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 음성 복제와 음성 변환

> 음성 복제(voice cloning)는 여러분의 텍스트를 남의 목소리로 읽어 줍니다. 음성 변환(voice conversion)은 여러분이 한 말의 내용은 그대로 둔 채 목소리만 다른 사람 것으로 바꿔 버립니다. 둘 다 같은 분해에 기반합니다: 화자의 정체성과 내용을 분리하는 것이죠.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 06 (화자 인식), 페이즈 6 · 07 (TTS)
**소요 시간:** 약 75분

## 문제 상황

2026년에는 5초짜리 오디오 클립만 있으면 가정용 GPU로 누구나의 목소리를 고품질로 복제할 수 있습니다. ElevenLabs, F5-TTS, OpenVoice v2, VoiceBox가 모두 제로샷 또는 퓨샷(few-shot) 복제를 제공합니다. 이 기술은 축복이기도 합니다(접근성 TTS, 더빙, 보조 음성) — 그리고 무기이기도 합니다(보이스피싱 사기, 정치 딥페이크, 지식재산권 침해).

밀접하게 연관된 두 작업이 있습니다:

- **음성 복제 (TTS 쪽):** 텍스트 + 5초 참조 목소리 → 그 목소리로 말하는 오디오.
- **음성 변환 (음성 쪽):** 원본 오디오(A라는 사람이 X를 말함) + B의 참조 목소리 → B가 X를 말하는 오디오.

둘 다 파형을 (내용, 화자, 운율)로 분해한 뒤, 한쪽에서 가져온 내용과 다른 쪽에서 가져온 화자 정보를 다시 조합합니다.

2026년 현재 여러분이 감수해야 하는 핵심 제약: **EU(AI Act, 2026년 8월 시행)와 캘리포니아(AB 2905, 2025년 시행)에서는 워터마킹과 동의 절차가 법적으로 요구됩니다.** 여러분의 파이프라인은 들을 수 없는 워터마크를 심어야 하고, 동의 없는 복제는 거부해야 합니다.

## 개념

![음성 복제 vs 변환: 분해하고, 화자를 바꾸고, 다시 조합한다](../assets/voice-cloning.svg)

**제로샷 복제.** 수천 명의 화자로 학습된 모델에 5초짜리 클립을 넘깁니다. 화자 인코더가 클립을 화자 임베딩으로 바꾸고, TTS 디코더가 그 임베딩과 텍스트를 조건 삼아 생성합니다.

사용 사례: F5-TTS (2024), YourTTS (2022), XTTS v2 (2024), OpenVoice v2 (2024).

**퓨샷 파인튜닝.** 목표 목소리를 5~30분 녹음합니다. 베이스 모델을 LoRA로 한 시간 파인튜닝하면, 품질이 "그럭저럭" 수준에서 "구분 불가" 수준으로 뛰어오릅니다. Coqui와 ElevenLabs 모두 이 패턴을 지원하고, 커뮤니티도 F5-TTS로 이 방식을 씁니다.

**음성 변환 (VC).** 두 계열이 있습니다:

- **인식-합성(recognition-synthesis).** ASR 비슷한 모델로 내용 표현(예: 소프트 음소 사후확률, PPG)을 뽑아낸 뒤, 목표 화자 임베딩으로 다시 합성합니다. 언어와 억양에 강합니다. KNN-VC (2023), Diff-HierVC (2023)가 이 방식입니다.
- **분리(disentanglement).** 병목(bottleneck)에서 내용·화자·운율을 잠재 공간에서 분리하는 오토인코더를 학습합니다. 추론 때 화자 임베딩을 갈아 끼우죠. 품질은 낮지만 빠릅니다. AutoVC (2019), VITS-VC 변형들이 이 방식입니다.

**뉴럴 코덱 기반 복제 (2024 이후).** VALL-E, VALL-E 2, NaturalSpeech 3, VoiceBox — 오디오를 SoundStream / EnCodec의 이산 토큰으로 취급하고, 코덱 토큰 위에서 커다란 자기회귀 또는 플로우 매칭 모델을 학습합니다. 짧은 프롬프트에서는 ElevenLabs에 버금가는 품질입니다.

### 윤리, 덧붙임이 아니라 기본 장착품

**워터마킹.** PerTh (Perth)와 SilentCipher (2024)는 사람이 느끼지 못하게 약 16~32비트짜리 ID를 오디오에 심습니다. 재인코딩, 스트리밍, 흔한 편집을 견딥니다. 프로덕션에 쓸 수 있는 오픈소스입니다.

**동의 게이트.** 복제된 출력마다 검증 가능한 동의 기록이 붙어야 합니다. "나, 로히트는, 2026-04-22자로, 이 목소리를 X 목적으로 쓰는 것을 승인합니다." 변조 탐지가 가능한 로그에 저장하세요.

**탐지.** AASIST, RawNet2, Wav2Vec2-AASIST가 탐지기로 제공됩니다. ASVspoof 2025 챌린지에 따르면 최신 탐지기가 ElevenLabs, VALL-E 2, Bark 출력 상대로 EER 0.8~2.3%를 기록했습니다.

### 수치 (2026)

| 모델 | 제로샷? | SECS (목표 유사도) | WER (전달력) | 파라미터 |
|-------|-----------|--------------------|--------------|--------|
| F5-TTS | 예 | 0.72 | 2.1% | 335M |
| XTTS v2 | 예 | 0.65 | 3.5% | 470M |
| OpenVoice v2 | 예 | 0.70 | 2.8% | 220M |
| VALL-E 2 | 예 | 0.77 | 2.4% | 370M |
| VoiceBox | 예 | 0.78 | 2.1% | 330M |

SECS가 0.70을 넘으면 대부분의 청취자는 목표 목소리와 구분하지 못합니다.

```figure
sp-voice-factorize
```

## 직접 만들어 보기

### 단계 1: 인식-합성으로 분해하기 (코드 데모는 main.py에)

```python
def clone_pipeline(ref_audio, text, target_embedder, tts_model):
    speaker_emb = target_embedder.encode(ref_audio)
    mel = tts_model(text, speaker=speaker_emb)
    return vocoder(mel)
```

개념은 간단합니다. 구현의 묵직함은 `tts_model`과 화자 인코더에 들어 있죠.

### 단계 2: F5-TTS로 제로샷 복제

```python
from f5_tts.api import F5TTS
tts = F5TTS()
wav = tts.infer(
    ref_file="rohit_5s.wav",
    ref_text="The quick brown fox jumps over the lazy dog.",
    gen_text="Please add milk and bread to my list.",
)
```

참조 전사 텍스트는 오디오와 정확히 일치해야 합니다. 어긋나면 정렬이 깨집니다.

### 단계 3: KNN-VC로 음성 변환

```python
import torch
from knnvc import KNNVC  # 2023년 모델, https://github.com/bshall/knn-vc
vc = KNNVC.load("wavlm-base-plus")
out_wav = vc.convert(source="my_voice.wav", target_pool=["alice_1.wav", "alice_2.wav"])
```

KNN-VC는 WavLM을 돌려 원본과 목표 풀(target pool)의 프레임별 임베딩을 뽑은 뒤, 원본 프레임 하나하나를 풀 안에서 가장 가까운 이웃으로 갈아끼웁니다. 파라미터가 없는(non-parametric) 방식이며, 목표 음성 1분이면 충분합니다.

### 단계 4: 워터마크 심기

```python
from silentcipher import SilentCipher
sc = SilentCipher(model="2024-06-01")
payload = b"consent_id:abc123;ts:1745353200"
watermarked = sc.embed(wav, sr=24000, message=payload)
detected = sc.detect(watermarked, sr=24000)   # 페이로드 바이트를 반환
```

페이로드 약 32비트. MP3 재인코딩과 가벼운 노이즈 이후에도 탐지됩니다.

### 단계 5: 동의 게이트

```python
def cloned_inference(text, ref_audio, consent_record):
    assert verify_signature(consent_record), "서명된 동의가 필요합니다"
    assert consent_record["speaker_id"] == hash_speaker(ref_audio)
    wav = tts.infer(ref_file=ref_audio, gen_text=text)
    wav = watermark(wav, payload=consent_record["id"])
    return wav
```

## 사용해 보기

2026년 스택:

| 상황 | 선택 |
|-----------|------|
| 5초 제로샷 복제, 오픈소스 | F5-TTS 또는 OpenVoice v2 |
| 상용 프로덕션 복제 | ElevenLabs Instant Voice Clone v2.5 |
| 음성 변환 (목소리 갈아끼우기) | KNN-VC 또는 Diff-HierVC |
| 다수 화자 파인튜닝 | StyleTTS 2 + 화자 어댑터 |
| 크로스링구얼 복제 | XTTS v2 또는 VALL-E X |
| 딥페이크 탐지 | Wav2Vec2-AASIST |

## 함정들

- **어긋난 참조 전사 텍스트.** F5-TTS 같은 모델은 참조 텍스트가 참조 오디오와 문장부호까지 완벽히 일치해야 합니다.
- **잔향 섞인 참조 음성.** 메아리는 복제물을 망칩니다. 마이크를 가까이 두고 건조한(잔향 없는) 환경에서 녹음하세요.
- **감정 불일치.** "쾌활한" 참조 음성으로 학습하면 모든 걸 쾌활하게 복제합니다. 참조 음성의 감정을 실제 용도에 맞추세요.
- **언어 새어 나가기.** 영어 화자를 복제한 뒤 프랑스어를 말하게 하면 억양이 그대로 따라오는 경우가 많습니다. 크로스링구얼 모델(XTTS, VALL-E X)을 쓰세요.
- **워터마크 없음.** 2026년 8월부터 EU에서는 법적으로 출시할 수 없습니다.

## 출시해 보기

`outputs/skill-voice-cloner.md`로 저장하세요. 동의 게이트 + 워터마크 + 품질 목표를 갖춘 복제 또는 변환 파이프라인을 설계합니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 교체 전후로 두 "화자" 사이의 코사인 유사도를 계산하며 화자 임베딩 교체를 시연합니다.
2. **보통.** OpenVoice v2로 자기 목소리를 복제해 보세요. 참조 음성과 복제물 사이의 SECS를 측정하고, Whisper로 CER도 측정합니다.
3. **어려움.** SilentCipher 워터마크를 복제물 20개에 심고, 128 kbps MP3 인코딩+디코딩을 통과시킨 뒤 페이로드를 탐지해 보세요. 비트 정확도(bit-accuracy)를 보고합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 제로샷 복제 | 5초면 충분 | 사전학습 모델 + 화자 임베딩. 학습 불필요. |
| PPG | 음성 사후확률 그램(Phonetic posteriorgram) | 언어 불가지론적인 내용 표현으로 쓰이는 프레임별 ASR 사후확률. |
| KNN-VC | 최근접 이웃 변환 | 원본 프레임을 목표 풀에서 가장 가까운 프레임으로 교체한다. |
| 뉴럴 코덱 TTS | VALL-E 스타일 | EnCodec/SoundStream 토큰 위의 자기회귀 모델. |
| 워터마크 | 들리지 않는 서명 | 오디오에 심어 재인코딩에도 살아남는 비트. |
| SECS | 복제 충실도 | 목표 화자 임베딩과 복제물 화자 임베딩 사이의 코사인. |
| AASIST | 딥페이크 탐지기 | 안티 스푸핑 모델. 합성 음성을 탐지한다. |

## 더 읽을거리

- [Chen 외 (2024). F5-TTS](https://arxiv.org/abs/2410.06885) — 오픈소스 SOTA 제로샷 복제.
- [Baevski 외 / Microsoft (2023). VALL-E](https://arxiv.org/abs/2301.02111)와 [VALL-E 2 (2024)](https://arxiv.org/abs/2406.05370) — 뉴럴 코덱 TTS.
- [Qian 외 (2019). AutoVC](https://arxiv.org/abs/1905.05879) — 분리(disentanglement) 기반 음성 변환.
- [Baas, Waubert de Puiseau, Kamper (2023). KNN-VC](https://arxiv.org/abs/2305.18975) — 검색 기반 음성 변환.
- [SilentCipher (2024) — 오디오 워터마킹](https://github.com/sony/silentcipher) — 프로덕션급 32비트 오디오 워터마크.
- [ASVspoof 2025 결과](https://www.asvspoof.org/) — 탐지기 vs 합성기의 군비 경쟁, 2026년 갱신.
