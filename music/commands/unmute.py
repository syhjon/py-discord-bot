# music/commands/unmute.py - 提供機器人取消靜音功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class UnmuteCommandMixin:
    """提供取消靜音指令的 Mixin 類別。"""

    @app_commands.command(name="unmute", description="取消靜音")
    async def unmute_command(self, interaction: discord.Interaction) -> None:
        """恢復機器人在靜音前的音量設定。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會檢查 `previous_volume` 的紀錄並進行還原。若機器人目前非靜音狀態，
            系統將會回覆不需要執行任何動作。
        """
        ctx = InteractionContext(interaction)
        player = get_player(ctx)

        if player.volume == 0.0 and player.previous_volume is not None:
            # 恢復音量設定
            player.volume = player.previous_volume

            # 若目前有語音連線，同步調整來源音量
            if ctx.voice_client and ctx.voice_client.source:
                ctx.voice_client.source.volume = player.volume

            # 重置儲存的音量紀錄
            player.previous_volume = None
            await ctx.send("🔊 機器人已取消靜音。")

        elif player.volume > 0:
            await ctx.send("🔊 機器人目前不是靜音狀態。")
