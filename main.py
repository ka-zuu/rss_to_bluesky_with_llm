import os
from dotenv import load_dotenv
import db_manager
import rss_fetcher
import gemini_processor
import bluesky_poster
import grapheme
from atproto import models

# 要約する記事の最大数
MAX_SUMMARIES = 1

def truncate_graphemes(text: str, length: int, placeholder: str = "...") -> str:
    """Truncates a string to a maximum number of graphemes."""
    if grapheme.length(text) <= length:
        return text

    placeholder_len = grapheme.length(placeholder)
    keep_len = length - placeholder_len
    if keep_len < 0:
        keep_len = 0

    graphemes = list(grapheme.graphemes(text))
    return "".join(graphemes[:keep_len]) + placeholder

def main():
    """メインの処理フロー"""
    # 環境変数を読み込む
    load_dotenv()

    

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
    all_new_articles = rss_fetcher.fetch_new_articles(rss_urls)

    if not all_new_articles:
        print("新しい記事はありませんでした。")
        return

    # 処理対象の記事を決定（最新20件に絞り込む）
    articles_to_process = all_new_articles
    if len(all_new_articles) > 20:
        print(f"新着記事が{len(all_new_articles)}件見つかりました。最新20件に絞り込みます。")
        articles_to_process = all_new_articles[-20:]

    print(f"{len(articles_to_process)}件の新しい記事を処理します。")

    # 4. 記事の重要度評価
    print("記事をランク付け中...")
    ranked_articles = gemini_processor.rank_articles(articles_to_process)
    if not ranked_articles:
        print("記事のランク付けに失敗しました。")
        return

    # 5. Blueskyへの投稿準備
    posts = []

    # 上位1件の記事に絞り込む
    top_article = ranked_articles[0] if ranked_articles else None

    if not top_article:
        print("投稿対象の記事がありません。")
        return

    # 6. 上位記事の要約と投稿準備
    print("上位記事の要約を生成中...")
    summary = gemini_processor.summarize_article(top_article['content'])
    if summary:
        # 投稿テキストを作成
        post_text = f"【要約】{top_article['title']}\n\n{summary}"
        # Blueskyの文字数制限（300書記素）を超えないようにテキストを切り詰める
        post_text = truncate_graphemes(post_text, 300)

        # 外部リンクの埋め込みを作成
        embed_external = models.AppBskyEmbedExternal.Main(
            external=models.AppBskyEmbedExternal.External(
                uri=top_article['link'],
                title=top_article['title'],
                description=summary, # 要約をdescriptionとして使用
            )
        )
        posts.append({'text': post_text, 'embed': embed_external})
    else:
        print("要約の生成に失敗しました。")
        return


    # 7. Blueskyへの投稿
    if posts:
        print("Blueskyへ投稿中...")
        success = bluesky_poster.post_thread(posts)
    else:
        print("投稿するコンテンツがありません。")
        success = False

    # 8. データベースの更新
    if success:
        print("データベースを更新中...")
        # 投稿の成否に関わらず、取得したすべての記事をDBに追加する
        for article in all_new_articles:
            db_manager.add_url(article['link'])
        print("データベースの更新が完了しました。")
    else:
        print("Blueskyへの投稿に失敗したため、データベースは更新されませんでした。")

    print("処理が完了しました。")


if __name__ == "__main__":
    main()
