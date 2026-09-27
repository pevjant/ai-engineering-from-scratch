> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

# ControlNet, LoRA, 그리고 조건화

> 텍스트만으로는 어설픈 제어 신호밖에 안 됩니다. ControlNet은 사전학습된 확산 모델을 복제한 뒤 깊이 맵, 포즈 스켈레톤, 낙서, 에지 이미지로 조종할 수 있게 해 줍니다. LoRA는 20억 파라미터 모델을 1천만 파라미터만 학습해서 파인튜닝하게 해 줍니다. 둘이 합쳐지면서 Stable Diffusion은 장난감에서 모든 에이전시가 출시하는 2026년형 이미지 파이프라인이 되었습니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 8 · 07(잠재 확산), 페이즈 10(LLM 밑바닥부터 — LoRA 기반 지식)
**시간:** 약 75분

## 문제 상황

"번화한 거리에서 빨간 원피스를 입은 여성이 개를 산책시킨다" 같은 프롬프트는 개가 *어디 있는지*, 여성이 *어떤 포즈인지*, 거리의 *시점*이 어떤지에 대한 정보를 모델에게 전혀 주지 못합니다. 텍스트는 이미지를 특정하는 데 필요한 것의 약 10%만 고정시킵니다. 나머지는 시각적인 것이라 말로 효율적으로 묘사할 수 없죠.

모든 신호(포즈, 깊이, canny, 세그멘테이션)마다 새 조건부 모델을 백지부터 학습시키는 것은 감당할 수 없는 일입니다. 여러분이 원하는 것은 2.6B 파라미터 SDXL 백본을 고정한 채, 조건 입력을 읽는 작은 사이드 네트워크를 붙여서 백본의 중간 특성을 살짝 밀어주는 것입니다. 그것이 ControlNet입니다.

또한 전체 모델을 재학습하지 않고 새 개념(얼굴, 제품, 스타일)을 가르치고 싶을 것입니다. 100배 작은 변화량(delta)을 원하는 것이죠. 그것이 LoRA입니다 — 기존 어텐션 가중치에 꽂는 저계수 어댑터입니다.

ControlNet + LoRA + 텍스트 = 2026년 실무자의 도구 상자. 대부분의 프로덕션 이미지 파이프라인은 SDXL / SD3 / Flux 베이스 위에 LoRA 2~5개, ControlNet 1~3개, IP-Adapter 하나를 겹칩니다.

## 개념

![ControlNet은 인코더를 복제하고, LoRA는 저계수 델타를 더한다](../assets/controlnet-lora.svg)

### ControlNet (Zhang 외, 2023)

사전학습된 SD를 가져옵니다. U-Net 인코더 절반을 *복제*합니다. 원본은 고정합니다. 복제본이 추가 조건 입력(에지, 깊이, 포즈)을 받도록 학습시킵니다. 복제본을 *제로 합성곱*(zero-convolution) 스킵 연결 — 0으로 초기화된 1×1 conv(학습 전까지는 no-op이고, 델타만 배웁니다) — 로 원본의 디코더 절반에 다시 연결합니다.

```
SD U-Net decoder:   ... ← orig_enc_features + zero_conv(controlnet_enc(condition))
```

제로 conv 초기화 덕분에 ControlNet은 항등 함수로 시작합니다 — 학습 전이라도 해가 없습니다. 표준 확산 손실로 (프롬프트, 조건, 이미지) 삼중 항목 100만 개를 학습합니다.

모달리티별 ControlNet은 작은 사이드 모델로 출시됩니다(SDXL은 약 360M, SD 1.5는 약 70M). 추론 때 조합할 수 있습니다:

```
features += weight_a * control_a(depth) + weight_b * control_b(pose)
```

### LoRA (Hu 외, 2021)

모델 안의 임의의 선형 층 `W ∈ R^{d×d}`에 대해, `W`를 고정하고 저계수 델타를 더합니다:

```
W' = W + ΔW,  ΔW = B @ A,  A ∈ R^{r×d},  B ∈ R^{d×r}
```

`r << d`입니다. 어텐션에는 계수 4-16이 표준이고, 무거운 파인튜닝에는 64-128입니다. 새 파라미터 수: `d²` 대신 `2 · d · r`. `d=640`, `r=16`인 SDXL 어텐션이면 어댑터당 410k가 아닌 20k 파라미터 — 20배 절감입니다. 모델 전체로 보면 LoRA는 보통 20-200MB로 베이스 5GB와 비교됩니다.

추론 때는 LoRA를 스케일할 수 있습니다: `W' = W + α · B @ A`. `α = 0.5-1.5`가 보통입니다. 여러 LoRA는 덧셈으로 쌓입니다(비선형적으로 상호작용한다는 흔한 주의사항과 함께).

### IP-Adapter (Ye 외, 2023)

*이미지*를 조건으로 받는(텍스트와 함께) 아주 작은 어댑터입니다. CLIP 이미지 인코더로 이미지 토큰을 만들어 텍스트 토큰과 함께 크로스 어텐션에 주입합니다. 베이스 모델당 약 20MB. LoRA 없이도 "이 레퍼런스 스타일의 이미지를 만들어 줘"를 할 수 있게 해 줍니다.

