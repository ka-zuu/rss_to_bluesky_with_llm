import os
from atproto import Client, models
from typing import List, Dict, Any

def post_thread(posts: List[Dict[str, Any]]) -> bool:
    """
    Blueskyにスレッドを投稿する。
    最初の投稿が親投稿となり、以降はリプライとして連結される。
    投稿はテキストとオプションのembedを持つ辞書のリストとして渡される。
    """
    if not posts:
        return False

    try:
        client = Client()
        client.login(
            os.getenv("BLUESKY_HANDLE"),
            os.getenv("BLUESKY_APP_PASSWORD")
        )

        # 親投稿のデータを取得
        parent_post_data = posts[0]
        parent_post_text = parent_post_data.get('text', '')

        # 親投稿が空の場合、最初の有効な投稿を親とする
        if not parent_post_text.strip():
            print("親投稿のテキストが空です。投稿をスキップします。")
            first_valid_post_index = -1
            for i, post_data in enumerate(posts):
                if post_data.get('text', '').strip():
                    first_valid_post_index = i
                    break
            
            if first_valid_post_index == -1:
                print("投稿する有効なテキストがありません。")
                return False

            # 有効な投稿を先頭に移動
            posts.insert(0, posts.pop(first_valid_post_index))
            parent_post_data = posts[0]
            parent_post_text = parent_post_data.get('text', '')

        parent_embed = parent_post_data.get('embed')
        post_ref = client.send_post(text=parent_post_text, embed=parent_embed)

        # 親投稿の参照を保存
        parent_ref = models.ComAtprotoRepoStrongRef.Main(uri=post_ref.uri, cid=post_ref.cid)
        root_ref = parent_ref # スレッドのルートは常に最初の投稿

        # リプライ投稿
        for i in range(1, len(posts)):
            reply_data = posts[i]
            reply_text = reply_data.get('text', '')
            reply_embed = reply_data.get('embed')

            if not reply_text.strip():
                continue # 空の投稿はスキップ

            post_ref = client.send_post(
                text=reply_text,
                embed=reply_embed,
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
