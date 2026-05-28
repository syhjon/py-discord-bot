# music/commands/skip.py - 提供跳過目前播放歌曲功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext


class SkipCommandMixin:
    """提供跳過歌曲指令的 Mixin 類別。"""

    @app_commands.command(name="skip", description="跳過目前播放的歌曲")
    async def skip_command(self, interaction: discord.Interaction) -> None:
        """透過停止目前的語音來源以跳過目前歌曲。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            停止目前音訊來源會喚醒播放器迴圈 (Player Loop)，進而觸發載入佇列中的下一首歌曲。
        """
        ctx = InteractionContext(interaction)
        if ctx.voice_client and (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            ctx.voice_client.stop()
            await ctx.send("⏭️ 已跳過歌曲！")
        else:
            await ctx.send("目前沒有播放任何歌曲可以跳過。")
