# music/commands/song.py
from typing import Optional
from discord.ext import commands

from music.services.playback import process_track_request


class SongCommandMixin:
    """提供一般點歌功能的 Mixin 類別。"""

    @commands.command(
        name="song", aliases=["播放"], help="搜尋並透過選單選擇要播放的歌曲"
    )
    async def song_command(
        self, ctx: commands.Context, *, query: Optional[str] = None
    ) -> None:
        if not query:
            return await ctx.send("❌ 請提供要播放的歌曲名稱或 URL。")

        # 抓 10 筆，且啟用選單
        await process_track_request(
            ctx, query, self.ytdl, is_cutin=False, fetch_count=10, use_select_menu=True
        )