## 조합 가능성 매트릭스

| 도구 | 통제하는 것 | 크기 | 언제 쓰나 |
|------|------------------|------|-------------|
| ControlNet | 공간 구조(포즈, 깊이, 에지) | 70-360MB | 정확한 레이아웃, 구도 |
| LoRA | 스타일, 소재, 개념 | 20-200MB | 개인화, 스타일 |
| IP-Adapter | 레퍼런스 이미지의 스타일 또는 소재 | 20MB | 그 룩을 텍스트로 묘사할 수 없을 때 |
| Textual Inversion | 새 토큰 하나에 담은 단일 개념 | 10KB | 레거시, 대부분 LoRA로 대체됨 |
| DreamBooth | 소재에 대한 전체 파인튜닝 | 2-5GB | 강한 신원, 높은 계산 비용 |
| T2I-Adapter | 더 가벼운 ControlNet 대안 | 70MB | 엣지 디바이스, 추론 예산 |

ControlNet ≈ 공간. LoRA ≈ 의미. 둘 다 쓰세요.

```figure
v4-controlnet-zero
```

## 만들어 보기

`code/main.py`는 두 메커니즘을 1차원에서 시뮬레이션합니다:

1. **LoRA.** 사전학습된 선형 층 `W`. 고정합니다. `W + BA`가 목표 선형 층과 일치하도록 저계수 `B @ A`를 학습시킵니다. `r = 1`만으로 계수-1 보정을 완벽히 배울 수 있음을 보여 줍니다.

2. **ControlNet-lite.** "고정된 베이스" 예측기와 추가 신호를 읽는 "사이드 네트워크". 사이드 네트워크의 출력은 0으로 초기화된 학습 가능한 스칼라 게이트로 조절됩니다(우리 버전의 제로 conv). 학습시키면서 게이트가 올라가는 것을 지켜 보세요.

### 단계 1: LoRA 수학

```python
def lora(W, A, B, x, alpha=1.0):
    # W는 고정; A, B가 학습 대상인 저계수 인자.
    return [W[i][j] * x[j] for i, j in ...] + alpha * (B @ (A @ x))
```

### 단계 2: 제로 초기화 사이드 네트워크

```python
side_out = control_net(x, condition)
gated = gate * side_out  # gate는 0으로 초기화
h = base(x) + gated
```

스텝 0에서 출력은 베이스와 완전히 같습니다. 학습 초기에는 `gate`가 천천히 갱신됩니다 — 치명적인 표류가 없죠.

## 함정들

- **LoRA 과다 스케일링.** `α = 2`나 `α = 3`은 흔한 "더 강하게" 해킹인데 과하게 스타일화되거나 깨진 출력을 냅니다. `α ≤ 1.5`를 지키세요.
- **ControlNet 가중치 충돌.** Pose ControlNet을 가중치 1.0, Depth ControlNet도 가중치 1.0으로 쓰면 보통 과합니다. 가중치 합 ≈ 1.0이 안전한 기본값입니다.
- **잘못된 베이스에 LoRA 얹기.** SDXL LoRA는 어텐션 차원이 맞지 않아 SD 1.5에서 조용히 아무 효과가 없습니다. Diffusers 0.30+는 경고를 줍니다.
- **Textual Inversion 표류.** 한 체크포인트에서 학습한 토큰은 다른 체크포인트에서 심하게 흘러갑니다. LoRA가 더 이동성이 좋습니다.
- **LoRA 가중치 병합과 저장.** 추론을 빠르게 하려고 LoRA를 베이스 가중치에 굽는(bake) 것도 가능하지만(런타임 덧셈 없음), 런타임에 `α`를 스케일하는 능력을 잃습니다. 두 버전 모두 갖고 계세요.

## 사용해 보기

| 목표 | 2026년 파이프라인 |
|------|---------------|
| 브랜드 아트 스타일 재현 | 엄선한 이미지 약 30장으로 계수 32짜리 LoRA 학습 |
| 생성 이미지에 내 얼굴 넣기 | DreamBooth 또는 LoRA + IP-Adapter-FaceID |
| 특정 포즈 + 프롬프트 | ControlNet-Openpose + SDXL + 텍스트 |
| 깊이 인지 구도 | ControlNet-Depth + SD3 |
| 레퍼런스 + 프롬프트 | IP-Adapter + 텍스트 |
| 정확한 레이아웃 | ControlNet-Scribble 또는 ControlNet-Canny |
| 배경 교체 | ControlNet-Seg + 인페인팅 (레슨 09) |
| 빠른 1스텝 스타일 | SDXL-Turbo 위의 LCM-LoRA |

## 출시하기

`outputs/skill-sd-toolkit-composer.md`로 저장하세요. 이 스킬은 과제(입력 자산: 프롬프트, 선택적 레퍼런스 이미지, 선택적 포즈, 선택적 깊이, 선택적 낙서)를 받아 도구 스택, 가중치, 재현 가능한 시드 프로토콜을 출력합니다.

## 연습 문제

