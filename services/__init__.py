# services/__init__.py - 服務層實作的初始化模組
"""
服務層實作的初始化模組 (Concrete service implementations)。

此模組負責匯入並對外暴露 (Export) 系統中各項服務的具體實作類別。
這些實作類別 (例如 GeminiService 與 YouTubeSearchService) 將會被
實例化並註冊到應用程式的依賴注入容器 (Service Container) 中，
以供上層的展示層 (Cogs/Commands) 呼叫使用。
"""

from .gemini_service import GeminiService
from .youtube_service import YouTubeSearchService

# 明確定義模組的對外暴露清單，確保當其他模組使用 `from services import *` 時，
# 只會取得這些具體的服務實作類別，維持命名空間的整潔並避免內部依賴或輔助函式外洩。
__all__ = [
    "GeminiService",
    "YouTubeSearchService",
]
