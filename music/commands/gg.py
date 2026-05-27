from discord.ext import commands

from music.player import get_player


class GgCommandMixin:
    @commands.command(name="gg", aliases=["getQueue"], help="測試用")
    async def gg_command(self, ctx):
        player = get_player(ctx)
        print(f"目前佇列: {player.queue}")
        await ctx.send("已在終端機印出目前 Queue 的狀態。")
