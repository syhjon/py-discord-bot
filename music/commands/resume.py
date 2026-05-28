# music/commands/resume.py - 提供繼續播放功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback_controls import resume_playback


class ResumeCommandMixin:
    """提供繼續播放指令的 Mixin 類別。"""

    @app_commands.command(name="resume", description="繼續播放")
    async def resume_command(self, interaction: discord.Interaction) -> None:
        """若目前處於暫停狀態，則恢復語音播放。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會更新播放器的時間狀態，確保後續的進度顯示與實際播放時間保持準確。
        """
        await resume_playback(InteractionContext(interaction))
