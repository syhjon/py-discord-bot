from discord.ext import commands

from music.player import get_player


class VolumecheckCommandMixin:
    @commands.command(name="volumecheck", aliases=["vol"], help="檢查目前音量")
    async def volumecheck_command(self, ctx):
        player = get_player(ctx)
        await ctx.send(f"🔊 目前音量為：{int(player.volume * 100)}%")
