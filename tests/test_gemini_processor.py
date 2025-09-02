import pytest
from gemini_processor import rank_articles, summarize_article

@pytest.fixture
def mock_gemini_client(mocker):
    """google.genai.Clientをモック化するフィクスチャ"""
    # `google.genai`をモック化
    mock_genai = mocker.patch("gemini_processor.genai")
    
    # Clientインスタンスと、その中の`models.generate_content`メソッドをモック化
    mock_client_instance = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    
    # `genai.Client()`が呼び出されたら、モックインスタンスを返すように設定
    mock_genai.Client.return_value = mock_client_instance
    
    return mock_client_instance, mock_response

def test_rank_articles_success(mocker, mock_gemini_client):
    """記事のランク付けが成功するかのテスト"""
    mock_client, mock_response = mock_gemini_client

    articles = [
        {"title": "Article A", "link": "http://a.com", "summary": "Sum A"},
        {"title": "Article B", "link": "http://b.com", "summary": "Sum B"},
    ]

    # Geminiからのレスポンスを模倣
    mock_response.text = "1. Article B\nhttp://b.com\n2. Article A\nhttp://a.com"

    ranked = rank_articles(articles)

    # `generate_content`が正しい引数で呼び出されたか検証
    mock_client.models.generate_content.assert_called_once()
    call_args, call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs['model'] == 'gemini-2.5-flash'
    assert "Article A" in call_kwargs['contents']
    assert "Article B" in call_kwargs['contents']

    assert len(ranked) == 2
    assert ranked[0]["title"] == "Article B"
    assert ranked[1]["title"] == "Article A"

def test_rank_articles_api_error(mocker, mock_gemini_client):
    """ランク付け時にAPIエラーが発生した場合のテスト"""
    mock_client, _ = mock_gemini_client
    mock_client.models.generate_content.side_effect = Exception("API Error")

    articles = [{"title": "Article A", "link": "http://a.com", "summary": "Sum A"}]
    ranked = rank_articles(articles)

    assert ranked == []

def test_rank_articles_empty_input():
    """入力記事リストが空の場合のテスト"""
    assert rank_articles([]) == []

def test_summarize_article_success(mocker, mock_gemini_client):
    """記事の要約が成功するかのテスト"""
    mock_client, mock_response = mock_gemini_client

    mock_response.text = "これは要約です。"

    summary = summarize_article("これは長い記事の本文です。")

    # `generate_content`が正しい引数で呼び出されたか検証
    mock_client.models.generate_content.assert_called_once()
    call_args, call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs['model'] == 'gemini-2.5-flash'
    assert "日本語3文で簡潔に要約してください" in call_kwargs['contents']
    assert "これは長い記事の本文です" in call_kwargs['contents']
    
    assert summary == "これは要約です。"

def test_summarize_article_api_error(mocker, mock_gemini_client):
    """要約時にAPIエラーが発生した場合のテスト"""
    mock_client, _ = mock_gemini_client
    mock_client.models.generate_content.side_effect = Exception("API Error")

    summary = summarize_article("記事本文")

    assert "要約の生成中にエラーが発生しました" in summary

def test_summarize_article_empty_input():
    """入力記事本文が空の場合のテスト"""
    assert summarize_article("") == ""
