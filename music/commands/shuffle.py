import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.queue_actions import shuffle_queue


class ShuffleCommandMixin:
    """提供佇列隨機排序指令的 Mixin 類別。"""

    @app_commands.command(name="shuffle", description="隨機打亂播放佇列")
    async def shuffle_command(self, interaction: discord.Interaction) -> None:
        """將佇列中的歌曲順序進行隨機打亂。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            若佇列中歌曲數量少於 2 首，隨機打亂則無實質意義，系統將會忽略該請求。
        """
        await shuffle_queue(InteractionContext(interaction))
