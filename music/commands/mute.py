# music/commands/mute.py - 提供機器人靜音功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.volume import mute


class MuteCommandMixin:
    """提供靜音指令的 Mixin 類別。"""

    @app_commands.command(name="mute", description="靜音機器人")
    async def mute_command(self, interaction: discord.Interaction) -> None:
        """將機器人靜音，並記錄目前的音量以便後續恢復。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            系統會儲存靜音前的音量，使得 `/unmute` 指令能夠精確還原之前的音量等級。
        """
        await mute(InteractionContext(interaction))
