> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 화자 인식과 검증

> ASR이 "무엇이라고 말했지?"를 묻는다면, 화자 인식은 "누가 말했지?"를 묻습니다. 수학적으로는 똑같아 보입니다 — 임베딩에 코사인 유사도죠. 하지만 모든 프로덕션(운영 환경) 의사 결정은 EER이라는 단 하나의 숫자에 달려 있습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 6 · 02 (스펙트로그램과 멜), 페이즈 5 · 22 (임베딩 모델)
**소요 시간:** 약 45분

## 문제 상황

사용자가 암호 문구를 말합니다. 여러분이 알고 싶은 것은 이 사람이 본인 맞는지(*검증*, 1:1)인지, 아니면 등록해 둔 사람 은행(enrollment bank) 중 첫 번째 사람인지(*식별*, 1:N)입니다. 아니면 둘 다 아닐 수도 있죠 — 모르는 화자인지(*오픈셋*, open-set) 확인해야 할 때도 있습니다.

2018년 이전: GMM-UBM + i-vector. 나쁘지 않은 EER을 냈지만 채널이 바뀌면(전화기 vs 노트북) 감정 변화에도 잘 무너졌습니다. 2018~2022년: x-vector(각도 마진으로 학습한 TDNN 백본). 2022년 이후: ECAPA-TDNN과 WavLM-large 임베딩. 2026년 현재 이 분야는 세 가지 모델과 하나의 지표가 지배합니다.

그 지표가 바로 **EER** — 등오류율(Equal Error Rate)입니다. 거짓 수용률(False Accept Rate)과 거짓 거부률(False Reject Rate)이 같아지도록 판정 임계값을 잡습니다. 그 교차점이 EER입니다. 모든 논문, 모든 리더보드, 모든 조달 심사에서 쓰입니다.

## 개념

![임베딩 + 코사인 + EER을 곁들인 등록 + 검증 파이프라인](../assets/speaker-verification.svg)

**파이프라인.** 등록(enrollment): 대상 화자의 음성을 5~30초 녹음하고, 고정 차원의 임베딩(ECAPA-TDNN은 192차원, WavLM-large는 256차원)을 계산합니다. 검증: 테스트 발화의 임베딩을 구하고, 코사인 유사도를 계산한 뒤, 임계값과 비교합니다.

**ECAPA-TDNN (2020, 2026년에도 여전히 강자).** Emphasized Channel Attention, Propagation and Aggregation - Time-Delay Neural Network. 셀린즈-익사이테이션(squeeze-excitation)을 넣은 1D 합성곱 블록과 멀티헤드 어텐션 풀링, 그 뒤에 192차원으로 보내는 선형 레이어로 이루어집니다. VoxCeleb 1+2(화자 2,700명, 발화 110만 개)에서 Additive Angular Margin 손실(AAM-softmax)로 학습했습니다.

**WavLM-SV (2022 이후).** 사전학습된 WavLM-large SSL 백본을 AAM 손실로 파인튜닝합니다. 품질은 더 좋지만 느립니다 — 15 MB짜리와 비교하면 300 MB 이상입니다.

**x-vector (베이스라인).** TDNN + 통계 풀링. 고전이지만 CPU / 엣지 환경에서는 여전히 유용합니다.

**AAM-softmax.** 기본 소프트맥스에 각도 공간에서 마진 `m`을 더한 것입니다. 정답 클래스에는 `cos(θ + m)`을 적용하죠. 클래스 사이의 각도를 강제로 벌려 줍니다. 보통 `m=0.2`, 스케일 `s=30`을 씁니다.

### 스코어링

- **코사인.** 등록 임베딩과 테스트 임베딩 사이의 코사인 유사도. 임계값 기반 판정.
- **PLDA (Probabilistic LDA).** 임베딩을 잠재 공간으로 사영해, 같은 화자 vs 다른 화자의 우도비(likelihood ratio)를 닫힌 형태(closed-form)로 계산합니다. 코사인 위에 얹으면 EER이 10~20% 더 줄어듭니다. 2020년 이전의 표준이었고, 지금은 클로즈셋(closed-set) 환경에서만 씁니다.
- **점수 정규화.** `S-norm` 또는 `AS-norm`: 각 점수를 침입자(imposter) 집단의 평균과 표준편차에 대해 정규화합니다. 도메인이 다른 평가에서는 필수입니다.

