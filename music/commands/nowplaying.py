import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.status import show_nowplaying


class NowplayingCommandMixin:
    """提供「現在播放 (Now Playing)」功能指令的 Mixin 類別。"""

    @app_commands.command(
        name="nowplaying", description="顯示目前播放的歌曲與播放器狀態"
    )
    async def nowplaying_command(self, interaction: discord.Interaction) -> None:
        """發送一個包含目前播放狀態資訊的 Embed 訊息。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此 Embed 訊息整合了歌曲進度、原始連結、暫停狀態、音量、循環模式以及佇列長度。
        """
        await show_nowplaying(InteractionContext(interaction))
