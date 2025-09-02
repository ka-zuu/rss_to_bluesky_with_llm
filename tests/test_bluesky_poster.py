import pytest
import os
from atproto import models
from bluesky_poster import post_thread

@pytest.fixture
def mock_atproto_client(mocker):
    """atproto.Clientをモック化するフィクスチャ"""
    # 環境変数を設定
    mocker.patch.dict(os.environ, {
        "BLUESKY_HANDLE": "user.bsky.social",
        "BLUESKY_APP_PASSWORD": "password1234"
    })

    # Clientクラスのインスタンスをモック化
    mock_client_instance = mocker.MagicMock()

    # send_postが返すオブジェクトを模倣
    mock_post_ref = mocker.MagicMock()
    mock_post_ref.uri = "at://did:plc:fake/app.bsky.feed.post/3kyn7l2zq2w2q"
    mock_post_ref.cid = "bafyreih5b2n4jdfj2l3z4z4y5l6x7q7z7y7x5l6x7q7z7y7x5l6x7"
    mock_client_instance.send_post.return_value = mock_post_ref

    # atproto.Clientのコンストラクタがモックインスタンスを返すようにする
    mock_client_class = mocker.patch("bluesky_poster.Client")
    mock_client_class.return_value = mock_client_instance

    return mock_client_instance

def test_post_thread_success(mock_atproto_client):
    """スレッド投稿が成功するかのテスト"""
    post_texts = ["Parent post", "Reply 1", "Reply 2"]

    result = post_thread(post_texts)

    # 認証が呼ばれたか
    mock_atproto_client.login.assert_called_once_with("user.bsky.social", "password1234")

    # send_postが3回呼ばれたか
    assert mock_atproto_client.send_post.call_count == 3

    # 1回目の呼び出し（親投稿）を検証
    first_call_args = mock_atproto_client.send_post.call_args_list[0]
    assert first_call_args.kwargs['text'] == "Parent post"
    assert 'reply_to' not in first_call_args.kwargs

    # 2回目の呼び出し（リプライ1）を検証
    second_call_args = mock_atproto_client.send_post.call_args_list[1]
    assert second_call_args.kwargs['text'] == "Reply 1"
    assert isinstance(second_call_args.kwargs['reply_to'], models.AppBskyFeedPost.ReplyRef)

    # 3回目の呼び出し（リプライ2）を検証
    third_call_args = mock_atproto_client.send_post.call_args_list[2]
    assert third_call_args.kwargs['text'] == "Reply 2"

    assert result is True

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
