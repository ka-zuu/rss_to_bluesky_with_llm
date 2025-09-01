import os
from dotenv import load_dotenv
import db_manager
import rss_fetcher
import gemini_processor
import bluesky_poster

# 環境変数を読み込む
load_dotenv()

# 要約する記事の最大数
MAX_SUMMARIES = 3

def main():
    """メインの処理フロー"""
    print("処理を開始します...")

    # 1. データベースの初期化
    db_manager.init_db()

    # 2. RSSフィードのURLを環境変数から取得
    rss_urls_str = os.getenv("RSS_URLS")
    if not rss_urls_str:
        print("エラー: 環境変数 RSS_URLS が設定されていません。")
        return
    rss_urls = [url.strip() for url in rss_urls_str.split(',')]

    # 3. 新しい記事の取得
    print("新しい記事を取得中...")
    new_articles = rss_fetcher.fetch_new_articles(rss_urls)

    if not new_articles:
        print("新しい記事はありませんでした。")
        return

    print(f"{len(new_articles)}件の新しい記事が見つかりました。")

    # 4. 記事の重要度評価
    print("記事をランク付け中...")
    ranked_articles = gemini_processor.rank_articles(new_articles)
    if not ranked_articles:
        print("記事のランク付けに失敗しました。")
        return

    # 5. Blueskyへの投稿準備（親投稿）
    post_texts = []
    parent_post_text = "【最新記事の自動キュレーション】\n\nAIが選んだ注目記事リストはこちらです。\n"
    for i, article in enumerate(ranked_articles):
        parent_post_text += f"\n{i+1}. {article['title']}\n{article['link']}"

    # Blueskyの文字数制限を考慮（単純なチェック）
    if len(parent_post_text) > 300:
        parent_post_text = parent_post_text[:290] + "... (文字数制限のため省略)"

    post_texts.append(parent_post_text)

    # 6. 上位記事の要約とリプライ準備
    print("上位記事の要約を生成中...")
    articles_to_summarize = ranked_articles[:MAX_SUMMARIES]

    for article in articles_to_summarize:
        summary = gemini_processor.summarize_article(article['summary'])
        if summary:
            reply_text = f"【要約】{article['title']}\n\n{summary}\n\n記事URL:\n{article['link']}"
            if len(reply_text) > 300:
                 reply_text = reply_text[:290] + "... (文字数制限のため省略)"
            post_texts.append(reply_text)

    # 7. Blueskyへのスレッド投稿
    print("Blueskyへスレッドを投稿中...")
    success = bluesky_poster.post_thread(post_texts)

    # 8. データベースの更新
    if success:
        print("データベースを更新中...")
        for article in ranked_articles: # ランク付けされたすべての記事をDBに追加
            db_manager.add_url(article['link'])
        print("データベースの更新が完了しました。")
    else:
        print("Blueskyへの投稿に失敗したため、データベースは更新されませんでした。")

    print("処理が完了しました。")


if __name__ == "__main__":
    main()
