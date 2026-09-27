> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 엣지 추론(Edge Inference) — Apple Neural Engine, Qualcomm Hexagon, WebGPU/WebLLM, Jetson

> 엣지(기기 위 추론)의 핵심 제약은 연산 능력이 아니라 메모리 대역폭입니다. 모바일 DRAM은 50-90 GB/s 수준이지만 데이터센터 HBM3는 2-3 TB/s를 넘습니다 — 30~50배 차이입니다. 디코드는 메모리 병목이기 때문에 이 격차가 결정적입니다. 2026년 현재 엣지 환경은 네 갈래로 나뉩니다. Apple M4/A18 Neural Engine은 통합 메모리(CPU↔NPU 복사 불필요)로 최대 38 TOPS입니다. Qualcomm Snapdragon X Elite / 8 Gen 4 Hexagon은 45 TOPS에 도달합니다. WebGPU + WebLLM은 M3 Max에서 Llama 3.1 8B(Q4)를 초당 약 41 토큰으로 구동합니다(네이티브의 약 70-80%); GitHub 스타 17.6k, OpenAI 호환 API, 모바일 커버리지 약 70-75%입니다. NVIDIA Jetson Orin Nano Super(8GB)는 Llama 3.2 3B / Phi-3를 담을 수 있고, AGX Orin은 vLLM으로 gpt-oss-20b를 초당 약 40 토큰으로 구동하며, Jetson T4000(JetPack 7.1)은 AGX Orin의 2배입니다. TensorRT Edge-LLM은 EAGLE-3, NVFP4, 청크 프리필(chunked prefill)을 지원합니다 — Bosch, ThunderSoft, MediaTek이 CES 2026에서 시연했습니다.

**유형:** 학습
**언어:** Python (표준 라이브러리, 대역폭 병목 디코드 시뮬레이터 장난감 버전)
**선수 지식:** 페이즈 17 · 04 (서빙 엔진 내부 구조), 페이즈 17 · 09 (프로덕션(운영 환경) 양자화)
**시간:** 약 60분

## 학습 목표

- 모바일 LLM 추론이 왜 메모리 대역폭 병목인지, 그리고 연산 능력이 왜 부차적인지 설명할 수 있습니다.
- 네 가지 엣지 타깃(Apple ANE, Qualcomm Hexagon, WebGPU/WebLLM, NVIDIA Jetson)을 나열하고 각각에 맞는 사용 사례를 짝지을 수 있습니다.
- 2026년 WebGPU 커버리지 공백(Firefox Android가 뒤따르는 중)과 Safari iOS 26 정식 출시를 언급할 수 있습니다.
- 타깃별 양자화 포맷을 고를 수 있습니다 (ANE에는 Core ML INT4 + FP16, Hexagon에는 QNN INT8/INT4, 브라우저에는 WebGPU Q4, Jetson Thor에는 NVFP4).

## 문제 상황

어떤 고객이 온디바이스 챗봇을 원합니다. 음성 우선, 기본값이 프라이버시 보호, 오프라인 동작이어야 합니다. MacBook Pro M3 Max에서는 Llama 3.1 8B Q4가 초당 약 55 토큰으로 돌아갑니다 — 충분합니다. 그런데 iPhone 16 Pro에서 같은 모델은 초당 3 토큰 — 문제가 있습니다. Snapdragon 8 Gen 3을 얹은 중저가 Android에서는 초당 7 토큰입니다. Chrome Android v121+에서 WebGPU로 브라우저에서 돌리면 기기에 따라 초당 4-8 토큰입니다.

이 처리량 편차는 포팅 문제가 아닙니다. 대역폭 격차 × 양자화 포맷 × 사용자 공간에서 NPU에 접근 가능한지 여부가 곱해진 결과입니다. 2026년의 엣지 추론은 서로 다른 네 가지 문제이고, 네 가지 서로 다른 해법이 필요합니다.

## 개념

### 진짜 상한선은 대역폭입니다

디코드는 토큰 하나를 뽑아낼 때마다 가중치 전체를 읽습니다. 7B 모델 하나를 Q4로 담으면 3.5 GB입니다. 이 3.5 GB를 50 GB/s로 읽으면 70ms가 걸립니다 — 이론상 상한이 초당 약 14 토큰입니다. 90 GB/s(고사양 모바일 DRAM)면 상한이 초당 약 25 토큰으로 올라갑니다. 이 숫자 아래에서는 아무리 연산 능력을 더해도 소용이 없습니다.

데이터센터의 3 TB/s HBM3는 같은 3.5 GB를 1.2ms에 읽습니다 — 상한이 초당 830 토큰입니다. 같은 모델, 같은 가중치. 메모리 서브시스템만 다를 뿐입니다.

