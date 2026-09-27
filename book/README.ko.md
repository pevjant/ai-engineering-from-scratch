> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [README.md](README.md)

# 북(Book) 파이프라인

이 커리큘럼은 여섯 권짜리 책 시리즈로 컴파일됩니다. 책은 대체재가 아니라 함께 보는 보조 자료입니다: 인터랙티브 그림, 채점되는 퀴즈, 실행 가능한 코드는 웹사이트와 이 저장소에 그대로 남아 있고, 모든 챕터 끝에는 독자를 그곳으로 안내하는 링크가 붙습니다.

## 권(Volumes)

`volumes.json`에 정의되어 있습니다. 각 권은 페이즈 묶음에 대응합니다:

| 권 | 제목 | 페이즈 |
|-----|-------|--------|
| 1 | 기초(Foundations) | 00-02 |
| 2 | 딥러닝 | 03, 04, 06 |
| 3 | 언어 | 05, 07 |
| 4 | 대규모 언어 모델 | 08-11 |
| 5 | 에이전트 | 12-16 |
| 6 | 프로덕션(운영 환경) | 17-19 |

## 빌드

```bash
python3 scripts/build_book.py                  # 전체 권, EPUB
python3 scripts/build_book.py --volume language
python3 scripts/build_book.py --pdf            # PDF 추가 (xelatex + DejaVu 폰트 필요)
```

pandoc이 필요합니다. 선택 사항: mermaid 다이어그램을 이미지로 렌더링하려면 `@mermaid-js/mermaid-cli`(mmdc)를 쓰면 됩니다. 이것이 없으면 다이어그램은 웹판으로 안내하는 포인터가 됩니다. 결과물은 `dist/book/`에 저장됩니다.

CI(`.github/workflows/build-book.yml`)는 `phases/`가 변경되는 푸시가 있을 때마다 EPUB을 빌드하고, 릴리스에서는 EPUB + PDF를 빌드해 둘 다 릴리스에 첨부합니다.

## 어셈블러가 레슨마다 하는 일

- 레슨의 `# title`은 챕터가 되고, 페이즈는 번호 없는 파트 페이지가 됩니다.
- `figure` 블록(인터랙티브 JS 위젯)은 레슨의 웹판을 가리키는 박스형 안내가 됩니다.
- Mermaid 블록은 mmdc가 있으면 SVG로 렌더링되고, 없으면 웹판 안내 포인터가 됩니다.
- `## Ship It` 섹션은 저장소 산출물을 가리키는 안내로 대체됩니다.
- `## Exercises` 섹션에는 레슨의 `code/` 디렉터리로 가는 시작 코드 링크가 추가됩니다.
- 모든 챕터는 Continue Online 박스로 끝맺습니다: 웹판, 코드, 퀴즈.
- pandoc이 레슨 SVG를 삽입할 수 있도록 에셋 이미지 경로가 다시 쓰입니다.

에이전트가 커리큘럼을 탐색할 때 쓰는 기계 판독용 인덱스(`site/llms.txt`, 배포 시 `site/build.js`가 생성)는 각 레슨의 원본 마크다운으로 연결되고, 책의 "Learning with an AI" 표지 페이지는 독자에게 자기 어시스턴트를 그 인덱스로 향하게 하는 방법을 알려 줍니다.
