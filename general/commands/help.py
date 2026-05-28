# general/commands/help.py - 提供機器人指令說明的功能模組
"""
機器人幫助指令模組 (Help command module)。

此模組提供了一個 Mixin 類別，封裝了 `/help` 斜線指令 (Slash Command) 的定義與路由邏輯。
它負責接收使用者的幫助請求，並將實際的介面渲染與訊息發送邏輯委派給底層的服務層
(Services Layer) 處理，保持展示層的簡潔。
"""

from typing import Optional

import discord
from discord import app_commands

from core.context import InteractionContext
from general.services import send_help


class HelpCommandMixin:
    """
    提供幫助指令功能的 Mixin 類別。

    預期被混入 (Mixed-in) 至繼承自 `commands.Cog` 的類別中 (例如 `General` Cog)。
    請注意，繼承此 Mixin 的宿主類別 (Host Class) 必須具備 `bot` 屬性
    (即 Discord 機器人實例)，以便底層服務能讀取並列出目前載入的所有指令。
    """

    @app_commands.command(name="help", description="顯示所有可用的斜線指令")
    @app_commands.describe(specific_cmd="要查看詳細說明的指令名稱")
    async def help_command(
        self, interaction: discord.Interaction, specific_cmd: Optional[str] = None
    ) -> None:
        """
        處理 `/help` 斜線指令的非同步方法。

        當使用者不提供參數時，會列出所有可用的指令清單與簡介；
        若提供特定指令名稱，則會顯示該指令的詳細用法與參數說明。

        Args:
            interaction (discord.Interaction): 觸發此指令的 Discord 互動事件物件。
            specific_cmd (Optional[str], optional): 使用者想深入查詢的特定指令名稱。
                預設為 None。
        """
        # 將 Discord 原始的 Interaction 封裝為通用的 InteractionContext，
        # 並將機器人實例與查詢參數轉交給服務層的 send_help 函式處理實際邏輯
        await send_help(InteractionContext(interaction), self.bot, specific_cmd)
