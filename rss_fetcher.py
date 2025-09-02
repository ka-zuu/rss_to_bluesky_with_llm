import feedparser
from typing import List, Dict
import db_manager
import time

def fetch_new_articles(rss_urls: List[str]) -> List[Dict[str, str]]:
    """
    指定されたRSSフィードURLのリストから新しい記事を取得する。
    データベースに既に存在する記事は除外する。
    記事は発行日時の昇順（古いものから新しいもの）でソートされる。
    """
    new_articles = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # 記事のURLが一意の識別子として機能する
            article_url = entry.link
            if not db_manager.url_exists(article_url):
                # published_parsed or updated_parsed を使用
                published_time = entry.get('published_parsed') or entry.get('updated_parsed')
                new_articles.append({
                    "title": entry.title,
                    "link": article_url,
                    "summary": entry.summary,
                    "published_time": published_time
                })

    # 記事を発行日時でソートする（古いものが先頭）
    # published_time がない記事は、現在時刻を仮の値として最後尾に配置
    new_articles.sort(key=lambda x: x['published_time'] or time.gmtime())

    return new_articles
