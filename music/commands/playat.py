# music/commands/playat.py - 提供佇列跳轉播放功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.queue_actions import jump_to_index


class PlayatCommandMixin:
    """提供佇列跳轉播放指令的 Mixin 類別。"""

    @app_commands.command(name="playat", description="立即播放佇列中指定編號的歌曲")
    @app_commands.describe(index="佇列中的歌曲編號")
    async def playat_command(
        self, interaction: discord.Interaction, index: int
    ) -> None:
        """播放佇列中指定編號的歌曲。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            index (Optional[int]): 指定要跳轉並播放的歌曲編號 (從 1 開始計數)。

        Returns:
            None.

        Notes:
            此指令將執行邏輯委派給 `jump_command`，確保 `/jump` 與 `/playat`
            在伺服器上的行為邏輯完全一致。
        """
        await jump_to_index(InteractionContext(interaction), index)
