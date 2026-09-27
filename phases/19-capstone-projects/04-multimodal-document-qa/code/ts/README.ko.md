> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 캡스톤 04 - 멀티모달 문서 QA (TypeScript)

문서에 대해 페이지 이미지 URL과 인용된 바운딩 박스의 JSON 목록을 돌려주는
뷰어 뼈대입니다. HTML 응답은 페이지 이미지 위에 인용된 영역을 그리는 작은
캔버스 오버레이 스크립트를 인라인으로 담고 있습니다. `../main.py`의 Python
파이프라인과 짝을 이룹니다.

## 구성

```text
ts/
  package.json
  tsconfig.json
  src/
    index.ts        # 진입점, 데모 + HTTP 서버
    server.ts       # hono 앱, /health, /, /document/:id
    fixtures.ts     # 10-K 표 + Nature 그림 픽스처
    render.ts       # HTML 인덱스 + 문서별 오버레이 렌더러
    types.ts        # DocumentFixture, EvidenceRegion, BoundingBox
  tests/
    fixtures.test.ts
    render.test.ts
    server.test.ts
```

## 실행

```bash
npm install
npm run typecheck
npm test
npm start          # 자기 점검 한 패스를 돌리고 0으로 종료
npm run serve      # 127.0.0.1:<port>에서 대화형 HTTP 서버
```

대화형 서버는 `PORT`가 정해져 있지 않으면 빈 포트를 골라 선택된 URL을
stdout에 출력합니다. `/`는 인덱스, `/document/10k-acme-2025`는 데모 오버레이이며,
`accept: application/json`을 지정하면 구조화된 응답을 받을 수 있습니다.

## 테스트

tsx를 통한 `node --test` 러너. 테스트는 픽스처 조회(성공 + 실패),
다섯 위험 문자에 대한 HTML 이스케이프, 문서 HTML 페이로드 구조,
hono 라우트(200, 404, 콘텐츠 협상)를 다룹니다.
