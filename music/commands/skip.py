# music/commands/skip.py - 提供跳過目前播放歌曲功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback_controls import skip_track


class SkipCommandMixin:
    """提供跳過歌曲指令的 Mixin 類別。"""

    @app_commands.command(name="skip", description="跳過目前播放的歌曲")
    async def skip_command(self, interaction: discord.Interaction) -> None:
        """透過停止目前的語音來源以跳過目前歌曲。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            停止目前音訊來源會喚醒播放器迴圈 (Player Loop)，進而觸發載入佇列中的下一首歌曲。
        """
        await skip_track(InteractionContext(interaction))
