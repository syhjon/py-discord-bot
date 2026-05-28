# music/commands/volup.py - 提供增加音量功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.volume import increase_volume


class VolupCommandMixin:
    """提供增加音量指令的 Mixin 類別。"""

    @app_commands.command(name="volup", description="增加音量 10%")
    async def volup_command(self, interaction: discord.Interaction) -> None:
        """將播放器音量增加 10%。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            音量調整具有上限限制，調整後的數值最大為 100%。
        """
        await increase_volume(InteractionContext(interaction))
