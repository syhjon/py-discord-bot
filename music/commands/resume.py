from discord.ext import commands

from music.player import get_player


class ResumeCommandMixin:
    @commands.command(name="resume", help="繼續播放")
    async def resume_command(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            get_player(ctx).resume_time()
            await ctx.send("▶️ 已繼續播放。")
