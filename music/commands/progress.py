import discord
from discord.ext import commands

from music.player import get_player
from music.utils import create_progress_bar, format_time


class ProgressCommandMixin:
    @commands.command(name="progress", help="顯示目前播放歌曲的進度")
    async def progress_command(self, ctx):
        player = get_player(ctx)
        if not player.current:
            return await ctx.send("目前沒有任何歌曲正在播放。")

        current_time = player.get_current_time()
        duration = player.current.get("duration", 0)
        progress_bar = create_progress_bar(current_time, duration)

        embed = discord.Embed(
            title=f"🎶 {player.current['title']}", color=discord.Color.blue()
        )
        embed.description = (
            f"`{format_time(current_time)}` {progress_bar} `{format_time(duration)}`"
        )
        await ctx.send(embed=embed)
