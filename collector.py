"""구글 뉴스 RSS 수집기 — keywords.json의 키워드로 검색해 articles.db에 저장한다."""
import json
import sqlite3
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KEYWORDS_FILE = BASE_DIR / "keywords.json"
DB_FILE = BASE_DIR / "articles.db"

RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
HEADERS = {"User-Agent": "Mozilla/5.0 (NewsMonitor/1.0)"}


def load_keywords():
    with open(KEYWORDS_FILE, encoding="utf-8") as f:
        return json.load(f)


def init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword  TEXT NOT NULL,
            title    TEXT NOT NULL,
            link     TEXT NOT NULL UNIQUE,
            source   TEXT,
            pub_date TEXT,
            pub_ts   INTEGER
        )
        """
    )
    conn.commit()


def fetch_rss(keyword):
    url = RSS_URL.format(query=urllib.parse.quote(keyword))
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def parse_items(xml_bytes):
    """RSS XML에서 (title, link, source, pub_date, pub_ts) 튜플을 뽑아낸다."""
    root = ET.fromstring(xml_bytes)
    for item in root.iterfind("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        source = (item.findtext("source") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if not link:
            continue
        try:
            pub_ts = int(parsedate_to_datetime(pub_date).timestamp())
        except (ValueError, TypeError):
            pub_ts = 0
        yield title, link, source, pub_date, pub_ts


def collect_all():
    """모든 키워드를 수집하고 {키워드: 신규 저장 건수}를 반환한다."""
    keywords = load_keywords()
    conn = sqlite3.connect(DB_FILE)
    try:
        init_db(conn)
        result = {}
        for keyword in keywords:
            new_count = 0
            try:
                xml_bytes = fetch_rss(keyword)
            except Exception as e:
                print(f"[오류] '{keyword}' 수집 실패: {e}")
                result[keyword] = 0
                continue
            for title, link, source, pub_date, pub_ts in parse_items(xml_bytes):
                cur = conn.execute(
                    "INSERT OR IGNORE INTO articles"
                    " (keyword, title, link, source, pub_date, pub_ts)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (keyword, title, link, source, pub_date, pub_ts),
                )
                new_count += cur.rowcount
            conn.commit()
            result[keyword] = new_count
        return result
    finally:
        conn.close()


if __name__ == "__main__":
    for kw, count in collect_all().items():
        print(f"'{kw}': 신규 {count}건 저장")
