import pytest
import os
from gemini_processor import configure_gemini, rank_articles, summarize_article

@pytest.fixture
def mock_gemini(mocker):
    """google.generativeaiモジュールをモック化するフィクスチャ"""
    mock_genai = mocker.patch("gemini_processor.genai")

    # model.generate_content().text のチェーンをモック化
    mock_response = mocker.MagicMock()
    mock_model = mocker.MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    # configure_gemini内のgenai.configureもモック化
    mock_genai.configure = mocker.MagicMock()

    return mock_genai, mock_model, mock_response

def test_configure_gemini_success(mocker, mock_gemini):
    """GEMINI_API_KEYが設定されている場合のテスト"""
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    mock_genai, _, _ = mock_gemini

    configure_gemini()

    mock_genai.configure.assert_called_once_with(api_key="test_key")

def test_configure_gemini_failure(mocker):
    """GEMINI_API_KEYが設定されていない場合にValueErrorを送出するかのテスト"""
    mocker.patch.dict(os.environ, clear=True)
    with pytest.raises(ValueError, match="GEMINI_API_KEYが設定されていません。"):
        configure_gemini()

def test_rank_articles_success(mocker, mock_gemini):
    """記事のランク付けが成功するかのテスト"""
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    _, mock_model, mock_response = mock_gemini

    articles = [
        {"title": "Article A", "link": "http://a.com", "summary": "Sum A"},
        {"title": "Article B", "link": "http://b.com", "summary": "Sum B"},
    ]

    # Geminiからのレスポンスを模倣
    mock_response.text = "1. Article B\nhttp://b.com\n2. Article A\nhttp://a.com"

    ranked = rank_articles(articles)

    mock_model.generate_content.assert_called_once()
    assert len(ranked) == 2
    assert ranked[0]["title"] == "Article B"
    assert ranked[1]["title"] == "Article A"

def test_rank_articles_api_error(mocker, mock_gemini):
    """ランク付け時にAPIエラーが発生した場合のテスト"""
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    _, mock_model, _ = mock_gemini
    mock_model.generate_content.side_effect = Exception("API Error")

    articles = [{"title": "Article A", "link": "http://a.com", "summary": "Sum A"}]
    ranked = rank_articles(articles)

    assert ranked == []

def test_rank_articles_empty_input():
    """入力記事リストが空の場合のテスト"""
    assert rank_articles([]) == []

def test_summarize_article_success(mocker, mock_gemini):
    """記事の要約が成功するかのテスト"""
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    _, mock_model, mock_response = mock_gemini

    mock_response.text = "これは要約です。"

    summary = summarize_article("これは長い記事の本文です。")

    mock_model.generate_content.assert_called_once()
    assert summary == "これは要約です。"
    # プロンプトの内容を検証
    prompt = mock_model.generate_content.call_args[0][0]
    assert "日本語3文で簡潔に要約してください" in prompt
    assert "これは長い記事の本文です" in prompt

def test_summarize_article_api_error(mocker, mock_gemini):
    """要約時にAPIエラーが発生した場合のテスト"""
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    _, mock_model, _ = mock_gemini
    mock_model.generate_content.side_effect = Exception("API Error")

    summary = summarize_article("記事本文")

    assert "要約の生成中にエラーが発生しました" in summary

def test_summarize_article_empty_input():
    """入力記事本文が空の場合のテスト"""
    assert summarize_article("") == ""
