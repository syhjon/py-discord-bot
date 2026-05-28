# general/services/__init__.py - 通用功能服務層套件的初始化模組
"""
通用功能服務層 (Services Layer) 套件的初始化模組。

負責集中管理並對外暴露 (Export) 與機器人通用功能相關的核心邏輯與服務
(例如處理幫助指令介面的 `send_help` 函式)。透過此檔案進行封裝，
可以簡化外部模組 (例如 cogs.general) 的匯入路徑，同時隱藏內部的檔案
結構與輔助實作細節。
"""

from .help import send_help

# 明確定義模組的對外暴露清單，確保使用 `from general.services import *` 時，
# 只會匯出經過授權對外使用的 API (如 send_help)，避免內部依賴或區域變數外洩，
# 維持模組介面的整潔與封閉性。
__all__ = ["send_help"]
