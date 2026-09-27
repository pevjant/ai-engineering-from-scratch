> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 캡스톤 14 — 추측 디코딩(Speculative-Decoding) 추론 서버

> 추측 디코딩 — 값싼 드래프트 모델이 토큰을 제안하면 대상 모델이 한 번의 패스로 검증한다 — 는 이제 연구 트릭이 아니라 프로덕션(운영 환경)에서 쓸 수 있는 최적화입니다. vLLM 0.7의 EAGLE-3는 실제 트래픽에서 2.5~3배 처리량을 냅니다. P-EAGLE(AWS 2026)은 병렬 추측(speculation)을 더 앞으로 밀었습니다. SGLang의 SpecForge는 대규모로 드래프트 헤드를 학습시켰습니다. Red Hat의 Speculators 허브는 흔한 오픈 모델을 위한 정합(aligned) 드래프트를 공개했습니다. TensorRT-LLM은 NVIDIA에서 추측 디코딩을 일급 시민으로 만들었습니다. 2026년 프로덕션 서빙 스택은 EAGLE 계열 드래프트를 얹은 vLLM 또는 SGLang, FP8 또는 INT4 양자화, 큐 대기 기준 HPA입니다. 이 캡스톤은 오픈 모델 두 개를 베이스라인 대비 2.5배 이상 처리량으로 서빙하고 꼬리 지연 보고서를 온전히 제출하는 것입니다.

**유형:** 캡스톤
**언어:** Python (서빙), C++ / CUDA (커널 들여다보기), YAML (설정)
**선수 지식:** 페이즈 3 (딥러닝), 페이즈 7 (트랜스포머), 페이즈 10 (스크래치 LLM), 페이즈 17 (인프라)
**활용 페이즈:** P3 · P7 · P10 · P17
**소요 시간:** 30시간

## 문제

추측 디코딩은 2026년에 상품(commodity)이 됐습니다. EAGLE-3 드래프트 헤드는 대상 모델의 은닉 상태(hidden states)에서 학습하고 N개 토큰 앞을 예측합니다; 대상 모델은 한 번의 패스로 검증합니다. 60~80%의 수용률(acceptance rate)은 끝까지 2~3배 처리량으로 이어집니다. vLLM 0.7은 이를 기본으로 통합합니다. SGLang + SpecForge가 학습 파이프라인을 줍니다. Red Hat의 Speculators는 Llama 3.3 70B, Qwen3-Coder-30B MoE, GPT-OSS-120B용 정합 드래프트를 공개합니다.

기술은 모델이 아니라 서빙 운영에 있습니다. 수용률은 트래픽 분포(ShareGPT vs 코드 vs 도메인 데이터)에 따라 흔들립니다. 거절될 때의 꼬리 지연은 추측을 안 쓸 때보다 나쁩니다 — 안정 상태 토큰/초만이 아니라 여러 배치 크기에서 p99를 보고해야 합니다. Anthropic / OpenAI API 대비 100만 토큰당 비용이 신뢰도의 지렛대입니다.

## 개념

추측 디코딩은 두 레이어로 이루어져 있습니다. **드래프트** 모델(EAGLE-3 헤드, ngram, 또는 더 작은 대상 정합 모델)이 한 단계에 k개 후보 토큰을 제안합니다. **대상** 모델은 k개를 한 번의 패스로 검증합니다; 수용된 접두사가 탐욕(greedy) 경로를 대체합니다. 수용률은 드래프트-대상 정합도와 입력 분포에 달려 있습니다.

EAGLE-3는 대부분의 트래픽에서 ngram 드래프트를 이깁니다. P-EAGLE은 병렬 추측으로 더 깊은 드래프트 트리를 돌립니다. 트레이드오프: 거절 시 P99 지연이 더 높습니다. 검증 패스가 더 크기 때문입니다. 서빙 설정은 배치 크기별 구간화된 지연을 보고해 이를 드러내야 합니다.

