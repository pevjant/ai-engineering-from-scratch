---
name: edge-target-picker
description: 기기, 모델, 지연 시간 예산이 주어지면 엣지 추론 타깃(Apple ANE, Qualcomm Hexagon, WebGPU/WebLLM, NVIDIA Jetson)과 그에 맞는 양자화 포맷을 골라 줍니다.
version: 1.0.0
phase: 17
lesson: 12
tags: [edge, ane, hexagon, webgpu, webllm, jetson, core-ml, qnn, nvfp4]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-edge-target-picker.md](skill-edge-target-picker.md)

배포 플랫폼(iOS, Android, 브라우저, 로봇/자동차/엣지 서버), 모델, 지연 시간/메모리 예산이 주어지면 엣지 타깃 추천을 만들어 냅니다.

산출물:

1. 타깃. 구체적인 NPU/GPU 이름(ANE, Hexagon, WebGPU, Jetson Orin Nano / AGX / Thor)을 말합니다. 플랫폼과 2026년 런타임 커버리지를 근거로 정당화합니다.
2. 대역폭 상한. 이론상 디코드 상한을 계산합니다: bandwidth_GB_s / model_size_GB. 사용자의 토큰/초 요구치와 비교하세요. 상한이 요구치보다 낮으면 거절하거나 더 작은 모델 / 더 공격적인 양자화를 제안합니다.
3. 양자화 포맷. Q4 GGUF(브라우저/엣지 CPU), Core ML INT4 + FP16(ANE), QNN INT8/INT4(Hexagon), NVFP4 + FP8 KV(Jetson Thor / Edge-LLM) 중에서 고릅니다.
4. 변환 파이프라인. 정확한 변환기 이름(Core ML converter, Qualcomm AI Hub, WebLLM용 MLC-LLM, TensorRT-LLM Edge 컴파일러)을 말합니다.
5. 컨텍스트 예산. 기기 RAM 안에서 가중치와 함께 들어갈 수 있는 최대 컨텍스트를 밝힙니다. 롱 컨텍스트 사용 사례에는 KV 양자화(Q4 KV)를 명시하거나 거절합니다.
6. 폴백. 기기가 역부족이거나 WebGPU를 쓸 수 없을 때(Firefox Android, 구형 브라우저), 같은 OpenAI 호환 인터페이스를 쓰는 서버 측 API 폴백을 명시합니다.

하드 리젝(무조건 거절):

- 대역폭 상한을 넘는 토큰/초를 약속하는 것. 거절하세요 — 물리 법칙입니다.
- 2026년에 Core ML이 아닌 런타임으로 ANE를 직접 노리는 것. 네이티브로 ANE를 여는 길은 Core ML뿐입니다.
- WebGPU가 모든 브라우저에 있다고 가정하는 것. 2026년 커버리지는 모바일 약 70-75%입니다. 항상 폴백을 명시하세요.

거절 규칙:

- 모델이 6 GB를 넘는데 타깃이 휴대폰(RAM 4-8 GB)이라면 거절 — 더 작은 모델이나 공격적인 양자화를 먼저 제안합니다.
- iPhone에서 7B 모델로 128K 컨텍스트 요청이라면 거절 — Q4 KV에 슬라이딩 윈도우 어텐션까지 더하지 않으면 기기 RAM에 들어갈 수 없습니다.
- Android에서 WebGPU로 롱 컨텍스트 스트리밍이 필요한데 Firefox 지원이 요구된다면 거절하고 Chrome 또는 서버 폴백을 요구합니다.

출력: 타깃, 상한, 양자화, 변환기, 컨텍스트 예산, 폴백을 적은 한 페이지짜리 계획서. 마지막에 단 하나의 지표로 마무리합니다: 타깃 플릿(기기 묶음)에서 가장 열악한 기기에서 관측된 토큰/초.
