# 음성 안티스푸핑 & 오디오 워터마킹 — ASVspoof 5, AudioSeal, WaveVerify

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 음성 복제 기술은 방어 기술보다 먼저 세상에 나왔습니다. 2026년의 프로덕션(운영 환경) 음성 시스템에는 두 가지가 필요합니다: 진짜 음성과 가짜 음성을 가려내는 탐지기(AASIST, RawNet2), 그리고 압축과 편집을 견뎌내는 워터마크(AudioSeal). 둘 다 갖추지 않고는 음성 복제 기능을 출시하지 마세요.

**유형:** 빌드
**언어:** Python
**선수 지식:** 페이즈 6 · 06 (화자 인식), 페이즈 6 · 08 (음성 복제)
**시간:** 약 75분

## 문제 상황

서로 연관된 세 가지 방어책:

1. **안티스푸핑 / 딥페이크 탐지.** 오디오 클립이 주어졌을 때 합성 음성인지 진짜인지 판별합니다. ASVspoof 벤치마크(ASVspoof 2019 → 2021 → 5)가 이 분야의 표준입니다.
2. **오디오 워터마킹.** 생성된 오디오 안에 사람이 느낄 수 없는 신호를 심어 두고, 나중에 탐지기가 그 신호를 꺼내 확인할 수 있게 합니다. AudioSeal(Meta)과 WavMark가 공개된 선택지입니다.
3. **인증 기반 출처 추적.** 오디오 파일에 암호학적 서명 + 메타데이터를 붙입니다. C2PA / Content Authenticity Initiative가 그 예입니다.

탐지는 협조해 주지 않는 공격자를 막는 방어책입니다. 워터마킹은 규제 준수를 위한 방어책입니다 — AI로 생성한 오디오는 AI 생성물임을 식별할 수 있어야 합니다. 2026년에는 둘 다 필요합니다.

## 핵심 개념

![안티스푸핑 vs 워터마킹 vs 출처 추적 — 세 겹의 방어선](../assets/spoofing-watermark.svg)

### ASVspoof 5 — 2024-2025 벤치마크

이전 대회들과 비교한 가장 큰 변화:

- **크라우드소싱 데이터**(스튜디오에서 녹음한 깨끗한 음성이 아님) — 실제와 비슷한 조건.
- **약 2000명의 화자**(이전에는 약 100명).
- **32가지 공격 알고리즘.** TTS + 음성 변환 + 적대적 섭동.
- **두 개의 트랙.** 대책(CM, Countermeasure) 단독 탐지; 생체 인식 시스템용 스푸핑 강건 ASV(SASV).

ASVspoof 5의 최고 수준 성능: 약 7.23% EER. 더 오래된 ASVspoof 2019 LA에서는: 0.42% EER. 실제 환경 배포 시: 세상에 나와 있는 클립에서는 5-10% EER을 예상해야 합니다.

### AASIST와 RawNet2 — 탐지 모델 계열

**AASIST**(2021년, 2026년까지 계속 업데이트). 스펙트럼 특성(feature)에 그래프 어텐션을 적용한 모델. 현재 ASVspoof 5 대책 과제의 SOTA(최고 수준 기법).

**RawNet2.** 원시 파형(raw waveform) 위에 합성곱 프런트엔드 + TDNN 백본을 얹은 구조. 더 단순한 베이스라인; 파인튜닝을 하면 여전히 경쟁력이 있습니다.

**NeXt-TDNN + SSL 특성.** 2025년 변형: ECAPA 스타일 + WavLM 특성 + focal loss. ASVspoof 2019 LA에서 0.42% EER을 달성했습니다.

### AudioSeal — 2024년 워터마크의 기본 선택지

Meta의 **AudioSeal**(2024년 1월, v0.2는 2024년 12월). 핵심 설계:

- **위치 특정 가능.** 16 kHz 샘플 해상도(1/16000초)로 프레임마다 워터마크를 탐지합니다.
- **생성기 + 탐지기를 함께 학습.** 생성기는 들을 수 없는 신호를 심는 법을, 탐지기는 여러 증강(augmentation)을 통과한 뒤에도 그 신호를 찾는 법을 배웁니다.
- **강건함.** MP3 / AAC 압축, EQ, 속도 변화 ±10%, 노이즈 믹스 +10 dB SNR을 견뎌냅니다.
- **빠름.** 탐지기가 실시간의 485배 속도로 동작; WavMark보다 1000배 빠릅니다.
- **용량.** 16비트 페이로드(모델 ID, 생성 타임스탬프, 사용자 ID 등을 담을 수 있음)를 발화(utterance)마다 심을 수 있습니다.