### 알아 둬야 할 수치들 (2026)

| 모델 | VoxCeleb1-O EER | 파라미터 | 처리량 (A100) |
|-------|-----------------|--------|-------------------|
| x-vector (고전) | 3.10% | 5 M | 400× RT |
| ECAPA-TDNN | 0.87% | 15 M | 200× RT |
| WavLM-SV large | 0.42% | 316 M | 20× RT |
| Pyannote 3.1 segmentation + embedding | 0.65% | 6 M | 100× RT |
| ReDimNet (2024) | 0.39% | 24 M | 100× RT |

### 화자 분리(diarization)

여러 명이 말하는 클립에서 "누가 언제 말했나"를 찾는 문제입니다. 파이프라인: VAD → 세그먼트 분할 → 세그먼트마다 임베딩 → 클러스터링(응집형 또는 스펙트럴) → 경계 다듬기. 현대의 스택은 `pyannote.audio` 3.1로, 화자 분할 + 임베딩 + 클러스터링을 호출 한 번으로 묶어 제공합니다. 2026년 AMI 데이터셋의 SOTA DER은 약 15%입니다(2022년의 23%에서 내려왔습니다).

```figure
sp-eer-crossover
```

## 직접 만들어 보기

### 단계 1: MFCC 통계로 만든 장난감 임베딩

```python
def embed_mfcc_stats(signal, sr):
    frames = featurize_mfcc(signal, sr, n_mfcc=13)
    mean = [sum(f[i] for f in frames) / len(frames) for i in range(13)]
    std = [
        math.sqrt(sum((f[i] - mean[i]) ** 2 for f in frames) / len(frames))
        for i in range(13)
    ]
    return mean + std  # 26차원
```

SOTA와는 거리가 멉니다 — 교육용일 뿐입니다. `code/main.py`는 합성 화자 데이터 위에서 이것을 개념 증명(proof-of-concept)으로 사용합니다.

### 단계 2: 코사인 유사도 + 임계값

```python
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

def verify(enroll, test, threshold=0.75):
    return cosine(enroll, test) >= threshold
```

### 단계 3: 유사도 쌍으로 EER 구하기

```python
def eer(same_scores, diff_scores):
    thresholds = sorted(set(same_scores + diff_scores))
    best = (1.0, 1.0, 0.0)  # (거짓 수용률, 거짓 거부률, 임계값)
    for t in thresholds:
        fr = sum(1 for s in same_scores if s < t) / len(same_scores)
        fa = sum(1 for s in diff_scores if s >= t) / len(diff_scores)
        if abs(fa - fr) < abs(best[0] - best[1]):
            best = (fa, fr, t)
    return (best[0] + best[1]) / 2, best[2]
```

(eer, eer에서의 임계값)을 반환합니다. 둘 다 보고하세요.

### 단계 4: SpeechBrain으로 프로덕션 수준 만들기

```python
from speechbrain.pretrained import EncoderClassifier

clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")

# 등록: 깨끗한 샘플 3~5개의 임베딩을 평균 낸다
enroll = torch.stack([clf.encode_batch(load(x)) for x in enrollment_clips]).mean(0)
# 검증
score = clf.similarity(enroll, clf.encode_batch(load("test.wav"))).item()
verdict = score > 0.25   # ECAPA의 전형적인 임계값. 여러분 데이터로 튜닝할 것
```

### 단계 5: pyannote로 화자 분리하기

```python
from pyannote.audio import Pipeline

pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
diarization = pipe("meeting.wav", num_speakers=None)
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"{turn.start:.1f}–{turn.end:.1f}  {speaker}")
```

## 사용해 보기

2026년 스택:

