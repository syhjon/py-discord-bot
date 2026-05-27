from discord.ext import commands

from music.player import get_player


class VolumeCommandMixin:
    @commands.command(name="volume", help="設定音量 (0-100)")
    async def volume_command(self, ctx, vol: int = None):
        if vol is None or vol < 0 or vol > 100:
            return await ctx.send("請指定 0 到 100 之間的有效音量值。")
        player = get_player(ctx)
        player.volume = vol / 100.0
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
        await ctx.send(f"🔊 音量已設定為 {vol}%。")
