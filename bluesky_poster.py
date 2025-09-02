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
        if not parent_post_text.strip():
            print("親投稿のテキストが空です。投稿をスキップします。")
            # 親投稿が空の場合、後続の投稿をどう扱うか決める必要がある
            # ここでは、最初の有効なテキストを親投稿として扱う
            first_valid_post_index = -1
            for i, text in enumerate(post_texts):
                if text.strip():
                    first_valid_post_index = i
                    break
            
            if first_valid_post_index == -1:
                print("投稿する有効なテキストがありません。")
                return False

            # 有効な投稿を先頭に移動
            post_texts.insert(0, post_texts.pop(first_valid_post_index))
            parent_post_text = post_texts[0]

        post_ref = client.send_post(text=parent_post_text)

<<<<<<< Updated upstream
        # 親投稿の参照を保存
        parent_ref = models.ComAtprotoRepoStrongRef.Main(uri=post_ref.uri, cid=post_ref.cid)
        root_ref = parent_ref # スレッドのルートは常に最初の投稿
=======
        root_ref = models.ComAtprotoRepoStrongRef.Main(
            uri=post_ref.uri,
            cid=post_ref.cid
        )
        parent_ref = root_ref
>>>>>>> Stashed changes

        # リプライ投稿
        for i in range(1, len(post_texts)):
            reply_text = post_texts[i]
            if not reply_text.strip():
                continue # 空の投稿はスキップ

            post_ref = client.send_post(
                text=reply_text,
                reply_to=models.AppBskyFeedPost.ReplyRef(
                    parent=parent_ref,
<<<<<<< Updated upstream
                    root=root_ref # rootは常に最初の投稿を指す
=======
                    root=root_ref
>>>>>>> Stashed changes
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
