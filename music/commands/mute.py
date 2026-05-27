from discord.ext import commands

from music.player import get_player


class MuteCommandMixin:
    @commands.command(name="mute", help="靜音機器人")
    async def mute_command(self, ctx):
        player = get_player(ctx)
        if player.volume > 0:
            player.previous_volume = player.volume
            player.volume = 0.0
            if ctx.voice_client and ctx.voice_client.source:
                ctx.voice_client.source.volume = 0.0
            await ctx.send("🔇 機器人已靜音。")
        else:
            await ctx.send("🔇 機器人已經是靜音狀態。")
