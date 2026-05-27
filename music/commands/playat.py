from discord.ext import commands


class PlayatCommandMixin:
    @commands.command(
        name="playat", aliases=["pt"], help="立即播放佇列中指定編號的歌曲"
    )
    async def playat_command(self, ctx, index: int = None):
        await self.jump_command(ctx, index)  # 邏輯跟 jump 一模一樣
