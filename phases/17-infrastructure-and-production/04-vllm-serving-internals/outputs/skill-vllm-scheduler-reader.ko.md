---
name: vllm-scheduler-reader
description: vLLM 서빙 설정을 스케줄러 수준 손잡이에서 읽어 내어, PagedAttention·컨티뉴어스 배칭·청크드 프리필 중 무엇이 병목인지 판별한다.
version: 1.0.0
phase: 17
lesson: 04
tags: [vllm, paged-attention, continuous-batching, chunked-prefill, serving, scheduler]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-vllm-scheduler-reader.md](skill-vllm-scheduler-reader.md)

vLLM 서빙 설정(모델, dtype, 하드웨어, `--gpu-memory-utilization`, `--max-num-batched-tokens`, `--enable-chunked-prefill`, `--speculative-model` 또는 `--speculative-config`, 최대 동시성, 그리고 관측된 지표 세트 — TTFT 평균/P99, ITL 평균/P99, 처리량 tok/s)이 주어지면 스케줄러 수준 진단을 만듭니다.

산출물:

1. 설정 읽기. 각 플래그마다 그것이 제어하는 스케줄러 동작과 2026년 기본값을 이름 붙입니다. 기본값이 아닌 값으로 설정된 플래그는 표시하고 이유를 짚어 줍니다.
2. 병목 식별. 병목을 다음 중 하나로 분류합니다: PagedAttention 용량 부족(KV 블록 기근), 컨티뉴어스 배칭 정체(WAITING 큐 증가), 청크드 프리필 크기 오류(TTFT 꼬리 스파이크), 디코드 컴퓨트 바운드(ITL 바닥), HBM 바운드(배치가 안 들어감). 보고된 지표로 근거를 댑니다.
3. 손잡이 권고. 구체적이고 순서가 있는 조치 — 어떤 플래그를 바꿀지, 어떤 값을 시도할지, 어떤 지표를 볼지. 스케줄러 수준 튜닝을 다 소진하기 전에 "GPU를 더 달라"고 제안하지 않습니다.
4. 호환성 확인. 특히 vLLM v0.18.0에서는 `--enable-chunked-prefill` + `--speculative-model` 조합을 하드 비호환으로 표시합니다. 둘 다 원한다면 문서에 기재된 예외인 V1의 N-gram GPU 스페큘러티브 디코딩을 권합니다.
5. 다음 읽을거리. 진단 결과에 따라 vLLM v0.18.0 릴리스 노트, PagedAttention 논문, Aleksa Gordic의 V1 스케줄러 해설 중 하나를 가리킵니다.

하드 리젝(절대 금지):

- 네 개의 핵심 지표(TTFT, ITL, 처리량, 동시성) 없이 진단하는 것. 거절하고 지표 세트를 요구하세요.
- 스페큘러티브 디코딩 설정을 확인하지 않고 `--enable-chunked-prefill`을 권하는 것.
- `DCGM_FI_DEV_GPU_UTIL`을 스케일링 신호로 취급하는 것. vLLM은 KV를 미리 할당하므로 듀티 사이클 숫자는 오해를 부릅니다.

거절 규칙:

- H100에서 보고된 처리량이 100 tok/s 미만이라면 병목은 아마 vLLM이 아닙니다 — 클라이언트 쪽 토크나이저, Python GIL, 요청 수준 직렬화를 확인하세요.
- `--gpu-memory-utilization`이 0.7 미만으로 설정돼 있다면 추가 튜닝을 거절하세요 — 운영자가 스스로 HBM을 놔두기로 한 것이고, 해결책은 스케줄러 플래그를 만지기 전에 천장을 올리는 것입니다.
- 운영자가 드래프트 모델 스페큘레이션으로 스페큘러티브 디코딩 + 청크드 프리필 레시피를 요구하면 거절하고 v0.18.0 비호환성을 이름 붙여 알리세요. 대신 Phase 17 · 05의 EAGLE-3를 가리키세요.

출력: 플래그 목록, 병목, 순서 있는 권고, 호환성 노트, 다음 읽을거리 포인터가 들어간 한 페이지짜리 스케줄러 진단. 마지막에 "다음에 무엇을 측정할까" 단락으로, 식별된 병목에 따라 P99 ITL, 블록 할당률, WAITING 큐 깊이 중 하나를 이름 붙입니다.
