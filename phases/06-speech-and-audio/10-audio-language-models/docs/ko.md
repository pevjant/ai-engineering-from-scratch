> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 오디오 언어 모델 — Qwen2.5-Omni, Audio Flamingo, GPT-4o Audio

> 2026년의 오디오 언어 모델은 음성 + 주변 소리 + 음악을 아울러 추론합니다. Qwen2.5-Omni-7B는 MMAU-Pro에서 GPT-4o Audio와 어깨를 나란히 하고, Audio Flamingo Next는 LongAudioBench에서 Gemini 2.5 Pro를 앞섭니다. 오픈과 클로즈드의 격차는 사실상 사라졌습니다 — 다만 멀티 오디오 과제만은 예외로, 누구나 무작위 찍기 수준입니다.

**유형:** Learn
**언어:** Python
**선수 지식:** 페이즈 6 · 04 (ASR), 페이즈 12 · 03 (비전-언어 모델), 페이즈 7 · 10 (오디오 트랜스포머)
**소요 시간:** 약 45분

## 문제 상황

여러분에게 5초짜리 오디오가 있습니다. 개 짖는 소리, 누군가 "멈춰!"라고 외치는 소리, 그리고 침묵. 유용한 질문은 여러 축에 걸쳐 있습니다:

- **전사.** "무슨 말이 나왔지?" — ASR의 영역.
- **의미 추론.** "이 사람이 위험한가?" — 짖는 소리 + 외침 + 침묵을 함께 이해해야 합니다.
- **음악 추론.** "멜로디를 연주하는 악기는 뭐지?"
- **긴 오디오 검색.** "90분짜리 이 강연에서 강사가 경사 하강법을 설명한 지점이 어디지?"

이 모든 질문에 프롬프트 하나로 답하는 모델이 바로 **오디오 언어 모델**(LALM / ALM)입니다. 순수 ASR과는 다릅니다: LALM은 전사본이 아니라 자유 형식의 자연어 답을 내놓습니다.

## 개념

![오디오 언어 모델: 오디오 인코더 + 프로젝터 + LLM 디코더](../assets/alm-architecture.svg)

### 세 구성 요소 템플릿

2026년의 모든 LALM은 같은 뼈대를 씁니다:

1. **오디오 인코더.** Whisper 인코더 · BEATs · CLAP · WavLM · 또는 모델별 맞춤 인코더.
2. **프로젝터.** 오디오 인코더 특성을 LLM의 토큰 임베딩 공간으로 연결하는 선형층 또는 MLP.
3. **LLM.** Llama / Qwen / Gemma 계열 디코더. 텍스트 + 오디오 토큰을 섞어 받고, 텍스트를 생성합니다.

학습:

- **스테이지 1.** 인코더 + LLM은 얼려 두고, ASR / 캡셔닝 데이터로 프로젝터만 학습합니다.
- **스테이지 2.** 지시를 따르는 오디오 과제(QA, 추론, 음악 이해)로 전체 또는 LoRA 파인튜닝합니다.
- **스테이지 3 (선택).** 음성 입력/음성 출력을 위해 음성 디코더를 추가합니다. Qwen2.5-Omni와 AF3-Chat이 이렇게 합니다.

### 2026년 모델 지도

| 모델 | 백본 | 오디오 인코더 | 출력 모달리티 | 접근 |
|-------|----------|---------------|-----------------|--------|
| Qwen2.5-Omni-7B | Qwen2.5-7B | 맞춤 + Whisper | 텍스트 + 음성 | Apache-2.0 |
| Qwen3-Omni | Qwen3 | 맞춤 | 텍스트 + 음성 | Apache-2.0 |
| Audio Flamingo 3 | Qwen2 | AF-CLAP | 텍스트 | NVIDIA 비상용 |
| Audio Flamingo Next | Qwen2 | AF-CLAP v2 | 텍스트 | NVIDIA 비상용 |
| SALMONN | Vicuna | Whisper + BEATs | 텍스트 | Apache-2.0 |
| LTU / LTU-AS | Llama | CAV-MAE | 텍스트 | Apache-2.0 |
| GAMA | Llama | AST + Q-Former | 텍스트 | Apache-2.0 |
| Gemini 2.5 Flash/Pro (비공개) | Gemini | 자체 기술 | 텍스트 + 음성 | API |
| GPT-4o Audio (비공개) | GPT-4o | 자체 기술 | 텍스트 + 음성 | API |

