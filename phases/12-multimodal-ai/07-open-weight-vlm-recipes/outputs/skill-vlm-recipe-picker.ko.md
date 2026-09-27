---
name: vlm-recipe-picker
description: 오픈 웨이트 VLM 레시피(인코더, 커넥터, LLM, 데이터 믹스, 해상도 스케줄)를 모든 선택에 ablation 표 인용을 붙여 고른다.
version: 1.0.0
phase: 12
lesson: 07
tags: [vlm, mm1, idefics2, molmo, cambrian, prismatic, ablation]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-vlm-recipe-picker.md](skill-vlm-recipe-picker.md)

과제 믹스(OCR, 차트, UI 에이전트, 추론, 그라운딩), 컴퓨팅 예산(LLM 파라미터, 학습 GPU 시간, 또는 추론 지연 시간 목표), 배포 제약(엣지, 클라우드, 온디바이스)이 주어지면, 인용이 붙은 완전한 오픈 웨이트 VLM 레시피를 내놓습니다.

산출물:

1. 인코더 선택. 기본은 SigLIP 2 SO400m/14; 과제 믹스에 그라운딩/세그멘테이션이 있으면 DINOv2 ViT-g/14와 연결; MM1 Table 3과 Cambrian-1의 비전 인코더 대결(match-up)을 인용.
2. 커넥터 선택. 기본은 2층 MLP, 토큰 제약이 있을 때만 Q-Former 32 쿼리; 1점 미만 차이를 보여주는 Prismatic VLMs의 커넥터 ablation을 인용.
3. LLM 선택. 예산 기준: 10B 미만은 Qwen2.5-7B, 30B 이상은 Llama-3.1-70B 또는 Qwen2.5-72B. 70B를 넘기면 MMMU가 포화된다는 점을 표시.
4. 데이터 믹스. 기본은 PixMo + ShareGPT4V + Cauldron; Molmo의 상세-인간-캡션 결과(같은 토큰 수에서 증류 대비 MMMU +2-3)를 인용.
5. 해상도 스케줄. 기본은 동적(256-1280) + 스테이지 1 고정-384 정렬 사전학습; Idefics2 해상도 ablation(AnyRes로 DocVQA +3-5)과 Qwen2.5-VL 동적 M-RoPE를 인용.
6. 학습 스테이지. 스테이지 1은 프로젝터만, 스테이지 2는 전체 파인튜닝, 스테이지 3은 과제 특화.

하드 리젝(거절 사항):
- 새 프로젝트의 기본 인코더로 CLIP ViT-L/14를 추천하면서, SigLIP 2가 대체한다는 사실(사용 중단 권고)을 표시하지 않는 것.
- Q-Former를 MLP보다 품질을 올리는 요소로 소개하는 것. Q-Former는 토큰 예산 레버지지 품질 레버지가 아닙니다.
- 사람이 쓴 캡션 대안이 존재하는데도 합성 GPT-4V 캡션을 주 학습 데이터로 제안하는 것. Molmo를 인용할 것.
- 실제로는 토큰 수에서 나오는 편차를 커넥터 아키텍처 탓으로 설명하는 것.

거절 규칙:
- 사용자가 추론 위주 과제에 1-3B VLM을 원하면 거절하고 더 큰 LLM을 권하세요. 추론 천장은 LLM이 정합니다.
- 사용자가 상세-인간-캡션 데이터를 감당할 수 없다면, 예상되는 MMMU 2-3점 천장을 명시적으로 표시하고 최선을 다하는 증류 폴백을 제안하세요.
- 과제 믹스에 4K 이상 문서 이미지가 있는데 고정 인코더 배포라면 AnyRes를 거절하고 Qwen2.5-VL 같은 네이티브 해상도 M-RoPE 인코더를 권하세요.

출력: 축별 선택, ablation 인용(arXiv ID), 학습 스테이지 계획, 예상 벤치마크 범위가 담긴 한 페이지짜리 레시피 카드. 마지막에 다음에 읽을 세 가지 ablation 논문으로 마무리: arXiv 2403.09611 (MM1), 2405.02246 (Idefics2), 2409.17146 (Molmo).
