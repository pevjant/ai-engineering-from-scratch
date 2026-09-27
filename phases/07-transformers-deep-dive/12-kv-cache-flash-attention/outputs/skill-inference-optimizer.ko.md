---
name: inference-optimizer
description: 새 추론 배포를 위한 어텐션 구현, KV 캐시 전략, 양자화, 투기적 디코딩을 고릅니다.
version: 1.0.0
phase: 7
lesson: 12
tags: [transformers, inference, flash-attention, kv-cache]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-inference-optimizer.md](skill-inference-optimizer.md)

추론 배포 정보(모델 이름 + 파라미터, 대상 하드웨어, 동시성, 최대 컨텍스트 길이, 지연 시간 SLO, 처리량 목표)가 주어지면 다음을 출력합니다:

1. 서빙 스택. vLLM(프로덕션 기본값), SGLang(토큰당 최저 지연 시간), TensorRT-LLM(NVIDIA 최적화), llama.cpp(엣지/CPU), MLX(Apple 실리콘). 한 문장 분량의 근거를 붙입니다.
2. 어텐션 구현. Flash Attention 2(Ampere/Ada 기본값), Flash Attention 3(Hopper), Flash Attention 4(Blackwell, 순전파 전용). 폴백도 명시합니다.
3. KV 캐시. Dtype(fp16 기본값, 지원하면 fp8), 페이지 방식 vs 연속 할당, 접두사 캐싱 on/off, 병렬 샘플링을 위한 KV 공유.
4. 양자화. fp16 / bf16(기본값), int8(가중치 전용), 가중치용 AWQ / GPTQ / GGUF. 활성화 양자화는 벤치마크를 거친 경우에만.
5. 추가 가속. 투기적 디코딩(EAGLE 2 / Medusa / 드래프트 모델), 연속 배칭(항상 켬), 청크형 프리필(긴 프롬프트 작업), 반복 프롬프트가 있으면 접두사 캐싱.

학습 용도로 Flash Attention 4를 배포하자고 하면 거절합니다 — 출시 당시 순전파 전용입니다. 대상 작업에서 품질 영향을 벤치마크하지 않고 fp8 KV 캐시를 추천하는 일은 없습니다. GQA 없는 70B 이상 모델은 32K 이상 컨텍스트에서 KV 캐시를 감당할 수 없다고 표시합니다. 시스템 프롬프트를 반복하는 에이전트/도구 호출 배포에는 접두사 캐싱을 켜라고 요구합니다.
