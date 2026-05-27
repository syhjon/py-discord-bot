from discord.ext import commands

from music.player import get_player
from music.utils import format_time


class QueueCommandMixin:
    @commands.command(name="queue", aliases=["list"], help="查看目前的播放佇列")
    async def queue_list(self, ctx):
        player = get_player(ctx)
        if len(player.queue) == 0:
            return await ctx.send("目前沒有任何歌曲在佇列中。")

        queue_str = "\n".join(
            [
                f"{i+1}. {song['title']} - `{format_time(song.get('duration', 0))}`"
                for i, song in enumerate(player.queue[:10])
            ]
        )
        if len(player.queue) > 10:
            queue_str += f"\n... 還有 {len(player.queue) - 10} 首歌曲"

        await ctx.send(f"**播放佇列：**\n{queue_str}")
