# general/commands/__init__.py - 通用指令模組的初始化檔案
"""
通用指令模組的初始化檔案 (General commands initialization)。

負責集中管理並對外暴露 (Export) 所有與通用功能相關的 Discord 指令 Mixin
(例如幫助指令 `HelpCommandMixin`)。這種作法能簡化外部模組 (如 cogs.general)
的匯入路徑，隱藏內部檔案結構的細節，進而提升模組的可讀性與封裝性。
"""

from .help import HelpCommandMixin

# 明確定義模組的對外暴露清單，確保使用 `from general.commands import *` 時，
# 只會匯出 HelpCommandMixin，維持命名空間的整潔並避免不必要的依賴洩漏。
__all__ = ["HelpCommandMixin"]
