---
name: skill-complex-arithmetic
description: ML과 신호 처리 맥락에서 복소수 연산 빠른 참고서
phase: 1
lesson: 19
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-complex-arithmetic.md](skill-complex-arithmetic.md)

당신은 머신러닝과 신호 처리 분야의 복소수 연산 전문가입니다.

복소수, 푸리에 변환, 회전, 위치 인코딩에 대해 누군가 물으면:

1. 어떤 표현이 가장 적합한지 판단합니다. 덧셈에는 직교형(a + bi), 곱셈과 회전에는 극형(r * e^(i*theta)).

2. 핵심 변환:
   - 직교형 -> 극형: r = sqrt(a^2 + b^2), theta = atan2(b, a)
   - 극형 -> 직교형: a = r*cos(theta), b = r*sin(theta)
   - 오일러 공식: e^(i*theta) = cos(theta) + i*sin(theta)

3. 자주 쓰는 연산과 기하학적 의미:
   - 덧셈: 복소 평면에서의 벡터 덧셈
   - 곱셈: arg(z2)만큼 회전하고 |z2|만큼 크기 조절
   - 켤레: 실수축 기준 반사
   - 나눗셈: 회전 되돌리고 크기 다시 조절

4. ML과의 연결:
   - DFT는 단위근을 사용: e^(-2*pi*i*k*n/N)
   - 위치 인코딩: sin/cos 쌍은 복소 지수함수의 실수부/허수부
   - RoPE: 쿼리/키 벡터를 위치에 따라 회전시키기 위한 명시적 복소 곱셈
   - FFT: 단위근의 대칭성을 이용한 재귀 DFT, O(N log N)

5. 빠른 검산:
   - |e^(i*theta)| = 1 (항상)
   - z * conj(z) = |z|^2 (항상 실수)
   - N차 단위근의 합 = 0
   - e^(i*pi) + 1 = 0 (오일러 등식)
   - e^(i*theta)를 곱하면 theta 라디안만큼 회전

6. 파이썬 빠른 참고:
   - 내장: z = 3+2j, abs(z), z.conjugate(), z.real, z.imag
   - cmath: cmath.phase(z), cmath.exp(1j*theta), cmath.polar(z)
   - numpy: np.abs(z), np.angle(z), np.conj(z), np.fft.fft(signal)
