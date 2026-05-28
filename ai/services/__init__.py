# ai/services/__init__.py - 匯出供 AI 相關功能使用的服務模組
"""
此模組為 `ai.services` 套件的初始化檔案。

負責集中管理並匯出所有與 AI 相關的外部服務整合模組（目前包含 Gemini API 的封裝）。
透過明確定義公開介面，讓專案的其他部分可以直接從套件層級匯入所需服務，
而無需依賴內部的具體檔案結構。

範例:
    >>> from ai.services import GeminiService
"""

from .gemini import GeminiService

# 定義公開介面，確保其他模組匯入時路徑清晰，並限制 `from ai.services import *` 的行為
__all__ = [
    "GeminiService",
]