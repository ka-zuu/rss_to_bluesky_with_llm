import os
import json
from bluesky_poster import post_thread
from dotenv import load_dotenv

def main():
    """
    GitHub Actionsから渡されたプルリクエスト情報を元に、
    Blueskyへ通知を投稿する。
    """
    # ローカルでのテスト用に.envファイルを読み込む
    load_dotenv()

    # GitHub Actionsのイベントペイロードを取得
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        print("エラー: GITHUB_EVENT_PATH 環境変数が設定されていません。")
        print("このスクリプトはGitHub Actionsのコンテキストで実行されることを意図しています。")
        # ローカルテスト用のダミーデータ
        pr_title = "テストプルリクエスト"
        pr_url = "https://github.com/example/repo/pull/1"
        pr_author = "test-user"
        pr_body = "これはテスト用のプルリクエストの本文です。"
    else:
        with open(event_path, 'r', encoding='utf-8') as f:
            event_data = json.load(f)

        pr = event_data.get("pull_request")
        if not pr:
            print("エラー: プルリクエストのデータが見つかりません。")
            return

        pr_title = pr.get("title", "タイトルの取得に失敗")
        pr_url = pr.get("html_url", "#")
        pr_author = pr.get("user", {}).get("login", "不明な作成者")
        pr_body = pr.get("body", "本文なし")

    # 本文が長い場合は短縮
    if len(pr_body) > 100:
        pr_body = pr_body[:100] + "..."

    # Blueskyに投稿するメッセージを作成
    post_text = (
        f"新しいプルリクエストが作成されました\n\n"
        f"タイトル: {pr_title}\n"
        f"作成者: {pr_author}\n\n"
        f"{pr_body}\n\n"
        f"リンクはこちら:\n{pr_url}"
    )

    print("以下の内容でBlueskyに投稿します:")
    print("--------------------------------")
    print(post_text)
    print("--------------------------------")

    # スレッド形式で投稿（今回は親投稿のみ）
    success = post_thread([post_text])

    if success:
        print("Blueskyへの投稿が正常に完了しました。")
    else:
        print("Blueskyへの投稿に失敗しました。")
        # 失敗した場合、Actionsを失敗させる
        exit(1)

if __name__ == "__main__":
    main()
