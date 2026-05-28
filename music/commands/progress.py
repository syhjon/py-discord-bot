import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.status import show_progress


class ProgressCommandMixin:
    """提供播放進度顯示指令的 Mixin 類別。"""

    @app_commands.command(name="progress", description="顯示目前播放歌曲的進度")
    async def progress_command(self, interaction: discord.Interaction) -> None:
        """發送一個包含目前播放進度條的 Embed 訊息。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令為 `/nowplaying` 指令的精簡版本，專注於顯示目前歌曲的播放時長與視覺化進度條。
        """
        await show_progress(InteractionContext(interaction))
