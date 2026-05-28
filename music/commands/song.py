# music/commands/song.py - 提供一般點歌功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.services.playback import process_track_request


class SongCommandMixin:
    """提供一般點歌功能的 Mixin 類別。"""

    @app_commands.command(name="song", description="搜尋並透過選單選擇要播放的歌曲")
    @app_commands.describe(query="請輸入歌名或 YouTube 網址")
    async def song_command(self, interaction: discord.Interaction, query: str) -> None:
        ctx = InteractionContext(interaction)
        if not query:
            return await ctx.send("❌ 請提供要播放的歌曲名稱或 URL。")

        # 抓 10 筆，且啟用選單
        await process_track_request(
            ctx, query, self.ytdl, is_cutin=False, fetch_count=10, use_select_menu=True
        )
