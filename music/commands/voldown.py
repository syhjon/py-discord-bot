# music/commands/voldown.py - 提供降低音量功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.volume import decrease_volume


class VoldownCommandMixin:
    """提供降低音量指令的 Mixin 類別。"""

    @app_commands.command(name="voldown", description="降低音量 10%")
    async def voldown_command(self, interaction: discord.Interaction) -> None:
        """將播放器音量降低 10%。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            音量調整具有下限限制，調整後的數值最小為 0%。
        """
        await decrease_volume(InteractionContext(interaction))
