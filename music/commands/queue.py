# music/commands/queue.py - 提供佇列列表查看功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player
from music.utils import format_time


class QueueCommandMixin:
    """提供佇列查看指令的 Mixin 類別。"""

    @app_commands.command(name="queue", description="查看目前的播放佇列")
    async def queue_list(self, interaction: discord.Interaction) -> None:
        """發送目前播放佇列的格式化清單。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            為了保持訊息簡潔並符合 Discord 訊息長度限制，系統預設僅顯示佇列中的前 10 首歌曲。
        """
        ctx = InteractionContext(interaction)
        player = get_player(ctx)

        if len(player.queue) == 0:
            return await ctx.send("目前沒有任何歌曲在佇列中。")

        # 格式化佇列顯示字串
        queue_str = "\n".join(
            [
                f"{i+1}. {song['title']} - `{format_time(song.get('duration', 0))}`"
                for i, song in enumerate(player.queue[:10])
            ]
        )

        # 若佇列長度超過 10 首，顯示省略提示
        if len(player.queue) > 10:
            queue_str += f"\n... 以及其他 {len(player.queue) - 10} 首歌曲"

        await ctx.send(f"**播放佇列：**\n{queue_str}")
