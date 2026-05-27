# music/commands/pause.py - 提供暫停播放功能的指令 Mixin
from discord.ext import commands

from music.player import get_player


class PauseCommandMixin:
    """提供暫停指令的 Mixin 類別。"""

    @commands.command(name="pause", help="暫停播放")
    async def pause_command(self, ctx: commands.Context) -> None:
        """若有音訊正在播放，則暫停目前的語音播放。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會記錄暫停時間點，確保播放進度條的顯示狀態在暫停期間保持準確。
        """
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            get_player(ctx).pause_time()
            await ctx.send("⏸️ 已暫停播放。")
