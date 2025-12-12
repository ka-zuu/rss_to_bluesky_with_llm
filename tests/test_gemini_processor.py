import pytest
from unittest.mock import patch, MagicMock
import os
import importlib

# `gemini_processor` をインポートする前に、APIキーの存在チェックを無効化
# テストではAPIをモックするため、実際のキーは不要
if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = "dummy_key_for_testing"

import gemini_processor
from gemini_processor import rank_articles, summarize_article

@pytest.fixture
def articles():
    """テスト用の記事リストを提供するフィクスチャ"""
    return [
        {'title': '記事1', 'link': 'http://example.com/1'},
        {'title': '記事2', 'link': 'http://example.com/2'},
        {'title': '記事3', 'link': 'http://example.com/3'},
    ]

class TestGeminiProcessor:

    @patch('gemini_processor.client.models.generate_content')
    def test_rank_articles_success(self, mock_generate_content, articles):
        """rank_articlesが成功する場合のテスト"""
        # モックの設定
        mock_response = MagicMock()
        # AIの応答をシミュレート
        mock_response.text = """
1. 記事3
http://example.com/3
2. 記事1
http://example.com/1
3. 記事2
http://example.com/2
"""
        mock_generate_content.return_value = mock_response

        # テスト対象の関数を実行
        ranked = rank_articles(articles)

        # 結果の検証
        assert len(ranked) == 3
        assert ranked[0]['link'] == 'http://example.com/3'
        assert ranked[1]['link'] == 'http://example.com/1'
        assert ranked[2]['link'] == 'http://example.com/2'
        mock_generate_content.assert_called_once()
        # モデル名がデフォルトまたは設定値であることを確認
        assert mock_generate_content.call_args[1]['model'] == gemini_processor.GEMINI_MODEL

    @patch('gemini_processor.client.models.generate_content')
    def test_rank_articles_api_error(self, mock_generate_content, articles):
        """rank_articlesでAPIエラーが発生する場合のテスト"""
        # モックの設定
        mock_generate_content.side_effect = Exception("API Error")

        # テスト対象の関数を実行
        ranked = rank_articles(articles)

        # 結果の検証
        assert ranked == []

    def test_rank_articles_empty_list(self):
        """rank_articlesに空のリストを渡す場合のテスト"""
        ranked = rank_articles([])
        assert ranked == []

    @patch('gemini_processor.client.models.generate_content')
    def test_rank_articles_parsing_failure(self, mock_generate_content, articles):
        """rank_articlesでAIの応答の解析に失敗する場合のテスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.text = "予期しない形式のテキスト"
        mock_generate_content.return_value = mock_response

        # テスト対象の関数を実行
        ranked = rank_articles(articles)

        # 解析失敗時は元の順序で返されることを確認
        assert ranked == articles

    @patch('gemini_processor.client.models.generate_content')
    def test_summarize_article_success(self, mock_generate_content):
        """summarize_articleが成功する場合のテスト"""
        # モックの設定
        mock_response = MagicMock()
        summary_text = "これは要約です。3文で構成されています。最後の文です。"
        mock_response.text = summary_text
        mock_generate_content.return_value = mock_response

        # テスト対象の関数を実行
        content = "これはテスト用の記事内容です。"
        summary = summarize_article(content)

        # 結果の検証
        assert summary == summary_text
        mock_generate_content.assert_called_once()
        # モデル名がデフォルトまたは設定値であることを確認
        assert mock_generate_content.call_args[1]['model'] == gemini_processor.GEMINI_MODEL

    @patch('gemini_processor.client.models.generate_content')
    def test_summarize_article_api_error(self, mock_generate_content):
        """summarize_articleでAPIエラーが発生する場合のテスト"""
        # モックの設定
        mock_generate_content.side_effect = Exception("API Error")

        # テスト対象の関数を実行
        content = "これはテスト用の記事内容です。"
        summary = summarize_article(content)

        # 結果の検証
        assert summary == ""

    def test_summarize_article_empty_content(self):
        """summarize_articleに空のコンテンツを渡す場合のテスト"""
        summary = summarize_article("")
        assert summary == ""

    def test_model_selection_from_env(self):
        """環境変数からモデル名が読み込まれることを確認するテスト"""
        # 環境変数を一時的に変更
        test_model = "gemini-pro-test"
        with patch.dict(os.environ, {"GEMINI_MODEL": test_model}):
            # モジュールをリロードして環境変数を読み直させる
            importlib.reload(gemini_processor)
            assert gemini_processor.GEMINI_MODEL == test_model

        # 再度リロードしてデフォルトに戻す（後続のテストへの影響を防ぐ）
        # 同時にデフォルト値が正しいかも確認
        if "GEMINI_MODEL" in os.environ:
             del os.environ["GEMINI_MODEL"]
        importlib.reload(gemini_processor)
        assert gemini_processor.GEMINI_MODEL == "gemma-3-27b"
