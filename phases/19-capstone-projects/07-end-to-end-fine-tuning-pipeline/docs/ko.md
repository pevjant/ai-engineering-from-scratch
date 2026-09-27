> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 07 — 끝까지 파인튜닝 파이프라인 (데이터부터 SFT, DPO, 서빙까지)

> 당신의 데이터로 학습한 8B 모델, 당신의 선호로 DPO 정렬한 모델, 양자화하고, 스페큘러티브 디코딩을 얹고, 측정 가능한 $/1M 토큰으로 서빙하는 것. 2026년 오픈 스택은 Axolotl v0.8, TRL 0.15, 반복 실험용 Unsloth, 양자화용 GPTQ/AWQ/GGUF, 서빙용 vLLM 0.7 + EAGLE-3입니다. 이 캡스톤은 전체 파이프라인을 재현 가능하게 돌리는 것입니다 — YAML을 넣으면 서빙 엔드포인트가 나옵니다 — 그리고 2026 Model Openness Framework 아래 모델 카드를 내놓는 것입니다.

**유형:** Capstone
**언어:** Python (파이프라인), YAML (설정), Bash (스크립트)
**선수 지식:** 페이즈 2 (ML), 페이즈 3 (DL), 페이즈 7 (트랜스포머), 페이즈 10 (스크래치 LLM), 페이즈 11 (LLM 엔지니어링), 페이즈 17 (인프라), 페이즈 18 (안전)
**활용하는 페이즈:** P2 · P3 · P7 · P10 · P11 · P17 · P18
**시간:** 35시간

## 문제

2026년 제대로 된 AI 팀이라면 파인튜닝 파이프라인을 상시 대기시켜 둡니다. 프론티어 베이스 모델을 출시해서가 아닙니다. 측정 가능한 승리가 사는 곳은 다운스트림 적응이기 때문입니다 — 도메인 SFT, 라벨된 선호에 대한 DPO, 스페큘러티브 디코딩용 증류 초안, EAGLE-3로 서빙. Axolotl v0.8은 멀티 GPU SFT 설정을 다루고, TRL 0.15는 DPO와 GRPO를 다루고, Unsloth는 빠른 단일 GPU 반복을 가능케 하고, vLLM 0.7 + EAGLE-3는 품질 손실 없이 디코딩 처리량을 2~3배 밀어 올립니다. 도구는 동작합니다. 기술은 YAML과 데이터 위생, 평가 규율에 있습니다.

당신은 8B 베이스(Llama 3.3, Qwen3, 또는 Gemma 3)를 작업 특화 데이터로 SFT 후 DPO까지 돌리고, 서빙을 위해 양자화하고, lm-evaluation-harness, RewardBench-2, MT-Bench-v2, MMLU-Pro 대비 이득을 측정하게 됩니다. 2026 Model Openness Framework 아래 모델 카드를 만들어 냅니다. 핵심은 재현성입니다 — 명령 하나가 파이프라인 전체를 끝까지 다시 돌립니다.

## 개념

파이프라인은 다섯 단계입니다. **데이터**: 중복 제거(MinHash / Datatrove), 품질 필터(Nemotron-CC 방식 분류기), PII 제거, 공개 벤치마크 오염에 대한 분할 위생 점검. **SFT**: Axolotl YAML, 8xH100의 ZeRO-3, 코사인 스케줄, 패킹된 시퀀스, 2~3 에포크. **DPO 또는 GRPO**: TRL 설정, 1 에포크, 선호 쌍은 사람이 라벨하거나 모델이 판정, 베타 튜닝. **양자화**: 배포 유연성을 위한 GPTQ + AWQ + GGUF. **서빙**: EAGLE-3 스페큘러티브 헤드를 갖춘 vLLM 0.7(또는 SpecForge가 있는 SGLang), K8s 배포, 큐 대기 기반 HPA.

소거 실험(ablation)이 산출물입니다: 세 개의 작업 특화 벤치마크에서 SFT만 vs SFT+DPO vs SFT+GRPO. 서빙 지표: 배치 1 / 8 / 32의 tokens/s, EAGLE-3 수용률, $/1M 토큰. 안전 평가: Llama Guard 4 통과율. 모델 카드: 편향 평가, 재현성 시드, 데이터 라이선싱.

## 아키텍처