### 벤치마크 냉정하게 보기 (2026)

**MMAU-Pro.** 음성 / 소리 / 음악 / 혼합을 아우르는 QA 1800쌍. 멀티 오디오 하위 집합 포함.

| 모델 | 전체 | 음성 | 소리 | 음악 | 멀티 오디오 |
|-------|---------|--------|-------|-------|-------------|
| Gemini 2.5 Pro | ~60% | 73.4% | 51.9% | 64.9% | ~22% |
| Gemini 2.5 Flash | ~57% | 73.4% | 50.5% | 64.9% | 21.2% |
| GPT-4o Audio | 52.5% | — | — | — | 26.5% |
| Qwen2.5-Omni-7B | 52.2% | 57.4% | 47.6% | 61.5% | ~20% |
| Audio Flamingo 3 | ~54% | — | — | — | — |
| Audio Flamingo Next | LongAudioBench SOTA | — | — | — | — |

**멀티 오디오 열이 모두를 비판합니다.** 4지선다형에서 찍으면 25%인데, 대부분의 모델이 그 근처입니다. LALM은 여전히 두 클립을 비교하는 데 고전합니다.

### 2026년 LALM이 쓸모 있는 곳

- **콜센터 녹음의 컴플라이언스 감사.** "상담원이 필수 안내 문구를 언급했나?"
- **접근성.** 청각장애 사용자에게 소리 사건을 묘사 (단순 전사가 아니라).
- **콘텐츠 검열.** 폭력적 언어 + 협박 어조 + 배경 맥락 탐지.
- **팟캐스트 / 회의 챕터 나누기.** 화자 교대점이 아니라 의미 기반 요약.
- **음악 카탈로그 분석.** "B섹션에서 조가 바뀌는 트랙을 모두 찾아 줘."

### 아직 (당장은) 쓸모없는 곳

- 세밀한 음악 이론 (코드 수준보다 아래).
- 긴 대화에서 화자별 귀속 추론 (10분 넘으면 성능 저하).
- 멀티 오디오 비교 (22~26%는 무작위를 겨우 넘는 수준).
- 실시간 스트리밍 추론 (대부분 오프라인 배치 추론).

```figure
v4-alm-tokens
```

## 직접 만들어 보기

### 단계 1: Qwen2.5-Omni에 질문하기

```python
from transformers import AutoModelForCausalLM, AutoProcessor

processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-Omni-7B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Omni-7B", torch_dtype="auto")

audio, sr = load_wav("clip.wav", sr=16000)
messages = [{
    "role": "user",
    "content": [
        {"type": "audio", "audio": audio},
        {"type": "text", "text": "What sounds do you hear, and what's happening?"},
    ],
}]
inputs = processor.apply_chat_template(messages, tokenize=True, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=200)
print(processor.decode(output[0], skip_special_tokens=True))
```

### 단계 2: 프로젝터 패턴

```python
import torch.nn as nn

class AudioProjector(nn.Module):
    def __init__(self, audio_dim=1280, llm_dim=4096):
        super().__init__()
        self.down = nn.Linear(audio_dim, llm_dim)
        self.act = nn.GELU()
        self.up = nn.Linear(llm_dim, llm_dim)

    def forward(self, audio_features):
        return self.up(self.act(self.down(audio_features)))
```

이게 전부입니다. 프로젝터는 보통 선형층 1~3개입니다. ASR 쌍(오디오 → 전사본)으로 학습하는 것이 스테이지 1의 선행 학습 과제입니다.

### 단계 3: MMAU / LongAudioBench 벤치마킹

```python
from datasets import load_dataset
mmau = load_dataset("MMAU/MMAU-Pro")

correct = 0
for item in mmau["test"]:
    answer = call_model(item["audio"], item["question"], item["choices"])
    if answer == item["correct_choice"]:
        correct += 1
print(f"Accuracy: {correct / len(mmau['test']):.3f}")
```

