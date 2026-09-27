---
name: cross-policy-diff
description: OpenAI Preparedness Framework v2, Anthropic RSP v3.0, DeepMind FSF v3를 참조로 특정 능력에 대한 정책 간 비교를 작성합니다.
version: 1.0.0
phase: 15
lesson: 20
tags: [preparedness-framework, fsf, rsp, cross-policy, scaling-policy]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-cross-policy-diff.md](skill-cross-policy-diff.md)

특정 프론티어 능력(예: "장기 자율성", "자율 복제 및 적응", "R&D 자동화")이 주어지면, 세 프레임워크가 각각 그 능력을 어떻게 분류하고 어떤 완화책이 촉발되는지 보여주는 정책 간 비교(cross-policy diff)를 작성합니다.

산출물:

1. **OpenAI PF v2 분류.** Tracked 또는 Research. Tracked라면 Capabilities + Safeguards Report 촉발 조건을 밝힙니다. Research라면 정책 문구가 "잠재적" 완화책임을 기록합니다.
2. **Anthropic RSP v3.0 분류.** 어느 임계값인가(ASL-3, AI R&D-4, 하드코딩 금지)? 어느 완화책인가(소명 자료, 보안 + 배포)? 그 약속이 Anthropic 단독 실행 단계에 속하는지 업계 권고 단계에 속하는지 확인합니다.
3. **DeepMind FSF v3 분류.** 어느 도메인인가(사이버, 바이오, ML R&D, CBRN)? 어느 CCL 또는 Tracked Capability Level인가? 기만적 정렬 모니터링이 개입하는가?
4. **수렴 요약.** 세 정책이 그 능력의 심각도에 대해 동의하는가, 아니면 실질적 불일치가 있는가? 어느 분류가 가장 엄밀하고 어느 것이 가장 덜 엄밀한가?
5. **측정 의존성.** 모든 분류는 능력 측정에 의존합니다. 그 능력이 어떻게 측정되는지, 그 측정을 누가 소유하는지(METR, Apollo, 내부, 제3자) 평가 공급자를 밝힙니다.

하드 리젝(무조건 거부):

- 문서 수준의 증거 없이 발표문 문구의 유사성만으로 정책 간 정합성을 주장하는 것.
- 원문 문서의 구체적 조항을 가리킬 수 없는 분류.
- "Research Category"(OpenAI)를 "Tracked Category"와 동등하게 취급하는 것 — 둘은 운영상 결과가 다릅니다.

거부 규칙:

- 사용자가 각 분류에 대한 원문 문서 구절을 제시하지 못하면 거부하고 먼저 인용을 요구합니다.
- 사용자가 정책의 존재를 실제 완화 조치의 증거로 취급하면 거부하고 구체적 완화책이 작동했다는 증거를 요구합니다.
- 어떤 능력이 프레임워크에 "커버된다"고 주장되었는데 그 단어가 문서에 등장하지 않으면 거부하고 구체적 조항 참조를 요구합니다.

출력 형식:

다음을 포함한 비교 문서를 반환합니다:
- **능력 정의** (한 문장)
- **OpenAI PF v2 행** (분류, 촉발 조건, 원문 조항)
- **Anthropic RSP v3.0 행** (분류, 촉발 조건, 단독 실행 vs 권고)
- **DeepMind FSF v3 행** (도메인, CCL / TCL, 기만적 정렬 개입 여부)
- **수렴 요약** (동의 + 실질적 불일치)
- **측정 소유** (평가 공급자, 평가 주기)
- **독자 권고** (가장 엄밀, 가장 덜 엄밀, 근거)
