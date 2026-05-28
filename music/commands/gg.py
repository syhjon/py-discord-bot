# music/commands/gg.py - 提供播放佇列除錯功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class GgCommandMixin:
    """提供佇列除錯指令的 Mixin 類別。"""

    @app_commands.command(name="gg", description="將目前播放佇列輸出到終端機")
    async def gg_command(self, interaction: discord.Interaction) -> None:
        """將目前的播放佇列輸出至終端機，以便進行除錯。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令主要用於開發期間的診斷與狀態檢查。
        """
        ctx = InteractionContext(interaction)
        player = get_player(ctx)
        print(f"目前佇列: {player.queue}")
        await ctx.send("已在終端機印出目前 Queue 的狀態。")
