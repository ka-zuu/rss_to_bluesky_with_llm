import sqlite3

DB_NAME = "rss_cache.db"

def init_db():
    """データベースを初期化し、テーブルが存在しない場合は作成する"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY
            )
        """)
        conn.commit()

def url_exists(url: str) -> bool:
    """指定されたURLがデータベースに存在するかどうかを確認する"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM articles WHERE url = ?", (url,))
        return cursor.fetchone() is not None

def add_url(url: str):
    """新しい記事のURLをデータベースに追加する"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO articles (url) VALUES (?)", (url,))
        conn.commit()
