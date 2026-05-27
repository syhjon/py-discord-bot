# core/logger.py - 負責系統日誌的初始化與配置
"""
此模組負責配置全域的日誌系統 (Logging)。
提供終端機與檔案的雙向輸出，並內建檔案大小輪轉機制，確保日誌檔案不會無限膨脹。
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(logger_name: str = "MusicBot") -> logging.Logger:
    """設定並初始化系統日誌。

    將日誌同時輸出至「終端機」與「檔案」。檔案具有輪轉機制，
    當單一檔案超過 5MB 時會自動建立新檔，最多保留 5 份備份。

    Args:
        logger_name (str): 根日誌記錄器的名稱。預設為 "MusicBot"。

    Returns:
        logging.Logger: 系統的日誌記錄器實例。

    Notes:
        根日誌記錄器 (Root Logger) 僅會在系統啟動時設定一次。
        日誌會同時輸出至終端機與 `logs/bot.log`，並啟用自動輪轉功能。
    """
    # 確保日誌存放的資料夾存在
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 設定日誌輸出的格式
    log_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 建立 Root Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 處理器 1：輸出到終端機 (Console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # 處理器 2：輸出到檔案 (File)，並帶有輪轉機制
    file_handler = RotatingFileHandler(
        filename="logs/bot.log",
        encoding="utf-8",
        maxBytes=5 * 1024 * 1024,  # 最大 5 MB
        backupCount=5,  # 最多保留 5 個舊檔案
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # 降低 discord 底層 Gateway 的日誌層級，避免網路連線訊號洗版
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)

    return logging.getLogger(logger_name)
