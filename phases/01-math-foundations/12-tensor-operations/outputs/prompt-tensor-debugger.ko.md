> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [prompt-tensor-debugger.md](prompt-tensor-debugger.md)

---
name: prompt-tensor-debugger
description: 딥러닝 코드의 텐서 shape 오류를 단계별로 디버깅하는 프롬프트
phase: 1
lesson: 12
---

딥러닝 코드에서 텐서 shape 오류가 발생했습니다. 고칠 수 있도록 도와주세요.

**오류 메시지:** [여기에 오류를 붙여 넣으세요]

**내 텐서 shape:**
- [이름]: [shape]
- [이름]: [shape]

**하려던 연산:** [설명을 적으세요]

---

디버깅할 때는 다음 절차를 그대로 따르세요:

**단계 1: 연산 유형을 파악합니다.**
어떤 연산이 오류를 냈나요? 다음 중 하나로 분류하세요:
- 행렬 곱셈 / Linear 레이어 (안쪽 차원이 일치해야 함)
- 브로드캐스팅 (오른쪽부터 정렬, 각 차원은 같거나 1이어야 함)
- 연결(concatenation) (cat하는 차원을 제외한 모든 차원이 일치해야 함)
- 합성곱(convolution) (특정 랭크와 채널 위치를 기대함)
- reshape (전체 원소 개수가 보존되어야 함)

**단계 2: shape 계약을 적어 봅니다.**
파악한 연산에 대해 기대되는 shape를 명시적으로 적습니다:
```
matmul(A, B): A is (..., m, k), B is (..., k, n) -> (..., m, n)
broadcast(A, B): align right, each pair must be (equal) or (one is 1)
cat([A, B], dim=d): all dims match except dim d
Linear(in_f, out_f): input last dim must equal in_f
Conv2d(in_c, out_c, k): input must be (B, in_c, H, W)
```

**단계 3: 불일치를 찾습니다.**
실제 shape를 계약과 비교합니다. 규칙을 어기는 정확히 그 차원을 찾아내세요.

**단계 4: 최소한의 수정을 고릅니다.**
다음 표에서 고르세요:

| 증상 | 수정 방법 |
|---|---|
| 배치 차원이 없음 | `.unsqueeze(0)` |
| 채널 차원이 없음 | `.unsqueeze(1)` |
| 크기 1인 불필요한 차원이 있음 | `.squeeze(dim)` |
| matmul의 안쪽 차원이 잘못됨 | `.transpose(-1, -2)` 또는 가중치 shape 확인 |
| NHWC를 NCHW로 바꿔야 함 | `.permute(0, 3, 1, 2)` |
| NCHW를 NHWC로 바꿔야 함 | `.permute(0, 2, 3, 1)` |
| Linear에 넣기 위해 공간 차원을 펼쳐야 함 | `.flatten(1)` 또는 `.reshape(B, -1)` |
| 헤드 분리: (B,T,D)에서 (B,H,T,D/H)로 | `.reshape(B, T, H, D//H).transpose(1, 2)` |
| 헤드 병합: (B,H,T,D/H)에서 (B,T,D)로 | `.transpose(1, 2).reshape(B, T, H*(D//H))` |
| non-contiguous 텐서에 .view() 사용 | `.contiguous().view(...)` 또는 `.reshape(...)` 사용 |

**단계 5: 수정을 검증합니다.**
각 단계에서 결과 shape를 보여 주세요. reshape을 거치면서 전체 원소 개수가 보존되는지 확인하고, 이제 연산의 shape 계약이 만족되는지도 확인합니다.

**단계 6: 조용히 발생하는 버그를 점검합니다.**
shape가 맞더라도 다음을 확인하세요:
- 브로드캐스팅이 의도한 축으로 일어나는지 (우연히 맞아떨어진 게 아닌지)
- reduction이 올바른 차원에 대해 합산하는지
- 배치 차원(dim 0)이 포워드 패스 전체에서 유지되는지
- 차원 순서가 중요할 때 transpose + reshape를 썼는지 (reshape만 쓰지 않았는지)

응답은 다음 형식으로 작성하세요:
```
OPERATION: [실패한 연산]
EXPECTED: [shape 계약]
ACTUAL: [제공된 shape]
MISMATCH: [어느 차원이, 왜]
FIX: [정확한 코드]
RESULT: [수정 후 shape]
```
