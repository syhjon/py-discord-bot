# general/ui/__init__.py - 通用介面 (UI) 元件的初始化模組
"""
通用使用者介面 (UI) 套件的初始化模組。

負責集中管理並對外暴露 (Export) 與機器人通用功能相關的 Discord UI 元件
(例如：按鈕、選單、分頁視圖等)。透過此模組進行封裝，外部程式碼
只需直接從 `general.ui` 匯入所需元件，而無需耦合底層特定的檔案結構。
"""

from .help import HelpPagination

# 明確定義模組的對外暴露清單，確保使用 `from general.ui import *` 時，
# 只會匯出授權對外的 UI 類別 (如 HelpPagination)，維持命名空間的整潔並避免不必要的依賴洩漏。
__all__ = ["HelpPagination"]
