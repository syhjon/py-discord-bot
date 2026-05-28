# music/commands/unmute.py - 提供機器人取消靜音功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.volume import unmute


class UnmuteCommandMixin:
    """提供取消靜音指令的 Mixin 類別。"""

    @app_commands.command(name="unmute", description="取消靜音")
    async def unmute_command(self, interaction: discord.Interaction) -> None:
        """恢復機器人在靜音前的音量設定。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會檢查 `previous_volume` 的紀錄並進行還原。若機器人目前非靜音狀態，
            系統將會回覆不需要執行任何動作。
        """
        await unmute(InteractionContext(interaction))
