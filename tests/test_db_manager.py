import pytest
import sqlite3
from db_manager import init_db, add_url, url_exists

@pytest.fixture
def db_connection(monkeypatch):
    """
    テスト用のインメモリSQLiteデータベース接続を作成し、
    sqlite3.connectが常にこの接続を返すようにモンキーパッチする。
    """
    # インメモリデータベースへの単一の接続を作成
    conn = sqlite3.connect(":memory:")

    # db_manager内のsqlite3.connectをモック化し、常に同じ接続を返すようにする
    def mock_connect(db_name):
        return conn

    monkeypatch.setattr("db_manager.sqlite3.connect", mock_connect)

    # データベースとテーブルを初期化
    init_db()

    yield conn  # テストに接続オブジェクトを渡す

    # テスト終了後に接続を閉じる
    conn.close()

def test_init_db(db_connection):
    """
    init_dbを呼び出した後に'articles'テーブルが存在することを確認するテスト。
    """
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
    assert cursor.fetchone() is not None, "articlesテーブルが作成されていません"

def test_add_and_check_url_exists(db_connection):
    """
    URLを追加した後に、そのURLが存在することを確認するテスト。
    """
    test_url = "https://example.com/new-article"

    # 最初は存在しないはず
    assert not url_exists(test_url), "追加前のURLが既に存在しています"

    # URLを追加
    add_url(test_url)

    # 追加後に存在することを確認
    assert url_exists(test_url), "追加したURLが見つかりません"

def test_check_url_not_exists(db_connection):
    """
    データベースに存在しないURLを確認するテスト。
    """
    test_url = "https://example.com/non-existent-article"
    assert not url_exists(test_url), "存在しないはずのURLが見つかりました"

def test_add_multiple_urls(db_connection):
    """
    複数のURLを正しく追加・確認できるかのテスト。
    """
    urls_to_add = [
        "https://example.com/article1",
        "https://example.com/article2",
        "https://example.com/article3"
    ]

    for url in urls_to_add:
        add_url(url)

    for url in urls_to_add:
        assert url_exists(url), f"追加したはずのURL {url} が見つかりません"

    assert not url_exists("https://example.com/not-added"), "追加していないURLが存在しています"
