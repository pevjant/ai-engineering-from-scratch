> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-3dgs-export-router.md](skill-3dgs-export-router.md)

---
name: skill-3dgs-export-router
description: 하위 뷰어나 엔진에 맞는 3DGS 내보내기 포맷(.ply / .splat / glTF KHR_gaussian_splatting / USD)을 고릅니다
version: 1.0.0
phase: 4
lesson: 22
tags: [3d-gaussian-splatting, export, glTF, OpenUSD, pipeline]
---

# 3DGS Export Router

하위 타깃을 알맞은 3DGS 파일 포맷으로 연결합니다. "로드가 안 된다" 디버깅에 몇 시간씩 아껴줍니다.

## 언제 사용하나

- 3DGS 장면을 학습한 뒤, 콘텐츠 파이프라인에 넘기기 전.
- 연구용(.ply)과 프로덕션용(glTF / USD) 포맷 사이에서 고를 때.
- 파이프라인 인계: 촬영팀 -> 3DGS 엔지니어 -> 게임 디자이너 / VFX 아티스트 / 웹 개발자.

## 입력

- `target_engine`: unreal | unity | omniverse | blender | vision_pro | three_js | babylon_js | cesium | playcanvas | supersplat
- `priority`: portability | file_size | quality_preservation
- `include_sh_degree`: 0 | 1 | 2 | 3

## 포맷 결정

| 타깃 | 권장 포맷 | 이유 |
|--------|--------------------|-----|
| Unreal Engine (가상 프로덕션) | Volinga 플러그인 또는 glTF KHR_gaussian_splatting | 네이티브 Unreal SDK 경로 |
| Unity (XR / 게임) | Aras-P Unity-GaussianSplatting 플러그인을 통한 .ply | 커뮤니티 표준 Unity 파이프라인 |
| NVIDIA Omniverse, Pixar 도구 | OpenUSD 26.03 (UsdVolParticleField3DGaussianSplat) | 네이티브 USD 프림 타입 |
| Apple Vision Pro | OpenUSD 26.03 | visionOS 2.x 네이티브 |
| Blender | .ply + KIRI Engine 애드온 | 커뮤니티 애드온이 원시 스플랫을 읽음 |
| Three.js 웹 뷰어 | glTF KHR_gaussian_splatting 또는 .splat | 브라우저 표준, `GaussianSplats3D`와 동작 |
| Babylon.js V9+ | glTF KHR_gaussian_splatting | V9에서 네이티브 지원 추가 |
| Cesium (CesiumJS 1.139+, Cesium for Unreal 2.23+) | glTF KHR_gaussian_splatting | 명시적 지원 제공 |
| PlayCanvas | .splat | PlayCanvas 네이티브 양자화 포맷 |
| SuperSplat (에디터) | .ply 또는 .splat | 임포트 + 익스포트 |

## 양자화 트레이드오프

- `.ply` 전체 정밀도: 가장 큰 파일, 무손실, 모든 뷰어.
- `.splat`: 4-8배 작음, SH3 계수에서 약간의 품질 손실, PlayCanvas 생태계 표준.
- glTF KHR: EXT_meshopt_compression으로 설정 가능; 가장 작고 호환성 최고.
- USD: USDZ 패키징으로 압축; Apple 파이프라인에서 가장 작음.

## 출력 보고서

```
[export plan]
  target:         <엔진>
  format:         <이름>
  sh degree:      <0|1|2|3>
  compression:    <none|meshopt|quantisation|usdz>
  expected size:  <MB>
  compatible with: <호환 뷰어 목록>

[pipeline]
  1. source: <학습에서 나온 .ply>
  2. optional: SuperSplat 정리 패스
  3. convert: <도구 + CLI 또는 API 호출>
  4. package: <.gltf / .glb / .usd / .usdz / .splat / .ply>
  5. validate: <뷰어 정상 동작 확인>
```

## 규칙

- SH3 계수를 조용히 잘라내지 마세요 — 정반사가 눈에 보이게 달라집니다.
- `priority == file_size`라면 `.splat`이나 meshopt를 곁들인 glTF를 권하고, 품질 손실을 경고하세요.
- Apple 플랫폼에서는 2026년 기준 glTF보다 USD / USDZ를 선호하세요. USDZ가 visionOS 1급 지원입니다.
- 타깃 뷰어의 3DGS 지원이 표준 이전(2026년 2월 이전)이라면 `.ply`와 뷰어의 커스텀 로더를 권하세요. Khronos 표준 glTF는 아직 인식되지 않습니다.
- 인계 전에 최소 하나의 뷰어에서 내보낸 파일을 반드시 검증하세요. 양자화 중에 조용히 손상이 일어날 수 있습니다.
