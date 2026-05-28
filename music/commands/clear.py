# music/commands/clear.py - 提供清空播放佇列指令的 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.queue_actions import clear_queue


class ClearCommandMixin:
    """提供清空播放佇列指令的 Mixin 類別。"""

    @app_commands.command(name="clear", description="清空播放佇列")
    async def clear_command(self, interaction: discord.Interaction) -> None:
        """清空伺服器播放佇列中的所有待播歌曲。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令不會停止目前正在播放的歌曲，僅清空佇列中剩餘的項目。
        """
        await clear_queue(InteractionContext(interaction))
