# music/commands/stop.py - 提供停止播放並釋放播放器資源的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback_controls import stop_playback


class StopCommandMixin:
    """提供停止指令的 Mixin 類別。"""

    @app_commands.command(name="stop", description="停止播放音樂並釋放播放器資源")
    async def stop_command(self, interaction: discord.Interaction) -> None:
        """停止播放、刪除播放器面板並釋放資源。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會清空目前歌曲與待播佇列，並中斷語音連線。
            若只是短暫停止音訊並保留狀態，請改用 `/pause`。
        """
        await stop_playback(InteractionContext(interaction))
