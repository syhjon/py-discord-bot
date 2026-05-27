# music/commands/volumecheck.py - 提供檢查目前音量功能的指令 Mixin
from discord.ext import commands

from music.player import get_player


class VolumecheckCommandMixin:
    """提供音量檢查指令的 Mixin 類別。"""

    @commands.command(name="volumecheck", aliases=["vol"], help="檢查目前音量")
    async def volumecheck_command(self, ctx: commands.Context) -> None:
        """回報當前播放器的音量設定百分比。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            音量數值係直接從該伺服器的 `MusicPlayer` 實例狀態中獲取。
        """
        player = get_player(ctx)
        await ctx.send(f"🔊 目前音量為：{int(player.volume * 100)}%")