```
raw data (HF datasets + internal)
    |
    v
Datatrove dedup + Nemotron-CC quality filter + PII scrub
    |
    v
split hygiene (MMLU-Pro contamination check)
    |
    v
Axolotl SFT config (YAML)  ---> 8xH100, ZeRO-3
    |
    v
TRL DPO / GRPO config       ---> 4xH100, 1 epoch
    |
    v
GPTQ + AWQ + GGUF quantize
    |
    v
vLLM 0.7 + EAGLE-3 speculative decoding
    |
    v
K8s deployment, HPA on queue-wait
    |
    v
lm-eval-harness + RewardBench-2 + MT-Bench-v2 + MMLU-Pro
    |
    v
model card (2026 MOF) + safety eval (Llama Guard 4)
```

## 스택

- 데이터: 중복 제거용 Datatrove, 품질용 Nemotron-CC 분류기, PII용 Presidio
- 베이스: Llama 3.3 8B, Qwen3 14B, 또는 Gemma 3 12B
- SFT: ZeRO-3, Flash Attention 3, 패킹된 시퀀스를 갖춘 Axolotl v0.8
- 선호 튜닝: DPO 또는 GRPO용 TRL 0.15; 단일 GPU 반복용 Unsloth
- 양자화: GPTQ (Marlin), AWQ, llama.cpp의 GGUF
- 서빙: EAGLE-3 스페큘러티브 디코딩을 갖춘 vLLM 0.7 (또는 SGLang 0.4 + SpecForge)
- 평가: lm-evaluation-harness, RewardBench-2, MT-Bench-v2, MMLU-Pro
- 안전 평가: Llama Guard 4, ShieldGemma-2
- 인프라: Kubernetes + NVIDIA 디바이스 플러그인, 큐 대기 지표 기반 HPA
- 관측 가능성: 학습용 W&B, 추론용 Langfuse

```figure
ce-finetune-stages
```

## 만들기

1. **데이터 파이프라인.** 날것 코퍼스에 Datatrove 중복 제거를 돌립니다. Nemotron-CC 방식 품질 분류기를 적용합니다. Presidio가 PII를 제거합니다. 명시적 시드로 train/val 분할을 씁니다.

2. **오염 점검.** 검증 분할마다 MMLU-Pro, MT-Bench-v2, RewardBench-2 테스트셋에 대해 MinHash를 계산합니다. 겹침이 있으면 반려합니다.

3. **Axolotl SFT.** ZeRO-3, FA3, 시퀀스 패킹을 넣은 YAML. 8xH100에서 2~3 에포크. W&B로 로깅합니다.

4. **TRL DPO / GRPO.** SFT 체크포인트를 가져와 선호 쌍으로 DPO 1 에포크를 돌립니다(또는 수학/코드에서 검증 가능한 보상으로 GRPO). 베타를 스윕합니다.

5. **양자화.** 양자화본 세 개를 만듭니다: GPTQ-INT4-Marlin, AWQ-INT4, llama.cpp용 GGUF-Q4_K_M. 크기와 명목 처리량을 기록합니다.

6. **스페큘러티브 디코딩으로 서빙.** Red Hat Speculators로 학습한 EAGLE-3 초안 헤드를 붙인 vLLM 0.7 설정. 배치 1 / 8 / 32에서 수용률과 꼬리 지연 시간을 측정합니다. 같은 평가에서 Anthropic / OpenAI 대비 $/1M 토큰을 보고합니다.

7. **평가 행렬.** 베이스, SFT만, SFT+DPO, SFT+GRPO에 대해 lm-eval-harness, RewardBench-2, MT-Bench-v2, MMLU-Pro를 돌립니다. 표로 만듭니다.

8. **안전 평가.** 개발 세트에 대한 Llama Guard 4 통과율. ShieldGemma-2 출력 필터.

9. **모델 카드.** MOF 2026 템플릿: 데이터, 학습, 평가, 안전, 라이선스, 그리고 YAML과 커밋 SHA를 담은 재현성 섹션.

## 사용해 보기

