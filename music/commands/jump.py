# music/commands/jump.py - 提供跳轉至佇列中指定歌曲的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


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
        ctx = InteractionContext(interaction)
        await self._jump_to_index(ctx, index)

    async def _jump_to_index(self, ctx: InteractionContext, index: int) -> None:
        if not index:
            return await ctx.send("請指定要跳轉的有效歌曲編號。")

        player = get_player(ctx)

        if index < 1 or index > len(player.queue):
            return await ctx.send("指定的歌曲編號無效。")

        # 將目標歌曲移至佇列最前端
        target_song = player.queue.pop(index - 1)
        player.queue.insert(0, target_song)

        # 若目前有播放中或暫停中的音訊，執行停止以觸發自動跳轉
        if ctx.voice_client and (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            ctx.voice_client.stop()

        await ctx.send(f"🦘 已跳轉至第 {index} 首。")
