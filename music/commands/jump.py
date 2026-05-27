# music/commands/jump.py - 提供跳轉至佇列中指定歌曲的指令 Mixin
from typing import Optional
from discord.ext import commands

from music.player import get_player


class JumpCommandMixin:
    """提供佇列跳轉指令的 Mixin 類別。"""

    @commands.command(name="jump", help="跳轉到佇列中指定編號的歌曲")
    async def jump_command(
        self, ctx: commands.Context, index: Optional[int] = None
    ) -> None:
        """將佇列中指定編號的歌曲移至第一位並立即播放。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            index (Optional[int]): 指定要跳轉的歌曲編號 (從 1 開始計數)。

        Returns:
            None.

        Notes:
            若當前有音樂正在播放，系統會停止當前播放內容，讓播放器迴圈 (Player Loop)
            能夠立即切換至選定的佇列項目。
        """
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