```
$ ./pipeline.sh config/llama3.3-8b-domainX.yaml
[data]    300k deduped, 12k filtered, 280k accepted (seed=7)
[SFT]     3 epochs, 8xH100, 6h12m, val loss 1.42 -> 1.03
[DPO]     1 epoch, beta=0.08, 4xH100, 1h40m
[quant]   GPTQ-INT4 4.6 GB, AWQ-INT4 4.8 GB, GGUF-Q4_K_M 5.1 GB
[serve]   vLLM 0.7, EAGLE-3 acceptance 0.74, p99 126ms @ bs=8
[eval]    MMLU-Pro +3.2, MT-Bench-v2 +0.41, RewardBench-2 +0.08
[card]    model-card.md generated under 2026 MOF
```

## 출시하기

`outputs/skill-finetuning-pipeline.md`가 산출물을 설명합니다. 명령 하나가 데이터에서 SFT, DPO, 양자화, 서빙, 평가까지 이어 돌리고, 모델 카드 + 서빙 엔드포인트를 내놓습니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 베이스 대비 평가 변화 | 목표 작업에서 측정된 이득(MMLU-Pro, MT-Bench-v2, 작업 특화) |
| 20 | 파이프라인 재현성 | 같은 시드로 한 명령이 끝까지 재실행 |
| 20 | 데이터 위생 | 중복 제거율, PII 제거 커버리지, 오염 점검 통과 |
| 20 | 서빙 효율 | bs=1/8/32의 tokens/s, EAGLE-3 수용률, $/1M 토큰 |
| 15 | 모델 카드 + 안전 평가 | 2026 MOF 완전도 + Llama Guard 4 통과율 |
| **100** | | |

## 연습 문제

1. 같은 작업 특화 벤치마크에서 SFT만 vs SFT+DPO vs SFT+GRPO를 돌려 보세요. 어느 선호 튜닝 방법이 이기는지, 얼마나 큰지 보고하세요.

2. Llama 3.3 8B를 Qwen3 14B로 바꿔 보세요. 같은 품질에서 $/1M 토큰을 측정하세요.

3. 일반 ShareGPT 대비 도메인 데이터에서의 EAGLE-3 수용률을 측정하세요. 변화량과 그것이 지연 시간 예산에 주는 의미를 보고하세요.

4. 1%의 오염을 주입하고(MMLU-Pro 답을 학습 데이터에 새어 넣음) 평가를 다시 돌려 보세요. MMLU-Pro 정확도가 비현실적으로 뛰는 걸 지켜보세요. 이걸 잡아내는 오염 점검 CI 게이트를 만드세요.

5. 풀 파인튜닝의 대안으로 LoRA SFT를 추가해 보세요. 메모리를 10배 아끼는 상태에서의 품질 격차를 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 표현 | 실제 의미 |
|------|-----------------|------------------------|
| Axolotl | "SFT 트레이너" | SFT, DPO, 증류를 다루는 YAML 기반 통합 트레이너 |
| TRL | "선호 튜너" | LLM의 DPO, GRPO, PPO를 위한 Hugging Face 라이브러리 |
| GRPO | "그룹 상대 정책 최적화" | 검증 가능한 보상을 쓰는 DeepSeek R1의 RL 레시피 |
| EAGLE-3 | "스페큘러티브 디코딩 초안" | N 토큰 앞을 예측하는 초안 헤드. vLLM이 대상 모델로 검증 |
| MOF | "Model Openness Framework" | 모델 공개를 데이터·코드·라이선스로 등급 매기는 2026 표준 |
| 오염 점검 | "분할 위생" | MinHash 기반으로 테스트셋이 학습에 새어 들었는지 탐지 |
| 수용률 | "EAGLE / MTP 지표" | 초안 토큰 중 대상 모델이 받아들인 비율 |

## 더 읽을거리

- [Axolotl 문서](https://axolotl-ai-cloud.github.io/axolotl/) — 참고용 SFT / DPO 트레이너
- [TRL 문서](https://huggingface.co/docs/trl) — DPO와 GRPO 참고 구현
- [Unsloth](https://github.com/unslothai/unsloth) — 단일 GPU 반복 참고자료
- [DeepSeek R1 논문 (arXiv:2501.12948)](https://arxiv.org/abs/2501.12948) — GRPO 방법론
- [vLLM + EAGLE-3 문서](https://docs.vllm.ai) — 참고용 서빙 스택
- [SGLang SpecForge](https://github.com/sgl-project/SpecForge) — 대안 스페큘러티브 디코딩 트레이너
- [Model Openness Framework 2026](https://isocpp.org/) — 오픈 공개 등급 표준
- [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) — 표준 평가 러너
