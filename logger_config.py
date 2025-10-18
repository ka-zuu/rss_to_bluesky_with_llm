import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "log"
LOG_FILE = "app.log"

def setup_logging():
    """
    アプリケーションのロギングを設定します。
    - INFOレベル以上のログを記録します。
    - ログは 'log/app.log' に保存されます。
    - ログファイルは毎日ローテーションされ、過去7日分が保持されます。
    """
    # ログディレクトリが存在しない場合は作成
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )

    # ルートロガーを取得
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # TimedRotatingFileHandler を設定
    # when='midnight' で日付が変わるタイミングでローテーション
    # backupCount=7 で7世代分のログを保持
    handler = TimedRotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        when='midnight',
        backupCount=7,
        encoding='utf-8'
    )
    handler.setFormatter(log_formatter)

    # ハンドラが既に追加されていない場合のみ追加する
    if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        logger.addHandler(handler)