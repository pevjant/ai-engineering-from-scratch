---
name: skill-release-gate
description: 릴리스 전에 Agent Skill 번들의 구조적 무결성, 트리거 품질, 산출물 개선, 스크립트 정확성, 안전성, 설치 트리 무결성, 대상 호스트 포터빌리티를 평가합니다.
license: MIT
metadata:
  lesson: "27"
---

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [SKILL.md](SKILL.md)

# 스킬 릴리스 게이트

Agent Skill 디렉터리 번들을 게시하거나 배포하기 전에 이 스킬을 사용하세요.

## 워크플로

1. 이 설치된 `SKILL.md`가 들어 있는 절대 디렉터리를 `SKILL_ROOT`로 찾아냅니다. 프로세스 cwd가 곧 설치된 번들이라고 가정하지 마세요.
2. 원본 작업 공간의 작업 디렉터리에서 `TARGET_ROOT`를 찾아내고, 사용자가 제공한 후보를 절대 `TARGET_BUNDLE`로 해석합니다.
3. `SKILL_ROOT`에서 `references/eval-contract.md`를 읽습니다.
4. `TARGET_BUNDLE` 아래 `evals/cases.json`의 긍정 및 근접 사례 트리거 케이스를 살펴봅니다.
5. `TARGET_BUNDLE` 아래 `evals/artifacts.json`의 공유 베이스라인 및 스킬 적용 어설션을 살펴봅니다.
6. `TARGET_BUNDLE` 아래 `evals/evidence.json`의 명시적 스크립트 및 안전 결과를 살펴봅니다.
7. `TARGET_BUNDLE` 아래 `assets/hosts.json`의 선언된 런타임 기능을 살펴보고, 대상 파일 해시를 `assets/manifest.json`과 대조해 검증합니다.
8. 프로덕션에서는 결정론적 예측, 산출물, 증거, 호스트 기능을 캡처된 결과로 교체하고, 네 가지 캡처 모드를 모두 설정하며, 모든 원시 트리거 관찰, 두 산출물, 완전한 증거 세트, 비어 있지 않은 호스트 매트릭스를 비어 있지 않은 소스와 일치하는 SHA-256 출처(provenance) 다이제스트에 묶습니다. 이 로컬 검사들은 `localEvidenceReady`를 설정할 수 있지만, 로컬에서 재계산 가능한 해시는 캡처를 증명하지 못합니다.
9. `evidenceRoot`가 보고서와 일치하는 외부 JSON 증명(attestation)과, 그 정확한 바이트의 SHA-256을 별도의 신뢰 정책이나 릴리스 채널에서 확보합니다. 증명은 대상 번들 밖의 일반 파일이어야 합니다.
10. 실행 전에 해석된 정확한 argv를 보여줍니다. 설치된 평가자는 `SKILL_ROOT` 아래 `scripts/evaluate_skill.py`입니다. 배포되는 레슨 픽스처의 경우 argv를 `python3`, 그 절대 평가자 경로, `--fixture-demo`, 절대 `TARGET_BUNDLE`로 구성합니다. 프로덕션에서는 `--fixture-demo` 없이 같은 설치 스크립트를 `--attestation`, `--trusted-attestation-sha256`, 절대 `TARGET_BUNDLE`과 함께 사용합니다.
11. `checksPassed`, `fixturePassed`, `localEvidenceReady`, `trustAnchorValid`, `productionReady`, `passed`를 증거 루트, 평가 모드, 실패한 검사, 정밀도, 재현율, 모든 원시 트리거 관찰, 사례별 반복 실행 비율, 산출물 비교, 스크립트·안전 증거, 설치 트리 검증, 포터빌리티 매트릭스와 함께 반환합니다. 해석된 스크립트 경로, 해석된 대상 경로, cwd, 정확한 argv, 종료 코드를 포함합니다. 관찰할 수 없는 항목은 미검증(unverified)으로 표시합니다.

## 출력 계약

완전한 JSON 평가 보고서를 반환하세요. 통과한 집계가 라우팅, 산출물, 스크립트, 안전, 설치 트리, 포터빌리티 실패를 숨기지 못하도록 모든 층별 검사와 그 증거를 보존하세요. `fixturePassed`는 교육용 픽스처의 성공을 보고합니다. `localEvidenceReady`는 로컬 다이제스트 무결성만 보고합니다. `passed`는 `productionReady`에 유효한 번들 외부 신뢰 앵커가 있을 때만 true입니다.

## 실패 동작

구성이 잘못되었거나, 출처(provenance)가 없거나 일치하지 않거나, 신뢰 증명이 없거나 잘못되었거나, 파일 해시가 다르거나, 필수 기능이 없거나, 프로덕션 게이트가 하나라도 실패하면 0이 아닌 결과로 멈추고 실패한 층을 보고합니다. 명시적인 `--fixture-demo` 경로는 `fixturePassed`가 true일 때만 성공적으로 종료할 수 있으며, 절대 릴리스를 주장하지 않습니다. 게시하거나, 다른 곳에 설치하거나, 증거를 수리하거나, 신뢰 결정을 대신 내리거나, 임계값을 자동으로 약화시키지 마세요.

SKILL.md가 파싱되거나 하나의 긍정 프롬프트가 활성화된다는 이유만으로 번들을 게시하지 마세요. 대상이 필수 동반 파일을 버리거나 필수 런타임 확장을 무시할 때 패키지를 이식 가능하다고 표시하지 마세요.
