---
name: workbench-benchmark
description: 프로젝트 자체의 샘플 앱에서 같은 태스크를 프롬프트만 파이프라인과 워크벤치 안내 파이프라인으로 돌리고, 다섯 결과의 전/후 리포트를 내놓습니다.
version: 1.0.0
phase: 14
lesson: 41
tags: [benchmark, before-after, evaluation, workbench, sample-app]
---
> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-workbench-benchmark.md](skill-workbench-benchmark.md)


저장소, 에이전트 제품, 작은 샘플 앱이 주어지면, 프롬프트만 파이프라인과 워크벤치 안내 파이프라인을 비교하는 이동 가능한 평가 하네스를 만들어 냅니다.

만들 것:

1. `eval/sample_app/` — 프로젝트 도메인에서 뽑은 최소한으로 쓸만한 샘플 앱.
2. `eval/run_prompt_only.py`와 `eval/run_workbench.py` — 각각 태스크 설명을 받아 `TaskOutcome`을 반환합니다.
3. `eval/report.py` — 두 파이프라인을 돌리고 `before-after-report.md`와 `comparison.json`을 씁니다.
4. 고정된 태스크 모음에서 워크벤치 결과가 퇴보하면 실패하는 CI 워크플로.
5. `docs/benchmark.md` — 다섯 결과와 무엇이 퇴보(regression)에 해당하는지 설명합니다.

하드 거부(hard reject) 항목:

- 파이프라인이 하나뿐인 벤치마크. 비교가 곧 요점입니다.
- 분모 없이 백분율로 표현된 결과. 항상 `n / m`으로 보고합니다.
- 에이전트 제품이 학습 데이터로 봤을 법한 샘플 앱. 도메인에 맞춘 픽스처를 쓰세요.
- 거짓 음성을 숨기는 리포트. 프롬프트만이 더 빨랐던 태스크는 반드시 열거해야 합니다.

거부 규칙:

- 프로젝트에 수용 명령이 없다면, 벤치마크 출시를 거부합니다. 측정할 것이 없습니다.
- 워크벤치 파이프라인이 중간값 태스크에서 프롬프트만 파이프라인의 3배보다 오래 걸린다면, 그 발견을 드러내세요. 단순화가 필요한 것은 워크벤치지 모델이 아닙니다.
- 하네스가 오프라인으로 돌 수 없다면, CI에 연결하는 것을 거부합니다. 네트워크 불안정성이 비교를 오염시킵니다.

출력 구조:

```
<repo>/
├── eval/
│   ├── sample_app/
│   ├── run_prompt_only.py
│   ├── run_workbench.py
│   └── report.py
├── outputs/eval/
│   ├── before-after-report.md
│   └── comparison.json
├── docs/benchmark.md
└── .github/workflows/benchmark.yml
```

마지막에는 다음을 가리키는 "what to read next"(다음 읽을거리)로 끝냅니다:

- 워크벤치 파이프라인이 쓰는 모든 표면을 묶는 캡스톤 팩은 레슨 42.
- 이것을 보완하는 거시 벤치마크는 레슨 19 (SWE-bench, GAIA, AgentBench).
- 벤치마크가 연결된 뒤의 지속 평가 루프는 레슨 30 (평가 주도 에이전트 개발).