| 상황 | 선택 |
|-----------|------|
| 클로즈셋 1:1 검증, 엣지 | ECAPA-TDNN + 코사인 임계값 |
| 오픈셋 검증, 클라우드 | WavLM-SV + AS-norm |
| 화자 분리 (회의, 팟캐스트) | `pyannote/speaker-diarization-3.1` |
| 안티 스푸핑 (재생 공격 / 딥페이크 탐지) | AASIST 또는 RawNet2 |
| 초소형 임베디드 (KWS + 등록) | Titanet-Small (NeMo) |

## 함정들

- **채널 불일치.** VoxCeleb(웹 동영상)으로 학습한 모델 ≠ 전화 통화 오디오. 반드시 목표 채널에서 평가하세요.
- **짧은 발화.** 테스트 오디오가 3초 미만이면 EER이 급격히 나빠집니다.
- **노이즈 섞인 등록.** 노이즈가 낀 등록 샘플 하나가 앵커 전체를 오염시킵니다. 깨끗한 샘플 3개 이상을 모아 평균 내세요.
- **조건이 다른데 임계값 고정.** 반드시 목표 도메인에서 모은 홀드아웃 개발 세트로 임계값을 튜닝하세요.
- **정규화되지 않은 임베딩에 코사인 적용.** 먼저 L2 정규화하세요. 그렇지 않으면 크기(magnitude)가 지배합니다.

## 출시해 보기

`outputs/skill-speaker-verifier.md`로 저장하세요. 모델, 등록 프로토콜, 임계값 튜닝 계획, 사기 방지 장치를 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 합성 "화자"(서로 다른 음높이 프로파일)를 만들고, 등록하고, 100쌍짜리 시험 목록에서 EER을 계산합니다.
2. **보통.** VoxCeleb1 발화 30개(화자 5명 × 6개씩)에 SpeechBrain ECAPA를 적용해 보세요. 코사인 vs PLDA로 EER을 계산해 비교합니다.
3. **어려움.** `pyannote.audio`로 등록 → 화자 분리 → 검증까지 이어지는 전체 파이프라인을 만들어 보세요. AMI 개발 세트에서 DER을 평가합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| EER | 대표 지표 | 거짓 수용 = 거짓 거부가 되는 임계값. |
| 검증 (Verification) | 1:1 | "이 사람이 앨리스 맞나?" |
| 식별 (Identification) | 1:N | "지금 말하는 사람은 누구지?" |
| 오픈셋 (Open-set) | 모르는 사람 가능 | 테스트 세트에 등록되지 않은 화자가 섞여 있을 수 있다. |
| 등록 (Enrollment) | 등록시키기 | 화자의 기준(reference) 임베딩을 계산하는 것. |
| AAM-softmax | 그 손실 함수 | 각도 마진을 더한 소프트맥스. 클러스터를 강제로 벌린다. |
| PLDA | 고전 스코어링 | Probabilistic LDA. 임베딩 위에서 우도비 방식으로 점수를 매긴다. |
| DER | 화자 분리 지표 | Diarization Error Rate — 누락 + 오탐 + 혼동의 합. |

## 더 읽을거리

- [Snyder 외 (2018). X-Vectors: Robust DNN Embeddings for Speaker Recognition](https://www.danielpovey.com/files/2018_icassp_xvectors.pdf) — 고전 딥 임베딩 논문.
- [Desplanques 외 (2020). ECAPA-TDNN](https://arxiv.org/abs/2005.07143) — 2020~2026년의 지배적 아키텍처.
- [Chen 외 (2022). WavLM: Large-Scale Self-Supervised Pre-Training for Full Stack Speech Processing](https://arxiv.org/abs/2110.13900) — 화자 검증과 화자 분리를 위한 SSL 백본.
- [Bredin 외 (2023). pyannote.audio 3.1](https://github.com/pyannote/pyannote-audio) — 프로덕션용 화자 분리 + 임베딩 스택.
- [VoxCeleb 리더보드 (2026년 갱신)](https://www.robots.ox.ac.uk/~vgg/data/voxceleb/) — 모델별 최신 EER 순위.
