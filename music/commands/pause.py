from discord.ext import commands

from music.player import get_player


class PauseCommandMixin:
    @commands.command(name="pause", help="暫停播放")
    async def pause_command(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            get_player(ctx).pause_time()
            await ctx.send("⏸️ 已暫停播放。")