### WavMark

AudioSeal 이전의 공개 베이스라인. 가역 신경망(invertible neural network) 기반이며 초당 32비트를 담습니다. 문제점:

- 동기화 위치를 무차별 대입으로 찾느라 느립니다.
- 가우시안 노이즈나 MP3 압축으로 제거될 수 있습니다.
- 실시간 처리에 부적합합니다.

### WaveVerify (2025년 7월)

AudioSeal의 약점 — 특히 시간축 조작(방향 반전, 속도 변경) — 을 해결합니다. FiLM 기반 생성기 + Mixture-of-Experts 탐지기를 사용합니다. 표준 공격에서는 AudioSeal과 대등하면서 시간축 편집까지 처리합니다.

### 공격자가 노리는 틈

AudioMarkBench에 따르면: "피치 시프트(pitch shift) 상황에서는 모든 워터마크의 비트 복원 정확도(Bit Recovery Accuracy)가 0.6 미만으로 떨어지는데, 이는 사실상 워터마크가 완전히 제거되었음을 뜻합니다." **피치 시프트가 만능 공격입니다.** 2026년 기준 어떤 워터마크도 공격적인 피치 변조에는 완전히 버티지 못합니다. 그래서 워터마킹과 함께 탐지(AASIST)가 필요한 것입니다.

### C2PA / Content Authenticity Initiative

ML 기법이 아니라 매니페스트 형식입니다. 오디오 파일이 생성 도구, 작성자, 날짜에 관한 암호학적으로 서명된 메타데이터를 함께 갖고 다닙니다. Audobox / Seamless가 이를 사용합니다. 출처 추적에는 좋지만, 악의적인 행위자가 다시 인코딩하면서 메타데이터를 벗겨내면 아무 소용이 없습니다.

```figure
v4-audio-watermark
```

## 만들어 보기

### 단계 1: 간단한 스펙트럼 특성 탐지기 (장난감 수준)

```python
def spectral_rolloff(spec, percentile=0.85):
    cum = 0
    total = sum(spec)
    if total == 0:
        return 0
    threshold = total * percentile
    for k, v in enumerate(spec):
        cum += v
        if cum >= threshold:
            return k
    return len(spec) - 1

def is_suspicious(audio):
    spec = magnitude_spectrum(audio)
    rolloff = spectral_rolloff(spec)
    return rolloff / len(spec) > 0.92
```

합성 음성은 고주파 에너지가 비정상적으로 평평한 경우가 많습니다. 프로덕션 탐지기는 이런 방식이 아니라 AASIST를 씁니다. 그래도 직관은 이와 같습니다.

### 단계 2: AudioSeal 심기 + 탐지하기

```python
from audioseal import AudioSeal
import torch

generator = AudioSeal.load_generator("audioseal_wm_16bits")
detector = AudioSeal.load_detector("audioseal_detector_16bits")

audio = load_wav("generated.wav", sr=16000)[None, None, :]
payload = torch.tensor([[1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0]])
watermark = generator.get_watermark(audio, sample_rate=16000, message=payload)
watermarked = audio + watermark

result, decoded_payload = detector.detect_watermark(watermarked, sample_rate=16000)
# result: [0, 1] 사이의 실수 — 워터마크가 존재할 확률
# decoded_payload: 16비트; 심은 페이로드와 일치하는지 비교
```

### 단계 3: 평가 — EER

```python
def eer(real_scores, fake_scores):
    thresholds = sorted(set(real_scores + fake_scores))
    best = (1.0, 0.0)
    for t in thresholds:
        far = sum(1 for s in fake_scores if s >= t) / len(fake_scores)
        frr = sum(1 for s in real_scores if s < t) / len(real_scores)
        if abs(far - frr) < best[0]:
            best = (abs(far - frr), (far + frr) / 2)
    return best[1]
```

### 단계 4: 프로덕션 통합

```python
def safe_tts(text, voice, clone_reference=None):
    if clone_reference is not None:
        verify_consent(user_id, clone_reference)
    audio = tts_model.synthesize(text, voice)
    audio_with_wm = audioseal_embed(audio, payload=build_payload(user_id, model_id))
    manifest = c2pa_sign(audio_with_wm, user_id, timestamp=now())
    return audio_with_wm, manifest
```

모든 생성 결과물에는 (1) 워터마크, (2) 서명된 매니페스트, (3) 보존 정책을 준수하는 감사 로그가 함께 나갑니다.

## 활용하기

