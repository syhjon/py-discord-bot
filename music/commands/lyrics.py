# music/commands/lyrics.py - lyrics slash command
import discord
from discord import app_commands

from core.context import InteractionContext


class LyricsCommandMixin:
    """歌詞查詢 slash command。"""

    @app_commands.command(name="lyrics", description="搜尋目前播放歌曲的歌詞")
    async def lyrics_command(self, interaction: discord.Interaction) -> None:
        await self.lyrics_service.show_current_lyrics(InteractionContext(interaction))
