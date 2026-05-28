# music/commands/volume.py - 提供直接設定音量功能的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class VolumeCommandMixin:
    """提供音量設定指令的 Mixin 類別。"""

    @app_commands.command(name="volume", description="設定音量 (0-100)")
    @app_commands.describe(vol="請輸入 0 到 100 之間的音量")
    async def volume_command(
        self, interaction: discord.Interaction, vol: int
    ) -> None:
        """設定播放器的播放音量。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            vol (Optional[int]): 目標音量百分比 (0 到 100)。

        Returns:
            None.

        Notes:
            若目前已有語音播放，系統會立即更新音訊來源的音量設定。
        """
        ctx = InteractionContext(interaction)
        if vol is None or vol < 0 or vol > 100:
            return await ctx.send("請指定 0 到 100 之間的有效音量值。")

        player = get_player(ctx)
        player.volume = vol / 100.0

        # 若目前有語音連線，同步調整來源音量
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume

        await ctx.send(f"🔊 音量已設定為 {vol}%。")
