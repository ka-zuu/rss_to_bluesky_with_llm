import feedparser
from typing import List, Dict
import db_manager

def fetch_new_articles(rss_urls: List[str]) -> List[Dict[str, str]]:
    """
    指定されたRSSフィードURLのリストから新しい記事を取得する。
    データベースに既に存在する記事は除外する。
    """
    new_articles = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # 記事のURLが一意の識別子として機能する
            article_url = entry.link
            if not db_manager.url_exists(article_url):
                new_articles.append({
                    "title": entry.title,
                    "link": article_url,
                    "summary": entry.summary
                })
    return new_articles
