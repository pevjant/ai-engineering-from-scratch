# 셀프 호스팅 서빙 선택 — 하드웨어와 규모에 맞는 엔진 고르기

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 엔진 선택은 하드웨어, 규모, 생태계의 함수이지, 리더보드를 읽고 정하는 게 아닙니다. 2026년 셀프 호스팅 추론을 지배하는 네 가지 엔진은 llama.cpp, Ollama, vLLM, SGLang이고, TGI는 뒤처진 채 유지보수 모드에 들어가 있습니다. **llama.cpp**는 CPU에서 가장 빠릅니다 — 가장 넓은 모델 지원, 양자화와 스레딩에 대한 완전한 제어. **Ollama**는 개발자 노트북용 원커맨드 설치로, llama.cpp보다 약 15~30% 느리고(Go + CGo + HTTP 직렬화 오버헤드), 프로덕션 비슷한 부하에서는 3배 처리량 격차가 벌어집니다. **TGI는 2025년 12월 11일 유지보수 모드에 진입**했습니다 — 이후 버그 수정만 이뤄지며, 순수 처리량은 vLLM보다 약 10% 느리지만 역사적으로 최고 수준의 관측 가능성과 HF 생태계 통합을 자랑했습니다. 그 유지보수 상태 때문에 장기적으로는 위험한 선택이 되었고, 새 프로젝트에는 SGLang이나 vLLM이 더 안전한 기본값입니다. **vLLM**은 범용 프로덕션 기본값입니다 — v0.15.1(2026년 2월)은 PyTorch 2.10, RTX Blackwell SM120, H200 최적화를 추가했습니다. **SGLang**은 에이전트형 멀티턴 / 접두어(prefix) 중심 워크로드의 전문가입니다 — 프로덕션에서 40만 개 이상의 GPU가 동작 중입니다(xAI, LinkedIn, Cursor, Oracle, GCP, Azure, AWS). 하드웨어 제약: CPU가 먼저면 → llama.cpp. AMD / 비 NVIDIA → vLLM이 가장 탄탄하게 지원되는 경로입니다(TRT-LLM은 NVIDIA 전용). 2026년의 파이프라인 패턴: 개발 = Ollama, 스테이징 = llama.cpp, 프로덕션 = vLLM 또는 SGLang. 엔진마다 받아들이는 가중치 포맷이 다릅니다 — llama.cpp 계열은 GGUF, GPU 엔진은 HF safetensors — 그래서 단계 사이에 포맷 변환이 들어설 수 있습니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 엔진 결정 트리 탐색기)
**선수 지식:** 엔진을 다루는 페이즈 17의 모든 레슨 (04, 06, 07, 09, 18)
**시간:** 약 45분

## 학습 목표

- 하드웨어(CPU / AMD / NVIDIA Hopper / Blackwell), 규모(사용자 1명 / 100명 / 10,000명), 워크로드(일반 챗 / 에이전트 / 긴 컨텍스트)를 주면 엔진을 고를 수 있습니다.
- 2026년 TGI 유지보수 모드 상태(2025년 12월 11일)와, 그것이 왜 새 프로젝트를 vLLM이나 SGLang 쪽으로 기울게 만드는지 말할 수 있습니다.
- 개발/스테이징/프로덕션 파이프라인을 설명하고, 단계 사이 어디에 GGUF-to-safetensors 포맷 변환이 들어서는지 짚을 수 있습니다.
- "CPU가 먼저"면 왜 llama.cpp를 가리키고, "AMD"는 왜 TRT-LLM을 배제하는지 설명할 수 있습니다.

## 문제 상황

팀이 새로운 셀프 호스팅 LLM 프로젝트를 시작합니다. 한 엔지니어는 Ollama를 말하고, 다른 이는 vLLM을, 세 번째는 "TGI는 개봉박두 바로 되는 거 아닌가요?"라고 합니다. 셋 다 문맥에 따라 맞는 말이고, 셋 다 모든 경우에 맞지는 않습니다.

2026년에는 선택 트리가 중요합니다. 하드웨어가 먼저, 규모가 두 번째, 워크로드가 세 번째입니다. 그리고 2025년의 한 사건 — TGI가 12월 11일 유지보수 모드에 진입한 것 — 이 새 프로젝트의 기본값을 바꿔 놓았습니다.

