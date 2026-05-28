# music/commands/stop.py - 提供停止播放但保留佇列功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import players


class StopCommandMixin:
    """提供停止指令的 Mixin 類別。"""

    @app_commands.command(name="stop", description="停止播放音樂（保留佇列）")
    async def stop_command(self, interaction: discord.Interaction) -> None:
        """暫停播放並完整保留目前歌曲與佇列。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令會暫停播放而非中斷語音連線，確保目前的播放狀態與後續佇列能隨時恢復。
            系統會同步暫停播放器的計時器，以確保進度條顯示正確。
        """
        ctx = InteractionContext(interaction)
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                # 使用 pause() 停止音訊輸出，能完美保留目前歌曲與後續佇列，且不觸發 player_loop 撥放下一首
                ctx.voice_client.pause()

                # 同步將播放器的計時器暫停，確保進度條不會繼續計算
                if ctx.guild.id in players:
                    players[ctx.guild.id].pause_time()

                await ctx.send("⏹️ 播放已停止，目前歌曲與後續佇列已完整保留。")

            elif ctx.voice_client.is_paused():
                await ctx.send("🎵 音樂目前已經是停止狀態。")

            else:
                await ctx.send("❌ 目前沒有任何歌曲正在播放。")
        else:
            await ctx.send("❌ 機器人目前不在語音頻道中。")
