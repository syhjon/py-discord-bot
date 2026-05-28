# system/commands/__init__.py - 系統與診斷指令的初始化模組
"""
系統與診斷指令模組的初始化檔案 (System and diagnostics commands initialization)。

負責集中管理並對外暴露 (Export) 所有與系統監控、硬體狀態、延遲診斷相關的 Discord 指令 Mixin 
(例如系統資訊指令 `SysInfoCommandMixin`)。透過此檔案進行封裝，能有效簡化主 Cog 
(如 `cogs.system`) 的匯入路徑，並隱藏內部底層檔案結構的細節。
"""

from .sysinfo import SysInfoCommandMixin

# 明確定義模組的對外暴露清單，確保使用 `from system.commands import *` 時，
# 只會匯出經過授權的 Mixin 類別 (如 SysInfoCommandMixin)，維持命名空間的整潔並避免內部依賴洩漏。
__all__ = ["SysInfoCommandMixin"]