## 개념

### 다섯 가지 엔진

| 엔진 | 가장 잘 맞는 곳 | 비고 |
|--------|----------|-------|
| **llama.cpp** | CPU / 엣지 / 최소 의존성 / 가장 넓은 모델 지원 | CPU에서 최고 속도, 완전한 제어 |
| **Ollama** | 개발용 노트북, 단일 사용자, 원커맨드 설치 | llama.cpp보다 15-30% 느림. 프로덕션 처리량 3배 격차 |
| **TGI** | HF 생태계, 규제 산업 | **2025년 12월 11일 유지보수 모드** |
| **vLLM** | 범용 프로덕션, 100명 이상 사용자 | 폭넓은 프로덕션 기본값. v0.15.1 (2026년 2월) |
| **SGLang** | 에이전트형 멀티턴, 접두어 중심 워크로드 | 프로덕션에서 40만 개 이상 GPU |

### 하드웨어 우선 결정

**CPU가 먼저** → llama.cpp. Ollama도 되지만 더 느립니다. 다른 엔진은 CPU에서 경쟁력이 없습니다.

**AMD GPU** → vLLM이 가장 탄탄하게 지원되는 경로입니다(AMD ROCm 지원). SGLang도 됩니다. TRT-LLM은 NVIDIA 전용이라 후보에서 제외입니다.

**NVIDIA Hopper (H100 / H200)** → vLLM, SGLang, TRT-LLM. 셋 모두 최상위입니다.

**NVIDIA Blackwell (B200 / GB200)** → TRT-LLM이 처리량 선두입니다(페이즈 17 · 07). vLLM과 SGLang이 바로 뒤를 따라갑니다.

**Apple Silicon (M 시리즈)** → llama.cpp (Metal). Ollama가 이걸 감싸 줍니다.

### 규모 두 번째 결정

**사용자 1명 / 로컬 개발** → Ollama. 명령 한 줄, 첫 토큰이 몇 초 안에.

**10-100명 / 소규모 팀** → vLLM 단일 GPU.

**100-1만 명 / 프로덕션** → vLLM 프로덕션 스택(페이즈 17 · 18) 또는 SGLang.

**1만 명 이상 / 엔터프라이즈** → vLLM 프로덕션 스택 + 이기종 분리 배치(페이즈 17 · 17) + LMCache(페이즈 17 · 18).

### 워크로드 세 번째 결정

**일반 챗 / Q&A** → 폭넓은 기본값으로는 vLLM이 이깁니다.

**에이전트형 멀티턴 (도구, 계획, 메모리)** → SGLang의 RadixAttention(페이즈 17 · 06)이 지배적입니다.

**접두어 재사용이 많은 RAG** → SGLang.

**코드 생성** → vLLM으로 충분. SGLang이 캐시에서 약간 더 좋습니다.

**긴 컨텍스트 (128K+)** → vLLM + 청크 프리필(chunked prefill), 또는 SGLang + 계층형 KV.

### TGI 유지보수 함정

Hugging Face TGI는 2025년 12월 11일 유지보수 모드에 들어갔습니다 — 앞으로는 버그 수정만 있습니다. 역사적으로는: 최상위 관측 가능성, 최고 수준의 HF 생태계 통합(모델 카드, 안전 도구), 순수 처리량은 vLLM에 약간 뒤짐.

2026년 새 프로젝트라면: 기본값에서 TGI를 피하세요. 기존 TGI 배포는 계속 운영할 수 있지만 결국에는 마이그레이션해야 합니다. SGLang과 vLLM이 더 안전한 기본값입니다.

### 파이프라인 패턴

개발(Ollama) → 스테이징(llama.cpp) → 프로덕션(vLLM). 엔진마다 받아들이는 가중치 포맷이 다릅니다 — llama.cpp 계열은 GGUF, GPU 엔진은 HF safetensors — 그래서 단계 사이에 포맷 변환이 들어설 수 있습니다. 엔지니어는 노트북에서 빠르게 반복하고, 스테이징은 프로덕션의 양자화를 그대로 재현하며, 프로덕션이 실제 서빙 대상입니다.

### Ollama 주의점

