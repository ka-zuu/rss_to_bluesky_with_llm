import feedparser
from typing import List, Dict
import db_manager
import time
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_article_content(url: str) -> str:
    """URLから記事の本文を取得する"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 一般的な記事コンテナを試す
        article_body = soup.find('article') or soup.find('main') or soup.find(class_='post-content') or soup.find(id='content')

        if article_body:
            # 不要な要素（ヘッダー、フッター、サイドバーなど）を削除
            for selector in ['header', 'footer', 'nav', 'aside', '.sidebar', '.related-posts']:
                for s in article_body.select(selector):
                    s.decompose()
            
            # テキストを抽出
            text = ' '.join(p.get_text() for p in article_body.find_all('p'))
            if len(text) > 100: # ある程度の長さがあるか確認
                return text

        # フォールバックとして、すべての<p>タグからテキストを抽出
        return ' '.join(p.get_text() for p in soup.find_all('p'))

    except requests.exceptions.RequestException as e:
        logger.error(f"記事の取得中にエラーが発生しました ({url}): {e}")
        return ""


def fetch_new_articles(rss_urls: List[str]) -> List[Dict[str, str]]:
    """
    指定されたRSSフィードURLのリストから新しい記事を取得する。
    データベースに既に存在する記事は除外する。
    記事は発行日時の昇順（古いものから新しいもの）でソートされる。
    """
    new_articles = []
    for url in rss_urls:
        logger.info(f"フィードを取得中: {url}")
        feed = feedparser.parse(url)
        for entry in feed.entries:
            article_url = entry.link
            if not db_manager.url_exists(article_url):
                logger.info(f"新しい記事が見つかりました: {entry.title}")
                # 記事の全文を取得
                content = get_article_content(article_url)
                
                published_time = entry.get('published_parsed') or entry.get('updated_parsed')
                new_articles.append({
                    "title": entry.title,
                    "link": article_url,
                    "summary": entry.summary,
                    "content": content or entry.summary, # コンテンツが取れなければサマリーを使う
                    "published_time": published_time
                })

    # 記事を発行日時でソートする（古いものが先頭）
    new_articles.sort(key=lambda x: x['published_time'] or time.gmtime())

    return new_articles
