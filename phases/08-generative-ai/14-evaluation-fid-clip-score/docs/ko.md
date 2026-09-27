> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# 평가 — FID, CLIP score, 인간 선호도

> 생성 모델 리더보드는 전부 FID, CLIP score, 그리고 인간 선호도 아레나에서 나온 승률을 인용합니다. 각 숫자에는 의지 있는 연구자가 조작할 수 있는 실패 모드가 있습니다. 실패 모드를 모르면 진짜 개선과 조작된 수치를 구분할 수 없습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 8 · 01(분류와 역사), 페이즈 2 · 04(평가 지표)
**시간:** 약 45분

## 문제 상황

생성 모델은 *샘플 품질*과 *조건화 순응도*로 판단받습니다. 둘 다 닫힌 형태의 측도가 없습니다. 모델이 이미지 1만 장을 렌더해야 하고, 무언가가 그것들에 숫자를 매겨야 하고, 여러분은 모델 계열을 넘고, 해상도를 넘고, 아키텍처를 넘어 그 숫자를 신뢰해야 합니다. 2014~2026년의 시련을 통과한 지표 세 개:

- **FID (Fréchet Inception Distance).** Inception 네트워크의 특성 공간에서 두 분포 — 실제와 생성 — 사이의 거리. 낮을수록 좋습니다.
- **CLIP score.** 생성 이미지의 CLIP 이미지 임베딩과 프롬프트의 CLIP 텍스트 임베딩 사이의 코사인 유사도. 높을수록 좋습니다. 프롬프트 순응도를 측정합니다.
- **인간 선호도.** 같은 프롬프트로 두 모델을 정면 대결시키고, 사람(또는 GPT-4급 모델)이 더 나은 쪽을 고르게 하여, 승수를 Elo 점수로 집계합니다.

이것도 보게 될 겁니다: IS(inception score, 사실상 은퇴), KID, CMMD, ImageReward, PickScore, HPSv2, MJHQ-30k. 각각이 이전 지표의 실패 하나를 교정합니다.

## 개념

![FID, CLIP, 선호도: 세 축, 저마다 다른 실패 모드](../assets/evaluation.svg)

### FID — 샘플 품질

Heusel 외(2017). 단계:

1. N개 실제 이미지와 N개 생성 이미지에 대해 Inception-v3 특성(2048차원)을 추출합니다.
2. 각 풀에 가우시안을 피팅합니다: 평균 `μ_r, μ_g`와 공분산 `Σ_r, Σ_g`를 계산합니다.
3. FID = `||μ_r - μ_g||² + Tr(Σ_r + Σ_g - 2 · (Σ_r · Σ_g)^0.5)`.

해석: 특성 공간에서 두 다변량 가우시안 사이의 Fréchet 거리. 낮을수록 = 더 비슷한 분포.

실패 모드:
- **작은 N에서 편향됩니다.** FID는 특성 분포에 대한 평균 제곱이므로 작은 N은 공분산을 과소 추정해 거짓으로 낮은 FID를 줍니다. 항상 N ≥ 10,000을 쓰세요.
- **Inception 의존적입니다.** Inception-v3는 ImageNet으로 학습됐습니다. ImageNet에서 먼 도메인(얼굴, 예술, 텍스트 이미지)은 무의미한 FID를 냅니다. 도메인 전용 특성 추출기를 쓰세요.
- **조작 가능합니다.** Inception 사전에 과적합하면 시각 품질 개선 없이 낮은 FID를 얻습니다. CMMD(아래)로 맞서세요.

### CLIP score — 프롬프트 순응도

Radford 외(2021). 생성 이미지 + 프롬프트에 대해:

```
clip_score = cos_sim( CLIP_image(x_gen), CLIP_text(prompt) )
```

3만 장의 생성 이미지에 걸쳐 평균 → 모델 간 비교 가능한 스칼라.

실패 모드:
- **CLIP 자신의 맹점.** CLIP의 조합적 추론은 약합니다("파란 구 위의 빨간 정육면체"가 자주 실패합니다). 모델은 복잡한 프롬프트를 실제로 따르지 않으면서도 CLIP score에서 좋은 순위를 차지할 수 있습니다.
- **짧은 프롬프트 편향.** 짧은 프롬프트는 실세계에서 CLIP 이미지 매칭이 더 많습니다. 긴 프롬프트는 기계적으로 CLIP 점수가 낮습니다.
- **프롬프트 조작.** 프롬프트에 "high quality, 4k, masterpiece"를 넣으면 이미지-텍스트 결합이 개선되지 않고도 CLIP 점수가 부풀어 오릅니다.

CMMD(Jayasumana 외, 2024)는 이 중 일부를 고칩니다: Inception 대신 CLIP 특성을, Fréchet 대신 최대평균차이(MMD)를 씁니다. 미세한 품질 차이 탐지에 더 뛰어납니다.

### 인간 선호도 — 접지 진실