### Apple Neural Engine (M4 / A18)

- 최대 38 TOPS. 통합 메모리(CPU와 ANE가 같은 메모리 풀 공유) — 복사 오버헤드가 없습니다.
- Core ML + 컴파일된 `.mlmodel` 모델로 접근하거나, PyTorch를 통해 Metal Performance Shaders(MPS)로 접근합니다.
- Llama.cpp의 Metal 백엔드는 MPS를 사용하며 ANE를 직접 쓰지 않습니다. 네이티브 ANE를 쓰려면 Core ML 변환이 필요합니다.
- 2026년 iOS 앱에서 가장 현실적인 경로: INT4 가중치 + FP16 활성값(activation)으로 Core ML 사용.

### Qualcomm Hexagon (Snapdragon X Elite / 8 Gen 4)

- 최대 45 TOPS. SoC 안에서 CPU, GPU와 통합돼 있지만 메모리 도메인은 분리되어 있습니다.
- QNN(Qualcomm Neural Network) SDK와 AI Hub가 PyTorch/ONNX 변환을 제공합니다.
- 챗 템플릿, Llama 3.2, Phi-3 모두 AI Hub에서 일급 아티팩트로 제공됩니다.

### Intel / AMD NPU (Lunar Lake, Ryzen AI 300)

- 40-50 TOPS. 소프트웨어 생태계가 Apple/Qualcomm보다 늦습니다. OpenVINO가 개선 중이지만 아직 소수 진영입니다.
- Windows ARM 코파일럿 앱에 가장 적합하고, AMD/Intel 데스크톱에서는 로컬 우선(local-first) 용도로 네이티브 지원됩니다.

### WebGPU + WebLLM

- WebGPU 컴퓨트 셰이더로 브라우저에서 모델을 구동합니다. 설치가 필요 없습니다.
- M3 Max에서 Llama 3.1 8B Q4를 초당 약 41 토큰 — 같은 백엔드 기준 네이티브의 약 70-80%입니다.
- WebLLM은 GitHub 스타 17.6k, OpenAI 호환 JS API, Apache 2.0 라이선스입니다.
- 2026년 커버리지: Chrome Android v121+, Safari iOS 26 GA(정식 출시), Firefox Android는 아직 따라잡는 중. 전체 모바일 커버리지 약 70-75%.

### NVIDIA Jetson 계열

- Orin Nano Super(8GB): Llama 3.2 3B, Phi-3를 준수한 토큰 속도로 담을 수 있습니다.
- AGX Orin: vLLM으로 gpt-oss-20b를 초당 약 40 토큰으로 구동합니다.
- Thor / T4000 (JetPack 7.1): AGX Orin의 2배 성능, EAGLE-3와 NVFP4 지원.
- TensorRT Edge-LLM(2026)은 EAGLE-3 추측 디코딩(speculative decoding), NVFP4 가중치, 청크 프리필을 지원합니다 — 데이터센터 최적화 기법들을 엣지로 옮겨온 것입니다.

### 타깃별 양자화 선택

| 타깃 | 포맷 | 비고 |
|--------|--------|-------|
| Apple ANE | INT4 가중치 + FP16 활성값 | Core ML 변환 경로 |
| Qualcomm Hexagon | QNN INT8 / INT4 | AI Hub 변환기 |
| WebGPU / WebLLM | Q4 MLC (q4f16_1) | `mlc_llm convert_weight` + 컴파일된 `.wasm` 사용; GGUF는 미지원 |
| Jetson Orin Nano | Q4 GGUF 또는 TRT-LLM INT4 | 메모리 병목 |
| Jetson AGX / Thor | NVFP4 + FP8 KV | Edge-LLM 경로 |

### 엣지에서의 롱 컨텍스트 함정

Llama 3.1의 128K 컨텍스트는 데이터센터용 기능입니다. RAM 8 GB짜리 휴대폰에서는 모델 4 GB + 32K 토큰용 KV 캐시 2 GB + OS 오버헤드 = 메모리 부족(OOM)입니다. 엣지 배포는 공격적인 KV 양자화(Q4 KV)를 받아들이지 않는 한 컨텍스트를 4K-8K로 유지합니다.

### 음성이 바로 킬러 앱입니다

음성 에이전트는 지연 시간에 민감합니다(첫 토큰 500ms 미만). 로컬 추론은 네트워크 지연을 아예 없애버립니다. 음성 인식(speech-to-text, 엣지에서 돌아가는 Whisper Turbo 변형들)과 결합하면 엣지 추론이 곧 프로덕션(운영 환경) 수준의 음성 루프가 됩니다.

