# music/commands/remove.py - 提供從佇列中移除指定歌曲功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.queue_actions import remove_from_queue


class RemoveCommandMixin:
    """提供佇列移除指令的 Mixin 類別。"""

    @app_commands.command(name="remove", description="從佇列中移除指定編號的歌曲")
    @app_commands.describe(index="要移除的佇列歌曲編號")
    async def remove_command(
        self, interaction: discord.Interaction, index: int
    ) -> None:
        """根據佇列索引位置移除特定歌曲。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            index (Optional[int]): 指定要移除的歌曲編號 (從 1 開始計數)。

        Returns:
            None.

        Notes:
            系統會先驗證輸入的編號是否在有效範圍內，確保不會發生超出佇列索引的錯誤。
        """
        await remove_from_queue(InteractionContext(interaction), index)
