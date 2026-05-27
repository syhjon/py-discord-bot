# music/commands/gg.py - 提供播放佇列除錯功能的指令 Mixin
from discord.ext import commands

from music.player import get_player


class GgCommandMixin:
    """提供佇列除錯指令的 Mixin 類別。"""

    @commands.command(name="gg", aliases=["getQueue"], help="測試用")
    async def gg_command(self, ctx: commands.Context) -> None:
        """將目前的播放佇列輸出至終端機，以便進行除錯。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令主要用於開發期間的診斷與狀態檢查。
        """
        player = get_player(ctx)
        print(f"目前佇列: {player.queue}")
        await ctx.send("已在終端機印出目前 Queue 的狀態。")
