# assistant/cog.py - 助理功能 Cog 的向後相容模組
"""
向後相容的 Assistant Cog 匯入路徑 (Backward-compatible import path)。

這個模組的主要目的是為了維持舊有程式碼的相容性。它將實際的 `Assistant` Cog
從新的路徑 (`cogs.assistant`) 重新匯出，以確保既有依賴 `assistant.cog` 路徑
的模組在專案架構重構後，不會發生匯入錯誤 (ImportError)。
"""

from cogs.assistant import Assistant

# 明確定義模組的匯出項目，確保使用 `from assistant.cog import *` 時，
# 只會對外暴露 Assistant 類別，避免污染命名空間。
__all__ = ["Assistant"]
