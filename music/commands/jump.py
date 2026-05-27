from discord.ext import commands

from music.player import get_player


class JumpCommandMixin:
    @commands.command(name="jump", help="跳轉到佇列中指定編號的歌曲")
    async def jump_command(self, ctx, index: int = None):
        if not index:
            return await ctx.send("請指定要跳轉的有效歌曲編號。")
        player = get_player(ctx)
        if index < 1 or index > len(player.queue):
            return await ctx.send("指定的歌曲編號無效。")

        # 把目標歌曲移到第一首
        target_song = player.queue.pop(index - 1)
        player.queue.insert(0, target_song)
        if ctx.voice_client and (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            ctx.voice_client.stop()  # 跳過當前歌曲
        await ctx.send(f"🦘 已跳轉至第 {index} 首。")
