# music/commands/quick.py - 提供快速播放功能的指令 Mixin
from typing import Optional
from discord.ext import commands

from music.services.playback import process_track_request


class QuickCommandMixin:
    """提供快速播放指令的 Mixin 類別。"""

    @commands.command(name="quick", aliases=["fast"], help="直接搜尋最相關歌曲並播放")
    async def quick_command(
        self, ctx: commands.Context, *, query: Optional[str] = None
    ) -> None:
        if not query:
            return await ctx.send("❌ 請提供歌曲名稱或連結。")

        # 只抓 1 筆，不啟用選單
        await process_track_request(
            ctx, query, self.ytdl, is_cutin=False, fetch_count=1, use_select_menu=False
        )
