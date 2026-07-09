"""뉴스 모니터링 웹 서버 — articles.db의 기사를 최신순으로 보여준다."""
import sqlite3
import time

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

from collector import DB_FILE, collect_all, init_db
from converter import convert_to_html

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 업로드 20MB 제한
app.secret_key = "news-monitor-flash-key"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
        init_db(g.db)
        g.db.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                orig_name  TEXT NOT NULL,
                html       TEXT NOT NULL,
                created_ts INTEGER NOT NULL
            )
            """
        )
        g.db.commit()
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


@app.route("/notices")
def notices():
    db = get_db()
    rows = db.execute(
        "SELECT id, title, orig_name, created_ts FROM notices"
        " ORDER BY created_ts DESC"
    ).fetchall()
    return render_template("notices.html", notices=rows)


@app.route("/notices", methods=["POST"])
def upload_notice():
    file = request.files.get("file")
    if file is None or not file.filename:
        flash("파일을 선택해주세요.")
        return redirect(url_for("notices"))
    title = request.form.get("title", "").strip() or file.filename
    try:
        html = convert_to_html(file.read(), file.filename)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("notices"))
    except Exception:
        flash("파일 변환에 실패했습니다. 파일이 손상되지 않았는지 확인해주세요.")
        return redirect(url_for("notices"))
    db = get_db()
    cur = db.execute(
        "INSERT INTO notices (title, orig_name, html, created_ts)"
        " VALUES (?, ?, ?, ?)",
        (title, file.filename, html, int(time.time())),
    )
    db.commit()
    return redirect(url_for("view_notice", notice_id=cur.lastrowid))


@app.route("/notices/<int:notice_id>")
def view_notice(notice_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM notices WHERE id = ?", (notice_id,)
    ).fetchone()
    if row is None:
        abort(404)
    return render_template("notice_view.html", notice=row)


@app.route("/notices/<int:notice_id>/delete", methods=["POST"])
def delete_notice(notice_id):
    db = get_db()
    db.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    db.commit()
    return redirect(url_for("notices"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
