# music/commands/remove.py - 提供從佇列中移除指定歌曲功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class RemoveCommandMixin:
    """提供佇列移除指令的 Mixin 類別。"""

    @app_commands.command(name="remove", description="從佇列中移除指定編號的歌曲")
    @app_commands.describe(index="要移除的佇列歌曲編號")
    async def remove_command(
        self, interaction: discord.Interaction, index: int
    ) -> None:
        """根據佇列索引位置移除特定歌曲。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            index (Optional[int]): 指定要移除的歌曲編號 (從 1 開始計數)。

        Returns:
            None.

        Notes:
            系統會先驗證輸入的編號是否在有效範圍內，確保不會發生超出佇列索引的錯誤。
        """
        ctx = InteractionContext(interaction)
        if not index:
            return await ctx.send("請提供要刪除的歌曲位置。\n用法: /remove <編號>")

        player = get_player(ctx)

        if not player.queue:
            return await ctx.send("目前播放佇列是空的。")

        if index < 1 or index > len(player.queue):
            return await ctx.send(
                f"無效的位置。請輸入 1 到 {len(player.queue)} 之間的數字。"
            )

        # 移除目標歌曲並取得資訊
        removed_song = player.queue.pop(index - 1)

        await ctx.send(f"🗑️ 已從播放清單中刪除第 {index} 首歌：{removed_song['title']}")
