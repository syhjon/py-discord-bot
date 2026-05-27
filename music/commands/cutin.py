# music/commands/cutin.py
from typing import Optional
from discord.ext import commands

from music.services.playback import process_track_request


class CutinCommandMixin:
    """提供插播 (Cut-in) 功能的 Mixin 類別。"""

    @commands.command(
        name="cutin",
        aliases=["insert", "插播", "pn"],
        help="將歌曲插入佇列最前並立即播放",
    )
    async def cutin_command(
        self, ctx: commands.Context, *, query: Optional[str] = None
    ) -> None:
        if not query:
            return await ctx.send("❌ 請提供要插播的歌曲名稱或 URL。")

        # 啟用插播，只抓 1 筆，不啟用選單
        await process_track_request(
            ctx, query, self.ytdl, is_cutin=True, fetch_count=1, use_select_menu=False
        )
