> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [youtube-source-review.md](youtube-source-review.md)

# YouTube 출처 검토

> 영상은 움직임을 가르쳐 줍니다. 인터페이스를 정의하는 것은 공식 문서입니다.

**검토일:** 2026-08-09

영상은 가르침의 순서, 랩 아이디어, 설명을 위해 사용했습니다. 시험 가중치,
수수료, 정책, 응시 자격, 현재 API 필드의 권위로는 쓰지 않았습니다. 2026년 7월
공개 시험 가이드와 현재 Anthropic 문서가 모든 영상보다 우선합니다.

## 커리큘럼 앵커

| 출처 | 왜 중요한가 | 유용한 구간 |
|--------|----------------|-----------------|
| [Prompting 101](https://www.youtube.com/watch?v=ysPbXH0LpIE), Anthropic | 실패 먼저 보여 주는 프롬프팅과 최소한의 개입 | [10:10의 구분자](https://www.youtube.com/watch?v=ysPbXH0LpIE&t=610s), [13:11의 few-shot](https://www.youtube.com/watch?v=ysPbXH0LpIE&t=791s), [15:47의 프롬프트 위치](https://www.youtube.com/watch?v=ysPbXH0LpIE&t=947s) |
| [Prompting for Agents](https://www.youtube.com/watch?v=XSZP9GhhuAc), Anthropic | 에이전트 경계, 도구 설계, 예산, 최종 상태 평가 | [9:47의 예산](https://www.youtube.com/watch?v=XSZP9GhhuAc&t=587s), [15:42의 맨 베이스라인](https://www.youtube.com/watch?v=XSZP9GhhuAc&t=942s), [21:38의 작은 평가](https://www.youtube.com/watch?v=XSZP9GhhuAc&t=1298s) |
| [The CLAUDE.md file](https://www.youtube.com/watch?v=O0FGCxkHM-U), Claude | 온보딩으로서의 간결한 프로젝트 지시 | [0:40의 온보딩](https://www.youtube.com/watch?v=O0FGCxkHM-U&t=40s), [1:57의 보조 문서](https://www.youtube.com/watch?v=O0FGCxkHM-U&t=117s) |
| [Hooks in Claude Code](https://www.youtube.com/watch?v=IkaPHiMDazM), Claude | 확률적 행동을 감싸는 결정론적 통제 | [0:13의 결정론](https://www.youtube.com/watch?v=IkaPHiMDazM&t=13s), [1:50의 도구 실행 전 차단](https://www.youtube.com/watch?v=IkaPHiMDazM&t=110s) |
| [Tool, skill, or subagent?](https://www.youtube.com/watch?v=mWvtOHlZM-I), Claude | 관심사가 너무 쌓인 프롬프트 분해하기 | [1:18의 프롬프트 비대화](https://www.youtube.com/watch?v=mWvtOHlZM-I&t=78s), [3:54의 컨텍스트 격리](https://www.youtube.com/watch?v=mWvtOHlZM-I&t=234s), [35:19의 서브에이전트](https://www.youtube.com/watch?v=mWvtOHlZM-I&t=2119s) |
| [Claude Agent SDK full workshop](https://www.youtube.com/watch?v=TqC1qOfiVcQ), AI Engineer with Anthropic | 하네스, 도구, 파일, 세션, 훅, 샌드박싱, 서브에이전트 | [4:47의 파일시스템](https://www.youtube.com/watch?v=TqC1qOfiVcQ&t=287s), [5:46의 압축과 훅](https://www.youtube.com/watch?v=TqC1qOfiVcQ&t=346s), [14:17의 샌드박싱](https://www.youtube.com/watch?v=TqC1qOfiVcQ&t=857s) |
| [Building Agents with MCP](https://www.youtube.com/watch?v=kQmXtrmQ5Zg), AI Engineer with Anthropic | 클라이언트, 서버, 도구, 리소스, 프롬프트, 탐색 | [4:24의 클라이언트 역할](https://www.youtube.com/watch?v=kQmXtrmQ5Zg&t=264s), [52:14의 도구 탐색](https://www.youtube.com/watch?v=kQmXtrmQ5Zg&t=3134s) |
| [Building with MCP and the Claude API](https://www.youtube.com/watch?v=aZLr962R6Ag), Anthropic | Claude API 통합의 형태 | 25분짜리 전체 구축, 현재 MCP 문서와 대조해 확인 |
| [Build Agents That Run for Hours](https://www.youtube.com/watch?v=mR-WAvEPRwE), AI Engineer with Anthropic | 체크포인트, 평가자, 작업 계약, 장기 일관성 | [10:14의 체크포인트](https://www.youtube.com/watch?v=mR-WAvEPRwE&t=614s), [19:02의 평가자](https://www.youtube.com/watch?v=mR-WAvEPRwE&t=1142s) |

## 실습 랩 자료

- [Your First Agent on the Raw Messages API](https://www.youtube.com/watch?v=RheXq2HKJmY)
  이 영상은 날것의 상태 기계 랩을 뒷받침합니다: `stop_reason` 검사, 전체 메시지
  히스토리 유지, tool-use 식별자 짝짓기, 도구 결과 반환, 명시적 종료 조건에서
  멈추기.
- [Hooks, Guardrails and Security](https://www.youtube.com/watch?v=GGO4tn4RTvY)
  이 영상은 파괴적 명령 차단, 출력 정규화, 증거 검사, 간접 프롬프트 주입
  fixture를 뒷받침합니다.
- [Complete Beginner's Course on AI Evaluations](https://www.youtube.com/watch?v=TL527yTpxlk)
  이 영상은 쓸모 있는 골든 셋과 사람 라벨링 교육 시퀀스를 제공합니다.
- [How to Systematically Set Up LLM Evals](https://www.youtube.com/watch?v=a3SMraZWNNs)
  이 영상은 단위 검사, 사람 검토, 모델 심판, A/B 비교, 분석-측정-개선 루프를
  강화합니다.

## 자격증 보조 자료

- [Claude Certified Architect Foundations full course](https://www.youtube.com/watch?v=reDRM0tqhNs)
  (freeCodeCamp와 ExamPro)는 폭넓은 주제 목록입니다. 편집 모델이 아니며 시험
  사실을 정의하지 않습니다.
- [Claude Certified Architect Foundations exam review](https://www.youtube.com/watch?v=n-Jse3TE3MI)
  (Tim Warner)는 답을 외우는 대신 공개 시나리오마다 프로젝트를 만들 것을
  강조합니다.
- 독립 Associate 및 Professional 과정들은 시나리오 연속성과 인시던트 먼저
  가르치기가 효과적임을 보여 줬습니다. 이 커리큘럼은 그 패턴을 새로운 시나리오와
  언어로 사용합니다.

## 사용자 제공 감사 대상

이 자료들은 커뮤니티 자료로 검토되고, 현재 공식 시험 가이드, 자격증 FAQ, Academy
과목 목표, 제품 문서와 대조됐습니다.

| 출처 | 취한 신호 | 사실로 취급하지 않은 주장 |
|--------|-------------|---------------------------|
| [freeCodeCamp and ExamPro CCAR-F course](https://www.youtube.com/watch?v=reDRM0tqhNs) | 공개 CCAR-F 시나리오 전반의 구축 우선 시퀀싱 | 시연 동작, 개인 조언, 현재 문서가 없는 제품 세부 사항 |
| [Chance Xie exam experience](https://www.youtube.com/watch?v=kY9z4hiH4nk) | 실전 사용과 시나리오 추론이 용어 암기보다 중요하다는 것 | 점수, 준비 시간, 난이도, 기억에 의존한 문항 패턴 |
| [Preporato study guide](https://www.youtube.com/watch?v=akzKBQVyFEI) | 실용적인 학습 리듬과 오답 분류법 | 원점수-합격 환산, 보장된 일정, 예측된 시험 출제 분포 |
| [Ivan Fediaev exam breakdown](https://www.youtube.com/watch?v=PUnB9b6VIWk) | 정확한 작동 방식과 기각된 대안을 살펴볼 것 | 개인적인 시험 구성, 난이도 순위, 기억에 의존한 문항 |
| [freeCodeCamp Claude Code Essentials](https://www.youtube.com/watch?v=brLhhkUqcn4) | 후보가 될 만한 긴 분량 연습 보조 자료 | 사실 주장은 반입 없음: 이 감사 당시 공개 자막을 이용할 수 없었음 |
| [Peace Of Code 22-video playlist](https://www.youtube.com/playlist?list=PLviC8AFqAj5A9MHkRIn2fU5Ac2lEdJxNf) | 에이전트 루프, 서브에이전트 계약, 도구, 복구, 컨텍스트, 검토 시연 | 구식 MCP 전송 안내, 네이티브 구조화된 출력 대용으로서의 프롬프트 전용 JSON, 시험 물류 정보 |
| [Tech With Deepanshu Academy ranking](https://www.youtube.com/watch?v=OYyYlH6Un0Y) | API 라이프사이클, Claude Code 운영, 스킬, MCP, 서브에이전트, 능력 한계의 우선순위 | 고정된 과목 수, 과목 순위, 공부 시간 추정, 자격증 가치, 고급 주제가 시험에 나왔다는 주장 |

순위 영상은 카탈로그를 18개 과목, 5개 트랙 묶음이라 부르고 전체 훑기를 50~60시간으로
추정합니다. Academy는 그 숫자가 커리큘럼 불변 조건이 될 수 없을 만큼 빨리
바뀝니다. 이 저장소는 공식 과목 목표를 오래 쓸 수 있는 레슨에 대응시키고 대신
검증 날짜를 기록합니다.

가르침에 중요한 한 가지 직접 교정: 그 영상은 네 번째 AI Fluency 역량을
"Dialogue"라고 부릅니다. 공식 프레임워크는 **Delegation, Description,
Discernment, Diligence**입니다. 이 커리큘럼은 공식 용어를 씁니다. 영상의
내레이션은 또한 18개 과목 카탈로그를 설명하면서 발표자가 17개 과목을 완주했다고
말하는데, 이것도 카탈로그 개수를 요구 사항으로 보존하지 말아야 하는 또 하나의
이유입니다.

## 표준 가르침 패턴

1. 그럴듯한 실패를 보여 준다.
2. 측정 가능한 베이스라인을 잡는다.
3. 설계 개입 하나를 더한다.
4. 최종 상태와 궤적을 모두 시험한다.
5. 기각한 대안을 기록한다.
6. 결과를 다른 사람이 검사할 수 있는 산출물로 꾸린다.

보안 랩에는 항상 레드팀 fixture가 들어갑니다. 아키텍처 랩에는 항상 독립
검토자가 들어갑니다. Professional 랩은 항상 이해관계자용 설명과 이름이 명시된
운영 담당자로 끝납니다.

## 표류 경고

- 2025년 3월 MCP 워크숍은 이후의 전송, 인증, 레지스트리, SDK 변경보다 앞선다.
- 오래된 Claude Code 영상은 좋은 워크플로 조언을 지니면서도 낡은 설정 키, 권한
  동작, 기능 이름을 보여 줄 수 있다.
- 독립 자격증 과정은 블루프린트 개정보다 늦을 수 있다.
- 개인 시험 후기는 학습자의 일화이지 사양이 아니다.
- 과목 수, 기간, 순위, 자격증 가치 주장은 카탈로그 스냅샷이나 의견일 뿐, 오래
  쓸 수 있는 자격증 요구 사항이 아니다.
- 어떤 자료도 답 패턴 요령, 재구성한 문항, 덤프, 합격 보장 주장을 정당화하지
  않는다.
