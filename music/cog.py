# music/cog.py - 音樂播放功能的 Cog 定義模組
"""
向後相容的 Music Cog 匯入路徑 (Backward-compatible import path)。

這個模組的主要目的是為了維持舊有程式碼的相容性。它將實際的 `Music` Cog
從新的路徑 (`cogs.music`) 重新匯出，以確保既有依賴 `music.cog` 路徑
的模組在專案架構重構後，不會發生匯入錯誤 (ImportError)。
"""

from cogs.music import Music

# 明確定義模組的匯出項目，確保使用 `from music.cog import *` 時，
# 只會對外暴露 Music 類別，維持命名空間的整潔並避免不必要的依賴洩漏。
__all__ = ["Music"]
