# music/commands/pause.py - 提供暫停播放功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback_controls import pause_playback


class PauseCommandMixin:
    """提供暫停指令的 Mixin 類別。"""

    @app_commands.command(name="pause", description="暫停播放")
    async def pause_command(self, interaction: discord.Interaction) -> None:
        """若有音訊正在播放，則暫停目前的語音播放。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會記錄暫停時間點，確保播放進度條的顯示狀態在暫停期間保持準確。
        """
        await pause_playback(InteractionContext(interaction))
