# music/commands/shuffle.py - 提供隨機打亂佇列功能的指令 Mixin
import random
from discord.ext import commands

from music.player import get_player


class ShuffleCommandMixin:
    """提供佇列隨機排序指令的 Mixin 類別。"""

    @commands.command(
        name="shuffle", aliases=["random", "mix"], help="隨機打亂播放佇列"
    )
    async def shuffle_command(self, ctx: commands.Context) -> None:
        """將佇列中的歌曲順序進行隨機打亂。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            若佇列中歌曲數量少於 2 首，隨機打亂則無實質意義，系統將會忽略該請求。
        """
        player = get_player(ctx)

        if len(player.queue) < 2:
            return await ctx.send("佇列中歌曲太少，無法隨機播放。")

        random.shuffle(player.queue)
        await ctx.send("🔀 佇列已隨機打亂。")