범주별(음성 / 소리 / 음악 / 멀티 오디오)로 따로 보고하세요. 합산 숫자는 모델이 어디서 무너지는지 가려 버립니다.

## 사용해 보기

| 과제 | 2026년 선택 |
|------|-----------|
| 자유 형식 오디오 QA (오픈) | Qwen2.5-Omni-7B |
| 긴 오디오 최고의 오픈 모델 | Audio Flamingo Next |
| 클로즈드 최강 | Gemini 2.5 Pro |
| 음성 입력/음성 출력 에이전트 | Qwen2.5-Omni 또는 GPT-4o Audio |
| 음악 추론 | Audio Flamingo 3 또는 2 (음악 특화 AF-CLAP) |
| 콜센터 감사 | 정책 문서에 RAG를 얹은 Gemini 2.5 Pro (API) |

## 함정들

- **멀티 오디오에 대한 과신.** "어느 클립에 X가 있나" 같은 과제라면, 무작위 찍기 수준 성능이 현실입니다.
- **긴 오디오 성능 저하.** 10분을 넘기면 대부분의 모델이 화자 귀속을 놓칩니다. 먼저 화자 분리(레슨 6)를 하고 그다음 요약하세요.
- **침묵에서의 환각.** Whisper 인코더를 쓰는 LALM이 물려받은 똑같은 문제입니다. VAD 게이트를 거치세요.
- **벤치마크 골라 내기.** 벤더 블로그는 잘 나오는 범주만 내세웁니다. MMAU-Pro 멀티 오디오 하위 집합은 직접 돌려 보세요.

## 출시해 보기

`outputs/skill-alm-picker.md`로 저장하세요. 주어진 오디오 이해 과제에 맞는 LALM + 벤치마크 하위 집합 + 출력 모달리티(텍스트 vs 음성)를 고릅니다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 보세요. 장난감 프로젝터 패턴 + (오디오 임베딩, 텍스트 토큰) → 출력 토큰이라는 가짜 LALM 라우팅을 보여 줍니다.
2. **보통.** MMAU-Pro 음성 항목 100개로 Qwen2.5-Omni-7B의 점수를 매겨 보세요. 논문에 보고된 숫자와 비교합니다.
3. **어려움.** 최소한의 오디오 캡셔닝 베이스라인을 만들어 보세요: BEATs 인코더 + 2층 프로젝터 + 얼린 Llama-3.2-1B. 프로젝터만 AudioCaps로 파인튜닝하고, Clotho-AQA에서 SALMONN과 비교합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| LALM | 오디오 ChatGPT | 오디오 인코더 + 프로젝터 + LLM 디코더. |
| 프로젝터 (Projector) | 어댑터 | 오디오 특성을 LLM 임베딩 공간으로 보내는 작은 MLP. |
| MMAU | 그 벤치마크 | 음성, 소리, 음악을 아우르는 오디오 QA 1만 쌍. |
| MMAU-Pro | 더 어려운 MMAU | 멀티 오디오 / 추론 위주의 문제 1800개. |
| LongAudioBench | 긴 오디오 평가 | 수십 분짜리 클립에 의미 기반 질문. |
| 음성 입력/음성 출력 | 음성 네이티브 | 모델이 음성을 받아 텍스트 우회 없이 음성으로 답한다. |

## 더 읽을거리

- [Chu 외 (2024). Qwen2-Audio](https://arxiv.org/abs/2407.10759) — 참조 아키텍처.
- [Alibaba (2025). Qwen2.5-Omni](https://huggingface.co/Qwen/Qwen2.5-Omni-7B) — 음성 입력, 음성 출력.
- [NVIDIA (2025). Audio Flamingo 3](https://arxiv.org/abs/2507.08128) — 오픈 긴 오디오 리더.
- [NVIDIA (2026). Audio Flamingo Next](https://arxiv.org/abs/2604.10905) — LongAudioBench SOTA.
- [Tang 외 (2023). SALMONN](https://arxiv.org/abs/2310.13289) — 듀얼 인코더 선구자.
- [MMAU-Pro 리더보드](https://mmaubenchmark.github.io/) — 살아 있는 2026년 순위.
