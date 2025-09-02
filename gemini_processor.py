from google import genai
from typing import List, Dict
import os

# APIクライアントをモジュールレベルで初期化
client = genai.Client()

def rank_articles(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Gemini APIを使用して記事を重要度順にランク付けする"""
    if not articles:
        return []

    # プロンプトの作成
    prompt_parts = ["以下の記事を重要度が高い順に、番号を付けてリスト化してください。タイトルとURLのみを出力してください。\n"]
    for i, article in enumerate(articles):
        prompt_parts.append(f"{i+1}. {article['title']}\n{article['link']}\n")

    prompt = "".join(prompt_parts)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        ranked_text = response.text
    except Exception as e:
        print(f"Gemini APIでエラーが発生しました: {e}")
        return [] # エラー時は空のリストを返す

    # AIの出力（テキスト）を解析して、順序付けられた記事リストを再構築
    ranked_articles = []
    lines = ranked_text.strip().split('\n')

    # AIの出力からURLを抽出し、元の記事リストと照合
    urls_in_order = []
    for line in lines:
        # URLを含む行を探す
        if 'http' in line:
            # AIの出力にはタイトルとURLが含まれる想定
            # URLをキーにして元の記事情報を引き当てる
            for article in articles:
                if article['link'] in line and article not in ranked_articles:
                    urls_in_order.append(article['link'])
                    break

    # 抽出したURLの順序で記事をリストに追加
    for url in urls_in_order:
        for article in articles:
            if article['link'] == url:
                ranked_articles.append(article)
                break

    # AIの出力の解析に失敗した場合、元の順序で返す
    if not ranked_articles:
        return articles

    return ranked_articles

def summarize_article(article_content: str) -> str:
    """Gemini APIを使用して記事を3文で要約する"""
    if not article_content:
        return ""

    prompt = f"以下の文章を日本語3文で簡潔に要約してください。\n\n---\n{article_content}\n---"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini APIでの要約中にエラーが発生しました: {e}")
        return "要約の生成中にエラーが発生しました。"
