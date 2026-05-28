# assistant/commands/__init__.py - Gemini 助理功能指令模組的初始化檔
"""
Gemini 助理指令套件的初始化模組。

負責集中管理並對外暴露 (Export) 所有與 AI 助理相關的 Discord 指令 Mixin。
這樣可以簡化外部模組 (例如 cogs.assistant) 的匯入路徑，隱藏內部檔案
結構的細節，使程式碼更具可讀性與維護性。
"""

from .ask import AskCommandMixin

# 明確定義模組的對外暴露清單，確保使用 `from assistant.commands import *` 時，
# 只會匯出 AskCommandMixin，維持命名空間的整潔並避免不必要的依賴洩漏。
__all__ = ["AskCommandMixin"]
