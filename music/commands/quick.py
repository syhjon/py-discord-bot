# music/commands/quick.py - 提供快速播放功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback import process_track_request


class QuickCommandMixin:
    """提供快速播放指令的 Mixin 類別。"""

    @app_commands.command(name="quick", description="直接搜尋最相關歌曲並播放")
    @app_commands.describe(query="請輸入歌名或 YouTube 網址")
    async def quick_command(self, interaction: discord.Interaction, query: str) -> None:
        ctx = InteractionContext(interaction)

        # 只抓 1 筆，不啟用選單
        await process_track_request(
            ctx,
            query,
            self.youtube_service,
            is_cutin=False,
            fetch_count=1,
            use_select_menu=False,
        )
