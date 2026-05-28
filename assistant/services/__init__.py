# assistant/services/__init__.py - 匯出供 Gemini 助理功能使用的服務模組
"""
Gemini 助理服務層 (Services Layer) 套件的初始化模組。

負責集中管理並對外暴露 (Export) 助理功能所需的核心商業邏輯與服務
(例如處理問答的 `ask_gemini` 函式)。這種封裝方式能簡化外部模組
(如 commands) 的匯入路徑，同時隱藏內部實作與檔案結構的細節，
提升架構的解耦性與可維護性。
"""

from .ask import ask_gemini

# 明確定義模組的對外暴露清單，確保使用 `from assistant.services import *` 時，
# 只會匯出經過授權對外使用的 API (如 ask_gemini)，避免內部依賴或輔助函式外洩。
__all__ = ["ask_gemini"]