배포는 Kubernetes입니다. vLLM 0.7은 GPU당(또는 텐서 병렬 샤드당) 복제본 하나로 돕니다. HPA는 CPU가 아니라 큐 대기 기준으로 오토스케일합니다. FP8(Marlin)과 INT4(AWQ) 양자화가 GPU 메모리를 H100 / H200 봉투 안에 가둡니다. 끝까지의 보고서는 처리량, 수용률, 배치 1/8/32에서의 p50/p99, 그리고 100만 토큰당 달러입니다.

## 아키텍처

```
request ingress
    |
    v
vLLM server (0.7) or SGLang (0.4)
    |
    +-- draft: EAGLE-3 heads | P-EAGLE parallel | ngram fallback
    +-- target: Llama 3.3 70B | Qwen3-Coder-30B | GPT-OSS-120B
    |     quantized FP8-Marlin or INT4-AWQ
    |
    v
verify pass: batch k draft tokens through target
    |
    v (accept prefix; resample for rejected suffix)
    v
token stream back to client
    |
    v
Prometheus metrics: throughput, acceptance rate, queue wait, latency p50/p99
    |
    v
HPA on queue-wait metric
```

## 스택

- 서빙: vLLM 0.7 또는 SGLang 0.4
- 추측 방법: EAGLE-3 드래프트 헤드, P-EAGLE 병렬 추측, ngram 폴백
- 드래프트 학습: SpecForge (SGLang) 또는 Red Hat Speculators
- 대상 모델: Llama 3.3 70B, Qwen3-Coder-30B MoE, GPT-OSS-120B
- 양자화: FP8 (Marlin), INT4 AWQ
- 배포: Kubernetes + NVIDIA device plugin; 큐 대기 지표 기준 HPA
- 평가: 도메인 분포별 수용률 측정을 위한 ShareGPT, MT-Bench-v2, GSM8K, HumanEval
- 참고: 벤더 베이스라인으로서의 TensorRT-LLM 추측 디코딩

```figure
cf-spec-decode
```

## 직접 만들기

1. **대상 모델 준비.** Llama 3.3 70B를 고릅니다. Marlin으로 FP8 양자화합니다. vLLM 0.7 아래 1xH100(또는 2x 텐서 병렬)에 배포합니다.

2. **드래프트 소스.** Red Hat Speculators에서 정합 EAGLE-3 드래프트 헤드를 받아 옵니다(또는 SpecForge로 하나 학습합니다). vLLM의 추측 디코딩 설정에 적재합니다.

3. **베이스라인 수치.** 추측 사용 전: 배치 1/8/32에서의 토큰/초, p50/p99 지연, GPU 사용률. 공개합니다.

4. **EAGLE-3 켜기.** 설정을 뒤집고 같은 벤치마크를 다시 돌립니다. 가속 배수, 수용률, p99 꼬리 지연 변화를 보고합니다.

5. **P-EAGLE.** 병렬 추측을 켜고 더 깊은 드래프트 트리를 직렬 EAGLE-3와 비교해 측정합니다. P-EAGLE이 도움이 되는 지점과 해가 되는 지점의 변곡점을 보고합니다.

6. **도메인 트래픽.** 같은 서버로 ShareGPT vs HumanEval vs 도메인 특화 트래픽을 돌립니다. 분포별 수용률을 측정합니다. 드래프트가 언제 어긋나는지 찾아냅니다.

7. **두 번째 대상 모델.** Qwen3-Coder-30B MoE에서 같은 파이프라인을 돌립니다. 드래프트가 더 까다롭습니다(MoE 라우팅 노이즈). 보고합니다.

8. **K8s HPA.** `queue_wait_ms`를 추적하는 HPA와 함께 K8s에 배포합니다. 부하가 3배가 될 때 확장되는 모습을 시연합니다.

9. **비용 비교.** 같은 평가에서 Anthropic Claude Sonnet 4.7과 OpenAI GPT-5.4 대비 100만 토큰당 달러를 계산합니다. 공개합니다.

## 사용해 보기

```
$ curl https://infer.example.com/v1/chat/completions -d '{"messages":[...]}'
[serve]     vLLM 0.7, Llama 3.3 70B FP8, EAGLE-3 active
[decode]    bs=8, accepted_tokens_per_step=3.2, acceptance_rate=0.76
[latency]   first-token 42ms, full-response 980ms (620 tokens)
[cost]      $0.34 per 1M output tokens at sustained throughput
```

