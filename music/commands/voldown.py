# music/commands/voldown.py - 提供降低音量功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class VoldownCommandMixin:
    """提供降低音量指令的 Mixin 類別。"""

    @app_commands.command(name="voldown", description="降低音量 10%")
    async def voldown_command(self, interaction: discord.Interaction) -> None:
        """將播放器音量降低 10%。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            音量調整具有下限限制，調整後的數值最小為 0%。
        """
        ctx = InteractionContext(interaction)
        player = get_player(ctx)
        new_vol = max(player.volume - 0.1, 0.0)
        player.volume = new_vol

        # 若目前有語音連線，同步調整來源音量
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume

        await ctx.send(f"🔉 音量已降低至 {int(new_vol * 100)}%。")
