from discord.ext import commands

from music.player import get_player


class VolupCommandMixin:
    @commands.command(name="volup", help="增加音量 10%")
    async def volup_command(self, ctx):
        player = get_player(ctx)
        new_vol = min(player.volume + 0.1, 1.0)
        player.volume = new_vol
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
        await ctx.send(f"🔊 音量已增加至 {int(new_vol * 100)}%。")