1. **쉬움.** `code/main.py`에서 LoRA 계수 `r`을 1부터 4까지 바꿔 보세요. 몇 계수에서 LoRA가 계수-2 목표 델타와 정확히 일치하나요?
2. **보통.** 두 목표 변환에 대해 LoRA 두 개를 따로 학습시키세요. 함께 로드해 덧셈적 상호작용을 보여 줍니다. 상호작용이 선형성을 깨는 순간은 언제인가요?
3. **어려움.** diffusers로 스택을 쌓아 보세요: SDXL-base + Canny-ControlNet(가중치 0.8) + 스타일 LoRA(α 0.8) + IP-Adapter(가중치 0.6). 스택 가중치를 바꿔 가며 FID 대비 프롬프트 충실도 트레이드오프를 측정합니다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| ControlNet | "공간 제어" | 복제된 인코더 + 제로 conv 스킵; 조건 이미지를 읽습니다. |
| 제로 합성곱 | "항등으로 시작" | 0으로 초기화된 1×1 conv; ControlNet이 no-op으로 시작합니다. |
| LoRA | "저계수 어댑터" | `W + B @ A`, `r << d`; 전체 파인튜닝보다 파라미터가 100배 적습니다. |
| rank r | "그 다이얼" | LoRA 압축; 보통 4-16, 무거운 개인화는 64+. |
| α | "LoRA 강도" | 런타임에 LoRA 델타를 스케일합니다. |
| IP-Adapter | "레퍼런스 이미지" | CLIP 이미지 토큰을 쓰는 작은 이미지 조건화 어댑터. |
| DreamBooth | "소재 전체 파인튜닝" | 소재 이미지 약 30장으로 전체 모델을 학습합니다. |
| Textual Inversion | "새 토큰" | 새 단어 임베딩만 학습; 레거시, 대부분 대체됨. |

## 프로덕션 노트: LoRA 교체, ControlNet 레인, 멀티테넌트 서빙

실제 텍스트-이미지 SaaS는 같은 베이스 체크포인트로 수백 개의 LoRA와 십여 개의 ControlNet을 서빙합니다. 이 서빙 문제는 LLM 멀티테넌시와 매우 닮았습니다(프로덕션 문헌은 연속 배칭과 LoRAX / S-LoRA 항목에서 LLM 사례를 다룹니다):

- **LoRA는 핫스왑하고, 병합하지 마세요.** `W' = W + α·B·A`를 베이스에 병합하면 스텝당 추론이 약 3-5% 빨라지지만 `α`와 베이스가 고정됩니다. LoRA는 계수-r 델타로 VRAM에 뜨겁게(hot) 유지하세요; diffusers는 `pipe.load_lora_weights()` + `pipe.set_adapters([...], adapter_weights=[...])`로 요청별 활성화를 지원합니다. 교체 비용은 `2 · d · r · num_layers` 가중치 — MB 규모, 1초 미만입니다.
- **ControlNet은 두 번째 어텐션 레인으로.** 복제된 인코더는 베이스와 병렬로 돌아갑니다. 가중치 1.0짜리 ControlNet 둘 = 스텝당 병합된 패스 하나가 아니라 추가 순전파 두 번. 배치 크기 여유는 이차식으로 줄어듭니다. 활성 ControlNet 하나당 스텝 비용 약 1.5배를 예산에 잡으세요.
- **LoRA도 양자화합니다.** 베이스를 양자화했다면(레슨 07의 8GB Flux 참조) LoRA 델타도 8비트나 4비트로 깔끔하게 양자화됩니다. QLoRA 스타일 로딩으로 4비트 Flux 베이스 위에 메모리를 터뜨리지 않고 LoRA 5~10개를 쌓을 수 있습니다.

Flux 관련: Niels의 8GB용 Flux 노트북은 베이스를 4비트로 양자화하는데, 그 양자화된 베이스 위에 스타일 LoRA를 쌓는(`pipe.load_lora_weights("user/style-lora")`) 것도 `weight_name="pytorch_lora_weights.safetensors"`로 여전히 작동합니다. 2026년 대다수 SaaS 에이전시가 출시하는 레시피가 바로 이것입니다.

## 더 읽을거리

- [Zhang, Rao, Agrawala (2023). Adding Conditional Control to Text-to-Image Diffusion Models](https://arxiv.org/abs/2302.05543) — ControlNet.
- [Hu 외 (2021). LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — LoRA (원래 LLM용; 확산으로 이식).
- [Ye 외 (2023). IP-Adapter: Text Compatible Image Prompt Adapter](https://arxiv.org/abs/2308.06721) — IP-Adapter.
- [Mou 외 (2023). T2I-Adapter: Learning Adapters to Dig Out More Controllable Ability](https://arxiv.org/abs/2302.08453) — ControlNet의 더 가벼운 대안.
- [Ruiz 외 (2023). DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation](https://arxiv.org/abs/2208.12242) — DreamBooth.
- [HuggingFace Diffusers — ControlNet / LoRA / IP-Adapter docs](https://huggingface.co/docs/diffusers/training/controlnet) — 레퍼런스 파이프라인.