### 기억해야 할 숫자들

- Apple M4 / A18 ANE: 38 TOPS.
- Qualcomm Hexagon SD X Elite: 45 TOPS.
- WebLLM M3 Max: Llama 3.1 8B Q4 기준 초당 약 41 토큰.
- AGX Orin: vLLM으로 gpt-oss-20b 기준 초당 약 40 토큰.
- 데이터센터-엣지 대역폭 격차: 30-50배.
- WebGPU 모바일 커버리지: 약 70-75% (Firefox Android가 뒤처져 있음).

```figure
edge-bandwidth-pipe
```

## 활용하기

`code/main.py`는 대역폭 병목 수학식으로 엣지 타깃별 이론 디코드 처리량 상한을 계산합니다. 관측된 벤치마크와 비교하고, 병목이 연산이 아니라 대역폭인 지점을 짚어줍니다.

## 출시하기

이 레슨은 `outputs/skill-edge-target-picker.md`를 산출합니다. 플랫폼(iOS/Android/브라우저/Jetson), 모델, 지연 시간/메모리 예산이 주어지면 양자화 포맷과 변환 파이프라인을 골라줍니다.

## 연습 문제

1. `code/main.py`를 실행하세요. Snapdragon 8 Gen 3(대역폭 약 77 GB/s)에서 Q4 7B 모델의 디코드 상한을 계산해 보세요. 관측된 초당 6-8 토큰과 비교하면, 런타임이 효율적이라고 볼 수 있습니까?
2. Android에서 WebGPU는 Chrome v121+가 필요합니다. 구형 브라우저를 위한 폴백(fallback)을 설계해 보세요 — 같은 OpenAI 호환 API를 쓰는 서버 측 처리로요.
3. 당신의 iOS 앱에 4K 컨텍스트 스트리밍이 필요합니다. iPhone 16에서 활성 메모리 4 GB 이하를 유지하려면 어떤 모델/포맷 조합을 써야 할까요?
4. Jetson AGX Orin은 gpt-oss-20b를 초당 40 토큰으로 구동하지만 Jetson Nano에는 3B만 들어갑니다. 제품이 둘 다 타깃이라면 추론 스택을 어떻게 통일하시겠습니까?
5. "WebLLM은 2026년에 프로덕션 준비가 됐는가"에 대해 논증해 보세요. 커버리지, 성능, Firefox Android 공백을 근거로 제시하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|----------------|------------------------|
| ANE | "Apple 신경망 엔진" | M시리즈·A시리즈 칩 안의 온디바이스 NPU; 통합 메모리 |
| Hexagon | "Qualcomm NPU" | Snapdragon NPU; QNN SDK로 접근 |
| WebGPU | "브라우저 GPU" | W3C 표준 브라우저 GPU API; Chrome/Safari 2026 |
| WebLLM | "브라우저 LLM 런타임" | MLC-LLM 프로젝트; Apache 2.0; OpenAI 호환 JS |
| Jetson | "NVIDIA 엣지" | Orin Nano / AGX / Thor / T4000 계열 |
| TRT Edge-LLM | "엣지용 TensorRT" | TensorRT-LLM의 2026년 엣지 포팅; EAGLE-3 + NVFP4 |
| 통합 메모리 | "공유 풀" | CPU와 NPU가 같은 RAM을 봄; 복사 오버헤드 없음 |
| 대역폭 병목 | "메모리 한계" | 가중치를 초당 몇 바이트 읽는지가 디코드를 제한 |
| Core ML | "Apple 변환 프레임워크" | ANE 네이티브 모델을 위한 Apple 프레임워크 |
| QNN | "Qualcomm 스택" | Qualcomm Neural Network SDK |

## 더 읽을거리

- [On-Device LLMs State of the Union 2026](https://v-chandra.github.io/on-device-llms/) — 현황과 벤치마크.
- [NVIDIA Jetson Edge AI](https://developer.nvidia.com/blog/getting-started-with-edge-ai-on-nvidia-jetson-llms-vlms-and-foundation-models-for-robotics/) — Orin / AGX / Thor.
- [NVIDIA TensorRT Edge-LLM](https://developer.nvidia.com/blog/accelerating-llm-and-vlm-inference-for-automotive-and-robotics-with-nvidia-tensorrt-edge-llm/) — 2026년 엣지 포팅 발표.
- [WebLLM (arXiv:2412.15803)](https://arxiv.org/html/2412.15803v2) — 설계와 벤치마크.
- [Apple Core ML](https://developer.apple.com/documentation/coreml) — ANE 네이티브 변환.
- [Qualcomm AI Hub](https://aihub.qualcomm.com/) — Hexagon용 사전 변환 모델.
