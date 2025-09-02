import os
from atproto import Client, models
from typing import List

def post_thread(post_texts: List[str]) -> bool:
    """
    Blueskyにスレッドを投稿する。
    最初のテキストが親投稿となり、以降はリプライとして連結される。
    """
    if not post_texts:
        return False

    try:
        client = Client()
        client.login(
            os.getenv("BLUESKY_HANDLE"),
            os.getenv("BLUESKY_APP_PASSWORD")
        )

        # 親投稿
        parent_post_text = post_texts[0]
        # テキストをチャンクに分割（Blueskyの文字数制限対策）
        # Facet（リンクなど）を考慮し、余裕を持った文字数で分割
        # ここでは単純な例として分割は実装せず、呼び出し元で調整する前提
        post_ref = client.send_post(text=parent_post_text)

        # 親投稿の参照を保存
        parent_ref = models.ComAtprotoRepoStrongRef.Main(uri=post_ref.uri, cid=post_ref.cid)
        root_ref = parent_ref # スレッドのルートは常に最初の投稿

        # リプライ投稿
        for i in range(1, len(post_texts)):
            reply_text = post_texts[i]
            post_ref = client.send_post(
                text=reply_text,
                reply_to=models.AppBskyFeedPost.ReplyRef(
                    parent=parent_ref,
                    root=root_ref # rootは常に最初の投稿を指す
                )
            )
            # 次のリプライのために、今投稿したものを親とする
            parent_ref = models.ComAtprotoRepoStrongRef.Main(
                uri=post_ref.uri,
                cid=post_ref.cid
            )

        print("Blueskyへのスレッド投稿に成功しました。")
        return True

    except Exception as e:
        print(f"Blueskyへの投稿中にエラーが発生しました: {e}")
        return False