Ollama는 개발에는 훌륭합니다. 하지만 공유 프로덕션에는 맞지 않습니다. Go HTTP 직렬화가 오버헤드를 더하고, 동시성 관리는 vLLM보다 단순하며, OpenTelemetry 지원도 뒤처져 있습니다. Ollama가 빛나는 곳 — 한 명의 사용자, 한 줄의 명령 — 에서 쓰고, 공유 환경에서는 vLLM으로 갈아타세요.

### 셀프 호스팅 vs 매니지드는 별개의 결정

페이즈 17 · 01(매니지드 하이퍼스케일러), · 02(추론 플랫폼)가 매니지드를 다룹니다. 이 레슨은 이미 셀프 호스팅을 결정했다고 가정합니다. 셀프 호스팅을 하는 이유: 데이터 레지던시, 커스텀 파인튜닝, 규모가 커질 때의 총 소유 비용, 호스티드 환경에서 쓸 수 없는 도메인 모델.

### 기억해야 할 숫자들

- TGI 유지보수 모드: 2025년 12월 11일.
- vLLM v0.15.1: 2026년 2월. PyTorch 2.10, Blackwell SM120 지원.
- SGLang 프로덕션 규모: 40만 개 이상 GPU.
- Ollama vs llama.cpp 처리량 격차: 15-30% 느림. 프로덕션 부하에서는 3배.

```figure
data-parallel
```

## 사용해 보기

`code/main.py`는 결정 트리 탐색기입니다. 하드웨어 + 규모 + 워크로드를 주면 엔진을 고르고 이유를 설명해 줍니다.

## 출시하기

이 레슨은 `outputs/skill-engine-picker.md`를 산출물로 만듭니다. 제약 조건을 바탕으로 엔진을 고르고 마이그레이션 계획을 작성합니다.

## 연습 문제

1. 자신의 하드웨어 / 규모 / 워크로드로 `code/main.py`를 실행해 보세요. 출력이 직관과 일치하나요?
2. 인프라가 H100 12장과 MI300X AMD 8장입니다. 어떤 엔진? TRT-LLM이 후보에서 빠지는 이유는?
3. 한 팀이 "우리가 아는 거라서" 2026년에 TGI를 쓰고 싶어 합니다. 마이그레이션을 주장해 보세요.
4. Ollama 개발에서 vLLM 프로덕션으로: 양자화, 설정, 관측 가능성에서 무엇이 달라지나요?
5. P99 접두어 길이가 8K이고 테넌트 간 재사용이 많은 RAG 제품입니다. 엔진을 고르고 페이즈 17 · 11 + 18로 스택을 쌓아 보세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| llama.cpp | "CPU 그것" | 가장 넓은 모델 지원, CPU에서 최고 속도 |
| Ollama | "노트북 그것" | 원커맨드 설치, 개발 등급 처리량 |
| TGI | "HF의 서빙" | 2025년 12월부터 유지보수 모드 |
| vLLM | "기본값" | 2026년 폭넓은 프로덕션 베이스라인 |
| SGLang | "에이전트 그것" | 접두어 중심, RadixAttention |
| TRT-LLM | "NVIDIA 전용" | Blackwell 처리량 선두, NVIDIA만 |
| GGUF | "llama.cpp 포맷" | 번들된 K-quant 변형 |
| 프로덕션 스택 | "vLLM K8s" | 페이즈 17 · 18 참조 배포 |
| 파이프라인 패턴 | "개발→스테이징→프로덕션" | Ollama → llama.cpp → vLLM. 엔진마다 가중치 포맷이 다름 |

## 더 읽을거리

- [AI Made Tools — vLLM vs Ollama vs llama.cpp vs TGI 2026](https://www.aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/)
- [Morph — llama.cpp vs Ollama 2026](https://www.morphllm.com/comparisons/llama-cpp-vs-ollama)
- [n1n.ai — Comprehensive LLM Inference Engine Comparison](https://explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13)
- [PremAI — 10 Best vLLM Alternatives 2026](https://blog.premai.io/10-best-vllm-alternatives-for-llm-inference-in-production-2026/)
- [TGI maintenance announcement](https://github.com/huggingface/text-generation-inference) — 릴리스 노트.
- [vLLM v0.15.1 release notes](https://github.com/vllm-project/vllm/releases)
