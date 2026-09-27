---
name: skill-quantization
description: 하드웨어, 품질, 지연 시간 제약 조건에 따라 LLM 배포에 맞는 양자화 전략을 선택합니다
version: 1.0.0
phase: 10
lesson: 11
tags: [quantization, inference, deployment, optimization, fp8, int4, int8, gptq, awq, gguf]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-quantization.md](skill-quantization.md)

# 양자화 의사결정 프레임워크

언어 모델을 배포할 때 이 프레임워크를 사용해 올바른 숫자 형식, 양자화 방법, 품질 검증 전략을 선택하세요.

## 입력 요구 사항

다음을 제공합니다:
- **모델** (이름, 파라미터 수, 원본 정밀도)
- **대상 하드웨어** (GPU 모델/VRAM, CPU, Apple Silicon, 엣지 기기)
- **지연 시간 목표** (초당 토큰 수, 첫 토큰까지의 시간)
- **품질 하한선** (허용 가능한 최대 퍼플렉시티 증가, 벤치마크 차이)
- **서빙 패턴** (배치 크기, 최대 컨텍스트 길이, 동시 사용자 수)

## 빠른 선택표

| 여러분의 상황 | 형식 | 방법 | 예상 품질 손실 |
|---------------|--------|--------|----------------------|
| H100 GPU, 최대 처리량 | FP8 E4M3 | H100 네이티브 캐스팅 | < 0.1% |
| A100/A10, 2배 처리량 필요 | INT8 | LLM.int8() 또는 SmoothQuant | < 0.5% |
| 24GB GPU 한 장, 70B 모델 | INT4 | AWQ 또는 GPTQ | 1-3% |
| 맥북 / Apple Silicon | INT4 GGUF | llama.cpp의 Q4_K_M | 1-2% |
| 모바일 / 엣지 기기 | INT4 또는 INT3 | QAT + 기기별 최적화 | 2-5% |
| 최대 압축, 일부 손실 감수 | INT2 | QuIP# 또는 AQLM | 5-15% |
| 학습 (혼합 정밀도) | BF16 + FP32 누적 | 프레임워크 네이티브 지원 | 0% |

## 구성 요소별 정밀도 선택

모든 텐서에 똑같은 처우를 해줄 필요는 없습니다.

| 구성 요소 | 안전한 최소치 | 권장 | 피할 것 |
|-----------|-------------|-------------|-------|
| FFN 가중치 | INT4 | INT4 (AWQ/GPTQ) | QAT 없는 INT2 |
| 어텐션 가중치 | INT4 | INT8 또는 FP8 | INT2 |
| 임베딩 레이어 | INT8 | FP16 (원본 유지) | INT4 |
| 출력 헤드 | INT8 | FP16 (원본 유지) | INT4 |
| KV 캐시 | FP8 | FP8 또는 INT8 | 긴 컨텍스트에서 INT4 |
| 어텐션 로짓 | FP16 | FP16 또는 BF16 | INT8 |
| 활성값 (추론) | INT8 | FP8 또는 INT8 | INT4 |

## 방법 비교

### GPTQ
- **언제:** GPU 추론, Hugging Face 호환 모델이 필요할 때
- **캘리브레이션 데이터:** 2048 토큰짜리 예시 128개
- **시간:** A100에서 70B 기준 30-60분
- **도구:** `auto-gptq`, `exllama`, `exllamav2`
- **강점:** 검증이 잘 되어 있고 Hugging Face에 거대한 모델 동물원(zoo)이 있음
- **약점:** AWQ보다 적용이 느리고, 일부 모델에서 품질이 AWQ보다 약간 낮음

### AWQ
- **언제:** GPU 추론, 비트당 최고 품질을 원할 때
- **캘리브레이션 데이터:** 예시 128개
- **시간:** A100에서 70B 기준 15-30분
- **도구:** `autoawq`, `vLLM` (네이티브 지원)
- **강점:** 최고의 INT4 품질, 빠른 적용, vLLM 통합
- **약점:** GPTQ보다 모델 zoo가 작음

### GGUF
- **언제:** CPU 추론, Apple Silicon, llama.cpp 생태계
- **변형:** Q2_K, Q3_K_S/M/L, Q4_K_S/M, Q5_K_S/M, Q6_K, Q8_0, F16
- **권장 기본값:** Q4_K_M (최고의 품질/크기 균형)
- **도구:** `llama.cpp`, `ollama`, `LM Studio`
- **강점:** 자기 완결형 파일, 혼합 정밀도, 거대한 생태계
- **약점:** GPU에는 최적이 아님 (CPU/Metal용으로 설계됨)

