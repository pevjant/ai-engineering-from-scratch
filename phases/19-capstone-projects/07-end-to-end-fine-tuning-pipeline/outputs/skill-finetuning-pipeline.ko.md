---
name: finetuning-pipeline
description: 소거 실험과 양자화, 2026 Model Openness Framework 모델 카드를 갖춘 재현 가능한 데이터-SFT-DPO-서빙 파인튜닝 파이프라인을 실행합니다.
version: 1.0.0
phase: 19
lesson: 07
tags: [capstone, fine-tuning, axolotl, trl, dpo, grpo, vllm, eagle-3, mof]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-finetuning-pipeline.md](skill-finetuning-pipeline.md)

베이스 모델(Llama 3.3 8B, Qwen3 14B, 또는 Gemma 3 12B)과 작업 특화 데이터셋이 주어지면, 서빙 엔드포인트와 재현 가능한 모델 카드를 만들어 내는 한 명령짜리 파이프라인을 만듭니다.

만들기 계획:

1. 데이터 단계: Datatrove 중복 제거, Nemotron-CC 방식 품질 필터, Presidio PII 제거, 시드가 고정된 train/val 분할.
2. 오염 점검: MMLU-Pro, MT-Bench-v2, RewardBench-2에 대한 MinHashLSH. 겹침이 있으면 반려.
3. SFT: ZeRO-3, Flash Attention 3, 패킹된 시퀀스를 갖춘 Axolotl v0.8, 8xH100에서 2~3 에포크.
4. 선호 튜닝: TRL 0.15 DPO(또는 검증 가능한 보상의 GRPO) 1 에포크, 베타 스윕.
5. 양자화: GPTQ-INT4-Marlin + AWQ-INT4 + GGUF-Q4_K_M.
6. 서빙: EAGLE-3 스페큘러티브 디코딩을 갖춘 vLLM 0.7(초안 헤드는 Red Hat Speculators 또는 SGLang SpecForge). 큐 대기 기반 HPA가 붙은 K8s 배포.
7. 평가: 베이스/SFT만/SFT+DPO/SFT+GRPO에 걸친 lm-evaluation-harness, RewardBench-2, MT-Bench-v2, MMLU-Pro.
8. 안전: Llama Guard 4 통과율, ShieldGemma-2 출력 필터.
9. 2026 Model Openness Framework 아래의 모델 카드. 데이터, 학습, 평가, 안전, 재현성 섹션 포함.

채점 기준:

| 가중치 | 기준 | 측정 |
|:-:|---|---|
| 25 | 베이스 대비 평가 변화 | MMLU-Pro, MT-Bench-v2, 작업 특화 벤치마크에서 측정된 이득 |
| 20 | 파이프라인 재현성 | 같은 시드로 한 명령 재실행 시 같은 해시 |
| 20 | 데이터 위생 | 중복 제거율, PII 제거 커버리지, 오염 점검 통과 |
| 20 | 서빙 효율 | 배치 1/8/32의 tokens/s, EAGLE-3 수용률, $/1M 토큰 |
| 15 | 모델 카드 + 안전 평가 | 2026 MOF 완전도 + Llama Guard 4 통과율 |

하드 리젝트(무조건 반려):

- MinHash 오염 점검을 건너뛰는 파이프라인. MMLU-Pro를 학습에 새어 넣는 것은 전형적인 평가 부정 실패 모드입니다.
- 시드나 YAML이 붙지 않은 학습 실행. 재현성은 하드 요구사항입니다.
- EAGLE-3나 동등한 스페큘러티브 디코딩 설정 없이 서빙하는 것. 베이스라인 tokens/s는 2026년의 기준이 아닙니다.
- 안전 평가 누락. 모든 파인튜닝은 Llama Guard 4 통과율을 달고 나갑니다.

거절 규칙:

- lm-eval-harness 커밋 SHA를 붙이지 않고 벤치마크 점수를 주장하는 모델 카드의 발행을 거절하세요.
- 라이선스가 파생 모델을 금지하는 데이터로 파인튜닝하는 것을 거절하세요. MOF는 데이터 라이선싱을 등급 매깁니다.
- 평가 행렬에서 품질 손실을 측정하지 않고 양자화 모델을 출시하는 것을 거절하세요.

출력: 파이프라인 오케스트레이터, Llama 3.3 8B + 대안 베이스 하나의 YAML, SFT와 DPO의 W&B 실행 로그, 양자화 산출물, 서빙 엔드포인트, 세 벤치마크 평가 행렬, 안전 평가, 2026 MOF 모델 카드, 그리고 잡아내서 고친 가장 큰 데이터 위생 문제 세 가지에 대한 보고서가 담긴 저장소.
