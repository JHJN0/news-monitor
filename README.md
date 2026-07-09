# 📰 뉴스 모니터링 (News Monitor)

구글 뉴스 RSS로 키워드 뉴스를 수집해 SQLite에 저장하고, Flask 웹 페이지로 보여주는 도구입니다.

## 구조

| 파일 | 역할 |
|---|---|
| `keywords.json` | 수집할 키워드 목록 (초기값: `["조선대"]`) |
| `collector.py` | 구글 뉴스 RSS 수집 스크립트 (표준 라이브러리만 사용) |
| `app.py` | Flask 웹 서버 (목록 표시, 키워드 필터, "지금 수집" 버튼, 공고 업로드) |
| `converter.py` | 공고 파일(PDF/JPG/PNG) → HTML 변환기 (PyMuPDF) |
| `templates/` | 뉴스 목록 · 공고 목록 · 공고 보기 페이지 |

## 동작 원리

1. `keywords.json`의 키워드마다 `https://news.google.com/rss/search?q={키워드}&hl=ko&gl=KR&ceid=KR:ko` 를 요청
2. 각 기사의 제목·링크·언론사·발행일을 파싱
3. SQLite(`articles.db`)에 저장 — `link UNIQUE` + `INSERT OR IGNORE`로 중복 제거
4. `pubDate`를 unix timestamp(`pub_ts`)로 변환해 저장, 목록은 이 값 내림차순 정렬

## 실행 방법

```bash
pip install -r requirements.txt
python collector.py   # 뉴스 수집
python app.py         # 웹 서버 실행 → http://localhost:5000
```

키워드를 추가하려면 `keywords.json` 배열에 항목을 넣고 웹 페이지의 "지금 수집" 버튼을 누르면 됩니다.

## 공고 업로드 (PDF/JPG/PNG → HTML)

상단 "공고" 탭에서 파일을 업로드하면 HTML로 변환되어 웹에서 바로 볼 수 있습니다.

- 텍스트가 있는 PDF → 읽기 좋은 웹 문서로 변환
- 스캔본 PDF(텍스트 없음) → 페이지를 150dpi 이미지로 렌더링해 표시
- JPG/PNG → 이미지를 그대로 페이지에 표시
- 변환 결과는 SQLite에 저장되므로 원본 파일은 보관하지 않습니다 (최대 20MB)

## 배포 (Render)

이 저장소에는 `render.yaml`이 포함되어 있어 [Render](https://render.com)에서 바로 배포할 수 있습니다.

1. Render 가입 후 **New → Blueprint** 선택
2. 이 GitHub 저장소 연결 → 자동으로 웹 서비스 생성
3. 배포 후 접속해서 "지금 수집" 버튼으로 데이터 수집

> 참고: 무료 플랜은 디스크가 임시라서 재배포 시 `articles.db`가 초기화됩니다. "지금 수집" 버튼을 누르면 다시 채워집니다.