### SmoothQuant
- **언제:** GPU에서 INT8, 가중치와 활성값을 모두 양자화해야 할 때
- **핵심 아이디어:** 채널별 스케일링으로 양자화 난이도를 활성값에서 가중치로 옮김
- **도구:** `smoothquant`, `TensorRT-LLM`
- **강점:** W8A8(가중치와 활성값 모두 INT8)을 가능하게 해 2배 가속
- **약점:** INT8 전용, INT4로 확장 안 됨

## 품질 검증 프로토콜

양자화 후에는 배포 전에 검증하세요:

1. **퍼플렉시티 테스트.** WikiText-2 또는 여러분의 도메인 코퍼스에서 계산합니다. 차이 < 0.5는 훌륭, 0.5-1.0은 양호, > 2.0은 문제입니다.

2. **벤치마크 스윕.** MMLU(일반), GSM8K(수학), HumanEval(코드)을 돌려 봅니다. 수학과 코드가 정밀도 손실에 가장 민감합니다.

3. **출력 비교.** 원본 모델과 양자화 모델에서 각각 100개의 응답을 생성합니다. LLM-as-judge로 승률을 계산합니다. 목표: 프롬프트의 90% 이상에서 양자화 모델이 이기거나 비기기.

4. **지연 시간 측정.** 배치 크기 1과 여러분의 목표 배치 크기에서 초당 토큰 수를 측정합니다. 속도 향상이 품질 비용을 정당화하는지 확인하세요.

5. **긴 컨텍스트 테스트.** 긴 컨텍스트(4K 토큰 초과)를 서빙한다면 최대 컨텍스트 길이에서 테스트하세요. KV 캐시 양자화 오차는 시퀀스 길이에 따라 누적됩니다.

## 메모리 예산 계산기

```
Weight memory (GB) = parameters (B) * bits / 8 / 1.073741824
KV cache per token (MB) = 2 * num_layers * d_model * bits / 8 / 1048576
KV cache for context (GB) = kv_per_token * max_context_length / 1024
Activation memory (GB) ~ 1-4 GB (비교적 일정, 배치 크기에 따라 달라짐)
Total = weight_memory + kv_cache + activation_memory + 오버헤드 (10-20%)
```

INT4, 32K 컨텍스트의 Llama 3 70B 예시:
- 가중치: 70B * 4 / 8 / 1.07 = 32.6 GB
- KV 캐시 (FP16): 2 * 80 * 8192 * 16 / 8 / 1e9 * 32768 = ~40 GB
- KV 캐시 (FP8): ~20 GB
- FP8 KV 포함 총계: ~55 GB (80GB A100 한 장에 들어감)

## 흔한 실수

| 실수 | 실패하는 이유 | 해결책 |
|---------|-------------|-----|
| 임베딩 레이어를 INT4로 양자화 | 첫 레이어가 오차를 모델 전체로 증폭 | 임베딩은 FP16 또는 INT8로 유지 |
| INT4에 텐서별 스케일 사용 | 이상치 행 하나가 모든 행의 정밀도를 파괴 | 채널별 또는 그룹별 스케일 사용 |
| GPTQ/AWQ 캘리브레이션 생략 | 대표적인 데이터 없이는 스케일 팩터가 틀림 | 여러분의 도메인에서 예시 128개 사용 |
| 모든 레이어에 같은 비트 폭 | 첫/마지막 레이어가 더 민감 | 혼합 정밀도: 첫/마지막에 더 높은 비트 |
| 아주 긴 컨텍스트에서 KV 캐시 양자화 | 오차가 시퀀스 길이에 따라 이차적으로 누적 | KV 캐시는 INT4가 아니라 FP8 사용 |
| 품질 검증 생략 | 일부 모델은 양자화가 잘 안 됨 (특히 경계 지점에서) | 항상 퍼플렉시티 + 과제 eval 실행 |

## 배포 레시피

### 레시피 1: vLLM + AWQ (GPU 서버)
```
pip install vllm autoawq
vllm serve model-awq --quantization awq --dtype half --max-model-len 8192
```

### 레시피 2: llama.cpp + GGUF (맥북)
```
./llama-server -m model.Q4_K_M.gguf -c 4096 -ngl 99
```

### 레시피 3: TensorRT-LLM + FP8 (H100)
```
trtllm-build --model_dir model --output_dir engine --dtype float16 --use_fp8
```
