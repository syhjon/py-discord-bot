# music/commands/clear.py - 提供清空播放佇列指令的 Mixin
from discord.ext import commands

from music.player import get_player


class ClearCommandMixin:
    """提供清空播放佇列指令的 Mixin 類別。"""

    @commands.command(name="clear", aliases=["clearqueue"], help="清空播放佇列")
    async def clear_command(self, ctx: commands.Context) -> None:
        """清空伺服器播放佇列中的所有待播歌曲。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令不會停止當前正在播放的歌曲，僅清空佇列中剩餘的項目。
        """
        player = get_player(ctx)
        player.queue.clear()
        await ctx.send("🗑️ 播放佇列已清空。")
