"""뉴스 모니터링 웹 서버 — articles.db의 기사를 최신순으로 보여준다."""
import sqlite3

from flask import Flask, g, redirect, render_template, request, url_for

from collector import DB_FILE, collect_all, init_db

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
        init_db(g.db)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    db = get_db()
    keyword = request.args.get("keyword", "")
    keywords = [
        row["keyword"]
        for row in db.execute(
            "SELECT DISTINCT keyword FROM articles ORDER BY keyword"
        )
    ]
    if keyword:
        rows = db.execute(
            "SELECT * FROM articles WHERE keyword = ? ORDER BY pub_ts DESC",
            (keyword,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM articles ORDER BY pub_ts DESC"
        ).fetchall()
    return render_template(
        "index.html", articles=rows, keywords=keywords, selected=keyword
    )


@app.route("/collect", methods=["POST"])
def collect():
    collect_all()
    return redirect(url_for("index", keyword=request.form.get("keyword", "")))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
