# music/commands/stop.py - 提供停止播放但保留佇列功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback_controls import stop_playback


class StopCommandMixin:
    """提供停止指令的 Mixin 類別。"""

    @app_commands.command(name="stop", description="停止播放音樂（保留佇列）")
    async def stop_command(self, interaction: discord.Interaction) -> None:
        """暫停播放並完整保留目前歌曲與佇列。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會暫停播放而非中斷語音連線，確保目前的播放狀態與後續佇列能隨時恢復。
            系統會同步暫停播放器的計時器，以確保進度條顯示正確。
        """
        await stop_playback(InteractionContext(interaction))
