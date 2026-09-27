> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 프로덕션(운영 환경) 양자화 — AWQ, GPTQ, GGUF K-quant, FP8, MXFP4/NVFP4

> 양자화 포맷은 만능 선택이 아닙니다. 하드웨어, 서빙 엔진, 워크로드의 함수입니다. GGUF Q4_K_M이나 Q5_K_M은 CPU와 엣지를 지배하며, llama.cpp와 Ollama로 전달됩니다. GPTQ는 같은 베이스 위에서 멀티-LoRA가 필요할 때 vLLM 안에서 이깁니다. AWQ는 Marlin-AWQ 커널로 7B급 모델에서 초당 약 741 토큰과 INT4 중 최고의 Pass@1을 냅니다 — 데이터센터 프로덕션의 2026년 기본값입니다. FP8은 Hopper, Ada, Blackwell에서 신뢰할 수 있는 중간 지대입니다 — 거의 무손실이고 지원 폭이 넓습니다. NVFP4와 MXFP4(Blackwell 마이크로스케일링)는 공격적이고 블록별 검증이 필요합니다. 팀들을 물어 오는 함정은 둘입니다. 캘리브레이션 데이터셋은 배포 도메인과 맞아야 하고, KV 캐시는 가중치 양자화와 별개라는 점입니다 — AWQ 레슨의 "이제 내 모델은 4GB"라는 말은 프로덕션 배치 크기에서 10~30GB를 차지하는 KV 캐시를 잊은 겁니다.

**유형:** Learn
**언어:** Python (표준 라이브러리, 포맷별 메모리·처리량을 비교하는 장난감 수준 도구)
**선수 지식:** Phase 10 · 13 (양자화 기초), Phase 17 · 04 (서빙 엔진 내부 구조)
**시간:** 약 75분

## 학습 목표

- 2026년의 여섯 프로덕션 양자화 포맷과 각각의 스위트 스팟을 말할 수 있다.
- 하드웨어(CPU vs GPU, Hopper vs Blackwell), 엔진(vLLM, TRT-LLM, llama.cpp), 워크로드(루틴 채팅, 추론, 멀티-LoRA)가 주어지면 포맷을 고를 수 있다.
- 선택한 포맷으로 절약되는 가중치 메모리와, 손대지 않은(그대로 남는) KV 캐시를 계산할 수 있다.
- 도메인 트래픽에서 양자화된 모델을 망가뜨리는 캘리브레이션 데이터셋 함정을 말할 수 있다.

## 문제 상황

양자화는 메모리와 HBM 대역폭을 줄이는데, 그건 디코드가 정확히 원하는 것입니다. FP16 70B 모델은 가중치가 140GB입니다. 가중치를 INT4(AWQ 또는 GPTQ)로 양자화하면 35GB가 됩니다 — H100 한 장에 KV 캐시 자리까지 남습니다. 이게 중요한 이유는, 2k 컨텍스트의 동시 128 시퀀스에서 KV 캐시만 20~30GB이기 때문입니다.

하지만 양자화는 공짜가 아닙니다. 공격적인 양자화는 품질을 깎고, 특히 추론 사고가 많은 태스크에서 그렇습니다. 포맷마다 호환되는 엔진이 다릅니다. 하드웨어마다 기본 지원하는 정밀도가 다릅니다. 2026년의 포맷 동물원은 실재하고, 남의 선택을 베낄 수는 없습니다 — 자기 스택에 기반해 골라야 합니다.

## 개념

### 여섯 포맷

| 포맷 | 비트 | 스위트 스팟 | 엔진 |
|--------|------|-----------|---------|
| GGUF Q4_K_M / Q5_K_M | 4-5 | CPU, 엣지, 노트북 | llama.cpp, Ollama |
| GPTQ | 4-8 | vLLM의 멀티-LoRA | vLLM, TGI |
| AWQ | 4 | 데이터센터 GPU 프로덕션 | vLLM (Marlin-AWQ), TGI |
| FP8 | 8 | Hopper/Ada/Blackwell 데이터센터 | vLLM, TRT-LLM, SGLang |
| MXFP4 | 4 | Blackwell 멀티 유저 | TRT-LLM |
| NVFP4 | 4 | Blackwell 멀티 유저 | TRT-LLM |

### GGUF — CPU/엣지 기본값

GGUF는 파일 포맷이지 양자화 방식 그 자체는 아닙니다 — K-quant 변형들(Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0)을 하나의 컨테이너에 담습니다. Q4_K_M과 Q5_K_M이 프로덕션 기본값입니다 — 4~5비트로 거의 BF16급 품질입니다. CPU나 엣지 서빙이라는 배포 목표라면 최선의 선택입니다. llama.cpp가 CPU 추론 엔진 중 압도적으로 빠르니까요.

