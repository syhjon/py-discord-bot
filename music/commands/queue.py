# music/commands/queue.py - 提供佇列列表查看功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.queue_actions import show_queue


class QueueCommandMixin:
    """提供佇列查看指令的 Mixin 類別。"""

    @app_commands.command(name="queue", description="查看目前的播放佇列")
    async def queue_list(self, interaction: discord.Interaction) -> None:
        """發送目前播放佇列的格式化清單。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            為了保持訊息簡潔並符合 Discord 訊息長度限制，系統預設僅顯示佇列中的前 10 首歌曲。
        """
        await show_queue(InteractionContext(interaction))
