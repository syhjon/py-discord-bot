# music/commands/skip.py - 跳過當前播放的歌曲
from discord.ext import commands


class SkipCommandMixin:
    @commands.command(name="skip", aliases=["next", "跳過"], help="跳過當前播放的歌曲")
    async def skip_command(self, ctx):
        if ctx.voice_client and (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            ctx.voice_client.stop()
            await ctx.send("⏭️ 已跳過歌曲！")
        else:
            await ctx.send("目前沒有播放任何歌曲可以跳過。")
