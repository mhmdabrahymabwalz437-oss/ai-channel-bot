import sqlite3
from datetime import datetime, timezone

class Storage:
    def __init__(self, path: str):
        self.path = path
        with self.connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, title TEXT, caption TEXT, source_url TEXT, media_path TEXT, status TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path)

    def already_used(self, source_url: str) -> bool:
        with self.connect() as con:
            return con.execute("SELECT 1 FROM posts WHERE source_url=? LIMIT 1", (source_url,)).fetchone() is not None

    def save(self, title: str, caption: str, source_url: str, media_path: str, status: str):
        with self.connect() as con:
            con.execute("INSERT INTO posts(created_at,title,caption,source_url,media_path,status) VALUES(?,?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), title, caption, source_url, media_path, status))
