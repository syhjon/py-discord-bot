from discord.ext import commands

from music.player import get_player


class VoldownCommandMixin:
    @commands.command(name="voldown", help="降低音量 10%")
    async def voldown_command(self, ctx):
        player = get_player(ctx)
        new_vol = max(player.volume - 0.1, 0.0)
        player.volume = new_vol
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
        await ctx.send(f"🔉 音量已降低至 {int(new_vol * 100)}%。")