프롬프트 풀을 고릅니다. 모델 A와 모델 B로 생성합니다. 사람(또는 강한 LLM 심판)에게 페어를 보여 줍니다. 승수를 Elo나 Bradley-Terry 점수로 집계합니다. 벤치마크:

- **PartiPrompts (Google)**: 12개 카테고리에 걸친 1,600개 다양한 프롬프트.
- **HPSv2**: 10.7만 건 인간 주석, 자동 프록시로 널리 쓰임.
- **ImageReward**: 13.7만 건 프롬프트-이미지 선호 페어, MIT 라이선스.
- **PickScore**: Pick-a-Pic 260만 건 선호로 학습.
- **챗봇 아레나 스타일 이미지 아레나**: https://imagearena.ai/ 등.

실패 모드:
- **심판 분산.** 비전문가는 전문가와 취향이 다릅니다. 둘 다 쓰세요.
- **프롬프트 분포.** 골라 담은 프롬프트는 특정 계열을 유리하게 만듭니다. 항상 문서화하세요.
- **LLM 심판 보상 해킹.** GPT-4 심판은 예쁘지만 틀린 출력에 속습니다. 인간으로 삼각측정하세요.

## 함께 사용하기

프로덕션 평가 보고서에는 다음이 있어야 합니다:

1. 홀드아웃 실제 분포 대비 1만~3만 샘플의 FID (샘플 품질).
2. 같은 샘플과 각 프롬프트에 대한 CLIP score / CMMD (순응도).
3. 이전 모델 대비 블라인드 아레나 승률 (전반적 선호도).
4. 실패 모드 분석: 무작위로 뽑은 출력 50개를 알려진 문제(손 해부학, 텍스트 렌더링, 물체 개수 일관성) 기준으로 표시.

지표 하나는 거짓말입니다. 세 지표의 상호 확인 + 정성 리뷰가 비로소 주장이 됩니다.

```figure
gx-fid-distributions
```

## 만들어 보기

`code/main.py`는 합성 "특성 벡터"(Inception 특성 대신 쓰는 4차원 벡터)에 대해 FID, CLIP-score 유사 지표, Elo 집계를 구현합니다. 다음을 보게 됩니다:

- 작은 N과 큰 N에서의 FID 계산 — 그 편향.
- 특성 풀 사이의 코사인 유사도로서의 "CLIP score".
- 합성 선호 스트림에서의 Elo 갱신 규칙.

### 단계 1: 네 줄짜리 FID

```python
def fid(real_features, gen_features):
    mu_r, cov_r = mean_and_cov(real_features)
    mu_g, cov_g = mean_and_cov(gen_features)
    mean_diff = sum((a - b) ** 2 for a, b in zip(mu_r, mu_g))
    trace_term = trace(cov_r) + trace(cov_g) - 2 * sqrt_cov_product(cov_r, cov_g)
    return mean_diff + trace_term
```

### 단계 2: CLIP 스타일 코사인 유사도

```python
def clip_like(image_feat, text_feat):
    dot = sum(a * b for a, b in zip(image_feat, text_feat))
    norm = math.sqrt(dot_self(image_feat) * dot_self(text_feat))
    return dot / max(norm, 1e-8)
```

### 단계 3: Elo 집계

```python
def elo_update(r_a, r_b, winner, k=32):
    expected_a = 1 / (1 + 10 ** ((r_b - r_a) / 400))
    actual_a = 1.0 if winner == "a" else 0.0
    r_a_new = r_a + k * (actual_a - expected_a)
    r_b_new = r_b - k * (actual_a - expected_a)
    return r_a_new, r_b_new
```

## 함정들

- **N=1000에서의 FID.** N=10k 미만에서는 휴리스틱이 신뢰할 수 없습니다. 낮은 N의 FID를 보고하는 논문은 조작 중입니다.
- **해상도를 넘나드는 FID 비교.** Inception의 299×299 리사이즈가 특성 분포를 바꿉니다. 해상도를 맞춘 경우에만 비교하세요.
- **시드 하나만 보고.** 최소 3개 시드를 돌리세요. 표준편차를 보고하세요.
- **네거티브 프롬프트로 부풀린 CLIP 점수.** 어떤 파이프라인은 프롬프트에 과적합해 CLIP 점수를 올립니다. 시각적 포화 여부를 확인하세요.
- **프롬프트 겹침에서 오는 Elo 편향.** 두 모델 모두 학습 중 벤치마크 프롬프트를 봤다면 Elo는 무의미합니다. 홀드아웃 프롬프트 세트를 쓰세요.
- **유료 크라우드 인간 평가의 왜곡.** Prolific, MTurk 주석자는 젊고 기술 친화적인 쪽으로 쏠립니다. 섭외한 예술/디자인 전문가와 섞으세요.

## 사용해 보기

2026년 프로덕션 평가 프로토콜:

| 기둥 | 최소 | 권장 |
|--------|---------|-------------|
| 샘플 품질 | 홀드아웃 실제 세트 대비 1만 샘플 FID | + 5천 샘플 CMMD + 카테고리별 부분집합 FID |
| 프롬프트 순응도 | 3만 샘플 CLIP score | + HPSv2 + ImageReward + VQA 스타일 질의응답 |
| 선호도 | 베이스라인 대비 200 블라인드 페어 | + 2,000 페어 인간 + LLM 심판 + Chatbot Arena |
| 실패 분석 | 손으로 표시한 50개 | 손으로 표시한 500개 + 자동 안전 분류기 |

네 기둥이 하나의 보고서에 모이면 주장입니다. 하나만으로는 마케팅입니다.

## 출시하기

`outputs/skill-eval-report.md`로 저장하세요. 이 스킬은 새 모델 체크포인트 + 베이스라인을 받아 전체 평가 계획을 출력합니다: 샘플 크기, 지표, 실패 모드 탐침, 사인오프 기준.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행해 같은 합성 분포에서 N=100과 N=1000의 FID를 비교해 보세요. 편향 크기를 보고합니다.
2. **보통.** 합성 CLIP 스타일 특성으로 CMMD를 구현해 보세요(공식은 Jayasumana 외, 2024 참조). 품질 차이에 대한 민감도를 FID와 비교합니다.
3. **어려움.** HPSv2 세팅을 재현해 보세요: Pick-a-Pic 부분집합에서 이미지-프롬프트 페어 1,000개를 가져와 선호 데이터로 작은 CLIP 기반 스코어러를 파인튜닝하고, 홀드아웃 세트와의 일치도를 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| FID | "프레셰 인셉션 거리" | 실제 vs 생성 Inception 특성에 피팅한 가우시안의 Fréchet 거리. |
| CLIP score | "텍스트-이미지 유사도" | CLIP 이미지 임베딩과 텍스트 임베딩 사이의 코사인 유사도. |
| CMMD | "FID의 후계자" | CLIP 특성 MMD; 편향이 적고 가우시안 가정이 없습니다. |
| IS | "인셉션 점수" | Exp KL(p(y|x) || p(y)); 현대 모델에서 상관이 나빠 은퇴했습니다. |
| HPSv2 / ImageReward / PickScore | "학습된 선호 프록시" | 인간 선호로 학습된 작은 모델; 자동 심판으로 쓰입니다. |
| Elo | "체스 레이팅" | 페어별 승수에 대한 Bradley-Terry 집계. |
| PartiPrompts | "그 벤치마크 프롬프트 세트" | 12개 카테고리에 걸친 Google 엄선 프롬프트 1,600개. |
| FD-DINO | "자기지도 대체재" | DINOv2 특성을 쓰는 FD; ImageNet 밖 도메인에 더 좋습니다. |

## 프로덕션 노트: 평가도 하나의 추론 워크로드입니다

1만 샘플에 FID를 돌린다는 것은 이미지 1만 장을 생성한다는 뜻입니다. L4 한 장에서 1024² 50스텝 SDXL 베이스라면 단일 요청 추론으로 약 11시간입니다. 평가 예산은 실재하고, 그 관점은 정확히 오프라인 추론 시나리오(처리량 최대화, TTFT 무시)입니다:

- **배치를 때려 넣고, 지연 시간은 잊으세요.** 오프라인 평가 = 메모리에 들어가는 최대 크기의 정적 배칭입니다. 80GB H100에서 `num_images_per_prompt=8`인 `pipe(...).images`는 단일 요청보다 벽시계 기준 4-6배 빠르게 돌아갑니다.
- **실제 특성은 캐시하세요.** 실제 레퍼런스 세트에 대한 Inception(FID) 또는 CLIP(CLIP score, CMMD) 특성 추출은 *한 번만* 돌려 `.npz`로 저장합니다. 평가마다 다시 계산하지 마세요.

CI / 회귀 게이트: PR마다 500샘플 부분집합에 FID + CLIP score(약 30분); 밤마다 전체 1만 FID + HPSv2 + Elo.

## 더 읽을거리

- [Heusel 외 (2017). GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium (FID)](https://arxiv.org/abs/1706.08500) — FID 논문.
- [Jayasumana 외 (2024). Rethinking FID: Towards a Better Evaluation Metric for Image Generation (CMMD)](https://arxiv.org/abs/2401.09603) — CMMD.
- [Radford 외 (2021). Learning Transferable Visual Models from Natural Language Supervision (CLIP)](https://arxiv.org/abs/2103.00020) — CLIP.
- [Wu 외 (2023). HPSv2: A Comprehensive Human Preference Score](https://arxiv.org/abs/2306.09341) — HPSv2.
- [Xu 외 (2023). ImageReward: Learning and Evaluating Human Preferences for Text-to-Image Generation](https://arxiv.org/abs/2304.05977) — ImageReward.
- [Yu 외 (2023). Scaling Autoregressive Models for Content-Rich Text-to-Image Generation (Parti + PartiPrompts)](https://arxiv.org/abs/2206.10789) — PartiPrompts.
- [Stein 외 (2023). Exposing flaws of generative model evaluation metrics](https://arxiv.org/abs/2306.04675) — 실패 모드 조사.
