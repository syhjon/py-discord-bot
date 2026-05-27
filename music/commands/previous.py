from discord.ext import commands

from music.player import get_player


class PreviousCommandMixin:
    @commands.command(name="previous", help="播放上一首歌曲")
    async def previous_command(self, ctx):
        player = get_player(ctx)
        if not player.history:
            return await ctx.send("沒有上一首歌曲的紀錄。")

        last_song = player.history.pop()
        if player.current:
            player.queue.insert(0, player.current)  # 把當前的塞回佇列
        player.current = last_song  # 強制設定為上一首
        if ctx.voice_client and (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            ctx.voice_client.stop()  # 觸發重新播放
        await ctx.send("⏮️ 播放上一首歌曲。")
