# system/commands/sysinfo.py - 系統資源監控指令模組
"""
系統資源監控指令模組 (System resource monitoring command module)。

此模組提供了一個 Mixin 類別，定義了 `/sysinfo` 斜線指令 (Slash Command)。
該指令用於收集並呈現運行機器人的主機硬體資源狀態，例如 CPU、記憶體使用率，
以及非同步任務 (asyncio tasks) 與執行緒的詳細診斷資訊。
"""

import discord
from discord import app_commands

from core.context import InteractionContext
from system.services import send_sysinfo


class SysInfoCommandMixin:
    """
    提供系統資源監控與診斷指令的 Mixin 類別。

    預期被混入 (Mixed-in) 至主 System Cog 中。它負責接收使用者的斜線指令請求，
    並將 Discord 的 Interaction 封裝成統一的上下文物件，隨後交由服務層 (Services Layer)
    執行實際的系統狀態採集與資料渲染。
    """

    @app_commands.command(
        name="sysinfo",
        description="查看系統資源與詳細的執行緒/任務清單",
    )
    async def sysinfo_command(self, interaction: discord.Interaction) -> None:
        """
        處理 `/sysinfo` 斜線指令的非同步方法。

        呼叫此指令時，會即時觸發服務層的 `send_sysinfo` 邏輯，
        收集當前伺服器主機的資源健康指標並回傳至 Discord 頻道。

        Args:
            interaction (discord.Interaction): 觸發此指令的 Discord 互動事件物件。
        """
        # 將原始的 Interaction 封裝成系統通用的 InteractionContext，
        # 並轉交給服務層處理實際的診斷與訊息發送作業。
        await send_sysinfo(InteractionContext(interaction))
