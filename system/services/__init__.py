# system/services/__init__.py - 系統與診斷指令的服務模組初始化
"""
系統與診斷服務層 (Services Layer) 套件的初始化模組。

負責集中管理並對外暴露 (Export) 與系統監控、硬體狀態採集相關的核心服務
(例如用於收集主機資源資訊並發送至 Discord 的 `send_sysinfo` 函式)。
透過此檔案進行封裝，可簡化展示層 (如 system.commands 或主 Cog) 的匯入路徑，
並隱藏內部的檔案結構與輔助實作細節。
"""

from .sysinfo import send_sysinfo

# 明確定義模組的對外暴露清單，確保當其他模組使用 `from system.services import *` 時，
# 只會匯出經過授權的 API (如 send_sysinfo)，維持命名空間的整潔並避免內部依賴洩漏。
__all__ = ["send_sysinfo"]
