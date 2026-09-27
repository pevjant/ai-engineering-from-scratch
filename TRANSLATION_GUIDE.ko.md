# 한국어 번역 가이드 (TRANSLATION GUIDE — KO)

이 저장소의 모든 문서를 한국어로 번역할 때 지켜야 할 규칙입니다. **번역 작업 전 반드시 읽을 것.**

## 1. 기본 원칙

- **ELI5 스타일**: 원문을 충실하게 옮기되, 어려운 문장은 일상 비유를 들어 쉽게 풀어 쓴다. 원문의 뉘앙스(유머, 경고, 강조)를 유지한다.
- **내용 추가/삭제 금지**: 모든 섹션과 문단이 번역본에 그대로 있어야 한다(맥락 유지). 쉽게 풀어 쓰는 것은 OK, 생략은 금지. 괄호 안 짧은 보충 설명은 허용.
- **문체**: '~입니다/~합니다' 문어체. 청자는 초보 학습자. 번역투 어색한 문장 금지 — 우리말로 자연스럽게 재배열한다.
- **전문 용어**: 아래 대조표에 없는 용어는 "한국어 표기(English)" 형태로 첫 등장 시 병기, 이후에는 한국어 표기만 사용.

## 2. 용어 대조표 (반드시 이 표를 따를 것)

| English | 한국어 | 비고 |
|---|---|---|
| phase | 페이즈 | 커리큘럼 구조 단위 (00~19) |
| step | 단계 | 레슨 내 진행 단계 |
| lesson | 레슨 | |
| learning objective | 학습 목표 | |
| prerequisite | 선수 지식 | |
| embedding | 임베딩 | |
| token / tokenizer | 토큰 / 토크나이저 | |
| transformer | 트랜스포머 | |
| attention | 어텐션 | |
| fine-tuning | 파인튜닝 | |
| prompt | 프롬프트 | |
| agent | 에이전트 | |
| tool use / function calling | 도구 사용 / 함수 호출 | |
| RAG (Retrieval-Augmented Generation) | RAG(검색 증강 생성) | |
| fine-grained | 세밀한 | 문맥에 따라 |
| supervised learning | 지도 학습 | |
| unsupervised learning | 비지도 학습 | |
| reinforcement learning | 강화 학습 | |
| gradient descent | 경사 하강법 | |
| backpropagation | 역전파 | |
| neural network | 신경망 | |
| convolution | 합성곱 | |
| overfitting / underfitting | 과적합 / 과소적합 | |
| dataset | 데이터셋 | |
| feature | 특성(feature) | 첫 등장 시 병기 |
| label | 레이블 | |
| inference | 추론 | |
| training | 학습(훈련) | 문맥상 자연스러운 쪽 |
| loss function | 손실 함수 | |
| regularization | 정규화 | |
| normalization | 정규화 | 문맥 구분 필요 시 "정규화(Normalization)" 병기 |
| batch | 배치 | |
| epoch | 에포크 | |
| hyperparameter | 하이퍼파라미터 | |
| checkpoint | 체크포인트 | |
| quantization | 양자화 | |
| distillation | 증류 | |
| context window | 컨텍스트 윈도우 | |
| hallucination | 환각 | |
| guardrail | 가드레일 | |
| MCP (Model Context Protocol) | MCP(Model Context Protocol) | 약어 그대로 |
| skill | 스킬 | |
| output / artifact | 산출물 | 레슨 결과물 의미 |
| workflow | 워크플로 | |
| pipeline | 파이프라인 | |
| throughput | 처리량 | |
| latency | 지연 시간 | |
| benchmark | 벤치마크 | |
| evaluation (eval) | 평가(eval) | |
| baseline | 베이스라인 | |
| fine-tune dataset | 파인튜닝 데이터셋 | |
| ship / deploy | 출시 / 배포 | |
| production | 프로덕션(운영 환경) | 첫 등장 시 병기 |
| scalability | 확장성 | |
| observability | 관측 가능성(옵저버빌리티) | 첫 등장 시 병기 |

## 3. 형식 규칙 (중요)

1. **대상 파일은 절대 수정 금지.** 번역본은 항상 새 파일로 저장한다:
   - `docs/en.md` → 같은 폴더에 `docs/ko.md`
   - `README.md` → `README.ko.md`, `SKILL.md` → `SKILL.ko.md`, 그 외 `X.md` → `X.ko.md`
2. **첫 줄 배너** (원문 파일명에 맞춰 상대 링크 수정):
   ```
   > 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)
   ```
3. **코드 블록·명령어·파일 경로·식별자(변수명, 함수명)·URL**: 그대로 유지. 코드 안 **주석**은 한국어로 번역한다.
4. **마크다운 구조**(제목 레벨, 목록, 표, 인용) 유지. 링크의 URL은 유지, 링크 텍스트는 번역. 내부 앵커 링크(#...)는 영문 제목 기준 그대로 둔다.
5. **mermaid 다이어그램**: 문법 구조는 그대로, 따옴표 안 라벨 텍스트만 번역.
6. **```figure 블록**(```figure / s0-env-stack 등): 식별자 그대로 유지.
7. **frontmatter(YAML)**: 키는 유지, 사람이 읽는 값(title, description 등)만 번역.
8. **숫자·단위·고유명사**(PyTorch, CUDA, OpenAI, Claude 등): 그대로.
9. **영어 그대로 두는 것**: 약어(LLM, GPU, API, LoRA, RLHF …)는 약어 그대로, 첫 등장 시 짧은 한국어 설명을 붙여도 좋음.
10. **이모지·강조**(굵게, 기울임): 원문 위치 그대로 유지.

## 4. 금지

- 기계 번역투("것입니다", "~에 대한", 주어 생략으로 모호해지는 문장) 금지
- 섹션 통합/삭제/순서 변경 금지
- 코드 블록 안 실행 코드 수정 금지 (주석 제외)
- 원문에 없는 장황한 부연 설명 금지 (짧은 괄호 보충만 허용)
