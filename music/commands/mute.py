# music/commands/mute.py - 提供機器人靜音功能的指令 Mixin
from discord.ext import commands

from music.player import get_player


class MuteCommandMixin:
    """提供靜音指令的 Mixin 類別。"""

    @commands.command(name="mute", help="靜音機器人")
    async def mute_command(self, ctx: commands.Context) -> None:
        """將機器人靜音，並記錄目前的音量以便後續恢復。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            系統會儲存靜音前的音量，使得 `!unmute` 指令能夠精確還原之前的音量等級。
        """
        player = get_player(ctx)

        if player.volume > 0:
            # 儲存靜音前的音量狀態
            player.previous_volume = player.volume
            player.volume = 0.0

            # 若目前有語音連線且有音訊來源，直接調整來源音量
            if ctx.voice_client and ctx.voice_client.source:
                ctx.voice_client.source.volume = 0.0

            await ctx.send("🔇 機器人已靜音。")
        else:
            await ctx.send("🔇 機器人已經是靜音狀態。")
