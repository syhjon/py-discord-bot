# general/cog.py - 通用指令 Cog 的向後相容模組
"""
向後相容的 General Cog 匯入路徑 (Backward-compatible import path)。

這個模組的主要目的是為了維持舊有程式碼的相容性。它將實際的 `General` Cog
從新的路徑 (`cogs.general`) 重新匯出，以確保既有依賴 `general.cog` 路徑
的模組在專案架構重構後，不會發生匯入錯誤 (ImportError)。
"""

from cogs.general import General

# 明確定義模組的匯出項目，確保使用 `from general.cog import *` 時，
# 只會對外暴露 General 類別，維持命名空間的整潔並避免不必要的依賴洩漏。
__all__ = ["General"]
