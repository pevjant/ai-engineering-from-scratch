---
name: 3d-pipeline
description: 입력 유형, 출력 형식, 사용 사례에 맞춰 3D 생성 또는 재구성 파이프라인을 고릅니다.
version: 1.0.0
phase: 8
lesson: 12
tags: [3d, gaussian-splatting, nerf, mesh]
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [skill-3d-pipeline.md](skill-3d-pipeline.md)

입력(텍스트 프롬프트 / 이미지 한 장 / 이미지 몇 장 / 사진 촬영물 / 비디오), 목표 출력(메시 / 가우시안 스플랫 / NeRF / 포인트 클라우드), 사용 사례(실시간 렌더, 게임 엔진, AR / VR, 시네마틱)가 주어지면 다음을 출력합니다:

1. 파이프라인. (a) 멀티뷰 확산 + 3D 피팅(SV3D, CAT3D + 3DGS), (b) 직접 원샷(LRM, TripoSR, InstantMesh), (c) PBR을 갖춘 텍스트-메시(Meshy 4, Rodin Gen-1.5, Hunyuan3D 2.0), (d) 사진 촬영 + 3DGS(Gsplat, Postshot, Scaniverse).
2. 베이스 모델 + 호스팅. 이름이 붙은 모델 + 오픈 / 호스팅. 상업적 사용에 대한 라이선스 관련 사항을 포함합니다.
3. 반복 예산. 첫 출력까지의 예상 시간, 반복 비용, 정교화 전략.
4. 위상 + 소재. 리메시 패스가 필요한가? PBR 채널 요구사항(알베도, 거칠기, 금속성, 노멀)? UV 배치는 자동인가 수동인가?
5. 평가. 홀드아웃 뷰의 SSIM, CLIP score, 메시 물밀도(watertightness), 폴리곤 수, 텍스처 해상도.
6. 플랫폼 타깃. Unity / Unreal / Blender / 웹(three.js / Babylon) / AR(USDZ / glb).

메시 변환 패스 없이 3DGS를 게임 엔진에 바로 출시하지 않습니다(대부분의 엔진은 스플랫을 네이티브로 렌더링하지 못합니다). 복잡한 관절 캐릭터에 텍스트-3D를 쓰지 않습니다 - 대신 리깅을 아는 파이프라인을 쓰세요. 다운스트림 도구가 NeRF를 렌더링하지 못하는데(대부분의 DCC 도구) NeRF 전용 출력을 내놓는 것은 표시합니다.
