# system/cog.py - System Cog 的向後相容匯入模組
"""
向後相容的 System Cog 匯入路徑 (Backward-compatible import path)。

這個模組的主要目的是為了維持舊有程式碼的相容性。它將實際的 `System` Cog
從新的實作路徑 (`cogs.system`) 重新匯出，以確保既有依賴 `system.cog` 路徑
的模組在專案架構重構後，不會發生匯入錯誤 (ImportError)。
"""

from cogs.system import System

# 明確定義模組的對外暴露清單，確保使用 `from system.cog import *` 時，
# 只會對外暴露 System 類別，維持命名空間的整潔並避免不必要的依賴洩漏。
__all__ = ["System"]
