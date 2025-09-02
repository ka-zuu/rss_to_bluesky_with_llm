import pytest
import os
from atproto import models
from bluesky_poster import post_thread

@pytest.fixture
def mock_atproto_client(mocker):
    """atproto.Clientをモック化するフィクスチャ"""
    mocker.patch.dict(os.environ, {
        "BLUESKY_HANDLE": "user.bsky.social",
        "BLUESKY_APP_PASSWORD": "password1234"
    })

    mock_client_instance = mocker.MagicMock()

    # send_postが呼び出されるたびに異なる参照を返すように設定
    def send_post_side_effect(*args, **kwargs):
        mock_post_ref = mocker.MagicMock()
        # 呼び出しごとに一意のURIとCIDを生成
        mock_post_ref.uri = f"at://did:plc:fake/app.bsky.feed.post/{mocker.ANY}"
        mock_post_ref.cid = f"bafyreih_{mocker.ANY}"
        return mock_post_ref

    mock_client_instance.send_post.side_effect = send_post_side_effect

    mock_client_class = mocker.patch("bluesky_poster.Client")
    mock_client_class.return_value = mock_client_instance

    return mock_client_instance


def test_post_thread_success(mock_atproto_client):
    """スレッド投稿が成功し、rootとparentが正しく設定されているかのテスト"""
    post_texts = ["Parent post", "Reply 1", "Reply 2"]

    # send_postが返すモックオブジェクトを事前に作成
    # send_postが返すオブジェクトを事前に作成
    mock_refs = []
    for i in range(len(post_texts)):
        ref = models.ComAtprotoRepoStrongRef.Main(
            uri=f"at://did:plc:fake/app.bsky.feed.post/post{i}",
            cid=f"cid{i}"
        )
        mock_refs.append(ref)

    # MagicMockのsend_postメソッドのside_effectを設定
    mock_atproto_client.send_post.side_effect = mock_refs

    result = post_thread(post_texts)

    assert result is True
    mock_atproto_client.login.assert_called_once_with("user.bsky.social", "password1234")
    assert mock_atproto_client.send_post.call_count == 3

    # 1. 親投稿の検証
    first_call_args = mock_atproto_client.send_post.call_args_list[0]
    assert first_call_args.kwargs['text'] == "Parent post"
    assert 'reply_to' not in first_call_args.kwargs

    # 2. 最初の返信の検証
    second_call_args = mock_atproto_client.send_post.call_args_list[1]
    assert second_call_args.kwargs['text'] == "Reply 1"
    reply_to_1 = second_call_args.kwargs['reply_to']
    assert isinstance(reply_to_1, models.AppBskyFeedPost.ReplyRef)
    # rootは親投稿の参照
    assert reply_to_1.root.uri == mock_refs[0].uri
    assert reply_to_1.root.cid == mock_refs[0].cid
    # parentは親投稿の参照
    assert reply_to_1.parent.uri == mock_refs[0].uri
    assert reply_to_1.parent.cid == mock_refs[0].cid

    # 3. 2番目の返信の検証
    third_call_args = mock_atproto_client.send_post.call_args_list[2]
    assert third_call_args.kwargs['text'] == "Reply 2"
    reply_to_2 = third_call_args.kwargs['reply_to']
    assert isinstance(reply_to_2, models.AppBskyFeedPost.ReplyRef)
    # rootは親投稿の参照
    assert reply_to_2.root.uri == mock_refs[0].uri
    assert reply_to_2.root.cid == mock_refs[0].cid
    # parentは1番目の返信の参照
    assert reply_to_2.parent.uri == mock_refs[1].uri
    assert reply_to_2.parent.cid == mock_refs[1].cid

def test_post_single_post_success(mock_atproto_client):
    """単一投稿が成功するかのテスト"""
    post_texts = ["Just one post"]

    result = post_thread(post_texts)

    mock_atproto_client.login.assert_called_once()
    mock_atproto_client.send_post.assert_called_once_with(text="Just one post")
    assert result is True

def test_post_thread_api_error(mock_atproto_client):
    """APIエラー時にFalseを返すかのテスト"""
    mock_atproto_client.send_post.side_effect = Exception("API Error")

    post_texts = ["Parent post", "Reply 1"]
    result = post_thread(post_texts)

    assert result is False

def test_post_thread_empty_input():
    """投稿リストが空の場合にFalseを返すかのテスト"""
    result = post_thread([])
    assert result is False

def test_post_thread_login_error(mock_atproto_client):
    """ログイン失敗時にFalseを返すかのテスト"""
    mock_atproto_client.login.side_effect = Exception("Login failed")

    post_texts = ["Some post"]
    result = post_thread(post_texts)

    mock_atproto_client.send_post.assert_not_called()
    assert result is False
