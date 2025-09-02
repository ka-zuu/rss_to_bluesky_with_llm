import pytest
import time
from rss_fetcher import fetch_new_articles

# feedparser.parseの結果を模倣するためのヘルパー
class MockFeed:
    def __init__(self, entries):
        self.entries = entries

class MockEntry:
    def __init__(self, title, link, summary, published_parsed=None):
        self._data = {
            'title': title,
            'link': link,
            'summary': summary,
            'published_parsed': published_parsed or time.gmtime()
        }

    def __getattr__(self, name):
        # .title, .link, .summary へのアクセスを維持
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'MockEntry' object has no attribute '{name}'")

    def get(self, key, default=None):
        return self._data.get(key, default)

def test_fetch_new_articles_and_sort(mocker):
    """新しい記事を取得し、日付でソートされることをテストする"""
    # モックするデータを準備（日付がバラバラ）
    mock_entries = [
        MockEntry("Newest Article", "http://example.com/new3", "S3", time.gmtime(1704240000)), # 2024-01-03
        MockEntry("Oldest Article", "http://example.com/new1", "S1", time.gmtime(1704067200)), # 2024-01-01
        MockEntry("Middle Article", "http://example.com/new2", "S2", time.gmtime(1704153600)), # 2024-01-02
    ]

    mocker.patch("rss_fetcher.feedparser.parse", return_value=MockFeed(mock_entries))
    mocker.patch("rss_fetcher.db_manager.url_exists", return_value=False)

    rss_urls = ["http://example.com/feed.xml"]
    new_articles = fetch_new_articles(rss_urls)

    # 結果を検証（古い順にソートされているか）
    assert len(new_articles) == 3
    assert new_articles[0]["title"] == "Oldest Article"
    assert new_articles[1]["title"] == "Middle Article"
    assert new_articles[2]["title"] == "Newest Article"

def test_fetch_new_articles_with_new_and_old_entries(mocker):
    """新しい記事と既存の記事が混在している場合のテスト"""
    # モックするデータを準備
    mock_entries = [
        MockEntry("New Article 1", "http://example.com/new1", "Summary 1"),
        MockEntry("Old Article 1", "http://example.com/old1", "Summary 2"),
        MockEntry("New Article 2", "http://example.com/new2", "Summary 3"),
    ]

    # feedparser.parseとdb_manager.url_existsをモック化
    mocker.patch("rss_fetcher.feedparser.parse", return_value=MockFeed(mock_entries))

    def mock_url_exists(url):
        return "old" in url  # URLに"old"が含まれていればTrueを返す
    mocker.patch("rss_fetcher.db_manager.url_exists", side_effect=mock_url_exists)

    # テスト対象の関数を実行
    rss_urls = ["http://example.com/feed.xml"]
    new_articles = fetch_new_articles(rss_urls)

    # 結果を検証
    assert len(new_articles) == 2
    # ソートされるため、順序は元のエントリ順とは限らない
    links = {a['link'] for a in new_articles}
    assert "http://example.com/new1" in links
    assert "http://example.com/new2" in links


def test_fetch_new_articles_with_only_old_entries(mocker):
    """すべての記事が既存の場合のテスト"""
    mock_entries = [
        MockEntry("Old Article 1", "http://example.com/old1", "Summary 1"),
        MockEntry("Old Article 2", "http://example.com/old2", "Summary 2"),
    ]
    mocker.patch("rss_fetcher.feedparser.parse", return_value=MockFeed(mock_entries))
    mocker.patch("rss_fetcher.db_manager.url_exists", return_value=True)

    rss_urls = ["http://example.com/feed.xml"]
    new_articles = fetch_new_articles(rss_urls)

    assert len(new_articles) == 0

def test_fetch_new_articles_with_only_new_entries(mocker):
    """すべての記事が新しい場合のテスト"""
    mock_entries = [
        MockEntry("New Article 1", "http://example.com/new1", "Summary 1", time.gmtime(100)),
        MockEntry("New Article 2", "http://example.com/new2", "Summary 2", time.gmtime(200)),
    ]
    mocker.patch("rss_fetcher.feedparser.parse", return_value=MockFeed(mock_entries))
    mocker.patch("rss_fetcher.db_manager.url_exists", return_value=False)

    rss_urls = ["http://example.com/feed.xml"]
    new_articles = fetch_new_articles(rss_urls)

    assert len(new_articles) == 2
    assert new_articles[0]["link"] == "http://example.com/new1"
    assert new_articles[1]["link"] == "http://example.com/new2"

def test_fetch_new_articles_with_empty_feed(mocker):
    """RSSフィードが空の場合のテスト"""
    mocker.patch("rss_fetcher.feedparser.parse", return_value=MockFeed([]))
    db_mock = mocker.patch("rss_fetcher.db_manager.url_exists")

    rss_urls = ["http://example.com/empty_feed.xml"]
    new_articles = fetch_new_articles(rss_urls)

    assert len(new_articles) == 0
    db_mock.assert_not_called() # DBチェックが呼ばれないことを確認

def test_fetch_new_articles_with_no_urls():
    """RSS URLのリストが空の場合のテスト"""
    # このケースでは外部ライブラリの呼び出しは発生しないはず
    new_articles = fetch_new_articles([])
    assert len(new_articles) == 0

def test_fetch_from_multiple_feeds(mocker):
    """複数のRSSフィードから取得するテスト"""
    feed1_entries = [MockEntry("Feed 1 Article", "http://f1.com/a1", "S1", time.gmtime(200))]
    feed2_entries = [MockEntry("Feed 2 Article", "http://f2.com/a2", "S2", time.gmtime(100))]

    # parseが呼ばれるたびに異なる値を返すように設定
    mocker.patch("rss_fetcher.feedparser.parse", side_effect=[
        MockFeed(feed1_entries),
        MockFeed(feed2_entries)
    ])
    mocker.patch("rss_fetcher.db_manager.url_exists", return_value=False)

    rss_urls = ["http://f1.com/feed.xml", "http://f2.com/feed.xml"]
    new_articles = fetch_new_articles(rss_urls)

    assert len(new_articles) == 2
    # ソート後の順序をチェック
    assert new_articles[0]["link"] == "http://f2.com/a2" # f2が古いはず
    assert new_articles[1]["link"] == "http://f1.com/a1"