## 출시하기

`outputs/skill-inference-server.md`가 산출물을 설명합니다. 추측 디코딩이 적용되고 온전한 벤치마크 보고서와 K8s 배포를 갖춘, 실측된 서빙 스택입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 베이스라인 대비 실측 가속 | 두 모델에서 품질을 맞춘 상태의 2.5배 이상 처리량 |
| 20 | 현실적 트래픽 수용률 | 분포별 수용률 보고서 |
| 20 | P99 꼬리 지연 규율 | 추측 사용/미사용 배치 1/8/32에서의 p99 |
| 20 | 운영 | K8s 배포, 큐 대기 기준 HPA, 매끄러운 롤아웃 |
| 15 | 보고서와 방법론 | 무엇이 어떻게 바뀌었는지 명확한 설명 |
| **100** | | |

## 연습 문제

1. 드래프트가 대상보다 한 버전 뒤처졌을 때(예: Llama 3.3 → 3.4 드리프트) 수용률 저하를 측정합니다. 모니터링 알림을 만듭니다.

2. ngram 폴백을 구현합니다: EAGLE-3 수용률이 임계값 아래로 떨어지면 ngram 드래프트로 전환합니다. 신뢰성 개선을 보고합니다.

3. 통제된 MoE 실험을 돌립니다: 같은 Qwen3-Coder-30B에 라우팅 노이즈를 주입한 경우와 아닌 경우. 드래프트 수용률의 민감도를 측정합니다.

4. H200(141 GB)으로 확장합니다. 복제본당 모델 크기 여유가 얼마나 생겼는지, 양자화하지 않은 Llama 3.3 70B를 서빙할 수 있는지 보고합니다.

5. 같은 H100 하드웨어에서 TensorRT-LLM 추측 디코딩을 벤치마크합니다. vLLM 대비 어디서 이기는지 보고합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| 드래프트 모델 | "스페큘레이터(speculator)" | 대상이 검증할 N개 토큰을 제안하는 작은 모델 |
| EAGLE-3 | "2026 드래프트 아키텍처" | 대상 은닉 상태에서 학습된 드래프트 헤드; 수용률 약 75% |
| P-EAGLE | "병렬 추측" | 한 번의 대상 패스로 검증되는 드래프트 브랜치 트리 |
| 수용률 | "히트율" | 재샘플링 없이 수용된 드래프트 토큰의 비율 |
| 양자화 | "FP8 / INT4" | 더 많은 모델을 GPU 메모리에 넣기 위한 저정밀 가중치 |
| 큐 대기 | "HPA 지표" | 요청이 추론 시작 전 대기 큐에서 기다린 시간 |
| Speculators 허브 | "정합 드래프트" | 흔한 오픈 모델용 EAGLE 드래프트를 모은 Red Hat Neural Magic 허브 |

## 더 읽을거리

- [vLLM EAGLE 및 P-EAGLE 문서](https://docs.vllm.ai) — 참고 서빙 스택
- [P-EAGLE (AWS 2026)](https://aws.amazon.com/blogs/machine-learning/p-eagle-faster-llm-inference-with-parallel-speculative-decoding-in-vllm/) — 병렬 추측 디코딩 논문 + 통합
- [SGLang SpecForge](https://github.com/sgl-project/SpecForge) — 드래프트 헤드 학습 파이프라인
- [Red Hat Speculators](https://github.com/neuralmagic/speculators) — 정합 드래프트 허브
- [TensorRT-LLM 추측 디코딩](https://nvidia.github.io/TensorRT-LLM/) — 벤더 대안
- [Fireworks.ai 서빙 아키텍처](https://fireworks.ai/blog) — 상용 참고 사례
- [EAGLE-3 논문 (arXiv:2503.01840)](https://arxiv.org/abs/2503.01840) — 방법론 논문
- [vLLM 저장소](https://github.com/vllm-project/vllm) — 코드와 벤치마크
