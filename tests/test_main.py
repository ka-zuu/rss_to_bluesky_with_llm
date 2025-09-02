import pytest
import os
from main import main

@pytest.fixture
def mock_modules(mocker):
    """すべての依存モジュールをモック化するフィクスチャ"""
    # 成功系のテストでは、必要な環境変数が設定されていることを前提とする
    mocker.patch.dict(os.environ, {"RSS_URLS": "http://test.com/rss"})

    mock_db = mocker.patch("main.db_manager")
    mock_rss = mocker.patch("main.rss_fetcher")
    mock_gemini = mocker.patch("main.gemini_processor")
    mock_bsky = mocker.patch("main.bluesky_poster")

    # モックの戻り値を設定
    mock_rss.fetch_new_articles.return_value = [
        {"title": "Article 1", "link": "http://a1.com", "summary": "Summary 1"},
        {"title": "Article 2", "link": "http://a2.com", "summary": "Summary 2"},
    ]
    mock_gemini.rank_articles.return_value = [
        {"title": "Article 2", "link": "http://a2.com", "summary": "Summary 2"},
        {"title": "Article 1", "link": "http://a1.com", "summary": "Summary 1"},
    ]
    mock_gemini.summarize_article.return_value = "This is a summary."
    mock_bsky.post_thread.return_value = True

    return mock_db, mock_rss, mock_gemini, mock_bsky

def test_main_success_flow(mock_modules):
    """メインの処理が正常に最後まで実行されるかのテスト"""
    mock_db, mock_rss, mock_gemini, mock_bsky = mock_modules

    main()

    # 各モジュールが期待通りに呼ばれたか検証
    mock_db.init_db.assert_called_once()
    mock_rss.fetch_new_articles.assert_called_once()
    mock_gemini.rank_articles.assert_called_once()
    assert mock_gemini.summarize_article.call_count > 0
    mock_bsky.post_thread.assert_called_once()

    # 投稿成功したのでDBにURLが追加されるはず
    assert mock_db.add_url.call_count == 2
    mock_db.add_url.assert_any_call("http://a2.com")
    mock_db.add_url.assert_any_call("http://a1.com")

def test_main_post_failure(mock_modules):
    """Blueskyへの投稿が失敗した場合のテスト"""
    mock_db, _, _, mock_bsky = mock_modules

    # 投稿が失敗するように設定
    mock_bsky.post_thread.return_value = False

    main()

    # 投稿に失敗したので、DBへの追加は行われない
    mock_db.add_url.assert_not_called()

def test_main_no_new_articles(mock_modules):
    """新しい記事がない場合のテスト"""
    _, mock_rss, mock_gemini, mock_bsky = mock_modules

    # 新しい記事がないように設定
    mock_rss.fetch_new_articles.return_value = []

    main()

    # 記事がないので、ランク付けや投稿は行われない
    mock_gemini.rank_articles.assert_not_called()
    mock_bsky.post_thread.assert_not_called()

def test_main_no_rss_urls_env(mocker):
    """RSS_URLS環境変数が設定されていない場合のテスト"""
    # RSS_URLSのみ未設定の状態を模倣
    mocker.patch.dict(os.environ, {"RSS_URLS": ""})

    # 他のモジュールが呼ばれないようにモック化
    mock_db = mocker.patch("main.db_manager")
    mock_rss = mocker.patch("main.rss_fetcher")

    main()

    # DB初期化は呼ばれるが、RSS_URLSがないため記事取得は呼ばれずに終了する
    mock_db.init_db.assert_called_once()
    mock_rss.fetch_new_articles.assert_not_called()