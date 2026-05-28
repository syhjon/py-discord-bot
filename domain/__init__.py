# domain/__init__.py - 領域協定模組的初始化
"""
展示層與服務層共用的領域協定 (Domain Protocols) 初始化模組。

此模組定義並對外暴露了應用程式的核心介面 (Interfaces / Protocols)。
在良好的系統架構中，展示層 (例如 Cogs) 應依賴這些抽象介面，而非
具體的服務實作類別。這能大幅降低模組間的耦合度，並提升未來抽換
底層實作或進行單元測試的便利性。
"""

from .ai_interface import IAIService
from .music_interface import IMusicSearchService

# 明確定義模組的對外暴露清單，確保外部模組使用 `from domain import *` 時，
# 只會取得這些抽象的介面協定，維持領域層的純粹性。
__all__ = [
    "IAIService",
    "IMusicSearchService",
]
