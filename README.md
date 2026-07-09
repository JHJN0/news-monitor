# 📰 뉴스 모니터링 (News Monitor)

구글 뉴스 RSS로 키워드 뉴스를 수집해 SQLite에 저장하고, Flask 웹 페이지로 보여주는 도구입니다.

## 구조

| 파일 | 역할 |
|---|---|
| `keywords.json` | 수집할 키워드 목록 (초기값: `["조선대"]`) |
| `collector.py` | 구글 뉴스 RSS 수집 스크립트 (표준 라이브러리만 사용) |
| `app.py` | Flask 웹 서버 (목록 표시, 키워드 필터, "지금 수집" 버튼) |
| `templates/index.html` | 목록 페이지 |

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

## 배포 (Render)

이 저장소에는 `render.yaml`이 포함되어 있어 [Render](https://render.com)에서 바로 배포할 수 있습니다.

1. Render 가입 후 **New → Blueprint** 선택
2. 이 GitHub 저장소 연결 → 자동으로 웹 서비스 생성
3. 배포 후 접속해서 "지금 수집" 버튼으로 데이터 수집

> 참고: 무료 플랜은 디스크가 임시라서 재배포 시 `articles.db`가 초기화됩니다. "지금 수집" 버튼을 누르면 다시 채워집니다.
