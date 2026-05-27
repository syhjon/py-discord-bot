from discord.ext import commands

from music.player import get_player


class UnmuteCommandMixin:
    @commands.command(name="unmute", help="取消靜音")
    async def unmute_command(self, ctx):
        player = get_player(ctx)
        if player.volume == 0.0 and player.previous_volume is not None:
            player.volume = player.previous_volume
            if ctx.voice_client and ctx.voice_client.source:
                ctx.voice_client.source.volume = player.volume
            player.previous_volume = None
            await ctx.send("🔊 機器人已取消靜音。")
        elif player.volume > 0:
            await ctx.send("🔊 機器人目前不是靜音狀態。")
