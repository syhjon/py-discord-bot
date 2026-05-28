# music/commands/progress.py - 提供顯示播放進度條功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player
from music.utils import create_progress_bar, format_time


class ProgressCommandMixin:
    """提供播放進度顯示指令的 Mixin 類別。"""

    @app_commands.command(name="progress", description="顯示目前播放歌曲的進度")
    async def progress_command(self, interaction: discord.Interaction) -> None:
        """發送一個包含目前播放進度條的 Embed 訊息。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此指令為 `/nowplaying` 指令的精簡版本，專注於顯示目前歌曲的播放時長與視覺化進度條。
        """
        ctx = InteractionContext(interaction)
        player = get_player(ctx)

        if not player.current:
            return await ctx.send("目前沒有任何歌曲正在播放。")

        current_time = player.get_current_time()
        duration = player.current.get("duration", 0)
        progress_bar = create_progress_bar(current_time, duration)

        embed = discord.Embed(
            title=f"🎶 {player.current['title']}", color=discord.Color.blue()
        )
        embed.description = (
            f"`{format_time(current_time)}` {progress_bar} `{format_time(duration)}`"
        )

        await ctx.send(embed=embed)
