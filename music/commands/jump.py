# music/commands/jump.py - 提供跳轉至佇列中指定歌曲的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.queue_actions import jump_to_index


class JumpCommandMixin:
    """提供佇列跳轉指令的 Mixin 類別。"""

    @app_commands.command(name="jump", description="跳轉到佇列中指定編號的歌曲")
    @app_commands.describe(index="佇列中的歌曲編號")
    async def jump_command(self, interaction: discord.Interaction, index: int) -> None:
        """將佇列中指定編號的歌曲移至第一位並立即播放。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            index (Optional[int]): 指定要跳轉的歌曲編號 (從 1 開始計數)。

        Returns:
            None.

        Notes:
            若目前有音樂正在播放，系統會停止目前播放內容，讓播放器迴圈 (Player Loop)
            能夠立即切換至選定的佇列項目。
        """
        await jump_to_index(InteractionContext(interaction), index)
