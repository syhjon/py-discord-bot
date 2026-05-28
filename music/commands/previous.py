# music/commands/previous.py - 提供播放上一首歌曲功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class PreviousCommandMixin:
    """提供上一首歌曲指令的 Mixin 類別。"""

    @app_commands.command(name="previous", description="播放上一首歌曲")
    async def previous_command(self, interaction: discord.Interaction) -> None:
        """將歷史紀錄中的上一首歌曲移回播放狀態。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            系統會將目前正在播放的歌曲移回佇列最前端，並將歷史紀錄中的最後一首歌曲設定為目前播放項目。
        """
        ctx = InteractionContext(interaction)
        player = get_player(ctx)

        if not player.history:
            return await ctx.send("沒有上一首歌曲的紀錄。")

        last_song = player.history.pop()

        # 將目前播放的歌曲塞回佇列最前
        if player.current:
            player.queue.insert(0, player.current)

        # 強制將上一首歌曲設定為目前播放
        player.current = last_song

        # 若目前有播放中或暫停中的音訊，執行停止以觸發自動重新播放
        if ctx.voice_client and (
            ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
        ):
            ctx.voice_client.stop()

        await ctx.send("⏮️ 播放上一首歌曲。")
