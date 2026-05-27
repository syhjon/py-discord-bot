import random

from discord.ext import commands

from music.player import get_player


class ShuffleCommandMixin:
    @commands.command(
        name="shuffle", aliases=["random", "mix"], help="隨機打亂播放佇列"
    )
    async def shuffle_command(self, ctx):
        player = get_player(ctx)
        if len(player.queue) < 2:
            return await ctx.send("佇列中歌曲太少，無法隨機播放。")
        random.shuffle(player.queue)
        await ctx.send("🔀 佇列已隨機打亂。")