vLLM에서의 처리량 페널티: 7B 기준 약 93 tok/s — 이 포맷은 GPU 커널에 맞춰 최적화되어 있지 않습니다. 배포 대상이 CPU/엣지일 때 GGUF를 쓰세요. 그 외에는 쓰지 마세요.

### GPTQ — vLLM의 멀티-LoRA

GPTQ는 캘리브레이션 패스를 거치는 학습 후(post-training) 양자화 알고리즘입니다. Marlin 커널이 GPU에서 빠르게 해 줍니다(비 Marlin GPTQ 대비 2.6배 가속). 7B 기준 약 712 tok/s.

고유한 강점: GPTQ-Int4는 vLLM에서 LoRA 어댑터를 지원합니다. 베이스 모델에 파인튜닝 변형 10~50개(각각 LoRA)를 서빙한다면 GPTQ가 경로입니다. NVFP4는 2026년 초 기준 아직 LoRA를 지원하지 않습니다.

### AWQ — 데이터센터 GPU 기본값

Activation-aware Weight Quantization(활성값 인지 가중치 양자화). 양자화 중 가장 영향력 큰 약 1%의 가중치를 보호합니다. Marlin-AWQ 커널: 순진한 구현 대비 10.9배 가속. 7B 기준 약 741 tok/s, INT4 포맷 중 최고 Pass@1.

멀티-LoRA가 필요하다거나(GPTQ) 공격적인 Blackwell FP4(NVFP4)가 필요한 경우가 아니라면, 새 GPU 서빙에는 AWQ를 고르세요.

### FP8 — 믿을 수 있는 중간 지대

8비트 부동소수점. 거의 무손실. 지원 폭이 넓습니다. Hopper Tensor Cores가 FP8을 기본 가속합니다. Blackwell도 물려받았습니다. 품질이 협상 불가능할 때(추론, 의료, 코드 생성) FP8이 2026년의 안전한 기본값입니다. 메모리 절약은 INT4의 절반이지만 품질 위험은 훨씬 낮습니다.

### MXFP4 / NVFP4 — Blackwell의 공격 카드

마이크로스케일링 FP4. 가중치 블록마다 자체 스케일 팩터를 갖습니다. 공격적이지만 Blackwell Tensor Cores에서 하드웨어 가속됩니다. FP8 대비 토큰당 바이트를 절반으로 줄입니다 — Phase 17 · 07의 경제적 이득이 이것입니다.

주의사항:
- 아직 LoRA 미지원(2026년 초 기준).
- 추론 사고가 많은 워크로드에서 품질 저하가 눈에 보임.
- 모델별로 여러분의 eval 세트에서 검증할 것.

### 캘리브레이션 함정

AWQ와 GPTQ는 캘리브레이션 데이터셋이 필요합니다 — 보통 C4나 WikiText를 씁니다. 도메인 모델(코드, 의료, 법률)을 범용 웹 텍스트로 캘리브레이션하면, 알고리즘이 어떤 가중치를 보호할지 잘못 판단합니다. HumanEval의 Pass@1이 몇 포인트 떨어질 수 있습니다.

해법: 도메인 내 데이터로 캘리브레이션하세요. 도메인 샘플 수백 개면 보통 충분합니다. 출시 전에 eval 세트로 테스트하세요.

### KV 캐시 함정

AWQ는 가중치를 4비트로 줄입니다. KV 캐시는 별개이고 FP16/FP8 그대로입니다. AWQ를 쓴 70B 모델 기준:

- 가중치: 약 35GB (140GB → INT4).
- KV 캐시(동시 128 × 2k 컨텍스트): 약 20GB.
- 활성값: 약 5GB.
- 합계: 약 60GB — H100 80GB에 들어감.

"모델을 4GB로 양자화했다"는 순진한 계산은 나머지 30~50GB를 잊은 겁니다. HBM은 통째로 예산 잡으세요.

별개의 이야기로, KV 캐시 양자화(FP8 KV 또는 INT8 KV)는 자체 트레이드오프가 있는 별개의 선택입니다 — 어텐션 정확도에 직접 영향을 주며 공짜 이득이 아닙니다.

### AWQ INT4는 추론 사고에 위험하다

사고의 연쇄, 수학, 긴 컨텍스트 코드 생성 — 이런 것들은 공격적 양자화의 타격이 눈에 띕니다. AWQ INT4는 MATH에서 약 3~5포인트를 잃습니다. 추론 사고가 많은 워크로드에는 FP8이나 BF16으로 출시하고 메모리 비용을 감수하세요.

