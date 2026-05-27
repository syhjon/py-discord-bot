from discord.ext import commands

from music.player import get_player


class RemoveCommandMixin:
    @commands.command(
        name="remove", aliases=["rm", "刪除"], help="從佇列中移除指定編號的歌曲"
    )
    async def remove_command(self, ctx, index: int = None):
        if not index:
            return await ctx.send("請提供要刪除的歌曲位置。\n用法: !remove <編號>")
        player = get_player(ctx)
        if not player.queue:
            return await ctx.send("目前播放佇列是空的。")
        if index < 1 or index > len(player.queue):
            return await ctx.send(
                f"無效的位置。請輸入 1 到 {len(player.queue)} 之間的數字。"
            )

        removed_song = player.queue.pop(index - 1)
        await ctx.send(f"🗑️ 已從播放清單中刪除第 {index} 首歌：{removed_song['title']}")
