from discord.ext import commands

from music.player import get_player


class ClearCommandMixin:
    @commands.command(name="clear", aliases=["clearqueue"], help="清空播放佇列")
    async def clear_command(self, ctx):
        player = get_player(ctx)
        player.queue.clear()
        await ctx.send("🗑️ 播放佇列已清空。")
