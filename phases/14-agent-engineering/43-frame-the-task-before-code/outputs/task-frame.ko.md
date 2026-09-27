> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [task-frame.md](task-frame.md)

# 태스크 프레임: 회원가입 중 중복 이메일 주소 방지

Status: READY

## 저장소 사실
- 계정 쓰기는 AccountStore를 사용 (`app/accounts.py:18`)
- 중복 에러는 상태 코드 409를 사용 (`tests/test_accounts.py:44`)

## 허용 경로
- `app/accounts.py`
- `tests/test_accounts.py`

## 금지 경로
- `migrations/**`
- `deploy/**`

## 수용 증거
- `python3 -m unittest tests.test_accounts`

## 미지(unknown)
- 이메일 비교가 대소문자를 구분하지 않는지 여부
