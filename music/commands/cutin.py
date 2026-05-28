# music/commands/cutin.py - 提供插播 (Cut-in) 功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.services.playback import process_track_request


class CutinCommandMixin:
    """提供插播 (Cut-in) 功能的 Mixin 類別。"""

    @app_commands.command(
        name="cutin",
        description="將歌曲插入佇列最前並立即播放",
    )
    @app_commands.describe(query="請輸入歌名或 YouTube 網址")
    async def cutin_command(self, interaction: discord.Interaction, query: str) -> None:
        ctx = InteractionContext(interaction)
        if not query:
            return await ctx.send("❌ 請提供要插播的歌曲名稱或 URL。")

        # 啟用插播，只抓 1 筆，不啟用選單
        await process_track_request(
            ctx, query, self.ytdl, is_cutin=True, fetch_count=1, use_select_menu=False
        )
