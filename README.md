# RSS to Bluesky with LLM

RSSフィードの更新を自動で取得し、大規模言語モデル（LLM）を使って要約とランク付けを行い、Blueskyにスレッド形式で投稿するPythonスクリプトです。

## 概要

このスクリプトは、指定された複数のRSSフィードを定期的に巡回し、新しい記事がないかを確認します。新しい記事が見つかった場合、Gemini APIを利用して記事の重要度を判断し、ランク付けされたリストを生成します。

その後、リストの親投稿と、上位記事の要約をリプライとして、Blueskyにスレッド形式で自動投稿します。一度処理した記事はローカルのSQLiteデータベースに記録され、重複して投稿されることはありません。

## システム要件

- Python 3.7以上
- `pip`

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/rss-to-bluesky-with-llm.git
cd rss-to-bluesky-with-llm
```

### 2. 依存関係のインストール

必要なPythonライブラリをインストールします。

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

スクリプトは、APIキーやアカウント情報などの設定を環境変数から読み込みます。`.env.example` ファイルをコピーして `.env` ファイルを作成してください。

```bash
cp .env.example .env
```

次に、作成した `.env` ファイルをエディタで開き、以下の項目を設定してください。

- `GEMINI_API_KEY`: Google AI Studioで取得したGemini APIキー。
- `BLUESKY_HANDLE`: あなたのBlueskyハンドル名（例: `example.bsky.social`）。
- `BLUESKY_APP_PASSWORD`: Blueskyのアプリパスワード。**通常のパスワードではなく、[設定画面](https://bsky.app/settings/app-passwords)で生成した専用のものを利用してください。**
- `RSS_URLS`: 監視したいRSSフィードのURL。複数ある場合はカンマ区切りで指定します（例: `https://example.com/rss1.xml,https://example.com/rss2.xml`）。

## 実行方法

### 手動実行

以下のコマンドでスクリプトを手動で実行できます。

```bash
python main.py
```

初回実行時には、プロジェクトディレクトリに `rss_cache.db` というSQLiteデータベースファイルが自動で作成されます。

### 定期実行 (cron)

Linuxサーバーなどで定期的に実行したい場合は、cronジョブを利用するのが便利です。例えば、3時間ごとにスクリプトを実行するには、`crontab -e` で以下の行を追加します。
※`/path/to/your/script` の部分は、実際のプロジェクトの絶対パスに置き換えてください。

```crontab
0 */3 * * * /usr/bin/python3 /path/to/your/script/main.py >> /path/to/your/script/cron.log 2>&1
```

## プロジェクト構造

- `main.py`: 全体の処理フローを制御するメインスクリプト。
- `rss_fetcher.py`: RSSフィードを取得し、新しい記事を抽出するモジュール。
- `gemini_processor.py`: Gemini APIと連携し、記事のランク付けと要約を行うモジュール。
- `bluesky_poster.py`: Blueskyへの認証とスレッド投稿を行うモジュール。
- `db_manager.py`: 投稿済み記事を記録するSQLiteデータベースを管理するモジュール。
- `requirements.txt`: 依存ライブラリのリスト。
- `.env.example`: 環境変数の設定例ファイル。
- `spec.md`: プロジェクトの仕様書。
- `.gitignore`: Gitの追跡から除外するファイル（`.env`や`rss_cache.db`など）を指定。