# music/commands/previous.py - 提供播放上一首歌曲功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback_controls import play_previous


class PreviousCommandMixin:
    """提供上一首歌曲指令的 Mixin 類別。"""

    @app_commands.command(name="previous", description="播放上一首歌曲")
    async def previous_command(self, interaction: discord.Interaction) -> None:
        """將歷史紀錄中的上一首歌曲移回播放狀態。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            系統會將目前正在播放的歌曲移回佇列最前端，並將歷史紀錄中的最後一首歌曲設定為目前播放項目。
        """
        await play_previous(InteractionContext(interaction))
