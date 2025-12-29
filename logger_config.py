import logging
import os
import sys
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
    file_handler = TimedRotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        when='midnight',
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)

    # ハンドラが既に追加されていない場合のみ追加する
    if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        logger.addHandler(file_handler)

    # 標準出力へのハンドラを追加
    # Note: FileHandler inherits from StreamHandler, so we must be specific
    # We want to add a StreamHandler that is NOT a FileHandler (or subclass)
    # Check if there is a handler that writes to sys.stdout or sys.stderr specifically,
    # OR just check exact type.

    has_stdout_handler = False
    for h in logger.handlers:
        # Check if it's exactly StreamHandler (not FileHandler etc)
        if type(h) is logging.StreamHandler:
            has_stdout_handler = True
            break

    if not has_stdout_handler:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
