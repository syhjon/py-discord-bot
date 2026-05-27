# music/commands/volup.py - 提供增加音量功能的指令 Mixin
from discord.ext import commands

from music.player import get_player


class VolupCommandMixin:
    """提供增加音量指令的 Mixin 類別。"""

    @commands.command(name="volup", help="增加音量 10%")
    async def volup_command(self, ctx: commands.Context) -> None:
        """將播放器音量增加 10%。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            音量調整具有上限限制，調整後的數值最大為 100%。
        """
        player = get_player(ctx)
        # 增加音量並確保不超過 100% (1.0)
        new_vol = min(player.volume + 0.1, 1.0)
        player.volume = new_vol

        # 若目前有語音連線，同步調整來源音量
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume

        await ctx.send(f"🔊 音量已增加至 {int(new_vol * 100)}%。")