### 2026년 선택 가이드

- CPU/엣지 서빙: GGUF Q4_K_M. 끝.
- GPU 서빙, 루틴 채팅, LoRA 없음: AWQ.
- GPU 서빙, 멀티-LoRA: Marlin을 얹은 GPTQ.
- 추론 워크로드: FP8.
- Blackwell 데이터센터, 품질 검증 완료: NVFP4 + FP8 KV.
- 애매하다면: 후보 포맷마다 1,000샘플 eval을 돌려 보세요.

```figure
gpu-memory-breakdown
```

## 직접 써보기

`code/main.py`는 여러 모델 크기에 대해 여섯 포맷의 메모리 점유(가중치 + KV + 활성값)와 상대 처리량을 계산합니다. KV 캐시가 지배하는 지점, 가중치 압축이 값을 하는 지점, FP8이 안전한 선택인 지점을 보여줍니다.

## 산출물

이 레슨은 `outputs/skill-quantization-picker.md`를 만듭니다. 하드웨어, 모델 크기, 워크로드 유형, 품질 허용치가 주어지면 포맷을 골라 캘리브레이션/검증 계획을 만들어 줍니다.

## 연습 문제

1. `code/main.py`를 실행하세요. 2k 컨텍스트의 동시 128에서 70B 모델의 포맷별 총 HBM을 계산하세요. H100 80GB 한 장에 들어가는 포맷은 무엇인가요?
2. 7B 코딩 모델이 있습니다. 포맷을 고르고 근거를 대세요. 품질 허용치 판단이 틀렸다면 회복 경로는 무엇인가요?
3. 의료 도메인 모델의 AWQ를 캘리브레이션하는 데 필요한 캘리브레이션 데이터셋 크기를 계산해 보세요. 데이터가 많다고 항상 좋은 건 아닌 이유는 무엇인가요?
4. Marlin-AWQ 커널 논문이나 릴리스 노트를 읽으세요. AWQ가 7B에서 741 tok/s에 도달하는 반면 날것 GPTQ는 약 712인 이유를 세 문장으로 설명하세요.
5. AWQ 가중치에 FP8 KV 캐시를 조합하는 것이 BF16 KV를 유지하는 것보다 합리적인 때는 언제인가요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| GGUF | "llama.cpp 포맷" | K-quant 변형을 묶은 파일 포맷. CPU/엣지 기본값 |
| Q4_K_M | "Q4 K M" | 4비트 K-quant 미디엄. 프로덕션 GGUF 기본값 |
| GPTQ | "지피티큐" | 캘리브레이션을 거치는 학습 후 INT4. vLLM에서 LoRA 지원 |
| AWQ | "에이더블유큐" | 활성값 인지 INT4. Marlin 커널. INT4 중 최고 Pass@1 |
| Marlin 커널 | "빠른 INT4 커널" | Hopper의 INT4용 커스텀 CUDA 커널. 10배 가속 |
| FP8 | "8비트 부동소수점" | Hopper/Ada/Blackwell의 안전한 정밀도 기본값 |
| MXFP4 / NVFP4 | "마이크로스케일링 포" | 블록별 스케일 팩터를 갖는 Blackwell 4비트 FP |
| 캘리브레이션 데이터셋 | "캘 데이터" | 양자화 파라미터를 고를 때 쓰는 입력 텍스트. 도메인과 맞아야 함 |
| KV 캐시 양자화 | "KV INT8" | 가중치와 별개의 선택. 어텐션 정확도에 영향 |

## 더 읽을거리

- [VRLA Tech — LLM Quantization 2026](https://vrlatech.com/llm-quantization-explained-int4-int8-fp8-awq-and-gptq-in-2026/) — 비교 벤치마크.
- [Jarvis Labs — vLLM Quantization Complete Guide](https://jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks) — 포맷별 처리량 숫자.
- [PremAI — GGUF vs AWQ vs GPTQ vs bitsandbytes 2026](https://blog.premai.io/llm-quantization-guide-gguf-vs-awq-vs-gptq-vs-bitsandbytes-compared-2026/) — 포맷별 선택 가이드.
- [vLLM docs — Quantization](https://docs.vllm.ai/en/latest/features/quantization/index.html) — 지원 포맷과 플래그.
- [AWQ 논문 (arXiv:2306.00978)](https://arxiv.org/abs/2306.00978) — 최초의 AWQ 정식화.
- [GPTQ 논문 (arXiv:2210.17323)](https://arxiv.org/abs/2210.17323) — 최초의 GPTQ 정식화.