| 사용 사례 | 방어책 |
|----------|---------|
| TTS / 음성 복제 출시 | 모든 출력물에 AudioSeal 심기(타협 불가) |
| 생체 음성 잠금 해제 | AASIST + ECAPA 앙상블; 라이브니스 챌린지(liveness challenge) |
| 콜센터 사기 탐지 | 수신 전화의 20% 샘플에 AASIST 적용 |
| 팟캐스트 진위 확인 | 업로드 시 C2PA 서명, AI 생성물이면 AudioSeal 추가 |
| 연구 / 탐지기 학습 | ASVspoof 5 train/dev/eval 세트 |

## 주의할 함정

- **탐지기는 한 번도 돌려 보지 않으면서 워터마크만 심기.** 무의미합니다. 탐지기를 CI에 넣으세요.
- **캘리브레이션 없는 탐지.** ASVspoof LA로 학습한 AASIST는 과적합되기 쉽고, 실제 환경에서는 정확도가 떨어집니다. 여러분의 도메인 데이터로 캘리브레이션하세요.
- **피치 시프트 틈.** 공격적인 피치 시프트는 대부분의 워터마크를 제거합니다. 탐지 기반 폴백(fallback)을 마련해 두세요.
- **메타데이터 벗겨내고 다시 올리기.** C2PA는 다시 인코딩만 하면 아주 쉽게 우회됩니다. 항상 암호학적 방어와 지각(perceptual) 기반 방어(워터마크)를 함께 적용하세요.
- **탐지 대신 라이브니스로 때우기.** 사용자에게 무작위 문장을 말하게 하는 방식입니다. 재생 공격(replay attack)은 막지만 실시간 복제는 막지 못합니다.

## 출시하기

`outputs/skill-spoof-defender.md`로 저장합니다. 음성 생성 배포를 위해 탐지 모델, 워터마크, 출처 증명 매니페스트, 운영 플레이북을 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행합니다. 합성 오디오를 대상으로 장난감 탐지기 + 장난감 워터마크 심기/탐지를 수행합니다.
2. **보통.** `audioseal`을 설치하고, TTS 출력물에 16비트 페이로드를 심은 뒤 다시 디코딩합니다. 노이즈로 오디오를 훼손하고 비트 복원 정확도(Bit Recovery Accuracy)를 측정합니다.
3. **어려움.** RawNet2 또는 AASIST를 ASVspoof 2019 LA로 파인튜닝합니다. EER을 측정합니다. F5-TTS로 생성한 클립의 홀드아웃(held-out) 세트로 테스트해 보세요 — OOD(분포 외) 데이터에서 탐지 성능이 어떻게 떨어지는지 확인할 수 있습니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| ASVspoof | 그 유명한 벤치마크 | 격년으로 열리는 챌린지; 2024년 = ASVspoof 5. |
| CM (countermeasure, 대책) | 탐지기 | 분류기: 진짜 음성 vs 합성 / 변환 음성. |
| SASV | 화자 검증 + CM | 생체 인식 + 스푸핑 탐지를 통합. |
| AudioSeal | Meta 워터마크 | 위치 특정 가능, 16비트 페이로드, WavMark보다 485배 빠름. |
| 비트 복원 정확도 (Bit Recovery Accuracy) | 워터마크 생존율 | 공격 이후 페이로드 비트 중 복원된 비율. |
| C2PA | 출처 증명 매니페스트 | 생성/저작 정보를 담은 암호학적 메타데이터. |
| AASIST | 탐지기 계열 | 그래프 어텐션 기반 안티스푸핑 SOTA. |

## 더 읽을거리

- [Todisco et al. (2024). ASVspoof 5](https://dl.acm.org/doi/10.1016/j.csl.2025.101825) — 현재의 벤치마크.
- [Defossez et al. (2024). AudioSeal](https://arxiv.org/abs/2401.17264) — 워터마크의 기본 선택지.
- [Chen et al. (2025). WaveVerify](https://arxiv.org/abs/2507.21150) — 시간축 공격을 위한 MoE 탐지기.
- [Jung et al. (2022). AASIST](https://arxiv.org/abs/2110.01200) — SOTA 탐지 백본.
- [AudioMarkBench (2024)](https://proceedings.neurips.cc/paper_files/paper/2024/file/5d9b7775296a641a1913ab6b4425d5e8-Paper-Datasets_and_Benchmarks_Track.pdf) — 강건성 평가.
- [C2PA specification](https://c2pa.org/specifications/specifications/) — 출처 증명 매니페스트 형식.
