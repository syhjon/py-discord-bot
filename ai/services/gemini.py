# ai/services/gemini.py - 提供 Gemini AI 服務的封裝模組
"""
向後相容的 Gemini 服務匯入路徑 (Backward-compatible import path)。

這個模組的目的是為了保持舊有程式碼的相容性，將實際的 `GeminiService`
從新的路徑 (`services.gemini_service`) 重新匯出，避免現有依賴此路徑的
模組在重構後發生匯入錯誤。
"""

from services.gemini_service import GeminiService

# 明確定義匯出項目，確保 `from ai.services.gemini import *` 只會匯出 GeminiService
__all__ = ["GeminiService"]
