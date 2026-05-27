from discord.ext import commands

from music.player import get_player
from music.utils import format_time


class SeekCommandMixin:
    @commands.command(name="seek", help="跳轉到指定時間 (秒數)")
    async def seek_command(self, ctx, seconds: int = None):
        if seconds is None or seconds < 0:
            return await ctx.send("請指定要跳轉的有效時間 (秒數)。")
        player = get_player(ctx)
        if (
            not player.current
            or not ctx.voice_client
            or not ctx.voice_client.is_playing()
        ):
            return await ctx.send("目前沒有歌曲正在播放。")

        player.seek_offset = seconds
        # 為了避免觸發 after_play 的循環邏輯，我們先暫存 current，讓他在重新 play 時繼續播同一首
        current_song = player.current
        player.current = current_song
        player.queue.insert(0, current_song)
        ctx.voice_client.stop()  # 觸發切歌並應用 seek
        await ctx.send(f"⏩ 已跳轉至 {format_time(seconds)}。")
